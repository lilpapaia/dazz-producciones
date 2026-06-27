import os
import re
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, case, false
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr

from config.database import get_db
from config.constants import ADMIN_RECIPIENT_ID
from app.models import schemas
from app.models.database import User, Project, ProjectStatus, Company, UserRole, ProjectShareToken
from app.services.auth import get_current_active_user, get_current_admin_user, get_password_hash
from app.services.guest_share_auth import generate_share_token, generate_pin
from app.services.companies_service import validate_company_access
from app.services.permissions import get_user_company_ids, get_mgmt_company_ids, can_access_project, can_modify_project

# FEAT-09: URL del frontend para construir el share_url (mismo origen que email.py)
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://dazz-producciones.vercel.app")

# LOGGING CRÍTICO
from app.services.critical_logger import log_project_deleted

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])

RESPONSIBLE_EMAILS = {
    'MIGUEL': 'miguel@dazzcreative.com',
    'JULIETA': 'julieta@dazzcreative.com',
    'ANTONIO': 'antonio@dazzcreative.com'
}

class CloseProjectRequest(BaseModel):
    recipients: Optional[List[EmailStr]] = None


# ============================================
# HELPERS EXCEL (FEAT-09 — reutilizados por close_project y GET /excel)
# ============================================

def generate_project_excel_bytes(project, tickets, db) -> bytes:
    """Genera los bytes del Excel del proyecto. HTTPException 500 si falla.

    NO cambia el estado del proyecto ni envía emails — eso es responsabilidad del caller.
    """
    try:
        from app.services.excel_generator import create_project_excel_bytes
        return create_project_excel_bytes(project, tickets, db)
    except Exception as e:
        logger.error(f"Error generando Excel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar Excel"
        )


def build_excel_response(project, excel_bytes, extra_headers: dict = None) -> Response:
    """Construye la Response de descarga del Excel (mismo media_type y filename que close_project)."""
    safe_code = re.sub(r'[^\w\-.]', '_', project.creative_code)
    headers = {"Content-Disposition": f'attachment; filename="{safe_code}_GASTOS.xlsx"'}
    if extra_headers:
        headers.update(extra_headers)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


# ============================================
# ENDPOINTS
# ============================================

@router.post("", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crear nuevo proyecto.

    - ADMIN: puede crear en cualquier empresa
    - BOSS: puede crear solo en su empresa
    - WORKER: puede crear solo en sus empresas asignadas
    """

    # Validar que la empresa existe
    company = db.query(Company).filter(Company.id == project.owner_company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa con ID {project.owner_company_id} no encontrada"
        )

    # Validar que el usuario tiene acceso a esa empresa
    if not validate_company_access(current_user, project.owner_company_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes permiso para crear proyectos en {company.name}"
        )

    # Validar que el responsable pertenece a la empresa (si se proporcionó)
    if project.responsible:
        responsible_user = db.query(User).filter(
            func.lower(User.name) == project.responsible.lower()
        ).first()
        if responsible_user:
            resp_company_ids = [c.id for c in responsible_user.companies] if responsible_user.companies else []
            if not resp_company_ids:
                from sqlalchemy.orm import joinedload as jl
                ru = db.query(User).options(jl(User.companies)).filter(User.id == responsible_user.id).first()
                resp_company_ids = [c.id for c in ru.companies] if ru else []
            if resp_company_ids and project.owner_company_id not in resp_company_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El responsable '{project.responsible}' no pertenece a la empresa seleccionada"
                )

    # Crear proyecto (company es campo legacy NOT NULL, rellenar con nombre de empresa)
    db_project = Project(**project.model_dump(exclude={"company"}), owner_id=current_user.id, status=ProjectStatus.EN_CURSO, company=company.name)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Legacy auto-link: handle any existing OC_PENDING invoices (new invoices require OC to exist)
    try:
        from app.models.suppliers import SupplierInvoice, InvoiceStatus, NotificationRecipientType, NotificationEventType
        from app.services.notifications import create_notification as _notify
        pending_invoices = db.query(SupplierInvoice).filter(
            SupplierInvoice.oc_number.ilike(db_project.creative_code),
            SupplierInvoice.status == InvoiceStatus.OC_PENDING,
        ).all()
        for inv in pending_invoices:
            inv.project_id = db_project.id
            inv.company_id = db_project.owner_company_id
            inv.status = InvoiceStatus.PENDING
            _notify(db, NotificationRecipientType.ADMIN, ADMIN_RECIPIENT_ID,
                    NotificationEventType.OC_LINKED, "OC Linked",
                    f"Invoice {inv.invoice_number} linked to project {db_project.creative_code}",
                    invoice_id=inv.id, supplier_id=inv.supplier_id)
        if pending_invoices:
            db.commit()
            logger.info(f"Auto-linked {len(pending_invoices)} OC_PENDING invoices to project {db_project.creative_code}")

        # BUG-60: Auto-link orphaned APPROVED invoices (approved before project existed, or after project deletion)
        from app.models.suppliers import Supplier
        from app.services.supplier_integration import create_ticket_from_supplier_invoice
        orphaned = db.query(SupplierInvoice).filter(
            SupplierInvoice.oc_number.ilike(db_project.creative_code),
            SupplierInvoice.status == InvoiceStatus.APPROVED,
            SupplierInvoice.project_id.is_(None),
        ).all()
        # PERF-11: Batch load suppliers instead of 1 query per orphan
        supplier_ids = list({inv.supplier_id for inv in orphaned})
        suppliers_map = {s.id: s for s in db.query(Supplier).filter(Supplier.id.in_(supplier_ids)).all()} if supplier_ids else {}
        for inv in orphaned:
            inv.project_id = db_project.id
            inv.company_id = db_project.owner_company_id
            supplier = suppliers_map.get(inv.supplier_id)
            if supplier:
                create_ticket_from_supplier_invoice(db, inv, supplier, db_project)
        if orphaned:
            db.commit()
            logger.info(f"Auto-linked {len(orphaned)} orphaned APPROVED invoices to project {db_project.creative_code}")
    except Exception as e:
        logger.warning(f"OC auto-link failed: {e}")

    return db_project


@router.get("", response_model=List[schemas.ProjectResponse])
async def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    status: str = None
):
    """
    Obtener proyectos según el rol del usuario:

    - ADMIN: ve TODOS los proyectos
    - BOSS: ve todos los proyectos de su empresa
    - WORKER: ve solo SUS proyectos de sus empresas
    """

    query = db.query(Project).options(joinedload(Project.owner_company))

    if current_user.role == UserRole.ADMIN:
        # ADMIN ve TODOS los proyectos
        pass

    elif current_user.role == UserRole.BOSS:
        # BOSS ve todos los proyectos de su empresa
        user_company_ids = get_user_company_ids(current_user, db)
        query = query.filter(Project.owner_company_id.in_(user_company_ids))

    else:
        # WORKER: proyectos propios (owner/responsible) + bypass MGMT
        # (BUG-65: miembros de empresas MGMT ven todos los proyectos de esas empresas).
        user_company_ids = get_user_company_ids(current_user, db)
        mgmt_company_ids = get_mgmt_company_ids(current_user)
        username_lower = (current_user.username or "").lower()
        query = query.filter(
            Project.owner_company_id.in_(user_company_ids),
            or_(
                # MGMT bypass: cualquier proyecto cuya empresa sea MGMT del user
                Project.owner_company_id.in_(mgmt_company_ids) if mgmt_company_ids else false(),
                # Regla normal: owner o responsible
                Project.owner_id == current_user.id,
                func.lower(Project.responsible) == username_lower,
            ),
        )

    # Filtrar por estado si se proporciona
    if status:
        query = query.filter(Project.status == status)

    projects = query.order_by(Project.created_at.desc()).all()
    return projects


@router.get("/{project_id}", response_model=schemas.ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener proyecto por ID (con validación de acceso por empresa)"""

    project = db.query(Project).options(joinedload(Project.owner_company)).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Validar acceso según empresa
    if not can_access_project(current_user, project, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este proyecto"
        )

    return project


@router.put("/{project_id}", response_model=schemas.ProjectResponse)
async def update_project(
    project_id: int,
    project_update: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar proyecto (con validación de permisos por empresa)"""

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Validar permisos de modificación
    if not can_modify_project(current_user, project, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para editar este proyecto"
        )

    # Si se intenta cambiar owner_company_id, validar acceso a la nueva empresa
    if project_update.owner_company_id and project_update.owner_company_id != project.owner_company_id:
        if not validate_company_access(current_user, project_update.owner_company_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para mover el proyecto a esa empresa"
            )

    # Validar que el responsable pertenece a la empresa del proyecto (si se cambia)
    new_responsible = getattr(project_update, 'responsible', None)
    if new_responsible:
        target_company_id = project_update.owner_company_id or project.owner_company_id
        responsible_user = db.query(User).filter(
            func.lower(User.name) == new_responsible.lower()
        ).first()
        if responsible_user:
            from sqlalchemy.orm import joinedload as jl
            ru = db.query(User).options(jl(User.companies)).filter(User.id == responsible_user.id).first()
            resp_company_ids = [c.id for c in ru.companies] if ru else []
            if resp_company_ids and target_company_id not in resp_company_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El responsable '{new_responsible}' no pertenece a la empresa seleccionada"
                )

    # Actualizar
    update_data = project_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/close")
async def close_project(
    project_id: int,
    request: CloseProjectRequest = CloseProjectRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cerrar proyecto (ADMIN, BOSS de la empresa, o dueño del proyecto)"""

    # LOGIC-M3: SELECT FOR UPDATE para prevenir race conditions (dos cierres simultáneos)
    project = db.query(Project).with_for_update().filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # LOGIC-M3: Verificar que no esté ya cerrado (después de obtener el lock)
    if project.status == ProjectStatus.CERRADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project is already closed"
        )

    # Validar permisos: ADMIN, BOSS de la empresa, o dueño
    if not can_modify_project(current_user, project, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cerrar este proyecto"
        )

    from app.models.database import Ticket
    tickets = db.query(Ticket).filter(Ticket.project_id == project_id).all()

    if not tickets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot close project without tickets"
        )

    excel_bytes = generate_project_excel_bytes(project, tickets, db)

    recipients = []
    if request.recipients and len(request.recipients) > 0:
        recipients = request.recipients
    else:
        recipients.append('miguel@dazzcreative.com')
        responsible_email = RESPONSIBLE_EMAILS.get(project.responsible)
        if responsible_email and responsible_email not in recipients:
            recipients.append(responsible_email)

    # Sanitizar creative_code para filenames (email + HTTP response)
    safe_code = re.sub(r'[^\w\-.]', '_', project.creative_code)

    email_sent = False
    email_error = None
    if excel_bytes and recipients:
        try:
            from app.services.email import send_project_closed_email_multi
            filename = f"{safe_code}_GASTOS.xlsx"
            send_project_closed_email_multi(
                recipients=recipients,
                project_name=project.description,
                project_code=project.creative_code,
                responsible_name=project.responsible,
                tickets_count=len(tickets),
                total_amount=project.total_amount,
                excel_bytes=excel_bytes,
                excel_filename=filename
            )
            email_sent = True
            logger.info(f"Email cierre proyecto enviado a: {recipients}")
        except Exception as e:
            # Log completo para debugging interno
            logger.error(f"EMAIL CIERRE FALLÓ para {project.creative_code}: {str(e)}")
            logger.error(f"Destinatarios: {recipients}")
            # Header sanitizado — no exponer detalles internos al cliente
            email_error = "Email delivery failed"

    project.status = ProjectStatus.CERRADO
    project.closed_at = datetime.now(timezone.utc)
    db.commit()

    return build_excel_response(project, excel_bytes, {
        "X-Email-Sent": "true" if email_sent else "false",
        "X-Email-Error": email_error or "",
    })


@router.post("/{project_id}/reopen")
async def reopen_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reabrir proyecto (ADMIN, BOSS o WORKER con acceso al proyecto)"""

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # ← FIX: cualquier rol puede reabrir si tiene acceso al proyecto
    # ADMIN → siempre / BOSS → su empresa / WORKER → sus propios proyectos
    if not can_access_project(current_user, project, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para reabrir este proyecto"
        )

    project.status = ProjectStatus.EN_CURSO
    project.closed_at = None
    db.commit()
    return {"message": "Project reopened successfully", "project_id": project_id}


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar proyecto (ADMIN, BOSS de la empresa, o dueño)"""

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Validar permisos de eliminación
    if not can_modify_project(current_user, project, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este proyecto"
        )

    # Guardar info ANTES de eliminar (para logging)
    project_code = project.creative_code
    tickets_count = 0

    # BUG-59: Unlink supplier invoices before deleting (keep OC intact, remove project link)
    try:
        from app.models.suppliers import SupplierInvoice
        supplier_invoices = db.query(SupplierInvoice).filter(
            SupplierInvoice.project_id == project_id
        ).all()
        for inv in supplier_invoices:
            inv.project_id = None
        if supplier_invoices:
            logger.info(f"Unlinked {len(supplier_invoices)} supplier invoices from project {project_id}")
    except Exception as e:
        logger.warning(f"Error unlinking supplier invoices: {e}")

    # 1. BORRAR TODOS LOS TICKETS DEL PROYECTO (con sus archivos en Cloudinary)
    from app.models.database import Ticket
    tickets = db.query(Ticket).filter(Ticket.project_id == project_id).all()
    tickets_count = len(tickets)

    if tickets:
        logger.info(f"Borrando {tickets_count} tickets del proyecto {project_id}")

        try:
            from app.services.cloudinary_service import delete_ticket_files

            for ticket in tickets:
                # INT-1: Skip Cloudinary cleanup for supplier tickets (files belong to supplier module)
                if not ticket.from_supplier_portal:
                    try:
                        delete_ticket_files(ticket.file_pages, ticket.pdf_url)
                        logger.info(f"Archivos eliminados para ticket {ticket.id}")
                    except Exception as e:
                        logger.warning(f"Error eliminando archivos del ticket {ticket.id}: {str(e)}")

                # Borrar ticket de BD
                db.delete(ticket)

            logger.info(f"{tickets_count} tickets eliminados")
        except Exception as e:
            logger.warning(f"Error durante borrado de tickets: {str(e)}")
            # Continuar con el borrado del proyecto aunque falle

    # 2. BORRAR EL PROYECTO
    db.delete(project)
    db.commit()

    # LOGGING CRÍTICO AMARILLO - Proyecto eliminado
    log_project_deleted(
        project_id=project_id,
        project_code=project_code,
        admin_email=current_user.email,
        tickets_count=tickets_count
    )

    logger.info(f"Proyecto {project_id} eliminado completamente")
    return None


@router.post("/recalculate-totals")
async def recalculate_project_totals(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """BUG-52: Recalculate tickets_count and total_amount for all projects from actual ticket data."""
    from app.models.database import Ticket

    # PERF-1: Single GROUP BY instead of 2 queries per project
    # BUG-69: Exclude suplido tickets from total_amount but count them in tickets_count
    aggregates = db.query(
        Ticket.project_id,
        func.count(Ticket.id),
        func.coalesce(func.sum(case(
            (Ticket.is_suplido == True, 0.0),
            else_=Ticket.final_total,
        )), 0.0),
    ).filter(
        Ticket.provider != "Error en extracción",
    ).group_by(Ticket.project_id).all()

    totals = {row[0]: (row[1], float(row[2])) for row in aggregates}

    projects = db.query(Project).all()
    fixed = []

    for project in projects:
        real_count, real_total = totals.get(project.id, (0, 0.0))

        if project.tickets_count != real_count or abs((project.total_amount or 0) - real_total) > 0.01:
            logger.warning(
                f"Project {project.id} ({project.creative_code}): "
                f"count {project.tickets_count}→{real_count}, "
                f"total {project.total_amount}→{real_total}"
            )
            fixed.append({
                "id": project.id,
                "code": project.creative_code,
                "old_count": project.tickets_count,
                "new_count": real_count,
                "old_total": float(project.total_amount or 0),
                "new_total": float(real_total),
            })
            project.tickets_count = real_count
            project.total_amount = real_total

    db.commit()
    return {"fixed": len(fixed), "details": fixed}


# ============================================
# SHARE TOKENS (FEAT-09) — acceso externo link + PIN
# ============================================

def _is_mgmt_project(project) -> bool:
    """True si la empresa del proyecto es MGMT (no se permite compartir con externos)."""
    company_name = (project.owner_company.name if project.owner_company else None) or project.company or ""
    return "MGMT" in company_name.upper()


def _to_naive_utc(dt: datetime) -> datetime:
    """Normaliza un datetime (naive o aware) a UTC naive para guardarlo en la BD."""
    aware = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    return aware.astimezone(timezone.utc).replace(tzinfo=None)


@router.get("/{project_id}/excel")
async def download_project_excel(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Descargar el Excel del proyecto SIN cerrarlo (el estado sigue EN_CURSO).

    Permite descargar incluso con 0 tickets (plantilla con los datos del proyecto).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver este proyecto")

    from app.models.database import Ticket
    tickets = db.query(Ticket).filter(Ticket.project_id == project_id).all()
    excel_bytes = generate_project_excel_bytes(project, tickets, db)
    return build_excel_response(project, excel_bytes)


@router.post("/{project_id}/share-tokens", response_model=schemas.ShareTokenCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_share_token(
    project_id: int,
    body: schemas.ShareTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generar un link + PIN para acceso externo a un proyecto (solo producción, no MGMT).

    El PIN se devuelve en texto plano ÚNICAMENTE aquí (en BD se guarda hasheado).
    """
    project = db.query(Project).options(joinedload(Project.owner_company)).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if not can_modify_project(current_user, project, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para compartir este proyecto")

    if _is_mgmt_project(project):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se pueden compartir proyectos MGMT")

    # La fecha de expiración debe ser futura.
    now = datetime.now(timezone.utc)
    expires_aware = body.expires_at.replace(tzinfo=timezone.utc) if body.expires_at.tzinfo is None else body.expires_at
    if expires_aware <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La fecha de expiración debe ser futura")

    # Límite: máximo 10 links activos por proyecto.
    active_count = db.query(func.count(ProjectShareToken.id)).filter(
        ProjectShareToken.project_id == project_id,
        ProjectShareToken.is_active == True,
    ).scalar()
    if active_count >= 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Máximo 10 links activos por proyecto")

    token = generate_share_token()
    pin = generate_pin()
    share = ProjectShareToken(
        project_id=project_id,
        token=token,
        pin_hash=get_password_hash(pin),
        guest_name=body.guest_name,
        expires_at=_to_naive_utc(body.expires_at),
        created_by=current_user.id,
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    return schemas.ShareTokenCreateResponse(
        id=share.id,
        token=token,
        pin=pin,
        guest_name=share.guest_name,
        expires_at=share.expires_at,
        share_url=f"{FRONTEND_URL}/share/{token}",
    )


@router.get("/{project_id}/share-tokens", response_model=List[schemas.ShareTokenResponse])
async def list_share_tokens(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Listar los links del proyecto (nunca devuelve token ni pin_hash)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver este proyecto")

    tokens = db.query(ProjectShareToken).filter(
        ProjectShareToken.project_id == project_id,
        ProjectShareToken.hidden != True,
    ).order_by(ProjectShareToken.created_at.desc()).all()

    # Batch load de nombres de los creadores (evita N+1).
    creator_ids = list({t.created_by for t in tokens})
    creators = {u.id: u.name for u in db.query(User).filter(User.id.in_(creator_ids)).all()} if creator_ids else {}

    now = datetime.now(timezone.utc)
    result = []
    for t in tokens:
        exp_aware = t.expires_at.replace(tzinfo=timezone.utc) if t.expires_at.tzinfo is None else t.expires_at
        result.append(schemas.ShareTokenResponse(
            id=t.id,
            guest_name=t.guest_name,
            expires_at=t.expires_at,
            is_active=t.is_active,
            created_at=t.created_at,
            last_accessed_at=t.last_accessed_at,
            last_accessed_ip=t.last_accessed_ip,
            created_by_name=creators.get(t.created_by, "—"),
            is_expired=exp_aware < now,
            share_url=f"{FRONTEND_URL}/share/{t.token}",
        ))
    return result


@router.delete("/{project_id}/share-tokens/{token_id}")
async def revoke_share_token(
    project_id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Revocar un link (is_active=False). NO se borra físicamente (auditoría)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if not can_modify_project(current_user, project, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para revocar links de este proyecto")

    share = db.query(ProjectShareToken).filter(
        ProjectShareToken.id == token_id,
        ProjectShareToken.project_id == project_id,
    ).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link no encontrado")

    share.is_active = False
    db.commit()
    return {"message": "Link revocado"}


@router.patch("/{project_id}/share-tokens/{token_id}/hide")
async def hide_share_token(
    project_id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Ocultar un link del panel (hidden=True). Solo para links ya revocados — no borra de BD."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if not can_modify_project(current_user, project, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para modificar links de este proyecto")

    share = db.query(ProjectShareToken).filter(
        ProjectShareToken.id == token_id,
        ProjectShareToken.project_id == project_id,
    ).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link no encontrado")

    if share.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden ocultar links revocados")

    share.hidden = True
    db.commit()
    return {"message": "Link ocultado"}


@router.post("/{project_id}/share-tokens/{token_id}/regenerate-pin", response_model=schemas.RegeneratePinResponse)
async def regenerate_share_pin(
    project_id: int,
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Regenerar el PIN de un link activo. Devuelve el nuevo PIN en texto plano (única vez)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if not can_modify_project(current_user, project, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para modificar links de este proyecto")

    share = db.query(ProjectShareToken).filter(
        ProjectShareToken.id == token_id,
        ProjectShareToken.project_id == project_id,
    ).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link no encontrado")

    if not share.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede regenerar el PIN de un link revocado")

    now = datetime.now(timezone.utc)
    exp_aware = share.expires_at.replace(tzinfo=timezone.utc) if share.expires_at.tzinfo is None else share.expires_at
    if exp_aware <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede regenerar el PIN de un link expirado")

    pin = generate_pin()
    share.pin_hash = get_password_hash(pin)
    # Resetear bloqueo/intentos: el PIN anterior queda invalidado.
    share.failed_pin_attempts = 0
    share.locked_until = None
    db.commit()

    return schemas.RegeneratePinResponse(
        pin=pin,
        message="PIN regenerado. El anterior ya no es válido.",
    )
