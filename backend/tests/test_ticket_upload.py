"""
Tests for POST /tickets/{project_id}/upload — the full upload flow.

All external services (Claude AI, Cloudinary, Exchange Rate) are mocked
using context managers to avoid fixture injection issues with @patch decorators.
"""

import io
import pytest
from unittest.mock import patch
from tests.conftest import auth_header
from tests.mocks import (
    mock_claude_extraction_success,
    mock_claude_extraction_low_confidence,
    mock_claude_extraction_math_error,
    mock_claude_extraction_error,
    mock_claude_extraction_foreign_usd,
    mock_cloudinary_upload,
    mock_exchange_rate,
    UPLOAD_PATCHES,
)


def make_fake_file(filename="test_ticket.jpg", content=b"fake image content", content_type="image/jpeg"):
    """Create a fake file tuple for multipart upload."""
    return ("file", (filename, io.BytesIO(content), content_type))


def patch_externals(claude_fn=mock_claude_extraction_success):
    """Returns a combined context manager that patches all external services."""
    from contextlib import ExitStack

    class PatchContext:
        def __enter__(self):
            self.stack = ExitStack()
            self.stack.__enter__()
            self.stack.enter_context(patch(UPLOAD_PATCHES["cloudinary"], side_effect=mock_cloudinary_upload))
            self.stack.enter_context(patch(UPLOAD_PATCHES["claude_ai"], side_effect=claude_fn))
            self.stack.enter_context(patch(UPLOAD_PATCHES["exchange_rate"], side_effect=mock_exchange_rate))
            return self

        def __exit__(self, *args):
            self.stack.__exit__(*args)

    return PatchContext()


class TestTicketUploadSuccess:
    """Happy path upload tests."""

    def test_upload_valid_image(self, client, admin_token, project_dazz):
        with patch_externals():
            response = client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file()],
                headers=auth_header(admin_token),
            )
        assert response.status_code == 201
        data = response.json()
        assert data["ticket"]["provider"] == "Mock Proveedor SL"
        assert data["ticket"]["final_total"] == 121.0
        assert data["ticket"]["currency"] == "EUR"
        assert data["ticket"]["file_hash"] is not None

    def test_upload_pdf(self, client, admin_token, project_dazz):
        with patch_externals():
            response = client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file("invoice.pdf", b"%PDF-1.4 fake pdf content", "application/pdf")],
                headers=auth_header(admin_token),
            )
        assert response.status_code == 201

    def test_upload_updates_project_totals(self, client, admin_token, project_dazz):
        old_count = project_dazz.tickets_count
        with patch_externals():
            client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file()],
                headers=auth_header(admin_token),
            )
        proj = client.get(f"/projects/{project_dazz.id}", headers=auth_header(admin_token))
        assert proj.json()["tickets_count"] == old_count + 1
        assert proj.json()["total_amount"] == 121.0


class TestTicketUploadValidation:
    """File validation tests — rejected before AI, no mocks needed."""

    def test_upload_no_file(self, client, admin_token, project_dazz):
        response = client.post(
            f"/tickets/{project_dazz.id}/upload",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 422

    def test_upload_forbidden_extension(self, client, admin_token, project_dazz):
        response = client.post(
            f"/tickets/{project_dazz.id}/upload",
            files=[make_fake_file("malware.exe", b"evil content", "application/x-msdownload")],
            headers=auth_header(admin_token),
        )
        assert response.status_code == 400

    def test_upload_project_not_found(self, client, admin_token):
        response = client.post(
            "/tickets/99999/upload",
            files=[make_fake_file()],
            headers=auth_header(admin_token),
        )
        assert response.status_code == 404

    def test_upload_forbidden_other_company(self, client, boss_other_token, project_dazz):
        response = client.post(
            f"/tickets/{project_dazz.id}/upload",
            files=[make_fake_file()],
            headers=auth_header(boss_other_token),
        )
        assert response.status_code == 403


class TestTicketUploadDuplicate:
    """Hash and invoice number duplicate detection."""

    def test_duplicate_hash_blocked(self, client, admin_token, project_dazz):
        content = b"same content for both uploads"
        with patch_externals():
            r1 = client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file("first.jpg", content)],
                headers=auth_header(admin_token),
            )
            assert r1.status_code == 201

            r2 = client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file("second.jpg", content)],
                headers=auth_header(admin_token),
            )
        assert r2.status_code == 409
        assert r2.json()["detail"]["code"] == "duplicate_hash"

    def test_duplicate_invoice_number_warning(self, client, admin_token, project_dazz):
        with patch_externals():
            r1 = client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file("a.jpg", b"content a")],
                headers=auth_header(admin_token),
            )
            assert r1.status_code == 201

            r2 = client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file("b.jpg", b"content b")],
                headers=auth_header(admin_token),
            )
        assert r2.status_code == 201
        assert r2.json()["duplicate_invoice_warning"] is not None
        assert r2.json()["duplicate_invoice_warning"]["invoice_number"] == "F-2026-001"


class TestTicketUploadAIEdgeCases:
    """AI extraction edge cases — low confidence, math errors, failures."""

    def test_low_confidence_warning(self, client, admin_token, project_dazz):
        with patch_externals(claude_fn=mock_claude_extraction_low_confidence):
            response = client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file("low.jpg", b"low confidence content")],
                headers=auth_header(admin_token),
            )
        assert response.status_code == 201
        notes = response.json()["ticket"]["notes"] or ""
        assert "confianza" in notes.lower() or "confidence" in notes.lower()

    def test_math_incoherence_warning(self, client, admin_token, project_dazz):
        with patch_externals(claude_fn=mock_claude_extraction_math_error):
            response = client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file("math.jpg", b"math error content")],
                headers=auth_header(admin_token),
            )
        assert response.status_code == 201
        notes = response.json()["ticket"]["notes"] or ""
        assert "incoherencia" in notes.lower() or "math" in notes.lower()

    @pytest.mark.xfail(reason="BUG: TicketResponse.date has min_length=1 but error tickets set date='' — schema needs Optional or empty allowed")
    def test_ai_failure_creates_error_ticket(self, client, admin_token, project_dazz):
        with patch_externals(claude_fn=mock_claude_extraction_error):
            response = client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file("broken.jpg", b"ai will fail content")],
                headers=auth_header(admin_token),
            )
        assert response.status_code == 201
        ticket = response.json()["ticket"]
        assert ticket["provider"] == "Error en extracción"
        assert ticket["final_total"] == 0.0


class TestTicketUploadForeignCurrency:
    """Foreign currency upload with exchange rate conversion."""

    def test_usd_invoice_converted(self, client, admin_token, project_dazz):
        with patch_externals(claude_fn=mock_claude_extraction_foreign_usd):
            response = client.post(
                f"/tickets/{project_dazz.id}/upload",
                files=[make_fake_file("usd.jpg", b"usd invoice content")],
                headers=auth_header(admin_token),
            )
        assert response.status_code == 201
        ticket = response.json()["ticket"]
        assert ticket["is_foreign"] is True
        assert ticket["currency"] == "USD"
        assert ticket["exchange_rate"] == 0.92
        assert ticket["foreign_total"] == 220.0
        # EUR amounts converted: 200 * 0.92 = 184.0
        assert ticket["base_amount"] == 184.0
