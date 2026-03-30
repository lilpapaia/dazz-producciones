"""
Fixtures compartidas para todos los tests.

Proporciona:
- Base de datos SQLite en memoria (aislada por test)
- TestClient FastAPI con dependency override
- Usuarios (admin, boss, worker) con tokens JWT
- Empresas y proyectos de ejemplo
"""

import pytest
import sys
import os

# Asegurar que el directorio backend está en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar environment de test ANTES de importar la app
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-not-production")
os.environ.setdefault("ENVIRONMENT", "development")

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.models.database import Base, User, Company, UserCompany, Project, Ticket, ProjectStatus
from app.models.suppliers import (
    Supplier, SupplierInvoice, SupplierOC, SupplierInvitation,
    SupplierNotification, SupplierRefreshToken,
    SupplierStatus, InvoiceStatus, NotificationRecipientType, NotificationEventType,
)
from app.services.auth import get_password_hash, create_access_token
from app.services.supplier_auth import get_password_hash as supplier_hash, create_supplier_access_token
from app.services.encryption import encrypt_iban


# ============================================
# DATABASE FIXTURES
# ============================================

@pytest.fixture(scope="function")
def db_engine():
    """Motor SQLite en memoria con StaticPool (misma conexión para todos)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Sesión de BD limpia por cada test."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ============================================
# FASTAPI CLIENT FIXTURE
# ============================================

@pytest.fixture(scope="function")
def client(db_session):
    """TestClient con BD de test inyectada. Rate limiter se resetea por test."""
    from config.database import get_db
    from main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Resetear TODOS los rate limiters para evitar 429 entre tests
    for limiter_ref in [app.state.limiter]:
        try:
            limiter_ref.reset()
            limiter_ref._storage.reset()
            limiter_ref._storage.storage.clear()
            limiter_ref._storage.expirations.clear()
        except Exception:
            pass
    try:
        from app.routes.auth import limiter as auth_limiter
        auth_limiter.reset()
        auth_limiter._storage.reset()
        auth_limiter._storage.storage.clear()
        auth_limiter._storage.expirations.clear()
    except Exception:
        pass

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ============================================
# COMPANY FIXTURES
# ============================================

@pytest.fixture
def company_dazz(db_session):
    """Empresa principal: Dazz Creative."""
    company = Company(name="Dazz Creative", cif="B12345678", address="Madrid")
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def company_other(db_session):
    """Segunda empresa para tests de multi-tenant."""
    company = Company(name="Other Corp", cif="B87654321", address="Barcelona")
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


# ============================================
# USER FIXTURES
# ============================================

@pytest.fixture
def admin_user(db_session, company_dazz):
    """Usuario ADMIN con empresa asignada."""
    user = User(
        name="Admin Test",
        email="admin@test.com",
        username="admin",
        hashed_password=get_password_hash("Password123!"),
        role="ADMIN",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    uc = UserCompany(user_id=user.id, company_id=company_dazz.id)
    db_session.add(uc)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def boss_user(db_session, company_dazz):
    """Usuario BOSS con empresa Dazz asignada."""
    user = User(
        name="Boss Test",
        email="boss@test.com",
        username="boss",
        hashed_password=get_password_hash("Password123!"),
        role="BOSS",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    uc = UserCompany(user_id=user.id, company_id=company_dazz.id)
    db_session.add(uc)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def worker_user(db_session, company_dazz):
    """Usuario WORKER con empresa Dazz asignada."""
    user = User(
        name="Worker Test",
        email="worker@test.com",
        username="worker",
        hashed_password=get_password_hash("Password123!"),
        role="WORKER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    uc = UserCompany(user_id=user.id, company_id=company_dazz.id)
    db_session.add(uc)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def boss_other_company(db_session, company_other):
    """BOSS de otra empresa (para tests de aislamiento)."""
    user = User(
        name="Boss Other",
        email="boss_other@test.com",
        username="boss_other",
        hashed_password=get_password_hash("Password123!"),
        role="BOSS",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    uc = UserCompany(user_id=user.id, company_id=company_other.id)
    db_session.add(uc)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session):
    """Usuario inactivo."""
    user = User(
        name="Inactive User",
        email="inactive@test.com",
        username="inactive",
        hashed_password=get_password_hash("Password123!"),
        role="WORKER",
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================
# TOKEN FIXTURES
# ============================================

@pytest.fixture
def admin_token(admin_user):
    """Token JWT válido para admin."""
    return create_access_token(data={"sub": admin_user.email})


@pytest.fixture
def boss_token(boss_user):
    """Token JWT válido para boss."""
    return create_access_token(data={"sub": boss_user.email})


@pytest.fixture
def worker_token(worker_user):
    """Token JWT válido para worker."""
    return create_access_token(data={"sub": worker_user.email})


@pytest.fixture
def boss_other_token(boss_other_company):
    """Token JWT para boss de otra empresa."""
    return create_access_token(data={"sub": boss_other_company.email})


def auth_header(token: str) -> dict:
    """Helper para crear header Authorization."""
    return {"Authorization": f"Bearer {token}"}


# ============================================
# PROJECT FIXTURES
# ============================================

@pytest.fixture
def project_dazz(db_session, admin_user, company_dazz):
    """Proyecto de la empresa Dazz, creado por admin."""
    project = Project(
        year="2026",
        creative_code="DAZ-001",
        company=company_dazz.name,
        owner_company_id=company_dazz.id,
        responsible="MIGUEL",
        invoice_type="Factura",
        description="Proyecto Test Dazz",
        status=ProjectStatus.EN_CURSO,
        owner_id=admin_user.id,
        total_amount=0.0,
        tickets_count=0
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def project_other(db_session, boss_other_company, company_other):
    """Proyecto de otra empresa."""
    project = Project(
        year="2026",
        creative_code="OTH-001",
        company=company_other.name,
        owner_company_id=company_other.id,
        responsible="ANTONIO",
        invoice_type="Ticket",
        description="Proyecto Other Corp",
        status=ProjectStatus.EN_CURSO,
        owner_id=boss_other_company.id,
        total_amount=0.0,
        tickets_count=0
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def project_worker(db_session, worker_user, company_dazz):
    """Proyecto creado por un worker."""
    project = Project(
        year="2026",
        creative_code="WRK-001",
        company=company_dazz.name,
        owner_company_id=company_dazz.id,
        responsible="JULIETA",
        invoice_type="Factura",
        description="Proyecto Worker",
        status=ProjectStatus.EN_CURSO,
        owner_id=worker_user.id,
        total_amount=0.0,
        tickets_count=0
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


# ============================================
# TICKET FIXTURES
# ============================================

@pytest.fixture
def ticket_nacional(db_session, project_dazz):
    """Ticket nacional (España, EUR)."""
    ticket = Ticket(
        project_id=project_dazz.id,
        date="15/01/2026",
        provider="Restaurante Madrid",
        base_amount=100.0,
        iva_amount=21.0,
        iva_percentage=21.0,
        total_with_iva=121.0,
        final_total=121.0,
        is_foreign=False,
        currency="EUR",
        country_code="ES",
        geo_classification="NACIONAL",
        type="ticket",
        file_path="https://cloudinary.com/test.webp",
        file_name="ticket_test.jpg",
        is_reviewed=False
    )
    db_session.add(ticket)
    project_dazz.tickets_count += 1
    project_dazz.total_amount += ticket.final_total
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


# ============================================
# SUPPLIER FIXTURES
# ============================================

@pytest.fixture
def supplier_user(db_session):
    """Proveedor activo con IBAN encriptado."""
    import hashlib
    email = "supplier@test.dazz.com"
    supplier = Supplier(
        name="Test Supplier SL",
        email=email,
        email_hash=hashlib.sha256(email.encode()).hexdigest(),
        hashed_password=supplier_hash("TestSupplier123!"),
        nif_cif="B11223344",
        phone="+34600111222",
        address="Calle Test 1, Madrid",
        iban_encrypted=encrypt_iban("ES7921000813610123456789"),
        status=SupplierStatus.ACTIVE,
        is_active=True,
        gdpr_consent=True,
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


@pytest.fixture
def supplier_token(supplier_user):
    """JWT válido para proveedor."""
    return create_supplier_access_token(supplier_user.id, supplier_user.email)


@pytest.fixture
def supplier_invitation(db_session, admin_user):
    """Invitación válida (72h) para tests de registro."""
    from datetime import datetime, timedelta, timezone
    inv = SupplierInvitation(
        email="newinvite@test.com",
        name="Invited Supplier",
        token="valid-invite-token-123",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
        invited_by=admin_user.id,
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(inv)
    return inv


@pytest.fixture
def supplier_invoice(db_session, supplier_user, company_dazz):
    """Factura de proveedor en estado PENDING."""
    inv = SupplierInvoice(
        supplier_id=supplier_user.id,
        invoice_number="SUP-2026-001",
        date="15/01/2026",
        provider_name=supplier_user.name,
        nif_cif=supplier_user.nif_cif,
        oc_number="OC-TEST001",
        company_id=company_dazz.id,
        base_amount=500.0,
        iva_percentage=21.0,
        iva_amount=105.0,
        irpf_percentage=0.0,
        irpf_amount=0.0,
        final_total=605.0,
        currency="EUR",
        is_foreign=False,
        file_url="https://res.cloudinary.com/test/raw/upload/v1/invoice.pdf",
        status=InvoiceStatus.PENDING,
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(inv)
    return inv


@pytest.fixture
def supplier_oc(db_session, company_dazz):
    """OC permanente para tests."""
    oc = SupplierOC(
        oc_number="OC-MGMTINT2026001",
        talent_name="Test Talent",
        nif_cif="X1234567A",
        company_id=company_dazz.id,
    )
    db_session.add(oc)
    db_session.commit()
    db_session.refresh(oc)
    return oc


@pytest.fixture
def ticket_foreign(db_session, project_dazz):
    """Ticket extranjero (US, USD)."""
    ticket = Ticket(
        project_id=project_dazz.id,
        date="20/02/2026",
        provider="US Supplier Inc",
        base_amount=200.0,
        iva_amount=20.0,
        iva_percentage=10.0,
        total_with_iva=220.0,
        final_total=220.0,
        is_foreign=True,
        currency="USD",
        country_code="US",
        geo_classification="INTERNACIONAL",
        foreign_amount=200.0,
        foreign_total=220.0,
        foreign_tax_amount=20.0,
        foreign_tax_eur=18.50,
        exchange_rate=0.925,
        type="factura",
        file_path="https://cloudinary.com/foreign.webp",
        file_name="invoice_us.pdf",
        is_reviewed=True
    )
    db_session.add(ticket)
    project_dazz.tickets_count += 1
    project_dazz.total_amount += ticket.final_total
    db_session.commit()
    db_session.refresh(ticket)
    return ticket
