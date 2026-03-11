"""
Funciones centralizadas de permisos y acceso.

Unifica la lógica duplicada que existía en projects.py y tickets.py.
"""
from typing import List
from sqlalchemy.orm import Session, joinedload
from app.models.database import User, Project


def get_user_company_ids(user: User, db: Session) -> List[int]:
    """
    Obtiene IDs de empresas del usuario, recargando desde DB
    para evitar DetachedInstanceError.

    Args:
        user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de IDs de empresas asignadas al usuario
    """
    u = db.query(User).options(joinedload(User.companies)).filter(User.id == user.id).first()
    return [c.id for c in u.companies] if u else []


def can_access_project(user: User, project: Project, db: Session) -> bool:
    """
    Verificar si un usuario puede acceder (ver) un proyecto.

    - ADMIN: acceso total
    - BOSS: proyectos de su empresa
    - WORKER: solo SUS proyectos de sus empresas
    """
    if user.role == "ADMIN":
        return True

    company_ids = get_user_company_ids(user, db)

    if user.role == "BOSS":
        return project.owner_company_id in company_ids

    # WORKER: solo sus propios proyectos de sus empresas
    if project.owner_id != user.id:
        return False
    return project.owner_company_id in company_ids


def can_modify_project(user: User, project: Project, db: Session) -> bool:
    """
    Verificar si un usuario puede modificar/eliminar un proyecto.

    - ADMIN: puede modificar cualquier proyecto
    - BOSS: puede modificar proyectos de su empresa
    - WORKER: puede modificar solo SUS proyectos
    """
    if user.role == "ADMIN":
        return True

    if user.role == "BOSS":
        company_ids = get_user_company_ids(user, db)
        return project.owner_company_id in company_ids

    # WORKER: solo sus propios proyectos
    return project.owner_id == user.id
