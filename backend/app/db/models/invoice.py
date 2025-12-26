"""
نموذج الفواتير - جدول invoices
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, ForeignKey, Float, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Invoice(Base):
    """نموذج الفاتورة - يمثل فاتورة في عيادات عادل كير"""
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف الفاتورة")
    invoice_number = Column(String, nullable=False, unique=True, index=True, comment="رقم الفاتورة")
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True, comment="معرف المريض")
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True, comment="معرف الموعد المرتبط")
    invoice_date = Column(Date, nullable=False, index=True, comment="تاريخ الفاتورة")
    subtotal = Column(Float, nullable=False, default=0.0, comment="المجموع الفرعي")
    discount = Column(Float, nullable=True, default=0.0, comment="الخصم")
    tax = Column(Float, nullable=True, default=0.0, comment="الضريبة")
    total_amount = Column(Float, nullable=False, comment="المبلغ الإجمالي")
    payment_status = Column(String, default="unpaid", index=True, comment="حالة الدفع (paid, unpaid, partial)")
    payment_method = Column(String, nullable=True, comment="طريقة الدفع (cash, card, bank_transfer)")
    notes = Column(Text, nullable=True, comment="ملاحظات")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")

