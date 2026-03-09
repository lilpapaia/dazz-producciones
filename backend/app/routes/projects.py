from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from io import BytesIO
from pydantic import BaseModel, EmailStr

from config.database import get_db
from app.models import schemas
from app.models.database import User, Project, ProjectStatus
from app.services.auth import get_current_active_user

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

@router.post("", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_project = Project(**project.dict(), owner_id=current_user.id, status=ProjectStatus.EN_CURSO)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("", response_model=List[schemas.ProjectResponse])
async def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), status: str = None):
    query = db.query(Project)
    if current_user.role != "admin":
        query = query.filter(Project.owner_id == current_user.id)
    if status:
        query = query.filter(Project.status == status)
    projects = query.order_by(Project.created_at.desc()).all()
    return projects

@router.get("/{project_id}", response_model=schemas.ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return project

@router.put("/{project_id}", response_model=schemas.ProjectResponse)
async def update_project(project_id: int, project_update: schemas.ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
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
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    from app.models.database import Ticket
    tickets = db.query(Ticket).filter(Ticket.project_id == project_id).all()
    
    if not tickets:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot close project without tickets")
    
    excel_bytes = None
    try:
        from app.services.excel_generator import create_project_excel_bytes
        excel_bytes = create_project_excel_bytes(project, tickets)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Excel generation failed: {str(e)}")
    
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate Excel")

@router.post("/{project_id}/reopen")
async def reopen_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can reopen projects")
    project.status = ProjectStatus.EN_CURSO
    project.closed_at = None
    db.commit()
    return {"message": "Project reopened successfully", "project_id": project_id}

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Verificar permisos: Admin o Owner del proyecto
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
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
