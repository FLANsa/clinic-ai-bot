"""
Services admin router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
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

