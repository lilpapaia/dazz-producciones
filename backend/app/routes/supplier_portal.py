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
from pydantic import BaseModel, EmailStr, Field, field_validator
import re
import hashlib

from config.database import get_db
from app.models.database import User
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
from app.services.supplier_storage import save_invoice_pdf, save_bank_cert, get_invoice_pdf_url
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
# SCHEMAS
# ============================================

class ValidateTokenResponse(BaseModel):
    valid: bool
    name: Optional[str] = None
    email: Optional[str] = None


class RegisterRequest(BaseModel):
    token: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=300)
    nif_cif: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)
    iban: Optional[str] = Field(default=None, max_length=50)
    password: str = Field(min_length=8)
    gdpr_consent: bool

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        return v


class RegisterResponse(BaseModel):
    message: str
    supplier_id: int
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    supplier: dict


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class ProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    nif_cif: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    iban_masked: Optional[str] = None
    supplier_type: str
    oc_number: Optional[str] = None
    created_at: datetime


class PortalInvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    date: str
    provider_name: str
    oc_number: str
    base_amount: float
    iva_amount: float
    final_total: float
    currency: str
    status: str
    rejection_reason: Optional[str] = None
    file_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeleteInvoiceRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class SummaryResponse(BaseModel):
    pending_amount: float
    paid_this_month: float
    total_invoices: int


# ============================================
# REGISTRATION
# ============================================

@router.get("/register/validate/{token}", response_model=ValidateTokenResponse)
async def validate_invitation_token(
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
async def register_supplier(
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
    iban_bytes = body.iban.encode("utf-8") if body.iban else None

    supplier = Supplier(
        name=body.name,
        email=invitation.email,
        email_hash=email_hash,
        hashed_password=get_password_hash(body.password),
        nif_cif=body.nif_cif,
        phone=body.phone,
        address=body.address,
        iban_encrypted=iban_bytes,  # TODO: Fase 3+ — cifrar con pgcrypto
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
    db: Session = Depends(get_db),
):
    revoked = revoke_supplier_refresh_token(db, body.refresh_token)
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

    # Mask IBAN for supplier view (only last 4 digits visible)
    iban_masked = None
    if supplier.iban_encrypted:
        try:
            raw = supplier.iban_encrypted.decode("utf-8")
            iban_masked = "**** **** **** **** " + raw[-4:] if len(raw) >= 4 else "****"
        except (UnicodeDecodeError, AttributeError):
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

    # Validate file
    if not file.content_type or file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are accepted")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB max
        raise HTTPException(400, "File too large (max 10MB)")
    await file.seek(0)

    # Save to temp file for AI extraction (Cloudinary upload happens AFTER validation)
    import uuid as _uuid
    temp_id = _uuid.uuid4().hex[:8]
    temp_path = os.path.join("uploads", "suppliers", f"tmp_ai_{temp_id}.pdf")
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    with open(temp_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

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

        # Validation passed → upload to Cloudinary (authenticated, no public URL)
        await file.seek(0)
        file_public_id = save_invoice_pdf(file, supplier.id)

        # Determine status
        invoice_status = InvoiceStatus.PENDING
        if validation["oc_status"] == "OC_PENDING":
            invoice_status = InvoiceStatus.OC_PENDING

        # Create invoice record (file_url stores public_id, not a URL)
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
            file_url=file_public_id,
            status=invoice_status,
            ia_validation_result=json.dumps(validation, default=str),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

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
        id=inv.id, invoice_number=inv.invoice_number, date=inv.date,
        provider_name=inv.provider_name, oc_number=inv.oc_number,
        base_amount=inv.base_amount, iva_amount=inv.iva_amount,
        final_total=inv.final_total, currency=inv.currency or "EUR",
        status=inv.status.value if inv.status else "PENDING",
        rejection_reason=inv.rejection_reason,
        created_at=inv.created_at,
        file_url=get_invoice_pdf_url(inv.file_url) if inv.file_url else None,
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

    return SummaryResponse(
        pending_amount=float(pending_amount),
        paid_this_month=float(paid_month),
        total_invoices=total,
    )
