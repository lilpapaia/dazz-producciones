from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class ProjectStatus(str, enum.Enum):
    EN_CURSO = "en_curso"
    CERRADO = "cerrado"

class TicketType(str, enum.Enum):
    TICKET = "ticket"
    FACTURA = "factura"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Cabecera del proyecto (línea 2-3 del Excel)
    year = Column(String, nullable=False)
    send_date = Column(String)
    creative_code = Column(String, nullable=False)  # OC-PROD
    company = Column(String, nullable=False)
    responsible = Column(String, nullable=False)
    invoice_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    other_invoice_data = Column(String)  # OTROS DATOS FACTURA
    client_oc = Column(String)  # OC DE CLIENTE
    client_data = Column(Text)
    client_email = Column(String)
    project_link = Column(String)  # SharePoint link
    
    # Metadata
    status = Column(Enum(ProjectStatus), default=ProjectStatus.EN_CURSO, nullable=False)
    total_amount = Column(Float, default=0.0)
    tickets_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # Foreign Keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    tickets = relationship("Ticket", back_populates="project", cascade="all, delete-orphan")

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Datos extraídos por IA (columnas A-K del Excel)
    date = Column(String, nullable=False)  # A: FECHA SU FACTURA
    provider = Column(String, nullable=False)  # B: Proveedor
    invoice_number = Column(String)  # C: Nº FACTURA PROVEEDOR
    po_notes = Column(Text)  # D: PO SI APLICA (notas)
    base_amount = Column(Float, nullable=False)  # E: IMPORTE (siempre en EUR)
    iva_amount = Column(Float, nullable=False)  # F: TIPO (cantidad IVA en EUR)
    iva_percentage = Column(Float, nullable=False)  # G: TIPO IVA (%)
    total_with_iva = Column(Float, nullable=False)  # H: TOTAL (en EUR)
    irpf_percentage = Column(Float, default=0.0)  # I: TIPO IRPF
    irpf_amount = Column(Float, default=0.0)  # J: RETENCION
    final_total = Column(Float, nullable=False)  # K: TOTAL (en EUR)
    
    # Campos adicionales para FACTURAS (columnas N, O, P)
    phone = Column(String)  # N: TELEFONO
    email = Column(String)  # O: EMAIL
    contact_name = Column(String)  # P: NOMBRE
    
    # Campos de gestión (columnas L, M)
    invoice_status = Column(String)  # L: ESTATUS FACTURA
    payment_status = Column(String)  # M: ESTATUS PAGO
    
    # ============================================
    # NUEVOS CAMPOS MONEDA EXTRANJERA
    # ============================================
    is_foreign = Column(Boolean, default=False)  # ¿Es factura internacional?
    currency = Column(String, default='EUR')  # Divisa original (USD, GBP, CHF, etc.)
    country_code = Column(String, nullable=True)  # Código país (US, GB, CH, FR, etc.)
    geo_classification = Column(String, nullable=True)  # NACIONAL / UE / INTERNACIONAL
    
    # Importes en divisa original (si es extranjera)
    foreign_amount = Column(Float, nullable=True)  # Base en divisa original
    foreign_total = Column(Float, nullable=True)  # Total en divisa original
    foreign_tax_amount = Column(Float, nullable=True)  # IVA en divisa original
    
    # Tasa de cambio histórica
    exchange_rate = Column(Float, nullable=True)  # Tasa del día de la factura
    exchange_rate_date = Column(Date, nullable=True)  # Fecha tasa aplicada
    
    # IVA extranjero convertido a EUR (para estadísticas)
    foreign_tax_eur = Column(Float, nullable=True)  # IVA reclamable en EUR
    # ============================================
    
    # Metadata
    type = Column(Enum(TicketType), default=TicketType.TICKET, nullable=False)
    file_path = Column(String, nullable=False)  # Ruta del archivo original
    file_name = Column(String, nullable=False)  # Nombre del archivo original
    is_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="tickets")
