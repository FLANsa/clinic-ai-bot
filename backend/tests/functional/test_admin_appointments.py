"""
Functional tests for Admin Appointments endpoints
"""
import pytest
from datetime import datetime, timedelta


class TestAdminAppointments:
    """اختبارات Admin Appointments Endpoints"""
    
    def test_list_appointments_unauthenticated(self, test_client):
        """اختبار list appointments بدون authentication"""
        response = test_client.get("/admin/appointments/")
        assert response.status_code == 403
    
    def test_list_appointments_authenticated(self, authenticated_client):
        """اختبار list appointments مع authentication"""
        response = authenticated_client.get("/admin/appointments/")
        assert response.status_code == 200
        assert "appointments" in response.json()
    
    def test_create_appointment(self, authenticated_client, sample_doctor, sample_service):
        """اختبار إنشاء appointment جديد"""
        appointment_data = {
            "patient_name": "محمد أحمد",
            "patient_phone": "0501234567",
            "doctor_id": str(sample_doctor.id),
            "service_id": str(sample_service.id),
            "appointment_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "status": "scheduled"
        }
        response = authenticated_client.post("/admin/appointments/", json=appointment_data)
        assert response.status_code in [200, 201]
        assert response.json()["patient_name"] == appointment_data["patient_name"]
    
    def test_create_appointment_validation_error(self, authenticated_client):
        """اختبار validation error عند إنشاء appointment"""
        # Missing required fields
        appointment_data = {
            "patient_name": "محمد"
        }
        response = authenticated_client.post("/admin/appointments/", json=appointment_data)
        assert response.status_code == 422

