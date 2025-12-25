"""
FAQ admin router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.db.session import get_db
from app.db.models import FAQ
from app.middleware.auth import verify_api_key


router = APIRouter(prefix="/admin/faqs", tags=["Admin - FAQs"])


class FAQCreate(BaseModel):
    question: str
    answer: str
    tags: Optional[List[str]] = None
    is_active: bool = True


@router.get("/")
async def list_faqs(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """قائمة بجميع الأسئلة الشائعة"""
    faqs = db.query(FAQ).all()
    return {
        "faqs": [
            {
                "id": str(faq.id),
                "question": faq.question,
                "answer": faq.answer,
                "tags": faq.tags if isinstance(faq.tags, list) else [],
                "is_active": faq.is_active,
                "created_at": faq.created_at.isoformat(),
                "updated_at": faq.updated_at.isoformat()
            }
            for faq in faqs
        ]
    }


@router.post("/")
async def create_faq(
    faq_data: FAQCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """إنشاء سؤال شائع جديد"""
    faq = FAQ(**faq_data.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return {
        "id": str(faq.id),
        "question": faq.question,
        "answer": faq.answer,
        "tags": faq.tags if isinstance(faq.tags, list) else [],
        "is_active": faq.is_active
    }

