"""
نموذج المحادثات - جدول conversations
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, Float, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Conversation(Base):
    """نموذج المحادثة - يمثل سجل محادثة مع البوت"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف المحادثة")
    user_id = Column(String, nullable=False, index=True, comment="معرف المستخدم")
    channel = Column(String, nullable=False, comment="قناة الاتصال (مثال: whatsapp, instagram, google_maps)")
    user_message = Column(Text, nullable=False, comment="رسالة المستخدم")
    bot_reply = Column(Text, nullable=False, comment="رد البوت")
    intent = Column(String, nullable=True, comment="النية المكتشفة")
    db_context_used = Column(Boolean, default=False, comment="هل تم استخدام معلومات من قاعدة البيانات")
    unrecognized = Column(Boolean, default=False, comment="هل الرسالة لم تُفهم؟")
    needs_handoff = Column(Boolean, default=False, comment="هل تحتاج المحادثة لتحويل لموظف بشري؟")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ ووقت الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ ووقت آخر تحديث")
