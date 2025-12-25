"""
Pydantic schemas للتحقق من صحة webhook payloads
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any


class WhatsAppWebhookEntryChangeValueMessage(BaseModel):
    """نموذج رسالة WhatsApp"""
    from_: str = Field(..., alias="from")
    type: str
    text: Optional[Dict[str, str]] = None
    
    @validator("type")
    def validate_message_type(cls, v):
        """التحقق من نوع الرسالة - نسمح فقط بالنصوص حالياً"""
        if v != "text":
            raise ValueError("Only text messages are supported")
        return v
    
    @validator("text")
    def validate_text_content(cls, v):
        """التحقق من وجود نص الرسالة"""
        if v is None or not v.get("body"):
            raise ValueError("Text message must have body")
        return v


class WhatsAppWebhookEntryChangeValue(BaseModel):
    """نموذج value في webhook entry"""
    messages: Optional[List[WhatsAppWebhookEntryChangeValueMessage]] = None


class WhatsAppWebhookEntryChange(BaseModel):
    """نموذج change في webhook entry"""
    value: WhatsAppWebhookEntryChangeValue


class WhatsAppWebhookEntry(BaseModel):
    """نموذج entry في webhook payload"""
    changes: List[WhatsAppWebhookEntryChange]


class WhatsAppWebhookPayload(BaseModel):
    """نموذج كامل لـ WhatsApp webhook payload"""
    object: str = Field(..., description="Object type (should be 'whatsapp_business_account')")
    entry: List[WhatsAppWebhookEntry]
    
    @validator("object")
    def validate_object(cls, v):
        """التحقق من نوع object"""
        if v != "whatsapp_business_account":
            raise ValueError("Invalid object type")
        return v


class InstagramWebhookPayload(BaseModel):
    """نموذج لـ Instagram webhook payload (مشابه لـ WhatsApp)"""
    object: str
    entry: List[Dict[str, Any]]


class TikTokWebhookPayload(BaseModel):
    """نموذج لـ TikTok webhook payload"""
    object: str
    entry: List[Dict[str, Any]]

