"""
Doctors admin router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.session import get_db
from app.db.models import Doctor
from app.middleware.auth import verify_api_key


router = APIRouter(prefix="/admin/doctors", tags=["Admin - Doctors"])


class DoctorCreate(BaseModel):
    name: str
    specialty: str
    branch_id: UUID
    license_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    working_hours: Optional[dict] = None
    qualifications: Optional[str] = None
    experience_years: Optional[str] = None
    is_active: bool = True


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    branch_id: Optional[UUID] = None
    license_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    working_hours: Optional[dict] = None
    qualifications: Optional[str] = None
    experience_years: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_doctors(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """قائمة بجميع الأطباء"""
    doctors = db.query(Doctor).all()
    return {
        "doctors": [
            {
                "id": str(doctor.id),
                "name": doctor.name,
                "specialty": doctor.specialty,
                "bio": doctor.bio,
                "is_active": doctor.is_active,
                "created_at": doctor.created_at.isoformat(),
                "updated_at": doctor.updated_at.isoformat()
            }
            for doctor in doctors
        ]
    }


@router.post("/")
async def create_doctor(
    doctor_data: DoctorCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """إنشاء طبيب جديد"""
    doctor = Doctor(**doctor_data.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return {
        "id": str(doctor.id),
        "name": doctor.name,
        "specialty": doctor.specialty,
        "branch_id": str(doctor.branch_id),
        "license_number": doctor.license_number,
        "phone_number": doctor.phone_number,
        "email": doctor.email,
        "bio": doctor.bio,
        "working_hours": doctor.working_hours,
        "qualifications": doctor.qualifications,
        "experience_years": doctor.experience_years,
        "is_active": doctor.is_active
    }


@router.put("/{doctor_id}")
async def update_doctor(
    doctor_id: UUID,
    doctor_data: DoctorUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """تحديث طبيب"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="الطبيب غير موجود")
    
    update_data = doctor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doctor, field, value)
    
    doctor.updated_at = datetime.now()
    db.commit()
    db.refresh(doctor)
    
    return {
        "id": str(doctor.id),
        "name": doctor.name,
        "specialty": doctor.specialty,
        "branch_id": str(doctor.branch_id),
        "license_number": doctor.license_number,
        "phone_number": doctor.phone_number,
        "email": doctor.email,
        "bio": doctor.bio,
        "working_hours": doctor.working_hours,
        "qualifications": doctor.qualifications,
        "experience_years": doctor.experience_years,
        "is_active": doctor.is_active,
        "updated_at": doctor.updated_at.isoformat() if doctor.updated_at else None
    }


@router.delete("/{doctor_id}")
async def delete_doctor(
    doctor_id: UUID,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """حذف طبيب"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="الطبيب غير موجود")
    
    # التحقق من وجود مواعيد مرتبطة بالطبيب
    from app.db.models import Appointment
    appointments_count = db.query(Appointment).filter(Appointment.doctor_id == doctor_id).count()
    if appointments_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"لا يمكن حذف الطبيب لأنه لديه {appointments_count} موعد. يرجى حذف المواعيد أولاً."
        )
    
    db.delete(doctor)
    db.commit()
    
    return {"message": "تم حذف الطبيب بنجاح", "id": str(doctor_id)}

