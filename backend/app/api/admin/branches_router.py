"""
Branches admin router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.db.models import Branch
from app.middleware.auth import verify_api_key


router = APIRouter(prefix="/admin/branches", tags=["Admin - Branches"])


class BranchCreate(BaseModel):
    name: str
    city: str
    address: str
    location_url: Optional[str] = None
    phone: Optional[str] = None
    working_hours: dict
    is_active: bool = True


@router.get("/")
async def list_branches(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """قائمة بجميع الفروع"""
    branches = db.query(Branch).all()
    return {
        "branches": [
            {
                "id": str(branch.id),
                "name": branch.name,
                "city": branch.city,
                "address": branch.address,
                "location_url": branch.location_url,
                "phone": branch.phone,
                "working_hours": branch.working_hours,
                "is_active": branch.is_active,
                "created_at": branch.created_at.isoformat(),
                "updated_at": branch.updated_at.isoformat()
            }
            for branch in branches
        ]
    }


@router.post("/")
async def create_branch(
    branch_data: BranchCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """إنشاء فرع جديد"""
    branch = Branch(**branch_data.model_dump())
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return {
        "id": str(branch.id),
        "name": branch.name,
        "city": branch.city,
        "address": branch.address,
        "location_url": branch.location_url,
        "phone": branch.phone,
        "working_hours": branch.working_hours,
        "is_active": branch.is_active
    }

