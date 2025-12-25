"""
Functional tests for Admin Export endpoints
"""
import pytest


class TestAdminExport:
    """اختبارات Admin Export Endpoints"""
    
    def test_export_conversations_unauthenticated(self, test_client):
        """اختبار export conversations بدون authentication"""
        response = test_client.get("/admin/export/conversations")
        assert response.status_code == 403
    
    def test_export_conversations_authenticated(self, authenticated_client):
        """اختبار export conversations مع authentication"""
        response = authenticated_client.get("/admin/export/conversations")
        assert response.status_code == 200
        # يجب أن يعيد CSV
        assert response.headers.get("content-type") == "text/csv; charset=utf-8" or "csv" in response.headers.get("content-type", "").lower()

