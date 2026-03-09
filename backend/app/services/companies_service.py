from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.database import User, Company

def get_user_companies(user: User, db: Session) -> List[Company]:
    """
    Obtener las empresas a las que un usuario tiene acceso.
    
    Args:
        user: Usuario actual
        db: Sesión de base de datos
    
    Returns:
        Lista de empresas accesibles por el usuario
    """
    if user.role == "ADMIN":
        # ADMIN ve todas las empresas
        return db.query(Company).order_by(Company.name).all()
    else:
        # BOSS y WORKER ven solo sus empresas asignadas
        return sorted(user.companies, key=lambda c: c.name)


def validate_company_access(user: User, company_id: int) -> bool:
    """
    Verificar si un usuario tiene acceso a una empresa específica.
    
    Args:
        user: Usuario actual
        company_id: ID de la empresa a verificar
    
    Returns:
        True si tiene acceso, False en caso contrario
    """
    if user.role == "ADMIN":
        # ADMIN tiene acceso a todas
        return True
    
    # BOSS y WORKER solo a sus empresas asignadas
    user_company_ids = [c.id for c in user.companies]
    return company_id in user_company_ids


def get_company_by_id(company_id: int, db: Session) -> Optional[Company]:
    """
    Obtener una empresa por su ID.
    
    Args:
        company_id: ID de la empresa
        db: Sesión de base de datos
    
    Returns:
        Empresa si existe, None en caso contrario
    """
    return db.query(Company).filter(Company.id == company_id).first()


def check_user_has_companies(user: User) -> bool:
    """
    Verificar si un usuario tiene al menos una empresa asignada.
    
    Args:
        user: Usuario a verificar
    
    Returns:
        True si tiene empresas, False en caso contrario
    """
    if user.role == "ADMIN":
        # ADMIN siempre tiene acceso (a todas)
        return True
    
    return len(user.companies) > 0
