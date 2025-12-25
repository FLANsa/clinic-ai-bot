"""
Functional tests for Admin Offers endpoints
"""
import pytest
from datetime import datetime, timedelta


class TestAdminOffers:
    """اختبارات Admin Offers Endpoints"""
    
    def test_list_offers_unauthenticated(self, test_client):
        """اختبار list offers بدون authentication"""
        response = test_client.get("/admin/offers/")
        assert response.status_code == 403
    
    def test_list_offers_authenticated(self, authenticated_client):
        """اختبار list offers مع authentication"""
        response = authenticated_client.get("/admin/offers/")
        assert response.status_code == 200
        assert "offers" in response.json()
    
    def test_create_offer(self, authenticated_client):
        """اختبار إنشاء offer جديد"""
        offer_data = {
            "title": "عرض الاختبار",
            "description": "وصف العرض",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "is_active": True
        }
        response = authenticated_client.post("/admin/offers/", json=offer_data)
        assert response.status_code in [200, 201]
        assert response.json()["title"] == offer_data["title"]
    
    def test_create_offer_validation_error(self, authenticated_client):
        """اختبار validation error عند إنشاء offer"""
        # Missing required fields
        offer_data = {
            "description": "وصف فقط"
        }
        response = authenticated_client.post("/admin/offers/", json=offer_data)
        assert response.status_code == 422

