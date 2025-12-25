"""
نموذج مقاطع الوثائق - جدول document_chunks
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class DocumentChunk(Base):
    """نموذج مقطع الوثيقة - يمثل مقطعاً من وثيقة في نظام RAG"""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف المقطع")
    document_id = Column(UUID(as_uuid=True), ForeignKey("document_sources.id"), nullable=False, comment="معرف الوثيقة")
    chunk_index = Column(Integer, nullable=False, comment="فهرس المقطع في الوثيقة")
    text = Column(Text, nullable=False, comment="نص المقطع")
    chunk_metadata = Column(JSON, nullable=True, comment="بيانات إضافية (JSON)")
    # embedding: حقل vector لـ pgvector (384 dimensions لـ sentence-transformers paraphrase-multilingual-MiniLM-L12-v2)
    # يتم تخزينه كـ JSONB مؤقتاً حتى يتم تثبيت pgvector extension
    # بعد تثبيت pgvector، يمكن تحويله إلى vector type
    embedding = Column(JSON, nullable=True, comment="متجه Embedding (JSON array) - سيتم تحويله إلى vector بعد تثبيت pgvector")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    
    # العلاقات
    document = relationship("DocumentSource", back_populates="chunks")
