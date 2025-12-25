"""
Unit tests for intent detection
"""
import pytest
from app.core.intents import detect_intent, IntentResult
from app.core.models import ConversationInput
from app.core.llm_client import LLMClient


@pytest.mark.asyncio
async def test_detect_intent_booking():
    """Test intent detection for booking"""
    llm_client = LLMClient()
    conv_input = ConversationInput(
        channel="whatsapp",
        user_id="1234567890",
        message="أريد حجز موعد",
        locale="ar-SA"
    )
    
    result: IntentResult = await detect_intent(llm_client, conv_input)
    assert result.intent == "booking"
    assert result.confidence > 0.5


@pytest.mark.asyncio
async def test_detect_intent_faq():
    """Test intent detection for FAQ"""
    llm_client = LLMClient()
    conv_input = ConversationInput(
        channel="whatsapp",
        user_id="1234567890",
        message="ما هي أوقات العمل؟",
        locale="ar-SA"
    )
    
    result: IntentResult = await detect_intent(llm_client, conv_input)
    assert result.intent == "faq"
    assert result.confidence > 0.5


@pytest.mark.asyncio
async def test_detect_intent_complaint():
    """Test intent detection for complaint"""
    llm_client = LLMClient()
    conv_input = ConversationInput(
        channel="whatsapp",
        user_id="1234567890",
        message="لدي شكوى على الخدمة",
        locale="ar-SA"
    )
    
    result: IntentResult = await detect_intent(llm_client, conv_input)
    assert result.intent == "complaint"
    assert result.confidence > 0.6

