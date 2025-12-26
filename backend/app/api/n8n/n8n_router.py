"""
N8N Integration Router - ربط n8n مع قاعدة البيانات
Endpoints مخصصة لاستخدام n8n workflows
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel
from uuid import UUID

from app.db.session import get_db
from app.db.models import (
    Doctor, Service, Branch, Offer, FAQ, Appointment,
    Patient, Treatment, Invoice, Employee, Conversation
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/n8n", tags=["N8N Integration"])


# ==================== Models ====================

class DoctorResponse(BaseModel):
    """رد بيانات الطبيب"""
    id: str
    name: str
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    branch_id: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class ServiceResponse(BaseModel):
    """رد بيانات الخدمة"""
    id: str
    name: str
    description: Optional[str] = None
    base_price: Optional[float] = None
    is_active: bool

    class Config:
        from_attributes = True


class BranchResponse(BaseModel):
    """رد بيانات الفرع"""
    id: str
    name: str
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    working_hours: Optional[Dict[str, Any]] = None
    is_active: bool

    class Config:
        from_attributes = True


class AppointmentResponse(BaseModel):
    """رد بيانات الموعد"""
    id: str
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    phone: str
    branch_id: str
    doctor_id: Optional[str] = None
    service_id: str
    datetime: datetime
    status: str
    channel: str
    appointment_type: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    """إنشاء موعد جديد"""
    patient_name: str
    phone: str
    branch_id: UUID
    doctor_id: Optional[UUID] = None
    service_id: UUID
    datetime: datetime
    channel: str = "n8n"
    status: str = "pending"
    appointment_type: Optional[str] = None
    notes: Optional[str] = None


class PatientResponse(BaseModel):
    """رد بيانات المريض"""
    id: str
    full_name: str
    phone_number: str
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """رد بيانات المحادثة"""
    id: str
    user_id: str
    channel: str
    user_message: str
    bot_reply: str
    intent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Read Endpoints ====================

@router.get("/doctors", response_model=List[DoctorResponse])
async def get_doctors(
    active_only: bool = Query(True, description="جلب الأطباء النشطين فقط"),
    db: Session = Depends(get_db)
):
    """جلب قائمة الأطباء"""
    query = db.query(Doctor)
    if active_only:
        query = query.filter(Doctor.is_active == True)
    
    doctors = query.all()
    return [
        DoctorResponse(
            id=str(d.id),
            name=d.name,
            specialty=d.specialty,
            license_number=d.license_number,
            phone_number=d.phone_number,
            email=d.email,
            bio=d.bio,
            branch_id=str(d.branch_id) if d.branch_id else None,
            is_active=d.is_active
        )
        for d in doctors
    ]


@router.get("/services", response_model=List[ServiceResponse])
async def get_services(
    active_only: bool = Query(True, description="جلب الخدمات النشطة فقط"),
    db: Session = Depends(get_db)
):
    """جلب قائمة الخدمات"""
    query = db.query(Service)
    if active_only:
        query = query.filter(Service.is_active == True)
    
    services = query.all()
    return [
        ServiceResponse(
            id=str(s.id),
            name=s.name,
            description=s.description,
            base_price=s.base_price,
            is_active=s.is_active
        )
        for s in services
    ]


@router.get("/branches", response_model=List[BranchResponse])
async def get_branches(
    active_only: bool = Query(True, description="جلب الفروع النشطة فقط"),
    db: Session = Depends(get_db)
):
    """جلب قائمة الفروع"""
    query = db.query(Branch)
    if active_only:
        query = query.filter(Branch.is_active == True)
    
    branches = query.all()
    return [
        BranchResponse(
            id=str(b.id),
            name=b.name,
            city=b.city,
            address=b.address,
            phone=b.phone,
            working_hours=b.working_hours if isinstance(b.working_hours, dict) else None,
            is_active=b.is_active
        )
        for b in branches
    ]


@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_appointments(
    status: Optional[str] = Query(None, description="فلترة حسب الحالة"),
    from_date: Optional[date] = Query(None, description="من تاريخ"),
    to_date: Optional[date] = Query(None, description="إلى تاريخ"),
    limit: int = Query(100, description="عدد النتائج"),
    db: Session = Depends(get_db)
):
    """جلب قائمة المواعيد"""
    query = db.query(Appointment)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    if from_date:
        query = query.filter(Appointment.datetime >= datetime.combine(from_date, datetime.min.time()))
    
    if to_date:
        query = query.filter(Appointment.datetime <= datetime.combine(to_date, datetime.max.time()))
    
    appointments = query.order_by(desc(Appointment.datetime)).limit(limit).all()
    
    return [
        AppointmentResponse(
            id=str(a.id),
            patient_name=a.patient_name,
            patient_id=str(a.patient_id) if a.patient_id else None,
            phone=a.phone,
            branch_id=str(a.branch_id),
            doctor_id=str(a.doctor_id) if a.doctor_id else None,
            service_id=str(a.service_id),
            datetime=a.datetime,
            status=a.status,
            channel=a.channel,
            appointment_type=a.appointment_type,
            notes=a.notes,
            created_at=a.created_at
        )
        for a in appointments
    ]


@router.get("/patients", response_model=List[PatientResponse])
async def get_patients(
    active_only: bool = Query(True, description="جلب المرضى النشطين فقط"),
    limit: int = Query(100, description="عدد النتائج"),
    db: Session = Depends(get_db)
):
    """جلب قائمة المرضى"""
    query = db.query(Patient)
    
    if active_only:
        query = query.filter(Patient.is_active == True)
    
    patients = query.limit(limit).all()
    
    return [
        PatientResponse(
            id=str(p.id),
            full_name=p.full_name,
            phone_number=p.phone_number,
            email=p.email,
            date_of_birth=p.date_of_birth,
            gender=p.gender,
            is_active=p.is_active
        )
        for p in patients
    ]


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    channel: Optional[str] = Query(None, description="فلترة حسب القناة"),
    from_date: Optional[date] = Query(None, description="من تاريخ"),
    to_date: Optional[date] = Query(None, description="إلى تاريخ"),
    limit: int = Query(100, description="عدد النتائج"),
    db: Session = Depends(get_db)
):
    """جلب قائمة المحادثات"""
    query = db.query(Conversation)
    
    if channel:
        query = query.filter(Conversation.channel == channel)
    
    if from_date:
        query = query.filter(Conversation.created_at >= datetime.combine(from_date, datetime.min.time()))
    
    if to_date:
        query = query.filter(Conversation.created_at <= datetime.combine(to_date, datetime.max.time()))
    
    conversations = query.order_by(desc(Conversation.created_at)).limit(limit).all()
    
    return [
        ConversationResponse(
            id=str(c.id),
            user_id=c.user_id,
            channel=c.channel,
            user_message=c.user_message,
            bot_reply=c.bot_reply,
            intent=c.intent,
            created_at=c.created_at
        )
        for c in conversations
    ]


# ==================== Write Endpoints ====================

@router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db)
):
    """إنشاء موعد جديد من n8n"""
    try:
        appointment = Appointment(**appointment_data.model_dump())
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        
        return AppointmentResponse(
            id=str(appointment.id),
            patient_name=appointment.patient_name,
            patient_id=str(appointment.patient_id) if appointment.patient_id else None,
            phone=appointment.phone,
            branch_id=str(appointment.branch_id),
            doctor_id=str(appointment.doctor_id) if appointment.doctor_id else None,
            service_id=str(appointment.service_id),
            datetime=appointment.datetime,
            status=appointment.status,
            channel=appointment.channel,
            appointment_type=appointment.appointment_type,
            notes=appointment.notes,
            created_at=appointment.created_at
        )
    except Exception as e:
        db.rollback()
        logger.error(f"خطأ في إنشاء الموعد: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"فشل إنشاء الموعد: {str(e)}")


# ==================== Webhook Endpoints ====================

@router.post("/webhook/appointment-created")
async def webhook_appointment_created(
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Webhook لاستقبال إشعارات من n8n عند إنشاء موعد
    يمكن استخدامه لإرسال إشعارات أو تحديثات
    """
    logger.info(f"📨 استقبال webhook من n8n: {data}")
    
    # يمكنك إضافة منطق هنا للتعامل مع البيانات
    # مثلاً: إرسال إشعار، تحديث حالة، إلخ
    
    return {"status": "received", "message": "تم استقبال البيانات بنجاح"}


class UpdateAppointmentRequest(BaseModel):
    """طلب تحديث موعد"""
    appointment_id: str
    status: Optional[str] = None
    notes: Optional[str] = None


@router.post("/webhook/update-appointment")
async def webhook_update_appointment(
    data: UpdateAppointmentRequest,
    db: Session = Depends(get_db)
):
    """تحديث موعد من n8n"""
    try:
        appointment = db.query(Appointment).filter(Appointment.id == data.appointment_id).first()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="الموعد غير موجود")
        
        if data.status:
            appointment.status = data.status
        if data.notes:
            appointment.notes = data.notes
        
        db.commit()
        db.refresh(appointment)
        
        return {
            "status": "success",
            "message": "تم تحديث الموعد بنجاح",
            "appointment": {
                "id": str(appointment.id),
                "status": appointment.status,
                "notes": appointment.notes
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"خطأ في تحديث الموعد: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"فشل تحديث الموعد: {str(e)}")


# ==================== Summary Endpoints ====================

@router.get("/summary")
async def get_summary(db: Session = Depends(get_db)):
    """ملخص سريع للبيانات"""
    try:
        doctors_count = db.query(Doctor).filter(Doctor.is_active == True).count()
        services_count = db.query(Service).filter(Service.is_active == True).count()
        branches_count = db.query(Branch).filter(Branch.is_active == True).count()
        appointments_count = db.query(Appointment).filter(Appointment.status == "pending").count()
        patients_count = db.query(Patient).filter(Patient.is_active == True).count()
        
        return {
            "doctors": doctors_count,
            "services": services_count,
            "branches": branches_count,
            "pending_appointments": appointments_count,
            "patients": patients_count
        }
    except Exception as e:
        logger.error(f"خطأ في جلب الملخص: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"فشل جلب الملخص: {str(e)}")

