"""
Unit tests for ChatAgent
"""
import pytest
from app.core.models import ConversationInput
from app.core.agent import ChatAgent


@pytest.mark.asyncio
async def test_agent_handle_message(chat_agent, db_session):
    """Test agent message handling"""
    conv_input = ConversationInput(
        channel="whatsapp",
        user_id="1234567890",
        message="مرحباً",
        locale="ar-SA"
    )
    
    output = await chat_agent.handle_message(conv_input)
    assert output.reply_text is not None
    assert len(output.reply_text) > 0
    assert output.intent is not None


@pytest.mark.asyncio
async def test_agent_handoff_detection(chat_agent, db_session):
    """Test agent handoff detection for complaints"""
    conv_input = ConversationInput(
        channel="whatsapp",
        user_id="1234567890",
        message="الخدمة كانت سيئة جداً",
        locale="ar-SA"
    )
    
    output = await chat_agent.handle_message(conv_input)
    assert output.needs_handoff is True
    assert output.intent == "complaint"

