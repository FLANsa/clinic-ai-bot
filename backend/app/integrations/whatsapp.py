"""
WhatsApp Business API integration
"""
import logging
from typing import Optional, Dict, Any
from fastapi import Request
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def verify_webhook(request: Request) -> Optional[str]:
    """
    Verify WhatsApp webhook
    
    Args:
        request: FastAPI Request object
    
    Returns:
        Challenge string if verification succeeds, None otherwise
    """
    try:
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        verify_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "test_token")
        
        if mode == "subscribe" and token == verify_token:
            return challenge
        else:
            return None
    except Exception as e:
        logger.error(f"Error verifying webhook: {str(e)}", exc_info=True)
        return None


def parse_incoming(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Parse incoming WhatsApp webhook payload
    
    Args:
        payload: Raw webhook payload from WhatsApp
    
    Returns:
        Dict with user_id, message, and locale, or None if not a text message
    """
    try:
        logger.debug(f"Parsing WhatsApp payload: {payload}")
        
        # WhatsApp webhook format
        entry = payload.get("entry", [])
        if not entry:
            logger.debug("No entry in payload")
            return None
        
        changes = entry[0].get("changes", [])
        if not changes:
            logger.debug("No changes in entry")
            return None
        
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            logger.debug("No messages in value")
            return None
        
        message_obj = messages[0]
        message_type = message_obj.get("type")
        
        if message_type != "text":
            logger.debug(f"Message type is not text: {message_type}")
            return None
        
        from_number = message_obj.get("from")
        message_text = message_obj.get("text", {}).get("body", "")
        
        if not from_number:
            logger.warning("No 'from' field in message")
            return None
        
        if not message_text:
            logger.warning("No message text in message")
            return None
        
        logger.info(f"✅ Successfully parsed message from {from_number}: {message_text[:50]}")
        
        return {
            "user_id": from_number,
            "message": message_text,
            "locale": "ar-SA"
        }
    except Exception as e:
        logger.error(f"Error parsing WhatsApp payload: {str(e)}", exc_info=True)
        return None


async def send_message(to: str, text: str) -> Dict[str, Any]:
    """
    Send a WhatsApp message
    
    Args:
        to: Recipient phone number
        text: Message text
    
    Returns:
        Dict with success status, message_id, and any error details
    """
    try:
        import httpx
        
        phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        access_token = settings.WHATSAPP_ACCESS_TOKEN
        
        if not phone_number_id or not access_token:
            logger.warning("WhatsApp credentials not configured")
            return {
                "success": False,
                "error": "WhatsApp credentials not configured",
                "error_code": "NO_CREDENTIALS"
            }
        
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": text
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                message_id = response_data.get("messages", [{}])[0].get("id")
                logger.info(f"Message sent to {to}, message_id: {message_id}")
                return {
                    "success": True,
                    "message_id": message_id,
                    "response": response_data
                }
            else:
                error_info = response_data.get("error", {})
                error_message = error_info.get("message", "Unknown error")
                error_code = error_info.get("code", 0)
                error_subcode = error_info.get("error_subcode", 0)
                
                logger.error(f"WhatsApp API error: {error_message} (code: {error_code})")
                return {
                    "success": False,
                    "error": error_message,
                    "error_code": error_code,
                    "error_subcode": error_subcode,
                    "status_code": response.status_code,
                    "response": response_data
                }
            
    except httpx.TimeoutException:
        logger.error("WhatsApp API timeout")
        return {
            "success": False,
            "error": "Connection timeout",
            "error_code": "TIMEOUT"
        }
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_code": "EXCEPTION"
        }
