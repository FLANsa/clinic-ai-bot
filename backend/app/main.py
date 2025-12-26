"""
FastAPI application entry point for Clinic AI Bot
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import routers
from app.api.webhooks import whatsapp_router
# Instagram and TikTok routers - to be implemented
# from app.api.webhooks import instagram_router, tiktok_router
from app.api.admin import (
    branches_router,
    doctors_router,
    services_router,
    offers_router,
    faq_router,
    appointments_router,
    analytics_router
)
from app.api.admin.export_router import router as export_router
from app.api.admin import db_router
# from app.api.reports import daily_reports_router  # To be implemented
# from app.api.google import google_reviews_router  # To be implemented
from app.api.test import chat_router as test_chat_router
from app.api.test import whatsapp_test_router
from app.logging_config import setup_logging
import os

# إعداد logging
# استخدام JSON format في Production
use_json_logging = os.getenv("RENDER") == "true" or os.getenv("USE_JSON_LOGGING", "").lower() == "true"
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    enable_file_logging=os.getenv("ENABLE_FILE_LOGGING", "").lower() == "true",
    use_json=use_json_logging
)

# إعداد Sentry للـ Error Tracking
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.1,  # 10% of transactions
        )
        logger.info("Sentry initialized successfully")
    except ImportError:
        logger.warning("Sentry SDK not installed - error tracking disabled")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {str(e)}")

app = FastAPI(
    title="Clinic AI Bot API",
    description="Multi-channel chatbot system for Saudi clinic",
    version="0.1.0"
)

# CORS middleware
# Get allowed origins from environment variable or use defaults
import os
logger = logging.getLogger(__name__)

allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

# Add Render frontend URL if provided
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    frontend_url = frontend_url.strip()
    # إذا كان اسم خدمة فقط (بدون https://)، أضف https:// و .onrender.com
    if not frontend_url.startswith("http://") and not frontend_url.startswith("https://"):
        frontend_url = f"https://{frontend_url}.onrender.com"
    if frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)

# إضافة جميع Render frontend URLs المحتملة (للتأكد)
# هذا يساعد في حالة تغيير اسم الخدمة
render_frontend_patterns = [
    "https://clinic-ai-bot-frontend.onrender.com",
    "https://clinic-ai-bot-frontend-76pf.onrender.com",
    "https://*.onrender.com"  # لن يعمل مع wildcard، لكن نضيف الأنماط الشائعة
]

# إضافة Render frontend URLs الشائعة
for pattern in ["https://clinic-ai-bot-frontend.onrender.com", "https://clinic-ai-bot-frontend-76pf.onrender.com"]:
    if pattern not in allowed_origins:
        allowed_origins.append(pattern)

# Log allowed origins for debugging
logger.info(f"CORS Allowed Origins: {allowed_origins}")
logger.info(f"FRONTEND_URL from env: {os.getenv('FRONTEND_URL')}")
logger.info(f"ALLOWED_ORIGINS from env: {os.getenv('ALLOWED_ORIGINS')}")

# في حالة Production، يجب تحديد origins صريحة
is_production = os.getenv("RENDER") == "true" or "onrender.com" in str(os.getenv("FRONTEND_URL", ""))
if is_production and len(allowed_origins) == 0:
    logger.error("ERROR: No allowed origins configured in production! CORS will block all requests.")
    logger.error("Please set ALLOWED_ORIGINS environment variable with comma-separated origins.")
    # في Production، نستخدم Render frontend URLs الافتراضية إذا لم يتم تحديد origins
    allowed_origins = ["https://clinic-ai-bot-frontend-76pf.onrender.com", "https://clinic-ai-bot-frontend.onrender.com"]

# استخدام allowed_origins فقط (بدون wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # لا نستخدم wildcard في Production
    allow_credentials=True,
    allow_methods=["*"],  # السماح بجميع الطرق (يشمل OPTIONS للـ preflight)
    allow_headers=["*"],  # السماح بجميع الـ headers (يشمل X-API-Key)
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests لمدة ساعة
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return JSONResponse(content={
        "message": "Clinic AI Bot API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    })

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={"status": "ok"})


# Include routers
# Webhooks
app.include_router(whatsapp_router.router)
# Instagram and TikTok routers - to be implemented
# app.include_router(instagram_router.router)
# app.include_router(tiktok_router.router)

# Admin
app.include_router(branches_router.router)
app.include_router(doctors_router.router)
app.include_router(services_router.router)
app.include_router(offers_router.router)
app.include_router(faq_router.router)
app.include_router(appointments_router.router)
app.include_router(analytics_router.router)
app.include_router(export_router)
app.include_router(db_router.router)

# N8N Integration
from app.api.n8n import n8n_router
app.include_router(n8n_router.router)

# Reports - To be implemented
# app.include_router(daily_reports_router.router)

# Google - To be implemented
# app.include_router(google_reviews_router.router)

# Test
app.include_router(test_chat_router.router)
from app.api.test import performance_router as test_performance_router
from app.api.test import tests_router as test_tests_router
from app.api.test import health_check_router as test_health_check_router
app.include_router(test_performance_router.router)
app.include_router(test_tests_router.router)
app.include_router(test_health_check_router.router)
app.include_router(whatsapp_test_router.router)

# Start background scheduler
@app.on_event("startup")
async def startup_event():
    """Startup event - start background scheduler"""
    try:
        from app.tasks.scheduler import start_scheduler
        start_scheduler()
    except ImportError:
        logger.warning("APScheduler not installed - scheduler disabled")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event - stop background scheduler"""
    try:
        from app.tasks.scheduler import stop_scheduler
        stop_scheduler()
    except ImportError:
        pass  # Scheduler not available
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {str(e)}", exc_info=True)

# Exception handlers to ensure CORS headers are always sent
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Ensure CORS headers are sent even in error responses"""
    origin = request.headers.get("origin")
    # التحقق من أن الـ origin مسموح
    if origin in allowed_origins:
        cors_headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    else:
        cors_headers = {}
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=cors_headers
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Ensure CORS headers are sent even in validation error responses"""
    origin = request.headers.get("origin")
    # التحقق من أن الـ origin مسموح
    if origin in allowed_origins:
        cors_headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    else:
        cors_headers = {}
    
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers=cors_headers
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Ensure CORS headers are sent even in general error responses"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    origin = request.headers.get("origin")
    # التحقق من أن الـ origin مسموح
    if origin in allowed_origins:
        cors_headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    else:
        cors_headers = {}
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=cors_headers
    )

