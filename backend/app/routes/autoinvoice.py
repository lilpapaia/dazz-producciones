"""
Autoinvoice endpoints — Admin generates invoices on behalf of suppliers.
Prefix: /suppliers/autoinvoice
"""

import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timezone
from io import BytesIO

from config.database import get_db
from app.models.database import User, Company, Project
from app.models.suppliers import (
    Supplier, SupplierInvoice, SupplierNotification, InvoiceStatus,
    NotificationRecipientType, NotificationEventType,
)
from app.models.supplier_schemas import AutoInvoiceRequest
from app.services.auth import get_current_admin_user
from app.services.encryption import decrypt_iban
from app.services.autoinvoice_pdf import generate_autoinvoice_pdf
from app.services.supplier_storage import save_invoice_pdf
from app.services.supplier_email import send_autoinvoice_notification
from app.services.supplier_ai import resolve_company_from_oc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suppliers/autoinvoice", tags=["Autoinvoice (Admin)"])


@router.get("/next-number")
async def get_next_invoice_number(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Get the next sequential invoice number for a company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(404, "Company not found")

    year = datetime.now(timezone.utc).year

    # Find the highest autoinvoice number for this company this year
    latest = db.query(SupplierInvoice.invoice_number).filter(
        SupplierInvoice.company_id == company_id,
        SupplierInvoice.is_autoinvoice == True,
        SupplierInvoice.invoice_number.like(f"%-{year}-%"),
    ).order_by(desc(SupplierInvoice.created_at)).first()

    next_seq = 1
    if latest and latest[0]:
        try:
            # Format: PREFIX-YEAR-SEQ (e.g. DAZZCR-2026-047)
            parts = latest[0].rsplit("-", 1)
            if len(parts) == 2:
                next_seq = int(parts[1]) + 1
        except (ValueError, IndexError):
            pass

    # Build prefix from company name
    name_upper = company.name.upper()
    if "DAZZLE MGMT" in name_upper:
        prefix = "DAZZMG"
    elif "DAZZLE AGENCY" in name_upper:
        prefix = "DAZZAG"
    elif "DIGITAL ADVERTISING" in name_upper:
        prefix = "DASSAD"
    elif "DAZZ CREATIVE" in name_upper:
        prefix = "DAZZCR"
    else:
        prefix = "DAZZ"

    invoice_number = f"{prefix}-{year}-{next_seq:03d}"

    return {
        "invoice_number": invoice_number,
        "company_name": company.name,
        "company_cif": company.cif,
        "company_address": company.address,
    }


@router.get("/supplier-search")
async def search_suppliers_for_autoinvoice(
    q: str = Query("", max_length=50),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Autocomplete: search active suppliers by name or NIF."""
    term = q.strip()
    if len(term) < 2:
        return []

    suppliers = db.query(Supplier).filter(
        Supplier.is_active == True,
        (Supplier.name.ilike(f"%{term}%") | Supplier.nif_cif.ilike(f"%{term}%")),
    ).limit(8).all()

    results = []
    for s in suppliers:
        iban = None
        if s.iban_encrypted:
            iban = decrypt_iban(s.iban_encrypted)

        results.append({
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "nif_cif": s.nif_cif,
            "address": s.address,
            "iban": iban,
        })

    return results


@router.post("/generate")
async def generate_autoinvoice(
    body: AutoInvoiceRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Generate autoinvoice: create PDF, upload to Cloudinary, create DB record, notify supplier."""
    # Validate company
    company = db.query(Company).filter(Company.id == body.company_id).first()
    if not company:
        raise HTTPException(404, "Company not found")

    # Validate supplier
    supplier = db.query(Supplier).filter(Supplier.id == body.supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    # Calculate amounts
    iva_amount = round(body.base_amount * body.iva_percentage, 2)
    irpf_amount = round(body.base_amount * body.irpf_percentage, 2)
    final_total = round(body.base_amount + iva_amount - irpf_amount, 2)

    # Decrypt IBAN
    supplier_iban = ""
    if supplier.iban_encrypted:
        supplier_iban = decrypt_iban(supplier.iban_encrypted) or ""

    # Generate PDF
    pdf_bytes = generate_autoinvoice_pdf(
        invoice_number=body.invoice_number,
        date=body.date,
        concept=body.concept,
        oc_number=body.oc_number,
        issuer_name=company.name,
        issuer_cif=company.cif or "",
        issuer_address=company.address or "",
        supplier_name=supplier.name,
        supplier_nif=supplier.nif_cif or "",
        supplier_address=supplier.address or "",
        supplier_iban=supplier_iban,
        base_amount=body.base_amount,
        iva_percentage=body.iva_percentage,
        iva_amount=iva_amount,
        irpf_percentage=body.irpf_percentage,
        irpf_amount=irpf_amount,
        final_total=final_total,
    )

    # Upload PDF to Cloudinary
    import tempfile
    import os
    temp_path = os.path.join("uploads", "suppliers", f"autoinv_{body.invoice_number.replace('/', '_')}.pdf")
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(pdf_bytes)

    try:
        import cloudinary.uploader
        folder = f"dazz-suppliers/autoinvoices/{supplier.id}"
        result = cloudinary.uploader.upload(
            temp_path,
            public_id=body.invoice_number.replace("/", "_").replace(" ", "_"),
            folder=folder,
            resource_type="raw",
            type="upload",
            overwrite=False,
        )
        file_url = result.get("secure_url", "")
        logger.info(f"Autoinvoice PDF uploaded: {file_url}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Resolve project_id from OC
    project_id = None
    project = db.query(Project).filter(
        Project.creative_code.ilike(body.oc_number)
    ).first()
    if project:
        project_id = project.id

    # Create invoice record
    invoice = SupplierInvoice(
        supplier_id=supplier.id,
        invoice_number=body.invoice_number,
        date=body.date,
        provider_name=supplier.name,
        nif_cif=supplier.nif_cif,
        iban=supplier_iban,
        oc_number=body.oc_number,
        project_id=project_id,
        company_id=company.id,
        base_amount=body.base_amount,
        iva_percentage=body.iva_percentage,
        iva_amount=iva_amount,
        irpf_percentage=body.irpf_percentage,
        irpf_amount=irpf_amount,
        final_total=final_total,
        currency="EUR",
        is_foreign=False,
        file_url=file_url,
        status=InvoiceStatus.PENDING,
        is_autoinvoice=True,
        ia_validation_result=None,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Notify supplier
    notif = SupplierNotification(
        recipient_type=NotificationRecipientType.SUPPLIER,
        recipient_id=supplier.id,
        event_type=NotificationEventType.NEW_INVOICE,
        title="Invoice received from DAZZ",
        message=f"{body.invoice_number} — {final_total:.2f} EUR generated by {company.name}",
        related_invoice_id=invoice.id,
        related_supplier_id=supplier.id,
    )
    db.add(notif)
    # Admin notification
    admin_notif = SupplierNotification(
        recipient_type=NotificationRecipientType.ADMIN,
        recipient_id=0,
        event_type=NotificationEventType.NEW_INVOICE,
        title="Autoinvoice generated",
        message=f"{body.invoice_number} for {supplier.name} — {final_total:.2f} EUR",
        related_invoice_id=invoice.id,
        related_supplier_id=supplier.id,
    )
    db.add(admin_notif)
    db.commit()

    # Send email (non-blocking)
    try:
        send_autoinvoice_notification(
            supplier.name, supplier.email,
            body.invoice_number, final_total, company.name
        )
    except Exception as e:
        logger.warning(f"Autoinvoice email failed: {e}")

    return {
        "message": "Autoinvoice generated successfully",
        "invoice_id": invoice.id,
        "file_url": file_url,
        "final_total": final_total,
    }


@router.post("/preview")
async def preview_autoinvoice(
    body: AutoInvoiceRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Generate autoinvoice PDF preview without saving."""
    from fastapi.responses import Response

    company = db.query(Company).filter(Company.id == body.company_id).first()
    if not company:
        raise HTTPException(404, "Company not found")

    supplier = db.query(Supplier).filter(Supplier.id == body.supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    iva_amount = round(body.base_amount * body.iva_percentage, 2)
    irpf_amount = round(body.base_amount * body.irpf_percentage, 2)
    final_total = round(body.base_amount + iva_amount - irpf_amount, 2)

    supplier_iban = ""
    if supplier.iban_encrypted:
        supplier_iban = decrypt_iban(supplier.iban_encrypted) or ""

    pdf_bytes = generate_autoinvoice_pdf(
        invoice_number=body.invoice_number,
        date=body.date,
        concept=body.concept,
        oc_number=body.oc_number,
        issuer_name=company.name,
        issuer_cif=company.cif or "",
        issuer_address=company.address or "",
        supplier_name=supplier.name,
        supplier_nif=supplier.nif_cif or "",
        supplier_address=supplier.address or "",
        supplier_iban=supplier_iban,
        base_amount=body.base_amount,
        iva_percentage=body.iva_percentage,
        iva_amount=iva_amount,
        irpf_percentage=body.irpf_percentage,
        irpf_amount=irpf_amount,
        final_total=final_total,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{body.invoice_number}.pdf"'},
    )
