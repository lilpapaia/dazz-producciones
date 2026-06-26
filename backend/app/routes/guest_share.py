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

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload

from config.database import get_db
from app.models import schemas
from app.models.database import ProjectShareToken, Project, Ticket
from app.services.auth import verify_password, _DUMMY_HASH
from app.services.guest_share_auth import get_current_guest, create_guest_access_token, _as_utc
from app.services.rate_limit import limiter, get_real_client_ip
from app.services.email import send_guest_first_access_email

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
