"""
Functional tests for ChatAgent
"""
import pytest
from unittest.mock import AsyncMock
from app.core.models import ConversationInput
from app.core.agent import ChatAgent
from app.db.models import Conversation, Doctor, Service, Branch, Offer
from datetime import datetime
import uuid


class TestAgentBasic:
    """اختبارات معالجة الرسائل الأساسية"""
    
    @pytest.mark.asyncio
    async def test_handle_message_basic(self, test_agent):
        """اختبار معالجة رسالة أساسية"""
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_1",
            message="مرحباً",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.reply_text is not None
        assert len(output.reply_text) > 0
        assert output.intent is not None
        assert isinstance(output.db_context_used, bool)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, test_agent, test_db):
        """اختبار معالجة الأخطاء"""
        # جعل LLM يرمي خطأ
        from unittest.mock import AsyncMock
        test_agent.llm_client.chat = AsyncMock(side_effect=Exception("API Error"))
        
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_error",
            message="مرحباً",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.needs_handoff is True
        assert output.unrecognized is True
        assert "خطأ" in output.reply_text or "استقبال" in output.reply_text


class TestIntentDetection:
    """اختبارات كشف النوايا"""
    
    @pytest.mark.asyncio
    async def test_intent_detection_doctors(self, test_agent):
        """اختبار كشف نية الأطباء"""
        # تحديث mock للرد بناءً على النية
        from unittest.mock import AsyncMock
        test_agent.llm_client.chat = AsyncMock(return_value="عندنا أطباء في تخصصات مختلفة")
        
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_2",
            message="وش الأطباء اللي عندكم؟",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.intent == "doctor_info"
    
    @pytest.mark.asyncio
    async def test_intent_detection_services(self, test_agent):
        """اختبار كشف نية الخدمات"""
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_3",
            message="وش الخدمات المتاحة؟",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.intent == "service_info"
    
    @pytest.mark.asyncio
    async def test_intent_detection_branches(self, test_agent):
        """اختبار كشف نية الفروع"""
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_4",
            message="وين فروعكم؟",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.intent == "branch_info"
    
    @pytest.mark.asyncio
    async def test_intent_detection_prices(self, test_agent):
        """اختبار كشف نية الأسعار"""
        from unittest.mock import AsyncMock
        test_agent.llm_client.chat = AsyncMock(return_value="تبييض الأسنان يكلف 800 ريال")
        
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_5",
            message="بكم تبييض الأسنان؟",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.intent == "price"
    
    @pytest.mark.asyncio
    async def test_intent_detection_booking(self, test_agent):
        """اختبار كشف نية الحجز"""
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_6",
            message="ابي احجز موعد",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.intent == "booking"
    
    @pytest.mark.asyncio
    async def test_intent_detection_complaint(self, test_agent):
        """اختبار كشف نية الشكوى"""
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_7",
            message="عندي شكوى",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.intent == "complaint"
    
    @pytest.mark.asyncio
    async def test_intent_detection_other(self, test_agent):
        """اختبار كشف نية أخرى"""
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_8",
            message="السلام عليكم",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.intent == "other"


class TestDBContextLoading:
    """اختبارات جلب معلومات من قاعدة البيانات"""
    
    @pytest.mark.asyncio
    async def test_db_context_loading_doctors(self, test_agent, test_db, sample_doctor):
        """اختبار جلب معلومات الأطباء"""
        from unittest.mock import AsyncMock
        
        # Mock للـ LLM ليرجع رد يحتوي على معلومات الطبيب
        async def mock_chat(messages, **kwargs):
            system_prompt = messages[0]["content"] if messages else ""
            if "د. محمد العلي" in system_prompt or "doctor" in system_prompt.lower() or "طبيب" in system_prompt.lower():
                return f"عندنا طبيب {sample_doctor.name} متخصص في {sample_doctor.specialty}"
            return "أهلاً وسهلاً! الحمد لله بخير. وش اللي أقدر أساعدك فيه اليوم؟"
        
        test_agent.llm_client.chat = AsyncMock(side_effect=mock_chat)
        
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_9",
            message="وش الأطباء اللي عندكم؟",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.db_context_used is True
        assert sample_doctor.name in output.reply_text or "طبيب" in output.reply_text.lower()
    
    @pytest.mark.asyncio
    async def test_db_context_loading_services(self, test_agent, test_db, sample_service):
        """اختبار جلب معلومات الخدمات"""
        from unittest.mock import AsyncMock
        
        # Mock للـ LLM ليرجع رد يحتوي على معلومات الخدمة
        async def mock_chat(messages, **kwargs):
            system_prompt = messages[0]["content"] if messages else ""
            if sample_service.name in system_prompt or "خدم" in system_prompt.lower() or "service" in system_prompt.lower():
                return f"عندنا خدمة {sample_service.name} بسعر {sample_service.base_price} ريال"
            return "أهلاً وسهلاً! الحمد لله بخير. وش اللي أقدر أساعدك فيه اليوم؟"
        
        test_agent.llm_client.chat = AsyncMock(side_effect=mock_chat)
        
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_10",
            message="وش الخدمات المتاحة؟",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.db_context_used is True
        assert sample_service.name in output.reply_text or "خدم" in output.reply_text.lower()
    
    @pytest.mark.asyncio
    async def test_db_context_loading_branches(self, test_agent, test_db, sample_branch):
        """اختبار جلب معلومات الفروع"""
        from unittest.mock import AsyncMock
        
        # Mock للـ LLM ليرجع رد يحتوي على معلومات الفرع
        async def mock_chat(messages, **kwargs):
            system_prompt = messages[0]["content"] if messages else ""
            if sample_branch.name in system_prompt or "فرع" in system_prompt.lower() or "branch" in system_prompt.lower():
                return f"عندنا فرع {sample_branch.name} في {sample_branch.city} - {sample_branch.address}"
            return "أهلاً وسهلاً! الحمد لله بخير. وش اللي أقدر أساعدك فيه اليوم؟"
        
        test_agent.llm_client.chat = AsyncMock(side_effect=mock_chat)
        
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_11",
            message="وين فروعكم؟",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.db_context_used is True
        assert sample_branch.name in output.reply_text or "فرع" in output.reply_text.lower()
    
    @pytest.mark.asyncio
    async def test_db_context_loading_offers(self, test_agent, test_db, sample_offer):
        """اختبار جلب معلومات العروض"""
        from unittest.mock import AsyncMock
        
        # Mock للـ LLM ليرجع رد يحتوي على معلومات العرض
        async def mock_chat(messages, **kwargs):
            system_prompt = messages[0]["content"] if messages else ""
            if sample_offer.title in system_prompt or "عرض" in system_prompt.lower() or "offer" in system_prompt.lower():
                return f"عندنا عرض: {sample_offer.title} - {sample_offer.description}"
            return "أهلاً وسهلاً! الحمد لله بخير. وش اللي أقدر أساعدك فيه اليوم؟"
        
        test_agent.llm_client.chat = AsyncMock(side_effect=mock_chat)
        
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_12",
            message="وش العروض المتاحة؟",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        assert output.db_context_used is True
        assert sample_offer.title in output.reply_text or "عرض" in output.reply_text.lower()
    
    @pytest.mark.asyncio
    async def test_db_context_empty(self, test_agent, test_db):
        """اختبار عندما لا توجد بيانات في قاعدة البيانات"""
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_13",
            message="وش الأطباء اللي عندكم؟",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        # يجب أن يعمل حتى بدون بيانات
        assert output.reply_text is not None
        assert len(output.reply_text) > 0


class TestContextAwareness:
    """اختبارات الوعي بالسياق"""
    
    @pytest.mark.asyncio
    async def test_context_awareness(self, test_agent, test_db, sample_service):
        """اختبار الوعي بالسياق - استخدام معلومات من رسائل سابقة"""
        # رسالة أولى - ذكر خدمة
        conv_input1 = ConversationInput(
            channel="whatsapp",
            user_id="test_user_14",
            message="تبييض الأسنان",
            locale="ar-SA"
        )
        
        output1 = await test_agent.handle_message(conv_input1)
        assert output1.reply_text is not None
        
        # رسالة ثانية - سؤال غير مباشر
        conv_input2 = ConversationInput(
            channel="whatsapp",
            user_id="test_user_14",
            message="بكم؟",
            locale="ar-SA"
        )
        
        output2 = await test_agent.handle_message(conv_input2)
        assert output2.reply_text is not None
        # يجب أن يستخدم السياق من الرسالة السابقة
    
    @pytest.mark.asyncio
    async def test_conversation_history_loading(self, test_agent, test_db):
        """اختبار تحميل تاريخ المحادثة"""
        user_id = "test_user_15"
        
        # إنشاء محادثات سابقة
        now = datetime.now()
        conv1 = Conversation(
            user_id=user_id,
            channel="whatsapp",
            user_message="مرحباً",
            bot_reply="أهلاً وسهلاً",
            intent="other",
            db_context_used=False,
            unrecognized=False,
            needs_handoff=False,
            created_at=now,
            updated_at=now
        )
        test_db.add(conv1)
        test_db.commit()
        
        # رسالة جديدة
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id=user_id,
            message="وش الخدمات؟",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        # يجب أن يتم تحميل التاريخ
        assert output.reply_text is not None
        
        # التحقق من وجود محادثة جديدة
        conversations = test_db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).all()
        assert len(conversations) >= 2


class TestConversationSaving:
    """اختبارات حفظ المحادثات"""
    
    @pytest.mark.asyncio
    async def test_conversation_saving(self, test_agent, test_db):
        """اختبار حفظ المحادثة في قاعدة البيانات"""
        user_id = "test_user_16"
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id=user_id,
            message="مرحباً",
            locale="ar-SA"
        )
        
        output = await test_agent.handle_message(conv_input)
        
        # التحقق من حفظ المحادثة
        conversation = test_db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.channel == "whatsapp"
        ).order_by(Conversation.created_at.desc()).first()
        
        assert conversation is not None
        assert conversation.user_message == conv_input.message
        assert conversation.bot_reply == output.reply_text
        assert conversation.intent == output.intent
    
    @pytest.mark.asyncio
    async def test_multiple_conversations_same_user(self, test_agent, test_db):
        """اختبار محادثات متعددة لنفس المستخدم"""
        user_id = "test_user_17"
        
        # محادثة أولى
        conv_input1 = ConversationInput(
            channel="whatsapp",
            user_id=user_id,
            message="مرحباً",
            locale="ar-SA"
        )
        await test_agent.handle_message(conv_input1)
        
        # محادثة ثانية
        conv_input2 = ConversationInput(
            channel="whatsapp",
            user_id=user_id,
            message="وش الخدمات؟",
            locale="ar-SA"
        )
        await test_agent.handle_message(conv_input2)
        
        # التحقق من وجود محادثتين على الأقل (قد تكون هناك محادثات من اختبارات سابقة)
        conversations = test_db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).all()
        
        assert len(conversations) >= 2

