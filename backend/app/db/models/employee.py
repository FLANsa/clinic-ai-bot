"""
نموذج الموظفين - جدول employees
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, ForeignKey, Float, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Employee(Base):
    """نموذج الموظف - يمثل موظفاً في عيادات عادل كير"""
    __tablename__ = "employees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف الموظف")
    full_name = Column(String, nullable=False, index=True, comment="الاسم الكامل")
    position = Column(String, nullable=False, index=True, comment="الوظيفة (receptionist, nurse, admin, etc.)")
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True, comment="معرف الفرع")
    phone_number = Column(String, nullable=True, comment="رقم الهاتف")
    email = Column(String, nullable=True, comment="البريد الإلكتروني")
    hire_date = Column(Date, nullable=True, comment="تاريخ التوظيف")
    salary = Column(Float, nullable=True, comment="الراتب")
    notes = Column(Text, nullable=True, comment="ملاحظات")
    is_active = Column(Boolean, default=True, comment="هل الموظف نشط؟")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")

