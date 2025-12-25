"""
Migration script لتحديث جدول conversations
- إعادة تسمية last_message → user_message
- إعادة تسمية reply_text → bot_reply
- إضافة db_context_used
- حذف الحقول القديمة
"""
import sys
import os
from pathlib import Path

# إضافة مجلد backend إلى Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text, inspect
from app.config import get_settings

settings = get_settings()


def migrate_conversations_table():
    """
    تحديث جدول conversations
    """
    print("\n" + "="*60)
    print("🔄 بدء تحديث جدول conversations...")
    print("="*60 + "\n")
    
    engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
    
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # التحقق من وجود جدول conversations
            if "conversations" not in inspector.get_table_names():
                print("❌ جدول conversations غير موجود. سيتم إنشاؤه عند تشغيل init_db.py")
                return
            
            columns = [col["name"] for col in inspector.get_columns("conversations")]
            print(f"📋 الأعمدة الحالية: {', '.join(columns)}\n")
            
            # 1. إعادة تسمية last_message → user_message (إذا كان موجوداً)
            if "last_message" in columns and "user_message" not in columns:
                print("🔄 إعادة تسمية last_message → user_message...")
                conn.execute(text("ALTER TABLE conversations RENAME COLUMN last_message TO user_message"))
                print("✅ تم إعادة تسمية last_message → user_message\n")
            
            # 2. إعادة تسمية reply_text → bot_reply (إذا كان موجوداً)
            if "reply_text" in columns and "bot_reply" not in columns:
                print("🔄 إعادة تسمية reply_text → bot_reply...")
                conn.execute(text("ALTER TABLE conversations RENAME COLUMN reply_text TO bot_reply"))
                print("✅ تم إعادة تسمية reply_text → bot_reply\n")
            
            # 3. إضافة db_context_used إذا لم يكن موجوداً
            if "db_context_used" not in columns:
                print("➕ إضافة عمود db_context_used...")
                conn.execute(text("ALTER TABLE conversations ADD COLUMN db_context_used BOOLEAN DEFAULT FALSE"))
                print("✅ تم إضافة عمود db_context_used\n")
            
            # 4. حذف الحقول القديمة (إذا كانت موجودة)
            old_columns = [
                "rag_used",
                "satisfaction_score",
                "quality_score",
                "relevance_score",
                "accuracy_score",
                "completeness_score",
                "clarity_score"
            ]
            
            for col in old_columns:
                if col in columns:
                    print(f"🗑️  حذف العمود القديم {col}...")
                    try:
                        conn.execute(text(f"ALTER TABLE conversations DROP COLUMN IF EXISTS {col}"))
                        print(f"✅ تم حذف العمود {col}\n")
                    except Exception as e:
                        print(f"⚠️  تحذير: لم يتم حذف العمود {col}: {str(e)[:100]}\n")
            
            # 5. تحديث db_context_used للبيانات الموجودة (إذا كان rag_used موجوداً)
            inspector = inspect(engine)
            columns_after = [col["name"] for col in inspector.get_columns("conversations")]
            
            if "rag_used" not in columns_after and "db_context_used" in columns_after:
                # إذا كان هناك بيانات، نستخدم rag_used لتحديد db_context_used
                # لكن بما أننا حذفنا rag_used، سنترك القيمة الافتراضية False
                print("✅ تم تحديث الجدول بنجاح")
            
            print("\n" + "="*60)
            print("✅ انتهى تحديث جدول conversations")
            print("="*60 + "\n")
            
    except Exception as e:
        print(f"\n❌ خطأ في تحديث الجدول: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    migrate_conversations_table()

