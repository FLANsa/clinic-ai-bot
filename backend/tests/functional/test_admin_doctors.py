"""
Functional tests for Admin Doctors endpoints
"""
import pytest


class TestAdminDoctors:
    """اختبارات Admin Doctors Endpoints"""
    
    def test_list_doctors_unauthenticated(self, test_client):
        """اختبار list doctors بدون authentication"""
        response = test_client.get("/admin/doctors/")
        assert response.status_code == 403
    
    def test_list_doctors_authenticated(self, authenticated_client):
        """اختبار list doctors مع authentication"""
        response = authenticated_client.get("/admin/doctors/")
        assert response.status_code == 200
        assert "doctors" in response.json()
    
    def test_create_doctor(self, authenticated_client):
        """اختبار إنشاء doctor جديد"""
        doctor_data = {
            "name": "د. أحمد الاختبار",
            "specialty": "طب الأسنان",
            "bio": "طبيب أسنان متخصص",
            "is_active": True
        }
        response = authenticated_client.post("/admin/doctors/", json=doctor_data)
        assert response.status_code in [200, 201]
        assert response.json()["name"] == doctor_data["name"]
    
    def test_create_doctor_validation_error(self, authenticated_client):
        """اختبار validation error عند إنشاء doctor"""
        # Missing required fields
        doctor_data = {
            "specialty": "طب الأسنان"
        }
        response = authenticated_client.post("/admin/doctors/", json=doctor_data)
        assert response.status_code == 422

