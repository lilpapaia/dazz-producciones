"""
Endpoints de acceso externo a proyectos (FEAT-09) — link + PIN.

Prefijo: /guest
- POST /guest/validate-pin  (público, rate-limited) → JWT guest de 4h
- GET  /guest/project       (auth guest) → datos del proyecto SIN presupuesto/cliente
- GET  /guest/tickets       (auth guest) → tickets del proyecto

El project_id SIEMPRE sale del JWT (anti-IDOR). get_current_guest revalida en cada
request is_active / expires_at / locked_until.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from config.database import get_db
from app.models import schemas
from app.models.database import ProjectShareToken, Project, Ticket, ProjectStatus
from app.services.auth import verify_password, _DUMMY_HASH
from app.services.guest_share_auth import get_current_guest, create_guest_access_token, _as_utc
from app.services.rate_limit import limiter, get_real_client_ip
from app.services.email import send_guest_first_access_email
from app.services.ticket_service import process_ticket_upload, apply_ticket_update, delete_ticket_record
from app.routes.projects import generate_project_excel_bytes, build_excel_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guest", tags=["guest-share"])

PIN_MAX_ATTEMPTS = 5
PIN_LOCKOUT_MINUTES = 15


@router.post("/validate-pin", response_model=schemas.GuestValidatePinResponse)
@limiter.limit("5/minute")
async def validate_pin(
    request: Request,
    body: schemas.GuestValidatePinRequest,
    db: Session = Depends(get_db),
):
    """Valida el token + PIN y devuelve un JWT guest de 4h. Lockout 5 intentos/15 min."""
    ip = get_real_client_ip(request)
    now = datetime.now(timezone.utc)

    share = db.query(ProjectShareToken).options(
        joinedload(ProjectShareToken.project),
        joinedload(ProjectShareToken.creator),
    ).filter(ProjectShareToken.token == body.token).first()

    # Token inexistente → dummy verify (timing protection) + mensaje genérico.
    if not share:
        verify_password(body.pin, _DUMMY_HASH)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Enlace no válido")

    # Revocado / expirado: el usuario ya tiene el token, no es secreto → mensaje claro.
    if not share.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Este enlace ha sido revocado")

    if _as_utc(share.expires_at) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Este enlace ha expirado")

    # Lockout por intentos de PIN fallidos.
    locked_until = _as_utc(share.locked_until)
    if locked_until and locked_until > now:
        remaining = int((locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos. Inténtalo en {remaining} minutos",
        )
    # El bloqueo ya expiró → resetear contador antes de validar.
    if locked_until and locked_until <= now:
        share.failed_pin_attempts = 0
        share.locked_until = None

    # PIN incorrecto.
    if not verify_password(body.pin, share.pin_hash):
        share.failed_pin_attempts = (share.failed_pin_attempts or 0) + 1
        if share.failed_pin_attempts >= PIN_MAX_ATTEMPTS:
            share.locked_until = now + timedelta(minutes=PIN_LOCKOUT_MINUTES)
            logger.warning(f"Share token bloqueado: id={share.id} tras {PIN_MAX_ATTEMPTS} intentos fallidos")
        db.commit()
        logger.critical(f"PIN FALLIDO para token {body.token[:8]}... IP={ip}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="PIN incorrecto")

    # PIN correcto.
    share.failed_pin_attempts = 0
    share.locked_until = None
    share.last_accessed_at = now
    share.last_accessed_ip = ip

    # Notificación de primer acceso (idempotente, NON-BLOCKING).
    if not share.first_access_notified:
        try:
            creator = share.creator
            project = share.project
            if creator and creator.email:
                send_guest_first_access_email(
                    creator_email=creator.email,
                    creator_name=creator.name,
                    guest_name=share.guest_name,
                    project_name=project.description if project else "",
                    project_code=project.creative_code if project else "",
                )
        except Exception as e:
            logger.warning(f"Email primer acceso externo falló (no bloqueante): {str(e)}")
        share.first_access_notified = True

    db.commit()

    access_token = create_guest_access_token(
        token_id=share.id,
        project_id=share.project_id,
        guest_name=share.guest_name,
    )
    return schemas.GuestValidatePinResponse(
        access_token=access_token,
        guest_name=share.guest_name,
        project_id=share.project_id,
    )


@router.get("/project", response_model=schemas.GuestProjectResponse)
async def get_guest_project(
    guest: dict = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    """Datos del proyecto del externo, SIN presupuesto ni datos de cliente."""
    project = db.query(Project).options(joinedload(Project.owner_company)).filter(
        Project.id == guest["project_id"]
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    company_name = (project.owner_company.name if project.owner_company else None) or project.company
    return schemas.GuestProjectResponse(
        id=project.id,
        creative_code=project.creative_code,
        description=project.description,
        status=project.status,
        company_name=company_name,
        responsible=project.responsible,
        total_amount=project.total_amount or 0.0,
        tickets_count=project.tickets_count or 0,
        client_oc=project.client_oc,
        project_link=project.project_link,
        send_date=project.send_date,
        invoice_type=project.invoice_type,
        other_invoice_data=project.other_invoice_data,
    )


@router.get("/tickets", response_model=List[schemas.TicketResponse])
async def get_guest_tickets(
    guest: dict = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    """Lista los tickets del proyecto del externo (project_id del JWT — anti-IDOR)."""
    return db.query(Ticket).filter(Ticket.project_id == guest["project_id"]).all()


# ============================================
# MUTACIONES (FEAT-09 Fase 5)
# ============================================

def _guest_ticket_or_403(ticket_id: int, guest: dict, db: Session) -> Ticket:
    """Carga el ticket y verifica que pertenece al proyecto del JWT (anti-IDOR)."""
    ticket = db.query(Ticket).options(joinedload(Ticket.project)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.project_id != guest["project_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return ticket


@router.post("/tickets/upload", response_model=schemas.TicketUploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("40/minute")
async def guest_upload_ticket(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    guest: dict = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    """Subir un ticket como externo. project_id del JWT (anti-IDOR). Mismo flujo IA que empleados."""
    project = db.query(Project).filter(Project.id == guest["project_id"]).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.status == ProjectStatus.CERRADO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El proyecto está cerrado")

    return await process_ticket_upload(
        file, project, db,
        uploaded_by_guest_name=guest["guest_name"],
        guest_share_token_id=guest["token_id"],
    )


@router.put("/tickets/{ticket_id}", response_model=schemas.TicketResponse)
async def guest_update_ticket(
    ticket_id: int,
    ticket_update: schemas.TicketUpdate,
    guest: dict = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    """Editar un ticket del proyecto del externo. El guest nunca es admin →
    no puede mutar invoice_status/payment_status en tickets del portal de proveedores."""
    ticket = _guest_ticket_or_403(ticket_id, guest, db)
    update_data = ticket_update.model_dump(exclude_unset=True)
    return apply_ticket_update(ticket, update_data, db, is_admin=False)


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def guest_delete_ticket(
    ticket_id: int,
    guest: dict = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    """Borrar un ticket del proyecto del externo. Bloquea tickets de proveedor y PAGADO ADMIN."""
    ticket = _guest_ticket_or_403(ticket_id, guest, db)

    if ticket.from_supplier_portal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los tickets de proveedor deben gestionarse desde el módulo de proveedores",
        )
    if ticket.payment_status == "PAGADO ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se puede eliminar un ticket con estado de pago PAGADO ADMIN",
        )

    delete_ticket_record(ticket, db)
    return None


@router.get("/project/excel")
async def guest_download_excel(
    guest: dict = Depends(get_current_guest),
    db: Session = Depends(get_db),
):
    """Descargar el Excel del proyecto SIN cerrarlo. Permite 0 tickets (plantilla vacía)."""
    project = db.query(Project).filter(Project.id == guest["project_id"]).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    tickets = db.query(Ticket).filter(Ticket.project_id == guest["project_id"]).all()
    excel_bytes = generate_project_excel_bytes(project, tickets, db)
    return build_excel_response(project, excel_bytes)
