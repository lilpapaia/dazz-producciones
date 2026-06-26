import logging
from fastapi import APIRouter, Body, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from config.database import get_db
from config.constants import ADMIN_RECIPIENT_ID
from app.models import schemas
from app.models.database import User, Project, Ticket, UserRole
from app.services.auth import get_current_active_user
from app.services.permissions import can_access_project
# FEAT-09: lógica de tickets compartida con el flujo guest (upload/update/delete)
from app.services.ticket_service import process_ticket_upload, apply_ticket_update, delete_ticket_record

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("/{project_id}/upload", response_model=schemas.TicketUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_ticket(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # FEAT-09: lógica compartida con el flujo guest (ticket_service)
    return await process_ticket_upload(file, project, db)


@router.get("/{project_id}/tickets", response_model=List[schemas.TicketResponse])
async def get_project_tickets(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return db.query(Ticket).filter(Ticket.project_id == project_id).all()


@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    ticket = db.query(Ticket).options(joinedload(Ticket.project)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    project = ticket.project
    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    ticket.project_status = project.status
    return ticket


@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
async def update_ticket(ticket_id: int, ticket_update: schemas.TicketUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    ticket = db.query(Ticket).options(joinedload(Ticket.project)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    project = ticket.project
    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    update_data = ticket_update.model_dump(exclude_unset=True)
    # FEAT-09: lógica compartida con el flujo guest (ticket_service)
    return apply_ticket_update(ticket, update_data, db, is_admin=(current_user.role == UserRole.ADMIN))


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    ticket = db.query(Ticket).options(joinedload(Ticket.project)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    project = ticket.project
    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # SEC: los tickets de proveedor no se hard-deletan por esta vía (dejaría la
    # SupplierInvoice huérfana). El frontend ya lo oculta; este guard protege la API
    # directa. El borrado real va por delete_ticket_for_invoice (módulo proveedores).
    if ticket.from_supplier_portal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los tickets de proveedor deben gestionarse desde el módulo de proveedores"
        )

    if ticket.payment_status == "PAGADO ADMIN":
        raise HTTPException(status_code=403, detail="No se puede eliminar un ticket con estado de pago PAGADO ADMIN")

    # FEAT-09: lógica compartida con el flujo guest (ticket_service)
    delete_ticket_record(ticket, db)
    return None


@router.post("/{ticket_id}/request-supplier-deletion")
async def request_supplier_ticket_deletion(
    ticket_id: int,
    reason: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """INT-1: BOSS/WORKER requests deletion of a supplier-originated ticket.
    Sets ticket invoice_status to 'RECIBIDO PERO ERRONEO' and marks the
    linked SupplierInvoice as DELETE_REQUESTED."""
    ticket = db.query(Ticket).options(joinedload(Ticket.project)).filter(
        Ticket.id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    if not ticket.from_supplier_portal:
        raise HTTPException(400, "This ticket is not from the supplier portal")
    if not can_access_project(current_user, ticket.project, db):
        raise HTTPException(403, "Not enough permissions")
    if ticket.payment_status == "PAGADO ADMIN":
        raise HTTPException(400, "Cannot request deletion of a paid invoice")

    ticket.invoice_status = "RECIBIDO PERO ERRONEO"

    # Mark the linked supplier invoice as DELETE_REQUESTED
    if ticket.supplier_invoice_id:
        from app.models.suppliers import SupplierInvoice, InvoiceStatus
        invoice = db.query(SupplierInvoice).filter(
            SupplierInvoice.id == ticket.supplier_invoice_id
        ).first()
        if invoice and invoice.status not in (InvoiceStatus.PAID, InvoiceStatus.DELETE_REQUESTED):
            invoice.previous_status = invoice.status.value
            invoice.status = InvoiceStatus.DELETE_REQUESTED
            invoice.delete_reason = reason or "Solicitado desde proyecto DAZZ"

    # Notify admin
    from app.models.suppliers import NotificationRecipientType, NotificationEventType
    from app.services.notifications import create_notification as _notify
    msg = f"Ticket #{ticket_id} ({ticket.provider}) — deletion requested by {current_user.name}"
    if reason:
        msg += f": {reason}"
    _notify(
        db, NotificationRecipientType.ADMIN, ADMIN_RECIPIENT_ID,
        NotificationEventType.DELETED, "Supplier ticket deletion requested",
        msg, invoice_id=ticket.supplier_invoice_id, supplier_id=ticket.supplier_id,
    )

    db.commit()
    return {"message": "Solicitud de borrado enviada"}
