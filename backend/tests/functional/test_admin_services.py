"""
Functional tests for Admin Services endpoints
"""
import pytest


class TestAdminServices:
    """اختبارات Admin Services Endpoints"""
    
    def test_list_services_unauthenticated(self, test_client):
        """اختبار list services بدون authentication"""
        response = test_client.get("/admin/services/")
        assert response.status_code == 403
    
    def test_list_services_authenticated(self, authenticated_client):
        """اختبار list services مع authentication"""
        response = authenticated_client.get("/admin/services/")
        assert response.status_code == 200
        assert "services" in response.json()
    
    def test_create_service(self, authenticated_client):
        """اختبار إنشاء service جديد"""
        service_data = {
            "name": "خدمة الاختبار",
            "base_price": 500.0,
            "description": "وصف الخدمة",
            "is_active": True
        }
        response = authenticated_client.post("/admin/services/", json=service_data)
        assert response.status_code in [200, 201]
        assert response.json()["name"] == service_data["name"]
    
    def test_create_service_validation_error(self, authenticated_client):
        """اختبار validation error عند إنشاء service"""
        # Missing required fields
        service_data = {
            "base_price": 500.0
        }
        response = authenticated_client.post("/admin/services/", json=service_data)
        assert response.status_code == 422

