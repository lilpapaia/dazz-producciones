from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class ProjectStatus(str, Enum):
    EN_CURSO = "en_curso"
    CERRADO = "cerrado"

class TicketType(str, Enum):
    TICKET = "ticket"
    FACTURA = "factura"

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Project Schemas
class ProjectBase(BaseModel):
    year: str
    send_date: Optional[str] = None
    creative_code: str
    company: str
    responsible: str
    invoice_type: str
    description: str
    other_invoice_data: Optional[str] = None
    client_oc: Optional[str] = None
    client_data: Optional[str] = None
    client_email: Optional[str] = None
    project_link: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    year: Optional[str] = None
    send_date: Optional[str] = None
    creative_code: Optional[str] = None
    company: Optional[str] = None
    responsible: Optional[str] = None
    invoice_type: Optional[str] = None
    description: Optional[str] = None
    other_invoice_data: Optional[str] = None
    client_oc: Optional[str] = None
    client_data: Optional[str] = None
    client_email: Optional[str] = None
    project_link: Optional[str] = None
    status: Optional[ProjectStatus] = None

class ProjectResponse(ProjectBase):
    id: int
    status: ProjectStatus
    total_amount: float
    tickets_count: int
    created_at: datetime
    closed_at: Optional[datetime] = None
    owner_id: int
    
    class Config:
        from_attributes = True

# Ticket Schemas
class TicketBase(BaseModel):
    date: str
    provider: str
    invoice_number: Optional[str] = None
    po_notes: Optional[str] = None
    base_amount: float
    iva_amount: float
    iva_percentage: float
    total_with_iva: float
    irpf_percentage: float = 0.0
    irpf_amount: float = 0.0
    final_total: float
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None
    invoice_status: Optional[str] = None
    payment_status: Optional[str] = None
    type: TicketType = TicketType.TICKET

class TicketCreate(TicketBase):
    file_name: str
    file_path: str

class TicketUpdate(BaseModel):
    date: Optional[str] = None
    provider: Optional[str] = None
    invoice_number: Optional[str] = None
    po_notes: Optional[str] = None
    base_amount: Optional[float] = None
    iva_amount: Optional[float] = None
    iva_percentage: Optional[float] = None
    total_with_iva: Optional[float] = None
    irpf_percentage: Optional[float] = None
    irpf_amount: Optional[float] = None
    final_total: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None
    invoice_status: Optional[str] = None
    payment_status: Optional[str] = None
    type: Optional[TicketType] = None
    is_reviewed: Optional[bool] = None

class TicketResponse(TicketBase):
    id: int
    file_name: str
    file_path: str
    is_reviewed: bool
    created_at: datetime
    project_id: int
    
    class Config:
        from_attributes = True

# AI Extraction Response
class AIExtractionResponse(BaseModel):
    date: str
    provider: str
    invoice_number: Optional[str] = None
    base_amount: float
    iva_percentage: float
    iva_amount: float
    total_with_iva: float
    irpf_percentage: float
    irpf_amount: float
    final_total: float
    type: TicketType
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None
    confidence: float  # 0-1 score de confianza de la IA
