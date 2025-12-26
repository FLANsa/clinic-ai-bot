"""
نموذج العلاجات - جدول treatments
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Treatment(Base):
    """نموذج العلاج - يمثل علاجاً تم إجراؤه في عيادات عادل كير"""
    __tablename__ = "treatments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف العلاج")
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True, comment="معرف المريض")
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True, comment="معرف الموعد المرتبط")
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False, comment="معرف الطبيب")
    treatment_date = Column(Date, nullable=False, index=True, comment="تاريخ العلاج")
    description = Column(Text, nullable=False, comment="وصف العلاج")
    diagnosis = Column(Text, nullable=True, comment="التشخيص")
    prescription = Column(Text, nullable=True, comment="الوصفة الطبية")
    notes = Column(Text, nullable=True, comment="ملاحظات إضافية")
    follow_up_required = Column(Boolean, default=False, comment="هل يحتاج متابعة؟")
    follow_up_date = Column(Date, nullable=True, comment="تاريخ المتابعة")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")

