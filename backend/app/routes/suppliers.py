"""
Endpoints de gestión de proveedores — Solo ADMIN.
Prefijo: /suppliers
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
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
from app.services.supplier_auth import invalidate_all_supplier_tokens
from app.services.supplier_storage import get_invoice_pdf_url
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
# SCHEMAS (inline — specific to admin endpoints)
# ============================================

class InviteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    email: EmailStr


class InviteResponse(BaseModel):
    id: int
    name: str
    email: str
    expires_at: datetime
    message: str


class SupplierResponse(BaseModel):
    id: int
    name: str
    email: str
    nif_cif: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    supplier_type: str
    status: str
    oc_id: Optional[int] = None
    oc_number: Optional[str] = None
    is_active: bool
    notes_internal: Optional[str] = None
    gdpr_consent: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    invoices_count: int = 0
    pending_invoices: int = 0

    class Config:
        from_attributes = True


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    nif_cif: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    supplier_type: Optional[str] = None


class AssignOCRequest(BaseModel):
    oc_id: int


class NoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


class InvoiceStatusUpdate(BaseModel):
    status: str  # APPROVED, PAID, REJECTED
    reason: Optional[str] = None  # Required for REJECTED


class InvoiceResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    invoice_number: str
    date: str
    provider_name: str
    oc_number: str
    company_id: Optional[int] = None
    base_amount: float
    iva_percentage: float
    iva_amount: float
    irpf_percentage: float
    irpf_amount: float
    final_total: float
    currency: str
    is_foreign: bool
    file_url: str
    status: str
    rejection_reason: Optional[str] = None
    delete_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    event_type: str
    title: str
    message: str
    related_invoice_id: Optional[int] = None
    related_supplier_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    pending_invoices: int
    approved_this_month: int
    active_suppliers: int
    total_paid_this_month: float
    unread_notifications: int


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
    query = db.query(Supplier)

    if status_filter:
        query = query.filter(Supplier.status == status_filter)

    if company_id:
        # Filter by suppliers whose OC belongs to this company
        oc_ids = [oc.id for oc in db.query(SupplierOC).filter(SupplierOC.company_id == company_id).all()]
        query = query.filter(Supplier.oc_id.in_(oc_ids)) if oc_ids else query.filter(False)

    suppliers = query.order_by(desc(Supplier.created_at)).all()

    result = []
    for s in suppliers:
        inv_count = db.query(func.count(SupplierInvoice.id)).filter(
            SupplierInvoice.supplier_id == s.id).scalar()
        pending = db.query(func.count(SupplierInvoice.id)).filter(
            SupplierInvoice.supplier_id == s.id,
            SupplierInvoice.status == InvoiceStatus.PENDING,
        ).scalar()

        oc_number = None
        if s.oc_id:
            oc = db.query(SupplierOC).filter(SupplierOC.id == s.oc_id).first()
            oc_number = oc.oc_number if oc else None

        result.append(SupplierResponse(
            id=s.id, name=s.name, email=s.email, nif_cif=s.nif_cif,
            phone=s.phone, address=s.address,
            supplier_type=s.supplier_type.value if s.supplier_type else "GENERAL",
            status=s.status.value if s.status else "NEW",
            oc_id=s.oc_id, oc_number=oc_number,
            is_active=s.is_active, notes_internal=s.notes_internal,
            gdpr_consent=s.gdpr_consent,
            created_at=s.created_at, updated_at=s.updated_at,
            invoices_count=inv_count, pending_invoices=pending,
        ))

    return result


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    inv_count = db.query(func.count(SupplierInvoice.id)).filter(
        SupplierInvoice.supplier_id == supplier_id).scalar()
    pending = db.query(func.count(SupplierInvoice.id)).filter(
        SupplierInvoice.supplier_id == supplier_id,
        SupplierInvoice.status == InvoiceStatus.PENDING,
    ).scalar()

    oc_number = None
    if supplier.oc_id:
        oc = db.query(SupplierOC).filter(SupplierOC.id == supplier.oc_id).first()
        oc_number = oc.oc_number if oc else None

    return SupplierResponse(
        id=supplier.id, name=supplier.name, email=supplier.email,
        nif_cif=supplier.nif_cif, phone=supplier.phone, address=supplier.address,
        supplier_type=supplier.supplier_type.value if supplier.supplier_type else "GENERAL",
        status=supplier.status.value if supplier.status else "NEW",
        oc_id=supplier.oc_id, oc_number=oc_number,
        is_active=supplier.is_active, notes_internal=supplier.notes_internal,
        gdpr_consent=supplier.gdpr_consent,
        created_at=supplier.created_at, updated_at=supplier.updated_at,
        invoices_count=inv_count, pending_invoices=pending,
    )


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

    for field, value in body.model_dump(exclude_unset=True).items():
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

    invoices = query.order_by(desc(SupplierInvoice.created_at)).offset(offset).limit(limit).all()

    result = []
    for inv in invoices:
        supplier = db.query(Supplier).filter(Supplier.id == inv.supplier_id).first()
        result.append(InvoiceResponse(
            id=inv.id, supplier_id=inv.supplier_id,
            supplier_name=supplier.name if supplier else None,
            invoice_number=inv.invoice_number, date=inv.date,
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
        "OC_PENDING": ["PENDING", "REJECTED"],
        "APPROVED": ["PAID"],
    }
    current = invoice.status.value if invoice.status else "PENDING"
    allowed = valid_transitions.get(current, [])

    if new_status not in allowed:
        raise HTTPException(400, f"Cannot transition from {current} to {new_status}. Allowed: {allowed}")

    if new_status == "REJECTED" and not body.reason:
        raise HTTPException(400, "Rejection reason is required")

    invoice.status = new_status
    if new_status == "REJECTED":
        invoice.rejection_reason = body.reason

    db.commit()

    # Auto-create ticket in DAZZ Producciones when APPROVED
    if new_status == "APPROVED" and invoice.project_id:
        existing_ticket = db.query(Ticket).filter(
            Ticket.supplier_invoice_id == invoice.id
        ).first()
        if not existing_ticket:
            ticket = Ticket(
                project_id=invoice.project_id,
                date=invoice.date or "",
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
            db.commit()
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
