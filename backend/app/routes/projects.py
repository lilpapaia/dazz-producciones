import re
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime, timezone
from io import BytesIO
from pydantic import BaseModel, EmailStr

from config.database import get_db
from app.models import schemas
from app.models.database import User, Project, ProjectStatus, Company, UserRole
from app.services.auth import get_current_active_user
from app.services.companies_service import validate_company_access
from app.services.permissions import get_user_company_ids, can_access_project, can_modify_project

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

    # Crear proyecto (company es campo legacy NOT NULL, rellenar con nombre de empresa)
    db_project = Project(**project.dict(exclude={"company"}), owner_id=current_user.id, status=ProjectStatus.EN_CURSO, company=company.name)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Legacy auto-link: handle any existing OC_PENDING invoices (new invoices require OC to exist)
    try:
        from app.models.suppliers import SupplierInvoice, InvoiceStatus, NotificationRecipientType, NotificationEventType, SupplierNotification
        pending_invoices = db.query(SupplierInvoice).filter(
            SupplierInvoice.oc_number.ilike(db_project.creative_code),
            SupplierInvoice.status == InvoiceStatus.OC_PENDING,
        ).all()
        for inv in pending_invoices:
            inv.project_id = db_project.id
            inv.company_id = db_project.owner_company_id
            inv.status = InvoiceStatus.PENDING
            # Notify admin
            notif = SupplierNotification(
                recipient_type=NotificationRecipientType.ADMIN,
                recipient_id=0,
                event_type=NotificationEventType.OC_LINKED,
                title="OC Linked",
                message=f"Invoice {inv.invoice_number} linked to project {db_project.creative_code}",
                related_invoice_id=inv.id,
                related_supplier_id=inv.supplier_id,
            )
            db.add(notif)
        if pending_invoices:
            db.commit()
            logger.info(f"Auto-linked {len(pending_invoices)} OC_PENDING invoices to project {db_project.creative_code}")
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
        # WORKER ve proyectos donde es owner O responsible (case-insensitive)
        user_company_ids = get_user_company_ids(current_user, db)
        username_lower = (current_user.username or "").lower()
        query = query.filter(
            or_(
                Project.owner_id == current_user.id,
                func.lower(Project.responsible) == username_lower,
            ),
            Project.owner_company_id.in_(user_company_ids)
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

    project = db.query(Project).filter(Project.id == project_id).first()
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

    # Actualizar
    update_data = project_update.dict(exclude_unset=True)
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

    excel_bytes = None
    try:
        from app.services.excel_generator import create_project_excel_bytes
        excel_bytes = create_project_excel_bytes(project, tickets)
    except Exception as e:
        logger.error(f"Error generando Excel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar Excel"
        )

    recipients = []
    if request.recipients and len(request.recipients) > 0:
        recipients = request.recipients
    else:
        recipients.append('miguel@dazzcreative.com')
        responsible_email = RESPONSIBLE_EMAILS.get(project.responsible)
        if responsible_email and responsible_email not in recipients:
            recipients.append(responsible_email)

    if excel_bytes and recipients:
        try:
            from app.services.email import send_project_closed_email_multi
            filename = f"{project.creative_code}_GASTOS.xlsx"
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
        except Exception as e:
            logger.warning(f"Email sending failed: {str(e)}")

    project.status = ProjectStatus.CERRADO
    project.closed_at = datetime.now(timezone.utc)
    db.commit()

    if excel_bytes:
        # VULN-010: Sanitizar creative_code para Content-Disposition header
        safe_code = re.sub(r'[^\w\-.]', '_', project.creative_code)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{safe_code}_GASTOS.xlsx"'}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Excel"
        )


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

    # 1. BORRAR TODOS LOS TICKETS DEL PROYECTO (con sus archivos en Cloudinary)
    from app.models.database import Ticket
    tickets = db.query(Ticket).filter(Ticket.project_id == project_id).all()
    tickets_count = len(tickets)

    if tickets:
        logger.info(f"Borrando {tickets_count} tickets del proyecto {project_id}")

        try:
            from app.services.cloudinary_service import delete_ticket_files

            for ticket in tickets:
                # Borrar archivos de Cloudinary
                try:
                    delete_ticket_files(ticket.file_pages, ticket.pdf_url)
                    logger.info(f"Archivos eliminados para ticket {ticket.id}")
                except Exception as e:
                    logger.warning(f"Error eliminando archivos del ticket {ticket.id}: {str(e)}")
                    # Continuar aunque falle

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
