import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime, date
from enum import Enum

# ============================================
# ENUMS - DEBEN COINCIDIR CON database.py
# ============================================

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    BOSS = "BOSS"
    WORKER = "WORKER"

class ProjectStatus(str, Enum):
    EN_CURSO = "en_curso"
    CERRADO = "cerrado"

class TicketType(str, Enum):
    TICKET = "ticket"
    FACTURA = "factura"

# ============================================
# COMPANY SCHEMAS
# ============================================

class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    cif: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# USER SCHEMAS
# ============================================

class UserBase(BaseModel):
    email: EmailStr
    name: str
    username: Optional[str] = None
    role: UserRole = UserRole.WORKER

class UserCreate(UserBase):
    password: str = Field(min_length=8)
    company_ids: Optional[List[int]] = []

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/\\`~]', v):
            raise ValueError('La contraseña debe contener al menos un símbolo especial')
        return v

class UserLogin(BaseModel):
    identifier: str  # Email O username
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    companies: List[CompanyResponse] = []  # Empresas asignadas
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)

# ============================================
# PASSWORD RESET / SET PASSWORD SCHEMAS
# ============================================

class SetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8)

    @field_validator('new_password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/\\`~]', v):
            raise ValueError('La contraseña debe contener al menos un símbolo especial')
        return v

class SetPasswordResponse(BaseModel):
    message: str
    success: bool

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

# ============================================
# PROJECT SCHEMAS
# ============================================

class ProjectBase(BaseModel):
    year: str = Field(min_length=4, max_length=4)
    send_date: Optional[str] = None
    creative_code: str = Field(min_length=1, max_length=100)
    company: Optional[str] = None  # Campo antiguo (string)
    owner_company_id: Optional[int] = None  # Campo nuevo (FK)
    responsible: str = Field(min_length=1, max_length=200)
    invoice_type: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    other_invoice_data: Optional[str] = Field(default=None, max_length=1000)
    client_oc: Optional[str] = Field(default=None, max_length=200)
    client_data: Optional[str] = Field(default=None, max_length=500)
    client_email: Optional[str] = Field(default=None, max_length=200)
    project_link: Optional[str] = Field(default=None, max_length=500)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    year: Optional[str] = None
    send_date: Optional[str] = None
    creative_code: Optional[str] = None
    company: Optional[str] = None
    owner_company_id: Optional[int] = None
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
    owner_company: Optional[CompanyResponse] = None  # Empresa del proyecto
    
    class Config:
        from_attributes = True

# ============================================
# TICKET SCHEMAS
# ============================================

class TicketBase(BaseModel):
    date: str = Field(min_length=1)
    provider: str = Field(min_length=1, max_length=500)
    invoice_number: Optional[str] = Field(default=None, max_length=100)
    po_notes: Optional[str] = Field(default=None, max_length=1000)
    base_amount: float = Field(ge=0)
    iva_amount: float = Field(ge=0)
    iva_percentage: float = Field(ge=0, le=100)
    total_with_iva: float = Field(ge=0)
    irpf_percentage: float = Field(default=0.0, ge=0, le=100)
    irpf_amount: float = Field(default=0.0, ge=0)
    final_total: float = Field(ge=0)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=200)
    contact_name: Optional[str] = Field(default=None, max_length=200)
    invoice_status: Optional[str] = Field(default=None, max_length=50)
    payment_status: Optional[str] = Field(default=None, max_length=50)
    type: TicketType = TicketType.TICKET

class TicketCreate(TicketBase):
    file_name: str
    file_path: str

class TicketUpdate(BaseModel):
    date: Optional[str] = Field(default=None, min_length=1)
    provider: Optional[str] = Field(default=None, min_length=1, max_length=500)
    invoice_number: Optional[str] = Field(default=None, max_length=100)
    po_notes: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=2000)
    base_amount: Optional[float] = Field(default=None, ge=0)
    iva_amount: Optional[float] = Field(default=None, ge=0)
    iva_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    total_with_iva: Optional[float] = Field(default=None, ge=0)
    irpf_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    irpf_amount: Optional[float] = Field(default=None, ge=0)
    final_total: Optional[float] = Field(default=None, ge=0)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=200)
    contact_name: Optional[str] = Field(default=None, max_length=200)
    invoice_status: Optional[str] = Field(default=None, max_length=50)
    payment_status: Optional[str] = Field(default=None, max_length=50)
    type: Optional[TicketType] = None
    is_reviewed: Optional[bool] = None

class TicketResponse(TicketBase):
    id: int
    file_name: str
    file_path: str
    file_pages: Optional[str] = None
    pdf_url: Optional[str] = None
    notes: Optional[str] = None
    is_reviewed: bool
    created_at: datetime
    project_id: int
    is_foreign: bool
    currency: str
    country_code: Optional[str] = None
    geo_classification: Optional[str] = None
    foreign_amount: Optional[float] = None
    foreign_total: Optional[float] = None
    foreign_tax_amount: Optional[float] = None
    foreign_tax_eur: Optional[float] = None
    exchange_rate: Optional[float] = None
    exchange_rate_date: Optional[date] = None
    
    class Config:
        from_attributes = True

# ============================================
# AI EXTRACTION RESPONSE
# ============================================

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
    confidence: float
    is_foreign: bool = False
    currency: str = "EUR"
    country_code: Optional[str] = None
    foreign_amount: Optional[float] = None
    foreign_total: Optional[float] = None
    foreign_tax_amount: Optional[float] = None

# ============================================
# SCHEMAS ESTADÍSTICAS
# ============================================

class StatisticsOverview(BaseModel):
    total_spent: float
    international_spent: float
    iva_reclamable: float
    projects_total: int
    projects_closed: int
    projects_open: int

class MonthlyDataPoint(BaseModel):
    month: int
    month_name: str
    total: float

class CurrencyDistribution(BaseModel):
    currency: str
    label: str
    total: float
    percentage: float
    color: str

class TicketSummary(BaseModel):
    """Resumen de ticket para estadísticas de gastos internacionales"""
    id: int
    date: Optional[str] = None
    provider: str
    invoice_number: Optional[str] = None
    final_total: float
    foreign_amount: Optional[float] = None
    foreign_tax_eur: Optional[float] = None
    currency: str

class ProjectSummary(BaseModel):
    id: int
    creative_code: str
    description: str
    total_amount: float
    foreign_amount: Optional[float] = None
    currency: Optional[str] = None
    tickets: List[TicketSummary] = []

class CompanyGroup(BaseModel):
    """Agrupación de proyectos por empresa"""
    company_id: int
    company_name: str
    projects: List[ProjectSummary]

class CountryBreakdown(BaseModel):
    country_code: str
    country_name: str
    geo_classification: str
    currency: str
    total_spent: float
    tax_paid_foreign: Optional[float] = None
    tax_reclamable_eur: float
    projects_count: int
    projects: Optional[List[ProjectSummary]] = []
    companies: Optional[List[CompanyGroup]] = None

class StatisticsResponse(BaseModel):
    """
    Respuesta dinámica según el modo:
    - all_companies: ADMIN sin filtro de empresa
    - single_company: ADMIN con empresa específica o BOSS
    """
    mode: str  # "all_companies" | "single_company"
    overview: StatisticsOverview
    monthly_evolution: List[MonthlyDataPoint]
    currency_distribution: List[CurrencyDistribution]
    foreign_breakdown: List[CountryBreakdown]
    
    # Solo en modo single_company
    company: Optional[Dict[str, Any]] = None

    class Config:
        # Permite campos extra que lleguen del backend sin romper la validación
        extra = "allow"
