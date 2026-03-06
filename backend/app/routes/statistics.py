from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import datetime

from config.database import get_db
from app.models import schemas
from app.models.database import User, Project, Ticket, ProjectStatus
from app.services.auth import get_current_active_user
from app.services.geographic_classifier import classify_geography, get_country_name

router = APIRouter(prefix="/statistics", tags=["Statistics"])

MONTH_NAMES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

@router.get("/overview", response_model=schemas.StatisticsOverview)
async def get_statistics_overview(
    year: int = Query(..., description="Año a consultar"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Trimestre (1-4), opcional"),
    geo_filter: Optional[str] = Query(None, description="NACIONAL, UE, INTERNACIONAL"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene métricas generales para los cards principales
    
    Filtros:
    - year: Año obligatorio
    - quarter: Trimestre opcional (1=Q1, 2=Q2, 3=Q3, 4=Q4)
    - geo_filter: Filtrar por geografía (NACIONAL, UE, INTERNACIONAL)
    """
    
    # Base query para tickets del año
    query = db.query(Ticket).join(Project).filter(
        Project.year == str(year)
    )
    
    # Filtrar por trimestre si se especifica
    if quarter:
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3
        # Filtrar por rango de meses (asumiendo formato DD/MM/YYYY)
        # Nota: esto es una aproximación, idealmente date debería ser Date no String
        query = query.filter(
            func.substr(Ticket.date, 4, 2).cast(db.bind.dialect.NUMERIC).between(start_month, end_month)
        )
    
    # Filtrar por geografía si se especifica
    if geo_filter:
        query = query.filter(Ticket.geo_classification == geo_filter)
    
    tickets = query.all()
    
    # Calcular totales
    total_spent = sum(ticket.final_total for ticket in tickets)
    
    # Gastos internacionales (UE + INTERNACIONAL)
    international_tickets = [t for t in tickets if t.geo_classification in ['UE', 'INTERNACIONAL']]
    international_spent = sum(ticket.final_total for ticket in international_tickets)
    
    # IVA reclamable (solo tickets internacionales con foreign_tax_eur)
    iva_reclamable = sum(
        ticket.foreign_tax_eur or 0.0 
        for ticket in international_tickets 
        if ticket.foreign_tax_eur
    )
    
    # Contar proyectos
    projects_query = db.query(Project).filter(Project.year == str(year))
    
    if current_user.role != "admin":
        projects_query = projects_query.filter(Project.owner_id == current_user.id)
    
    projects_total = projects_query.count()
    projects_closed = projects_query.filter(Project.status == ProjectStatus.CERRADO).count()
    projects_open = projects_total - projects_closed
    
    return schemas.StatisticsOverview(
        total_spent=total_spent,
        international_spent=international_spent,
        iva_reclamable=iva_reclamable,
        projects_total=projects_total,
        projects_closed=projects_closed,
        projects_open=projects_open
    )


@router.get("/monthly-evolution", response_model=List[schemas.MonthlyDataPoint])
async def get_monthly_evolution(
    year: int = Query(..., description="Año a consultar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la evolución de gastos por mes para el gráfico de líneas
    
    Retorna 12 puntos de datos (uno por mes) con el total gastado cada mes
    """
    
    # Query todos los tickets del año
    tickets = db.query(Ticket).join(Project).filter(
        Project.year == str(year)
    ).all()
    
    # Inicializar array con 12 meses en 0
    monthly_totals = [0.0] * 12
    
    # Sumar gastos por mes
    for ticket in tickets:
        try:
            # Extraer mes de la fecha (formato DD/MM/YYYY)
            if ticket.date and "/" in ticket.date:
                parts = ticket.date.split("/")
                if len(parts) >= 2:
                    month = int(parts[1]) - 1  # 0-indexed
                    if 0 <= month < 12:
                        monthly_totals[month] += ticket.final_total
        except:
            continue
    
    # Convertir a lista de MonthlyDataPoint
    result = []
    for month_idx, total in enumerate(monthly_totals):
        result.append(schemas.MonthlyDataPoint(
            month=month_idx + 1,
            month_name=MONTH_NAMES_ES[month_idx],
            total=total
        ))
    
    return result


@router.get("/currency-distribution", response_model=List[schemas.CurrencyDistribution])
async def get_currency_distribution(
    year: int = Query(..., description="Año a consultar"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Trimestre opcional"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la distribución de gastos por origen geográfico para pie chart
    
    Retorna:
    - ESP Nacional: Solo España peninsular + Baleares
    - UE: Canarias + resto UE (aunque sea EUR)
    - Divisas internacionales: USD, GBP, CHF, etc.
    """
    
    # Query tickets del año
    query = db.query(Ticket).join(Project).filter(
        Project.year == str(year)
    )
    
    # Filtrar por trimestre si aplica
    if quarter:
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3
        query = query.filter(
            func.substr(Ticket.date, 4, 2).cast(db.bind.dialect.NUMERIC).between(start_month, end_month)
        )
    
    tickets = query.all()
    
    # Calcular total general
    total_general = sum(ticket.final_total for ticket in tickets)
    
    if total_general == 0:
        return []
    
    # Agrupar por clasificación geográfica y divisa
    distribution = {}
    
    for ticket in tickets:
        geo = ticket.geo_classification or 'NACIONAL'
        currency = ticket.currency or 'EUR'
        
        # Crear clave única
        if geo == 'NACIONAL':
            key = 'ESP_NACIONAL'
            label = 'ESP Nacional'
            color = '#10b981'  # Verde
        elif geo == 'UE':
            key = f'UE_{currency}'
            label = f'UE ({currency})'
            color = '#3b82f6'  # Azul
        else:  # INTERNACIONAL
            key = f'INT_{currency}'
            label = currency
            color = '#f59e0b' if currency == 'USD' else '#8b5cf6'  # Amber para USD, morado resto
        
        if key not in distribution:
            distribution[key] = {
                'currency': currency,
                'label': label,
                'total': 0.0,
                'color': color
            }
        
        distribution[key]['total'] += ticket.final_total
    
    # Convertir a lista con porcentajes
    result = []
    for data in distribution.values():
        percentage = (data['total'] / total_general) * 100
        result.append(schemas.CurrencyDistribution(
            currency=data['currency'],
            label=data['label'],
            total=data['total'],
            percentage=round(percentage, 1),
            color=data['color']
        ))
    
    # Ordenar por total descendente
    result.sort(key=lambda x: x.total, reverse=True)
    
    return result


@router.get("/foreign-breakdown", response_model=List[schemas.CountryBreakdown])
async def get_foreign_breakdown(
    year: int = Query(..., description="Año a consultar"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Trimestre opcional"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el desglose detallado de gastos internacionales por país
    
    Incluye:
    - Lista de proyectos por país
    - Total gastado por país
    - IVA reclamable por país
    - Clasificación geográfica (UE / INTERNACIONAL)
    
    SOLO retorna países con gastos internacionales (excluye ESP peninsular+Baleares)
    """
    
    # Query tickets internacionales del año
    query = db.query(Ticket).join(Project).filter(
        Project.year == str(year),
        Ticket.is_foreign == True  # Solo internacionales
    )
    
    # Filtrar por trimestre si aplica
    if quarter:
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3
        query = query.filter(
            func.substr(Ticket.date, 4, 2).cast(db.bind.dialect.NUMERIC).between(start_month, end_month)
        )
    
    tickets = query.all()
    
    # Agrupar por país
    countries = {}
    
    for ticket in tickets:
        country_code = ticket.country_code or 'XX'
        
        if country_code not in countries:
            countries[country_code] = {
                'tickets': [],
                'projects': set(),  # Para evitar duplicados
                'total_spent': 0.0,
                'tax_paid_foreign': 0.0,
                'tax_reclamable_eur': 0.0,
                'currency': ticket.currency or 'EUR',
                'geo_classification': ticket.geo_classification or 'INTERNACIONAL'
            }
        
        countries[country_code]['tickets'].append(ticket)
        countries[country_code]['projects'].add(ticket.project_id)
        countries[country_code]['total_spent'] += ticket.final_total
        
        # Acumular IVA
        if ticket.foreign_tax_amount:
            countries[country_code]['tax_paid_foreign'] += ticket.foreign_tax_amount
        
        if ticket.foreign_tax_eur:
            countries[country_code]['tax_reclamable_eur'] += ticket.foreign_tax_eur
    
    # Convertir a lista de CountryBreakdown
    result = []
    
    for country_code, data in countries.items():
        # Obtener proyectos únicos con detalles
        project_ids = list(data['projects'])
        projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
        
        project_summaries = []
        for project in projects:
            # Calcular total del proyecto en esta divisa/país
            project_tickets = [t for t in data['tickets'] if t.project_id == project.id]
            project_foreign_total = sum(t.foreign_amount or 0.0 for t in project_tickets)
            
            # Crear lista de TicketSummary para este proyecto
            ticket_summaries = []
            for ticket in project_tickets:
                ticket_summaries.append(schemas.TicketSummary(
                    id=ticket.id,
                    date=ticket.date,
                    provider=ticket.provider,
                    invoice_number=ticket.invoice_number,
                    final_total=ticket.final_total,
                    foreign_amount=ticket.foreign_amount,
                    foreign_tax_eur=ticket.foreign_tax_eur,
                    currency=ticket.currency or 'EUR'
                ))
            
            project_summaries.append(schemas.ProjectSummary(
                id=project.id,
                creative_code=project.creative_code,
                description=project.description,
                total_amount=sum(t.final_total for t in project_tickets),
                foreign_amount=project_foreign_total if project_foreign_total > 0 else None,
                currency=data['currency'],
                tickets=ticket_summaries  # ← NUEVO: incluir tickets
            ))
        
        result.append(schemas.CountryBreakdown(
            country_code=country_code,
            country_name=get_country_name(country_code),
            geo_classification=data['geo_classification'],
            currency=data['currency'],
            total_spent=data['total_spent'],
            tax_paid_foreign=data['tax_paid_foreign'] if data['tax_paid_foreign'] > 0 else None,
            tax_reclamable_eur=data['tax_reclamable_eur'],
            projects_count=len(project_ids),
            projects=project_summaries
        ))
    
    # Ordenar por total gastado descendente
    result.sort(key=lambda x: x.total_spent, reverse=True)
    
    return result


@router.get("/complete", response_model=schemas.StatisticsResponse)
async def get_complete_statistics(
    year: int = Query(..., description="Año a consultar"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Trimestre opcional"),
    geo_filter: Optional[str] = Query(None, description="Filtro geográfico"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint completo que retorna todas las estadísticas en una sola llamada
    
    Útil para cargar la página de estadísticas de una vez
    """
    
    overview = await get_statistics_overview(year, quarter, geo_filter, db, current_user)
    monthly = await get_monthly_evolution(year, db, current_user)
    distribution = await get_currency_distribution(year, quarter, db, current_user)
    breakdown = await get_foreign_breakdown(year, quarter, db, current_user)
    
    return schemas.StatisticsResponse(
        overview=overview,
        monthly_evolution=monthly,
        currency_distribution=distribution,
        foreign_breakdown=breakdown
    )
