"""
نموذج مصادر الوثائق - جدول document_sources
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class DocumentSource(Base):
    """نموذج مصدر الوثيقة - يمثل وثيقة في نظام RAG"""
    __tablename__ = "document_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف الوثيقة")
    title = Column(String, nullable=False, comment="عنوان الوثيقة")
    source_type = Column(String, nullable=False, comment="نوع المصدر (pdf, text, url, etc.)")
    tags = Column(JSON, nullable=True, comment="الوسوم (JSON array)")
    language = Column(String, default="ar", comment="لغة الوثيقة")
    file_path = Column(Text, nullable=True, comment="مسار الملف")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")
    
    # العلاقات
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
