"""
Endpoints del portal de proveedores — Solo proveedores autenticados.
Prefijo: /portal
"""

import os
import asyncio
import tempfile
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
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
    DataChangeRequest, IbanChangeRequest, DeactivationRequest,
)
from app.models.suppliers import (
    Supplier, SupplierInvoice, SupplierOC, SupplierNotification,
    SupplierInvitation, InvoiceStatus, SupplierStatus,
    NotificationRecipientType, NotificationEventType, PENDING_TITLES,
)
from app.services.supplier_auth import (
    get_password_hash, verify_password,
    create_supplier_access_token, create_supplier_refresh_token,
    validate_supplier_refresh_token, revoke_supplier_refresh_token,
    get_current_active_supplier,
)
from app.services.supplier_ai import (
    extract_supplier_invoice, validate_supplier_invoice, resolve_company_from_oc,
    extract_iban_from_cert, extract_bank_cert_data, _normalize_iban, _normalize_nif,
)
from app.services.supplier_storage import save_invoice_pdf, save_bank_cert, get_invoice_pdf_url, get_bank_cert_url
from app.services.encryption import encrypt_iban, decrypt_iban
from app.services.validators import validate_pdf_bytes, sanitize_filename, validate_iban_format
from app.services.supplier_ai import format_date_for_response

from app.services.rate_limit import limiter

router = APIRouter(prefix="/portal", tags=["Supplier Portal"])


def _notify(db: Session, recipient_type, recipient_id: int, event_type,
            title: str, message: str, invoice_id=None, supplier_id=None, extra_data=None):
    notif = SupplierNotification(
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        event_type=event_type,
        title=title,
        message=message,
        related_invoice_id=invoice_id,
        related_supplier_id=supplier_id,
        extra_data=extra_data,
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

    # SEC-5: Check NIF uniqueness (case-insensitive)
    if body.nif_cif:
        existing_nif = db.query(Supplier).filter(
            func.upper(Supplier.nif_cif) == body.nif_cif.strip().upper()
        ).first()
        if existing_nif:
            raise HTTPException(400, "A supplier with this NIF/CIF already exists")

    # Mark token as used (one-time)
    invitation.used_at = datetime.now(timezone.utc)

    # M-13: NIF/CIF matching for OC assignment (uses shared _normalize_nif)
    oc_id = None
    if body.nif_cif:
        normalized = _normalize_nif(body.nif_cif)
        if normalized:
            ocs_with_nif = db.query(SupplierOC).filter(SupplierOC.nif_cif != None).all()
            for oc in ocs_with_nif:
                if _normalize_nif(oc.nif_cif) == normalized:
                    # SEC-7: Only assign if OC is not already taken by another supplier
                    already_taken = db.query(Supplier).filter(Supplier.oc_id == oc.id).first()
                    if not already_taken:
                        oc_id = oc.id
                    break

    # SEC-M1: Validate + normalize IBAN format (mod-97 checksum) before encrypting
    if body.iban:
        body.iban = validate_iban_format(body.iban)

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
        status=SupplierStatus.ACTIVE,
        oc_id=oc_id,
        gdpr_consent=True,
        gdpr_consent_at=datetime.now(timezone.utc),
        is_active=True,
        ia_cert_verified=not body.has_cert_warnings,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    # Create tokens
    access_token = create_supplier_access_token(supplier.id, supplier.email)
    refresh_token = create_supplier_refresh_token(db, supplier.id)

    # Notifications
    if body.iban:
        _notify(db, NotificationRecipientType.ADMIN, 0, NotificationEventType.REGISTRATION,
                "New Supplier Registered", f"{supplier.name} ({supplier.email})",
                supplier_id=supplier.id)
    else:
        _notify(db, NotificationRecipientType.ADMIN, 0, NotificationEventType.REGISTRATION,
                "New Supplier Registered — No IBAN",
                f"{supplier.name} ({supplier.email}) — registered without IBAN, payment method pending",
                supplier_id=supplier.id)
    db.commit()

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
    company_name = None
    if supplier.oc_id:
        oc = db.query(SupplierOC).filter(SupplierOC.id == supplier.oc_id).first()
        if oc:
            oc_number = oc.oc_number
            if oc.company_id:
                from app.models.database import Company
                co = db.query(Company).filter(Company.id == oc.company_id).first()
                company_name = co.name if co else None

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

    # Check for pending change requests (unread admin notifications from this supplier)
    pending_change = db.query(SupplierNotification).filter(
        SupplierNotification.recipient_type == NotificationRecipientType.ADMIN,
        SupplierNotification.related_supplier_id == supplier.id,
        SupplierNotification.is_read == False,
        SupplierNotification.event_type.in_([
            NotificationEventType.REGISTRATION,  # reuse for data changes
        ]),
        SupplierNotification.title.in_(PENDING_TITLES),
    ).first()

    return ProfileResponse(
        id=supplier.id, name=supplier.name, email=supplier.email,
        nif_cif=supplier.nif_cif, phone=supplier.phone, address=supplier.address,
        iban_masked=iban_masked,
        has_permanent_oc=supplier.oc_id is not None,
        oc_number=oc_number,
        company_name=company_name,
        has_pending_change=pending_change is not None,
        pending_change_info=pending_change.message if pending_change else None,
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

    # PERF-M1: Offload upload R2 síncrono al thread pool para no bloquear event loop
    cert_key = await asyncio.to_thread(
        save_bank_cert, file, supplier.id, contents,
        nif_cif=supplier.nif_cif, tipo="initial"
    )
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


@router.post("/validate-bank-cert")
@limiter.limit("5/hour")
async def validate_bank_cert_iban(
    request: Request,
    iban: str = Query(..., min_length=10, max_length=50),
    nif_cif: Optional[str] = Query(None, max_length=50),
    token: str = Query(..., min_length=1, description="Invitation token for auth during registration"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Validate bank certificate: document type, IBAN match, NIF match. Never blocks registration."""
    # SEC-2: Verify invitation token exists and is not expired (do NOT consume it)
    invitation = db.query(SupplierInvitation).filter(
        SupplierInvitation.token == token,
        SupplierInvitation.used_at == None,
        SupplierInvitation.expires_at > datetime.now(timezone.utc),
    ).first()
    if not invitation:
        raise HTTPException(403, "Invalid or expired invitation token")
    import uuid as _uuid

    contents = await file.read()
    validate_pdf_bytes(contents, max_size=10 * 1024 * 1024)

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_path = tmp.name
    tmp.write(contents)
    tmp.close()

    try:
        cert_data = await asyncio.to_thread(extract_bank_cert_data, temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    warnings = []

    # IA no pudo leer nada
    if not cert_data or (not cert_data.get("iban") and not cert_data.get("nif") and cert_data.get("is_bank_certificate") is None):
        _notify(db, NotificationRecipientType.ADMIN, 0,
                NotificationEventType.IA_REJECTED, "Bank cert not readable",
                "New supplier registration: AI could not read the bank certificate — manual review needed",
                supplier_id=None)
        db.commit()
        return {"valid": True, "iban_match": None, "nif_match": None, "is_bank_certificate": None,
                "warnings": ["Could not verify certificate automatically"], "message": "Could not read certificate — proceeding"}

    # 1. Verificar tipo de documento
    is_cert = cert_data.get("is_bank_certificate")
    if is_cert is False:
        _notify(db, NotificationRecipientType.ADMIN, 0,
                NotificationEventType.IA_REJECTED, "Document is not a bank certificate",
                "New supplier registration: uploaded document does not appear to be a bank certificate",
                supplier_id=None)
        warnings.append("Document may not be a bank certificate")

    # 2. Verificar IBAN
    extracted_iban = cert_data.get("iban")
    iban_match = None
    if extracted_iban:
        normalized_input = _normalize_iban(iban)
        normalized_cert = _normalize_iban(extracted_iban)
        if normalized_input == normalized_cert:
            iban_match = True
        else:
            iban_match = False
            _notify(db, NotificationRecipientType.ADMIN, 0,
                    NotificationEventType.IA_REJECTED, "IBAN mismatch on bank cert",
                    f"New supplier registration: IBAN on certificate does not match the one entered by supplier",
                    supplier_id=None)
            warnings.append("IBAN on certificate does not match")

    # 3. Verificar NIF
    extracted_nif = cert_data.get("nif")
    nif_match = None
    if extracted_nif and nif_cif:
        normalized_input_nif = _normalize_nif(nif_cif)
        normalized_cert_nif = _normalize_nif(extracted_nif)
        if normalized_input_nif and normalized_cert_nif:
            if normalized_input_nif == normalized_cert_nif:
                nif_match = True
            else:
                nif_match = False
                _notify(db, NotificationRecipientType.ADMIN, 0,
                        NotificationEventType.IA_REJECTED, "NIF mismatch on bank cert",
                        f"New supplier registration: NIF on certificate does not match the one entered by supplier",
                        supplier_id=None)
                warnings.append("NIF on certificate does not match")

    if warnings:
        db.commit()

    return {
        "valid": True,
        "iban_match": iban_match,
        "nif_match": nif_match,
        "is_bank_certificate": is_cert,
        "confidence": cert_data.get("confidence"),
        "warnings": warnings,
    }


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
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_path = tmp.name
    tmp.write(contents)
    tmp.close()

    try:
        # PERF-M1: Offload AI extraction (3-10s) al thread pool
        extracted = await asyncio.to_thread(extract_supplier_invoice, temp_path, "application/pdf")

        if extracted.get("error"):
            raise HTTPException(422, f"Could not process PDF: {extracted.get('error')}")

        # Validation against DB
        validation = validate_supplier_invoice(extracted, supplier.id, db)

        # IBAN mismatch: non-blocking warning + admin notification
        if validation.get("iban_match") is False:
            _notify(db, NotificationRecipientType.ADMIN, 0,
                    NotificationEventType.IA_REJECTED, "IBAN Mismatch",
                    f"Invoice from {supplier.name}: IBAN on invoice does not match registered IBAN",
                    supplier_id=supplier.id)

        if not validation["valid"]:
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

        # PERF-M1: Offload Cloudinary upload (2-5s) al thread pool
        upload_result = await asyncio.to_thread(save_invoice_pdf, file, supplier.id, contents)

        # Invoices without OC start as OC_PENDING for admin to assign manually
        if validation.get("oc_status") == "NO_OC":
            invoice_status = InvoiceStatus.OC_PENDING
        else:
            invoice_status = InvoiceStatus.PENDING

        # Create invoice record (file_pages not in ORM — saved via raw SQL after)
        invoice = SupplierInvoice(
            supplier_id=supplier.id,
            invoice_number=extracted.get("invoice_number", ""),
            date=extracted.get("date", ""),
            provider_name=extracted.get("provider", supplier.name),
            nif_cif=extracted.get("nif_cif"),
            oc_number=extracted.get("oc_number") or None,
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
        try:
            db.commit()
        except Exception:
            db.rollback()
            # LOGIC-M4: Si falla el commit a BD, limpiar archivos ya subidos a Cloudinary
            try:
                from app.services.supplier_storage import delete_invoice_pdf
                delete_invoice_pdf(upload_result["url"])
            except Exception:
                pass
            raise
        db.refresh(invoice)

        # M-16: Atomic commit — file_pages + date_parsed + notifications together
        if upload_result.get("pages"):
            invoice.file_pages = json.dumps(upload_result["pages"])

        # LOGIC-M2: Store parsed date via ORM (column now mapped)
        date_parsed = validation.get("date_parsed")
        if date_parsed:
            invoice.date_parsed = date_parsed

        # Notifications (same transaction as file_pages + date_parsed)
        if invoice_status == InvoiceStatus.OC_PENDING:
            _notify(db, NotificationRecipientType.ADMIN, 0,
                    NotificationEventType.NEW_INVOICE, "New Invoice — OC Required",
                    f"{supplier.name} — {invoice.invoice_number} ({invoice.final_total:.2f} EUR) — no OC detected, manual assignment needed",
                    invoice_id=invoice.id, supplier_id=supplier.id)
            _notify(db, NotificationRecipientType.SUPPLIER, supplier.id,
                    NotificationEventType.NEW_INVOICE, "Invoice received — OC pending",
                    f"Your invoice {invoice.invoice_number} was received but no OC was detected. DAZZ will assign the OC manually.",
                    invoice_id=invoice.id, supplier_id=supplier.id)
        else:
            _notify(db, NotificationRecipientType.ADMIN, 0,
                    NotificationEventType.NEW_INVOICE, "New Invoice Submitted",
                    f"{supplier.name} — {invoice.invoice_number} ({invoice.final_total:.2f} EUR)",
                    invoice_id=invoice.id, supplier_id=supplier.id)
            _notify(db, NotificationRecipientType.SUPPLIER, supplier.id,
                    NotificationEventType.NEW_INVOICE, "Invoice Received",
                    f"Invoice {invoice.invoice_number} submitted successfully",
                    invoice_id=invoice.id, supplier_id=supplier.id)

        db.commit()  # Atomic: file_pages + date_parsed + notifications

    finally:
        # Always clean up temp file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
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


@router.get("/invoices/received", response_model=List[PortalInvoiceResponse])
async def list_received_invoices(
    limit: int = Query(50, le=200),
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    """List autoinvoices generated by DAZZ for this supplier."""
    invoices = db.query(SupplierInvoice).options(
        joinedload(SupplierInvoice.company)
    ).filter(
        SupplierInvoice.supplier_id == supplier.id,
        SupplierInvoice.is_autoinvoice == True,
    ).order_by(desc(SupplierInvoice.created_at)).limit(limit).all()

    results = []
    for inv in invoices:
        company_name = inv.company.name if inv.company else None

        results.append(PortalInvoiceResponse(
            id=inv.id, invoice_number=inv.invoice_number,
            date=format_date_for_response(inv.date),
            provider_name=inv.provider_name, oc_number=inv.oc_number,
            base_amount=inv.base_amount, iva_amount=inv.iva_amount,
            final_total=inv.final_total, currency=inv.currency or "EUR",
            status=inv.status.value if inv.status else "PENDING",
            rejection_reason=inv.rejection_reason,
            file_url=inv.file_url if (inv.file_url and inv.file_url.startswith("http")) else get_invoice_pdf_url(inv.file_url) if inv.file_url else None,
            is_autoinvoice=True,
            company_name=company_name,
            created_at=inv.created_at,
        ))
    return results


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

    # M-15: Allow deletion of both PENDING and OC_PENDING invoices
    if invoice.status not in (InvoiceStatus.PENDING, InvoiceStatus.OC_PENDING):
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

    unread = db.query(func.count(SupplierNotification.id)).filter(
        SupplierNotification.recipient_type == NotificationRecipientType.SUPPLIER,
        SupplierNotification.recipient_id == supplier.id,
        SupplierNotification.is_read == False,
    ).scalar() or 0

    return SummaryResponse(
        pending_amount=float(pending_amount),
        paid_this_month=float(paid_month),
        total_invoices=total,
        unread_notifications=unread,
    )


# ============================================
# NOTIFICATIONS (supplier-facing)
# ============================================

@router.get("/notifications")
async def get_my_notifications(
    limit: int = Query(50, le=200),
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    """List notifications for the authenticated supplier."""
    notifs = db.query(SupplierNotification).filter(
        SupplierNotification.recipient_type == NotificationRecipientType.SUPPLIER,
        SupplierNotification.recipient_id == supplier.id,
    ).order_by(desc(SupplierNotification.created_at)).limit(limit).all()

    return [{
        "id": n.id,
        "event_type": n.event_type.value if n.event_type else "",
        "title": n.title,
        "message": n.message,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
        "related_invoice_id": n.related_invoice_id,
    } for n in notifs]


@router.put("/notifications/{notification_id}/read")
async def mark_my_notification_read(
    notification_id: int,
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    notif = db.query(SupplierNotification).filter(
        SupplierNotification.id == notification_id,
        SupplierNotification.recipient_type == NotificationRecipientType.SUPPLIER,
        SupplierNotification.recipient_id == supplier.id,
    ).first()
    if not notif:
        raise HTTPException(404, "Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@router.put("/notifications/read-all")
async def mark_all_my_notifications_read(
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    db.query(SupplierNotification).filter(
        SupplierNotification.recipient_type == NotificationRecipientType.SUPPLIER,
        SupplierNotification.recipient_id == supplier.id,
        SupplierNotification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


# ============================================
# ACCOUNT ACTIONS (data change, IBAN, deactivation)
# ============================================

@router.post("/request-data-change")
async def request_data_change(
    body: DataChangeRequest,
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    """Request to change name/phone/address. Admin must approve."""
    import json
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(400, "No changes provided")

    _notify(db, NotificationRecipientType.ADMIN, 0,
            NotificationEventType.REGISTRATION, "Data Change Request",
            f"{supplier.name} requests data change",
            supplier_id=supplier.id,
            extra_data=json.dumps(changes))
    _notify(db, NotificationRecipientType.SUPPLIER, supplier.id,
            NotificationEventType.REGISTRATION, "Data change submitted",
            "Your data change request has been sent. The admin will review it.",
            supplier_id=supplier.id)
    db.commit()
    return {"message": "Data change request submitted for admin review"}


@router.post("/request-iban-change")
async def request_iban_change(
    new_iban: str = Form(..., min_length=10, max_length=50),
    file: UploadFile = File(...),
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    """Request IBAN change with new bank certificate. Admin must approve. SEC-1: IBAN in body, not URL."""
    contents = await file.read()
    validate_pdf_bytes(contents, max_size=10 * 1024 * 1024)

    # Validate + normalize IBAN format
    new_iban = validate_iban_format(new_iban)

    # Save new cert to R2 (never overwrites — all versions kept for RGPD)
    cert_key = await asyncio.to_thread(
        save_bank_cert, file, supplier.id, contents,
        nif_cif=supplier.nif_cif, tipo="update"
    )

    # Store pending IBAN + cert key on supplier (admin will approve/reject)
    supplier.pending_iban_encrypted = encrypt_iban(new_iban)
    supplier.pending_bank_cert_url = cert_key
    _notify(db, NotificationRecipientType.ADMIN, 0,
            NotificationEventType.REGISTRATION, "IBAN Change Request",
            f"{supplier.name} requests IBAN change to {new_iban[:4]}****{new_iban[-4:]}",
            supplier_id=supplier.id)
    _notify(db, NotificationRecipientType.SUPPLIER, supplier.id,
            NotificationEventType.REGISTRATION, "IBAN change submitted",
            "Your IBAN change request has been sent. Your current IBAN remains active until approved.",
            supplier_id=supplier.id)
    db.commit()
    return {"message": "IBAN change request submitted for admin review"}


@router.post("/request-deactivation")
async def request_deactivation(
    body: DeactivationRequest,
    supplier: Supplier = Depends(get_current_active_supplier),
    db: Session = Depends(get_db),
):
    """Request account deactivation. Admin must confirm."""
    _notify(db, NotificationRecipientType.ADMIN, 0,
            NotificationEventType.REGISTRATION, "Deactivation Request",
            f"{supplier.name} requests account deactivation. Reason: {body.reason}",
            supplier_id=supplier.id)
    _notify(db, NotificationRecipientType.SUPPLIER, supplier.id,
            NotificationEventType.REGISTRATION, "Deactivation request sent",
            "Your deactivation request has been sent. The admin will review it.",
            supplier_id=supplier.id)
    db.commit()
    return {"message": "Deactivation request submitted for admin review"}
