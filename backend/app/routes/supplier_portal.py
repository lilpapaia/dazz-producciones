"""
Endpoints del portal de proveedores — Solo proveedores autenticados.
Prefijo: /portal
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone
from typing import Optional, List
import hashlib

from config.database import get_db
from app.models.database import User
from app.models.supplier_schemas import (
    ValidateTokenResponse, RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse, RefreshRequest, ProfileResponse,
    PortalInvoiceResponse, DeleteInvoiceRequest, SummaryResponse,
)
from app.models.suppliers import (
    Supplier, SupplierInvoice, SupplierOC, SupplierNotification,
    SupplierInvitation, InvoiceStatus, SupplierStatus, SupplierType,
    NotificationRecipientType, NotificationEventType,
)
from app.services.supplier_auth import (
    get_password_hash, verify_password,
    create_supplier_access_token, create_supplier_refresh_token,
    validate_supplier_refresh_token, revoke_supplier_refresh_token,
    get_current_active_supplier,
)
from app.services.supplier_ai import (
    extract_supplier_invoice, validate_supplier_invoice, resolve_company_from_oc,
)
from app.services.supplier_storage import save_invoice_pdf, save_bank_cert, get_invoice_pdf_url, get_bank_cert_url
from app.services.encryption import encrypt_iban, decrypt_iban
from app.services.validators import validate_pdf_bytes, sanitize_filename
from app.services.supplier_ai import format_date_for_response
from app.services.supplier_email import (
    send_supplier_welcome,
    send_supplier_invoice_received,
    send_supplier_ia_rejected,
    send_admin_new_registration,
    send_admin_new_invoice,
    ADMIN_EMAIL,
)

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/portal", tags=["Supplier Portal"])


def _notify(db: Session, recipient_type, recipient_id: int, event_type,
            title: str, message: str, invoice_id=None, supplier_id=None):
    notif = SupplierNotification(
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        event_type=event_type,
        title=title,
        message=message,
        related_invoice_id=invoice_id,
        related_supplier_id=supplier_id,
    )
    db.add(notif)


# ============================================
# REGISTRATION
# ============================================

@router.get("/register/validate/{token}", response_model=ValidateTokenResponse)
@limiter.limit("10/minute")
async def validate_invitation_token(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
):
    """Validate invitation token without consuming it."""
    invitation = db.query(SupplierInvitation).filter(
        SupplierInvitation.token == token,
        SupplierInvitation.used_at == None,
        SupplierInvitation.expires_at > datetime.now(timezone.utc),
    ).first()

    if not invitation:
        return ValidateTokenResponse(valid=False)

    return ValidateTokenResponse(valid=True, name=invitation.name, email=invitation.email)


@router.post("/register", response_model=RegisterResponse, status_code=201)
@limiter.limit("5/hour")
async def register_supplier(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Complete supplier registration with invitation token."""
    # Validate token (one-time use)
    invitation = db.query(SupplierInvitation).filter(
        SupplierInvitation.token == body.token,
        SupplierInvitation.used_at == None,
        SupplierInvitation.expires_at > datetime.now(timezone.utc),
    ).first()

    if not invitation:
        raise HTTPException(400, "Invalid, expired, or already used invitation token")

    if not body.gdpr_consent:
        raise HTTPException(400, "GDPR consent is required to register")

    # Check email uniqueness
    if db.query(Supplier).filter(Supplier.email == invitation.email).first():
        raise HTTPException(400, "A supplier with this email already exists")

    # Mark token as used (one-time)
    invitation.used_at = datetime.now(timezone.utc)

    # NIF/CIF matching for influencer OC
    oc_id = None
    supplier_type = SupplierType.GENERAL
    if body.nif_cif:
        normalized = body.nif_cif.strip().upper().replace(" ", "").replace("-", "").replace(".", "")
        oc_match = db.query(SupplierOC).all()
        for oc in oc_match:
            if oc.nif_cif:
                oc_nif = oc.nif_cif.strip().upper().replace(" ", "").replace("-", "").replace(".", "")
                if normalized == oc_nif:
                    oc_id = oc.id
                    supplier_type = SupplierType.INFLUENCER
                    break

    # Create supplier
    email_hash = hashlib.sha256(invitation.email.lower().encode()).hexdigest()
    iban_bytes = encrypt_iban(body.iban) if body.iban else None

    supplier = Supplier(
        name=body.name,
        email=invitation.email,
        email_hash=email_hash,
        hashed_password=get_password_hash(body.password),
        nif_cif=body.nif_cif,
        phone=body.phone,
        address=body.address,
        iban_encrypted=iban_bytes,
        supplier_type=supplier_type,
        status=SupplierStatus.ACTIVE,
        oc_id=oc_id,
        gdpr_consent=True,
        gdpr_consent_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    # Create tokens
    access_token = create_supplier_access_token(supplier.id, supplier.email)
    refresh_token = create_supplier_refresh_token(db, supplier.id)

    # Notifications
    _notify(db, NotificationRecipientType.ADMIN, 0, NotificationEventType.REGISTRATION,
            "New Supplier Registered", f"{supplier.name} ({supplier.email})",
            supplier_id=supplier.id)
    db.commit()

    # Emails (non-blocking)
    try:
        send_supplier_welcome(supplier.name, supplier.email)
    except Exception:
        pass
    try:
        send_admin_new_registration(ADMIN_EMAIL, supplier.name, supplier.email)
    except Exception:
        pass

    return RegisterResponse(
        message="Registration successful",
        supplier_id=supplier.id,
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ============================================
# AUTH
# ============================================

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login_supplier(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    supplier = db.query(Supplier).filter(Supplier.email == body.email).first()

    if not supplier or not verify_password(body.password, supplier.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    if not supplier.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account deactivated")

    access_token = create_supplier_access_token(supplier.id, supplier.email)
    refresh_token = create_supplier_refresh_token(db, supplier.id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        supplier={
            "id": supplier.id,
            "name": supplier.name,
            "email": supplier.email,
            "supplier_type": supplier.supplier_type.value if supplier.supplier_type else "GENERAL",
        },
    )


@router.post("/refresh")
async def refresh_token(
    body: RefreshRequest,
    db: Session = Depends(get_db),
):
    rt = validate_supplier_refresh_token(db, body.refresh_token)
    if not rt:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    supplier = db.query(Supplier).filter(Supplier.id == rt.supplier_id).first()
    if not supplier or not supplier.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Supplier not found or inactive")

    access_token = create_supplier_access_token(supplier.id, supplier.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout_supplier(
    body: RefreshRequest,
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    revoked = revoke_supplier_refresh_token(db, body.refresh_token, supplier_id=supplier.id)
    if not revoked:
        raise HTTPException(400, "Refresh token not found or already revoked")
    return {"message": "Logged out successfully"}


# ============================================
# PROFILE
# ============================================

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    oc_number = None
    if supplier.oc_id:
        oc = db.query(SupplierOC).filter(SupplierOC.id == supplier.oc_id).first()
        oc_number = oc.oc_number if oc else None

    # Mask IBAN for supplier view: show country code + last 4 digits
    iban_masked = None
    if supplier.iban_encrypted:
        raw = decrypt_iban(supplier.iban_encrypted)
        if raw:
            raw = raw.replace(" ", "")
            if len(raw) >= 6:
                iban_masked = raw[:2] + "** **** **** **** **" + raw[-4:]
            elif len(raw) >= 4:
                iban_masked = "****" + raw[-4:]
            else:
                iban_masked = "****"
        else:
            iban_masked = "****"

    return ProfileResponse(
        id=supplier.id, name=supplier.name, email=supplier.email,
        nif_cif=supplier.nif_cif, phone=supplier.phone, address=supplier.address,
        iban_masked=iban_masked,
        supplier_type=supplier.supplier_type.value if supplier.supplier_type else "GENERAL",
        oc_number=oc_number,
        created_at=supplier.created_at,
    )


# ============================================
# BANK CERTIFICATE
# ============================================

@router.post("/bank-cert")
async def upload_bank_cert(
    file: UploadFile = File(...),
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    """Upload bank certificate PDF (required after registration)."""
    contents = await file.read()
    validate_pdf_bytes(contents, max_size=10 * 1024 * 1024)

    cert_key = save_bank_cert(file, supplier.id, contents=contents)
    supplier.bank_cert_url = cert_key
    db.commit()

    return {"message": "Bank certificate uploaded", "key": cert_key}


@router.get("/bank-cert-url")
async def get_my_bank_cert_url(
    supplier: Supplier = Depends(get_current_active_supplier),
):
    """Generate a signed URL (15min) for the authenticated supplier's bank certificate."""
    if not supplier.bank_cert_url:
        raise HTTPException(404, "No bank certificate uploaded")
    return {"url": get_bank_cert_url(supplier.bank_cert_url)}


# ============================================
# INVOICES
# ============================================

@router.post("/invoices/upload")
@limiter.limit("10/hour")
async def upload_invoice(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    supplier: Supplier = Depends(get_current_active_supplier),
):
    """Upload invoice PDF → AI extraction → validation → Cloudinary → create record."""
    import json
    import shutil

    # Validate file (magic bytes + size)
    contents = await file.read()
    validate_pdf_bytes(contents, max_size=10 * 1024 * 1024)

    # Save to temp file for AI extraction (Cloudinary upload happens AFTER validation)
    import uuid as _uuid
    temp_id = _uuid.uuid4().hex[:8]
    temp_path = os.path.join("uploads", "suppliers", f"tmp_ai_{temp_id}.pdf")
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    with open(temp_path, "wb") as out:
        out.write(contents)

    try:
        # AI extraction on local temp file
        extracted = extract_supplier_invoice(temp_path, "application/pdf")

        if extracted.get("error"):
            raise HTTPException(422, f"Could not process PDF: {extracted.get('error')}")

        # Validation against DB
        validation = validate_supplier_invoice(extracted, supplier.id, db)

        if not validation["valid"]:
            # IA rejected — notify supplier
            try:
                send_supplier_ia_rejected(
                    supplier.name, supplier.email,
                    extracted.get("invoice_number", "unknown"),
                    validation["errors"],
                )
            except Exception:
                pass

            _notify(db, NotificationRecipientType.ADMIN, 0,
                    NotificationEventType.IA_REJECTED, "AI Rejected Invoice",
                    f"Invoice from {supplier.name}: {'; '.join(validation['errors'])}",
                    supplier_id=supplier.id)
            db.commit()

            return JSONResponse(
                status_code=422,
                content={
                    "detail": {
                        "message": "Invoice validation failed",
                        "errors": validation["errors"],
                        "warnings": validation["warnings"],
                    }
                },
            )

        # Ensure file_pages column exists (ALTER TABLE before any ORM query)
        from sqlalchemy import text as sa_text
        try:
            db.execute(sa_text("ALTER TABLE supplier_invoices ADD COLUMN IF NOT EXISTS file_pages TEXT"))
            db.commit()
        except Exception:
            db.rollback()

        # Validation passed → upload to Cloudinary (public + page images)
        upload_result = save_invoice_pdf(file, supplier.id, contents=contents)

        # All validated invoices start as PENDING (OC must exist)
        invoice_status = InvoiceStatus.PENDING

        # Create invoice record (file_pages not in ORM — saved via raw SQL after)
        invoice = SupplierInvoice(
            supplier_id=supplier.id,
            invoice_number=extracted.get("invoice_number", ""),
            date=extracted.get("date", ""),
            provider_name=extracted.get("provider", supplier.name),
            nif_cif=extracted.get("nif_cif"),
            iban=extracted.get("iban"),
            oc_number=extracted.get("oc_number", ""),
            project_id=validation["project_id"],
            company_id=validation["company_id"],
            base_amount=extracted.get("base_amount", 0.0),
            iva_percentage=extracted.get("iva_percentage", 0.0),
            iva_amount=extracted.get("iva_amount", 0.0),
            irpf_percentage=extracted.get("irpf_percentage", 0.0),
            irpf_amount=extracted.get("irpf_amount", 0.0),
            final_total=extracted.get("final_total", 0.0),
            currency=extracted.get("currency", "EUR"),
            is_foreign=extracted.get("is_foreign", False),
            file_url=upload_result["url"],
            status=invoice_status,
            ia_validation_result=json.dumps(validation, default=str),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        # Save file_pages via raw SQL (column not in ORM)
        if upload_result.get("pages"):
            try:
                db.execute(sa_text("UPDATE supplier_invoices SET file_pages = :fp WHERE id = :id"),
                    {"fp": json.dumps(upload_result["pages"]), "id": invoice.id})
                db.commit()
            except Exception:
                pass

        # Store parsed date via raw SQL (column not in ORM model during migration)
        date_parsed = validation.get("date_parsed")
        if date_parsed:
            from sqlalchemy import text
            try:
                db.execute(
                    text("UPDATE supplier_invoices SET date_parsed = :dp WHERE id = :id"),
                    {"dp": date_parsed, "id": invoice.id},
                )
                db.commit()
            except Exception:
                pass  # Column may not exist yet — non-blocking

    finally:
        # Always clean up temp file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass

    # Notifications
    _notify(db, NotificationRecipientType.ADMIN, 0,
            NotificationEventType.NEW_INVOICE, "New Invoice Submitted",
            f"{supplier.name} — {invoice.invoice_number} ({invoice.final_total:.2f} EUR)",
            invoice_id=invoice.id, supplier_id=supplier.id)
    _notify(db, NotificationRecipientType.SUPPLIER, supplier.id,
            NotificationEventType.NEW_INVOICE, "Invoice Received",
            f"Invoice {invoice.invoice_number} submitted successfully",
            invoice_id=invoice.id, supplier_id=supplier.id)
    db.commit()

    # Emails (non-blocking)
    try:
        send_supplier_invoice_received(supplier.name, supplier.email, invoice.invoice_number)
    except Exception:
        pass
    try:
        send_admin_new_invoice(ADMIN_EMAIL, supplier.name, invoice.invoice_number)
    except Exception:
        pass

    return {
        "message": "Invoice uploaded successfully",
        "invoice_id": invoice.id,
        "status": invoice_status.value,
        "warnings": validation["warnings"],
    }


@router.get("/invoices", response_model=List[PortalInvoiceResponse])
async def list_my_invoices(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    query = db.query(SupplierInvoice).filter(SupplierInvoice.supplier_id == supplier.id)

    if status_filter:
        query = query.filter(SupplierInvoice.status == status_filter)

    invoices = query.order_by(desc(SupplierInvoice.created_at)).offset(offset).limit(limit).all()

    return [PortalInvoiceResponse(
        id=inv.id, invoice_number=inv.invoice_number,
        date=format_date_for_response(inv.date),
        provider_name=inv.provider_name, oc_number=inv.oc_number,
        base_amount=inv.base_amount, iva_amount=inv.iva_amount,
        final_total=inv.final_total, currency=inv.currency or "EUR",
        status=inv.status.value if inv.status else "PENDING",
        rejection_reason=inv.rejection_reason,
        created_at=inv.created_at,
        file_url=inv.file_url if (inv.file_url and inv.file_url.startswith("http")) else get_invoice_pdf_url(inv.file_url) if inv.file_url else None,
    ) for inv in invoices]


@router.delete("/invoices/{invoice_id}")
async def request_invoice_deletion(
    invoice_id: int,
    body: DeleteInvoiceRequest,
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    """Request deletion of an invoice (only PENDING status)."""
    invoice = db.query(SupplierInvoice).filter(
        SupplierInvoice.id == invoice_id,
        SupplierInvoice.supplier_id == supplier.id,
    ).first()

    if not invoice:
        raise HTTPException(404, "Invoice not found")

    if invoice.status != InvoiceStatus.PENDING:
        raise HTTPException(400, "Only pending invoices can be deleted")

    invoice.status = InvoiceStatus.DELETE_REQUESTED
    invoice.delete_reason = body.reason

    _notify(db, NotificationRecipientType.ADMIN, 0,
            NotificationEventType.DELETED, "Deletion Requested",
            f"{supplier.name} requests deletion of {invoice.invoice_number}: {body.reason}",
            invoice_id=invoice.id, supplier_id=supplier.id)
    db.commit()

    return {"message": "Deletion requested. The admin will confirm."}


# ============================================
# FINANCIAL SUMMARY
# ============================================

@router.get("/summary", response_model=SummaryResponse)
async def financial_summary(
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    """Financial summary for the supplier."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Pending = PENDING + APPROVED (not yet paid)
    pending_amount = db.query(
        func.coalesce(func.sum(SupplierInvoice.final_total), 0.0)
    ).filter(
        SupplierInvoice.supplier_id == supplier.id,
        SupplierInvoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.APPROVED]),
    ).scalar() or 0.0

    # Paid this month
    paid_month = db.query(
        func.coalesce(func.sum(SupplierInvoice.final_total), 0.0)
    ).filter(
        SupplierInvoice.supplier_id == supplier.id,
        SupplierInvoice.status == InvoiceStatus.PAID,
        SupplierInvoice.updated_at >= month_start,
    ).scalar() or 0.0

    total = db.query(func.count(SupplierInvoice.id)).filter(
        SupplierInvoice.supplier_id == supplier.id).scalar() or 0

    return SummaryResponse(
        pending_amount=float(pending_amount),
        paid_this_month=float(paid_month),
        total_invoices=total,
    )
