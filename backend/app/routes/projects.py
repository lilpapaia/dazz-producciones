from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from io import BytesIO
from pydantic import BaseModel, EmailStr

from config.database import get_db
from app.models import schemas
from app.models.database import User, Project, ProjectStatus, Company
from app.services.auth import get_current_active_user
from app.services.companies_service import validate_company_access  # ← NUEVO

# LOGGING CRÍTICO
from app.services.critical_logger import log_project_deleted

router = APIRouter(prefix="/projects", tags=["Projects"])

RESPONSIBLE_EMAILS = {
    'MIGUEL': 'miguel@dazzcreative.com',
    'JULIETA': 'julieta@dazzcreative.com',
    'ANTONIO': 'antonio@dazzcreative.com'
}

class CloseProjectRequest(BaseModel):
    recipients: Optional[List[EmailStr]] = None


# ============================================
# HELPER: Validar acceso a proyecto según empresa
# ============================================

def can_access_project(user: User, project: Project) -> bool:
    """
    Verificar si un usuario puede acceder a un proyecto.
    
    - ADMIN: puede acceder a cualquier proyecto
    - BOSS: puede acceder a proyectos de su empresa
    - WORKER: puede acceder solo a SUS proyectos de sus empresas
    """
    if user.role == "ADMIN":
        return True
    
    if user.role == "BOSS":
        # BOSS puede ver todos los proyectos de su empresa
        user_company_ids = [c.id for c in user.companies]
        return project.owner_company_id in user_company_ids
    
    # WORKER: solo sus propios proyectos de sus empresas
    if project.owner_id != user.id:
        return False
    
    user_company_ids = [c.id for c in user.companies]
    return project.owner_company_id in user_company_ids


def can_modify_project(user: User, project: Project) -> bool:
    """
    Verificar si un usuario puede modificar/eliminar un proyecto.
    
    - ADMIN: puede modificar cualquier proyecto
    - BOSS: puede modificar proyectos de su empresa
    - WORKER: puede modificar solo SUS proyectos
    """
    if user.role == "ADMIN":
        return True
    
    if user.role == "BOSS":
        # BOSS puede modificar todos los proyectos de su empresa
        user_company_ids = [c.id for c in user.companies]
        return project.owner_company_id in user_company_ids
    
    # WORKER: solo sus propios proyectos
    return project.owner_id == user.id


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
    if not validate_company_access(current_user, project.owner_company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes permiso para crear proyectos en {company.name}"
        )
    
    # Crear proyecto (company es campo legacy NOT NULL, rellenar con nombre de empresa)
    db_project = Project(**project.dict(), owner_id=current_user.id, status=ProjectStatus.EN_CURSO, company=company.name)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
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
    
    query = db.query(Project)
    
    if current_user.role == "ADMIN":
        # ADMIN ve TODOS los proyectos
        pass
    
    elif current_user.role == "BOSS":
        # BOSS ve todos los proyectos de su empresa
        user_company_ids = [c.id for c in current_user.companies]
        query = query.filter(Project.owner_company_id.in_(user_company_ids))
    
    else:
        # WORKER ve solo SUS proyectos de sus empresas
        user_company_ids = [c.id for c in current_user.companies]
        query = query.filter(
            Project.owner_id == current_user.id,
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
    if not can_access_project(current_user, project):
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
    if not can_modify_project(current_user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para editar este proyecto"
        )
    
    # Si se intenta cambiar owner_company_id, validar acceso a la nueva empresa
    if project_update.owner_company_id and project_update.owner_company_id != project.owner_company_id:
        if not validate_company_access(current_user, project_update.owner_company_id):
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
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Validar permisos: ADMIN, BOSS de la empresa, o dueño
    if not can_modify_project(current_user, project):
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel generation failed: {str(e)}"
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
            print(f"Warning: Email sending failed: {str(e)}")
    
    project.status = ProjectStatus.CERRADO
    project.closed_at = datetime.utcnow()
    db.commit()
    
    if excel_bytes:
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={project.creative_code}_GASTOS.xlsx"}
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
    """Reabrir proyecto (ADMIN o BOSS de la empresa)"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # ADMIN o BOSS de la empresa pueden reabrir
    if current_user.role == "ADMIN":
        pass  # ADMIN puede siempre
    elif current_user.role == "BOSS":
        # Validar que es BOSS de la empresa del proyecto
        user_company_ids = [c.id for c in current_user.companies]
        if project.owner_company_id not in user_company_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el BOSS de la empresa puede reabrir proyectos"
            )
    else:
        # WORKER no puede reabrir
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo ADMIN o BOSS pueden reabrir proyectos"
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
    if not can_modify_project(current_user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este proyecto"
        )
    
    # Guardar info ANTES de eliminar (para logging)
    project_code = project.creative_code
    
    # 1. BORRAR TODOS LOS TICKETS DEL PROYECTO (con sus archivos en Cloudinary)
    from app.models.database import Ticket
    tickets = db.query(Ticket).filter(Ticket.project_id == project_id).all()
    tickets_count = len(tickets)
    
    if tickets:
        print(f"🗑️ Borrando {tickets_count} tickets del proyecto {project_id}")
        
        try:
            from app.services.cloudinary_service import delete_ticket_files
            
            for ticket in tickets:
                # Borrar archivos de Cloudinary
                try:
                    delete_ticket_files(ticket.file_pages, ticket.pdf_url)
                    print(f"  ✅ Archivos eliminados para ticket {ticket.id}")
                except Exception as e:
                    print(f"  ⚠️ Error eliminando archivos del ticket {ticket.id}: {str(e)}")
                    # Continuar aunque falle
                
                # Borrar ticket de BD
                db.delete(ticket)
            
            print(f"✅ {tickets_count} tickets eliminados")
        except Exception as e:
            print(f"⚠️ Error durante borrado de tickets: {str(e)}")
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
    
    print(f"✅ Proyecto {project_id} eliminado completamente")
    return None
