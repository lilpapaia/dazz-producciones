from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import datetime

from config.database import get_db
from app.models import schemas
from app.models.database import User, Project, Ticket, ProjectStatus, Company  # ← Company añadido
from app.services.auth import get_current_active_user
from app.services.geographic_classifier import classify_geography, get_country_name

router = APIRouter(prefix="/statistics", tags=["Statistics"])

MONTH_NAMES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

def filter_tickets_by_quarter(tickets: List[Ticket], quarter: int) -> List[Ticket]:
    """
    Filtra tickets por trimestre basándose en el campo date (formato DD/MM/YYYY)
    
    Args:
        tickets: Lista de tickets a filtrar
        quarter: Trimestre (1-4)
    
    Returns:
        Lista de tickets filtrados
    """
    start_month = (quarter - 1) * 3 + 1
    end_month = quarter * 3
    
    filtered = []
    for ticket in tickets:
        if not ticket.date or '/' not in ticket.date:
            continue
        
        try:
            # Parsear fecha DD/MM/YYYY
            parts = ticket.date.split('/')
            if len(parts) >= 2:
                month = int(parts[1])  # Mes está en la posición 1
                if start_month <= month <= end_month:
                    filtered.append(ticket)
        except (ValueError, IndexError):
            continue
    
    return filtered

@router.get("/available-years", response_model=List[int])
async def get_available_years(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la lista de años que tienen proyectos o tickets
    
    Retorna años ordenados de más reciente a más antiguo
    """
    # Obtener años únicos de proyectos
    years = db.query(Project.year).distinct().all()
    
    # Convertir a lista de enteros y ordenar descendente
    year_list = sorted([int(y[0]) for y in years if y[0]], reverse=True)
    
    return year_list

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
    
    # Base query para tickets del año (SIN geo_filter para calcular internacionales)
    all_tickets_query = db.query(Ticket).join(Project).filter(
        Project.year == str(year)
    )
    
    all_tickets = all_tickets_query.all()
    
    # Filtrar por trimestre si se especifica (en memoria, porque date es string DD/MM/YYYY)
    if quarter:
        all_tickets = filter_tickets_by_quarter(all_tickets, quarter)
    
    # Calcular gastos internacionales (UE + INTERNACIONAL) - SIEMPRE de todos los tickets
    international_tickets = [t for t in all_tickets if t.geo_classification in ['UE', 'INTERNACIONAL']]
    international_spent = sum(ticket.final_total for ticket in international_tickets)
    
    # IVA reclamable (solo tickets internacionales con foreign_tax_eur) - SIEMPRE de todos
    iva_reclamable = sum(
        ticket.foreign_tax_eur or 0.0 
        for ticket in international_tickets 
        if ticket.foreign_tax_eur
    )
    
    # AHORA SÍ aplicar geo_filter solo para total_spent
    if geo_filter:
        filtered_tickets = [t for t in all_tickets if t.geo_classification == geo_filter]
    else:
        filtered_tickets = all_tickets
    
    # Calcular total_spent con filtro geo aplicado
    total_spent = sum(ticket.final_total for ticket in filtered_tickets)
    
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
    
    tickets = query.all()
    
    # Filtrar por trimestre si aplica (en memoria)
    if quarter:
        tickets = filter_tickets_by_quarter(tickets, quarter)
    
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
    
    tickets = query.all()
    
    # Filtrar por trimestre si aplica (en memoria)
    if quarter:
        tickets = filter_tickets_by_quarter(tickets, quarter)
    
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
    company_id: Optional[int] = Query(None, description="ID de empresa para filtrar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint completo que retorna todas las estadísticas en una sola llamada
    
    PERMISOS: Solo ADMIN y BOSS
    
    Filtros:
    - year: Año obligatorio
    - quarter: Trimestre opcional
    - geo_filter: Filtro geográfico opcional
    - company_id: Filtrar por empresa (obligatorio para BOSS, opcional para ADMIN)
    
    MODOS:
    - ADMIN sin company_id: Retorna vista "TODAS LAS EMPRESAS" con desglose
    - ADMIN con company_id: Retorna vista de empresa específica
    - BOSS: Auto-filtra por su empresa (ignora company_id si se pasa)
    """
    
    # ===== VALIDACIÓN DE PERMISOS =====
    if current_user.role not in ["ADMIN", "BOSS"]:
        raise HTTPException(
            status_code=403,
            detail="Solo ADMIN y BOSS pueden ver estadísticas"
        )
    
    # ===== BOSS: AUTO-FORZAR SU EMPRESA =====
    if current_user.role == "BOSS":
        # Obtener empresa del BOSS
        user_company_ids = [uc.id for uc in current_user.companies]
        if not user_company_ids:
            raise HTTPException(
                status_code=400,
                detail="Usuario BOSS sin empresas asignadas"
            )
        company_id = user_company_ids[0]  # Primera empresa
    
    # ===== ADMIN SIN COMPANY_ID: VISTA "TODAS" =====
    if current_user.role == "ADMIN" and company_id is None:
        return await get_all_companies_statistics(year, quarter, geo_filter, db, current_user)
    
    # ===== ADMIN O BOSS CON COMPANY_ID: VISTA EMPRESA ESPECÍFICA =====
    return await get_single_company_statistics(year, quarter, geo_filter, company_id, db, current_user)


async def get_all_companies_statistics(
    year: int,
    quarter: Optional[int],
    geo_filter: Optional[str],
    db: Session,
    current_user: User
):
    """
    Vista "TODAS LAS EMPRESAS" para ADMIN
    
    Retorna:
    - Cards resumen por empresa
    - Overview global
    - Foreign breakdown agrupado por empresa dentro de cada país
    """
    from app.models.database import Company
    
    # Obtener todas las empresas
    companies = db.query(Company).all()
    
    # Calcular stats por empresa
    companies_stats = []
    total_global = 0.0
    iva_global = 0.0
    
    for company in companies:
        # Obtener proyectos de esta empresa
        projects = db.query(Project).filter(
            Project.owner_company_id == company.id,
            Project.year == str(year)
        ).all()
        
        project_ids = [p.id for p in projects]
        
        if not project_ids:
            # Empresa sin proyectos este año
            companies_stats.append({
                "company_id": company.id,
                "company_name": company.name,
                "cif": company.cif,
                "total_spent": 0.0,
                "iva_reclamable": 0.0,
                "projects_count": 0
            })
            continue
        
        # Obtener tickets de estos proyectos
        tickets = db.query(Ticket).filter(Ticket.project_id.in_(project_ids)).all()
        
        # Filtrar por trimestre si aplica
        if quarter:
            tickets = filter_tickets_by_quarter(tickets, quarter)
        
        # Calcular totales
        total_spent = sum(t.final_total for t in tickets)
        international_tickets = [t for t in tickets if t.geo_classification in ['UE', 'INTERNACIONAL']]
        iva_reclamable = sum(t.foreign_tax_eur or 0.0 for t in international_tickets if t.foreign_tax_eur)
        
        companies_stats.append({
            "company_id": company.id,
            "company_name": company.name,
            "cif": company.cif,
            "total_spent": total_spent,
            "iva_reclamable": iva_reclamable,
            "projects_count": len(projects)
        })
        
        total_global += total_spent
        iva_global += iva_reclamable
    
    # Overview global
    overview = schemas.StatisticsOverview(
        total_spent=total_global,
        international_spent=sum(c["iva_reclamable"] for c in companies_stats),  # Aproximación
        iva_reclamable=iva_global,
        projects_total=sum(c["projects_count"] for c in companies_stats),
        projects_closed=0,  # Calcular si necesario
        projects_open=0
    )
    
    # Foreign breakdown agrupado por empresa
    breakdown = await get_foreign_breakdown_all_companies(year, quarter, geo_filter, db)
    
    # Calcular monthly_evolution y currency_distribution para TODAS las empresas
    all_projects = db.query(Project).filter(Project.year == str(year)).all()
    all_project_ids = [p.id for p in all_projects] if all_projects else []
    
    monthly = await get_monthly_evolution_filtered(year, all_project_ids, geo_filter, db, current_user)
    distribution = await get_currency_distribution_filtered(year, quarter, all_project_ids, db, current_user)
    
    # Retornar con modo "all_companies"
    return {
        "mode": "all_companies",
        "overview": overview,
        "companies": companies_stats,
        "monthly_evolution": monthly,
        "currency_distribution": distribution,
        "foreign_breakdown": breakdown
    }


async def get_single_company_statistics(
    year: int,
    quarter: Optional[int],
    geo_filter: Optional[str],
    company_id: int,
    db: Session,
    current_user: User
):
    """
    Vista de empresa específica (ADMIN o BOSS)
    
    Retorna stats normales pero filtradas por empresa
    """
    from app.models.database import Company
    
    # Verificar que la empresa existe
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Filtrar proyectos por empresa
    projects = db.query(Project).filter(
        Project.owner_company_id == company_id,
        Project.year == str(year)
    ).all()
    
    project_ids = [p.id for p in projects] if projects else []
    
    # Calcular overview
    overview = await get_statistics_overview_filtered(year, quarter, geo_filter, project_ids, db, current_user)
    monthly = await get_monthly_evolution_filtered(year, project_ids, geo_filter, db, current_user)    
    distribution = await get_currency_distribution_filtered(year, quarter, project_ids, db, current_user)
    breakdown = await get_foreign_breakdown_filtered(year, quarter, project_ids, db, current_user)
    
    return {
        "mode": "single_company",
        "company": {
            "company_id": company.id,
            "company_name": company.name,
            "cif": company.cif
        },
        "overview": overview,
        "monthly_evolution": monthly,
        "currency_distribution": distribution,
        "foreign_breakdown": breakdown
    }


async def get_foreign_breakdown_all_companies(
    year: int,
    quarter: Optional[int],
    geo_filter: Optional[str],
    db: Session
):
    """
    Foreign breakdown agrupado por empresa para vista "TODAS"
    
    Estructura: País → Empresa → Proyectos
    """
    from app.models.database import Company
    
    # Query tickets internacionales del año
    query = db.query(Ticket).join(Project).filter(
        Project.year == str(year),
        Ticket.is_foreign == True
    )
    
    # Aplicar filtro geo si existe
    if geo_filter:
        query = query.filter(Ticket.geo_classification == geo_filter)
    
    tickets = query.all()
    
    # Filtrar por trimestre si aplica
    if quarter:
        tickets = filter_tickets_by_quarter(tickets, quarter)
    
    # Agrupar por país y empresa
    countries = {}
    
    for ticket in tickets:
        country_code = ticket.country_code or 'XX'
        company_id = ticket.project.owner_company_id if ticket.project else None
        
        if not company_id:
            continue
        
        # Inicializar país si no existe
        if country_code not in countries:
            countries[country_code] = {
                'country_code': country_code,
                'country_name': get_country_name(country_code),
                'geo_classification': ticket.geo_classification or 'INTERNACIONAL',
                'currency': ticket.currency or 'EUR',
                'total_spent': 0.0,
                'tax_reclamable_eur': 0.0,
                'companies': {}
            }
        
        # Inicializar empresa dentro del país si no existe
        if company_id not in countries[country_code]['companies']:
            company = db.query(Company).filter(Company.id == company_id).first()
            countries[country_code]['companies'][company_id] = {
                'company_id': company_id,
                'company_name': company.name if company else "Sin empresa",
                'projects': {},
                'total_spent': 0.0
            }
        
        # Inicializar proyecto si no existe
        project_id = ticket.project_id
        if project_id not in countries[country_code]['companies'][company_id]['projects']:
            countries[country_code]['companies'][company_id]['projects'][project_id] = {
                'id': ticket.project.id,
                'creative_code': ticket.project.creative_code,
                'description': ticket.project.description,
                'tickets': [],
                'total_amount': 0.0,
                'foreign_amount': 0.0
            }
        
        # Añadir ticket al proyecto
        project_data = countries[country_code]['companies'][company_id]['projects'][project_id]
        project_data['tickets'].append({
            'id': ticket.id,
            'date': ticket.date,
            'provider': ticket.provider,
            'invoice_number': ticket.invoice_number,
            'final_total': ticket.final_total,
            'foreign_amount': ticket.foreign_amount,
            'foreign_tax_eur': ticket.foreign_tax_eur,
            'currency': ticket.currency or 'EUR'
        })
        project_data['total_amount'] += ticket.final_total
        project_data['foreign_amount'] += ticket.foreign_amount or 0.0
        
        # Acumular totales
        countries[country_code]['total_spent'] += ticket.final_total
        countries[country_code]['tax_reclamable_eur'] += ticket.foreign_tax_eur or 0.0
        countries[country_code]['companies'][company_id]['total_spent'] += ticket.final_total
    
    # Convertir a lista y formatear
    result = []
    for country_data in countries.values():
        companies_list = []
        for company_data in country_data['companies'].values():
            projects_list = [
                {
                    'id': p['id'],
                    'creative_code': p['creative_code'],
                    'description': p['description'],
                    'total_amount': p['total_amount'],
                    'foreign_amount': p['foreign_amount'] if p['foreign_amount'] > 0 else None,
                    'currency': country_data['currency'],
                    'tickets': p['tickets']
                }
                for p in company_data['projects'].values()
            ]
            
            companies_list.append({
                'company_id': company_data['company_id'],
                'company_name': company_data['company_name'],
                'projects': projects_list
            })
        
        result.append({
            'country_code': country_data['country_code'],
            'country_name': country_data['country_name'],
            'geo_classification': country_data['geo_classification'],
            'currency': country_data['currency'],
            'total_spent': country_data['total_spent'],
            'tax_reclamable_eur': country_data['tax_reclamable_eur'],
            'projects_count': sum(len(c['projects']) for c in companies_list),
            'projects': [],  # ← Vacío cuando hay companies (para schema Pydantic)
            'companies': companies_list  # ← NUEVO: Agrupado por empresa
        })
    
    # Ordenar por total gastado
    result.sort(key=lambda x: x['total_spent'], reverse=True)
    
    return result


# Funciones auxiliares filtradas (simplificadas)
async def get_statistics_overview_filtered(year, quarter, geo_filter, project_ids, db, current_user):
    tickets = db.query(Ticket).filter(Ticket.project_id.in_(project_ids)).all() if project_ids else []
    if quarter:
        tickets = filter_tickets_by_quarter(tickets, quarter)
    
    international_tickets = [t for t in tickets if t.geo_classification in ['UE', 'INTERNACIONAL']]
    
    return schemas.StatisticsOverview(
        total_spent=sum(t.final_total for t in tickets),
        international_spent=sum(t.final_total for t in international_tickets),
        iva_reclamable=sum(t.foreign_tax_eur or 0.0 for t in international_tickets if t.foreign_tax_eur),
        projects_total=len(project_ids),
        projects_closed=0,
        projects_open=len(project_ids)
    )

async def get_monthly_evolution_filtered(year, project_ids, geo_filter, db, current_user):
    """Evolución mensual filtrada por proyectos y geo"""
    if not project_ids:
        return []
    
    # Query tickets de los proyectos filtrados
    tickets_query = db.query(Ticket).filter(Ticket.project_id.in_(project_ids))
    
    # Aplicar filtro geo si existe
    if geo_filter:
        tickets_query = tickets_query.filter(Ticket.geo_classification == geo_filter)
    
    tickets = tickets_query.all()
    
    # Inicializar array con 12 meses en 0
    monthly_totals = [0.0] * 12
    
    # Sumar gastos por mes
    for ticket in tickets:
        try:
            if ticket.date and "/" in ticket.date:
                parts = ticket.date.split("/")
                if len(parts) >= 2:
                    month = int(parts[1]) - 1  # 0-indexed
                    if 0 <= month < 12:
                        monthly_totals[month] += ticket.final_total
        except:
            continue
    
    # Convertir a lista de MonthlyDataPoint
    MONTH_NAMES_ES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    
    result = []
    for month_idx, total in enumerate(monthly_totals):
        result.append(schemas.MonthlyDataPoint(
            month=month_idx + 1,
            month_name=MONTH_NAMES_ES[month_idx],
            total=total
        ))
    
    return result

async def get_currency_distribution_filtered(year, quarter, project_ids, db, current_user):
    """Distribución por divisa filtrada por proyectos"""
    if not project_ids:
        return []
    
    # Query tickets de los proyectos filtrados
    tickets = db.query(Ticket).filter(Ticket.project_id.in_(project_ids)).all()
    
    # Filtrar por trimestre si aplica
    if quarter:
        tickets = filter_tickets_by_quarter(tickets, quarter)
    
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

async def get_foreign_breakdown_filtered(year, quarter, project_ids, db, current_user):
    if not project_ids:
        return []
    
    tickets = db.query(Ticket).filter(
        Ticket.project_id.in_(project_ids),
        Ticket.is_foreign == True
    ).all()
    
    if quarter:
        tickets = filter_tickets_by_quarter(tickets, quarter)
    
    # Agrupar por país (sin agrupar por empresa)
    countries = {}
    for ticket in tickets:
        country_code = ticket.country_code or 'XX'
        if country_code not in countries:
            countries[country_code] = {
                'tickets': [],
                'projects': set(),
                'total_spent': 0.0,
                'tax_reclamable_eur': 0.0,
                'currency': ticket.currency or 'EUR',
                'geo_classification': ticket.geo_classification or 'INTERNACIONAL'
            }
        
        countries[country_code]['tickets'].append(ticket)
        countries[country_code]['projects'].add(ticket.project_id)
        countries[country_code]['total_spent'] += ticket.final_total
        countries[country_code]['tax_reclamable_eur'] += ticket.foreign_tax_eur or 0.0
    
    # Convertir a formato de respuesta
    result = []
    for country_code, data in countries.items():
        project_ids_list = list(data['projects'])
        projects = db.query(Project).filter(Project.id.in_(project_ids_list)).all()
        
        project_summaries = []
        for project in projects:
            project_tickets = [t for t in data['tickets'] if t.project_id == project.id]
            ticket_summaries = [
                schemas.TicketSummary(
                    id=t.id,
                    date=t.date,
                    provider=t.provider,
                    invoice_number=t.invoice_number,
                    final_total=t.final_total,
                    foreign_amount=t.foreign_amount,
                    foreign_tax_eur=t.foreign_tax_eur,
                    currency=t.currency or 'EUR'
                )
                for t in project_tickets
            ]
            
            project_summaries.append(schemas.ProjectSummary(
                id=project.id,
                creative_code=project.creative_code,
                description=project.description,
                total_amount=sum(t.final_total for t in project_tickets),
                foreign_amount=sum(t.foreign_amount or 0.0 for t in project_tickets),
                currency=data['currency'],
                tickets=ticket_summaries
            ))
        
        result.append(schemas.CountryBreakdown(
            country_code=country_code,
            country_name=get_country_name(country_code),
            geo_classification=data['geo_classification'],
            currency=data['currency'],
            total_spent=data['total_spent'],
            tax_paid_foreign=None,
            tax_reclamable_eur=data['tax_reclamable_eur'],
            projects_count=len(project_ids_list),
            projects=project_summaries
        ))
    
    result.sort(key=lambda x: x.total_spent, reverse=True)
    return result
