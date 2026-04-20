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


def get_mgmt_company_ids(user: User) -> set:
    """
    IDs de las empresas del usuario cuyo nombre contiene "MGMT" (case-insensitive).

    BUG-65: los miembros de empresas MGMT ven y modifican TODOS los proyectos de
    esas empresas, independientemente de owner_id o responsible. Esto refleja la
    gestión de influencers en equipo — cualquiera del equipo MGMT debe poder
    operar sobre cualquier talento.
    """
    if not user or not user.companies:
        return set()
    return {c.id for c in user.companies if "MGMT" in (c.name or "").upper()}


def can_access_project(user: User, project: Project, db: Session) -> bool:
    """
    Verificar si un usuario puede acceder (ver) un proyecto.

    - ADMIN: acceso total
    - BOSS: proyectos de su empresa
    - WORKER: proyectos propios (owner/responsible) + bypass MGMT (todos los de empresas MGMT del user)
    """
    # DEUDA-M3: Usar enum UserRole en vez de strings literales
    if user.role == UserRole.ADMIN:
        return True

    company_ids = get_user_company_ids(user, db)
    if project.owner_company_id not in company_ids:
        return False

    if user.role == UserRole.BOSS:
        return True

    # WORKER
    if project.owner_company_id in get_mgmt_company_ids(user):
        return True  # BUG-65: MGMT team-wide visibility

    is_owner = project.owner_id == user.id
    is_responsible = (user.username or "").lower() == (project.responsible or "").lower()
    return is_owner or is_responsible


def can_modify_project(user: User, project: Project, db: Session) -> bool:
    """
    Verificar si un usuario puede modificar/eliminar un proyecto.

    - ADMIN: puede modificar cualquier proyecto
    - BOSS: puede modificar proyectos de su empresa
    - WORKER: proyectos propios + bypass MGMT (modifica todos los de sus empresas MGMT)
    """
    if user.role == UserRole.ADMIN:
        return True

    company_ids = get_user_company_ids(user, db)
    if project.owner_company_id not in company_ids:
        return False

    if user.role == UserRole.BOSS:
        return True

    # WORKER
    if project.owner_company_id in get_mgmt_company_ids(user):
        return True  # BUG-65: MGMT team-wide modify

    is_owner = project.owner_id == user.id
    is_responsible = (user.username or "").lower() == (project.responsible or "").lower()
    return is_owner or is_responsible
