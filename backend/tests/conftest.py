"""
pytest configuration and fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.core.llm_client import LLMClient
from app.core.agent import ChatAgent


# Test database (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def llm_client():
    """Mock LLM client for testing"""
    return LLMClient()


@pytest.fixture
def chat_agent(db_session, llm_client):
    """Create a ChatAgent instance for testing"""
    return ChatAgent(
        llm_client=llm_client,
        db_session=db_session,
        embeddings_client=None,
        vector_store=None
    )

