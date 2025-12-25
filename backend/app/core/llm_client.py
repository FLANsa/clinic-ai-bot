"""
عميل LLM - Groq API
"""
import logging
from typing import List, Dict, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("groq package not installed. Install it with: pip install groq")


class LLMClient:
    """عميل Groq API للـ LLM"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        تهيئة عميل Groq
        
        Args:
            api_key: مفتاح API (إذا لم يُحدد، يُستخدم من الإعدادات)
            model_name: اسم النموذج (إذا لم يُحدد، يُستخدم من الإعدادات)
        """
        if not GROQ_AVAILABLE:
            raise ValueError("groq package must be installed. Run: pip install groq")
        
        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be set in environment variables or passed as parameter")
        
        self.model_name = model_name or settings.GROQ_MODEL_NAME
        self.client = Groq(api_key=self.api_key)
    
    async def chat(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        إرسال رسائل إلى Groq والحصول على رد
        
        Args:
            messages: قائمة الرسائل بالشكل [{"role": "system/user/assistant", "content": "..."}]
            max_tokens: الحد الأقصى للتوكنات في الرد
            temperature: درجة الحرارة (0.0-2.0) - كلما زادت، كلما كان الرد أكثر إبداعاً
        
        Returns:
            نص الرد من النموذج
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"خطأ في الاتصال بـ Groq: {str(e)}")


