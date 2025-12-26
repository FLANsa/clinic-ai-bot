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

