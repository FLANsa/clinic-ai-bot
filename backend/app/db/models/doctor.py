"""
نموذج الأطباء - جدول doctors
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Doctor(Base):
    """نموذج الطبيب - يمثل طبيباً في عيادات عادل كير"""
    __tablename__ = "doctors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف الطبيب")
    name = Column(String, nullable=False, index=True, comment="اسم الطبيب")
    specialty = Column(String, nullable=True, index=True, comment="تخصص الطبيب")
    license_number = Column(String, nullable=True, unique=True, comment="رقم الترخيص")
    branch_id = Column(UUID(as_uuid=True), nullable=True, comment="معرف الفرع")
    phone_number = Column(String, nullable=True, comment="رقم الهاتف")
    email = Column(String, nullable=True, comment="البريد الإلكتروني")
    bio = Column(Text, nullable=True, comment="نبذة عن الطبيب")
    working_hours = Column(JSON, nullable=True, comment="ساعات العمل (JSON)")
    qualifications = Column(Text, nullable=True, comment="المؤهلات العلمية")
    experience_years = Column(String, nullable=True, comment="سنوات الخبرة")
    is_active = Column(Boolean, default=True, comment="هل الطبيب نشط؟")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")
