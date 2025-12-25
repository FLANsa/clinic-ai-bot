"""
نموذج الأسئلة غير المجابة - جدول unanswered_questions
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class UnansweredQuestion(Base):
    """نموذج السؤال غير المجاب"""
    __tablename__ = "unanswered_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف السؤال")
    user_id = Column(String, nullable=False, comment="معرف المستخدم")
    channel = Column(String, nullable=False, comment="قناة الاتصال")
    message_text = Column(Text, nullable=False, comment="نص الرسالة")
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, comment="معرف المحادثة")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
