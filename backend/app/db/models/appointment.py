"""
نموذج المواعيد - جدول appointments
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Appointment(Base):
    """نموذج الموعد - يمثل موعداً في عيادات عادل كير"""
    __tablename__ = "appointments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف الموعد")
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True, comment="معرف المريض")
    patient_name = Column(String, nullable=True, comment="اسم المريض (إذا لم يكن مسجلاً)")
    phone = Column(String, nullable=False, comment="رقم الهاتف")
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, comment="معرف الفرع")
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=True, comment="معرف الطبيب")
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False, comment="معرف الخدمة")
    datetime = Column(DateTime, nullable=False, index=True, comment="تاريخ ووقت الموعد")
    channel = Column(String, nullable=False, comment="قناة الحجز (whatsapp, instagram, etc.)")
    status = Column(String, default="pending", index=True, comment="حالة الموعد (pending, confirmed, completed, cancelled)")
    appointment_type = Column(String, nullable=True, comment="نوع الموعد (consultation, follow_up, emergency)")
    notes = Column(Text, nullable=True, comment="ملاحظات")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")
