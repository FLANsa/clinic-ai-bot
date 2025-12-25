"""
Functional tests for Admin Analytics endpoints
"""
import pytest


class TestAdminAnalytics:
    """اختبارات Admin Analytics Endpoints"""
    
    def test_get_analytics_unauthenticated(self, test_client):
        """اختبار get analytics بدون authentication"""
        response = test_client.get("/admin/analytics/summary")
        # قد يعيد 403 (Forbidden) أو 422 (Validation Error) أو 401
        assert response.status_code in [403, 401, 422]
    
    def test_get_analytics_authenticated(self, authenticated_client):
        """اختبار get analytics مع authentication"""
        response = authenticated_client.get("/admin/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data or "analytics" in data or "total_conversations" in data
    
    def test_get_analytics_with_date_range(self, authenticated_client):
        """اختبار get analytics مع نطاق تاريخ"""
        from datetime import date, timedelta
        to_date = date.today()
        from_date = to_date - timedelta(days=30)
        
        response = authenticated_client.get(
            "/admin/analytics/summary",
            params={
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            }
        )
        assert response.status_code == 200

