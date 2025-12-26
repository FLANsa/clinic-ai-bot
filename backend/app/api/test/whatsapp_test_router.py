"""
WhatsApp API Test Router - اختبار ربط WhatsApp Business API
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.config import get_settings
from app.integrations import whatsapp as whatsapp_integration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test/whatsapp", tags=["Test - WhatsApp"])


class TestMessageRequest(BaseModel):
    """نموذج طلب إرسال رسالة تجريبية"""
    phone_number: str = Field(..., description="رقم الهاتف (مع رمز البلد، مثال: 966501234567)")
    message: str = Field(default="رسالة تجريبية من عيادة - هذا اختبار للتحقق من ربط WhatsApp API", description="نص الرسالة")


class TestConnectionResponse(BaseModel):
    """نموذج رد اختبار الاتصال"""
    success: bool
    message: str
    details: Dict[str, Any] = {}


class TestMessageResponse(BaseModel):
    """نموذج رد إرسال الرسالة"""
    success: bool
    message: str
    message_id: Optional[str] = None
    details: Dict[str, Any] = {}


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_whatsapp_connection():
    """
    اختبار اتصال WhatsApp API والتحقق من البيانات
    
    يتحقق من:
    1. وجود Access Token و Phone Number ID
    2. صحة Access Token عبر الاتصال بـ Graph API
    3. صحة Phone Number ID
    """
    try:
        settings = get_settings()
        details = {}
        
        # 1. التحقق من وجود البيانات
        has_access_token = bool(settings.WHATSAPP_ACCESS_TOKEN)
        has_phone_number_id = bool(settings.WHATSAPP_PHONE_NUMBER_ID)
        
        details["credentials"] = {
            "access_token": "✅ موجود" if has_access_token else "❌ غير موجود",
            "phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID if has_phone_number_id else "❌ غير موجود",
            "business_account_id": settings.WHATSAPP_BUSINESS_ACCOUNT_ID if hasattr(settings, 'WHATSAPP_BUSINESS_ACCOUNT_ID') and settings.WHATSAPP_BUSINESS_ACCOUNT_ID else "غير معرّف"
        }
        
        if not has_access_token or not has_phone_number_id:
            return TestConnectionResponse(
                success=False,
                message="❌ بيانات الاعتماد غير كاملة. تأكد من إضافة WHATSAPP_ACCESS_TOKEN و WHATSAPP_PHONE_NUMBER_ID في ملف .env",
                details=details
            )
        
        # 2. التحقق من صحة Access Token عبر Graph API
        try:
            import httpx
            
            phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
            access_token = settings.WHATSAPP_ACCESS_TOKEN
            
            # محاولة الحصول على معلومات Phone Number
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    phone_info = response.json()
                    details["api_connection"] = {
                        "status": "✅ نجح الاتصال",
                        "phone_number_info": {
                            "id": phone_info.get("id"),
                            "display_phone_number": phone_info.get("display_phone_number"),
                            "verified_name": phone_info.get("verified_name")
                        }
                    }
                    
                    return TestConnectionResponse(
                        success=True,
                        message="✅ تم التحقق بنجاح! البيانات صحيحة والاتصال بـ WhatsApp API يعمل بشكل صحيح.",
                        details=details
                    )
                elif response.status_code == 401:
                    error_data = response.json() if response.content else {}
                    error_info = error_data.get("error", {})
                    error_message = error_info.get("message", "Access Token غير صحيح")
                    error_type = error_info.get("type", "")
                    
                    # تحديد نوع الخطأ
                    if "expired" in error_message.lower() or "Session has expired" in error_message:
                        detailed_message = (
                            f"❌ Access Token منتهي الصلاحية!\n\n"
                            f"{error_message}\n\n"
                            f"⚠️ يجب إنشاء Access Token جديد من Meta Business Suite:\n"
                            f"1. اذهب إلى https://business.facebook.com\n"
                            f"2. افتح WhatsApp Business Account الخاص بك\n"
                            f"3. اذهب إلى API Setup > Access Tokens\n"
                            f"4. أنشئ Token جديد وانسخه\n"
                            f"5. حدث ملف .env بالـ Token الجديد"
                        )
                    elif "logged out" in error_message.lower() or "session is invalid" in error_message.lower():
                        detailed_message = (
                            f"❌ Access Token غير صالح!\n\n"
                            f"{error_message}\n\n"
                            f"⚠️ يجب الحصول على Access Token جديد:\n"
                            f"📌 الطريقة الصحيحة:\n"
                            f"1. اذهب إلى https://developers.facebook.com/apps\n"
                            f"2. اختر التطبيق المرتبط بـ WhatsApp Business\n"
                            f"3. اذهب إلى WhatsApp > API Setup\n"
                            f"4. انسخ Temporary access token (للاختبار)\n"
                            f"   أو أنشئ System User Token (للإنتاج)\n"
                            f"5. تأكد من أن Token لديه صلاحيات:\n"
                            f"   - whatsapp_business_messaging\n"
                            f"   - whatsapp_business_management\n"
                            f"6. حدث ملف .env بالـ Token الجديد\n"
                            f"7. أعد تشغيل الباك إند"
                        )
                    else:
                        detailed_message = f"❌ فشل التحقق: {error_message}. تأكد من صحة Access Token."
                    
                    details["api_connection"] = {
                        "status": "❌ فشل الاتصال",
                        "error": error_message,
                        "error_type": error_type,
                        "status_code": response.status_code,
                        "solution": "يحتاج إلى Access Token جديد" if "expired" in error_message.lower() else "تأكد من صحة Access Token"
                    }
                    return TestConnectionResponse(
                        success=False,
                        message=detailed_message,
                        details=details
                    )
                else:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("error", {}).get("message", f"خطأ غير متوقع: {response.status_code}")
                    details["api_connection"] = {
                        "status": "❌ فشل الاتصال",
                        "error": error_message,
                        "status_code": response.status_code
                    }
                    return TestConnectionResponse(
                        success=False,
                        message=f"❌ فشل الاتصال: {error_message}",
                        details=details
                    )
                    
        except httpx.TimeoutException:
            details["api_connection"] = {
                "status": "❌ انتهت مهلة الاتصال",
                "error": "استغراق الاتصال أكثر من 10 ثواني"
            }
            return TestConnectionResponse(
                success=False,
                message="❌ انتهت مهلة الاتصال. تحقق من اتصالك بالإنترنت.",
                details=details
            )
        except Exception as e:
            error_msg = str(e)
            details["api_connection"] = {
                "status": "❌ خطأ في الاتصال",
                "error": error_msg
            }
            return TestConnectionResponse(
                success=False,
                message=f"❌ حدث خطأ أثناء الاتصال: {error_msg}",
                details=details
            )
            
    except Exception as e:
        logger.error(f"Error in test_whatsapp_connection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"خطأ غير متوقع: {str(e)}"
        )


@router.post("/send-test-message", response_model=TestMessageResponse)
async def send_test_message(request: TestMessageRequest):
    """
    إرسال رسالة تجريبية إلى رقم محدد
    
    يتطلب:
    - رقم هاتف صحيح (مع رمز البلد)
    - رسالة نصية
    """
    try:
        settings = get_settings()
        
        # التحقق من وجود البيانات
        if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            raise HTTPException(
                status_code=400,
                detail="بيانات الاعتماد غير موجودة. تأكد من إضافة WHATSAPP_ACCESS_TOKEN و WHATSAPP_PHONE_NUMBER_ID في ملف .env"
            )
        
        # تنظيف رقم الهاتف (إزالة المسافات والأحرف الخاصة)
        phone_number = request.phone_number.strip().replace(" ", "").replace("-", "").replace("+", "")
        
        # التحقق من صحة رقم الهاتف (يجب أن يكون أرقام فقط)
        if not phone_number.isdigit():
            raise HTTPException(
                status_code=400,
                detail="رقم الهاتف غير صحيح. يجب أن يحتوي على أرقام فقط (مثال: 966501234567)"
            )
        
        # إرسال الرسالة
        result = await whatsapp_integration.send_message(phone_number, request.message)
        
        if result.get("success"):
            return TestMessageResponse(
                success=True,
                message=f"✅ تم إرسال الرسالة بنجاح إلى {phone_number}",
                message_id=result.get("message_id"),
                details={
                    "phone_number": phone_number,
                    "message_preview": request.message[:50] + "..." if len(request.message) > 50 else request.message,
                    "whatsapp_response": result.get("response")
                }
            )
        else:
            error_message = result.get("error", "خطأ غير معروف")
            error_code = result.get("error_code", "UNKNOWN")
            
            # رسائل خطأ مفصلة حسب نوع الخطأ
            if error_code == 131030:
                detailed_error = (
                    f"❌ الرقم {phone_number} غير مسجل في WhatsApp أو غير موجود في قائمة الاختبار.\n\n"
                    f"💡 الحل: أضف الرقم لقائمة الاختبار في Facebook Developers:\n"
                    f"1. اذهب إلى WhatsApp > API Setup\n"
                    f"2. في قسم 'To' أضف الرقم\n"
                    f"3. أدخل كود التحقق الذي سيصلك"
                )
            elif error_code == 100:
                detailed_error = f"❌ خطأ في المعاملات: {error_message}"
            elif error_code == "NO_CREDENTIALS":
                detailed_error = "❌ بيانات اعتماد WhatsApp غير موجودة في ملف .env"
            else:
                detailed_error = f"❌ فشل إرسال الرسالة: {error_message}"
            
            return TestMessageResponse(
                success=False,
                message=detailed_error,
                details={
                    "phone_number": phone_number,
                    "error": error_message,
                    "error_code": error_code,
                    "full_response": result
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_test_message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في إرسال الرسالة: {str(e)}"
        )

