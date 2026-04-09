"""
Funciones centralizadas de permisos y acceso.

Unifica la lógica duplicada que existía en projects.py y tickets.py.
"""
from typing import List
from sqlalchemy.orm import Session
from app.models.database import User, Project, UserRole


def get_user_company_ids(user: User, db: Session) -> List[int]:
    """
    Obtiene IDs de empresas del usuario.
    user.companies ya está cargado con joinedload desde get_current_user.

    Args:
        user: Usuario autenticado
        db: Sesión de base de datos (mantenido por compatibilidad de firma)

    Returns:
        Lista de IDs de empresas asignadas al usuario
    """
    return [c.id for c in user.companies] if user else []


def can_access_project(user: User, project: Project, db: Session) -> bool:
    """
    Verificar si un usuario puede acceder (ver) un proyecto.

    - ADMIN: acceso total
    - BOSS: proyectos de su empresa
    - WORKER: solo SUS proyectos de sus empresas
    """
    # DEUDA-M3: Usar enum UserRole en vez de strings literales
    if user.role == UserRole.ADMIN:
        return True

    company_ids = get_user_company_ids(user, db)

    if user.role == UserRole.BOSS:
        return project.owner_company_id in company_ids

    # WORKER: proyectos donde es owner O responsible
    is_owner = project.owner_id == user.id
    is_responsible = (user.username or "").lower() == (project.responsible or "").lower()
    if not is_owner and not is_responsible:
        return False
    return project.owner_company_id in company_ids


def can_modify_project(user: User, project: Project, db: Session) -> bool:
    """
    Verificar si un usuario puede modificar/eliminar un proyecto.

    - ADMIN: puede modificar cualquier proyecto
    - BOSS: puede modificar proyectos de su empresa
    - WORKER: puede modificar solo SUS proyectos
    """
    if user.role == UserRole.ADMIN:
        return True

    if user.role == UserRole.BOSS:
        company_ids = get_user_company_ids(user, db)
        return project.owner_company_id in company_ids

    # WORKER: proyectos donde es owner O responsible, AND misma empresa
    company_ids = get_user_company_ids(user, db)
    is_owner = project.owner_id == user.id
    is_responsible = (user.username or "").lower() == (project.responsible or "").lower()
    return (is_owner or is_responsible) and project.owner_company_id in company_ids
