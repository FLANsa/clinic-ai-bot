"""
pytest configuration and fixtures for functional tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import uuid
import os

from app.db.base import Base
from app.core.llm_client import LLMClient
from app.core.agent import ChatAgent
from app.db.models import Doctor, Service, Branch, Offer, FAQ, Appointment, Conversation
from app.config import get_settings

settings = get_settings()

# Test database - استخدام PostgreSQL للاختبارات (يدعم UUID)
# إذا لم يكن متاحاً، سيتم استخدام SQLite مع String للـ UUID
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)

if TEST_DB_URL and "postgresql" in TEST_DB_URL:
    # استخدام PostgreSQL
    engine = create_engine(TEST_DB_URL, echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # استخدام SQLite - نحتاج لاستخدام String للـ UUID
    # لكن هذا معقد، لذا سنستخدم PostgreSQL للاختبارات
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        echo=False
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # لا نحذف الجداول من قاعدة البيانات الرئيسية
        if "sqlite" not in str(engine.url):
            # في PostgreSQL، نحذف البيانات فقط
            pass
        else:
            Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_client(test_db, mock_llm_client):
    """FastAPI test client with database and LLM client override"""
    from app.db.session import get_db
    from app.core.agent import ChatAgent
    from app.main import app
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    def override_get_agent():
        return ChatAgent(
            llm_client=mock_llm_client,
            db_session=test_db
        )
    
    def override_get_test_agent():
        return ChatAgent(
            llm_client=mock_llm_client,
            db_session=test_db
        )
    
    # Override dependencies
    from app.api.webhooks.whatsapp_router import get_agent as whatsapp_get_agent
    from app.api.test.chat_router import get_test_agent as chat_get_test_agent
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[whatsapp_get_agent] = override_get_agent
    app.dependency_overrides[chat_get_test_agent] = override_get_test_agent
    
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_llm_client():
    """Mock LLM client that returns predefined responses"""
    mock = MagicMock(spec=LLMClient)
    mock.chat = AsyncMock(return_value="أهلاً وسهلاً! الحمد لله بخير. وش اللي أقدر أساعدك فيه اليوم؟")
    return mock


@pytest.fixture
def test_agent(test_db, mock_llm_client):
    """Create a ChatAgent instance for testing"""
    return ChatAgent(
        llm_client=mock_llm_client,
        db_session=test_db
    )


@pytest.fixture
def api_key():
    """Test API key"""
    os.environ["API_KEY"] = "test_api_key_123"
    return "test_api_key_123"


@pytest.fixture
def authenticated_client(test_client, api_key):
    """Client with API key authentication"""
    test_client.headers["X-API-Key"] = api_key
    return test_client


@pytest.fixture
def sample_doctor(test_db, sample_branch):
    """Create a sample doctor for testing"""
    doctor = Doctor(
        id=uuid.uuid4(),
        name="د. محمد العلي",
        specialty="طب الأسنان",
        branch_id=sample_branch.id,
        bio="متخصص في تبييض الأسنان",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    test_db.add(doctor)
    test_db.commit()
    test_db.refresh(doctor)
    return doctor


@pytest.fixture
def sample_service(test_db):
    """Create a sample service for testing"""
    service = Service(
        id=uuid.uuid4(),
        name="تبييض الأسنان",
        base_price=800.0,
        description="خدمة تبييض الأسنان",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    test_db.add(service)
    test_db.commit()
    test_db.refresh(service)
    return service


@pytest.fixture
def sample_branch(test_db):
    """Create a sample branch for testing"""
    branch = Branch(
        id=uuid.uuid4(),
        name="فرع الرياض",
        city="الرياض",
        address="حي النخيل، شارع الملك فهد",
        phone="0112345678",
        working_hours={"from": "9:00", "to": "21:00"},
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    test_db.add(branch)
    test_db.commit()
    test_db.refresh(branch)
    return branch


@pytest.fixture
def sample_offer(test_db):
    """Create a sample offer for testing"""
    offer = Offer(
        id=uuid.uuid4(),
        title="عرض خاص على تبييض الأسنان",
        description="خصم 20% للجلسة الأولى",
        discount_type="percentage",
        discount_value=20.0,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    test_db.add(offer)
    test_db.commit()
    test_db.refresh(offer)
    return offer


@pytest.fixture
def sample_faq(test_db):
    """Create a sample FAQ for testing"""
    faq = FAQ(
        id=uuid.uuid4(),
        question="وش ساعات العمل؟",
        answer="ساعات العمل من 9 صباحاً إلى 9 مساءً",
        tags=[],  # JSON column accepts list
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    test_db.add(faq)
    test_db.commit()
    test_db.refresh(faq)
    return faq
