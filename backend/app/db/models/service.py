"""
نموذج الخدمات - جدول services
"""
from sqlalchemy import Column, String, Text, Boolean, Float, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Service(Base):
    """نموذج الخدمة - يمثل خدمة تقدمها العيادة"""
    __tablename__ = "services"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف الخدمة")
    name = Column(String, nullable=False, unique=True, index=True, comment="اسم الخدمة")
    description = Column(Text, nullable=True, comment="وصف الخدمة")
    base_price = Column(Float, nullable=True, comment="السعر الأساسي للخدمة")
    is_active = Column(Boolean, default=True, comment="هل الخدمة نشطة؟")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")
