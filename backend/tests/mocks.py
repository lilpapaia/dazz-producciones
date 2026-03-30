"""
Centralized mocks for external services.
Used across test modules to avoid calling real APIs.
"""


def mock_claude_extraction_success(*args, **kwargs):
    """Mock Claude AI extraction returning valid ticket data."""
    return {
        "provider": "Mock Proveedor SL",
        "date": "15/01/2026",
        "base_amount": 100.0,
        "iva_amount": 21.0,
        "iva_percentage": 21.0,
        "total_with_iva": 121.0,
        "irpf_percentage": 0.0,
        "irpf_amount": 0.0,
        "final_total": 121.0,
        "invoice_number": "F-2026-001",
        "type": "factura",
        "is_foreign": False,
        "currency": "EUR",
        "country_code": "ES",
        "confidence": 0.95,
    }


def mock_claude_extraction_low_confidence(*args, **kwargs):
    """Mock Claude AI with confidence below threshold."""
    data = mock_claude_extraction_success()
    data["confidence"] = 0.3
    return data


def mock_claude_extraction_math_error(*args, **kwargs):
    """Mock Claude AI with math incoherence (base + IVA != total)."""
    data = mock_claude_extraction_success()
    data["final_total"] = 999.99  # Doesn't match base(100) + iva(21) = 121
    return data


def mock_claude_extraction_error(*args, **kwargs):
    """Mock Claude AI failure."""
    return {"error": "AI extraction failed", "raw_response": "", "confidence": 0.0}


def mock_claude_extraction_foreign_usd(*args, **kwargs):
    """Mock Claude AI extraction for a USD invoice."""
    return {
        "provider": "US Vendor Inc",
        "date": "20/02/2026",
        "base_amount": 200.0,
        "iva_amount": 20.0,
        "iva_percentage": 10.0,
        "total_with_iva": 220.0,
        "irpf_percentage": 0.0,
        "irpf_amount": 0.0,
        "final_total": 220.0,
        "invoice_number": "INV-US-001",
        "type": "factura",
        "is_foreign": True,
        "currency": "USD",
        "country_code": "US",
        "confidence": 0.90,
        "foreign_amount": 200.0,
        "foreign_total": 220.0,
        "foreign_tax_amount": 20.0,
    }


def mock_cloudinary_upload(*args, **kwargs):
    """Mock Cloudinary upload returning fake URL."""
    return {
        "url": "https://res.cloudinary.com/test/image/upload/v1/test.webp",
        "pages": ["https://res.cloudinary.com/test/image/upload/v1/page1.webp"],
        "pdf_url": None,
    }


def mock_cloudinary_delete(*args, **kwargs):
    """Mock Cloudinary delete — no-op."""
    pass


def mock_exchange_rate(*args, **kwargs):
    """Mock exchange rate API returning 0.92 EUR/USD."""
    return 0.92


def mock_email_send(*args, **kwargs):
    """Mock Brevo email send — no-op."""
    pass


def mock_r2_upload(*args, **kwargs):
    """Mock R2 bank cert upload — returns fake key."""
    return "dazz-suppliers/certs/test/cert_test.pdf"


def mock_r2_get_url(*args, **kwargs):
    """Mock R2 signed URL — returns fake URL."""
    return "https://r2.test.com/signed/cert_test.pdf?token=fake"


def mock_r2_delete(*args, **kwargs):
    """Mock R2 delete — no-op."""
    pass


def mock_supplier_ai_extraction(*args, **kwargs):
    """Mock supplier invoice AI extraction."""
    return {
        "provider_name": "Test Supplier SL",
        "date": "15/01/2026",
        "invoice_number": "SUP-2026-099",
        "oc_number": "OC-TEST001",
        "base_amount": 500.0,
        "iva_percentage": 21.0,
        "iva_amount": 105.0,
        "irpf_percentage": 0.0,
        "irpf_amount": 0.0,
        "final_total": 605.0,
        "currency": "EUR",
        "nif_cif": "B11223344",
        "iban": "ES7921000813610123456789",
    }


def mock_supplier_ai_validation_success(*args, **kwargs):
    """Mock supplier invoice validation — all valid."""
    return {
        "valid": True,
        "errors": [],
        "warnings": [],
        "oc_status": "FOUND",
        "company_id": 1,
        "project_id": None,
        "iban_match": True,
    }


def mock_autoinvoice_pdf(*args, **kwargs):
    """Mock PDF generation — returns fake bytes."""
    return b"%PDF-1.4 fake autoinvoice content"


# Common patch targets for tickets upload flow
UPLOAD_PATCHES = {
    "cloudinary": "app.routes.tickets.upload_ticket_file",
    "claude_ai": "app.routes.tickets.extract_ticket_data",
    "exchange_rate": "app.routes.tickets.get_historical_exchange_rate",
}

# Patch targets for supplier portal upload flow
SUPPLIER_UPLOAD_PATCHES = {
    "extract": "app.routes.supplier_portal.extract_supplier_invoice",
    "validate": "app.routes.supplier_portal.validate_supplier_invoice",
    "save_pdf": "app.routes.supplier_portal.save_invoice_pdf",
    "save_cert": "app.routes.supplier_portal.save_bank_cert",
    "get_cert_url": "app.routes.supplier_portal.get_bank_cert_url",
}

# Patch targets for autoinvoice flow
AUTOINVOICE_PATCHES = {
    "pdf_gen": "app.routes.autoinvoice.generate_autoinvoice_pdf",
    "cloudinary": "cloudinary.uploader.upload",
    "email": "app.routes.autoinvoice.send_autoinvoice_notification",
}
