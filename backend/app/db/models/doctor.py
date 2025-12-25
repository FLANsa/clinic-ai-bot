"""
نموذج الأطباء - جدول doctors
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Doctor(Base):
    """نموذج الطبيب - يمثل طبيباً في العيادة"""
    __tablename__ = "doctors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="معرف الطبيب")
    name = Column(String, nullable=False, index=True, comment="اسم الطبيب")
    specialty = Column(String, nullable=True, comment="تخصص الطبيب")
    branch_id = Column(UUID(as_uuid=True), nullable=True, comment="معرف الفرع")
    bio = Column(Text, nullable=True, comment="نبذة عن الطبيب")
    is_active = Column(Boolean, default=True, comment="هل الطبيب نشط؟")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="تاريخ الإنشاء")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="تاريخ آخر تحديث")
