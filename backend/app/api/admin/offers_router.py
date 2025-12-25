"""
Offers admin router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.db.session import get_db
from app.db.models import Offer
from app.middleware.auth import verify_api_key


router = APIRouter(prefix="/admin/offers", tags=["Admin - Offers"])


class OfferCreate(BaseModel):
    title: str
    description: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    start_date: date
    end_date: date
    related_service_id: Optional[UUID] = None
    is_active: bool = True


@router.get("/")
async def list_offers(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """قائمة بجميع العروض"""
    offers = db.query(Offer).all()
    return {
        "offers": [
            {
                "id": str(offer.id),
                "title": offer.title,
                "description": offer.description,
                "discount_type": offer.discount_type,
                "discount_value": float(offer.discount_value),
                "start_date": offer.start_date.isoformat() if offer.start_date else None,
                "end_date": offer.end_date.isoformat() if offer.end_date else None,
                "related_service_id": str(offer.related_service_id) if offer.related_service_id else None,
                "is_active": offer.is_active,
                "created_at": offer.created_at.isoformat(),
                "updated_at": offer.updated_at.isoformat()
            }
            for offer in offers
        ]
    }


@router.post("/")
async def create_offer(
    offer_data: OfferCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """إنشاء عرض جديد"""
    offer = Offer(**offer_data.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return {
        "id": str(offer.id),
        "title": offer.title,
        "description": offer.description,
        "discount_type": offer.discount_type,
        "discount_value": float(offer.discount_value),
        "start_date": offer.start_date.isoformat(),
        "end_date": offer.end_date.isoformat(),
        "related_service_id": str(offer.related_service_id) if offer.related_service_id else None,
        "is_active": offer.is_active
    }

