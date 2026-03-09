from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
from app.models import schemas
from app.models.database import User, Project
from app.services.auth import get_current_admin_user, get_password_hash

# LOGGING CRÍTICO
from app.services.critical_logger import log_user_deleted, log_role_changed

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[schemas.UserResponse])  # ← Sin "/" 
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all users (admin only)"""
    users = db.query(User).all()
    return users

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get user by ID (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    user_update: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Detectar cambio de rol
    role_changed = False
    old_role = None
    new_role = None
    
    if user.role != user_update.role:
        role_changed = True
        old_role = user.role
        new_role = user_update.role
    
    user.name = user_update.name
    user.email = user_update.email
    user.role = user_update.role
    
    if user_update.password:
        user.hashed_password = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(user)
    
    # LOGGING CRÍTICO AMARILLO - Cambio de rol (si hubo)
    if role_changed:
        log_role_changed(
            target_user_email=user.email,
            old_role=old_role,
            new_role=new_role,
            admin_email=current_user.email
        )
    
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete user (admin only)
    
    OPCIÓN 2: Impedir borrar si tiene proyectos
    El usuario debe borrar/reasignar proyectos primero
    """
    # Verificar que no sea el propio admin
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes borrarte a ti mismo"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar si el usuario tiene proyectos
    user_projects = db.query(Project).filter(Project.owner_id == user_id).all()
    
    if user_projects:
        # Crear lista de proyectos para mostrar al usuario
        project_list = [
            f"{p.creative_code} - {p.description}" 
            for p in user_projects[:5]  # Máximo 5 para no saturar
        ]
        
        more_text = f" (y {len(user_projects) - 5} más)" if len(user_projects) > 5 else ""
        
        projects_text = "\n".join(project_list) + more_text
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede borrar este usuario porque tiene {len(user_projects)} proyecto(s) asignado(s).\n\nPrimero debes borrar o reasignar sus proyectos:\n{projects_text}"
        )
    
    # Guardar info ANTES de eliminar (para logging)
    user_email = user.email
    user_role = user.role
    
    # Si no tiene proyectos, borrar usuario
    db.delete(user)
    db.commit()
    
    # LOGGING CRÍTICO AMARILLO - Usuario eliminado
    log_user_deleted(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        admin_email=current_user.email
    )
    
    print(f"✅ Usuario {user_email} eliminado correctamente")
    
    return {
        "message": f"Usuario {user_email} eliminado correctamente"
    }
