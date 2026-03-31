"""
Autoinvoice endpoints — Admin generates invoices on behalf of suppliers.
Prefix: /suppliers/autoinvoice
"""

import logging
import re
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timezone

from config.database import get_db
from app.models.database import User, Company, Project, OCPrefix, ProjectStatus
from app.models.suppliers import (
    Supplier, SupplierInvoice, InvoiceStatus,
    NotificationRecipientType, NotificationEventType,
)
from app.services.notifications import create_notification as _notify
from app.models.supplier_schemas import AutoInvoiceRequest
from app.services.auth import get_current_admin_user
from app.services.encryption import decrypt_iban
from app.services.autoinvoice_pdf import generate_autoinvoice_pdf
from app.services.supplier_email import send_autoinvoice_notification

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

    # Build prefix from company (DB field with fallback)
    prefix = company.invoice_prefix or re.sub(r'[^A-Z]', '', company.name.upper())[:6] or "DAZZ"

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

    # Batch query: last invoice number per supplier
    supplier_ids = [s.id for s in suppliers]
    last_invoices = {}
    if supplier_ids:
        subq = db.query(
            SupplierInvoice.supplier_id,
            func.max(SupplierInvoice.id).label("max_id"),
        ).filter(
            SupplierInvoice.supplier_id.in_(supplier_ids)
        ).group_by(SupplierInvoice.supplier_id).subquery()

        rows = db.query(SupplierInvoice.supplier_id, SupplierInvoice.invoice_number).join(
            subq, SupplierInvoice.id == subq.c.max_id
        ).all()
        last_invoices = {r[0]: r[1] for r in rows}

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
            "last_invoice_number": last_invoices.get(s.id),
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
    service_total = round(body.base_amount + iva_amount - irpf_amount, 2)

    # FEAT-02: Calculate expenses (IRPF % inherited from main invoice)
    gastos_iva_amount = round(body.gastos_base * body.gastos_iva_percentage, 2)
    gastos_irpf_amount = round(body.gastos_base * body.irpf_percentage, 2)
    gastos_subtotal = round(body.gastos_base + gastos_iva_amount - gastos_irpf_amount, 2)
    final_total = round(service_total + gastos_subtotal, 2) if body.gastos_base > 0 else service_total

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
        gastos_base=body.gastos_base,
        gastos_iva_percentage=body.gastos_iva_percentage,
        gastos_iva_amount=gastos_iva_amount,
        gastos_irpf_amount=gastos_irpf_amount,
        gastos_subtotal=gastos_subtotal,
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
        slug = re.sub(r'[^a-z0-9]+', '_', supplier.name.lower().strip()).strip('_')[:60] or "unknown"
        folder = f"dazz-suppliers/autoinvoices/{slug}"
        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
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
    else:
        # Check if OC belongs to a permanent prefix → auto-create project
        oc_lower = body.oc_number.lower()
        oc_prefix = None
        if oc_lower.startswith("oc-"):
            active_prefixes = db.query(OCPrefix).filter(OCPrefix.active == True).all()
            for p in active_prefixes:
                if oc_lower.startswith(f"oc-{p.prefix.lower()}"):
                    oc_prefix = p
                    break

        if oc_prefix and oc_prefix.permanent_oc:
            project = Project(
                year=oc_prefix.year_format,
                send_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                creative_code=body.oc_number,
                company=company.name,
                owner_company_id=oc_prefix.company_id,
                owner_id=admin.id,
                responsible=admin.username,
                invoice_type=f"PRODUCCION{oc_prefix.year_format}",
                description=supplier.name,
                status=ProjectStatus.EN_CURSO,
            )
            db.add(project)
            db.flush()
            project_id = project.id
            logger.info(f"Auto-created project {project_id} for permanent OC {body.oc_number}")
        elif oc_prefix and not oc_prefix.permanent_oc:
            raise HTTPException(400, f"No existe proyecto con OC '{body.oc_number}'. Créalo primero.")

    # Duplicate invoice number check (SELECT FOR UPDATE on PostgreSQL)
    existing = db.query(SupplierInvoice.id).filter(
        SupplierInvoice.invoice_number == body.invoice_number,
    ).with_for_update().first()
    if existing:
        raise HTTPException(409, f"El número de factura '{body.invoice_number}' ya está registrado en el sistema.")

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
    db.flush()

    # Notify supplier + admin
    _notify(db, NotificationRecipientType.SUPPLIER, supplier.id,
            NotificationEventType.NEW_INVOICE, "Invoice received from DAZZ",
            f"{body.invoice_number} — {final_total:.2f} EUR generated by {company.name}",
            invoice_id=invoice.id, supplier_id=supplier.id)
    _notify(db, NotificationRecipientType.ADMIN, 0,
            NotificationEventType.NEW_INVOICE, "Autoinvoice generated",
            f"{body.invoice_number} for {supplier.name} — {final_total:.2f} EUR",
            invoice_id=invoice.id, supplier_id=supplier.id)
    try:
        db.commit()
    except Exception:
        db.rollback()
        try:
            from app.services.supplier_storage import delete_invoice_pdf
            delete_invoice_pdf(file_url)
        except Exception as e:
            logger.error(f"Cloudinary cleanup failed after rollback — orphan: {file_url}: {e}")
        raise

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
        "invoice_number": body.invoice_number,
        "supplier_name": supplier.name,
        "oc_number": body.oc_number,
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
    service_total = round(body.base_amount + iva_amount - irpf_amount, 2)

    gastos_iva_amount = round(body.gastos_base * body.gastos_iva_percentage, 2)
    gastos_irpf_amount = round(body.gastos_base * body.irpf_percentage, 2)
    gastos_subtotal = round(body.gastos_base + gastos_iva_amount - gastos_irpf_amount, 2)
    final_total = round(service_total + gastos_subtotal, 2) if body.gastos_base > 0 else service_total

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
        gastos_base=body.gastos_base,
        gastos_iva_percentage=body.gastos_iva_percentage,
        gastos_iva_amount=gastos_iva_amount,
        gastos_irpf_amount=gastos_irpf_amount,
        gastos_subtotal=gastos_subtotal,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{body.invoice_number}.pdf"'},
    )
