"""
Pydantic schemas for the supplier module.
Used by both admin routes (/suppliers) and portal routes (/portal).
"""

import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


# ============================================
# ADMIN SCHEMAS (used by /suppliers endpoints)
# ============================================

class CreateOCRequest(BaseModel):
    oc_number: str = Field(min_length=1, max_length=50)
    talent_name: str = Field(min_length=1, max_length=300)
    nif_cif: Optional[str] = Field(default=None, max_length=50)
    company_id: Optional[int] = None


class CreateOCResponse(BaseModel):
    id: int
    oc_number: str
    talent_name: str
    nif_cif: Optional[str] = None
    company_id: Optional[int] = None

class InviteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    email: EmailStr
    message: Optional[str] = Field(default=None, max_length=500)


class InviteResponse(BaseModel):
    id: int
    name: str
    email: str
    expires_at: datetime
    message: str


class SupplierResponse(BaseModel):
    id: int
    name: str
    email: str
    nif_cif: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    iban: Optional[str] = None
    bank_cert_url: Optional[str] = None
    supplier_type: str
    status: str
    oc_id: Optional[int] = None
    oc_number: Optional[str] = None
    company_name: Optional[str] = None
    is_active: bool
    notes_internal: Optional[str] = None
    gdpr_consent: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    invoices_count: int = 0
    pending_invoices: int = 0

    class Config:
        from_attributes = True


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    nif_cif: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    supplier_type: Optional[str] = None
    notes_internal: Optional[str] = None


class AssignOCRequest(BaseModel):
    oc_id: int


class NoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


class InvoiceStatusUpdate(BaseModel):
    status: Literal["APPROVED", "PAID", "REJECTED"]
    reason: Optional[str] = None  # Required for REJECTED


class InvoiceResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    invoice_number: str
    date: str
    provider_name: str
    oc_number: str
    company_id: Optional[int] = None
    base_amount: float
    iva_percentage: float
    iva_amount: float
    irpf_percentage: float
    irpf_amount: float
    final_total: float
    currency: str
    is_foreign: bool
    file_url: str
    status: str
    rejection_reason: Optional[str] = None
    delete_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceDetailResponse(InvoiceResponse):
    nif_cif: Optional[str] = None
    iban: Optional[str] = None
    ia_validation_result: Optional[str] = None


class NotificationResponse(BaseModel):
    id: int
    event_type: str
    title: str
    message: str
    related_invoice_id: Optional[int] = None
    related_supplier_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    pending_invoices: int
    approved_this_month: int
    active_suppliers: int
    total_paid_this_month: float
    unread_notifications: int


# ============================================
# PORTAL SCHEMAS (used by /portal endpoints)
# ============================================

class ValidateTokenResponse(BaseModel):
    valid: bool
    name: Optional[str] = None
    email: Optional[str] = None


class RegisterRequest(BaseModel):
    token: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=300)
    nif_cif: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)
    iban: Optional[str] = Field(default=None, max_length=50)
    password: str = Field(min_length=8)
    gdpr_consent: bool

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        return v


class RegisterResponse(BaseModel):
    message: str
    supplier_id: int
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    supplier: dict


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class ProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    nif_cif: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    iban_masked: Optional[str] = None
    supplier_type: str
    oc_number: Optional[str] = None
    created_at: datetime


class PortalInvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    date: str
    provider_name: str
    oc_number: str
    base_amount: float
    iva_amount: float
    final_total: float
    currency: str
    status: str
    rejection_reason: Optional[str] = None
    file_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeleteInvoiceRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class SummaryResponse(BaseModel):
    pending_amount: float
    paid_this_month: float
    total_invoices: int
