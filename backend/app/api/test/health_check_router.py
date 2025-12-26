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


class DiagnosticRequest(BaseModel):
    """طلب تشخيص"""
    test_message: str = "مرحبا"


class DiagnosticResult(BaseModel):
    """نتيجة تشخيص واحدة"""
    component: str
    status: str  # "ok", "error", "warning"
    message: str
    details: Dict[str, Any] = {}
    error_type: str = ""
    error_message: str = ""


class DiagnosticResponse(BaseModel):
    """رد التشخيص الشامل"""
    overall_status: str
    results: List[DiagnosticResult]
    recommendations: List[str] = []


@router.post("/diagnose", response_model=DiagnosticResponse)
async def diagnose_bot_issues(
    request: DiagnosticRequest = DiagnosticRequest(),
    db: Session = Depends(get_db)
):
    """
    تشخيص شامل لمشاكل البوت - يختبر كل مكون بشكل منفصل
    """
    results: List[DiagnosticResult] = []
    recommendations: List[str] = []
    settings = get_settings()
    
    # 1. اختبار قاعدة البيانات - جلب البيانات
    try:
        from app.db.models import Doctor, Service, Branch, Offer
        
        doctors_count = db.query(Doctor).filter(Doctor.is_active == True).count()
        services_count = db.query(Service).filter(Service.is_active == True).count()
        branches_count = db.query(Branch).filter(Branch.is_active == True).count()
        offers_count = db.query(Offer).filter(Offer.is_active == True).count()
        
        if doctors_count == 0 and services_count == 0:
            results.append(DiagnosticResult(
                component="database_data",
                status="warning",
                message="قاعدة البيانات فارغة - لا توجد بيانات (أطباء، خدمات، فروع)",
                details={
                    "doctors": doctors_count,
                    "services": services_count,
                    "branches": branches_count,
                    "offers": offers_count
                }
            ))
            recommendations.append("استخدم /admin/db/add-sample-data لإضافة بيانات تجريبية")
        else:
            results.append(DiagnosticResult(
                component="database_data",
                status="ok",
                message=f"قاعدة البيانات تحتوي على بيانات: {doctors_count} طبيب، {services_count} خدمة، {branches_count} فرع",
                details={
                    "doctors": doctors_count,
                    "services": services_count,
                    "branches": branches_count,
                    "offers": offers_count
                }
            ))
    except Exception as e:
        results.append(DiagnosticResult(
            component="database_data",
            status="error",
            message=f"خطأ في جلب البيانات من قاعدة البيانات: {str(e)[:100]}",
            error_type=type(e).__name__,
            error_message=str(e)[:200],
            details={}
        ))
        recommendations.append("تحقق من اتصال قاعدة البيانات وإعدادات DATABASE_URL")
    
    # 2. اختبار DB Context Loading
    try:
        from app.core.agent import ChatAgent
        from app.core.models import ConversationHistory, Message
        
        agent = ChatAgent(
            llm_client=LLMClient(),
            db_session=db
        )
        
        # إنشاء conversation history تجريبي
        test_history = ConversationHistory(
            messages=[
                Message(role="user", content=request.test_message)
            ]
        )
        
        db_context = agent._load_db_context(request.test_message, test_history)
        
        if db_context:
            results.append(DiagnosticResult(
                component="db_context_loading",
                status="ok",
                message=f"تم جلب سياق من قاعدة البيانات بنجاح ({len(db_context)} حرف)",
                details={"context_length": len(db_context)}
            ))
        else:
            results.append(DiagnosticResult(
                component="db_context_loading",
                status="warning",
                message="لم يتم جلب أي سياق من قاعدة البيانات - قد تكون قاعدة البيانات فارغة",
                details={}
            ))
            recommendations.append("تأكد من وجود بيانات في قاعدة البيانات")
            
    except Exception as e:
        results.append(DiagnosticResult(
            component="db_context_loading",
            status="error",
            message=f"خطأ في جلب سياق قاعدة البيانات: {str(e)[:100]}",
            error_type=type(e).__name__,
            error_message=str(e)[:200],
            details={}
        ))
        recommendations.append("تحقق من إعدادات قاعدة البيانات ووجود الجداول")
    
    # 3. اختبار LLM Connection
    try:
        llm_client = LLMClient()
        
        if not settings.GROQ_API_KEY:
            results.append(DiagnosticResult(
                component="llm_connection",
                status="error",
                message="GROQ_API_KEY غير مُعرّف",
                details={}
            ))
            recommendations.append("أضف GROQ_API_KEY في متغيرات البيئة")
        else:
            # اختبار بسيط (لا نستهلك credits)
            test_messages = [
                {"role": "system", "content": "You are a test assistant. Reply with 'OK' only."},
                {"role": "user", "content": "Test"}
            ]
            
            # محاولة استدعاء فعلي (سيستهلك credits قليلاً)
            try:
                response = await llm_client.chat(test_messages, max_tokens=10)
                results.append(DiagnosticResult(
                    component="llm_connection",
                    status="ok",
                    message=f"اتصال LLM يعمل بشكل صحيح - الرد: {response[:50]}",
                    details={"response_preview": response[:100]}
                ))
            except Exception as llm_error:
                results.append(DiagnosticResult(
                    component="llm_connection",
                    status="error",
                    message=f"فشل الاتصال بـ LLM: {str(llm_error)[:100]}",
                    error_type=type(llm_error).__name__,
                    error_message=str(llm_error)[:200],
                    details={}
                ))
                recommendations.append("تحقق من صحة GROQ_API_KEY واتصالك بالإنترنت")
                
    except Exception as e:
        results.append(DiagnosticResult(
            component="llm_connection",
            status="error",
            message=f"خطأ في تهيئة LLM Client: {str(e)[:100]}",
            error_type=type(e).__name__,
            error_message=str(e)[:200],
            details={}
        ))
        recommendations.append("تحقق من إعدادات GROQ_API_KEY")
    
    # 4. اختبار معالجة رسالة كاملة
    try:
        from app.core.agent import ChatAgent
        from app.core.models import ConversationInput
        
        agent = ChatAgent(
            llm_client=LLMClient(),
            db_session=db
        )
        
        test_input = ConversationInput(
            channel="whatsapp",
            user_id="test_user_diagnostic",
            message=request.test_message,
            locale="ar-SA"
        )
        
        output = await agent.handle_message(test_input)
        
        if output.reply_text and "خطأ" not in output.reply_text.lower():
            results.append(DiagnosticResult(
                component="message_handling",
                status="ok",
                message=f"تم معالجة الرسالة بنجاح - الرد: {output.reply_text[:100]}",
                details={
                    "reply_length": len(output.reply_text),
                    "db_context_used": output.db_context_used
                }
            ))
        else:
            results.append(DiagnosticResult(
                component="message_handling",
                status="error",
                message=f"فشل معالجة الرسالة - الرد: {output.reply_text[:100]}",
                details={
                    "reply_text": output.reply_text,
                    "needs_handoff": output.needs_handoff
                }
            ))
            recommendations.append("تحقق من السجلات (logs) لمعرفة الخطأ التفصيلي")
            
    except Exception as e:
        results.append(DiagnosticResult(
            component="message_handling",
            status="error",
            message=f"خطأ في معالجة الرسالة: {str(e)[:100]}",
            error_type=type(e).__name__,
            error_message=str(e)[:200],
            details={}
        ))
        recommendations.append("تحقق من السجلات (logs) لمعرفة الخطأ التفصيلي")
    
    # حساب Overall Status
    error_count = sum(1 for r in results if r.status == "error")
    warning_count = sum(1 for r in results if r.status == "warning")
    
    if error_count > 0:
        overall_status = "unhealthy"
    elif warning_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return DiagnosticResponse(
        overall_status=overall_status,
        results=results,
        recommendations=recommendations
    )

