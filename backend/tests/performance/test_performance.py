"""
Performance Tests - اختبارات الأداء
قياس وقت الاستجابة، معدل النجاح، واستخدام الموارد

ملاحظة: هذه الاختبارات تحتاج GROQ_API_KEY في البيئة
"""
import pytest
import time
import asyncio
import os
from typing import List, Dict
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.agent import ChatAgent
from app.core.models import ConversationInput
from app.core.llm_client import LLMClient
from app.db.session import get_db
from app.db.base import Base

# استخدام SQLite للاختبارات (أسرع ولا يحتاج اتصال خارجي)
TEST_DATABASE_URL = "sqlite:///./test_performance.db"

# إنشاء engine للاختبار
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# إنشاء الجداول
Base.metadata.create_all(bind=test_engine)

# Override get_db dependency
def override_get_db():
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class PerformanceMetrics:
    """تخزين مقاييس الأداء"""
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.intents: Dict[str, int] = {}
    
    def add_response_time(self, duration: float):
        self.response_times.append(duration)
    
    def add_success(self):
        self.success_count += 1
    
    def add_error(self):
        self.error_count += 1
    
    def add_intent(self, intent: str):
        self.intents[intent] = self.intents.get(intent, 0) + 1
    
    def get_stats(self) -> Dict:
        if not self.response_times:
            return {"error": "لا توجد بيانات"}
        
        return {
            "total_requests": len(self.response_times),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (self.success_count / (self.success_count + self.error_count) * 100) if (self.success_count + self.error_count) > 0 else 0,
            "response_time": {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "avg": sum(self.response_times) / len(self.response_times),
                "p50": sorted(self.response_times)[len(self.response_times) // 2],
                "p95": sorted(self.response_times)[int(len(self.response_times) * 0.95)],
                "p99": sorted(self.response_times)[int(len(self.response_times) * 0.99)]
            },
            "intents": self.intents
        }


# قائمة أسئلة اختبار متنوعة
TEST_QUESTIONS = [
    # FAQ
    "ما هي الخدمات المتاحة؟",
    "ما هي أوقات العمل؟",
    "هل تقبلون التأمين الطبي؟",
    
    # Booking
    "أريد حجز موعد",
    "متى متاح د. محمد؟",
    "أريد موعد لتنظيف الأسنان",
    
    # Branch Info
    "أين فرع الفاخرية؟",
    "ما هي أرقام هواتف الفروع؟",
    
    # Service Info
    "كم سعر تنظيف الأسنان؟",
    "ما هي مدة جلسة العلاج الطبيعي؟",
    
    # Doctor Info
    "من هم الأطباء المتاحون؟",
    "أريد طبيب أسنان",
    
    # Price
    "كم تكلفة تبييض الأسنان؟",
    "ما هي أسعار الخدمات؟",
    
    # Greetings
    "مرحباً",
    "شكراً",
]


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="يحتاج GROQ_API_KEY")
async def test_single_message_performance():
    """اختبار أداء رسالة واحدة"""
    db = TestSessionLocal()
    try:
        llm_client = LLMClient()
        agent = ChatAgent(
            llm_client=llm_client,
            db_session=db,
            embeddings_client=None,  # بدون RAG للاختبار السريع
            vector_store=None
        )
        
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="perf_test_user",
            message="ما هي الخدمات المتاحة؟",
            locale="ar-SA"
        )
        
        start_time = time.time()
        output = await agent.handle_message(conv_input)
        duration = time.time() - start_time
        
        print(f"\n⏱️  وقت الاستجابة: {duration:.2f} ثانية")
        print(f"✅ الرد: {output.reply_text[:100]}...")
        print(f"🎯 النية: {output.intent}")
        
        # التأكد من أن وقت الاستجابة معقول (< 10 ثواني)
        assert duration < 10, f"وقت الاستجابة بطيء جداً: {duration:.2f} ثانية"
        assert output.reply_text is not None, "يجب أن يكون هناك رد"
        
    finally:
        db.close()


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="يحتاج GROQ_API_KEY")
def test_api_endpoint_performance():
    """اختبار أداء API endpoint"""
    metrics = PerformanceMetrics()
    
    for question in TEST_QUESTIONS[:5]:  # اختبار 5 أسئلة فقط
        start_time = time.time()
        try:
            response = client.post(
                "/test/chat",
                json={"message": question}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                metrics.add_success()
                data = response.json()
                metrics.add_response_time(duration)
                if data.get("intent"):
                    metrics.add_intent(data["intent"])
            else:
                metrics.add_error()
                
        except Exception as e:
            metrics.add_error()
            print(f"❌ خطأ في السؤال '{question}': {str(e)}")
    
    stats = metrics.get_stats()
    print("\n" + "="*60)
    print("📊 نتائج اختبار الأداء - API Endpoint")
    print("="*60)
    print(f"إجمالي الطلبات: {stats['total_requests']}")
    print(f"النجاح: {stats['success_count']}")
    print(f"الفشل: {stats['error_count']}")
    print(f"معدل النجاح: {stats['success_rate']:.1f}%")
    
    rt = stats['response_time']
    print(f"\n⏱️  وقت الاستجابة:")
    print(f"  - المتوسط: {rt['avg']:.2f} ثانية")
    print(f"  - الأدنى: {rt['min']:.2f} ثانية")
    print(f"  - الأقصى: {rt['max']:.2f} ثانية")
    print(f"  - P50: {rt['p50']:.2f} ثانية")
    print(f"  - P95: {rt['p95']:.2f} ثانية")
    
    print(f"\n🎯 توزيع النوايا:")
    for intent, count in stats['intents'].items():
        print(f"  - {intent}: {count}")
    
    # التحقق من الأداء
    assert stats['success_rate'] >= 80, f"معدل النجاح منخفض: {stats['success_rate']:.1f}%"
    assert rt['avg'] < 5, f"متوسط وقت الاستجابة بطيء: {rt['avg']:.2f} ثانية"
    assert rt['p95'] < 10, f"P95 وقت الاستجابة بطيء جداً: {rt['p95']:.2f} ثانية"


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="يحتاج GROQ_API_KEY")
async def test_concurrent_requests_performance():
    """اختبار أداء الطلبات المتزامنة"""
    db = TestSessionLocal()
    try:
        llm_client = LLMClient()
        agent = ChatAgent(
            llm_client=llm_client,
            db_session=db,
            embeddings_client=None,
            vector_store=None
        )
        
        # 5 طلبات متزامنة
        questions = TEST_QUESTIONS[:5]
        
        async def process_message(question: str):
            conv_input = ConversationInput(
                channel="whatsapp",
                user_id="concurrent_test_user",
                message=question,
                locale="ar-SA"
            )
            start = time.time()
            output = await agent.handle_message(conv_input)
            duration = time.time() - start
            return duration, output
        
        start_time = time.time()
        results = await asyncio.gather(*[process_message(q) for q in questions])
        total_duration = time.time() - start_time
        
        durations = [r[0] for r in results]
        
        print(f"\n⚡ اختبار الطلبات المتزامنة (5 طلبات)")
        print(f"⏱️  الوقت الإجمالي: {total_duration:.2f} ثانية")
        print(f"⏱️  متوسط وقت كل طلب: {sum(durations) / len(durations):.2f} ثانية")
        print(f"🚀 السرعة: {len(questions) / total_duration:.2f} طلب/ثانية")
        
        # التحقق من أن جميع الطلبات نجحت
        assert all(r[1].reply_text for r in results), "يجب أن يكون هناك رد لكل طلب"
        assert total_duration < 30, f"الوقت الإجمالي بطيء: {total_duration:.2f} ثانية"
        
    finally:
        db.close()


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="يحتاج GROQ_API_KEY")
def test_response_time_percentiles():
    """اختبار توزيع أوقات الاستجابة"""
    metrics = PerformanceMetrics()
    
    # اختبار 20 سؤال لتحليل أفضل
    for question in TEST_QUESTIONS:
        start_time = time.time()
        try:
            response = client.post(
                "/test/chat",
                json={"message": question}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                metrics.add_success()
                metrics.add_response_time(duration)
            else:
                metrics.add_error()
        except Exception:
            metrics.add_error()
    
    stats = metrics.get_stats()
    rt = stats['response_time']
    
    print("\n" + "="*60)
    print("📊 تحليل توزيع أوقات الاستجابة")
    print("="*60)
    print(f"عدد الطلبات: {stats['total_requests']}")
    print(f"\n⏱️  الأوقات (بالثواني):")
    print(f"  - المتوسط (Mean): {rt['avg']:.2f}s")
    print(f"  - الوسيط (Median/P50): {rt['p50']:.2f}s")
    print(f"  - P95: {rt['p95']:.2f}s")
    print(f"  - P99: {rt['p99']:.2f}s")
    print(f"  - الأدنى: {rt['min']:.2f}s")
    print(f"  - الأقصى: {rt['max']:.2f}s")
    
    # معايير الجودة
    print(f"\n✅ معايير الجودة:")
    print(f"  - المتوسط < 5s: {'✅' if rt['avg'] < 5 else '❌'} ({rt['avg']:.2f}s)")
    print(f"  - P95 < 10s: {'✅' if rt['p95'] < 10 else '❌'} ({rt['p95']:.2f}s)")
    print(f"  - P99 < 15s: {'✅' if rt['p99'] < 15 else '❌'} ({rt['p99']:.2f}s)")
    
    # التحقق من المعايير
    assert rt['avg'] < 5, "المتوسط يجب أن يكون < 5 ثواني"
    assert rt['p95'] < 10, "P95 يجب أن يكون < 10 ثواني"


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="يحتاج GROQ_API_KEY")
def test_load_performance():
    """اختبار أداء تحت حمل (10 طلبات متتالية)"""
    metrics = PerformanceMetrics()
    
    print("\n" + "="*60)
    print("🔥 اختبار الأداء تحت الحمل (10 طلبات)")
    print("="*60)
    
    for i, question in enumerate(TEST_QUESTIONS[:10], 1):
        start_time = time.time()
        try:
            response = client.post(
                "/test/chat",
                json={"message": question}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                metrics.add_success()
                metrics.add_response_time(duration)
                data = response.json()
                if data.get("intent"):
                    metrics.add_intent(data["intent"])
                print(f"✅ [{i}/10] {duration:.2f}s - {data.get('intent', 'N/A')}")
            else:
                metrics.add_error()
                print(f"❌ [{i}/10] Failed - {response.status_code}")
        except Exception as e:
            metrics.add_error()
            print(f"❌ [{i}/10] Error: {str(e)[:50]}")
    
    stats = metrics.get_stats()
    
    print(f"\n📊 النتائج النهائية:")
    print(f"  - النجاح: {stats['success_count']}/10")
    print(f"  - معدل النجاح: {stats['success_rate']:.1f}%")
    print(f"  - متوسط وقت الاستجابة: {stats['response_time']['avg']:.2f}s")
    
    assert stats['success_rate'] >= 90, f"معدل النجاح يجب أن يكون >= 90% (حالياً: {stats['success_rate']:.1f}%)"

