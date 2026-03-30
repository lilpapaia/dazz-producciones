"""
Tests for /suppliers/autoinvoice endpoints.
Cloudinary, PDF generation, and email mocked.
"""

import pytest
from unittest.mock import patch, MagicMock
from contextlib import ExitStack
from tests.conftest import auth_header
from tests.mocks import mock_autoinvoice_pdf, mock_email_send


def patch_autoinvoice():
    """Context manager to mock all autoinvoice external services."""
    class Ctx:
        def __enter__(self):
            self.stack = ExitStack()
            self.stack.__enter__()
            self.stack.enter_context(patch("app.routes.autoinvoice.generate_autoinvoice_pdf", return_value=mock_autoinvoice_pdf()))
            cloud_mock = MagicMock(return_value={"secure_url": "https://res.cloudinary.com/test/raw/upload/v1/autoinv.pdf"})
            self.stack.enter_context(patch("cloudinary.uploader.upload", cloud_mock))
            self.stack.enter_context(patch("app.routes.autoinvoice.send_autoinvoice_notification", mock_email_send))
            return self
        def __exit__(self, *a):
            self.stack.__exit__(*a)
    return Ctx()


class TestNextNumber:
    def test_next_number(self, client, admin_token, company_dazz):
        r = client.get(f"/suppliers/autoinvoice/next-number?company_id={company_dazz.id}", headers=auth_header(admin_token))
        assert r.status_code == 200
        data = r.json()
        assert "invoice_number" in data
        assert "company_name" in data

    def test_company_not_found(self, client, admin_token):
        r = client.get("/suppliers/autoinvoice/next-number?company_id=99999", headers=auth_header(admin_token))
        assert r.status_code == 404


class TestSupplierSearch:
    def test_search_returns_results(self, client, admin_token, supplier_user):
        r = client.get("/suppliers/autoinvoice/supplier-search?q=Test", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert len(r.json()) >= 1
        assert r.json()[0]["name"] == "Test Supplier SL"

    def test_search_short_query(self, client, admin_token):
        r = client.get("/suppliers/autoinvoice/supplier-search?q=T", headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.json() == []


class TestGenerate:
    def test_generate_success(self, client, admin_token, company_dazz, supplier_user, project_dazz):
        with patch_autoinvoice():
            r = client.post("/suppliers/autoinvoice/generate", json={
                "company_id": company_dazz.id,
                "supplier_id": supplier_user.id,
                "invoice_number": "DAZZCR-2026-099",
                "date": "15/01/2026",
                "concept": "Test service",
                "base_amount": 1000.0,
                "iva_percentage": 0.21,
                "irpf_percentage": 0.15,
                "oc_number": project_dazz.creative_code,
            }, headers=auth_header(admin_token))
        assert r.status_code == 200
        data = r.json()
        assert data["invoice_number"] == "DAZZCR-2026-099"
        assert data["final_total"] == 1060.0  # 1000 + 210 - 150

    def test_duplicate_invoice_number(self, client, admin_token, company_dazz, supplier_user, supplier_invoice, project_dazz):
        with patch_autoinvoice():
            r = client.post("/suppliers/autoinvoice/generate", json={
                "company_id": company_dazz.id,
                "supplier_id": supplier_user.id,
                "invoice_number": supplier_invoice.invoice_number,  # Already exists
                "date": "15/01/2026",
                "concept": "Dup",
                "base_amount": 100.0,
                "iva_percentage": 0.21,
                "irpf_percentage": 0.0,
                "oc_number": project_dazz.creative_code,
            }, headers=auth_header(admin_token))
        assert r.status_code == 409

    def test_supplier_not_found(self, client, admin_token, company_dazz, project_dazz):
        with patch_autoinvoice():
            r = client.post("/suppliers/autoinvoice/generate", json={
                "company_id": company_dazz.id,
                "supplier_id": 99999,
                "invoice_number": "X-001",
                "date": "15/01/2026",
                "concept": "X",
                "base_amount": 100.0,
                "iva_percentage": 0.21,
                "irpf_percentage": 0.0,
                "oc_number": project_dazz.creative_code,
            }, headers=auth_header(admin_token))
        assert r.status_code == 404

    def test_company_not_found(self, client, admin_token, supplier_user, project_dazz):
        with patch_autoinvoice():
            r = client.post("/suppliers/autoinvoice/generate", json={
                "company_id": 99999,
                "supplier_id": supplier_user.id,
                "invoice_number": "X-002",
                "date": "15/01/2026",
                "concept": "X",
                "base_amount": 100.0,
                "iva_percentage": 0.21,
                "irpf_percentage": 0.0,
                "oc_number": project_dazz.creative_code,
            }, headers=auth_header(admin_token))
        assert r.status_code == 404


class TestPreview:
    def test_preview_returns_pdf(self, client, admin_token, company_dazz, supplier_user):
        with patch("app.routes.autoinvoice.generate_autoinvoice_pdf", return_value=mock_autoinvoice_pdf()):
            r = client.post("/suppliers/autoinvoice/preview", json={
                "company_id": company_dazz.id,
                "supplier_id": supplier_user.id,
                "invoice_number": "PREV-001",
                "date": "15/01/2026",
                "concept": "Preview test",
                "base_amount": 500.0,
                "iva_percentage": 0.21,
                "irpf_percentage": 0.0,
                "oc_number": "OC-TEST",
            }, headers=auth_header(admin_token))
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"

    def test_preview_requires_admin(self, client, boss_token, company_dazz, supplier_user):
        r = client.post("/suppliers/autoinvoice/preview", json={
            "company_id": company_dazz.id,
            "supplier_id": supplier_user.id,
            "invoice_number": "X",
            "date": "01/01/2026",
            "concept": "X",
            "base_amount": 100.0,
            "iva_percentage": 0.21,
            "irpf_percentage": 0.0,
            "oc_number": "OC-X",
        }, headers=auth_header(boss_token))
        assert r.status_code == 403
