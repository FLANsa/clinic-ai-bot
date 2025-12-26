"""
N8N Integration Router - تكامل مع n8n
يوفر endpoints للوصول إلى البيانات من n8n
"""
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel
from app.db.session import get_db
from app.middleware.auth import verify_api_key
from app.db.models import (
    Appointment, Doctor, Service, Branch, Offer, FAQ, 
    Patient, Treatment, Invoice, Employee, Conversation
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/n8n", tags=["N8N Integration"])


class N8NResponse(BaseModel):
    """رد عام من N8N"""
    success: bool
    data: Any
    count: Optional[int] = None
    message: Optional[str] = None


# ==================== المواعيد ====================
@router.get("/appointments", response_model=N8NResponse)
async def get_appointments_n8n(
    status: Optional[str] = Query(None, description="حالة الموعد (pending, confirmed, completed, cancelled)"),
    from_date: Optional[str] = Query(None, description="من تاريخ (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="إلى تاريخ (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="عدد النتائج"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """جلب المواعيد لـ n8n"""
    try:
        query = db.query(Appointment)
        
        if status:
            query = query.filter(Appointment.status == status)
        
        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date)
                query = query.filter(Appointment.datetime >= from_dt)
            except:
                pass
        
        if to_date:
            try:
                to_dt = datetime.fromisoformat(to_date)
                query = query.filter(Appointment.datetime <= to_dt)
            except:
                pass
        
        appointments = query.order_by(desc(Appointment.datetime)).limit(limit).all()
        
        data = []
        for apt in appointments:
            data.append({
                "id": str(apt.id),
                "patient_name": apt.patient_name,
                "phone": apt.phone,
                "patient_id": str(apt.patient_id) if apt.patient_id else None,
                "branch_id": str(apt.branch_id),
                "doctor_id": str(apt.doctor_id) if apt.doctor_id else None,
                "service_id": str(apt.service_id),
                "datetime": apt.datetime.isoformat(),
                "channel": apt.channel,
                "status": apt.status,
                "appointment_type": apt.appointment_type,
                "notes": apt.notes,
                "created_at": apt.created_at.isoformat(),
                "updated_at": apt.updated_at.isoformat()
            })
        
        return N8NResponse(
            success=True,
            data=data,
            count=len(data)
        )
    except Exception as e:
        logger.error(f"خطأ في جلب المواعيد: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== المرضى ====================
@router.get("/patients", response_model=N8NResponse)
async def get_patients_n8n(
    is_active: Optional[bool] = Query(None, description="المرضى النشطين فقط"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """جلب المرضى لـ n8n"""
    try:
        query = db.query(Patient)
        
        if is_active is not None:
            query = query.filter(Patient.is_active == is_active)
        
        patients = query.order_by(desc(Patient.created_at)).limit(limit).all()
        
        data = []
        for patient in patients:
            data.append({
                "id": str(patient.id),
                "full_name": patient.full_name,
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "gender": patient.gender,
                "phone_number": patient.phone_number,
                "email": patient.email,
                "address": patient.address,
                "is_active": patient.is_active,
                "created_at": patient.created_at.isoformat(),
                "updated_at": patient.updated_at.isoformat()
            })
        
        return N8NResponse(
            success=True,
            data=data,
            count=len(data)
        )
    except Exception as e:
        logger.error(f"خطأ في جلب المرضى: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== الأطباء ====================
@router.get("/doctors", response_model=N8NResponse)
async def get_doctors_n8n(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """جلب الأطباء لـ n8n"""
    try:
        query = db.query(Doctor)
        
        if is_active is not None:
            query = query.filter(Doctor.is_active == is_active)
        
        doctors = query.limit(limit).all()
        
        data = []
        for doctor in doctors:
            data.append({
                "id": str(doctor.id),
                "name": doctor.name,
                "specialty": doctor.specialty,
                "license_number": doctor.license_number,
                "phone_number": doctor.phone_number,
                "email": doctor.email,
                "bio": doctor.bio,
                "qualifications": doctor.qualifications,
                "experience_years": doctor.experience_years,
                "working_hours": doctor.working_hours,
                "branch_id": str(doctor.branch_id) if doctor.branch_id else None,
                "is_active": doctor.is_active,
                "created_at": doctor.created_at.isoformat(),
                "updated_at": doctor.updated_at.isoformat()
            })
        
        return N8NResponse(
            success=True,
            data=data,
            count=len(data)
        )
    except Exception as e:
        logger.error(f"خطأ في جلب الأطباء: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== الفواتير ====================
@router.get("/invoices", response_model=N8NResponse)
async def get_invoices_n8n(
    payment_status: Optional[str] = Query(None, description="حالة الدفع (pending, paid, partially_paid, cancelled)"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """جلب الفواتير لـ n8n"""
    try:
        query = db.query(Invoice)
        
        if payment_status:
            query = query.filter(Invoice.payment_status == payment_status)
        
        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date)
                query = query.filter(Invoice.invoice_date >= from_dt)
            except:
                pass
        
        if to_date:
            try:
                to_dt = datetime.fromisoformat(to_date)
                query = query.filter(Invoice.invoice_date <= to_dt)
            except:
                pass
        
        invoices = query.order_by(desc(Invoice.invoice_date)).limit(limit).all()
        
        data = []
        for invoice in invoices:
            data.append({
                "id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "patient_id": str(invoice.patient_id),
                "appointment_id": str(invoice.appointment_id) if invoice.appointment_id else None,
                "invoice_date": invoice.invoice_date.isoformat(),
                "sub_total": invoice.sub_total,
                "discount_amount": invoice.discount_amount,
                "tax_amount": invoice.tax_amount,
                "total_amount": invoice.total_amount,
                "payment_status": invoice.payment_status,
                "payment_method": invoice.payment_method,
                "notes": invoice.notes,
                "created_at": invoice.created_at.isoformat(),
                "updated_at": invoice.updated_at.isoformat()
            })
        
        return N8NResponse(
            success=True,
            data=data,
            count=len(data)
        )
    except Exception as e:
        logger.error(f"خطأ في جلب الفواتير: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== المحادثات ====================
@router.get("/conversations", response_model=N8NResponse)
async def get_conversations_n8n(
    channel: Optional[str] = Query(None, description="القناة (whatsapp, instagram, etc.)"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """جلب المحادثات لـ n8n"""
    try:
        query = db.query(Conversation)
        
        if channel:
            query = query.filter(Conversation.channel == channel)
        
        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date)
                query = query.filter(Conversation.created_at >= from_dt)
            except:
                pass
        
        if to_date:
            try:
                to_dt = datetime.fromisoformat(to_date)
                query = query.filter(Conversation.created_at <= to_dt)
            except:
                pass
        
        conversations = query.order_by(desc(Conversation.created_at)).limit(limit).all()
        
        data = []
        for conv in conversations:
            data.append({
                "id": str(conv.id),
                "user_id": conv.user_id,
                "channel": conv.channel,
                "user_message": conv.user_message,
                "bot_reply": conv.bot_reply,
                "intent": conv.intent,
                "db_context_used": conv.db_context_used,
                "unrecognized": conv.unrecognized,
                "needs_handoff": conv.needs_handoff,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat()
            })
        
        return N8NResponse(
            success=True,
            data=data,
            count=len(data)
        )
    except Exception as e:
        logger.error(f"خطأ في جلب المحادثات: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== إحصائيات سريعة ====================
@router.get("/stats", response_model=N8NResponse)
async def get_stats_n8n(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """إحصائيات سريعة لـ n8n"""
    try:
        stats = {
            "appointments": {
                "total": db.query(func.count(Appointment.id)).scalar(),
                "pending": db.query(func.count(Appointment.id)).filter(Appointment.status == "pending").scalar(),
                "confirmed": db.query(func.count(Appointment.id)).filter(Appointment.status == "confirmed").scalar(),
                "completed": db.query(func.count(Appointment.id)).filter(Appointment.status == "completed").scalar(),
            },
            "patients": {
                "total": db.query(func.count(Patient.id)).scalar(),
                "active": db.query(func.count(Patient.id)).filter(Patient.is_active == True).scalar(),
            },
            "doctors": {
                "total": db.query(func.count(Doctor.id)).scalar(),
                "active": db.query(func.count(Doctor.id)).filter(Doctor.is_active == True).scalar(),
            },
            "invoices": {
                "total": db.query(func.count(Invoice.id)).scalar(),
                "paid": db.query(func.count(Invoice.id)).filter(Invoice.payment_status == "paid").scalar(),
                "pending": db.query(func.count(Invoice.id)).filter(Invoice.payment_status == "pending").scalar(),
                "total_amount": db.query(func.sum(Invoice.total_amount)).scalar() or 0,
            },
            "conversations": {
                "total": db.query(func.count(Conversation.id)).scalar(),
                "today": db.query(func.count(Conversation.id)).filter(
                    func.date(Conversation.created_at) == date.today()
                ).scalar(),
            }
        }
        
        return N8NResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        logger.error(f"خطأ في جلب الإحصائيات: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

