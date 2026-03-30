"""
Tests for /suppliers admin endpoints.
All external services mocked.
"""

import pytest
from unittest.mock import patch
from tests.conftest import auth_header


class TestDashboard:
    def test_dashboard_stats(self, client, admin_token, supplier_user, supplier_invoice):
        r = client.get("/suppliers/dashboard/stats", headers=auth_header(admin_token))
        assert r.status_code == 200
        data = r.json()
        assert "pending_invoices" in data
        assert "active_suppliers" in data
        assert data["active_suppliers"] >= 1

    def test_dashboard_requires_admin(self, client, boss_token):
        r = client.get("/suppliers/dashboard/stats", headers=auth_header(boss_token))
        assert r.status_code == 403


class TestListSuppliers:
    def test_list_all(self, client, admin_token, supplier_user):
        r = client.get("/suppliers", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_filter_active(self, client, admin_token, supplier_user):
        r = client.get("/suppliers?status=ACTIVE", headers=auth_header(admin_token))
        assert r.status_code == 200
        for s in r.json():
            assert s["is_active"] is True

    def test_requires_admin(self, client, worker_token):
        r = client.get("/suppliers", headers=auth_header(worker_token))
        assert r.status_code == 403


class TestSupplierDetail:
    def test_get_detail(self, client, admin_token, supplier_user):
        r = client.get(f"/suppliers/{supplier_user.id}", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.json()["name"] == "Test Supplier SL"
        assert r.json()["email"] == "supplier@test.dazz.com"

    def test_not_found(self, client, admin_token):
        r = client.get("/suppliers/99999", headers=auth_header(admin_token))
        assert r.status_code == 404

    def test_deactivate(self, client, admin_token, supplier_user):
        r = client.put(f"/suppliers/{supplier_user.id}/deactivate", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert "deactivated" in r.json()["message"].lower()

    def test_reactivate(self, client, admin_token, db_session, supplier_user):
        supplier_user.is_active = False
        supplier_user.status = "DEACTIVATED"
        db_session.commit()
        r = client.put(f"/suppliers/{supplier_user.id}/reactivate", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert "reactivated" in r.json()["message"].lower()

    def test_add_note(self, client, admin_token, supplier_user):
        r = client.post(
            f"/suppliers/{supplier_user.id}/notes",
            json={"note": "Test internal note"},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200

    def test_verify_cert(self, client, admin_token, db_session, supplier_user):
        supplier_user.ia_cert_verified = False
        db_session.commit()
        r = client.post(f"/suppliers/{supplier_user.id}/verify-cert", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_update_supplier(self, client, admin_token, supplier_user):
        r = client.put(
            f"/suppliers/{supplier_user.id}",
            json={"name": "Updated Name SL"},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200


class TestInvoiceManagement:
    def test_list_invoices(self, client, admin_token, supplier_invoice):
        r = client.get("/suppliers/invoices/all", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_invoice_detail(self, client, admin_token, supplier_invoice):
        r = client.get(f"/suppliers/invoices/{supplier_invoice.id}", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.json()["invoice_number"] == "SUP-2026-001"

    def test_invoice_not_found(self, client, admin_token):
        r = client.get("/suppliers/invoices/99999", headers=auth_header(admin_token))
        assert r.status_code == 404

    @patch("app.routes.suppliers.send_supplier_invoice_paid")
    def test_approve_then_pay(self, mock_email, client, admin_token, supplier_invoice):
        # Approve
        r1 = client.put(
            f"/suppliers/invoices/{supplier_invoice.id}/status",
            json={"status": "APPROVED"},
            headers=auth_header(admin_token),
        )
        assert r1.status_code == 200

        # Pay
        r2 = client.put(
            f"/suppliers/invoices/{supplier_invoice.id}/status",
            json={"status": "PAID"},
            headers=auth_header(admin_token),
        )
        assert r2.status_code == 200

    def test_invalid_transition(self, client, admin_token, supplier_invoice):
        # PENDING → PAID is not allowed (must go PENDING → APPROVED → PAID)
        r = client.put(
            f"/suppliers/invoices/{supplier_invoice.id}/status",
            json={"status": "PAID"},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 400

    @patch("app.services.supplier_storage.delete_invoice_pdf")
    def test_delete_invoice(self, mock_del_pdf, client, admin_token, supplier_invoice):
        r = client.delete(
            f"/suppliers/invoices/{supplier_invoice.id}",
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200


class TestInviteSupplier:
    @patch("app.routes.suppliers.send_supplier_invitation")
    def test_invite_success(self, mock_email, client, admin_token):
        r = client.post(
            "/suppliers/invite",
            json={"name": "New Supplier", "email": "newsupplier@test.com"},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 201
        assert r.json()["email"] == "newsupplier@test.com"

    @patch("app.routes.suppliers.send_supplier_invitation")
    def test_invite_duplicate_email(self, mock_email, client, admin_token, supplier_user):
        r = client.post(
            "/suppliers/invite",
            json={"name": "Dup", "email": "supplier@test.dazz.com"},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 400

    def test_invite_requires_admin(self, client, boss_token):
        r = client.post(
            "/suppliers/invite",
            json={"name": "X", "email": "x@test.com"},
            headers=auth_header(boss_token),
        )
        assert r.status_code == 403


class TestNotifications:
    def test_list_notifications(self, client, admin_token):
        r = client.get("/suppliers/notifications/all", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_mark_all_read(self, client, admin_token):
        r = client.put("/suppliers/notifications/read-all", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_delete_read(self, client, admin_token):
        r = client.delete("/suppliers/notifications/read", headers=auth_header(admin_token))
        assert r.status_code == 200


class TestOCManagement:
    def test_create_oc(self, client, admin_token, company_dazz):
        r = client.post(
            "/suppliers/ocs",
            json={"oc_number": "OC-NEWTEST001", "talent_name": "New Talent", "company_id": company_dazz.id},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 201
        assert r.json()["oc_number"] == "OC-NEWTEST001"

    def test_create_oc_duplicate(self, client, admin_token, supplier_oc, company_dazz):
        r = client.post(
            "/suppliers/ocs",
            json={"oc_number": supplier_oc.oc_number, "talent_name": "Dup", "company_id": company_dazz.id},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 400

    def test_list_prefixes(self, client, admin_token):
        r = client.get("/suppliers/ocs/prefixes", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_validate_oc_new(self, client, admin_token):
        r = client.get("/suppliers/ocs/validate-oc?oc=OC-DOESNOTEXIST999", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_check_nif(self, client, admin_token, supplier_oc):
        r = client.get(f"/suppliers/ocs/check-nif?nif={supplier_oc.nif_cif}", headers=auth_header(admin_token))
        assert r.status_code == 200

    def test_assign_oc_to_supplier(self, client, admin_token, supplier_user, supplier_oc):
        r = client.put(
            f"/suppliers/{supplier_user.id}/assign-oc",
            json={"oc_number": supplier_oc.oc_number},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200
