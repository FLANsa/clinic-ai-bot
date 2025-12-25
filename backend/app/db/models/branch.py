"""
نموذج الفروع - جدول branches
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Branch(Base):
    """نموذج الفرع - يمثل فرعاً للعيادة"""
    __tablename__ = "branches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف الفرع")
    name = Column(String, nullable=False, unique=True, index=True, comment="اسم الفرع")
    city = Column(String, nullable=True, comment="المدينة")
    address = Column(Text, nullable=True, comment="عنوان الفرع")
    location_url = Column(Text, nullable=True, comment="رابط الموقع على الخريطة")
    phone = Column(String, nullable=True, comment="رقم هاتف الفرع")
    working_hours = Column(JSON, nullable=True, comment="ساعات العمل (JSON)")
    is_active = Column(Boolean, default=True, comment="هل الفرع نشط؟")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")
