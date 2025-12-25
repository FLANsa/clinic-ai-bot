"""
اختبارات أداء شاملة للنظام
"""
import pytest
import time
import asyncio
import psutil
import os
from typing import List, Dict
from fastapi.testclient import TestClient
from app.main import app
from app.core.agent import ChatAgent
from app.core.models import ConversationInput
from app.core.llm_client import LLMClient
from app.db.session import get_db, SessionLocal
from app.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import numpy as np


# Test database
TEST_DATABASE_URL = "sqlite:///./test_performance_comprehensive.db"

@pytest.fixture(scope="module")
def db_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    if os.path.exists("./test_performance_comprehensive.db"):
        os.remove("./test_performance_comprehensive.db")


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="module")
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture(scope="function")
def chat_agent(db_session):
    """Create ChatAgent for testing"""
    llm_client = LLMClient()
    return ChatAgent(
        llm_client=llm_client,
        db_session=db_session,
        embeddings_client=None,
        vector_store=None
    )


class TestResponseTime:
    """اختبارات وقت الاستجابة"""
    
    @pytest.mark.asyncio
    async def test_single_message_response_time(self, chat_agent):
        """اختبار وقت استجابة رسالة واحدة"""
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="perf_test_user",
            message="ما هي الخدمات المتاحة؟",
            locale="ar-SA"
        )
        
        start_time = time.perf_counter()
        output = await chat_agent.handle_message(conv_input)
        end_time = time.perf_counter()
        
        response_time = end_time - start_time
        
        assert output.reply_text is not None
        assert response_time < 10.0  # يجب أن يكون أسرع من 10 ثواني
        print(f"\n✅ Single message response time: {response_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_multiple_messages_response_time(self, chat_agent):
        """اختبار وقت استجابة عدة رسائل"""
        messages = [
            "ما هي الخدمات المتاحة؟",
            "أريد حجز موعد",
            "كم سعر تنظيف الأسنان؟",
            "ما هي أوقات العمل؟",
            "من هم الأطباء المتاحون؟"
        ]
        
        response_times = []
        for message in messages:
            conv_input = ConversationInput(
                channel="whatsapp",
                user_id="perf_test_user",
                message=message,
                locale="ar-SA"
            )
            
            start_time = time.perf_counter()
            await chat_agent.handle_message(conv_input)
            end_time = time.perf_counter()
            
            response_times.append(end_time - start_time)
        
        avg_time = np.mean(response_times)
        max_time = np.max(response_times)
        
        assert avg_time < 8.0  # متوسط وقت الاستجابة يجب أن يكون أقل من 8 ثواني
        assert max_time < 15.0  # أقصى وقت استجابة يجب أن يكون أقل من 15 ثانية
        
        print(f"\n✅ Average response time: {avg_time:.2f}s")
        print(f"✅ Max response time: {max_time:.2f}s")


class TestConcurrency:
    """اختبارات التزامن"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, chat_agent):
        """اختبار معالجة طلبات متزامنة"""
        messages = [
            "ما هي الخدمات المتاحة؟",
            "أريد حجز موعد",
            "كم سعر تنظيف الأسنان؟",
            "ما هي أوقات العمل؟",
            "من هم الأطباء المتاحون؟"
        ]
        
        async def process_message(msg: str):
            conv_input = ConversationInput(
                channel="whatsapp",
                user_id="concurrent_test_user",
                message=msg,
                locale="ar-SA"
            )
            start_time = time.perf_counter()
            output = await chat_agent.handle_message(conv_input)
            end_time = time.perf_counter()
            return {
                "message": msg,
                "response_time": end_time - start_time,
                "success": output.reply_text is not None
            }
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*[process_message(msg) for msg in messages])
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        avg_response_time = np.mean([r["response_time"] for r in results])
        
        # جميع الطلبات يجب أن تنجح
        assert all(r["success"] for r in results)
        # الوقت الإجمالي يجب أن يكون أقل من مجموع الأوقات الفردية (بسبب التزامن)
        assert total_time < sum(r["response_time"] for r in results)
        
        print(f"\n✅ Concurrent requests total time: {total_time:.2f}s")
        print(f"✅ Average response time: {avg_response_time:.2f}s")


class TestLoad:
    """اختبارات الحمل"""
    
    @pytest.mark.asyncio
    async def test_load_10_requests(self, chat_agent):
        """اختبار حمل 10 طلبات متتالية"""
        message = "ما هي الخدمات المتاحة؟"
        response_times = []
        
        start_time = time.perf_counter()
        for i in range(10):
            conv_input = ConversationInput(
                channel="whatsapp",
                user_id=f"load_test_user_{i}",
                message=message,
                locale="ar-SA"
            )
            
            req_start = time.perf_counter()
            output = await chat_agent.handle_message(conv_input)
            req_end = time.perf_counter()
            
            response_times.append(req_end - req_start)
            assert output.reply_text is not None
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        avg_time = np.mean(response_times)
        p95_time = np.percentile(response_times, 95)
        
        assert total_time < 60.0  # 10 طلبات يجب أن تكتمل في أقل من دقيقة
        assert avg_time < 6.0  # متوسط وقت الاستجابة يجب أن يكون أقل من 6 ثواني
        
        print(f"\n✅ Load test (10 requests):")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average: {avg_time:.2f}s")
        print(f"   P95: {p95_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_load_20_requests(self, chat_agent):
        """اختبار حمل 20 طلب متتالي"""
        message = "أريد حجز موعد"
        response_times = []
        errors = 0
        
        start_time = time.perf_counter()
        for i in range(20):
            try:
                conv_input = ConversationInput(
                    channel="whatsapp",
                    user_id=f"load_test_user_{i}",
                    message=message,
                    locale="ar-SA"
                )
                
                req_start = time.perf_counter()
                output = await chat_agent.handle_message(conv_input)
                req_end = time.perf_counter()
                
                response_times.append(req_end - req_start)
                assert output.reply_text is not None
            except Exception as e:
                errors += 1
                print(f"Error in request {i}: {str(e)}")
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # يجب أن يكون معدل الأخطاء أقل من 10%
        error_rate = (errors / 20) * 100
        assert error_rate < 10.0
        
        if response_times:
            avg_time = np.mean(response_times)
            assert total_time < 120.0  # 20 طلب يجب أن تكتمل في أقل من دقيقتين
            
            print(f"\n✅ Load test (20 requests):")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Average: {avg_time:.2f}s")
            print(f"   Errors: {errors} ({error_rate:.1f}%)")


class TestMemoryUsage:
    """اختبارات استخدام الذاكرة"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_single_request(self, chat_agent):
        """اختبار استخدام الذاكرة لطلب واحد"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        conv_input = ConversationInput(
            channel="whatsapp",
            user_id="memory_test_user",
            message="ما هي الخدمات المتاحة؟",
            locale="ar-SA"
        )
        
        await chat_agent.handle_message(conv_input)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # زيادة الذاكرة يجب أن تكون معقولة (< 50MB)
        assert memory_increase < 50.0
        
        print(f"\n✅ Memory usage:")
        print(f"   Initial: {initial_memory:.2f} MB")
        print(f"   Final: {final_memory:.2f} MB")
        print(f"   Increase: {memory_increase:.2f} MB")
    
    @pytest.mark.asyncio
    async def test_memory_usage_multiple_requests(self, chat_agent):
        """اختبار استخدام الذاكرة لعدة طلبات"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        messages = [
            "ما هي الخدمات المتاحة؟",
            "أريد حجز موعد",
            "كم سعر تنظيف الأسنان؟",
            "ما هي أوقات العمل؟",
            "من هم الأطباء المتاحون؟"
        ]
        
        for message in messages:
            conv_input = ConversationInput(
                channel="whatsapp",
                user_id="memory_test_user",
                message=message,
                locale="ar-SA"
            )
            await chat_agent.handle_message(conv_input)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # زيادة الذاكرة يجب أن تكون معقولة (< 100MB لـ 5 طلبات)
        assert memory_increase < 100.0
        
        print(f"\n✅ Memory usage (5 requests):")
        print(f"   Initial: {initial_memory:.2f} MB")
        print(f"   Final: {final_memory:.2f} MB")
        print(f"   Increase: {memory_increase:.2f} MB")


class TestAPIEndpoints:
    """اختبارات أداء API Endpoints"""
    
    def test_root_endpoint_performance(self, client):
        """اختبار أداء root endpoint"""
        response_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            response = client.get("/")
            end_time = time.perf_counter()
            response_times.append(end_time - start_time)
            assert response.status_code == 200
        
        avg_time = np.mean(response_times)
        assert avg_time < 0.1  # يجب أن يكون أسرع من 100ms
        
        print(f"\n✅ Root endpoint average response time: {avg_time*1000:.2f}ms")
    
    def test_health_check_performance(self, client):
        """اختبار أداء health check endpoint"""
        response_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            response = client.get("/health")
            end_time = time.perf_counter()
            response_times.append(end_time - start_time)
            assert response.status_code == 200
        
        avg_time = np.mean(response_times)
        assert avg_time < 0.1  # يجب أن يكون أسرع من 100ms
        
        print(f"\n✅ Health check average response time: {avg_time*1000:.2f}ms")

