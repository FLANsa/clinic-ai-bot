"""
سكريبت تهيئة قاعدة البيانات
يُنشئ جميع الجداول ويثبت pgvector extension
"""
import sys
import os
from pathlib import Path

# إضافة مجلد backend إلى Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.config import get_settings
from app.db.base import Base
from app.db.session import engine

settings = get_settings()


def init_database():
    """
    تهيئة قاعدة البيانات: إنشاء الجداول وتثبيت pgvector
    """
    print("\n" + "="*60)
    print("🔧 بدء تهيئة قاعدة البيانات...")
    print("="*60 + "\n")
    
    try:
        # 1. تثبيت pgvector extension (اختياري - لم نعد نستخدمه بعد إزالة RAG)
        print("📦 جاري التحقق من pgvector extension (اختياري)...")
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
                    print("✅ تم تثبيت pgvector extension")
                else:
                    print("✅ pgvector extension موجود بالفعل")
        except Exception as e:
            # pgvector غير متوفر - هذا مقبول لأننا لا نستخدمه بعد الآن
            print(f"⚠️  تحذير: pgvector غير متوفر (هذا مقبول - لم نعد نستخدمه): {str(e)[:100]}")
        
        # 2. إنشاء جميع الجداول
        print("\n📝 جاري إنشاء الجداول...")
        Base.metadata.create_all(bind=engine)
        print("✅ تم إنشاء جميع الجداول بنجاح")
        
        # 3. إنشاء indexes لتحسين الأداء
        print("\n📊 جاري إنشاء indexes لتحسين الأداء...")
        with pgvector_engine.connect() as conn:
            indexes = [
                # Indexes للـ conversations (للـ conversation history)
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_user_channel_created 
                ON conversations(user_id, channel, created_at DESC)
                """,
                # Indexes للـ active records (يستخدم كثيراً في _load_db_context)
                """
                CREATE INDEX IF NOT EXISTS idx_branches_is_active 
                ON branches(is_active) WHERE is_active = true
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_services_is_active 
                ON services(is_active) WHERE is_active = true
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_doctors_is_active 
                ON doctors(is_active) WHERE is_active = true
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_faqs_is_active 
                ON faqs(is_active) WHERE is_active = true
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_offers_is_active 
                ON offers(is_active) WHERE is_active = true
                """,
                # Index للـ document_chunks (للـ RAG)
                """
                CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id 
                ON document_chunks(document_id)
                """,
            ]
            
            created_count = 0
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    created_count += 1
                except Exception as e:
                    # بعض indexes قد تكون موجودة بالفعل أو تحتاج شروط خاصة
                    print(f"⚠️  تحذير في إنشاء index: {str(e)[:100]}")
            
            print(f"✅ تم إنشاء {created_count} indexes بنجاح")
        
        print("\n" + "="*60)
        print("✅ اكتملت تهيئة قاعدة البيانات بنجاح")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ فشل تهيئة قاعدة البيانات")
        print("="*60)
        print(f"\n📝 الخطأ التفصيلي: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

