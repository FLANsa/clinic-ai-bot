"""
نموذج المرضى - جدول patients
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Patient(Base):
    """نموذج المريض - يمثل مريضاً في عيادات عادل كير"""
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف المريض")
    full_name = Column(String, nullable=False, index=True, comment="الاسم الكامل")
    date_of_birth = Column(Date, nullable=True, comment="تاريخ الميلاد")
    gender = Column(String, nullable=True, comment="الجنس (male, female)")
    address = Column(Text, nullable=True, comment="العنوان")
    phone_number = Column(String, nullable=False, index=True, comment="رقم الهاتف")
    email = Column(String, nullable=True, comment="البريد الإلكتروني")
    medical_history = Column(Text, nullable=True, comment="التاريخ الطبي")
    emergency_contact_name = Column(String, nullable=True, comment="اسم جهة الاتصال في الطوارئ")
    emergency_contact_phone = Column(String, nullable=True, comment="رقم جهة الاتصال في الطوارئ")
    notes = Column(Text, nullable=True, comment="ملاحظات إضافية")
    is_active = Column(Boolean, default=True, comment="هل المريض نشط؟")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")

