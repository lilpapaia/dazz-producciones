from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from config.database import get_db
from app.models import schemas
from app.models.database import User, Project, ProjectStatus
from app.services.auth import get_current_active_user

router = APIRouter(prefix="/projects", tags=["Projects"])

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
async def close_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Close a project, generate Excel and send email"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    from app.models.database import Ticket
    tickets = db.query(Ticket).filter(Ticket.project_id == project_id).all()
    project.status = ProjectStatus.CERRADO
    project.closed_at = datetime.utcnow()
    db.commit()
    excel_path = None
    try:
        from app.services.excel_generator import create_project_excel_from_db
        excel_path = create_project_excel_from_db(project, tickets)
        print(f"✅ Excel generated: {excel_path}")
    except Exception as e:
        print(f"⚠️ Warning: Excel generation failed: {str(e)}")
    if excel_path:
        try:
            from app.services.email import send_project_closed_email
            import os
            excel_filename = os.path.basename(excel_path)
            email_sent = send_project_closed_email(project_name=project.description, project_code=project.creative_code, responsible_name=project.responsible, responsible_email=project.owner.email if project.owner else "", tickets_count=project.tickets_count, total_amount=project.total_amount, excel_filename=excel_filename, excel_path=excel_path)
            if email_sent:
                print(f"✅ Email sent successfully")
            else:
                print(f"⚠️ Warning: Email could not be sent")
        except Exception as e:
            print(f"⚠️ Warning: Email sending failed: {str(e)}")
    return {"message": "Project closed successfully. Excel generated and email sent.", "project_id": project_id, "total_amount": project.total_amount, "tickets_count": project.tickets_count, "excel_generated": excel_path is not None, "excel_path": excel_path}

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
