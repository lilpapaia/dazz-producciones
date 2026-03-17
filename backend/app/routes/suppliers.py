"""
Endpoints de gestión de proveedores — Solo ADMIN.
Prefijo: /suppliers
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, case
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import secrets
import string

from config.database import get_db
from app.models.database import User, Company, Ticket, TicketType
from app.models.suppliers import (
    Supplier, SupplierInvoice, SupplierOC, SupplierNotification,
    SupplierInvitation, InvoiceStatus, SupplierStatus,
    NotificationRecipientType, NotificationEventType,
)
from app.services.auth import get_current_admin_user
from app.models.supplier_schemas import (
    InviteRequest, InviteResponse, SupplierResponse, SupplierUpdate,
    AssignOCRequest, NoteRequest, InvoiceStatusUpdate, InvoiceResponse,
    NotificationResponse, DashboardResponse, CreateOCRequest, CreateOCResponse,
)
from app.services.supplier_auth import invalidate_all_supplier_tokens
from app.services.supplier_storage import get_invoice_pdf_url
from app.services.encryption import decrypt_iban, encrypt_iban, is_encryption_available
from app.services.supplier_ai import format_date_for_response, parse_invoice_date
from app.services.supplier_email import (
    send_supplier_invitation,
    send_supplier_invoice_approved,
    send_supplier_invoice_paid,
    send_supplier_invoice_rejected,
    send_supplier_invoice_deleted,
    send_admin_new_invoice,
    ADMIN_EMAIL,
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers (Admin)"])


def _decode_iban(supplier) -> str | None:
    """Decrypt IBAN for admin view (full, unmasked)."""
    if not supplier.iban_encrypted:
        return None
    return decrypt_iban(supplier.iban_encrypted)


def _generate_token(length: int = 64) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def _notify(db: Session, recipient_type, recipient_id: int, event_type,
            title: str, message: str, invoice_id=None, supplier_id=None):
    """Helper to create a notification."""
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
# OC MANAGEMENT
# ============================================

@router.post("/ocs", response_model=CreateOCResponse, status_code=201)
async def create_oc(
    body: CreateOCRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Create a new OC for a talent/influencer."""
    existing = db.query(SupplierOC).filter(SupplierOC.oc_number == body.oc_number.strip()).first()
    if existing:
        raise HTTPException(400, f"OC {body.oc_number} already exists")

    if body.company_id:
        company = db.query(Company).filter(Company.id == body.company_id).first()
        if not company:
            raise HTTPException(404, "Company not found")

    oc = SupplierOC(
        oc_number=body.oc_number.strip(),
        talent_name=body.talent_name.strip(),
        nif_cif=body.nif_cif.strip() if body.nif_cif else None,
        company_id=body.company_id,
    )
    db.add(oc)
    db.commit()
    db.refresh(oc)

    return CreateOCResponse(
        id=oc.id,
        oc_number=oc.oc_number,
        talent_name=oc.talent_name,
        nif_cif=oc.nif_cif,
        company_id=oc.company_id,
    )


# ============================================
# INVITATIONS
# ============================================

@router.post("/invite", response_model=InviteResponse, status_code=201)
async def invite_supplier(
    body: InviteRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Send invitation email to a new supplier."""
    # Check if supplier already exists
    existing = db.query(Supplier).filter(Supplier.email == body.email).first()
    if existing:
        raise HTTPException(400, "A supplier with this email already exists")

    # Check for pending invitation
    pending = db.query(SupplierInvitation).filter(
        SupplierInvitation.email == body.email,
        SupplierInvitation.used_at == None,
        SupplierInvitation.expires_at > datetime.now(timezone.utc),
    ).first()
    if pending:
        raise HTTPException(400, "An active invitation already exists for this email")

    token = _generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=72)

    invitation = SupplierInvitation(
        email=body.email,
        name=body.name,
        token=token,
        expires_at=expires_at,
        invited_by=admin.id,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # Send email (non-blocking — don't fail if email fails)
    try:
        send_supplier_invitation(body.name, body.email, token)
    except Exception as e:
        print(f"Warning: invitation email failed: {e}")

    return InviteResponse(
        id=invitation.id,
        name=body.name,
        email=body.email,
        expires_at=expires_at,
        message="Invitation sent successfully",
    )


# ============================================
# SUPPLIER CRUD
# ============================================

@router.get("", response_model=List[SupplierResponse])
async def list_suppliers(
    status_filter: Optional[str] = Query(None, alias="status"),
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """List all suppliers with optional filters."""
    query = db.query(Supplier).options(
        joinedload(Supplier.oc).joinedload(SupplierOC.company)
    )

    if status_filter:
        query = query.filter(Supplier.status == status_filter)

    if company_id:
        oc_ids = [oc.id for oc in db.query(SupplierOC).filter(SupplierOC.company_id == company_id).all()]
        query = query.filter(Supplier.oc_id.in_(oc_ids)) if oc_ids else query.filter(False)

    suppliers = query.order_by(desc(Supplier.created_at)).all()

    if not suppliers:
        return []

    # Batch pre-fetch: invoice counts (total + pending) per supplier
    supplier_ids = [s.id for s in suppliers]

    counts = db.query(
        SupplierInvoice.supplier_id,
        func.count(SupplierInvoice.id).label("total"),
        func.count(case((SupplierInvoice.status == InvoiceStatus.PENDING, 1))).label("pending"),
    ).filter(
        SupplierInvoice.supplier_id.in_(supplier_ids)
    ).group_by(SupplierInvoice.supplier_id).all()
    counts_map = {c.supplier_id: (c.total, c.pending) for c in counts}

    # Batch pre-fetch: last activity timestamps
    last_inv_map = dict(db.query(
        SupplierInvoice.supplier_id,
        func.max(SupplierInvoice.created_at),
    ).filter(
        SupplierInvoice.supplier_id.in_(supplier_ids)
    ).group_by(SupplierInvoice.supplier_id).all())

    last_notif_map = dict(db.query(
        SupplierNotification.related_supplier_id,
        func.max(SupplierNotification.created_at),
    ).filter(
        SupplierNotification.related_supplier_id.in_(supplier_ids)
    ).group_by(SupplierNotification.related_supplier_id).all())

    # Build responses using pre-loaded data (no per-supplier queries)
    result = []
    for s in suppliers:
        oc_number = s.oc.oc_number if s.oc else None
        company_name = s.oc.company.name if s.oc and s.oc.company else None
        inv_total, inv_pending = counts_map.get(s.id, (0, 0))
        last_activity = max(filter(None, [
            last_notif_map.get(s.id), last_inv_map.get(s.id), s.created_at
        ]))

        result.append(SupplierResponse(
            id=s.id, name=s.name, email=s.email, nif_cif=s.nif_cif,
            phone=s.phone, address=s.address, iban=_decode_iban(s),
            bank_cert_url=s.bank_cert_url,
            supplier_type=s.supplier_type.value if s.supplier_type else "GENERAL",
            status=s.status.value if s.status else "NEW",
            oc_id=s.oc_id, oc_number=oc_number, company_name=company_name,
            is_active=s.is_active, notes_internal=s.notes_internal,
            gdpr_consent=s.gdpr_consent,
            created_at=s.created_at, updated_at=s.updated_at,
            last_activity=last_activity,
            invoices_count=inv_total, pending_invoices=inv_pending,
        ))
    return result


def _build_supplier_response(s: Supplier, db: Session) -> SupplierResponse:
    """Build a full SupplierResponse with computed fields."""
    inv_count = db.query(func.count(SupplierInvoice.id)).filter(
        SupplierInvoice.supplier_id == s.id).scalar()
    pending = db.query(func.count(SupplierInvoice.id)).filter(
        SupplierInvoice.supplier_id == s.id,
        SupplierInvoice.status == InvoiceStatus.PENDING,
    ).scalar()

    oc_number = None
    company_name = None
    if s.oc_id:
        oc = db.query(SupplierOC).filter(SupplierOC.id == s.oc_id).first()
        if oc:
            oc_number = oc.oc_number
            if oc.company_id:
                co = db.query(Company).filter(Company.id == oc.company_id).first()
                company_name = co.name if co else None

    # Last activity: most recent notification or invoice for this supplier
    last_notif = db.query(func.max(SupplierNotification.created_at)).filter(
        SupplierNotification.related_supplier_id == s.id).scalar()
    last_inv = db.query(func.max(SupplierInvoice.created_at)).filter(
        SupplierInvoice.supplier_id == s.id).scalar()
    last_activity = max(filter(None, [last_notif, last_inv, s.created_at]))

    return SupplierResponse(
        id=s.id, name=s.name, email=s.email, nif_cif=s.nif_cif,
        phone=s.phone, address=s.address, iban=_decode_iban(s),
        bank_cert_url=s.bank_cert_url,
        supplier_type=s.supplier_type.value if s.supplier_type else "GENERAL",
        status=s.status.value if s.status else "NEW",
        oc_id=s.oc_id, oc_number=oc_number, company_name=company_name,
        is_active=s.is_active, notes_internal=s.notes_internal,
        gdpr_consent=s.gdpr_consent,
        created_at=s.created_at, updated_at=s.updated_at,
        last_activity=last_activity,
        invoices_count=inv_count, pending_invoices=pending,
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    return _build_supplier_response(supplier, db)


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    body: SupplierUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    ALLOWED_FIELDS = {"name", "nif_cif", "phone", "address", "supplier_type"}
    for field, value in body.model_dump(exclude_unset=True).items():
        if field in ALLOWED_FIELDS:
            setattr(supplier, field, value)

    db.commit()
    return {"message": "Supplier updated"}


@router.put("/{supplier_id}/deactivate")
async def deactivate_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Deactivate supplier and invalidate all their tokens."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    supplier.is_active = False
    supplier.status = SupplierStatus.DEACTIVATED
    invalidate_all_supplier_tokens(db, supplier_id)
    db.commit()
    return {"message": f"Supplier {supplier.name} deactivated, all tokens invalidated"}


@router.put("/{supplier_id}/assign-oc")
async def assign_oc(
    supplier_id: int,
    body: AssignOCRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Manually assign an OC to a supplier (for talents without NIF match)."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    oc = db.query(SupplierOC).filter(SupplierOC.id == body.oc_id).first()
    if not oc:
        raise HTTPException(404, "OC not found")

    supplier.oc_id = oc.id
    db.commit()
    return {"message": f"OC {oc.oc_number} assigned to {supplier.name}"}


@router.post("/{supplier_id}/notes")
async def add_note(
    supplier_id: int,
    body: NoteRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    new_note = f"[{timestamp}] {body.note}"
    supplier.notes_internal = (
        f"{supplier.notes_internal}\n{new_note}" if supplier.notes_internal else new_note
    )
    db.commit()
    return {"message": "Note added"}


# ============================================
# INVOICES MANAGEMENT
# ============================================

@router.get("/invoices/all", response_model=List[InvoiceResponse])
async def list_all_invoices(
    status_filter: Optional[str] = Query(None, alias="status"),
    company_id: Optional[int] = None,
    oc_number: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """List all supplier invoices with filters."""
    query = db.query(SupplierInvoice)

    if status_filter:
        query = query.filter(SupplierInvoice.status == status_filter)
    if company_id:
        query = query.filter(SupplierInvoice.company_id == company_id)
    if oc_number:
        query = query.filter(SupplierInvoice.oc_number.ilike(f"%{oc_number}%"))

    invoices = query.options(
        joinedload(SupplierInvoice.supplier)
    ).order_by(desc(SupplierInvoice.created_at)).offset(offset).limit(limit).all()

    result = []
    for inv in invoices:
        result.append(InvoiceResponse(
            id=inv.id, supplier_id=inv.supplier_id,
            supplier_name=inv.supplier.name if inv.supplier else None,
            invoice_number=inv.invoice_number,
            date=format_date_for_response(inv.date),
            provider_name=inv.provider_name, oc_number=inv.oc_number,
            company_id=inv.company_id,
            base_amount=inv.base_amount, iva_percentage=inv.iva_percentage,
            iva_amount=inv.iva_amount, irpf_percentage=inv.irpf_percentage or 0,
            irpf_amount=inv.irpf_amount or 0, final_total=inv.final_total,
            currency=inv.currency or "EUR", is_foreign=inv.is_foreign or False,
            file_url=get_invoice_pdf_url(inv.file_url) if inv.file_url else "",
            status=inv.status.value if inv.status else "PENDING",
            rejection_reason=inv.rejection_reason, delete_reason=inv.delete_reason,
            created_at=inv.created_at,
        ))

    return result


@router.put("/invoices/{invoice_id}/status")
async def update_invoice_status(
    invoice_id: int,
    body: InvoiceStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Change invoice status: PENDING → APPROVED → PAID (or REJECTED)."""
    invoice = db.query(SupplierInvoice).filter(SupplierInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    supplier = db.query(Supplier).filter(Supplier.id == invoice.supplier_id).first()
    new_status = body.status.upper()

    # Validate transitions
    valid_transitions = {
        "PENDING": ["APPROVED", "REJECTED"],
        "OC_PENDING": ["PENDING", "REJECTED"],  # Legacy: kept for existing data
        "APPROVED": ["PAID"],
    }
    current = invoice.status.value if invoice.status else "PENDING"
    allowed = valid_transitions.get(current, [])

    if new_status not in allowed:
        raise HTTPException(400, f"Cannot transition from {current} to {new_status}. Allowed: {allowed}")

    if new_status == "REJECTED" and not body.reason:
        raise HTTPException(400, "Rejection reason is required")

    invoice.status = InvoiceStatus(new_status)
    if new_status == "REJECTED":
        invoice.rejection_reason = body.reason

    # Auto-create ticket in DAZZ Producciones when APPROVED
    if new_status == "APPROVED" and invoice.project_id:
        existing_ticket = db.query(Ticket).filter(
            Ticket.supplier_invoice_id == invoice.id
        ).first()
        if not existing_ticket:
            ticket = Ticket(
                project_id=invoice.project_id,
                date=format_date_for_response(invoice.date),
                provider=invoice.provider_name or "",
                invoice_number=invoice.invoice_number,
                po_notes=invoice.oc_number,
                base_amount=invoice.base_amount,
                iva_percentage=invoice.iva_percentage,
                iva_amount=invoice.iva_amount,
                irpf_percentage=invoice.irpf_percentage or 0,
                irpf_amount=invoice.irpf_amount or 0,
                total_with_iva=invoice.base_amount + invoice.iva_amount,
                final_total=invoice.final_total,
                currency=invoice.currency or "EUR",
                is_foreign=invoice.is_foreign or False,
                invoice_status="Aprobada",
                payment_status="Pendiente",
                type=TicketType.FACTURA,
                file_path=invoice.file_url or "",
                file_name=f"{invoice.invoice_number}.pdf",
                notes="Ticket generated automatically from supplier portal",
                from_supplier_portal=True,
                supplier_id=invoice.supplier_id,
                supplier_invoice_id=invoice.id,
            )
            db.add(ticket)
            print(f"Ticket created in DAZZ for invoice {invoice.invoice_number} -> project {invoice.project_id}")

    # Notifications + emails
    if supplier:
        if new_status == "APPROVED":
            _notify(db, NotificationRecipientType.SUPPLIER, supplier.id,
                    NotificationEventType.APPROVED, "Invoice Approved",
                    f"Invoice {invoice.invoice_number} has been approved",
                    invoice_id=invoice.id, supplier_id=supplier.id)
            try:
                send_supplier_invoice_approved(supplier.name, supplier.email, invoice.invoice_number)
            except Exception:
                pass

        elif new_status == "PAID":
            _notify(db, NotificationRecipientType.SUPPLIER, supplier.id,
                    NotificationEventType.PAID, "Invoice Paid",
                    f"Invoice {invoice.invoice_number} — {invoice.final_total:.2f} EUR",
                    invoice_id=invoice.id, supplier_id=supplier.id)
            try:
                send_supplier_invoice_paid(supplier.name, supplier.email,
                                           invoice.invoice_number, invoice.final_total)
            except Exception:
                pass

        elif new_status == "REJECTED":
            _notify(db, NotificationRecipientType.SUPPLIER, supplier.id,
                    NotificationEventType.REJECTED, "Invoice Rejected",
                    f"Invoice {invoice.invoice_number}: {body.reason}",
                    invoice_id=invoice.id, supplier_id=supplier.id)
            try:
                send_supplier_invoice_rejected(supplier.name, supplier.email,
                                               invoice.invoice_number, body.reason)
            except Exception:
                pass

    # Single commit: status change + ticket + notifications
    db.commit()
    return {"message": f"Invoice status changed to {new_status}"}


@router.delete("/invoices/{invoice_id}")
async def confirm_invoice_deletion(
    invoice_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Confirm deletion of an invoice that was requested by the supplier."""
    invoice = db.query(SupplierInvoice).filter(SupplierInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    if invoice.status != InvoiceStatus.DELETE_REQUESTED:
        raise HTTPException(400, "Invoice must be in DELETE_REQUESTED status")

    supplier = db.query(Supplier).filter(Supplier.id == invoice.supplier_id).first()

    # Cascade: delete or void the linked ticket in DAZZ Producciones
    linked_ticket = db.query(Ticket).filter(
        Ticket.supplier_invoice_id == invoice.id
    ).first()
    if linked_ticket:
        # If ticket has been reviewed (is_reviewed=True), mark as voided instead of deleting
        if linked_ticket.is_reviewed:
            linked_ticket.payment_status = "Anulado"
            linked_ticket.notes = (linked_ticket.notes or "") + "\n[AUTO] Voided: supplier invoice deleted from portal"
            print(f"Ticket {linked_ticket.id} marked as Anulado (had activity)")
        else:
            db.delete(linked_ticket)
            print(f"Ticket {linked_ticket.id} deleted (cascade from supplier invoice)")

    db.delete(invoice)
    db.commit()

    if supplier:
        try:
            send_supplier_invoice_deleted(supplier.name, supplier.email, invoice.invoice_number)
        except Exception:
            pass

    return {"message": "Invoice deleted"}


# ============================================
# NOTIFICATIONS
# ============================================

@router.get("/notifications/all", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Get admin notifications (polling endpoint)."""
    query = db.query(SupplierNotification).filter(
        SupplierNotification.recipient_type == NotificationRecipientType.ADMIN
    )
    if unread_only:
        query = query.filter(SupplierNotification.is_read == False)

    notifications = query.order_by(desc(SupplierNotification.created_at)).limit(limit).all()

    return [NotificationResponse(
        id=n.id, event_type=n.event_type.value if n.event_type else "",
        title=n.title, message=n.message,
        related_invoice_id=n.related_invoice_id,
        related_supplier_id=n.related_supplier_id,
        is_read=n.is_read, created_at=n.created_at,
    ) for n in notifications]


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    notif = db.query(SupplierNotification).filter(SupplierNotification.id == notification_id).first()
    if not notif:
        raise HTTPException(404, "Notification not found")

    notif.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@router.put("/notifications/read-all")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Mark all admin notifications as read."""
    db.query(SupplierNotification).filter(
        SupplierNotification.recipient_type == NotificationRecipientType.ADMIN,
        SupplierNotification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


# ============================================
# DASHBOARD
# ============================================

@router.get("/dashboard/stats", response_model=DashboardResponse)
async def dashboard_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """KPIs for the supplier dashboard."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    pending = db.query(func.count(SupplierInvoice.id)).filter(
        SupplierInvoice.status == InvoiceStatus.PENDING).scalar() or 0

    approved_month = db.query(func.count(SupplierInvoice.id)).filter(
        SupplierInvoice.status == InvoiceStatus.APPROVED,
        SupplierInvoice.updated_at >= month_start).scalar() or 0

    active = db.query(func.count(Supplier.id)).filter(
        Supplier.is_active == True).scalar() or 0

    paid_month = db.query(func.coalesce(func.sum(SupplierInvoice.final_total), 0.0)).filter(
        SupplierInvoice.status == InvoiceStatus.PAID,
        SupplierInvoice.updated_at >= month_start).scalar() or 0.0

    unread = db.query(func.count(SupplierNotification.id)).filter(
        SupplierNotification.recipient_type == NotificationRecipientType.ADMIN,
        SupplierNotification.is_read == False).scalar() or 0

    return DashboardResponse(
        pending_invoices=pending,
        approved_this_month=approved_month,
        active_suppliers=active,
        total_paid_this_month=float(paid_month),
        unread_notifications=unread,
    )


# ============================================
# IBAN MIGRATION (one-shot)
# ============================================

@router.post("/admin/migrate-ibans")
async def migrate_ibans_to_encrypted(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    One-shot migration: re-encrypt existing plaintext IBANs with Fernet.

    Safe to run multiple times — skips already-encrypted IBANs.
    Requires ENCRYPTION_KEY env var to be set.
    """
    if not is_encryption_available():
        raise HTTPException(400, "ENCRYPTION_KEY not configured — cannot migrate")

    suppliers = db.query(Supplier).filter(Supplier.iban_encrypted != None).all()
    migrated = 0
    skipped = 0

    for s in suppliers:
        # Try to decode as UTF-8 — if it works, it's plaintext and needs encryption
        plaintext = decrypt_iban(s.iban_encrypted)
        if not plaintext:
            skipped += 1
            continue

        # Check if already Fernet-encrypted (starts with 'gAAAAA' when base64-decoded)
        try:
            raw = s.iban_encrypted
            if raw[:6] == b"gAAAAA" or raw[:5] == b"gAAAA":
                skipped += 1
                continue
        except (IndexError, TypeError):
            pass

        # Re-encrypt with Fernet
        s.iban_encrypted = encrypt_iban(plaintext)
        migrated += 1

    db.commit()
    return {
        "message": f"Migration complete: {migrated} IBANs encrypted, {skipped} skipped",
        "migrated": migrated,
        "skipped": skipped,
    }


# ============================================
# DATE MIGRATION (one-shot)
# ============================================

@router.post("/admin/migrate-dates")
async def migrate_dates_to_parsed(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    One-shot migration: parse existing date strings into date_parsed column.

    Uses raw SQL throughout — ORM can't reference date_parsed until the column exists.
    Creates the column if it doesn't exist, then parses all date strings.
    Safe to run multiple times — skips invoices that already have date_parsed.
    """
    from sqlalchemy import text

    # Step 1: Create column if missing (raw SQL — ORM can't do this)
    db.execute(text("ALTER TABLE supplier_invoices ADD COLUMN IF NOT EXISTS date_parsed DATE"))
    db.commit()

    # Step 2: Fetch rows needing migration (raw SQL — ORM mapping may not reflect new column)
    rows = db.execute(text(
        "SELECT id, date FROM supplier_invoices "
        "WHERE date_parsed IS NULL AND date IS NOT NULL AND date != ''"
    )).fetchall()

    migrated = 0
    failed = 0
    failed_samples = []

    for row in rows:
        inv_id, date_str = row[0], row[1]
        parsed = parse_invoice_date(date_str)
        if parsed:
            db.execute(
                text("UPDATE supplier_invoices SET date_parsed = :dp WHERE id = :id"),
                {"dp": parsed, "id": inv_id},
            )
            migrated += 1
        else:
            failed += 1
            if len(failed_samples) < 10:
                failed_samples.append(f"Invoice {inv_id}: '{date_str}'")

    db.commit()
    return {
        "message": f"Migration complete: {migrated} dates parsed, {failed} unparseable",
        "migrated": migrated,
        "failed": failed,
        "failed_samples": failed_samples,
    }
