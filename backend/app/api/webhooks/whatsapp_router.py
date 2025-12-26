"""
WhatsApp webhook router
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.db.models import Conversation, UnansweredQuestion, PendingHandoff
from app.core.llm_client import LLMClient
from app.core.agent import ChatAgent
from app.integrations import whatsapp as whatsapp_integration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp"])


def get_agent(
    db: Session = Depends(get_db)
) -> ChatAgent:
    """Dependency للحصول على ChatAgent المبسط"""
    llm_client = LLMClient()
    return ChatAgent(
        llm_client=llm_client,
        db_session=db
    )


@router.get("/")
async def verify_webhook(request: Request):
    """Webhook verification for WhatsApp (GET)"""
    challenge = whatsapp_integration.verify_webhook(request)
    if challenge:
        return PlainTextResponse(challenge)
    return Response(status_code=403)


@router.post("/")
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db),
    agent: ChatAgent = Depends(get_agent)
):
    """Handle incoming WhatsApp messages (POST)"""
    try:
        payload_data = await request.json()
        logger.info(f"📨 Received WhatsApp webhook payload")
        
        # التحقق من صحة payload باستخدام Pydantic
        try:
            from app.api.webhooks.schemas import WhatsAppWebhookPayload
            validated_payload = WhatsAppWebhookPayload(**payload_data)
            logger.info("✅ Payload validation successful")
        except Exception as validation_error:
            logger.warning(f"❌ Invalid webhook payload: {str(validation_error)}")
            logger.debug(f"Payload data: {payload_data}")
            return {"status": "error", "message": "Invalid webhook payload format"}
        
        # تحليل الرسالة الواردة
        parsed_data = whatsapp_integration.parse_incoming(payload_data)
        
        if not parsed_data:
            # ليست رسالة نصية أو لا يمكن تحليلها
            logger.info("⚠️ Message ignored - not a text message or cannot be parsed")
            return {"status": "ignored"}
        
        logger.info(f"✅ Parsed message: user_id={parsed_data['user_id']}, message={parsed_data['message'][:50]}")
        
        # إنشاء ConversationInput
        from app.core.models import ConversationInput
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id=parsed_data["user_id"],
            message=parsed_data["message"],
            locale=parsed_data.get("locale", "ar-SA")
        )
        
        # معالجة الرسالة بواسطة الوكيل
        logger.info("🤖 Processing message with agent...")
        agent_output = await agent.handle_message(conv_input)
        logger.info(f"✅ Agent response generated: {agent_output.reply_text[:50]}")
        
        # إرسال الرد
        logger.info(f"📤 Sending reply to {conv_input.user_id}...")
        send_result = await whatsapp_integration.send_message(
            to=conv_input.user_id,
            text=agent_output.reply_text
        )
        
        if send_result.get("success"):
            logger.info(f"✅ Message sent successfully: {send_result.get('message_id')}")
        else:
            error_msg = send_result.get("error", "Unknown error")
            error_code = send_result.get("error_code", "UNKNOWN")
            logger.error(f"❌ Failed to send message: {error_msg} (code: {error_code})")
            # لا نعيد الخطأ للعميل، فقط نسجله
        
        # المحادثة تم حفظها بالفعل في agent.handle_message
        # نحتاج فقط للحصول على آخر محادثة للـ ID
        conversation = db.query(Conversation)\
            .filter(
                Conversation.user_id == conv_input.user_id,
                Conversation.channel == conv_input.channel
            )\
            .order_by(desc(Conversation.created_at))\
            .first()
        
        if conversation:
            # إذا كانت الرسالة غير مفهومة، نسجلها في UnansweredQuestion
            if agent_output.unrecognized:
                unanswered = UnansweredQuestion(
                    user_id=conv_input.user_id,
                    channel=conv_input.channel,
                    message_text=conv_input.message,
                    conversation_id=conversation.id
                )
                db.add(unanswered)
            
            # إذا كانت المحادثة تحتاج تحويل لموظف، نسجلها في PendingHandoff
            if agent_output.needs_handoff:
                handoff = PendingHandoff(
                    user_id=conv_input.user_id,
                    channel=conv_input.channel,
                    conversation_id=conversation.id,
                    last_message=conv_input.message,
                    status="open"
                )
                db.add(handoff)
            
            db.commit()
            return {"status": "ok", "message_id": str(conversation.id)}
        else:
            return {"status": "ok", "message": "conversation saved"}
        
    except Exception as e:
        logger.error(f"خطأ في معالجة رسالة WhatsApp: {str(e)}", exc_info=True)
        db.rollback()
        return {"status": "error", "message": str(e)}

