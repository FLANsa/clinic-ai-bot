"""
Caching system - يدعم Redis أو in-memory cache
"""
import logging
import json
from typing import Optional, Any
from functools import wraps
from datetime import timedelta
import hashlib
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# محاولة استيراد Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - using in-memory cache")

# In-memory cache fallback
_memory_cache: dict = {}
_cache_ttl: dict = {}


class CacheManager:
    """مدير الـ Cache - يدعم Redis أو in-memory"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.use_redis = False
        
        # محاولة الاتصال بـ Redis
        if REDIS_AVAILABLE and settings.REDIS_URL:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # اختبار الاتصال
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {str(e)} - using in-memory cache")
                self.use_redis = False
    
    def get(self, key: str) -> Optional[Any]:
        """الحصول على قيمة من الـ cache"""
        if self.use_redis and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {str(e)}")
                return None
        else:
            # In-memory cache
            if key in _memory_cache:
                return _memory_cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        حفظ قيمة في الـ cache
        
        Args:
            key: مفتاح الـ cache
            value: القيمة (يجب أن تكون JSON-serializable)
            ttl: وقت انتهاء الصلاحية بالثواني (افتراضي: ساعة)
        """
        try:
            serialized_value = json.dumps(value)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize cache value: {str(e)}")
            return False
        
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(key, ttl, serialized_value)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {str(e)}")
                return False
        else:
            # In-memory cache
            _memory_cache[key] = value
            _cache_ttl[key] = ttl
            return True
    
    def delete(self, key: str) -> bool:
        """حذف مفتاح من الـ cache"""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {str(e)}")
                return False
        else:
            _memory_cache.pop(key, None)
            _cache_ttl.pop(key, None)
            return True
    
    def clear_pattern(self, pattern: str) -> int:
        """حذف جميع المفاتيح المطابقة للنمط (Redis only)"""
        if self.use_redis and self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            except Exception as e:
                logger.error(f"Redis clear_pattern error: {str(e)}")
                return 0
        return 0


# Global cache instance
cache_manager = CacheManager()


def cache_key(*args, **kwargs) -> str:
    """إنشاء cache key من args و kwargs"""
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator لتخزين نتائج الدوال في الـ cache
    
    Args:
        ttl: وقت انتهاء الصلاحية بالثواني
        key_prefix: بادئة للمفتاح
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # إنشاء cache key
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # محاولة الحصول من الـ cache
            cached_value = cache_manager.get(cache_key_str)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key_str}")
                return cached_value
            
            # إذا لم تكن في الـ cache، تنفيذ الدالة
            result = await func(*args, **kwargs)
            
            # حفظ النتيجة في الـ cache
            cache_manager.set(cache_key_str, result, ttl)
            logger.debug(f"Cache set: {cache_key_str}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # إنشاء cache key
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # محاولة الحصول من الـ cache
            cached_value = cache_manager.get(cache_key_str)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key_str}")
                return cached_value
            
            # إذا لم تكن في الـ cache، تنفيذ الدالة
            result = func(*args, **kwargs)
            
            # حفظ النتيجة في الـ cache
            cache_manager.set(cache_key_str, result, ttl)
            logger.debug(f"Cache set: {cache_key_str}")
            
            return result
        
        # إرجاع wrapper حسب نوع الدالة
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

