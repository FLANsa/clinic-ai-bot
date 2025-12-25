"""
إعدادات قاعدة البيانات والجلسات
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends
from app.config import get_settings

settings = get_settings()

# إنشاء محرك قاعدة البيانات مع Connection Pooling محسّن
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,          # عدد الاتصالات في pool (افتراضي: 5)
    max_overflow=10,       # إضافية عند الحاجة (افتراضي: 10)
    pool_pre_ping=True,    # التحقق من الاتصال قبل الاستخدام
    pool_recycle=3600,     # إعادة تدوير الاتصالات كل ساعة (تجنب connection timeout)
    echo=False  # ضبط على True للتطوير لرؤية استعلامات SQL
)

# إنشاء جلسة محلية
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency للحصول على جلسة قاعدة البيانات
    يتم إغلاق الجلسة تلقائياً بعد الاستخدام
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

