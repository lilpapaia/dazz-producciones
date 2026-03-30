"""
Tests for /portal supplier portal endpoints.
All external services mocked.
"""

import io
import pytest
from unittest.mock import patch
from tests.conftest import auth_header
from tests.mocks import (
    mock_supplier_ai_extraction,
    mock_supplier_ai_validation_success,
    mock_email_send,
    mock_r2_upload,
    mock_r2_get_url,
    SUPPLIER_UPLOAD_PATCHES,
)


def supplier_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestValidateToken:
    def test_valid_token(self, client, supplier_invitation):
        r = client.get(f"/portal/register/validate/{supplier_invitation.token}")
        assert r.status_code == 200
        assert r.json()["valid"] is True
        assert r.json()["name"] == "Invited Supplier"

    def test_invalid_token(self, client):
        r = client.get("/portal/register/validate/nonexistent-token")
        assert r.status_code == 200
        assert r.json()["valid"] is False

    def test_expired_token(self, client, db_session, supplier_invitation):
        from datetime import datetime, timedelta, timezone
        supplier_invitation.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session.commit()
        r = client.get(f"/portal/register/validate/{supplier_invitation.token}")
        assert r.status_code == 200
        assert r.json()["valid"] is False


class TestRegister:
    def test_register_success(self, client, supplier_invitation):
        r = client.post("/portal/register", json={
            "token": supplier_invitation.token,
            "name": "New Supplier Corp",
            "password": "SecurePass123!",
            "gdpr_consent": True,
        })
        assert r.status_code == 201
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["supplier_id"] > 0

    def test_register_invalid_token(self, client):
        r = client.post("/portal/register", json={
            "token": "bad-token",
            "name": "X",
            "password": "SecurePass123!",
            "gdpr_consent": True,
        })
        assert r.status_code == 400

    def test_register_no_gdpr(self, client, supplier_invitation):
        r = client.post("/portal/register", json={
            "token": supplier_invitation.token,
            "name": "No GDPR",
            "password": "SecurePass123!",
            "gdpr_consent": False,
        })
        assert r.status_code == 400
        assert "GDPR" in r.json()["detail"]

    def test_register_weak_password(self, client, supplier_invitation):
        r = client.post("/portal/register", json={
            "token": supplier_invitation.token,
            "name": "Weak",
            "password": "short",
            "gdpr_consent": True,
        })
        assert r.status_code == 422

    def test_register_duplicate_email(self, client, db_session, supplier_invitation, supplier_user):
        # Change invitation email to match existing supplier
        supplier_invitation.email = supplier_user.email
        db_session.commit()
        r = client.post("/portal/register", json={
            "token": supplier_invitation.token,
            "name": "Dup Email",
            "password": "SecurePass123!",
            "gdpr_consent": True,
        })
        assert r.status_code == 400


class TestLogin:
    def test_login_success(self, client, supplier_user):
        r = client.post("/portal/login", json={
            "email": "supplier@test.dazz.com",
            "password": "TestSupplier123!",
        })
        assert r.status_code == 200
        assert "access_token" in r.json()
        assert "refresh_token" in r.json()

    def test_login_wrong_password(self, client, supplier_user):
        r = client.post("/portal/login", json={
            "email": "supplier@test.dazz.com",
            "password": "wrongpassword",
        })
        assert r.status_code == 401

    def test_login_nonexistent(self, client):
        r = client.post("/portal/login", json={
            "email": "nobody@test.com",
            "password": "whatever",
        })
        assert r.status_code == 401

    def test_login_deactivated(self, client, db_session, supplier_user):
        supplier_user.is_active = False
        db_session.commit()
        r = client.post("/portal/login", json={
            "email": "supplier@test.dazz.com",
            "password": "TestSupplier123!",
        })
        assert r.status_code == 403


class TestProfile:
    def test_get_profile(self, client, supplier_token):
        r = client.get("/portal/profile", headers=supplier_header(supplier_token))
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test Supplier SL"
        assert data["iban_masked"] is not None  # IBAN present and masked

    def test_profile_no_auth(self, client):
        r = client.get("/portal/profile")
        assert r.status_code in (401, 403)  # HTTPBearer auto_error returns 403


class TestInvoices:
    def test_list_invoices(self, client, supplier_token, supplier_invoice):
        r = client.get("/portal/invoices", headers=supplier_header(supplier_token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_list_received(self, client, supplier_token):
        r = client.get("/portal/invoices/received", headers=supplier_header(supplier_token))
        assert r.status_code == 200

    def test_request_deletion(self, client, supplier_token, supplier_invoice):
        import json
        r = client.request(
            "DELETE",
            f"/portal/invoices/{supplier_invoice.id}",
            content=json.dumps({"reason": "Uploaded by mistake"}),
            headers={**supplier_header(supplier_token), "Content-Type": "application/json"},
        )
        assert r.status_code == 200
        assert "requested" in r.json()["message"].lower()

    def test_delete_non_pending_fails(self, client, supplier_token, db_session, supplier_invoice):
        import json
        from app.models.suppliers import InvoiceStatus
        supplier_invoice.status = InvoiceStatus.APPROVED
        db_session.commit()
        r = client.request(
            "DELETE",
            f"/portal/invoices/{supplier_invoice.id}",
            content=json.dumps({"reason": "test"}),
            headers={**supplier_header(supplier_token), "Content-Type": "application/json"},
        )
        assert r.status_code == 400


class TestSummary:
    def test_financial_summary(self, client, supplier_token, supplier_invoice):
        r = client.get("/portal/summary", headers=supplier_header(supplier_token))
        assert r.status_code == 200
        data = r.json()
        assert "pending_amount" in data
        assert "total_invoices" in data


class TestNotifications:
    def test_list_notifications(self, client, supplier_token):
        r = client.get("/portal/notifications", headers=supplier_header(supplier_token))
        assert r.status_code == 200

    def test_mark_all_read(self, client, supplier_token):
        r = client.put("/portal/notifications/read-all", headers=supplier_header(supplier_token))
        assert r.status_code == 200


class TestAccountActions:
    def test_request_data_change(self, client, supplier_token):
        r = client.post(
            "/portal/request-data-change",
            json={"name": "Updated Name SL", "phone": "+34600999888"},
            headers=supplier_header(supplier_token),
        )
        assert r.status_code == 200

    def test_request_data_change_empty(self, client, supplier_token):
        r = client.post(
            "/portal/request-data-change",
            json={},
            headers=supplier_header(supplier_token),
        )
        assert r.status_code == 400

    def test_request_deactivation(self, client, supplier_token):
        r = client.post(
            "/portal/request-deactivation",
            json={"reason": "No longer working with DAZZ"},
            headers=supplier_header(supplier_token),
        )
        assert r.status_code == 200
