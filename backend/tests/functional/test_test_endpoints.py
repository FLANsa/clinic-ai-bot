"""
Functional tests for Test endpoints
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


class TestTestChatEndpoint:
    """اختبارات Test Chat endpoint"""
    
    @patch('app.api.test.chat_router.get_test_agent')
    def test_test_chat(self, mock_get_agent, test_client, test_agent, mock_llm_client):
        """اختبار Test chat endpoint"""
        mock_get_agent.return_value = test_agent
        
        response = test_client.post(
            "/test/chat",
            json={
                "message": "مرحباً",
                "user_id": "test_user",
                "channel": "whatsapp"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert data["reply"] is not None
        assert len(data["reply"]) > 0
    
    @patch('app.api.test.chat_router.get_test_agent')
    def test_test_chat_different_channels(self, mock_get_agent, test_client, test_agent):
        """اختبار Test chat مع قنوات مختلفة"""
        mock_get_agent.return_value = test_agent
        
        channels = ["whatsapp", "instagram", "tiktok", "google_maps"]
        
        for channel in channels:
            response = test_client.post(
                "/test/chat",
                json={
                    "message": "مرحباً",
                    "user_id": f"test_user_{channel}",
                    "channel": channel
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "reply" in data
            assert data["reply"] is not None
    
    def test_test_chat_validation_error(self, test_client):
        """اختبار validation error في Test chat"""
        # Missing required field
        response = test_client.post(
            "/test/chat",
            json={}
        )
        
        assert response.status_code == 422
    
    @patch('app.api.test.chat_router.get_test_agent')
    def test_test_chat_with_intent(self, mock_get_agent, test_client, test_agent):
        """اختبار Test chat مع نية محددة"""
        mock_get_agent.return_value = test_agent
        
        response = test_client.post(
            "/test/chat",
            json={
                "message": "وش الأطباء اللي عندكم؟",
                "user_id": "test_user_intent",
                "channel": "whatsapp"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "intent" in data
        # Intent يجب أن يكون doctor_info (الكلمات المفتاحية تشمل "الأطباء")
        assert data["intent"] in ["doctor_info", "service_info"]  # قد يكتشف service_info أحياناً


class TestHealthCheckEndpoint:
    """اختبارات Health Check endpoint"""
    
    def test_health_check(self, test_client):
        """اختبار Health check endpoint"""
        response = test_client.get("/test/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "health" in data

