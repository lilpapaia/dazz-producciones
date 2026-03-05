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
    username = Column(String, unique=True, index=True, nullable=True)  # ← AÑADIDO
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(String, nullable=False)
    send_date = Column(String)
    creative_code = Column(String, nullable=False)
    company = Column(String, nullable=False)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="projects")
    tickets = relationship("Ticket", back_populates="project", cascade="all, delete-orphan")

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
    is_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    project = relationship("Project", back_populates="tickets")
