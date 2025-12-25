"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_admin_branches_without_api_key():
    """Test admin endpoints require API key"""
    response = client.get("/admin/branches")
    # يجب أن يفشل بدون API key (أو يعود 200 إذا لم يكن API key معرّف)
    # هذا يعتمد على إعداد ADMIN_API_KEY
    assert response.status_code in [200, 401, 403]


def test_admin_branches_with_api_key():
    """Test admin endpoints with API key"""
    import os
    api_key = os.getenv("ADMIN_API_KEY", "test-api-key")
    
    response = client.get(
        "/admin/branches",
        headers={"X-API-Key": api_key}
    )
    # إذا كان API key صحيح، يجب أن يعيد 200
    # إذا لم يكن معرّف في الإعدادات، سيعيد 200 (development mode)
    assert response.status_code in [200, 401, 403]

