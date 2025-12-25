"""
اختبارات وظيفية شاملة لجميع مكونات النظام
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.models import Branch, Doctor, Service, FAQ, Offer, Appointment, Conversation
from datetime import datetime, date
import json


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def api_key():
    """Test API key"""
    import os
    os.environ["API_KEY"] = "test_api_key_123"
    return "test_api_key_123"


@pytest.fixture
def authenticated_client(client, api_key):
    """Client with API key authentication"""
    client.headers["X-API-Key"] = api_key
    return client


class TestHealthAndRoot:
    """اختبارات Health Check و Root Endpoints"""
    
    def test_root_endpoint(self, client):
        """اختبار root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_health_check(self, client):
        """اختبار health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAdminBranches:
    """اختبارات Admin Branches Endpoints"""
    
    def test_list_branches_unauthenticated(self, client):
        """اختبار list branches بدون authentication"""
        response = client.get("/admin/branches/")
        assert response.status_code == 403
    
    def test_list_branches_authenticated(self, authenticated_client):
        """اختبار list branches مع authentication"""
        response = authenticated_client.get("/admin/branches/")
        assert response.status_code == 200
        assert "branches" in response.json()
    
    def test_create_branch(self, authenticated_client):
        """اختبار إنشاء branch جديد"""
        branch_data = {
            "name": "فرع الاختبار",
            "city": "الرياض",
            "address": "شارع الاختبار 123",
            "working_hours": {"sat_to_thu": "9:00 - 18:00"},
            "is_active": True
        }
        response = authenticated_client.post("/admin/branches/", json=branch_data)
        assert response.status_code in [200, 201]
        assert response.json()["name"] == branch_data["name"]
    
    def test_get_branch_by_id(self, authenticated_client):
        """اختبار الحصول على branch بالـ ID"""
        # إنشاء branch أولاً
        branch_data = {
            "name": "فرع للاختبار",
            "city": "جدة",
            "address": "شارع الاختبار",
            "working_hours": {},
            "is_active": True
        }
        create_response = authenticated_client.post("/admin/branches/", json=branch_data)
        branch_id = create_response.json()["id"]
        
        # الحصول على branch
        response = authenticated_client.get(f"/admin/branches/{branch_id}")
        assert response.status_code == 200
        assert response.json()["id"] == branch_id


class TestAdminDoctors:
    """اختبارات Admin Doctors Endpoints"""
    
    def test_list_doctors(self, authenticated_client):
        """اختبار list doctors"""
        response = authenticated_client.get("/admin/doctors/")
        assert response.status_code == 200
        assert "doctors" in response.json()
    
    def test_create_doctor(self, authenticated_client):
        """اختبار إنشاء doctor جديد"""
        # نحتاج branch أولاً
        branch_data = {
            "name": "فرع للأطباء",
            "city": "الرياض",
            "address": "شارع الأطباء",
            "working_hours": {},
            "is_active": True
        }
        branch_response = authenticated_client.post("/admin/branches/", json=branch_data)
        branch_id = branch_response.json()["id"]
        
        doctor_data = {
            "name": "د. أحمد الاختبار",
            "specialty": "طب الأسنان",
            "branch_id": branch_id,
            "is_active": True
        }
        response = authenticated_client.post("/admin/doctors/", json=doctor_data)
        assert response.status_code in [200, 201]
        assert response.json()["name"] == doctor_data["name"]


class TestAdminServices:
    """اختبارات Admin Services Endpoints"""
    
    def test_list_services(self, authenticated_client):
        """اختبار list services"""
        response = authenticated_client.get("/admin/services/")
        assert response.status_code == 200
        assert "services" in response.json()
    
    def test_create_service(self, authenticated_client):
        """اختبار إنشاء service جديد"""
        service_data = {
            "name": "تنظيف الأسنان",
            "description": "خدمة تنظيف شامل",
            "base_price": 200.0,
            "duration_minutes": 30,
            "is_active": True
        }
        response = authenticated_client.post("/admin/services/", json=service_data)
        assert response.status_code in [200, 201]
        assert response.json()["name"] == service_data["name"]


class TestAdminFAQ:
    """اختبارات Admin FAQ Endpoints"""
    
    def test_list_faqs(self, authenticated_client):
        """اختبار list FAQs"""
        response = authenticated_client.get("/admin/faq/")
        assert response.status_code == 200
        assert "faqs" in response.json()
    
    def test_create_faq(self, authenticated_client):
        """اختبار إنشاء FAQ جديد"""
        faq_data = {
            "question": "ما هي أوقات العمل؟",
            "answer": "نعمل من السبت إلى الخميس من 9 صباحاً إلى 6 مساءً",
            "is_active": True
        }
        response = authenticated_client.post("/admin/faq/", json=faq_data)
        assert response.status_code in [200, 201]
        assert response.json()["question"] == faq_data["question"]


class TestAdminOffers:
    """اختبارات Admin Offers Endpoints"""
    
    def test_list_offers(self, authenticated_client):
        """اختبار list offers"""
        response = authenticated_client.get("/admin/offers/")
        assert response.status_code == 200
        assert "offers" in response.json()
    
    def test_create_offer(self, authenticated_client):
        """اختبار إنشاء offer جديد"""
        offer_data = {
            "title": "عرض خاص",
            "description": "خصم 20% على جميع الخدمات",
            "discount_type": "percentage",
            "discount_value": 20,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "is_active": True
        }
        response = authenticated_client.post("/admin/offers/", json=offer_data)
        assert response.status_code in [200, 201]
        assert response.json()["title"] == offer_data["title"]


class TestAdminAppointments:
    """اختبارات Admin Appointments Endpoints"""
    
    def test_list_appointments(self, authenticated_client):
        """اختبار list appointments"""
        response = authenticated_client.get("/admin/appointments/")
        assert response.status_code == 200
        assert "appointments" in response.json()
    
    def test_create_appointment(self, authenticated_client):
        """اختبار إنشاء appointment جديد"""
        # نحتاج branch و service أولاً
        branch_data = {
            "name": "فرع للمواعيد",
            "city": "الرياض",
            "address": "شارع المواعيد",
            "working_hours": {},
            "is_active": True
        }
        branch_response = authenticated_client.post("/admin/branches/", json=branch_data)
        branch_id = branch_response.json()["id"]
        
        service_data = {
            "name": "كشف",
            "base_price": 100.0,
            "is_active": True
        }
        service_response = authenticated_client.post("/admin/services/", json=service_data)
        service_id = service_response.json()["id"]
        
        appointment_data = {
            "patient_name": "محمد الاختبار",
            "phone": "0501234567",
            "branch_id": branch_id,
            "service_id": service_id,
            "datetime": "2024-12-31T10:00:00",
            "channel": "whatsapp",
            "status": "pending"
        }
        response = authenticated_client.post("/admin/appointments/", json=appointment_data)
        assert response.status_code in [200, 201]
        assert response.json()["patient_name"] == appointment_data["patient_name"]


class TestAdminAnalytics:
    """اختبارات Admin Analytics Endpoints"""
    
    def test_get_analytics_summary(self, authenticated_client):
        """اختبار الحصول على analytics summary"""
        response = authenticated_client.get("/admin/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "conversations_by_channel" in data
        assert "avg_satisfaction" in data


class TestTestChat:
    """اختبارات Test Chat Endpoint"""
    
    def test_test_chat_endpoint(self, client):
        """اختبار test chat endpoint"""
        chat_data = {
            "message": "ما هي الخدمات المتاحة؟",
            "user_id": "test_user",
            "channel": "whatsapp"
        }
        response = client.post("/test/chat", json=chat_data)
        assert response.status_code == 200
        assert "reply" in response.json()
        assert response.json()["reply"] is not None


class TestWebhooks:
    """اختبارات Webhooks"""
    
    def test_whatsapp_webhook_verification(self, client):
        """اختبار WhatsApp webhook verification"""
        response = client.get("/webhooks/whatsapp/?hub.mode=subscribe&hub.challenge=test_challenge&hub.verify_token=test_token")
        # قد يكون 200 أو 403 حسب الإعدادات
        assert response.status_code in [200, 403]
    
    def test_whatsapp_webhook_post(self, client):
        """اختبار WhatsApp webhook POST"""
        # Mock webhook payload
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "test_entry",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test_phone_id"
                        },
                        "messages": [{
                            "from": "1234567890",
                            "id": "test_msg_id",
                            "text": {
                                "body": "مرحبا"
                            },
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        response = client.post("/webhooks/whatsapp/", json=payload)
        # قد يكون 200 أو 400 حسب validation
        assert response.status_code in [200, 400, 422]


class TestExport:
    """اختبارات Export Endpoints"""
    
    def test_export_conversations_csv(self, authenticated_client):
        """اختبار export conversations to CSV"""
        response = authenticated_client.get("/admin/export/conversations/csv")
        # قد يكون 200 أو 404 إذا لم توجد محادثات
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert "text/csv" in response.headers.get("content-type", "")


class TestReports:
    """اختبارات Reports Endpoints"""
    
    def test_daily_report(self, client):
        """اختبار daily report"""
        today = date.today().isoformat()
        response = client.get(f"/reports/daily/?date={today}")
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations_offhours" in data

