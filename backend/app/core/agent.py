"""
الوكيل الذكي المبسط - يربط قاعدة البيانات + LLM
Agent مبسط مع الوعي بالسياق وردود مختلفة حسب القناة
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.models import ConversationInput, AgentOutput, ConversationMessage, ConversationHistory
from app.core.llm_client import LLMClient
from app.core.prompts import build_system_prompt
from app.db.models import Conversation, Service, Doctor, Branch, Offer

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
        try:
            # 1. تحميل تاريخ المحادثة (Context Awareness)
            conversation_history = await self._load_conversation_history(
                conv_input.user_id, 
                conv_input.channel
            )
            
            # 2. جلب معلومات من قاعدة البيانات (فهم ذكي من السياق)
            db_context = self._load_db_context(conv_input.message, conversation_history)
            db_context_used = bool(db_context)
            
            # 4. بناء System Prompt
            system_prompt = build_system_prompt(
                channel=conv_input.channel,
                context=db_context
            )
            
            # 5. بناء رسائل المحادثة
            messages = self._build_messages(
                system_prompt,
                conversation_history,
                conv_input.message
            )
            
            # 6. توليد الرد باستخدام LLM
            reply_text = await self.llm_client.chat(messages, max_tokens=500)
            
            # 7. حفظ المحادثة
            self._save_conversation(conv_input, reply_text, db_context_used)
            
            return AgentOutput(
                reply_text=reply_text,
                intent=None,
                needs_handoff=False,
                unrecognized=False,
                db_context_used=db_context_used
            )
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الرسالة: {str(e)}", exc_info=True)
            # رد fallback
            fallback_reply = "عذراً، حدث خطأ. تبي أحوّلك للاستقبال يساعدونك؟"
            try:
                self._save_conversation(conv_input, fallback_reply, False)
            except:
                pass
            return AgentOutput(
                reply_text=fallback_reply,
                intent=None,
                needs_handoff=True,
                unrecognized=True,
                db_context_used=False
            )
    
    def _load_db_context(self, message: str, conversation_history: ConversationHistory) -> str:
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
                "هل عندكم أطباء", "عندكم دكتور", "هل عندكم دكتور", "أطباء"
            ])
            need_services = any(kw in context_text for kw in [
                "خدم", "خدمات", "تبييض", "تقويم", "تنظيف", "حشوه", "علاج",
                "عندكم خدمات", "وش الخدمات", "أي خدمات", "بكم", "كم يكلف", "سعر"
            ])
            need_branches = any(kw in context_text for kw in [
                "فرع", "فروع", "عنوان", "موقع", "وينكم", "وين", "عنوانكم",
                "ساعات العمل", "ساعات", "وقت العمل", "متى تفتحون", "متى تغلقون",
                "رقم", "هاتف", "تواصل", "اتصال", "كيف أتواصل", "رقمكم"
            ])
            need_offers = any(kw in context_text for kw in [
                "عرض", "عروض", "خصم", "عندكم عروض", "هل عندكم عروض"
            ])
            
            # إذا لم يكن هناك إشارة واضحة، نجلب البيانات الأساسية (أطباء وخدمات وفروع)
            if not (need_doctors or need_services or need_branches or need_offers):
                need_doctors = True
                need_services = True
                need_branches = True
            
            formatted_sections = []
            
            # جلب وتنسيق الأطباء
            if need_doctors:
                doctors = self._get_doctors_smart(message_lower)
                if doctors:
                    formatted_sections.append(self._format_doctors_table(doctors))
            
            # جلب وتنسيق الخدمات
            if need_services:
                services = self._get_services_smart(message_lower)
                if services:
                    formatted_sections.append(self._format_services_table(services))
            
            # جلب وتنسيق الفروع
            if need_branches:
                branches = self.db.query(Branch).filter(Branch.is_active == True).limit(10).all()
                if branches:
                    formatted_sections.append(self._format_branches_table(branches))
            
            # جلب وتنسيق العروض
            if need_offers:
                offers = self.db.query(Offer).filter(Offer.is_active == True).limit(10).all()
                if offers:
                    formatted_sections.append(self._format_offers_table(offers))
            
            return "\n\n".join(formatted_sections) if formatted_sections else ""
            
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
