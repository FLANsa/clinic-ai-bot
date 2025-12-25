"""
HTTP Client مع Retry Logic و Exponential Backoff
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from functools import wraps
import httpx
from datetime import timedelta

logger = logging.getLogger(__name__)


class HTTPClientWithRetry:
    """HTTP Client مع retry logic"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        exponential_base: float = 2.0
    ):
        """
        تهيئة HTTP Client مع retry
        
        Args:
            max_retries: عدد المحاولات القصوى
            initial_backoff: وقت الانتظار الأولي بالثواني
            max_backoff: وقت الانتظار الأقصى بالثواني
            exponential_base: قاعدة الأس (2.0 يعني double كل مرة)
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.exponential_base = exponential_base
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        إرسال طلب HTTP مع retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL
            **kwargs: باقي المعاملات لـ httpx
            
        Returns:
            Response object
            
        Raises:
            httpx.HTTPError: إذا فشلت جميع المحاولات
        """
        last_exception = None
        backoff = self.initial_backoff
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)
                
                # نجح الطلب
                if response.is_success:
                    return response
                
                # إذا كان خطأ 429 (Rate Limit)، نعيد المحاولة
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                            logger.info(f"Rate limited, waiting {wait_time} seconds (Retry-After header)")
                            await asyncio.sleep(wait_time)
                            continue
                        except ValueError:
                            pass
                
                # إذا كان خطأ 5xx، نعيد المحاولة
                if 500 <= response.status_code < 600:
                    logger.warning(
                        f"Server error {response.status_code} on attempt {attempt + 1}/{self.max_retries}, "
                        f"retrying in {backoff:.2f}s"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff = min(backoff * self.exponential_base, self.max_backoff)
                        continue
                
                # أخطاء أخرى (4xx) - لا نعيد المحاولة
                return response
                
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                last_exception = e
                logger.warning(
                    f"Network error on attempt {attempt + 1}/{self.max_retries}: {str(e)}, "
                    f"retrying in {backoff:.2f}s"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * self.exponential_base, self.max_backoff)
                else:
                    raise
            except httpx.HTTPError as e:
                # أخطاء HTTP أخرى - لا نعيد المحاولة
                raise
        
        # إذا وصلنا هنا، فشلت جميع المحاولات
        if last_exception:
            raise last_exception
        raise httpx.HTTPError("Request failed after all retries")
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request"""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST request"""
        return await self.request("POST", url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> httpx.Response:
        """PUT request"""
        return await self.request("PUT", url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """DELETE request"""
        return await self.request("DELETE", url, **kwargs)
    
    async def close(self):
        """إغلاق HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Global HTTP client instance
_default_client: Optional[HTTPClientWithRetry] = None


def get_http_client() -> HTTPClientWithRetry:
    """الحصول على HTTP client instance"""
    global _default_client
    if _default_client is None:
        _default_client = HTTPClientWithRetry()
    return _default_client

