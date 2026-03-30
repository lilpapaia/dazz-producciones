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


# Common patch targets for tickets upload flow
UPLOAD_PATCHES = {
    "cloudinary": "app.routes.tickets.upload_ticket_file",
    "claude_ai": "app.routes.tickets.extract_ticket_data",
    "exchange_rate": "app.routes.tickets.get_historical_exchange_rate",
}
