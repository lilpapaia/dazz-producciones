from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum, Date, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

Base = declarative_base()

# ============================================
# ENUMS (EN MAYÚSCULAS - coincide con PostgreSQL)
# ============================================

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    BOSS = "BOSS"
    WORKER = "WORKER"

class ProjectStatus(str, enum.Enum):
    EN_CURSO = "en_curso"
    CERRADO = "cerrado"

class TicketType(str, enum.Enum):
    TICKET = "ticket"
    FACTURA = "factura"

# ============================================
# NUEVA TABLA: COMPANIES
# ============================================

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    cif = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    users = relationship("User", secondary="user_companies", back_populates="companies")
    projects = relationship("Project", back_populates="owner_company")

# ============================================
# NUEVA TABLA INTERMEDIA: USER_COMPANIES (Many-to-Many)
# ============================================

class UserCompany(Base):
    __tablename__ = "user_companies"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# ============================================
# MODELO USER (ACTUALIZADO)
# ============================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.WORKER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # SEC-H2: Account lockout tras login fallidos
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    # Relaciones
    projects = relationship("Project", back_populates="owner")
    companies = relationship("Company", secondary="user_companies", back_populates="users")

# ============================================
# MODELO PROJECT (ACTUALIZADO)
# ============================================

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(String, nullable=False)
    send_date = Column(String)
    creative_code = Column(String, nullable=False)
    
    # ⚠️ MANTENER CAMPO ANTIGUO POR AHORA (compatibilidad)
    company = Column(String, nullable=True)
    
    # ✅ NUEVO CAMPO - Empresa dueña del proyecto
    owner_company_id = Column(Integer, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=True)
    
    responsible = Column(String, nullable=False)
    invoice_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    other_invoice_data = Column(String)
    client_oc = Column(String)
    client_data = Column(Text)
    client_email = Column(String)
    project_link = Column(String)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.EN_CURSO, nullable=False)
    total_amount = Column(Float, default=0.0)
    tickets_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relaciones
    owner = relationship("User", back_populates="projects")
    owner_company = relationship("Company", back_populates="projects")
    tickets = relationship("Ticket", back_populates="project", cascade="all, delete-orphan")

# ============================================
# MODELO TICKET (SIN CAMBIOS)
# ============================================

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    invoice_number = Column(String)
    po_notes = Column(Text)
    base_amount = Column(Float, nullable=False)
    iva_amount = Column(Float, nullable=False)
    iva_percentage = Column(Float, nullable=False)
    total_with_iva = Column(Float, nullable=False)
    irpf_percentage = Column(Float, default=0.0)
    irpf_amount = Column(Float, default=0.0)
    final_total = Column(Float, nullable=False)
    phone = Column(String)
    email = Column(String)
    contact_name = Column(String)
    invoice_status = Column(String)
    payment_status = Column(String)
    notes = Column(Text)
    is_foreign = Column(Boolean, default=False)
    currency = Column(String, default='EUR')
    country_code = Column(String, nullable=True)
    geo_classification = Column(String, nullable=True)
    foreign_amount = Column(Float, nullable=True)
    foreign_total = Column(Float, nullable=True)
    foreign_tax_amount = Column(Float, nullable=True)
    exchange_rate = Column(Float, nullable=True)
    exchange_rate_date = Column(Date, nullable=True)
    foreign_tax_eur = Column(Float, nullable=True)
    type = Column(Enum(TicketType), default=TicketType.TICKET, nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_pages = Column(Text, nullable=True)
    pdf_url = Column(String, nullable=True)
    file_hash = Column(String(32), nullable=True, index=True)
    is_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Campos portal proveedores (Fase 1)
    from_supplier_portal = Column(Boolean, default=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)
    supplier_invoice_id = Column(Integer, ForeignKey("supplier_invoices.id"), nullable=True, index=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Relaciones
    project = relationship("Project", back_populates="tickets")
    supplier = relationship("Supplier", foreign_keys=[supplier_id])
    supplier_invoice = relationship("SupplierInvoice", foreign_keys=[supplier_invoice_id])

# ============================================
# MODELO PASSWORD RESET TOKEN (SIN CAMBIOS)
# ============================================

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    user = relationship("User")

# ============================================
# MODELO REFRESH TOKEN (VULN-009)
# ============================================

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User")
