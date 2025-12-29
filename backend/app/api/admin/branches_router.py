"""
Branches admin router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
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


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    location_url: Optional[str] = None
    phone: Optional[str] = None
    working_hours: Optional[dict] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_branches(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    active_only: bool = True
):
    """قائمة بجميع الفروع"""
    query = db.query(Branch)
    
    # إذا كان active_only=True، نعرض فقط الفروع النشطة
    if active_only:
        query = query.filter(Branch.is_active == True)
    
    branches = query.order_by(Branch.created_at.desc()).all()
    
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
                "created_at": branch.created_at.isoformat() if branch.created_at else None,
                "updated_at": branch.updated_at.isoformat() if branch.updated_at else None
            }
            for branch in branches
        ],
        "total": len(branches)
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


@router.put("/{branch_id}")
async def update_branch(
    branch_id: UUID,
    branch_data: BranchUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """تحديث فرع"""
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="الفرع غير موجود")
    
    update_data = branch_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(branch, field, value)
    
    branch.updated_at = datetime.now()
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
        "is_active": branch.is_active,
        "updated_at": branch.updated_at.isoformat() if branch.updated_at else None
    }


@router.delete("/{branch_id}")
async def delete_branch(
    branch_id: UUID,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """حذف فرع"""
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="الفرع غير موجود")
    
    # التحقق من وجود أطباء مرتبطين بالفرع
    from app.db.models import Doctor
    doctors_count = db.query(Doctor).filter(Doctor.branch_id == branch_id).count()
    if doctors_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"لا يمكن حذف الفرع لأنه يحتوي على {doctors_count} طبيب. يرجى حذف الأطباء أولاً أو نقلهم إلى فرع آخر."
        )
    
    db.delete(branch)
    db.commit()
    
    return {"message": "تم حذف الفرع بنجاح", "id": str(branch_id)}

