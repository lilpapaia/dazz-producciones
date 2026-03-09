from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
from app.models import schemas
from app.models.database import User, Company
from app.services.auth import get_current_active_user

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("", response_model=List[schemas.CompanyResponse])
async def get_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener empresas disponibles según el rol del usuario:
    - ADMIN: ve todas las empresas
    - BOSS: ve solo su empresa
    - WORKER: ve sus empresas asignadas
    """
    
    if current_user.role == "ADMIN":
        # ADMIN ve TODAS las empresas
        companies = db.query(Company).order_by(Company.name).all()
        return companies
    
    else:
        # BOSS y WORKER ven solo sus empresas asignadas
        companies = current_user.companies  # Relación many-to-many
        
        if not companies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tienes empresas asignadas. Contacta con un administrador."
            )
        
        return sorted(companies, key=lambda c: c.name)


@router.get("/{company_id}", response_model=schemas.CompanyResponse)
async def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener detalles de una empresa específica.
    Solo si el usuario tiene acceso a ella.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    # Verificar acceso
    if current_user.role != "ADMIN":
        # BOSS y WORKER solo pueden ver sus empresas
        user_company_ids = [c.id for c in current_user.companies]
        
        if company_id not in user_company_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta empresa"
            )
    
    return company


# ============================================
# ENDPOINTS FUTUROS (solo admin - Fase 8)
# ============================================

# @router.post("", response_model=schemas.CompanyResponse)
# async def create_company(...):
#     """Crear nueva empresa (solo admin)"""
#     pass

# @router.put("/{company_id}", response_model=schemas.CompanyResponse)
# async def update_company(...):
#     """Actualizar empresa (solo admin)"""
#     pass

# @router.delete("/{company_id}")
# async def delete_company(...):
#     """Eliminar empresa (solo admin)"""
#     pass
