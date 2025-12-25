"""
نماذج البيانات للـ Agent - Conversation Input/Output
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class ConversationInput(BaseModel):
    """نموذج إدخال المحادثة"""
    channel: str = Field(..., description="قناة الاتصال: whatsapp, instagram, tiktok, google_maps")
    user_id: str = Field(..., description="معرف المستخدم الفريد")
    message: str = Field(..., description="نص الرسالة من المستخدم")
    locale: str = Field(default="ar-SA", description="اللغة/المنطقة (ar-SA)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="سياق إضافي (مثل معلومات المستخدم السابقة)")


class AgentOutput(BaseModel):
    """نموذج إخراج الوكيل - الرد والنتائج"""
    reply_text: str = Field(..., description="نص الرد")
    intent: Optional[str] = Field(
        default=None,
        description="نية المحادثة (اختياري): faq, booking, branch_info, service_info, doctor_info, price, complaint, policy_info, other"
    )
    needs_handoff: bool = Field(
        default=False,
        description="هل تحتاج المحادثة إلى تحويل لموظف بشري"
    )
    unrecognized: bool = Field(
        default=False,
        description="هل كانت الرسالة غير مفهومة"
    )
    db_context_used: bool = Field(
        default=False,
        description="هل تم استخدام معلومات من قاعدة البيانات"
    )


class ConversationMessage(BaseModel):
    """نموذج رسالة في المحادثة"""
    role: str = Field(..., description="دور المرسل: user أو assistant")
    content: str = Field(..., description="نص الرسالة")


class ConversationHistory(BaseModel):
    """نموذج تاريخ المحادثة"""
    messages: List[ConversationMessage] = Field(default_factory=list, description="قائمة الرسائل")
    total_messages: int = Field(default=0, description="إجمالي عدد الرسائل")


