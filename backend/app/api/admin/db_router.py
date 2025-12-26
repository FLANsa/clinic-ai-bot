"""
Database Management Router - إدارة قاعدة البيانات
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from typing import Dict, Any
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
    """
    logger.warning("⚠️  بدء تنظيف قاعدة البيانات - سيتم حذف جميع البيانات!")
    
    try:
        from app.db.models import (
            Conversation, DocumentChunk, DocumentSource,
            Service, Doctor, Branch, Offer, FAQ,
            Appointment, UnansweredQuestion, PendingHandoff
        )
        
        deleted_counts = {}
        
        # ترتيب الحذف بناءً على العلاقات (Foreign Keys)
        # حذف البيانات التي تعتمد على جداول أخرى أولاً
        
        # 1. حذف DocumentChunks (يعتمد على DocumentSource)
        doc_chunk_count = db.query(DocumentChunk).delete()
        db.commit()
        deleted_counts["document_chunks"] = doc_chunk_count
        logger.info(f"✅ تم حذف {doc_chunk_count} document chunk")
        
        # 2. حذف DocumentSource
        doc_source_count = db.query(DocumentSource).delete()
        db.commit()
        deleted_counts["document_sources"] = doc_source_count
        logger.info(f"✅ تم حذف {doc_source_count} document source")
        
        # 3. حذف UnansweredQuestion (يعتمد على Conversation)
        unanswered_count = db.query(UnansweredQuestion).delete()
        db.commit()
        deleted_counts["unanswered_questions"] = unanswered_count
        logger.info(f"✅ تم حذف {unanswered_count} unanswered question")
        
        # 4. حذف PendingHandoff (يعتمد على Conversation)
        handoff_count = db.query(PendingHandoff).delete()
        db.commit()
        deleted_counts["pending_handoffs"] = handoff_count
        logger.info(f"✅ تم حذف {handoff_count} pending handoff")
        
        # 5. حذف Conversations (بعد حذف الجداول التي تعتمد عليه)
        conv_count = db.query(Conversation).delete()
        db.commit()
        deleted_counts["conversations"] = conv_count
        logger.info(f"✅ تم حذف {conv_count} محادثة")
        
        # 6. حذف Appointments (يعتمد على Branch, Doctor, Service)
        appt_count = db.query(Appointment).delete()
        db.commit()
        deleted_counts["appointments"] = appt_count
        logger.info(f"✅ تم حذف {appt_count} موعد")
        
        # 7. حذف Offers (يعتمد على Service) - يجب حذفه قبل Service!
        offer_count = db.query(Offer).delete()
        db.commit()
        deleted_counts["offers"] = offer_count
        logger.info(f"✅ تم حذف {offer_count} عرض")
        
        # 8. حذف Doctors (قد يعتمد على Branch، لكن branch_id nullable)
        doctor_count = db.query(Doctor).delete()
        db.commit()
        deleted_counts["doctors"] = doctor_count
        logger.info(f"✅ تم حذف {doctor_count} طبيب")
        
        # 9. حذف Services (بعد حذف Offers و Appointments التي تعتمد عليه)
        service_count = db.query(Service).delete()
        db.commit()
        deleted_counts["services"] = service_count
        logger.info(f"✅ تم حذف {service_count} خدمة")
        
        # 10. حذف Branches (بعد حذف Doctors و Appointments التي تعتمد عليه)
        branch_count = db.query(Branch).delete()
        db.commit()
        deleted_counts["branches"] = branch_count
        logger.info(f"✅ تم حذف {branch_count} فرع")
        
        # 11. حذف FAQs (لا يعتمد على أي شيء)
        faq_count = db.query(FAQ).delete()
        db.commit()
        deleted_counts["faqs"] = faq_count
        logger.info(f"✅ تم حذف {faq_count} FAQ")
        
        total_deleted = sum(deleted_counts.values())
        
        logger.info(f"✅ تم تنظيف قاعدة البيانات بنجاح - إجمالي السجلات المحذوفة: {total_deleted}")
        
        return CleanDBResponse(
            success=True,
            message=f"تم تنظيف قاعدة البيانات بنجاح - تم حذف {total_deleted} سجل",
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
        from app.db.models import Branch, Doctor, Service, Offer, FAQ
        from datetime import datetime, timedelta
        import uuid
        
        details = {}
        counts = {}
        
        # 1. إضافة فروع
        branches_data = [
            {
                "name": "فرع الرياض",
                "city": "الرياض",
                "address": "حي النخيل، شارع الملك فهد",
                "phone": "0112345678",
                "working_hours": {"from": "9:00", "to": "21:00"}
            },
            {
                "name": "فرع جدة",
                "city": "جدة",
                "address": "حي الزهراء، شارع التحلية",
                "phone": "0123456789",
                "working_hours": {"from": "10:00", "to": "22:00"}
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
        
        # 2. إضافة أطباء
        doctors_data = [
            {
                "name": "د. أحمد العلي",
                "specialty": "طب الأسنان",
                "bio": "متخصص في تبييض الأسنان وتجميلها",
                "branch_id": branches[0].id if branches else None
            },
            {
                "name": "د. سارة محمد",
                "specialty": "طب الأسنان",
                "bio": "متخصصة في تقويم الأسنان",
                "branch_id": branches[0].id if branches else None
            },
            {
                "name": "د. خالد السعيد",
                "specialty": "طب العائلة",
                "bio": "طبيب عام متخصص في طب العائلة",
                "branch_id": branches[1].id if len(branches) > 1 else (branches[0].id if branches else None)
            }
        ]
        
        doctors = []
        for doctor_data in doctors_data:
            doctor = Doctor(
                id=uuid.uuid4(),
                name=doctor_data["name"],
                specialty=doctor_data["specialty"],
                branch_id=doctor_data["branch_id"],
                bio=doctor_data["bio"],
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
        
        # 3. إضافة خدمات
        services_data = [
            {
                "name": "تبييض الأسنان",
                "base_price": 800.0,
                "description": "خدمة تبييض الأسنان بالليزر"
            },
            {
                "name": "تقويم الأسنان",
                "base_price": 5000.0,
                "description": "تقويم الأسنان التقليدي والشفاف"
            },
            {
                "name": "تنظيف الأسنان",
                "base_price": 200.0,
                "description": "تنظيف وتلميع الأسنان"
            },
            {
                "name": "حشو الأسنان",
                "base_price": 300.0,
                "description": "حشو الأسنان بالمواد الحديثة"
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
        
        # 5. إضافة FAQs
        faqs_data = [
            {
                "question": "وش ساعات العمل؟",
                "answer": "ساعات العمل من 9 صباحاً إلى 9 مساءً، من الأحد إلى الخميس",
                "tags": []
            },
            {
                "question": "وين موقع العيادة؟",
                "answer": "لدينا فروع في الرياض وجدة. يمكنك زيارة أي فرع من الفروع المتاحة",
                "tags": []
            },
            {
                "question": "وش هي الخدمات المتاحة؟",
                "answer": "نقدم خدمات متعددة في طب الأسنان مثل تبييض الأسنان، تقويم الأسنان، تنظيف الأسنان، وحشو الأسنان",
                "tags": []
            }
        ]
        
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

