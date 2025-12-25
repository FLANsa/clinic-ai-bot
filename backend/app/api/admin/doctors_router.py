"""
Doctors admin router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from app.db.session import get_db
from app.db.models import Doctor
from app.middleware.auth import verify_api_key


router = APIRouter(prefix="/admin/doctors", tags=["Admin - Doctors"])


class DoctorCreate(BaseModel):
    name: str
    specialty: str
    branch_id: UUID
    bio: Optional[str] = None
    is_active: bool = True


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
        "bio": doctor.bio,
        "is_active": doctor.is_active
    }

