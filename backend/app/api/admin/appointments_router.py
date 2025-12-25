"""
Appointments admin router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.session import get_db
from app.db.models import Appointment
from app.middleware.auth import verify_api_key


router = APIRouter(prefix="/admin/appointments", tags=["Admin - Appointments"])


class AppointmentCreate(BaseModel):
    patient_name: str
    phone: str
    branch_id: UUID
    doctor_id: Optional[UUID] = None
    service_id: UUID
    datetime: datetime
    channel: str
    status: str = "pending"
    notes: Optional[str] = None


@router.get("/")
async def list_appointments(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """قائمة بجميع المواعيد"""
    appointments = db.query(Appointment).all()
    return {
        "appointments": [
            {
                "id": str(appointment.id),
                "patient_name": appointment.patient_name,
                "phone": appointment.phone,
                "branch_id": str(appointment.branch_id),
                "doctor_id": str(appointment.doctor_id) if appointment.doctor_id else None,
                "service_id": str(appointment.service_id),
                "datetime": appointment.datetime.isoformat(),
                "channel": appointment.channel,
                "status": appointment.status,
                "notes": appointment.notes,
                "created_at": appointment.created_at.isoformat(),
                "updated_at": appointment.updated_at.isoformat()
            }
            for appointment in appointments
        ]
    }


@router.post("/")
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """إنشاء موعد جديد"""
    appointment = Appointment(**appointment_data.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return {
        "id": str(appointment.id),
        "patient_name": appointment.patient_name,
        "phone": appointment.phone,
        "branch_id": str(appointment.branch_id),
        "doctor_id": str(appointment.doctor_id) if appointment.doctor_id else None,
        "service_id": str(appointment.service_id),
        "datetime": appointment.datetime.isoformat(),
        "channel": appointment.channel,
        "status": appointment.status,
        "notes": appointment.notes
    }

