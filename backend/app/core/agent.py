"""
الوكيل الذكي المبسط - يربط قاعدة البيانات + LLM
Agent مبسط مع الوعي بالسياق وردود مختلفة حسب القناة
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import re
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.models import ConversationInput, AgentOutput, ConversationMessage, ConversationHistory
from app.core.llm_client import LLMClient
from app.core.prompts import build_system_prompt
from app.db.models import Conversation, Service, Doctor, Branch, Offer, Appointment, Patient

logger = logging.getLogger(__name__)


class ChatAgent:
    """الوكيل الذكي المبسط - يتعامل مع رسائل العملاء"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        db_session: Session
    ):
        """
        تهيئة الوكيل
        
        Args:
            llm_client: عميل LLM (Groq)
            db_session: جلسة قاعدة البيانات
        """
        self.llm_client = llm_client
        self.db = db_session
    
    async def handle_message(self, conv_input: ConversationInput) -> AgentOutput:
        """
        معالجة رسالة من عميل
        
        Args:
            conv_input: إدخال المحادثة
        
        Returns:
            إخراج الوكيل (الرد والنتائج)
        """
        error_details = {}
        try:
            # 1. تحميل تاريخ المحادثة (Context Awareness)
            try:
                conversation_history = await self._load_conversation_history(
                    conv_input.user_id, 
                    conv_input.channel
                )
                logger.debug("✅ تم تحميل تاريخ المحادثة بنجاح")
            except Exception as e:
                error_details["conversation_history"] = {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
                logger.error(f"❌ خطأ في تحميل تاريخ المحادثة: {str(e)}", exc_info=True)
                raise
            
            # 2. كشف نية حجز موعد
            appointment_intent = self._detect_appointment_intent(conv_input.message, conversation_history)
            
            # 3. جلب معلومات من قاعدة البيانات (فهم ذكي من السياق)
            try:
                db_context = self._load_db_context(conv_input.message, conversation_history, appointment_intent)
                db_context_used = bool(db_context)
                
                if db_context:
                    logger.info(f"✅ تم جلب سياق من قاعدة البيانات ({len(db_context)} حرف)")
                else:
                    logger.warning("⚠️ لم يتم جلب أي سياق من قاعدة البيانات - قد تكون قاعدة البيانات فارغة")
            except Exception as e:
                error_details["db_context"] = {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
                logger.error(f"❌ خطأ في جلب سياق قاعدة البيانات: {str(e)}", exc_info=True)
                db_context = ""
                db_context_used = False
            
            # 4. معالجة حجز الموعد إذا كان هناك نية للحجز
            if appointment_intent.get("wants_to_book"):
                try:
                    appointment_result = await self._handle_appointment_booking(
                        conv_input, 
                        conversation_history, 
                        db_context,
                        appointment_intent
                    )
                    if appointment_result.get("success"):
                        # تم حجز الموعد بنجاح
                        reply_text = appointment_result.get("reply", "تم حجز الموعد بنجاح!")
                        logger.info("✅ تم حجز الموعد بنجاح")
                    else:
                        # فشل الحجز أو يحتاج معلومات إضافية
                        reply_text = appointment_result.get("reply", "عذراً، لم أتمكن من حجز الموعد. تبي أحوّلك للاستقبال؟")
                        logger.warning(f"⚠️ لم يتم حجز الموعد: {appointment_result.get('reason')}")
                except Exception as e:
                    error_details["appointment_booking"] = {
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                    logger.error(f"❌ خطأ في حجز الموعد: {str(e)}", exc_info=True)
                    reply_text = "عذراً، حدث خطأ في حجز الموعد. تبي أحوّلك للاستقبال يساعدونك؟"
            else:
                # 5. بناء System Prompt
                try:
                    system_prompt = build_system_prompt(
                        channel=conv_input.channel,
                        context=db_context
                    )
                    logger.debug(f"✅ System Prompt جاهز ({len(system_prompt)} حرف)")
                except Exception as e:
                    error_details["system_prompt"] = {
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                    logger.error(f"❌ خطأ في بناء System Prompt: {str(e)}", exc_info=True)
                    raise
                
                # 6. بناء رسائل المحادثة
                try:
                    messages = self._build_messages(
                        system_prompt,
                        conversation_history,
                        conv_input.message
                    )
                    logger.debug(f"✅ تم بناء {len(messages)} رسالة للمحادثة")
                except Exception as e:
                    error_details["build_messages"] = {
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                    logger.error(f"❌ خطأ في بناء رسائل المحادثة: {str(e)}", exc_info=True)
                    raise
                
                # 7. توليد الرد باستخدام LLM
                try:
                    reply_text = await self.llm_client.chat(messages, max_tokens=500)
                    logger.info(f"✅ تم توليد الرد بنجاح ({len(reply_text)} حرف)")
                except Exception as e:
                    error_details["llm"] = {
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                    logger.error(f"❌ خطأ في توليد الرد من LLM: {str(e)}", exc_info=True)
                    raise
            
            # 8. حفظ المحادثة
            try:
                self._save_conversation(conv_input, reply_text, db_context_used)
                logger.debug("✅ تم حفظ المحادثة بنجاح")
            except Exception as e:
                error_details["save_conversation"] = {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
                logger.error(f"⚠️ خطأ في حفظ المحادثة (غير حرج): {str(e)}", exc_info=True)
                # لا نرفع الخطأ هنا لأن المحادثة تمت بنجاح
            
            return AgentOutput(
                reply_text=reply_text,
                intent="appointment_booking" if appointment_intent.get("wants_to_book") else None,
                needs_handoff=False,
                unrecognized=False,
                db_context_used=db_context_used
            )
            
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            
            # تسجيل تفاصيل الخطأ الكاملة
            logger.error(
                f"❌ خطأ في معالجة الرسالة:\n"
                f"   النوع: {error_type}\n"
                f"   الرسالة: {error_message}\n"
                f"   تفاصيل إضافية: {error_details}\n"
                f"   المستخدم: {conv_input.user_id}\n"
                f"   القناة: {conv_input.channel}\n"
                f"   الرسالة: {conv_input.message[:100]}",
                exc_info=True
            )
            
            # رد fallback مع معلومات الخطأ (في بيئة التطوير)
            import os
            is_dev = os.getenv("ENVIRONMENT", "production") == "development"
            
            if is_dev and error_details:
                fallback_reply = (
                    f"عذراً، حدث خطأ ({error_type}). "
                    f"الخطأ: {error_message[:100]}. "
                    f"تفاصيل: {list(error_details.keys())}. "
                    f"تيب أحوّلك للاستقبال يساعدونك؟"
                )
            else:
                fallback_reply = "عذراً، حدث خطأ. تبي أحوّلك للاستقبال يساعدونك؟"
            
            try:
                self._save_conversation(conv_input, fallback_reply, False)
            except Exception as save_error:
                logger.error(f"❌ فشل حفظ المحادثة بعد الخطأ: {str(save_error)}")
            
            return AgentOutput(
                reply_text=fallback_reply,
                intent=None,
                needs_handoff=True,
                unrecognized=True,
                db_context_used=False
            )
    
    def _detect_appointment_intent(self, message: str, conversation_history: ConversationHistory) -> Dict[str, Any]:
        """
        كشف نية حجز موعد من الرسالة
        
        Returns:
            Dict مع wants_to_book (bool) ومعلومات إضافية
        """
        message_lower = message.lower()
        
        # كلمات مفتاحية لحجز الموعد
        booking_keywords = [
            "احجز", "حجز", "حجزي", "احجزي", "أحجز", "أحجزي",
            "موعد", "موعدي", "موعدك", "موعدنا",
            "ابي احجز", "أبي أحجز", "أبي احجز", "ابي أحجز",
            "عندي موعد", "عندنا موعد", "عندك موعد",
            "بكرا", "بكرة", "غداً", "بعد بكرا", "بعد غد",
            "يوم", "تاريخ", "وقت"
        ]
        
        wants_to_book = any(kw in message_lower for kw in booking_keywords)
        
        # محاولة استخراج معلومات الحجز
        extracted_info = {}
        
        # استخراج التاريخ/الوقت
        date_patterns = [
            r"(\d{1,2})/(\d{1,2})",  # 15/12
            r"(\d{1,2})-(\d{1,2})",  # 15-12
            r"يوم (\d{1,2})",  # يوم 15
            r"بكرا", r"بكرة", r"غداً",
            r"بعد بكرا", r"بعد غد"
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, message_lower):
                extracted_info["has_date"] = True
                break
        
        # استخراج الوقت
        time_patterns = [
            r"(\d{1,2}):(\d{2})",  # 10:30
            r"(\d{1,2}) صباح", r"(\d{1,2}) مساء",
            r"(\d{1,2}) ص", r"(\d{1,2}) م"
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, message_lower):
                extracted_info["has_time"] = True
                break
        
        return {
            "wants_to_book": wants_to_book,
            "extracted_info": extracted_info
        }
    
    async def _handle_appointment_booking(
        self,
        conv_input: ConversationInput,
        conversation_history: ConversationHistory,
        db_context: str,
        appointment_intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        معالجة حجز الموعد
        
        Returns:
            Dict مع success (bool) و reply (str) و appointment_id (optional)
        """
        try:
            message = conv_input.message
            message_lower = message.lower()
            
            # استخراج معلومات الحجز من الرسالة وتاريخ المحادثة
            # جمع جميع المعلومات من المحادثة
            full_context = message
            for msg in conversation_history.messages[-5:]:
                if msg.role == "user":
                    full_context += " " + msg.content
            
            # استخراج الاسم
            patient_name = None
            name_patterns = [
                r"اسمي (\w+)",
                r"اسمي (\w+ \w+)",
                r"أنا (\w+)",
                r"(\w+) (\w+)",  # اسم عربي مكون من كلمتين
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, full_context)
                if match:
                    patient_name = match.group(1) if len(match.groups()) == 1 else match.group(0)
                    break
            
            # استخراج رقم الهاتف
            phone = None
            phone_patterns = [
                r"(\d{10})",  # 10 أرقام
                r"(\d{9})",   # 9 أرقام
                r"05\d{8}",  # رقم سعودي
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, full_context)
                if match:
                    phone = match.group(0)
                    break
            
            # إذا لم نجد رقم هاتف، نستخدم user_id (قد يكون رقم هاتف)
            if not phone and conv_input.user_id and conv_input.user_id.isdigit():
                phone = conv_input.user_id
            
            # استخراج الخدمة
            service_id = None
            services = self.db.query(Service).filter(Service.is_active == True).all()
            for service in services:
                if service.name.lower() in message_lower:
                    service_id = service.id
                    break
            
            # إذا لم نجد خدمة محددة، نستخدم أول خدمة متاحة
            if not service_id and services:
                service_id = services[0].id
            
            # استخراج الفرع
            branch_id = None
            branches = self.db.query(Branch).filter(Branch.is_active == True).all()
            for branch in branches:
                if branch.name.lower() in message_lower or branch.city.lower() in message_lower:
                    branch_id = branch.id
                    break
            
            # إذا لم نجد فرع محدد، نستخدم أول فرع متاح
            if not branch_id and branches:
                branch_id = branches[0].id
            
            # استخراج الطبيب (اختياري)
            doctor_id = None
            doctors = self.db.query(Doctor).filter(Doctor.is_active == True).all()
            for doctor in doctors:
                if doctor.name.lower() in message_lower:
                    doctor_id = doctor.id
                    break
            
            # استخراج التاريخ والوقت
            appointment_datetime = None
            
            # محاولة استخراج التاريخ من الرسالة
            # إذا لم نجد تاريخ محدد، نستخدم بعد 3 أيام كتاريخ افتراضي
            appointment_datetime = datetime.now() + timedelta(days=3)
            appointment_datetime = appointment_datetime.replace(hour=10, minute=0, second=0, microsecond=0)
            
            # التحقق من المعلومات المطلوبة
            missing_info = []
            if not patient_name:
                missing_info.append("الاسم")
            if not phone:
                missing_info.append("رقم الهاتف")
            if not service_id:
                missing_info.append("الخدمة")
            if not branch_id:
                missing_info.append("الفرع")
            
            if missing_info:
                # نحتاج معلومات إضافية
                missing_str = "، ".join(missing_info)
                reply = f"عشان أحجز لك موعد، أحتاج: {missing_str}. ممكن تعطيني هالمعلومات؟"
                return {
                    "success": False,
                    "reply": reply,
                    "reason": f"Missing info: {missing_str}",
                    "missing_info": missing_info
                }
            
            # إنشاء الموعد
            appointment = Appointment(
                patient_name=patient_name,
                phone=phone,
                branch_id=branch_id,
                doctor_id=doctor_id,
                service_id=service_id,
                datetime=appointment_datetime,
                channel=conv_input.channel,
                status="pending",
                appointment_type="consultation",
                notes=f"حجز تلقائي من {conv_input.channel}"
            )
            
            self.db.add(appointment)
            self.db.commit()
            self.db.refresh(appointment)
            
            # جلب معلومات الموعد للرد
            branch = self.db.query(Branch).filter(Branch.id == branch_id).first()
            service = self.db.query(Service).filter(Service.id == service_id).first()
            doctor = self.db.query(Doctor).filter(Doctor.id == doctor_id).first() if doctor_id else None
            
            # بناء رد تأكيد
            reply_parts = [
                f"✅ تم حجز موعدك بنجاح!",
                f"📅 التاريخ: {appointment_datetime.strftime('%Y-%m-%d %I:%M %p')}",
                f"🏥 الفرع: {branch.name if branch else 'غير محدد'}",
                f"🩺 الخدمة: {service.name if service else 'غير محدد'}"
            ]
            
            if doctor:
                reply_parts.append(f"👨‍⚕️ الطبيب: {doctor.name}")
            
            reply_parts.append(f"📞 سنتواصل معك على {phone} لتأكيد الموعد")
            reply_parts.append("شكراً لثقتك في عيادات عادل كير! 😊")
            
            reply = "\n".join(reply_parts)
            
            logger.info(f"✅ تم حجز موعد بنجاح: {appointment.id}")
            
            return {
                "success": True,
                "reply": reply,
                "appointment_id": str(appointment.id)
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في حجز الموعد: {str(e)}", exc_info=True)
            self.db.rollback()
            return {
                "success": False,
                "reply": "عذراً، حدث خطأ في حجز الموعد. تبي أحوّلك للاستقبال يساعدونك؟",
                "reason": str(e)
            }
    
    def _load_db_context(self, message: str, conversation_history: ConversationHistory, appointment_intent: Optional[Dict[str, Any]] = None) -> str:
        """
        جلب معلومات من قاعدة البيانات بناءً على السياق
        
        Args:
            message: نص الرسالة
            conversation_history: تاريخ المحادثة
        
        Returns:
            سياق من قاعدة البيانات بتنسيق table-like
        """
        try:
            message_lower = message.lower()
            
            # جمع السياق من الرسالة وتاريخ المحادثة
            context_text = message.lower()
            for msg in conversation_history.messages[-3:]:  # آخر 3 رسائل
                if msg.role == "user":
                    context_text += " " + msg.content.lower()
            
            # تحديد البيانات المطلوبة بشكل ذكي
            need_doctors = any(kw in context_text for kw in [
                "دكتور", "طبيب", "الاطباء", "اطباء", "الأطباء", "عندكم أطباء", 
                "هل عندكم أطباء", "عندكم دكتور", "هل عندكم دكتور", "أطباء", "تخصص"
            ])
            need_services = any(kw in context_text for kw in [
                "خدم", "خدمات", "استشارة", "فحص", "علاج", "تطعيم",
                "عندكم خدمات", "وش الخدمات", "أي خدمات", "بكم", "كم يكلف", "سعر", "تكلفة"
            ])
            need_branches = any(kw in context_text for kw in [
                "فرع", "فروع", "عنوان", "موقع", "وينكم", "وين", "عنوانكم",
                "ساعات العمل", "ساعات", "وقت العمل", "متى تفتحون", "متى تغلقون",
                "رقم", "هاتف", "تواصل", "اتصال", "كيف أتواصل", "رقمكم"
            ])
            need_offers = any(kw in context_text for kw in [
                "عرض", "عروض", "خصم", "عندكم عروض", "هل عندكم عروض"
            ])
            
            # إذا كان هناك نية لحجز موعد، نجلب جميع المعلومات المطلوبة
            if appointment_intent and appointment_intent.get("wants_to_book"):
                need_doctors = True
                need_services = True
                need_branches = True
            # إذا لم يكن هناك إشارة واضحة، نجلب البيانات الأساسية (أطباء وخدمات وفروع)
            elif not (need_doctors or need_services or need_branches or need_offers):
                need_doctors = True
                need_services = True
                need_branches = True
            
            formatted_sections = []
            
            # جلب وتنسيق الأطباء
            if need_doctors:
                doctors = self._get_doctors_smart(message_lower)
                logger.info(f"تم جلب {len(doctors)} طبيب من قاعدة البيانات")
                if doctors:
                    formatted_sections.append(self._format_doctors_table(doctors))
                else:
                    logger.warning("لا توجد أطباء في قاعدة البيانات")
            
            # جلب وتنسيق الخدمات
            if need_services:
                services = self._get_services_smart(message_lower)
                logger.info(f"تم جلب {len(services)} خدمة من قاعدة البيانات")
                if services:
                    formatted_sections.append(self._format_services_table(services))
                else:
                    logger.warning("لا توجد خدمات في قاعدة البيانات")
            
            # جلب وتنسيق الفروع
            if need_branches:
                branches = self.db.query(Branch).filter(Branch.is_active == True).limit(10).all()
                logger.info(f"تم جلب {len(branches)} فرع من قاعدة البيانات")
                if branches:
                    formatted_sections.append(self._format_branches_table(branches))
                else:
                    logger.warning("لا توجد فروع في قاعدة البيانات")
            
            # جلب وتنسيق العروض
            if need_offers:
                offers = self.db.query(Offer).filter(Offer.is_active == True).limit(10).all()
                logger.info(f"تم جلب {len(offers)} عرض من قاعدة البيانات")
                if offers:
                    formatted_sections.append(self._format_offers_table(offers))
                else:
                    logger.warning("لا توجد عروض في قاعدة البيانات")
            
            result = "\n\n".join(formatted_sections) if formatted_sections else ""
            logger.info(f"السياق النهائي من قاعدة البيانات: {len(result)} حرف")
            return result
            
        except Exception as e:
            logger.error(f"خطأ في جلب معلومات قاعدة البيانات: {str(e)}", exc_info=True)
            try:
                self.db.rollback()
            except:
                pass
            return ""
    
    def _get_doctors_smart(self, message_lower: str) -> List[Doctor]:
        """جلب الأطباء بشكل ذكي - البحث عن أسماء محددة أو جلب الجميع"""
        # البحث عن أسماء محددة في الرسالة
        all_doctors = self.db.query(Doctor).filter(Doctor.is_active == True).all()
        if not all_doctors:
            return []
        
        # محاولة العثور على أسماء محددة
        matched_doctors = []
        for doctor in all_doctors:
            # البحث عن الاسم في الرسالة (بدون "د." أو "دكتور")
            doctor_name_simple = doctor.name.replace("د.", "").replace("دكتور", "").strip().lower()
            if doctor_name_simple in message_lower:
                matched_doctors.append(doctor)
        
        # إذا وُجد أطباء محددون، أرجعهم فقط
        if matched_doctors:
            return matched_doctors[:5]
        
        # وإلا أرجع جميع الأطباء (حتى 10)
        return all_doctors[:10]
    
    def _get_services_smart(self, message_lower: str) -> List[Service]:
        """جلب الخدمات بشكل ذكي - البحث عن أسماء محددة أو جلب الجميع"""
        all_services = self.db.query(Service).filter(Service.is_active == True).all()
        if not all_services:
            return []
        
        # البحث عن أسماء خدمات محددة
        service_keywords = {
            "تبييض": "تبييض",
            "تنظيف": "تنظيف",
            "تقويم": "تقويم",
            "حشو": "حشو",
            "فحص": "فحص"
        }
        
        matched_services = []
        for service in all_services:
            service_name_lower = service.name.lower()
            # البحث عن كلمات مفتاحية في اسم الخدمة
            if any(keyword in message_lower and keyword in service_name_lower 
                   for keyword in service_keywords.keys()):
                matched_services.append(service)
        
        # إذا وُجدت خدمات محددة، أرجعها فقط
        if matched_services:
            return matched_services[:5]
        
        # وإلا أرجع جميع الخدمات (حتى 10)
        return all_services[:10]
    
    def _format_doctors_table(self, doctors: List[Doctor]) -> str:
        """تنسيق بيانات الأطباء بشكل table-like"""
        if not doctors:
            return ""
        
        # جلب أسماء الفروع
        branch_ids = [d.branch_id for d in doctors if d.branch_id]
        branches_map = {}
        if branch_ids:
            branches = self.db.query(Branch).filter(Branch.id.in_(branch_ids)).all()
            branches_map = {str(b.id): b.name for b in branches}
        
        # إنشاء الجدول
        header = "=== الأطباء ==="
        separator = "─" * 80
        
        # العناوين
        columns = ["الاسم", "التخصص", "الفرع"]
        header_row = "│ " + " │ ".join(columns) + " │"
        
        rows = []
        for doctor in doctors:
            name = doctor.name[:25]  # تقصير الاسم
            specialty = (doctor.specialty or "اختصاص عام")[:20]
            branch_name = branches_map.get(str(doctor.branch_id), "-")[:15] if doctor.branch_id else "-"
            
            row = f"│ {name:<25} │ {specialty:<20} │ {branch_name:<15} │"
            rows.append(row)
        
        # تجميع الجدول
        table = f"{header}\n{separator}\n{header_row}\n{separator}\n"
        table += "\n".join(rows)
        table += f"\n{separator}"
        
        return table
    
    def _format_services_table(self, services: List[Service]) -> str:
        """تنسيق بيانات الخدمات بشكل table-like"""
        if not services:
            return ""
        
        header = "=== الخدمات ==="
        separator = "─" * 90
        
        # العناوين
        columns = ["الاسم", "السعر", "الوصف"]
        header_row = "│ " + " │ ".join(columns) + " │"
        
        rows = []
        for service in services:
            name = service.name[:20]
            price = f"{service.base_price} ريال" if service.base_price else "-"
            description = (service.description or "-")[:35]
            if len(description) > 35:
                description = description[:32] + "..."
            
            row = f"│ {name:<20} │ {price:<15} │ {description:<35} │"
            rows.append(row)
        
        # تجميع الجدول
        table = f"{header}\n{separator}\n{header_row}\n{separator}\n"
        table += "\n".join(rows)
        table += f"\n{separator}"
        
        return table
    
    def _format_branches_table(self, branches: List[Branch]) -> str:
        """تنسيق بيانات الفروع بشكل table-like"""
        if not branches:
            return ""
        
        header = "=== الفروع ==="
        separator = "─" * 120
        
        # العناوين
        columns = ["الاسم", "المدينة", "العنوان", "الهاتف", "ساعات العمل"]
        header_row = "│ " + " │ ".join(columns) + " │"
        
        rows = []
        for branch in branches:
            name = branch.name[:15]
            city = (branch.city or "-")[:15]
            address = (branch.address or "-")[:25]
            if len(address) > 25:
                address = address[:22] + "..."
            phone = (branch.phone or "-")[:15]
            
            # ساعات العمل
            working_hours_str = "-"
            if branch.working_hours:
                if isinstance(branch.working_hours, dict):
                    from_hour = branch.working_hours.get('from', '')
                    to_hour = branch.working_hours.get('to', '')
                    if from_hour and to_hour:
                        working_hours_str = f"{from_hour} - {to_hour}"
                elif isinstance(branch.working_hours, str):
                    working_hours_str = branch.working_hours[:15]
            
            row = f"│ {name:<15} │ {city:<15} │ {address:<25} │ {phone:<15} │ {working_hours_str:<15} │"
            rows.append(row)
        
        # تجميع الجدول
        table = f"{header}\n{separator}\n{header_row}\n{separator}\n"
        table += "\n".join(rows)
        table += f"\n{separator}"
        
        return table
    
    def _format_offers_table(self, offers: List[Offer]) -> str:
        """تنسيق بيانات العروض بشكل table-like"""
        if not offers:
            return ""
        
        header = "=== العروض ==="
        separator = "─" * 100
        
        # العناوين
        columns = ["العنوان", "الخصم", "الوصف"]
        header_row = "│ " + " │ ".join(columns) + " │"
        
        rows = []
        for offer in offers:
            title = offer.title[:30]
            
            # الخصم
            discount_str = "-"
            if offer.discount_type == "percentage" and offer.discount_value:
                discount_str = f"{offer.discount_value}%"
            elif offer.discount_type == "fixed" and offer.discount_value:
                discount_str = f"{offer.discount_value} ريال"
            
            description = (offer.description or "-")[:40]
            if len(description) > 40:
                description = description[:37] + "..."
            
            row = f"│ {title:<30} │ {discount_str:<15} │ {description:<40} │"
            rows.append(row)
        
        # تجميع الجدول
        table = f"{header}\n{separator}\n{header_row}\n{separator}\n"
        table += "\n".join(rows)
        table += f"\n{separator}"
        
        return table
    
    async def _load_conversation_history(
        self, 
        user_id: str, 
        channel: str,
        limit: int = 10
    ) -> ConversationHistory:
        """
        تحميل تاريخ المحادثة (Context Awareness)
        
        Args:
            user_id: معرف المستخدم
            channel: القناة
            limit: عدد الرسائل الأخيرة
        
        Returns:
            ConversationHistory
        """
        try:
            conversations = self.db.query(Conversation)\
                .filter(
                    Conversation.user_id == user_id,
                    Conversation.channel == channel
                )\
                .order_by(desc(Conversation.created_at))\
                .limit(limit)\
                .all()
            
            messages = []
            # عكس الترتيب للحصول على الترتيب الصحيح (من الأقدم للأحدث)
            for conv in reversed(conversations):
                if conv.user_message:
                    messages.append(ConversationMessage(
                        role="user",
                        content=conv.user_message
                    ))
                if conv.bot_reply:
                    messages.append(ConversationMessage(
                        role="assistant",
                        content=conv.bot_reply
                    ))
            
            return ConversationHistory(
                messages=messages,
                total_messages=len(messages)
            )
        except Exception as e:
            logger.warning(f"خطأ في تحميل تاريخ المحادثة: {str(e)}")
            try:
                self.db.rollback()
            except:
                pass
            return ConversationHistory(messages=[], total_messages=0)
    
    def _build_messages(
        self,
        system_prompt: str,
        conversation_history: ConversationHistory,
        current_message: str
    ) -> List[Dict[str, str]]:
        """
        بناء رسائل المحادثة للـ LLM
        
        Args:
            system_prompt: System Prompt
            conversation_history: تاريخ المحادثة
            current_message: الرسالة الحالية
        
        Returns:
            قائمة الرسائل
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        # إضافة تاريخ المحادثة (آخر 5 رسائل)
        for msg in conversation_history.messages[-5:]:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # إضافة الرسالة الحالية
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages
    
    def _save_conversation(
        self,
        conv_input: ConversationInput,
        reply_text: str,
        db_context_used: bool
    ):
        """
        حفظ المحادثة في قاعدة البيانات
        
        Args:
            conv_input: إدخال المحادثة
            reply_text: نص الرد
            db_context_used: هل تم استخدام معلومات من قاعدة البيانات
        """
        try:
            from datetime import datetime
            now = datetime.now()
            conversation = Conversation(
                user_id=conv_input.user_id,
                channel=conv_input.channel,
                user_message=conv_input.message,
                bot_reply=reply_text,
                intent=None,
                db_context_used=db_context_used,
                unrecognized=False,
                needs_handoff=False,
                created_at=now,
                updated_at=now
            )
            self.db.add(conversation)
            self.db.commit()
        except Exception as e:
            logger.error(f"خطأ في حفظ المحادثة: {str(e)}", exc_info=True)
            try:
                self.db.rollback()
            except:
                pass
