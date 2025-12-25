"""
إعدادات البيئة (DB, Groq, Google, Meta, Vector DB)

هذا الملف يحتوي على إعدادات التطبيق للبيئة التطويرية والإنتاجية.
في بيئة التطوير، القيمة الافتراضية لـ DATABASE_URL تشير إلى قاعدة بيانات PostgreSQL
المحلية التي تعمل عبر Docker Compose (راجع infra/docker-compose.yml).

ملاحظة: يتم تحميل المتغيرات من ملف .env تلقائياً إذا كان موجوداً.
"""
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()


class Settings(BaseSettings):
    """إعدادات التطبيق - يتم تحميلها من متغيرات البيئة"""
    
    # Database
    # القيمة الافتراضية تتطابق مع إعدادات Docker Compose للتطوير
    DATABASE_URL: str = Field(
        default="postgresql://clinic:clinic_dev@localhost:5432/clinic_ai_bot",
        description="Connection string for PostgreSQL database"
    )
    
    # Groq (للـ LLM)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"  # نموذج Groq الافتراضي (أو mixtral-8x7b-32768)
    
    # Embeddings (نموذج محلي باستخدام sentence-transformers - لا يحتاج API)
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"  # نموذج أصغر (~80MB) - يدعم العربية
    
    # Vector DB
    VECTOR_DB_URL: Optional[str] = None
    VECTOR_DB_TYPE: str = "pgvector"  # أو "qdrant"
    
    # WhatsApp Business Cloud API
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    
    # Instagram Direct (Meta)
    INSTAGRAM_APP_ID: Optional[str] = None
    INSTAGRAM_APP_SECRET: Optional[str] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_VERIFY_TOKEN: Optional[str] = None
    
    # TikTok / Provider
    TIKTOK_API_KEY: Optional[str] = None
    TIKTOK_API_SECRET: Optional[str] = None
    TIKTOK_VERIFY_TOKEN: Optional[str] = None
    
    # Google Business Profile API
    GOOGLE_PROJECT_ID: Optional[str] = None
    GOOGLE_CREDENTIALS_JSON_PATH: Optional[str] = None
    GOOGLE_CREDENTIALS_JSON: Optional[str] = None  # JSON content as string
    GOOGLE_BUSINESS_ACCOUNT_NAME: Optional[str] = None
    GOOGLE_LOCATION_NAME: Optional[str] = None
    
    # Admin API Key (للـ Admin APIs)
    ADMIN_API_KEY: Optional[str] = None
    
    # Sentry DSN (للـ Error Tracking)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    
    # Redis (للـ Caching - اختياري)
    REDIS_URL: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """الحصول على إعدادات التطبيق (مع التخزين المؤقت)"""
    return Settings()

