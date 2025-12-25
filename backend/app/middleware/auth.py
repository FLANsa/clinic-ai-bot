"""
API Key Authentication Middleware للـ Admin APIs
"""
import logging
from fastapi import HTTPException, Security, Header
from fastapi.security import APIKeyHeader
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# API Key Header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    التحقق من API Key
    
    Args:
        api_key: API Key من header
        
    Returns:
        API Key إذا كان صحيحاً
        
    Raises:
        HTTPException: إذا كان API Key غير صحيح أو مفقود
    """
    # الحصول على API Key من الإعدادات
    expected_api_key = getattr(settings, "ADMIN_API_KEY", None)
    
    # إذا لم يكن API Key مُعرف في الإعدادات، نسمح بالوصول (لتطوير/اختبار محلي)
    if not expected_api_key:
        logger.warning("ADMIN_API_KEY not configured - allowing all requests")
        return "development"
    
    # التحقق من API Key
    if not api_key:
        logger.warning("API Key missing from request")
        raise HTTPException(
            status_code=401,
            detail="API Key missing. Please provide X-API-Key header."
        )
    
    if api_key != expected_api_key:
        logger.warning(f"Invalid API Key attempted: {api_key[:10]}...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    
    return api_key

