"""
Services admin router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from app.db.session import get_db
from app.db.models import Service
from app.middleware.auth import verify_api_key


router = APIRouter(prefix="/admin/services", tags=["Admin - Services"])


class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    is_active: bool = True


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_services(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """قائمة بجميع الخدمات"""
    services = db.query(Service).all()
    return {
        "services": [
            {
                "id": str(service.id),
                "name": service.name,
                "description": service.description,
                "base_price": float(service.base_price) if service.base_price is not None else None,
                "is_active": service.is_active,
                "created_at": service.created_at.isoformat(),
                "updated_at": service.updated_at.isoformat()
            }
            for service in services
        ]
    }


@router.post("/")
async def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """إنشاء خدمة جديدة"""
    service = Service(**service_data.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return {
        "id": str(service.id),
        "name": service.name,
        "description": service.description,
        "base_price": float(service.base_price) if service.base_price else None,
        "duration_minutes": service.duration_minutes,
        "is_active": service.is_active
    }


@router.put("/{service_id}")
async def update_service(
    service_id: UUID,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """تحديث خدمة"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="الخدمة غير موجودة")
    
    update_data = service_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)
    
    service.updated_at = datetime.now()
    db.commit()
    db.refresh(service)
    
    return {
        "id": str(service.id),
        "name": service.name,
        "description": service.description,
        "base_price": float(service.base_price) if service.base_price else None,
        "duration_minutes": service.duration_minutes,
        "is_active": service.is_active,
        "updated_at": service.updated_at.isoformat() if service.updated_at else None
    }


@router.delete("/{service_id}")
async def delete_service(
    service_id: UUID,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """حذف خدمة"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="الخدمة غير موجودة")
    
    # التحقق من وجود مواعيد مرتبطة بالخدمة
    from app.db.models import Appointment
    appointments_count = db.query(Appointment).filter(Appointment.service_id == service_id).count()
    if appointments_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"لا يمكن حذف الخدمة لأنها مرتبطة بـ {appointments_count} موعد. يرجى حذف المواعيد أولاً."
        )
    
    db.delete(service)
    db.commit()
    
    return {"message": "تم حذف الخدمة بنجاح", "id": str(service_id)}

