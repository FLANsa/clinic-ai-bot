"""
Functional tests for Admin FAQ endpoints
"""
import pytest


class TestAdminFAQ:
    """اختبارات Admin FAQ Endpoints"""
    
    def test_list_faqs_unauthenticated(self, test_client):
        """اختبار list FAQs بدون authentication"""
        response = test_client.get("/admin/faqs/")
        assert response.status_code == 403
    
    def test_list_faqs_authenticated(self, authenticated_client):
        """اختبار list FAQs مع authentication"""
        response = authenticated_client.get("/admin/faqs/")
        assert response.status_code == 200
        assert "faqs" in response.json()
    
    def test_create_faq(self, authenticated_client):
        """اختبار إنشاء FAQ جديد"""
        faq_data = {
            "question": "سؤال الاختبار؟",
            "answer": "إجابة الاختبار",
            "tags": [],
            "is_active": True
        }
        response = authenticated_client.post("/admin/faqs/", json=faq_data)
        assert response.status_code in [200, 201]
        assert response.json()["question"] == faq_data["question"]
    
    def test_create_faq_validation_error(self, authenticated_client):
        """اختبار validation error عند إنشاء FAQ"""
        # Missing required fields
        faq_data = {
            "answer": "إجابة فقط"
        }
        response = authenticated_client.post("/admin/faqs/", json=faq_data)
        assert response.status_code == 422

