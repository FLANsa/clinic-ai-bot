"""
نموذج العروض - جدول offers
"""
from sqlalchemy import Column, String, Text, Boolean, Float, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Offer(Base):
    """نموذج العرض - يمثل عرضاً خاصاً تقدمه العيادة"""
    __tablename__ = "offers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف العرض")
    title = Column(String, nullable=False, index=True, comment="عنوان العرض")
    description = Column(Text, nullable=True, comment="وصف العرض")
    discount_type = Column(String, nullable=True, comment="نوع الخصم (مثال: percentage, fixed_amount)")
    discount_value = Column(Float, nullable=True, comment="قيمة الخصم")
    start_date = Column(DateTime, nullable=True, comment="تاريخ بداية العرض")
    end_date = Column(DateTime, nullable=True, comment="تاريخ انتهاء العرض")
    related_service_id = Column(UUID(as_uuid=True), ForeignKey('services.id'), nullable=True, comment="معرف الخدمة المرتبطة")
    is_active = Column(Boolean, default=True, comment="هل العرض نشط؟")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")
