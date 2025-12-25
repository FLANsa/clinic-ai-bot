"""
نموذج الأسئلة الشائعة - جدول faqs
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class FAQ(Base):
    """نموذج السؤال الشائع"""
    __tablename__ = "faqs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف السؤال")
    question = Column(Text, nullable=False, comment="السؤال")
    answer = Column(Text, nullable=False, comment="الإجابة")
    tags = Column(JSON, nullable=True, comment="الوسوم (JSON array)")
    is_active = Column(Boolean, default=True, comment="هل السؤال نشط؟")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")
