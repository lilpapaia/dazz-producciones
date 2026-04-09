from sqlalchemy.orm import Session
from typing import List
from app.models.database import User, Company, UserRole


def _load_user_companies(user: User, db: Session) -> List[Company]:
    """Returns user companies (already loaded via joinedload in get_current_user)."""
    return user.companies if user else []


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
