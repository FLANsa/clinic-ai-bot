"""
Health Check & System Diagnostics Router
فحص صحة النظام والإعدادات
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Any
from pydantic import BaseModel
from app.db.session import get_db
from app.config import get_settings
from app.core.llm_client import LLMClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test/health", tags=["Test - Health Check"])


@router.get("/")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "message": "Health check endpoint is working"}


class HealthCheckResult(BaseModel):
    """نتيجة فحص واحد"""
    component: str
    status: str  # "ok", "warning", "error"
    message: str
    details: Dict[str, Any] = {}


class SystemHealthResponse(BaseModel):
    """رد شامل لصحة النظام"""
    overall_status: str  # "healthy", "degraded", "unhealthy"
    checks: List[HealthCheckResult]
    summary: Dict[str, int]  # عدد كل نوع من الحالات


@router.get("/system", response_model=SystemHealthResponse)
async def check_system_health(db: Session = Depends(get_db)):
    """
    فحص شامل لصحة النظام والإعدادات
    """
    checks: List[HealthCheckResult] = []
    settings = get_settings()

    # 1. فحص Database Connection
    try:
        db.execute(text("SELECT 1"))
        checks.append(HealthCheckResult(
            component="database",
            status="ok",
            message="اتصال قاعدة البيانات يعمل بشكل صحيح",
            details={}
        ))
    except Exception as e:
        checks.append(HealthCheckResult(
            component="database",
            status="error",
            message=f"فشل الاتصال بقاعدة البيانات: {str(e)[:100]}",
            details={"error": str(e)[:200]}
        ))

    # 2. فحص GROQ_API_KEY
    if not settings.GROQ_API_KEY:
        checks.append(HealthCheckResult(
            component="groq_api_key",
            status="error",
            message="GROQ_API_KEY غير مُعرّف - لن يعمل الـ LLM",
            details={}
        ))
    else:
        # محاولة اختبار الاتصال بـ Groq
        try:
            llm_client = LLMClient()
            # محاولة استدعاء بسيط (نستخدم system prompt قصير جداً)
            test_messages = [
                {"role": "system", "content": "You are a test."},
                {"role": "user", "content": "Say OK"}
            ]
            # لا نستدعي فعلياً لأن هذا سيستهلك credits - فقط نتحقق من وجود API key
            checks.append(HealthCheckResult(
                component="groq_api_key",
                status="ok",
                message="GROQ_API_KEY مُعرّف",
                details={"configured": True}
            ))
        except Exception as e:
            checks.append(HealthCheckResult(
                component="groq_api_key",
                status="warning",
                message=f"GROQ_API_KEY موجود لكن قد يكون غير صحيح: {str(e)[:100]}",
                details={"error": str(e)[:200]}
            ))

    # 3. فحص ADMIN_API_KEY
    if not settings.ADMIN_API_KEY:
        checks.append(HealthCheckResult(
            component="admin_api_key",
            status="warning",
            message="ADMIN_API_KEY غير مُعرّف - جميع الـ admin endpoints متاحة بدون مصادقة",
            details={}
        ))
    else:
        checks.append(HealthCheckResult(
            component="admin_api_key",
            status="ok",
            message="ADMIN_API_KEY مُعرّف",
            details={"configured": True}
        ))

    # 4. فحص Redis (اختياري)
    if settings.REDIS_URL:
        try:
            import redis
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            redis_client.ping()
            checks.append(HealthCheckResult(
                component="redis",
                status="ok",
                message="اتصال Redis يعمل بشكل صحيح",
                details={}
            ))
        except Exception as e:
            checks.append(HealthCheckResult(
                component="redis",
                status="warning",
                message=f"Redis غير متاح (سيستخدم cache محلي): {str(e)[:100]}",
                details={"error": str(e)[:200]}
            ))
    else:
        checks.append(HealthCheckResult(
            component="redis",
            status="ok",
            message="Redis غير مُعرّف - سيستخدم cache محلي",
            details={}
        ))

    # 5. فحص Vector Store (تم إزالته - لا RAG في البوت المبسط)
    # تم إزالة فحص Vector Store لأن البوت المبسط لا يستخدم RAG

    # حساب Overall Status
    error_count = sum(1 for check in checks if check.status == "error")
    warning_count = sum(1 for check in checks if check.status == "warning")
    
    if error_count > 0:
        overall_status = "unhealthy"
    elif warning_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    summary = {
        "total": len(checks),
        "ok": sum(1 for check in checks if check.status == "ok"),
        "warnings": warning_count,
        "errors": error_count
    }

    return SystemHealthResponse(
        overall_status=overall_status,
        checks=checks,
        summary=summary
    )

