"""
تكامل Google Business Profile API (Google Maps Reviews)
"""
import httpx
import json
import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from app.config import get_settings
from app.core.http_client import get_http_client

settings = get_settings()
logger = logging.getLogger(__name__)

GOOGLE_BUSINESS_API_BASE = "https://mybusiness.googleapis.com/v4"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"


@dataclass
class ReviewModel:
    """نموذج تقييم Google Maps"""
    name: str  # اسم التقييم (resource name)
    reviewer_display_name: str  # اسم المراجع
    star_rating: int  # عدد النجوم (1-5)
    comment: str  # نص التقييم
    create_time: datetime  # وقت إنشاء التقييم
    has_owner_reply: bool  # هل يوجد رد من المالك


async def get_google_access_token() -> Optional[str]:
    """
    الحصول على Google access token باستخدام OAuth2 Service Account
    يستخدم GOOGLE_CREDENTIALS_JSON للحصول على token
    """
    if not settings.GOOGLE_CREDENTIALS_JSON:
        logger.error("GOOGLE_CREDENTIALS_JSON not configured")
        return None
    
    try:
        # تحليل JSON credentials
        if isinstance(settings.GOOGLE_CREDENTIALS_JSON, str):
            credentials = json.loads(settings.GOOGLE_CREDENTIALS_JSON)
        else:
            credentials = settings.GOOGLE_CREDENTIALS_JSON
        
        # Service Account credentials
        if "type" in credentials and credentials["type"] == "service_account":
            # JWT assertion للـ Service Account
            import jwt
            from datetime import datetime, timedelta
            
            now = datetime.utcnow()
            claims = {
                "iss": credentials.get("client_email"),
                "sub": credentials.get("client_email"),
                "aud": GOOGLE_OAUTH_TOKEN_URL,
                "iat": now,
                "exp": now + timedelta(hours=1),
                "scope": "https://www.googleapis.com/auth/business.manage"
            }
            
            # إنشاء JWT
            private_key = credentials.get("private_key", "").replace("\\n", "\n")
            jwt_token = jwt.encode(claims, private_key, algorithm="RS256")
            
            # طلب access token
            payload = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token
            }
            
            http_client = get_http_client()
            response = await http_client.post(GOOGLE_OAUTH_TOKEN_URL, data=payload)
            response.raise_for_status()
            token_data = response.json()
            
            return token_data.get("access_token")
        else:
            logger.error("Unsupported credentials type")
            return None
            
    except Exception as e:
        logger.error(f"Error getting Google access token: {str(e)}", exc_info=True)
        return None


class GoogleBusinessClient:
    """عميل Google Business Profile API"""
    
    def __init__(self, access_token: Optional[str] = None):
        """
        تهيئة عميل Google Business
        
        Args:
            access_token: رمز الوصول (إذا لم يُحدد، يُحاول الحصول من OAuth2)
        """
        self.access_token = access_token
    
    async def ensure_access_token(self) -> bool:
        """التأكد من وجود access token صالح"""
        if not self.access_token:
            self.access_token = await get_google_access_token()
            if not self.access_token:
                return False
        return True
    
    async def list_reviews(self) -> List[ReviewModel]:
        """
        جلب قائمة التقييمات من Google Maps
        
        Returns:
            قائمة من ReviewModel
        """
        if not await self.ensure_access_token():
            raise ValueError("Failed to obtain Google access token")
        
        if not settings.GOOGLE_LOCATION_NAME:
            raise ValueError("GOOGLE_LOCATION_NAME not configured")
        
        url = f"{GOOGLE_BUSINESS_API_BASE}/{settings.GOOGLE_LOCATION_NAME}/reviews"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            http_client = get_http_client()
            response = await http_client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                reviews = []
                for review_data in data.get("reviews", []):
                    # تحويل createTime من ISO format إلى datetime
                    create_time_str = review_data.get("createTime", "")
                    create_time = datetime.fromisoformat(create_time_str.replace("Z", "+00:00"))
                    
                    # تحويل starRating من enum إلى رقم
                    star_rating_str = review_data.get("starRating", "FIVE")
                    # STAR_RATING_FIVE -> 5, STAR_RATING_FOUR -> 4, etc.
                    rating_map = {
                        "STAR_RATING_ONE": 1,
                        "STAR_RATING_TWO": 2,
                        "STAR_RATING_THREE": 3,
                        "STAR_RATING_FOUR": 4,
                        "STAR_RATING_FIVE": 5
                    }
                    star_rating = rating_map.get(star_rating_str, 5)
                    
                    review = ReviewModel(
                        name=review_data.get("name", ""),
                        reviewer_display_name=review_data.get("reviewer", {}).get("displayName", "مجهول"),
                        star_rating=star_rating,
                        comment=review_data.get("comment", ""),
                        create_time=create_time,
                        has_owner_reply=bool(review_data.get("reply"))
                    )
                    reviews.append(review)
                
                return reviews
        except Exception as e:
            raise Exception(f"خطأ في جلب التقييمات: {str(e)}")
    
    async def reply_to_review(self, review_name: str, reply_text: str) -> bool:
        """
        الرد على تقييم Google Maps
        
        Args:
            review_name: اسم التقييم (resource name)
            reply_text: نص الرد
        
        Returns:
            True إذا نجح الرد، False خلاف ذلك
        """
        url = f"{GOOGLE_BUSINESS_API_BASE}/{review_name}/reply"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "reply": {
                "comment": reply_text
            }
        }
        
        if not await self.ensure_access_token():
            logger.error("Failed to obtain Google access token for reply")
            return False
        
        try:
            http_client = get_http_client()
            response = await http_client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"خطأ في الرد على التقييم: {str(e)}", exc_info=True)
            return False

