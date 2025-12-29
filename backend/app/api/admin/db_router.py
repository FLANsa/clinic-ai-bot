"""
Database Management Router - إدارة قاعدة البيانات
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, inspect as sqlalchemy_inspect
from pydantic import BaseModel
from typing import Dict, Any, List
from app.db.session import get_db
from app.middleware.auth import verify_api_key
from app.config import get_settings
from app.db.base import Base

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/db", tags=["Admin - Database"])

settings = get_settings()


class InitDBResponse(BaseModel):
    """رد تهيئة قاعدة البيانات"""
    success: bool
    message: str
    details: Dict[str, Any] = {}


class CleanDBResponse(BaseModel):
    """رد تنظيف قاعدة البيانات"""
    success: bool
    message: str
    deleted_counts: Dict[str, int] = {}


class DropTablesResponse(BaseModel):
    """رد حذف جميع الجداول"""
    success: bool
    message: str
    dropped_tables: List[str] = []


class AddSampleDataResponse(BaseModel):
    """رد إضافة البيانات التجريبية"""
    success: bool
    message: str
    details: Dict[str, Any] = {}




@router.post("/init", response_model=InitDBResponse)
async def init_database(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    تهيئة قاعدة البيانات: إنشاء جميع الجداول والـ indexes
    """
    logger.info("بدء تهيئة قاعدة البيانات...")
    
    try:
        details = {}
        
        # 1. تثبيت pgvector extension (اختياري - لم نعد نستخدمه بعد إزالة RAG)
        logger.info("جاري التحقق من pgvector extension (اختياري)...")
        pgvector_engine = create_engine(
            settings.DATABASE_URL,
            isolation_level="AUTOCOMMIT"
        )
        
        try:
            with pgvector_engine.connect() as conn:
                # التحقق من وجود extension
                check_query = text("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'vector'
                    )
                """)
                result = conn.execute(check_query)
                exists = result.scalar()
                
                if not exists:
                    install_query = text("CREATE EXTENSION IF NOT EXISTS vector")
                    conn.execute(install_query)
                    details["pgvector"] = "تم التثبيت"
                    logger.info("✅ تم تثبيت pgvector extension")
                else:
                    details["pgvector"] = "موجود بالفعل"
                    logger.info("✅ pgvector extension موجود بالفعل")
        except Exception as e:
            # pgvector غير متوفر - هذا مقبول لأننا لا نستخدمه بعد الآن
            details["pgvector"] = f"غير متوفر (هذا مقبول): {str(e)[:100]}"
            logger.warning(f"⚠️  تحذير: pgvector غير متوفر (هذا مقبول - لم نعد نستخدمه): {str(e)[:100]}")
        
        # 2. إنشاء جميع الجداول
        logger.info("جاري إنشاء الجداول...")
        Base.metadata.create_all(bind=pgvector_engine)
        details["tables"] = "تم إنشاء جميع الجداول"
        logger.info("✅ تم إنشاء جميع الجداول بنجاح")
        
        # 2.5. تحديث الجداول الموجودة بإضافة الأعمدة المفقودة
        logger.info("جاري تحديث الجداول الموجودة...")
        inspector = sqlalchemy_inspect(pgvector_engine)
        migration_results = []
        
        with pgvector_engine.connect() as conn:
            # تحديث جدول conversations
            if "conversations" in inspector.get_table_names():
                conv_columns = [col["name"] for col in inspector.get_columns("conversations")]
                logger.info(f"📋 أعمدة conversations الحالية: {', '.join(conv_columns)}")
                
                if "user_message" not in conv_columns:
                    logger.info("➕ إضافة عمود user_message لجدول conversations...")
                    try:
                        conn.execute(text("ALTER TABLE conversations ADD COLUMN user_message TEXT"))
                        migration_results.append("تم إضافة user_message لـ conversations")
                        logger.info("✅ تم إضافة user_message")
                    except Exception as e:
                        error_msg = str(e)
                        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                            logger.info("ℹ️  العمود user_message موجود بالفعل")
                        else:
                            logger.warning(f"⚠️  لم يتم إضافة user_message: {error_msg[:100]}")
                
                if "bot_reply" not in conv_columns:
                    logger.info("➕ إضافة عمود bot_reply لجدول conversations...")
                    try:
                        conn.execute(text("ALTER TABLE conversations ADD COLUMN bot_reply TEXT"))
                        migration_results.append("تم إضافة bot_reply لـ conversations")
                        logger.info("✅ تم إضافة bot_reply")
                    except Exception as e:
                        error_msg = str(e)
                        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                            logger.info("ℹ️  العمود bot_reply موجود بالفعل")
                        else:
                            logger.warning(f"⚠️  لم يتم إضافة bot_reply: {error_msg[:100]}")
            
            # تحديث جدول doctors
            if "doctors" in inspector.get_table_names():
                doctors_columns = [col["name"] for col in inspector.get_columns("doctors")]
                logger.info(f"📋 أعمدة doctors الحالية: {', '.join(doctors_columns)}")
                
                new_doctor_columns = {
                    "license_number": "VARCHAR",
                    "phone_number": "VARCHAR",
                    "email": "VARCHAR",
                    "qualifications": "TEXT",
                    "experience_years": "VARCHAR",
                    "working_hours": "JSONB"
                }
                
                for col_name, col_type in new_doctor_columns.items():
                    if col_name not in doctors_columns:
                        logger.info(f"➕ إضافة عمود {col_name} لجدول doctors...")
                        try:
                            conn.execute(text(f"ALTER TABLE doctors ADD COLUMN {col_name} {col_type}"))
                            migration_results.append(f"تم إضافة {col_name} لـ doctors")
                            logger.info(f"✅ تم إضافة {col_name}")
                        except Exception as e:
                            error_msg = str(e)
                            # إذا كان العمود موجود بالفعل، نتجاهل الخطأ
                            if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                                logger.info(f"ℹ️  العمود {col_name} موجود بالفعل")
                            else:
                                logger.warning(f"⚠️  لم يتم إضافة {col_name}: {error_msg[:100]}")
            
            # تحديث جدول appointments
            if "appointments" in inspector.get_table_names():
                appointments_columns = [col["name"] for col in inspector.get_columns("appointments")]
                logger.info(f"📋 أعمدة appointments الحالية: {', '.join(appointments_columns)}")
                
                if "patient_id" not in appointments_columns:
                    logger.info("➕ إضافة عمود patient_id لجدول appointments...")
                    try:
                        conn.execute(text("ALTER TABLE appointments ADD COLUMN patient_id UUID"))
                        migration_results.append("تم إضافة patient_id لـ appointments")
                        logger.info("✅ تم إضافة patient_id")
                    except Exception as e:
                        error_msg = str(e)
                        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                            logger.info("ℹ️  العمود patient_id موجود بالفعل")
                        else:
                            logger.warning(f"⚠️  لم يتم إضافة patient_id: {error_msg[:100]}")
                
                if "appointment_type" not in appointments_columns:
                    logger.info("➕ إضافة عمود appointment_type لجدول appointments...")
                    try:
                        conn.execute(text("ALTER TABLE appointments ADD COLUMN appointment_type VARCHAR"))
                        migration_results.append("تم إضافة appointment_type لـ appointments")
                        logger.info("✅ تم إضافة appointment_type")
                    except Exception as e:
                        error_msg = str(e)
                        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                            logger.info("ℹ️  العمود appointment_type موجود بالفعل")
                        else:
                            logger.warning(f"⚠️  لم يتم إضافة appointment_type: {error_msg[:100]}")
        
        if migration_results:
            details["migrations"] = migration_results
            logger.info(f"✅ تم تحديث {len(migration_results)} جدول/عمود")
        else:
            details["migrations"] = "لا توجد تحديثات مطلوبة"
            logger.info("✅ جميع الجداول محدثة")
        
        # 3. إنشاء indexes لتحسين الأداء
        logger.info("جاري إنشاء indexes...")
        index_results = []
        with pgvector_engine.connect() as conn:
            indexes = [
                {
                    "name": "idx_conversations_user_channel_created",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_conversations_user_channel_created 
                    ON conversations(user_id, channel, created_at DESC)
                    """
                },
                {
                    "name": "idx_branches_is_active",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_branches_is_active 
                    ON branches(is_active) WHERE is_active = true
                    """
                },
                {
                    "name": "idx_services_is_active",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_services_is_active 
                    ON services(is_active) WHERE is_active = true
                    """
                },
                {
                    "name": "idx_doctors_is_active",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_doctors_is_active 
                    ON doctors(is_active) WHERE is_active = true
                    """
                },
                {
                    "name": "idx_faqs_is_active",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_faqs_is_active 
                    ON faqs(is_active) WHERE is_active = true
                    """
                },
                {
                    "name": "idx_offers_is_active",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_offers_is_active 
                    ON offers(is_active) WHERE is_active = true
                    """
                },
                {
                    "name": "idx_document_chunks_document_id",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id 
                    ON document_chunks(document_id)
                    """
                },
                # Indexes للإحصائيات والتقارير
                {
                    "name": "idx_conversations_created_at",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_conversations_created_at 
                    ON conversations(created_at DESC)
                    """
                },
                {
                    "name": "idx_conversations_channel",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_conversations_channel 
                    ON conversations(channel)
                    """
                },
                {
                    "name": "idx_conversations_intent",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_conversations_intent 
                    ON conversations(intent)
                    """
                },
                {
                    "name": "idx_conversations_satisfaction",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_conversations_satisfaction 
                    ON conversations(satisfaction_score) WHERE satisfaction_score IS NOT NULL
                    """
                },
                {
                    "name": "idx_appointments_datetime",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_appointments_datetime 
                    ON appointments(datetime)
                    """
                },
                {
                    "name": "idx_appointments_status",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_appointments_status 
                    ON appointments(status)
                    """
                },
                {
                    "name": "idx_appointments_patient_id",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_appointments_patient_id 
                    ON appointments(patient_id) WHERE patient_id IS NOT NULL
                    """
                },
                {
                    "name": "idx_patients_phone_number",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_patients_phone_number 
                    ON patients(phone_number)
                    """
                },
                {
                    "name": "idx_treatments_patient_id",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_treatments_patient_id 
                    ON treatments(patient_id)
                    """
                },
                {
                    "name": "idx_treatments_treatment_date",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_treatments_treatment_date 
                    ON treatments(treatment_date DESC)
                    """
                },
                {
                    "name": "idx_invoices_patient_id",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_invoices_patient_id 
                    ON invoices(patient_id)
                    """
                },
                {
                    "name": "idx_invoices_payment_status",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_invoices_payment_status 
                    ON invoices(payment_status)
                    """
                },
                {
                    "name": "idx_invoices_invoice_date",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date 
                    ON invoices(invoice_date DESC)
                    """
                },
                {
                    "name": "idx_employees_position",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_employees_position 
                    ON employees(position)
                    """
                },
                {
                    "name": "idx_doctors_license_number",
                    "sql": """
                    CREATE INDEX IF NOT EXISTS idx_doctors_license_number 
                    ON doctors(license_number) WHERE license_number IS NOT NULL
                    """
                },
            ]
            
            created_count = 0
            for index in indexes:
                try:
                    conn.execute(text(index["sql"]))
                    index_results.append({"name": index["name"], "status": "تم الإنشاء"})
                    created_count += 1
                except Exception as e:
                    index_results.append({"name": index["name"], "status": f"خطأ: {str(e)[:100]}"})
                    logger.warning(f"⚠️  تحذير في إنشاء index {index['name']}: {str(e)[:100]}")
            
            details["indexes"] = {
                "total": len(indexes),
                "created": created_count,
                "results": index_results
            }
            logger.info(f"✅ تم إنشاء {created_count} من أصل {len(indexes)} indexes")
        
        return InitDBResponse(
            success=True,
            message="تم تهيئة قاعدة البيانات بنجاح",
            details=details
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ فشل تهيئة قاعدة البيانات: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"فشل تهيئة قاعدة البيانات: {error_msg[:200]}"
        )


@router.post("/clean", response_model=CleanDBResponse)
async def clean_database(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    تنظيف قاعدة البيانات: حذف جميع البيانات من جميع الجداول
    ⚠️ تحذير: هذه العملية لا يمكن التراجع عنها!
    سيتم حذف كل شيء تماماً من قاعدة البيانات!
    """
    logger.warning("⚠️  بدء تنظيف قاعدة البيانات - سيتم حذف جميع البيانات تماماً!")
    
    try:
        from app.db.models import (
            Conversation, DocumentChunk, DocumentSource,
            Service, Doctor, Branch, Offer, FAQ,
            Appointment, UnansweredQuestion, PendingHandoff,
            Patient, Treatment, Invoice, Employee
        )
        from sqlalchemy import text
        
        deleted_counts = {}
        
        # استخدام TRUNCATE CASCADE لحذف جميع البيانات بشكل كامل وأسرع
        # TRUNCATE يحذف جميع البيانات ويعيد reset للـ sequences
        
        logger.info("🗑️  بدء حذف جميع البيانات باستخدام TRUNCATE CASCADE...")
        
        # تعطيل Foreign Key Constraints مؤقتاً
        db.execute(text("SET session_replication_role = 'replica'"))
        db.commit()
        
        # قائمة بجميع الجداول بالترتيب الصحيح
        tables_to_truncate = [
            ("treatments", "العلاجات"),
            ("invoices", "الفواتير"),
            ("appointments", "المواعيد"),
            ("document_chunks", "Document Chunks"),
            ("document_sources", "Document Sources"),
            ("unanswered_questions", "Unanswered Questions"),
            ("pending_handoffs", "Pending Handoffs"),
            ("conversations", "المحادثات"),
            ("offers", "العروض"),
            ("doctors", "الأطباء"),
            ("services", "الخدمات"),
            ("branches", "الفروع"),
            ("patients", "المرضى"),
            ("employees", "الموظفين"),
            ("faqs", "الأسئلة الشائعة"),
        ]
        
        # حذف جميع الجداول
        for table_name, table_label in tables_to_truncate:
            try:
                # استخدام TRUNCATE CASCADE لحذف جميع البيانات
                result = db.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
                db.commit()
                
                # جلب عدد السجلات قبل الحذف (للعرض)
                count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = count_result.scalar()
                
                deleted_counts[table_name] = count
                logger.info(f"✅ تم حذف جميع البيانات من جدول {table_label} ({table_name})")
            except Exception as e:
                # إذا فشل TRUNCATE، جرب DELETE
                try:
                    logger.warning(f"⚠️  TRUNCATE فشل لـ {table_name}، جاري استخدام DELETE...")
                    if table_name == "treatments":
                        count = db.query(Treatment).delete()
                    elif table_name == "invoices":
                        count = db.query(Invoice).delete()
                    elif table_name == "appointments":
                        count = db.query(Appointment).delete()
                    elif table_name == "document_chunks":
                        count = db.query(DocumentChunk).delete()
                    elif table_name == "document_sources":
                        count = db.query(DocumentSource).delete()
                    elif table_name == "unanswered_questions":
                        count = db.query(UnansweredQuestion).delete()
                    elif table_name == "pending_handoffs":
                        count = db.query(PendingHandoff).delete()
                    elif table_name == "conversations":
                        count = db.query(Conversation).delete()
                    elif table_name == "offers":
                        count = db.query(Offer).delete()
                    elif table_name == "doctors":
                        count = db.query(Doctor).delete()
                    elif table_name == "services":
                        count = db.query(Service).delete()
                    elif table_name == "branches":
                        count = db.query(Branch).delete()
                    elif table_name == "patients":
                        count = db.query(Patient).delete()
                    elif table_name == "employees":
                        count = db.query(Employee).delete()
                    elif table_name == "faqs":
                        count = db.query(FAQ).delete()
                    else:
                        count = 0
                    
                    db.commit()
                    deleted_counts[table_name] = count
                    logger.info(f"✅ تم حذف {count} سجل من جدول {table_label} ({table_name})")
                except Exception as delete_error:
                    logger.error(f"❌ فشل حذف {table_name}: {str(delete_error)}")
                    deleted_counts[table_name] = 0
        
        # إعادة تفعيل Foreign Key Constraints
        db.execute(text("SET session_replication_role = 'origin'"))
        db.commit()
        
        total_deleted = sum(deleted_counts.values())
        
        logger.info(f"✅ تم تنظيف قاعدة البيانات بنجاح - إجمالي السجلات المحذوفة: {total_deleted}")
        logger.info(f"📊 الجداول المحذوفة: {', '.join(deleted_counts.keys())}")
        
        return CleanDBResponse(
            success=True,
            message=f"✅ تم حذف جميع البيانات من قاعدة البيانات تماماً!\n\nإجمالي السجلات المحذوفة: {total_deleted}",
            deleted_counts=deleted_counts
        )
        
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(f"❌ فشل تنظيف قاعدة البيانات: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"فشل تنظيف قاعدة البيانات: {error_msg[:200]}"
        )


@router.post("/drop-all-tables", response_model=DropTablesResponse)
async def drop_all_tables(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    حذف جميع الجداول من قاعدة البيانات (DROP TABLE)
    ⚠️⚠️⚠️ تحذير خطير: هذه العملية تحذف الجداول نفسها وليس فقط البيانات!
    ⚠️⚠️⚠️ لا يمكن التراجع عن هذه العملية!
    بعد الحذف، يجب تشغيل /admin/db/init لإعادة إنشاء الجداول
    """
    logger.critical("🚨🚨🚨 بدء حذف جميع الجداول من قاعدة البيانات - عملية خطيرة جداً!")
    
    try:
        from sqlalchemy import text, inspect as sqlalchemy_inspect
        
        # إنشاء محرك قاعدة البيانات
        # استخدام AUTOCOMMIT لتجنب مشاكل الـ transactions
        engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
        inspector = sqlalchemy_inspect(engine)
        
        # جلب جميع أسماء الجداول
        all_tables = inspector.get_table_names()
        
        if not all_tables:
            return DropTablesResponse(
                success=True,
                message="لا توجد جداول في قاعدة البيانات",
                dropped_tables=[]
            )
        
        dropped_tables = []
        
        # حذف جميع الجداول
        # استخدام DROP TABLE CASCADE لحذف الجداول والعلاقات تلقائياً
        # CASCADE يحذف الجداول المعتمدة (Foreign Keys) تلقائياً
        # لا حاجة لتعطيل Foreign Keys لأن CASCADE يتعامل معها
        with engine.connect() as conn:
            # حذف جميع الجداول مباشرة
            # CASCADE سيتعامل مع Foreign Keys تلقائياً
            for table_name in all_tables:
                try:
                    # DROP TABLE CASCADE يحذف الجدول والعلاقات تلقائياً
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    dropped_tables.append(table_name)
                    logger.warning(f"🗑️  تم حذف جدول: {table_name}")
                except Exception as e:
                    logger.error(f"❌ فشل حذف جدول {table_name}: {str(e)}")
                    # المتابعة مع الجداول الأخرى حتى لو فشل أحدها
        
        logger.critical(f"🚨 تم حذف {len(dropped_tables)} جدول من قاعدة البيانات!")
        
        return DropTablesResponse(
            success=True,
            message=f"✅ تم حذف جميع الجداول من قاعدة البيانات!\n\nتم حذف {len(dropped_tables)} جدول",
            dropped_tables=dropped_tables
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ فشل حذف الجداول: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"فشل حذف الجداول: {error_msg[:200]}"
        )


@router.post("/add-sample-data", response_model=AddSampleDataResponse)
async def add_sample_data(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    إضافة بيانات تجريبية لقاعدة البيانات
    """
    logger.info("بدء إضافة البيانات التجريبية...")
    
    try:
        from app.db.models import Branch, Doctor, Service, Offer, FAQ, Patient, Employee
        from datetime import datetime, timedelta, date
        import uuid
        
        details = {}
        counts = {}
        
        # 1. إضافة فروع عيادات عادل كير
        branches_data = [
            {
                "name": "عيادات عادل كير - فرع الرياض",
                "city": "الرياض",
                "address": "حي العليا، طريق الملك فهد",
                "phone": "0112345678",
                "location_url": "https://maps.google.com/?q=24.7136,46.6753",
                "working_hours": {
                    "sunday": {"from": "9:00", "to": "21:00"},
                    "monday": {"from": "9:00", "to": "21:00"},
                    "tuesday": {"from": "9:00", "to": "21:00"},
                    "wednesday": {"from": "9:00", "to": "21:00"},
                    "thursday": {"from": "9:00", "to": "21:00"},
                    "friday": {"from": "14:00", "to": "22:00"},
                    "saturday": {"from": "9:00", "to": "21:00"}
                }
            },
            {
                "name": "عيادات عادل كير - فرع جدة",
                "city": "جدة",
                "address": "حي الزهراء، شارع التحلية",
                "phone": "0123456789",
                "location_url": "https://maps.google.com/?q=21.5433,39.1728",
                "working_hours": {
                    "sunday": {"from": "9:00", "to": "21:00"},
                    "monday": {"from": "9:00", "to": "21:00"},
                    "tuesday": {"from": "9:00", "to": "21:00"},
                    "wednesday": {"from": "9:00", "to": "21:00"},
                    "thursday": {"from": "9:00", "to": "21:00"},
                    "friday": {"from": "14:00", "to": "22:00"},
                    "saturday": {"from": "9:00", "to": "21:00"}
                }
            }
        ]
        
        branches = []
        now = datetime.now()
        for branch_data in branches_data:
            branch = Branch(
                id=uuid.uuid4(),
                name=branch_data["name"],
                city=branch_data["city"],
                address=branch_data["address"],
                phone=branch_data["phone"],
                location_url=branch_data.get("location_url"),
                working_hours=branch_data["working_hours"],
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(branch)
            branches.append(branch)
        
        db.commit()
        for branch in branches:
            db.refresh(branch)
        counts["branches"] = len(branches)
        details["branches"] = [b.name for b in branches]
        logger.info(f"✅ تم إضافة {len(branches)} فرع")
        
        # 2. إضافة أطباء عيادات عادل كير
        doctors_data = [
            {
                "name": "د. عادل كير",
                "specialty": "طب العائلة",
                "license_number": "SA-MED-001",
                "phone_number": "0501234567",
                "email": "dr.adele@adelecare.com",
                "bio": "استشاري طب العائلة مع خبرة تزيد عن 15 عاماً في الرعاية الصحية الشاملة",
                "qualifications": "دكتوراه في الطب من جامعة الملك سعود، زمالة طب العائلة",
                "experience_years": "15",
                "working_hours": {
                    "sunday": {"from": "9:00", "to": "17:00"},
                    "monday": {"from": "9:00", "to": "17:00"},
                    "tuesday": {"from": "9:00", "to": "17:00"},
                    "wednesday": {"from": "9:00", "to": "17:00"},
                    "thursday": {"from": "9:00", "to": "17:00"}
                },
                "branch_id": branches[0].id if branches else None
            },
            {
                "name": "د. فاطمة أحمد",
                "specialty": "طب الأطفال",
                "license_number": "SA-MED-002",
                "phone_number": "0502345678",
                "email": "dr.fatima@adelecare.com",
                "bio": "استشارية طب الأطفال متخصصة في رعاية الأطفال من الولادة حتى المراهقة",
                "qualifications": "دكتوراه في طب الأطفال، زمالة طب الأطفال",
                "experience_years": "12",
                "working_hours": {
                    "sunday": {"from": "10:00", "to": "18:00"},
                    "monday": {"from": "10:00", "to": "18:00"},
                    "tuesday": {"from": "10:00", "to": "18:00"},
                    "wednesday": {"from": "10:00", "to": "18:00"},
                    "thursday": {"from": "10:00", "to": "18:00"}
                },
                "branch_id": branches[0].id if branches else None
            },
            {
                "name": "د. محمد السالم",
                "specialty": "طب الباطنة",
                "license_number": "SA-MED-003",
                "phone_number": "0503456789",
                "email": "dr.mohammed@adelecare.com",
                "bio": "استشاري طب الباطنة متخصص في الأمراض المزمنة والوقاية",
                "qualifications": "دكتوراه في الطب الباطني، زمالة طب الباطنة",
                "experience_years": "18",
                "working_hours": {
                    "sunday": {"from": "8:00", "to": "16:00"},
                    "monday": {"from": "8:00", "to": "16:00"},
                    "tuesday": {"from": "8:00", "to": "16:00"},
                    "wednesday": {"from": "8:00", "to": "16:00"},
                    "thursday": {"from": "8:00", "to": "16:00"}
                },
                "branch_id": branches[1].id if len(branches) > 1 else (branches[0].id if branches else None)
            }
        ]
        
        doctors = []
        for doctor_data in doctors_data:
            doctor = Doctor(
                id=uuid.uuid4(),
                name=doctor_data["name"],
                specialty=doctor_data["specialty"],
                license_number=doctor_data.get("license_number"),
                branch_id=doctor_data["branch_id"],
                phone_number=doctor_data.get("phone_number"),
                email=doctor_data.get("email"),
                bio=doctor_data["bio"],
                qualifications=doctor_data.get("qualifications"),
                experience_years=doctor_data.get("experience_years"),
                working_hours=doctor_data.get("working_hours"),
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(doctor)
            doctors.append(doctor)
        
        db.commit()
        for doctor in doctors:
            db.refresh(doctor)
        counts["doctors"] = len(doctors)
        details["doctors"] = [d.name for d in doctors]
        logger.info(f"✅ تم إضافة {len(doctors)} طبيب")
        
        # 3. إضافة خدمات عيادات عادل كير
        services_data = [
            {
                "name": "استشارة طبية عامة",
                "base_price": 200.0,
                "description": "استشارة طبية شاملة مع طبيب العائلة"
            },
            {
                "name": "استشارة طب الأطفال",
                "base_price": 250.0,
                "description": "استشارة متخصصة لرعاية الأطفال"
            },
            {
                "name": "فحص دوري شامل",
                "base_price": 500.0,
                "description": "فحص طبي شامل يتضمن تحاليل وفحوصات أساسية"
            },
            {
                "name": "متابعة حالة مزمنة",
                "base_price": 150.0,
                "description": "متابعة دورية للمرضى الذين يعانون من أمراض مزمنة"
            },
            {
                "name": "فحص طبي للتوظيف",
                "base_price": 300.0,
                "description": "فحص طبي شامل للتوظيف"
            },
            {
                "name": "تطعيمات",
                "base_price": 100.0,
                "description": "تطعيمات للأطفال والكبار"
            }
        ]
        
        services = []
        for service_data in services_data:
            service = Service(
                id=uuid.uuid4(),
                name=service_data["name"],
                base_price=service_data["base_price"],
                description=service_data["description"],
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(service)
            services.append(service)
        
        db.commit()
        for service in services:
            db.refresh(service)
        counts["services"] = len(services)
        details["services"] = [s.name for s in services]
        logger.info(f"✅ تم إضافة {len(services)} خدمة")
        
        # 4. إضافة عروض
        offers_data = []
        if services:
            offers_data = [
                {
                    "title": "عرض خاص على تبييض الأسنان",
                    "description": "خصم 20% على تبييض الأسنان للجلسة الأولى",
                    "discount_type": "percentage",
                    "discount_value": 20.0,
                    "related_service_id": services[0].id,
                    "start_date": now,
                    "end_date": now + timedelta(days=30)
                },
                {
                    "title": "عرض تنظيف الأسنان",
                    "description": "خصم 50 ريال على تنظيف الأسنان",
                    "discount_type": "fixed",
                    "discount_value": 50.0,
                    "related_service_id": services[2].id if len(services) > 2 else services[0].id,
                    "start_date": now,
                    "end_date": now + timedelta(days=15)
                }
            ]
        
        offers = []
        for offer_data in offers_data:
            offer = Offer(
                id=uuid.uuid4(),
                title=offer_data["title"],
                description=offer_data["description"],
                discount_type=offer_data["discount_type"],
                discount_value=offer_data["discount_value"],
                related_service_id=offer_data["related_service_id"],
                start_date=offer_data["start_date"],
                end_date=offer_data["end_date"],
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(offer)
            offers.append(offer)
        
        db.commit()
        for offer in offers:
            db.refresh(offer)
        counts["offers"] = len(offers)
        details["offers"] = [o.title for o in offers]
        logger.info(f"✅ تم إضافة {len(offers)} عرض")
        
        # 5. إضافة FAQs لعيادات عادل كير
        faqs_data = [
            {
                "question": "وش ساعات العمل؟",
                "answer": "ساعات العمل من 9 صباحاً إلى 9 مساءً من الأحد إلى الخميس، ومن 2 مساءً إلى 10 مساءً يوم الجمعة. يوم السبت من 9 صباحاً إلى 9 مساءً",
                "tags": ["ساعات", "عمل", "وقت"]
            },
            {
                "question": "وين موقع عيادات عادل كير؟",
                "answer": "لدينا فروع في الرياض (حي العليا) وجدة (حي الزهراء). يمكنك زيارة أي فرع من الفروع المتاحة",
                "tags": ["موقع", "عنوان", "فروع"]
            },
            {
                "question": "وش هي الخدمات المتاحة؟",
                "answer": "نقدم خدمات متعددة تشمل: استشارات طبية عامة، استشارات طب الأطفال، فحوصات دورية شاملة، متابعة حالات مزمنة، فحوصات التوظيف، والتطعيمات",
                "tags": ["خدمات", "علاج", "استشارة"]
            },
            {
                "question": "كيف أحجز موعد؟",
                "answer": "يمكنك الحجز من خلال واتساب، الموقع الإلكتروني، أو الاتصال بنا مباشرة على الأرقام المتاحة",
                "tags": ["حجز", "موعد", "طريقة"]
            },
            {
                "question": "وش التخصصات المتاحة؟",
                "answer": "نقدم خدمات في: طب العائلة، طب الأطفال، طب الباطنة، والرعاية الصحية الشاملة",
                "tags": ["تخصص", "أطباء", "خدمات"]
            }
        ]
        
        # 6. إضافة موظفين
        employees_data = [
            {
                "full_name": "سارة أحمد",
                "position": "receptionist",
                "phone_number": "0501111111",
                "email": "sara@adelecare.com",
                "branch_id": branches[0].id if branches else None,
                "hire_date": date(2020, 1, 15),
                "salary": 8000.0
            },
            {
                "full_name": "خالد محمد",
                "position": "nurse",
                "phone_number": "0502222222",
                "email": "khalid@adelecare.com",
                "branch_id": branches[0].id if branches else None,
                "hire_date": date(2019, 6, 1),
                "salary": 12000.0
            },
            {
                "full_name": "نورا علي",
                "position": "receptionist",
                "phone_number": "0503333333",
                "email": "nora@adelecare.com",
                "branch_id": branches[1].id if len(branches) > 1 else (branches[0].id if branches else None),
                "hire_date": date(2021, 3, 10),
                "salary": 8000.0
            }
        ]
        
        employees = []
        for employee_data in employees_data:
            employee = Employee(
                id=uuid.uuid4(),
                full_name=employee_data["full_name"],
                position=employee_data["position"],
                branch_id=employee_data["branch_id"],
                phone_number=employee_data.get("phone_number"),
                email=employee_data.get("email"),
                hire_date=employee_data.get("hire_date"),
                salary=employee_data.get("salary"),
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(employee)
            employees.append(employee)
        
        db.commit()
        for employee in employees:
            db.refresh(employee)
        counts["employees"] = len(employees)
        details["employees"] = [e.full_name for e in employees]
        logger.info(f"✅ تم إضافة {len(employees)} موظف")
        
        faqs = []
        for faq_data in faqs_data:
            faq = FAQ(
                id=uuid.uuid4(),
                question=faq_data["question"],
                answer=faq_data["answer"],
                tags=faq_data["tags"],
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(faq)
            faqs.append(faq)
        
        db.commit()
        for faq in faqs:
            db.refresh(faq)
        counts["faqs"] = len(faqs)
        details["faqs"] = [f.question for f in faqs]
        logger.info(f"✅ تم إضافة {len(faqs)} FAQ")
        
        # 7. إضافة بيانات تجريبية للمرضى (اختياري - للاختبار)
        patients_data = [
            {
                "full_name": "أحمد محمد العلي",
                "date_of_birth": date(1990, 5, 15),
                "gender": "male",
                "phone_number": "0501234567",
                "email": "ahmed@example.com",
                "address": "الرياض، حي النخيل"
            },
            {
                "full_name": "فاطمة سعيد",
                "date_of_birth": date(1985, 8, 20),
                "gender": "female",
                "phone_number": "0507654321",
                "email": "fatima@example.com",
                "address": "جدة، حي الزهراء"
            }
        ]
        
        patients = []
        for patient_data in patients_data:
            patient = Patient(
                id=uuid.uuid4(),
                full_name=patient_data["full_name"],
                date_of_birth=patient_data.get("date_of_birth"),
                gender=patient_data.get("gender"),
                phone_number=patient_data["phone_number"],
                email=patient_data.get("email"),
                address=patient_data.get("address"),
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(patient)
            patients.append(patient)
        
        db.commit()
        for patient in patients:
            db.refresh(patient)
        counts["patients"] = len(patients)
        details["patients"] = [p.full_name for p in patients]
        logger.info(f"✅ تم إضافة {len(patients)} مريض")
        
        total_added = sum(counts.values())
        logger.info(f"✅ تم إضافة البيانات التجريبية بنجاح - إجمالي: {total_added} سجل")
        
        return AddSampleDataResponse(
            success=True,
            message=f"تم إضافة البيانات التجريبية بنجاح - تم إضافة {total_added} سجل",
            details={
                "counts": counts,
                "items": details
            }
        )
        
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(f"❌ فشل إضافة البيانات التجريبية: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"فشل إضافة البيانات التجريبية: {error_msg[:200]}"
        )


@router.post("/add-north-branch-data", response_model=AddSampleDataResponse)
async def add_north_branch_data(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    إضافة بيانات فرع الشمال - حي الحزم
    من الجدول المرفق: فرع الشمال حي الحزم ساعات العمل من ٨ص حتى ١ص والجمعة من ١م ١ص
    """
    logger.info("بدء إضافة بيانات فرع الشمال - حي الحزم...")
    
    try:
        from app.db.models import Branch, Doctor, Service
        from datetime import datetime
        import uuid
        
        details = {}
        counts = {}
        now = datetime.now()
        
        # 1. إضافة فرع الشمال - حي الحزم
        # ساعات العمل: من 8 صباحاً حتى 1 صباحاً (الليلة التالية)
        # الجمعة: من 1 ظهراً حتى 1 صباحاً
        branch_data = {
            "name": "فرع الشمال - حي الحزم",
            "city": "الرياض",
            "address": "حي الحزم",
            "phone": "0112345679",
            "location_url": "https://maps.google.com/?q=24.7136,46.6753",
            "working_hours": {
                "sunday": {"from": "08:00", "to": "01:00"},
                "monday": {"from": "08:00", "to": "01:00"},
                "tuesday": {"from": "08:00", "to": "01:00"},
                "wednesday": {"from": "08:00", "to": "01:00"},
                "thursday": {"from": "08:00", "to": "01:00"},
                "friday": {"from": "13:00", "to": "01:00"},
                "saturday": {"from": "08:00", "to": "01:00"}
            }
        }
        
        # التحقق من وجود الفرع
        existing_branch = db.query(Branch).filter(Branch.name == branch_data["name"]).first()
        if existing_branch:
            branch = existing_branch
            logger.info(f"✅ الفرع موجود بالفعل: {branch.name}")
        else:
            branch = Branch(
                id=uuid.uuid4(),
                name=branch_data["name"],
                city=branch_data["city"],
                address=branch_data["address"],
                phone=branch_data["phone"],
                location_url=branch_data["location_url"],
                working_hours=branch_data["working_hours"],
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(branch)
            db.commit()
            db.refresh(branch)
            logger.info(f"✅ تم إضافة فرع: {branch.name}")
        
        counts["branches"] = 1
        details["branch"] = branch.name
        
        # 2. إضافة الأطباء حسب الأقسام
        doctors_data = [
            # الطب العام (4 أطباء)
            {"name": "د. أحمد محمد العلي", "specialty": "الطب العام", "count": 1},
            {"name": "د. فاطمة عبدالله السالم", "specialty": "الطب العام", "count": 1},
            {"name": "د. خالد سعد الدوسري", "specialty": "الطب العام", "count": 1},
            {"name": "د. نورا حسن القحطاني", "specialty": "الطب العام", "count": 1},
            # الباطنة (1)
            {"name": "د. محمد علي الشمري", "specialty": "الباطنة", "count": 1},
            # اطفال (1)
            {"name": "د. سارة أحمد الزهراني", "specialty": "اطفال", "count": 1},
            # اسنان (9 أطباء)
            {"name": "د. عبدالرحمن فهد المطيري", "specialty": "اسنان", "count": 1},
            {"name": "د. ليلى عبدالعزيز العتيبي", "specialty": "اسنان", "count": 1},
            {"name": "د. يوسف صالح الحربي", "specialty": "اسنان", "count": 1},
            {"name": "د. منى خالد الدوسري", "specialty": "اسنان", "count": 1},
            {"name": "د. بندر ناصر القحطاني", "specialty": "اسنان", "count": 1},
            {"name": "د. ريم عبدالله السبيعي", "specialty": "اسنان", "count": 1},
            {"name": "د. تركي فيصل العلي", "specialty": "اسنان", "count": 1},
            {"name": "د. هناء محمد الشمري", "specialty": "اسنان", "count": 1},
            {"name": "د. ماجد سعد المطيري", "specialty": "اسنان", "count": 1},
            # نساء وولادة (2)
            {"name": "د. عبير فهد الزهراني", "specialty": "نساء وولادة", "count": 1},
            {"name": "د. نورة صالح العتيبي", "specialty": "نساء وولادة", "count": 1},
            # جلدية (2)
            {"name": "د. وليد خالد الحربي", "specialty": "جلدية", "count": 1},
            {"name": "د. ريم ناصر الدوسري", "specialty": "جلدية", "count": 1},
        ]
        
        doctors = []
        for doctor_data in doctors_data:
            # التحقق من وجود الطبيب
            existing_doctor = db.query(Doctor).filter(
                Doctor.name == doctor_data["name"],
                Doctor.branch_id == branch.id
            ).first()
            
            if existing_doctor:
                doctors.append(existing_doctor)
                logger.info(f"ℹ️  الطبيب موجود: {doctor_data['name']}")
            else:
                doctor = Doctor(
                    id=uuid.uuid4(),
                    name=doctor_data["name"],
                    specialty=doctor_data["specialty"],
                    branch_id=branch.id,
                    license_number=f"LIC-{uuid.uuid4().hex[:8].upper()}",
                    working_hours=branch_data["working_hours"],  # نفس ساعات الفرع
                    is_active=True,
                    created_at=now,
                    updated_at=now
                )
                db.add(doctor)
                doctors.append(doctor)
        
        db.commit()
        for doctor in doctors:
            db.refresh(doctor)
        
        counts["doctors"] = len(doctors)
        details["doctors"] = [d.name for d in doctors]
        logger.info(f"✅ تم إضافة {len(doctors)} طبيب")
        
        # 3. إضافة الخدمات حسب الأقسام
        services_data = [
            {"name": "الطب العام", "description": "استشارات طبية عامة وفحوصات دورية", "base_price": 150.0},
            {"name": "الباطنة", "description": "استشارات أمراض الباطنة والجهاز الهضمي", "base_price": 200.0},
            {"name": "طب الأطفال", "description": "استشارات وعلاج الأطفال", "base_price": 180.0},
            {"name": "طب الأسنان", "description": "علاج الأسنان واللثة", "base_price": 250.0},
            {"name": "نساء وولادة", "description": "استشارات نسائية ومتابعة الحمل", "base_price": 300.0},
            {"name": "الجلدية", "description": "علاج أمراض الجلد والجمال", "base_price": 200.0},
            {"name": "المختبر", "description": "تحاليل طبية شاملة", "base_price": 100.0},
            {"name": "الأشعة", "description": "فحوصات الأشعة التشخيصية", "base_price": 150.0},
            {"name": "التشقير", "description": "خدمات التشقير والتجميل", "base_price": 120.0},
        ]
        
        services = []
        for service_data in services_data:
            # التحقق من وجود الخدمة
            existing_service = db.query(Service).filter(Service.name == service_data["name"]).first()
            
            if existing_service:
                services.append(existing_service)
                logger.info(f"ℹ️  الخدمة موجودة: {service_data['name']}")
            else:
                service = Service(
                    id=uuid.uuid4(),
                    name=service_data["name"],
                    description=service_data["description"],
                    base_price=service_data["base_price"],
                    is_active=True,
                    created_at=now,
                    updated_at=now
                )
                db.add(service)
                services.append(service)
        
        db.commit()
        for service in services:
            db.refresh(service)
        
        counts["services"] = len(services)
        details["services"] = [s.name for s in services]
        logger.info(f"✅ تم إضافة {len(services)} خدمة")
        
        # ملخص
        summary = f"""
✅ تم إضافة بيانات فرع الشمال - حي الحزم بنجاح!

📊 الملخص:
- الفروع: {counts.get('branches', 0)}
- الأطباء: {counts.get('doctors', 0)}
- الخدمات: {counts.get('services', 0)}

🏥 الفرع: {branch.name}
📍 العنوان: {branch.address}
⏰ ساعات العمل: من 8 صباحاً حتى 1 صباحاً (الجمعة من 1 ظهراً)
        """
        
        return AddSampleDataResponse(
            success=True,
            message=summary.strip(),
            details={
                "counts": counts,
                "branch": branch.name,
                "doctors_count": len(doctors),
                "services_count": len(services),
                "working_hours": branch.working_hours
            }
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ فشل إضافة بيانات فرع الشمال: {error_msg}", exc_info=True)
        
        # تحسين رسالة الخطأ إذا كانت الجداول غير موجودة
        if "does not exist" in error_msg.lower() or "relation" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"❌ الجداول غير موجودة في قاعدة البيانات!\n\nيجب تهيئة قاعدة البيانات أولاً:\n1. اضغط على زر 'تهيئة قاعدة البيانات' في صفحة test-chat\n2. ثم حاول إضافة بيانات فرع الشمال مرة أخرى\n\nالخطأ التفصيلي: {error_msg[:150]}"
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"فشل إضافة بيانات فرع الشمال: {error_msg[:200]}"
        )

