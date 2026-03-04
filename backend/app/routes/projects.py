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

router = APIRouter(prefix="/projects", tags=["Projects"])

# Mapeo de emails responsables (compatibilidad)
RESPONSIBLE_EMAILS = {
    'MIGUEL': 'miguel@dazzcreative.com',
    'JULIETA': 'julieta@dazzcreative.com',
    'ANTONIO': 'antonio@dazzcreative.com'
}

# Schema para recibir emails personalizados
class CloseProjectRequest(BaseModel):
    recipients: Optional[List[EmailStr]] = None

@router.post("/", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new project"""
    db_project = Project(**project.dict(), owner_id=current_user.id, status=ProjectStatus.EN_CURSO)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=List[schemas.ProjectResponse])
async def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), status: str = None):
    """Get all projects (admins see all, users see only theirs)"""
    query = db.query(Project)
    if current_user.role != "admin":
        query = query.filter(Project.owner_id == current_user.id)
    if status:
        query = query.filter(Project.status == status)
    projects = query.order_by(Project.created_at.desc()).all()
    return projects

@router.get("/{project_id}", response_model=schemas.ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Get a specific project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return project

@router.put("/{project_id}", response_model=schemas.ProjectResponse)
async def update_project(project_id: int, project_update: schemas.ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Update a project"""
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
    """Close project, generate Excel, send to custom recipients, return Excel for download"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    from app.models.database import Ticket
    tickets = db.query(Ticket).filter(Ticket.project_id == project_id).all()
    
    if not tickets:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot close project without tickets")
    
    # Generar Excel en memoria
    excel_bytes = None
    try:
        from app.services.excel_generator import create_project_excel_bytes
        excel_bytes = create_project_excel_bytes(project, tickets)
        print(f"✅ Excel generated in memory")
    except Exception as e:
        print(f"⚠️ Warning: Excel generation failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Excel generation failed: {str(e)}")
    
    # Preparar destinatarios email
    recipients = []
    
    if request.recipients and len(request.recipients) > 0:
        # Usar emails personalizados del frontend
        recipients = request.recipients
        print(f"📧 Usando emails personalizados: {recipients}")
    else:
        # Fallback: usar mapeo antiguo (compatibilidad)
        recipients.append('miguel@dazzcreative.com')
        responsible_email = RESPONSIBLE_EMAILS.get(project.responsible)
        if responsible_email and responsible_email not in recipients:
            recipients.append(responsible_email)
        print(f"📧 Usando emails por defecto (compatibilidad): {recipients}")
    
    # Enviar email con Excel adjunto
    if excel_bytes and recipients:
        try:
            from app.services.email import send_project_closed_email_multi
            filename = f"{project.creative_code}_GASTOS.xlsx"
            
            email_sent = send_project_closed_email_multi(
                recipients=recipients,
                project_name=project.description,
                project_code=project.creative_code,
                responsible_name=project.responsible,
                tickets_count=len(tickets),
                total_amount=project.total_amount,
                excel_bytes=excel_bytes,
                excel_filename=filename
            )
            
            if email_sent:
                print(f"✅ Email sent to: {', '.join(recipients)}")
            else:
                print(f"⚠️ Warning: Email could not be sent")
        except Exception as e:
            print(f"⚠️ Warning: Email sending failed: {str(e)}")
            # Continuar aunque falle email
    
    # Marcar proyecto como cerrado
    project.status = ProjectStatus.CERRADO
    project.closed_at = datetime.utcnow()
    db.commit()
    
    print(f"✅ Project {project_id} closed successfully")
    
    # Retornar Excel como blob para descarga
    if excel_bytes:
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={project.creative_code}_GASTOS.xlsx"
            }
        )
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate Excel")

@router.post("/{project_id}/reopen")
async def reopen_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Reopen a closed project"""
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
    """Delete a project (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete projects")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    db.delete(project)
    db.commit()
    return None
