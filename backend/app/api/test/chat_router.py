"""
Test Chat Endpoint - للاختبار المباشر للشات بوت
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.db.session import get_db
from app.core.llm_client import LLMClient
from app.core.agent import ChatAgent
from app.core.models import ConversationInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Test"])


class ChatRequest(BaseModel):
    """نموذج طلب المحادثة"""
    message: str
    user_id: Optional[str] = "test_user"
    channel: Optional[str] = "whatsapp"  # استخدام whatsapp كقناة افتراضية


class ChatResponse(BaseModel):
    """نموذج رد المحادثة"""
    reply: str
    intent: Optional[str] = None
    unrecognized: bool = False
    needs_handoff: bool = False
    db_context_used: bool = False


def get_test_agent(
    db: Session = Depends(get_db)
) -> ChatAgent:
    """Dependency للحصول على ChatAgent للاختبار"""
    llm_client = LLMClient()
    return ChatAgent(
        llm_client=llm_client,
        db_session=db
    )


@router.post("/chat", response_model=ChatResponse)
async def test_chat(
    request: ChatRequest,
    agent: ChatAgent = Depends(get_test_agent),
    db: Session = Depends(get_db)
):
    """
    اختبار الشات بوت مباشرة
    
    Args:
        request: طلب المحادثة (يحتوي على message)
        agent: ChatAgent instance
        db: database session
    
    Returns:
        ChatResponse: رد البوت مع معلومات إضافية
    """
    try:
        # إنشاء ConversationInput
        # استخدام 'whatsapp' كقناة افتراضية للاختبار
        conv_input = ConversationInput(
            channel=request.channel if request.channel in ['whatsapp', 'instagram', 'tiktok', 'google_maps'] else 'whatsapp',
            user_id=request.user_id,
            message=request.message,
            locale="ar-SA"
        )
        
        # معالجة الرسالة
        output = await agent.handle_message(conv_input)
        
        return ChatResponse(
            reply=output.reply_text,
            intent=output.intent,
            unrecognized=output.unrecognized if hasattr(output, 'unrecognized') else False,
            needs_handoff=output.needs_handoff if hasattr(output, 'needs_handoff') else False,
            db_context_used=output.db_context_used if hasattr(output, 'db_context_used') else False
        )
    except Exception as e:
        logger.error(f"Error in test chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"خطأ في معالجة الرسالة: {str(e)}")

