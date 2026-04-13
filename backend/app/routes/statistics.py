from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from config.database import get_db
from app.models import schemas
from app.models.database import User, Project, Ticket, ProjectStatus, Company, UserRole
from app.services.auth import get_current_active_user
from app.services.permissions import get_user_company_ids
from app.services.geographic_classifier import classify_geography, get_country_name

router = APIRouter(prefix="/statistics", tags=["Statistics"])


# VULN-007: Dependencia que verifica que el usuario es ADMIN o BOSS
async def get_current_admin_or_boss(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Solo ADMIN y BOSS pueden ver estadísticas"""
    if current_user.role not in [UserRole.ADMIN, UserRole.BOSS]:
        raise HTTPException(status_code=403, detail="Solo ADMIN y BOSS pueden ver estadísticas")
    return current_user

MONTH_NAMES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def filter_tickets_by_quarter(tickets: List, quarter: int) -> List:
    """Filtra tickets por trimestre basándose en el campo date (formato DD/MM/YYYY)"""
    start_month = (quarter - 1) * 3 + 1
    end_month = quarter * 3
    
    filtered = []
    for ticket in tickets:
        if not ticket.date or '/' not in ticket.date:
            continue
        try:
            parts = ticket.date.split('/')
            if len(parts) >= 2:
                month = int(parts[1])
                if start_month <= month <= end_month:
                    filtered.append(ticket)
        except (ValueError, IndexError):
            continue
    return filtered


# ============================================================
# ENDPOINTS INDIVIDUALES (mantener compatibilidad)
# ============================================================

@router.get("/available-years", response_model=List[int])
async def get_available_years(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_boss)
):
    """Obtiene la lista de años que tienen proyectos"""
    years = db.query(Project.year).distinct().all()
    year_list = sorted([int(y[0]) for y in years if y[0]], reverse=True)
    return year_list


@router.get("/overview", response_model=schemas.StatisticsOverview)
async def get_statistics_overview(
    year: int = Query(..., ge=2000, le=2100),
    quarter: Optional[int] = Query(None, ge=1, le=4),
    geo_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_boss)
):
    # BOSS filter: restrict to their companies (same as /complete and other endpoints)
    boss_cids = None
    if current_user.role == UserRole.BOSS:
        boss_cids = get_user_company_ids(current_user, db)

    # PERF-M6: Cuando no hay quarter, calcular sumas en SQL directo
    # Con quarter, necesitamos parsear date strings en Python (campo date es String, no Date)
    if quarter:
        q = db.query(Ticket).join(Project).filter(Project.year == str(year), Ticket.is_suplido != True)
        if boss_cids:
            q = q.filter(Project.owner_company_id.in_(boss_cids))
        all_tickets = q.all()
        all_tickets = filter_tickets_by_quarter(all_tickets, quarter)
        intl = [t for t in all_tickets if t.geo_classification in ['UE', 'INTERNACIONAL']]
        international_spent = sum(t.final_total for t in intl)
        iva_reclamable = sum(t.foreign_tax_eur or 0.0 for t in intl if t.foreign_tax_eur)
        filtered = [t for t in all_tickets if t.geo_classification == geo_filter] if geo_filter else all_tickets
        total_spent = sum(t.final_total for t in filtered)
    else:
        boss_extra = [Project.owner_company_id.in_(boss_cids)] if boss_cids else []
        geo_extra = [Ticket.geo_classification == geo_filter] if geo_filter else []
        suplido_filter = [Ticket.is_suplido != True]
        total_spent = float(db.query(func.coalesce(func.sum(Ticket.final_total), 0.0)).join(Project).filter(
            Project.year == str(year), *geo_extra, *boss_extra, *suplido_filter).scalar())
        intl_filter = [Project.year == str(year), Ticket.geo_classification.in_(['UE', 'INTERNACIONAL']), *boss_extra, *suplido_filter]
        international_spent = float(db.query(func.coalesce(func.sum(Ticket.final_total), 0.0)).join(Project).filter(
            *intl_filter).scalar())
        iva_reclamable = float(db.query(func.coalesce(func.sum(Ticket.foreign_tax_eur), 0.0)).join(Project).filter(
            *intl_filter).scalar())

    projects_query = db.query(Project).filter(Project.year == str(year))
    if boss_cids:
        projects_query = projects_query.filter(Project.owner_company_id.in_(boss_cids))
    projects_total = projects_query.count()
    projects_closed = projects_query.filter(Project.status == ProjectStatus.CERRADO).count()

    return schemas.StatisticsOverview(
        total_spent=round(total_spent, 2),
        international_spent=round(international_spent, 2),
        iva_reclamable=round(iva_reclamable, 2),
        projects_total=projects_total,
        projects_closed=projects_closed,
        projects_open=projects_total - projects_closed
    )


@router.get("/monthly-evolution", response_model=List[schemas.MonthlyDataPoint])
async def get_monthly_evolution(
    year: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_boss)
):
    query = db.query(Ticket).join(Project).filter(Project.year == str(year), Ticket.is_suplido != True)
    if current_user.role == UserRole.BOSS:
        boss_cids = get_user_company_ids(current_user, db)
        query = query.filter(Project.owner_company_id.in_(boss_cids))
    tickets = query.all()
    monthly_totals = [0.0] * 12

    for ticket in tickets:
        try:
            if ticket.date and "/" in ticket.date:
                parts = ticket.date.split("/")
                if len(parts) >= 2:
                    month = int(parts[1]) - 1
                    if 0 <= month < 12:
                        monthly_totals[month] += ticket.final_total
        except (ValueError, IndexError):
            continue
    
    return [
        schemas.MonthlyDataPoint(month=i+1, month_name=MONTH_NAMES_ES[i], total=monthly_totals[i])
        for i in range(12)
    ]


@router.get("/currency-distribution", response_model=List[schemas.CurrencyDistribution])
async def get_currency_distribution(
    year: int = Query(..., ge=2000, le=2100),
    quarter: Optional[int] = Query(None, ge=1, le=4),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_boss)
):
    query = db.query(Ticket).join(Project).filter(Project.year == str(year), Ticket.is_suplido != True)
    if current_user.role == UserRole.BOSS:
        boss_cids = get_user_company_ids(current_user, db)
        query = query.filter(Project.owner_company_id.in_(boss_cids))
    tickets = query.all()
    if quarter:
        tickets = filter_tickets_by_quarter(tickets, quarter)
    return _calc_distribution_from_tickets(tickets)


@router.get("/foreign-breakdown", response_model=List[schemas.CountryBreakdown])
async def get_foreign_breakdown(
    year: int = Query(..., ge=2000, le=2100),
    quarter: Optional[int] = Query(None, ge=1, le=4),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_boss)
):
    query = db.query(Ticket).join(Project).filter(
        Project.year == str(year),
        Ticket.is_foreign == True,
        Ticket.is_suplido != True,
    )
    if current_user.role == UserRole.BOSS:
        boss_cids = get_user_company_ids(current_user, db)
        query = query.filter(Project.owner_company_id.in_(boss_cids))
    tickets = query.all()
    if quarter:
        tickets = filter_tickets_by_quarter(tickets, quarter)
    return _build_breakdown_single(tickets, db)


# ============================================================
# ENDPOINT COMPLETO - LÓGICA PRINCIPAL
# ============================================================

@router.get("/complete")
async def get_complete_statistics(
    year: int = Query(..., ge=2000, le=2100, description="Año a consultar"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Trimestre (1-4)"),
    geo_filter: Optional[str] = Query(None, description="NACIONAL | UE | INTERNACIONAL"),
    company_id: Optional[int] = Query(None, description="ID empresa (solo ADMIN)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint principal de estadísticas.

    Filtros y su efecto:
    - year + company_id → afectan a TODO (cards, gráficos, breakdown)
    - geo_filter        → solo afecta al gráfico de evolución mensual
    - quarter           → afecta al gráfico de distribución y al breakdown

    Modos:
    - ADMIN sin company_id  → "all_companies": breakdown agrupa País → Empresa → Proyectos
    - ADMIN con company_id  → "single_company": breakdown agrupa País → Proyectos
    - BOSS                  → "single_company" forzado a su empresa
    - WORKER                → 403
    """

    # ── Permisos ──────────────────────────────────────────────
    if current_user.role not in [UserRole.ADMIN, UserRole.BOSS]:
        raise HTTPException(status_code=403, detail="Solo ADMIN y BOSS pueden ver estadísticas")

    # ── BOSS: validar company_id o usar todas sus empresas ─────
    boss_company_ids = None
    if current_user.role == UserRole.BOSS:
        boss_company_ids = get_user_company_ids(current_user, db)
        if not boss_company_ids:
            raise HTTPException(status_code=400, detail="Usuario BOSS sin empresas asignadas")
        # Si envía company_id, validar que es suya
        if company_id and company_id not in boss_company_ids:
            raise HTTPException(status_code=403, detail="No tienes acceso a esa empresa")

    # ── Obtener proyectos del año (+ empresa si aplica) ────────
    projects_query = db.query(Project).filter(Project.year == str(year))
    if company_id:
        # ADMIN con empresa específica o BOSS con empresa específica
        projects_query = projects_query.filter(Project.owner_company_id == company_id)
    elif boss_company_ids:
        # BOSS sin company_id → todas sus empresas
        projects_query = projects_query.filter(Project.owner_company_id.in_(boss_company_ids))
    projects = projects_query.all()
    project_ids = [p.id for p in projects]

    # ── Calcular cada componente con su filtro correcto ────────

    # 1. CARDS: year + company → sin quarter, sin geo_filter
    overview = _calc_overview(project_ids, db)

    # 2. EVOLUCIÓN MENSUAL: year + company + geo_filter → sin quarter
    monthly = _calc_monthly(project_ids, geo_filter, db)

    # 3. PIE DISTRIBUCIÓN: year + company + quarter (NO geo_filter — representa distribución global)
    distribution = _calc_distribution(project_ids, quarter, None, db)

    # 4. BREAKDOWN INTERNACIONAL: year + company + quarter
    # Modo multi-empresa: ADMIN sin filtro o BOSS sin filtro (ve todas sus empresas)
    is_multi_company = company_id is None and (
        current_user.role == UserRole.ADMIN or
        (current_user.role == UserRole.BOSS and boss_company_ids and len(boss_company_ids) > 1)
    )

    if is_multi_company:
        breakdown = _get_breakdown_all_companies(year, quarter, db, boss_company_ids)
        mode = "all_companies"
    else:
        # Tickets internacionales de los proyectos filtrados
        intl_tickets = db.query(Ticket).filter(
            Ticket.project_id.in_(project_ids),
            Ticket.is_foreign == True,
            Ticket.is_suplido != True,
        ).all() if project_ids else []
        if quarter:
            intl_tickets = filter_tickets_by_quarter(intl_tickets, quarter)
        breakdown = _build_breakdown_single(intl_tickets, db)
        mode = "single_company"

    # ── Respuesta ──────────────────────────────────────────────
    response = {
        "mode": mode,
        "overview": overview,
        "monthly_evolution": monthly,
        "currency_distribution": distribution,
        "foreign_breakdown": breakdown,
    }

    if mode == "single_company" and company_id:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            response["company"] = {
                "company_id": company.id,
                "company_name": company.name,
                "cif": company.cif
            }

    return response


# ============================================================
# HELPERS INTERNOS
# ============================================================

def _calc_overview(project_ids: list, db: Session) -> schemas.StatisticsOverview:
    """Cards resumen: year + company únicamente (sin quarter ni geo_filter)"""
    if not project_ids:
        return schemas.StatisticsOverview(
            total_spent=0.0, international_spent=0.0, iva_reclamable=0.0,
            projects_total=0, projects_closed=0, projects_open=0
        )

    # PERF-M6: Sumas calculadas en SQL en vez de cargar todos los tickets en Python
    # BUG-69: Exclude suplido tickets from all statistics
    suplido_filter = Ticket.is_suplido != True
    total_spent = db.query(
        func.coalesce(func.sum(Ticket.final_total), 0.0)
    ).filter(Ticket.project_id.in_(project_ids), suplido_filter).scalar()

    intl_filter = [
        Ticket.project_id.in_(project_ids),
        Ticket.geo_classification.in_(['UE', 'INTERNACIONAL']),
        suplido_filter,
    ]
    international_spent = db.query(
        func.coalesce(func.sum(Ticket.final_total), 0.0)
    ).filter(*intl_filter).scalar()

    iva_reclamable = db.query(
        func.coalesce(func.sum(Ticket.foreign_tax_eur), 0.0)
    ).filter(*intl_filter).scalar()

    closed = db.query(func.count(Project.id)).filter(
        Project.id.in_(project_ids),
        Project.status == ProjectStatus.CERRADO
    ).scalar()
    total = len(project_ids)

    return schemas.StatisticsOverview(
        total_spent=round(float(total_spent), 2),
        international_spent=round(float(international_spent), 2),
        iva_reclamable=round(float(iva_reclamable), 2),
        projects_total=total,
        projects_closed=closed,
        projects_open=total - closed
    )


def _calc_monthly(project_ids: list, geo_filter: Optional[str], db: Session) -> list:
    """Evolución mensual: year + company + geo_filter (sin quarter, siempre 12 meses)

    PERF-H1: Esta función (y _calc_distribution, _build_breakdown_single, _get_breakdown_all_companies)
    cargan tickets en memoria porque necesitan parsear Ticket.date (String DD/MM/YYYY) para agrupar
    por mes/trimestre. Migrar a SQL requeriría convertir la columna date a tipo Date — cambio de
    esquema mayor. Con <500 tickets/año el overhead es aceptable.
    """
    empty = [
        schemas.MonthlyDataPoint(month=i+1, month_name=MONTH_NAMES_ES[i], total=0.0)
        for i in range(12)
    ]
    if not project_ids:
        return empty

    q = db.query(Ticket).filter(Ticket.project_id.in_(project_ids), Ticket.is_suplido != True)
    if geo_filter:
        q = q.filter(Ticket.geo_classification == geo_filter)
    tickets = q.all()

    monthly_totals = [0.0] * 12
    for ticket in tickets:
        if ticket.date and '/' in ticket.date:
            try:
                parts = ticket.date.split('/')
                if len(parts) >= 2:
                    month = int(parts[1]) - 1
                    if 0 <= month < 12:
                        monthly_totals[month] += ticket.final_total
            except (ValueError, IndexError):
                continue

    return [
        schemas.MonthlyDataPoint(month=i+1, month_name=MONTH_NAMES_ES[i], total=round(monthly_totals[i], 2))
        for i in range(12)
    ]


def _calc_distribution(project_ids: list, quarter: Optional[int], geo_filter: Optional[str], db: Session) -> list:
    """Distribución por origen: year + company + quarter + geo_filter"""
    if not project_ids:
        return []

    tickets = db.query(Ticket).filter(Ticket.project_id.in_(project_ids), Ticket.is_suplido != True).all()
    if quarter:
        tickets = filter_tickets_by_quarter(tickets, quarter)
    if geo_filter:
        tickets = [t for t in tickets if t.geo_classification == geo_filter]

    return _calc_distribution_from_tickets(tickets)


def _calc_distribution_from_tickets(tickets: list) -> list:
    """Convierte lista de tickets a CurrencyDistribution"""
    total_general = sum(t.final_total for t in tickets)
    if total_general == 0:
        return []

    distribution = {}
    for ticket in tickets:
        geo = ticket.geo_classification or 'NACIONAL'
        currency = ticket.currency or 'EUR'

        if geo == 'NACIONAL':
            key = 'ESP_NACIONAL'
            label = 'ESP Nacional'
            color = '#10b981'
        elif geo == 'UE':
            key = f'UE_{currency}'
            label = f'UE ({currency})'
            color = '#3b82f6'
        else:
            key = f'INT_{currency}'
            label = currency
            color = '#f59e0b' if currency == 'USD' else '#8b5cf6'

        if key not in distribution:
            distribution[key] = {'currency': currency, 'label': label, 'total': 0.0, 'color': color}
        distribution[key]['total'] += ticket.final_total

    result = []
    for data in distribution.values():
        result.append(schemas.CurrencyDistribution(
            currency=data['currency'],
            label=data['label'],
            total=round(data['total'], 2),
            percentage=round((data['total'] / total_general) * 100, 1),
            color=data['color']
        ))

    result.sort(key=lambda x: x.total, reverse=True)
    return result


def _build_breakdown_single(tickets: list, db: Session) -> list:
    """
    Breakdown para empresa específica o BOSS.
    Estructura: País → Proyectos (con tickets)
    """
    countries: dict = {}

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

    # Pre-fetch TODOS los projects en 1 sola query (evita N+1 por país)
    all_project_ids = set()
    for data in countries.values():
        all_project_ids.update(data['projects'])
    all_projects = db.query(Project).filter(Project.id.in_(list(all_project_ids))).all() if all_project_ids else []
    projects_map = {p.id: p for p in all_projects}

    result = []
    for country_code, data in countries.items():
        project_ids_list = list(data['projects'])
        projects = [projects_map[pid] for pid in project_ids_list if pid in projects_map]

        project_summaries = []
        for project in projects:
            proj_tickets = [t for t in data['tickets'] if t.project_id == project.id]
            ticket_summaries = [
                schemas.TicketSummary(
                    id=t.id, date=t.date, provider=t.provider,
                    invoice_number=t.invoice_number, final_total=t.final_total,
                    foreign_amount=t.foreign_amount, foreign_tax_eur=t.foreign_tax_eur,
                    currency=t.currency or 'EUR'
                )
                for t in proj_tickets
            ]
            foreign_total = sum(t.foreign_amount or 0.0 for t in proj_tickets)
            project_summaries.append(schemas.ProjectSummary(
                id=project.id,
                creative_code=project.creative_code,
                description=project.description,
                total_amount=round(sum(t.final_total for t in proj_tickets), 2),
                foreign_amount=round(foreign_total, 2) if foreign_total > 0 else None,
                currency=data['currency'],
                tickets=ticket_summaries
            ))

        result.append(schemas.CountryBreakdown(
            country_code=country_code,
            country_name=get_country_name(country_code),
            geo_classification=data['geo_classification'],
            currency=data['currency'],
            total_spent=round(data['total_spent'], 2),
            tax_paid_foreign=None,
            tax_reclamable_eur=round(data['tax_reclamable_eur'], 2),
            projects_count=len(project_ids_list),
            projects=project_summaries,
            companies=None
        ))

    result.sort(key=lambda x: x.total_spent, reverse=True)
    return result


def _get_breakdown_all_companies(year: int, quarter: Optional[int], db: Session, company_ids: Optional[list] = None) -> list:
    """
    Breakdown para modo multi-empresa (ADMIN todas o BOSS sus empresas).
    Estructura: País → Empresa → Proyectos (con tickets)

    Usa joinedload para evitar N+1 queries con ticket.project
    """
    query = (
        db.query(Ticket)
        .join(Project)
        .options(joinedload(Ticket.project))
        .filter(
            Project.year == str(year),
            Ticket.is_foreign == True,
            Ticket.is_suplido != True,
        )
    )
    if company_ids:
        query = query.filter(Project.owner_company_id.in_(company_ids))
    tickets = query.all()

    if quarter:
        tickets = filter_tickets_by_quarter(tickets, quarter)

    # Pre-fetch TODAS las companies en 1 sola query (evita N+1 por empresa)
    all_company_ids = set()
    for ticket in tickets:
        if ticket.project and ticket.project.owner_company_id:
            all_company_ids.add(ticket.project.owner_company_id)
    companies_list = db.query(Company).filter(Company.id.in_(list(all_company_ids))).all() if all_company_ids else []
    company_cache = {c.id: c.name for c in companies_list}

    countries: dict = {}

    for ticket in tickets:
        if not ticket.project:
            continue

        country_code = ticket.country_code or 'XX'
        comp_id = ticket.project.owner_company_id
        if not comp_id:
            continue  # Tickets sin empresa asignada se ignoran en modo TODAS

        # Inicializar país
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

        # Inicializar empresa dentro del país
        if comp_id not in countries[country_code]['companies']:
            countries[country_code]['companies'][comp_id] = {
                'company_id': comp_id,
                'company_name': company_cache.get(comp_id, 'Sin empresa'),
                'projects': {}
            }

        # Inicializar proyecto
        project_id = ticket.project_id
        comp_projects = countries[country_code]['companies'][comp_id]['projects']
        if project_id not in comp_projects:
            comp_projects[project_id] = {
                'id': project_id,
                'creative_code': ticket.project.creative_code,
                'description': ticket.project.description,
                'tickets': [],
                'total_amount': 0.0,
                'foreign_amount': 0.0,
                'currency': ticket.currency or 'EUR'
            }

        # Añadir ticket
        proj_data = comp_projects[project_id]
        proj_data['tickets'].append({
            'id': ticket.id,
            'date': ticket.date,
            'provider': ticket.provider,
            'invoice_number': ticket.invoice_number,
            'final_total': ticket.final_total,
            'foreign_amount': ticket.foreign_amount,
            'foreign_tax_eur': ticket.foreign_tax_eur,
            'currency': ticket.currency or 'EUR'
        })
        proj_data['total_amount'] += ticket.final_total
        proj_data['foreign_amount'] += ticket.foreign_amount or 0.0

        # Acumular totales
        countries[country_code]['total_spent'] += ticket.final_total
        countries[country_code]['tax_reclamable_eur'] += ticket.foreign_tax_eur or 0.0

    # Convertir a formato de respuesta (dicts planos, no Pydantic — el endpoint /complete devuelve dict)
    result = []
    for country_data in countries.values():
        companies_list = []
        for comp_data in country_data['companies'].values():
            projects_list = [
                {
                    'id': p['id'],
                    'creative_code': p['creative_code'],
                    'description': p['description'],
                    'total_amount': round(p['total_amount'], 2),
                    'foreign_amount': round(p['foreign_amount'], 2) if p['foreign_amount'] > 0 else None,
                    'currency': p['currency'],
                    'tickets': p['tickets']
                }
                for p in comp_data['projects'].values()
            ]
            companies_list.append({
                'company_id': comp_data['company_id'],
                'company_name': comp_data['company_name'],
                'projects': projects_list
            })

        result.append({
            'country_code': country_data['country_code'],
            'country_name': country_data['country_name'],
            'geo_classification': country_data['geo_classification'],
            'currency': country_data['currency'],
            'total_spent': round(country_data['total_spent'], 2),
            'tax_paid_foreign': None,
            'tax_reclamable_eur': round(country_data['tax_reclamable_eur'], 2),
            'projects_count': sum(len(c['projects']) for c in companies_list),
            'projects': [],
            'companies': companies_list
        })

    result.sort(key=lambda x: x['total_spent'], reverse=True)
    return result

