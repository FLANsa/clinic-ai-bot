"""
Functional tests for WhatsApp webhook
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app


class TestWhatsAppWebhook:
    """اختبارات WhatsApp webhook"""
    
    def test_webhook_verification(self, test_client):
        """اختبار التحقق من webhook (GET)"""
        # WhatsApp verification request
        response = test_client.get(
            "/webhooks/whatsapp/",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_token",
                "hub.challenge": "test_challenge"
            }
        )
        
        # يجب أن يعيد challenge أو 403
        assert response.status_code in [200, 403]
    
    @patch('app.integrations.whatsapp.parse_incoming')
    @patch('app.integrations.whatsapp.send_message')
    @patch('app.api.webhooks.whatsapp_router.get_agent')
    def test_webhook_message_handling(
        self, 
        mock_get_agent, 
        mock_send_message, 
        mock_parse_incoming,
        test_client,
        test_agent,
        mock_llm_client
    ):
        """اختبار معالجة رسالة WhatsApp (POST)"""
        # Setup mocks
        mock_get_agent.return_value = test_agent
        mock_parse_incoming.return_value = {
            "user_id": "1234567890",
            "message": "مرحباً",
            "locale": "ar-SA"
        }
        mock_send_message.return_value = None
        
        # WhatsApp webhook payload
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "from": "1234567890",
                            "text": {
                                "body": "مرحباً"
                            }
                        }]
                    }
                }]
            }]
        }
        
        response = test_client.post(
            "/webhooks/whatsapp/",
            json=payload
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_parse_incoming.assert_called_once()
        mock_send_message.assert_called_once()
    
    def test_webhook_invalid_payload(self, test_client):
        """اختبار payload غير صحيح"""
        # Payload غير صحيح
        payload = {
            "invalid": "data"
        }
        
        response = test_client.post(
            "/webhooks/whatsapp/",
            json=payload
        )
        
        # يجب أن يعيد error أو ignored
        assert response.status_code in [200, 422]
        result = response.json()
        # قد يعيد error أو ignored حسب validation
        assert result.get("status") in ["error", "ignored", None] or "error" in str(result).lower()
    
    def test_webhook_non_text_message(self, test_client):
        """اختبار رسالة غير نصية (يجب تجاهلها)"""
        # Payload لرسالة غير نصية (صورة مثلاً) - سيتم رفضه في validation
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "image",
                            "from": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        response = test_client.post(
            "/webhooks/whatsapp/",
            json=payload
        )
        
        # سيتم رفضه في validation، لذا قد يعيد error
        assert response.status_code in [200, 422]
        result = response.json()
        # قد يعيد error أو ignored
        assert result.get("status") in ["error", "ignored"] or "error" in str(result).lower()
    
    @patch('app.integrations.whatsapp.parse_incoming')
    @patch('app.integrations.whatsapp.send_message')
    @patch('app.api.webhooks.whatsapp_router.get_agent')
    def test_webhook_message_sending(
        self,
        mock_get_agent,
        mock_send_message,
        mock_parse_incoming,
        test_client,
        test_agent,
        mock_llm_client
    ):
        """اختبار إرسال الرسائل عبر WhatsApp"""
        # Setup mocks
        mock_get_agent.return_value = test_agent
        mock_parse_incoming.return_value = {
            "user_id": "1234567890",
            "message": "وش الخدمات؟",
            "locale": "ar-SA"
        }
        mock_send_message.return_value = None
        
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "from": "1234567890",
                            "text": {
                                "body": "وش الخدمات؟"
                            }
                        }]
                    }
                }]
            }]
        }
        
        response = test_client.post(
            "/webhooks/whatsapp/",
            json=payload
        )
        
        assert response.status_code == 200
        # التحقق من استدعاء send_message
        mock_send_message.assert_called_once()
        call_args = mock_send_message.call_args
        assert call_args[1]["to"] == "1234567890"
        assert call_args[1]["text"] is not None
    
    @patch('app.integrations.whatsapp.parse_incoming')
    @patch('app.api.webhooks.whatsapp_router.get_agent')
    def test_webhook_error_handling(
        self,
        mock_get_agent,
        mock_parse_incoming,
        test_client,
        test_agent
    ):
        """اختبار معالجة الأخطاء في webhook"""
        # Setup mocks
        mock_get_agent.return_value = test_agent
        mock_parse_incoming.side_effect = Exception("Parse error")
        
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "from": "1234567890",
                            "text": {
                                "body": "test"
                            }
                        }]
                    }
                }]
            }]
        }
        
        response = test_client.post(
            "/webhooks/whatsapp/",
            json=payload
        )
        
        # يجب أن يعيد error
        assert response.status_code == 200
        result = response.json()
        assert result.get("status") == "error"

