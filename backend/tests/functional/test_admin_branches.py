"""
Functional tests for Admin Branches endpoints
"""
import pytest
from datetime import datetime
import uuid


class TestAdminBranches:
    """اختبارات Admin Branches Endpoints"""
    
    def test_list_branches_unauthenticated(self, test_client):
        """اختبار list branches بدون authentication"""
        response = test_client.get("/admin/branches/")
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
            "working_hours": {"from": "9:00", "to": "21:00"},
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
            "working_hours": {"from": "9:00", "to": "21:00"},
            "is_active": True
        }
        create_response = authenticated_client.post("/admin/branches/", json=branch_data)
        branch_id = create_response.json()["id"]
        
        # الحصول على branch
        response = authenticated_client.get(f"/admin/branches/{branch_id}")
        assert response.status_code == 200
        assert response.json()["id"] == branch_id
    
    def test_create_branch_validation_error(self, authenticated_client):
        """اختبار validation error عند إنشاء branch"""
        # Missing required fields
        branch_data = {
            "name": "فرع بدون بيانات كاملة"
        }
        response = authenticated_client.post("/admin/branches/", json=branch_data)
        assert response.status_code == 422

