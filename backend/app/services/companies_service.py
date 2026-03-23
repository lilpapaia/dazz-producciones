from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.database import User, Company, UserRole

def _load_user_companies(user: User, db: Session) -> List[Company]:
    """Recarga companies desde DB para evitar DetachedInstanceError."""
    from sqlalchemy.orm import joinedload
    u = db.query(User).options(joinedload(User.companies)).filter(User.id == user.id).first()
    return u.companies if u else []


def get_user_companies(user: User, db: Session) -> List[Company]:
    """
    Obtener las empresas a las que un usuario tiene acceso.
    """
    if user.role == UserRole.ADMIN:
        return db.query(Company).order_by(Company.name).all()
    else:
        companies = _load_user_companies(user, db)
        return sorted(companies, key=lambda c: c.name)


def validate_company_access(user: User, company_id: int, db: Session = None) -> bool:
    """
    Verificar si un usuario tiene acceso a una empresa específica.
    """
    if user.role == UserRole.ADMIN:
        return True

    if db is not None:
        companies = _load_user_companies(user, db)
    else:
        companies = user.companies

    user_company_ids = [c.id for c in companies]
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
    if user.role == UserRole.ADMIN:
        # ADMIN siempre tiene acceso (a todas)
        return True
    
    return len(user.companies) > 0
