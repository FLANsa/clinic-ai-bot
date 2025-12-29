"""
CSV Import Router - استيراد البيانات من ملفات CSV
"""
import logging
import csv
import io
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy import create_engine
from datetime import datetime
import uuid
from app.db.session import get_db
from app.middleware.auth import verify_api_key
from app.config import get_settings
from app.db.models import Branch, Doctor, Service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/csv-import", tags=["Admin - CSV Import"])

settings = get_settings()


def parse_working_hours(work_hours_str: str) -> Dict[str, Any]:
    """
    تحليل ساعات العمل من النص العربي إلى JSON
    مثال: "من 8ص حتى 1ص والجمعة من 1م-1ص"
    """
    if not work_hours_str or work_hours_str.strip() == "":
        return {
            "sunday": {"from": "08:00", "to": "01:00"},
            "monday": {"from": "08:00", "to": "01:00"},
            "tuesday": {"from": "08:00", "to": "01:00"},
            "wednesday": {"from": "08:00", "to": "01:00"},
            "thursday": {"from": "08:00", "to": "01:00"},
            "friday": {"from": "13:00", "to": "01:00"},
            "saturday": {"from": "08:00", "to": "01:00"}
        }
    
    # تحليل بسيط - يمكن تحسينه لاحقاً
    work_hours_str = work_hours_str.strip()
    
    # افتراضي: من 8 صباحاً حتى 1 صباحاً
    default_hours = {
        "sunday": {"from": "08:00", "to": "01:00"},
        "monday": {"from": "08:00", "to": "01:00"},
        "tuesday": {"from": "08:00", "to": "01:00"},
        "wednesday": {"from": "08:00", "to": "01:00"},
        "thursday": {"from": "08:00", "to": "01:00"},
        "friday": {"from": "13:00", "to": "01:00"},  # الجمعة من 1 ظهراً
        "saturday": {"from": "08:00", "to": "01:00"}
    }
    
    # إذا كان النص يحتوي على "الجمعة"
    if "الجمعة" in work_hours_str:
        if "1م" in work_hours_str or "1 ظهراً" in work_hours_str:
            default_hours["friday"] = {"from": "13:00", "to": "01:00"}
    
    return default_hours


@router.post("/import-local-csv")
async def import_local_csv(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    استيراد البيانات من ملفات CSV المحلية في المشروع
    يقرأ الملفات من: branches_import.csv, doctors_import.csv, services_import.csv
    """
    logger.info("بدء استيراد البيانات من ملفات CSV المحلية...")
    
    try:
        from pathlib import Path
        import os
        
        # تحديد مسار المشروع
        project_root = Path(__file__).parent.parent.parent.parent.parent
        csv_dir = project_root / "clinic-ai-bot"
        
        # إذا لم يكن موجود، جرب المسار الحالي
        if not csv_dir.exists():
            csv_dir = project_root
        
        details = {}
        counts = {"branches": 0, "doctors": 0, "services": 0}
        now = datetime.now()
        
        # التحقق من وجود الجداول
        engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
        inspector = sqlalchemy_inspect(engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = ["branches", "doctors", "services"]
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            raise HTTPException(
                status_code=400,
                detail=f"الجداول التالية غير موجودة: {', '.join(missing_tables)}. يرجى إنشاء الجداول أولاً."
            )
        
        # 1. استيراد الفروع
        branches_file_path = csv_dir / "branches_import.csv"
        if branches_file_path.exists():
            logger.info(f"📂 قراءة ملف الفروع: {branches_file_path}")
            with open(branches_file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                branches_added = 0
                for row in reader:
                    branch_name = row.get('name_ar', '').strip()
                    if not branch_name:
                        continue
                    
                    existing = db.query(Branch).filter(Branch.name == branch_name).first()
                    if not existing:
                        branch = Branch(
                            id=uuid.uuid4(),
                            name=branch_name,
                            city=row.get('district_ar', '').strip() or "الرياض",
                            address=row.get('address_ar', '').strip() or row.get('district_ar', '').strip(),
                            phone=row.get('phone', '').strip(),
                            location_url=row.get('map_url', '').strip(),
                            working_hours=parse_working_hours(row.get('work_hours_ar', '')),
                            is_active=True,
                            created_at=now,
                            updated_at=now
                        )
                        db.add(branch)
                        branches_added += 1
                
                db.commit()
                counts["branches"] = branches_added
                logger.info(f"✅ تم إضافة {branches_added} فرع")
        else:
            logger.warning(f"⚠️  ملف branches_import.csv غير موجود في: {branches_file_path}")
        
        # 2. استيراد الأطباء
        doctors_file_path = csv_dir / "doctors_import.csv"
        if doctors_file_path.exists():
            logger.info(f"📂 قراءة ملف الأطباء: {doctors_file_path}")
            with open(doctors_file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                doctors_added = 0
                for row in reader:
                    doctor_name = row.get('doctor_name_ar', '').strip()
                    if not doctor_name:
                        continue
                    
                    # البحث عن الفرع
                    branch_code = row.get('branch_code', '').strip()
                    branch_id = None
                    if branch_code:
                        # البحث بالكود أولاً
                        branch = db.query(Branch).filter(Branch.name.like(f'%{branch_code}%')).first()
                        if not branch:
                            # البحث بالاسم
                            if branch_code == 'north_hazm':
                                branch = db.query(Branch).filter(Branch.name.like('%شمال%')).first()
                        if branch:
                            branch_id = branch.id
                    
                    # التحقق من وجود الطبيب
                    existing = db.query(Doctor).filter(
                        Doctor.name == doctor_name,
                        Doctor.branch_id == branch_id
                    ).first()
                    
                    if not existing:
                        # تحليل سنوات الخبرة
                        experience_years = None
                        exp_str = row.get('experience_years', '').strip() or row.get('experience_ar', '').strip()
                        if exp_str:
                            # استخراج الأرقام
                            import re
                            numbers = re.findall(r'\d+', exp_str)
                            if numbers:
                                try:
                                    experience_years = int(numbers[0])
                                except:
                                    pass
                        
                        doctor = Doctor(
                            id=uuid.uuid4(),
                            name=doctor_name,
                            specialty=row.get('specialty_ar', '').strip() or row.get('department_ar', '').strip(),
                            license_number=f"LIC-{uuid.uuid4().hex[:8].upper()}",
                            branch_id=branch_id,
                            working_hours=parse_working_hours(row.get('work_hours_ar', '')),
                            experience_years=str(experience_years) if experience_years else None,
                            bio=row.get('cases_ar', '').strip() or row.get('notes_ar', '').strip(),
                            is_active=row.get('status_ar', '').strip() == 'على رأس العمل',
                            created_at=now,
                            updated_at=now
                        )
                        db.add(doctor)
                        doctors_added += 1
                
                db.commit()
                counts["doctors"] = doctors_added
                logger.info(f"✅ تم إضافة {doctors_added} طبيب")
        else:
            logger.warning(f"⚠️  ملف doctors_import.csv غير موجود في: {doctors_file_path}")
        
        # 3. استيراد الخدمات
        services_file_path = csv_dir / "services_import.csv"
        if services_file_path.exists():
            logger.info(f"📂 قراءة ملف الخدمات: {services_file_path}")
            with open(services_file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                services_added = 0
                for row in reader:
                    service_name = row.get('name_ar', '').strip()
                    if not service_name:
                        continue
                    
                    existing = db.query(Service).filter(Service.name == service_name).first()
                    if not existing:
                        price_str = row.get('price_sar', '').strip()
                        base_price = None
                        if price_str:
                            try:
                                base_price = float(price_str)
                            except ValueError:
                                pass
                        
                        description = row.get('description_ar', '').strip() or row.get('notes', '').strip()
                        if not description and row.get('category_ar', '').strip():
                            description = f"({row.get('category_ar', '').strip()})"
                        
                        service = Service(
                            id=uuid.uuid4(),
                            name=service_name,
                            description=description,
                            base_price=base_price,
                            is_active=True,
                            created_at=now,
                            updated_at=now
                        )
                        db.add(service)
                        services_added += 1
                
                db.commit()
                counts["services"] = services_added
                logger.info(f"✅ تم إضافة {services_added} خدمة")
        else:
            logger.warning(f"⚠️  ملف services_import.csv غير موجود في: {services_file_path}")
        
        summary = f"""
✅ تم استيراد البيانات من ملفات CSV المحلية بنجاح!

📊 الملخص:
- الفروع المضافة: {counts.get('branches', 0)}
- الأطباء المضافون: {counts.get('doctors', 0)}
- الخدمات المضافة: {counts.get('services', 0)}
        """
        
        return {
            "success": True,
            "message": summary.strip(),
            "details": {"counts": counts}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(f"❌ فشل استيراد البيانات من CSV المحلية: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"فشل استيراد البيانات: {error_msg[:200]}"
        )


@router.post("/import-from-csv")
async def import_from_csv(
    branches_file: UploadFile = File(None),
    doctors_file: UploadFile = File(None),
    services_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    استيراد البيانات من ملفات CSV
    
    يقبل 3 ملفات:
    - branches_file: ملف CSV للفروع
    - doctors_file: ملف CSV للأطباء
    - services_file: ملف CSV للخدمات
    """
    logger.info("بدء استيراد البيانات من ملفات CSV...")
    
    try:
        from app.db.base import Base
        
        # التحقق من وجود الجداول
        engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
        inspector = sqlalchemy_inspect(engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = ["branches", "doctors", "services"]
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            raise HTTPException(
                status_code=400,
                detail=f"الجداول التالية غير موجودة: {', '.join(missing_tables)}. يرجى إنشاء الجداول أولاً."
            )
        
        details = {}
        counts = {"branches": 0, "doctors": 0, "services": 0}
        now = datetime.now()
        
        # 1. استيراد الفروع
        if branches_file:
            logger.info("📂 جاري قراءة ملف الفروع...")
            content = await branches_file.read()
            csv_content = content.decode('utf-8-sig')  # دعم BOM
            reader = csv.DictReader(io.StringIO(csv_content))
            
            branches_added = 0
            for row in reader:
                branch_name = row.get('name_ar', '').strip()
                if not branch_name:
                    continue
                
                existing = db.query(Branch).filter(Branch.name == branch_name).first()
                if not existing:
                    branch = Branch(
                        id=uuid.uuid4(),
                        name=branch_name,
                        city=row.get('district_ar', '').strip() or "الرياض",
                        address=row.get('address_ar', '').strip() or row.get('district_ar', '').strip(),
                        phone=row.get('phone', '').strip(),
                        location_url=row.get('map_url', '').strip(),
                        working_hours=parse_working_hours(row.get('work_hours_ar', '')),
                        is_active=True,
                        created_at=now,
                        updated_at=now
                    )
                    db.add(branch)
                    branches_added += 1
            
            db.commit()
            counts["branches"] = branches_added
            logger.info(f"✅ تم إضافة {branches_added} فرع")
        
        # 2. استيراد الأطباء
        if doctors_file:
            logger.info("📂 جاري قراءة ملف الأطباء...")
            content = await doctors_file.read()
            csv_content = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(csv_content))
            
            doctors_added = 0
            for row in reader:
                doctor_name = row.get('doctor_name_ar', '').strip()
                if not doctor_name:
                    continue
                
                # البحث عن الفرع
                branch_code = row.get('branch_code', '').strip()
                branch_id = None
                if branch_code:
                    branch = db.query(Branch).filter(Branch.name.like(f'%{branch_code}%')).first()
                    if not branch:
                        # البحث بالاسم الكامل
                        if branch_code == 'north_hazm':
                            branch = db.query(Branch).filter(Branch.name.like('%شمال%')).first()
                    if branch:
                        branch_id = branch.id
                
                # التحقق من وجود الطبيب
                existing = db.query(Doctor).filter(
                    Doctor.name == doctor_name,
                    Doctor.branch_id == branch_id
                ).first()
                
                if not existing:
                    doctor = Doctor(
                        id=uuid.uuid4(),
                        name=doctor_name,
                        specialty=row.get('specialty_ar', '').strip() or row.get('department_ar', '').strip(),
                        license_number=f"LIC-{uuid.uuid4().hex[:8].upper()}",
                        branch_id=branch_id,
                        working_hours=parse_working_hours(row.get('work_hours_ar', '')),
                        experience_years=row.get('experience_years', '').strip() or row.get('experience_ar', '').strip(),
                        is_active=row.get('status_ar', '').strip() == 'على رأس العمل',
                        created_at=now,
                        updated_at=now
                    )
                    db.add(doctor)
                    doctors_added += 1
            
            db.commit()
            counts["doctors"] = doctors_added
            logger.info(f"✅ تم إضافة {doctors_added} طبيب")
        
        # 3. استيراد الخدمات
        if services_file:
            logger.info("📂 جاري قراءة ملف الخدمات...")
            content = await services_file.read()
            csv_content = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(csv_content))
            
            services_added = 0
            for row in reader:
                service_name = row.get('name_ar', '').strip()
                if not service_name:
                    continue
                
                existing = db.query(Service).filter(Service.name == service_name).first()
                if not existing:
                    price_str = row.get('price_sar', '').strip()
                    base_price = None
                    if price_str:
                        try:
                            base_price = float(price_str)
                        except ValueError:
                            pass
                    
                    service = Service(
                        id=uuid.uuid4(),
                        name=service_name,
                        description=row.get('description_ar', '').strip() or row.get('notes', '').strip(),
                        base_price=base_price,
                        is_active=True,
                        created_at=now,
                        updated_at=now
                    )
                    db.add(service)
                    services_added += 1
            
            db.commit()
            counts["services"] = services_added
            logger.info(f"✅ تم إضافة {services_added} خدمة")
        
        summary = f"""
✅ تم استيراد البيانات من ملفات CSV بنجاح!

📊 الملخص:
- الفروع المضافة: {counts.get('branches', 0)}
- الأطباء المضافون: {counts.get('doctors', 0)}
- الخدمات المضافة: {counts.get('services', 0)}
        """
        
        return {
            "success": True,
            "message": summary.strip(),
            "details": {"counts": counts}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(f"❌ فشل استيراد البيانات من CSV: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"فشل استيراد البيانات: {error_msg[:200]}"
        )

