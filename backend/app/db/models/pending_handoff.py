"""
نموذج التحويلات المعلقة - جدول pending_handoffs
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class PendingHandoff(Base):
    """نموذج التحويل المعلق"""
    __tablename__ = "pending_handoffs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف التحويل")
    user_id = Column(String, nullable=False, comment="معرف المستخدم")
    channel = Column(String, nullable=False, comment="قناة الاتصال")
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, comment="معرف المحادثة")
    last_message = Column(Text, nullable=True, comment="آخر رسالة")
    status = Column(String, default="open", comment="حالة التحويل (open, closed)")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")
