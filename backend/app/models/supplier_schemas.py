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
    status: str
    has_permanent_oc: bool = False
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
    has_pending_actions: bool = False
    ia_cert_verified: bool = True

    class Config:
        from_attributes = True


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    nif_cif: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes_internal: Optional[str] = None


class AssignOCRequest(BaseModel):
    oc_number: str = Field(min_length=1, max_length=50)


class AssignInvoiceOCRequest(BaseModel):
    oc_number: str = Field(min_length=1, max_length=100)


class NoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


class InvoiceStatusUpdate(BaseModel):
    status: Literal["APPROVED", "PAID"]
    reason: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    invoice_number: str
    date: str
    provider_name: str
    oc_number: Optional[str] = None
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
    file_pages: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    delete_reason: Optional[str] = None
    is_autoinvoice: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceDetailResponse(InvoiceResponse):
    nif_cif: Optional[str] = None
    ia_validation_result: Optional[str] = None


class NotificationResponse(BaseModel):
    id: int
    event_type: str
    title: str
    message: str
    related_invoice_id: Optional[int] = None
    related_supplier_id: Optional[int] = None
    extra_data: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    pending_invoices: int
    approved_this_month: int
    active_suppliers: int
    total_paid_this_month: float
    paid_invoices_this_month: int = 0
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
    password: str = Field(min_length=8, max_length=128)
    gdpr_consent: bool
    privacy_accepted: bool
    contract_accepted: Optional[bool] = None
    accepted_document_ids: Optional[list[int]] = None  # FEAT-06 Phase 2: dynamic document acceptance
    has_cert_warnings: bool = False

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        from app.services.password_validator import validate_password_strength
        return validate_password_strength(v, lang="en")


class RegisterResponse(BaseModel):
    message: str
    supplier_id: int
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


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
    has_permanent_oc: bool = False
    oc_number: Optional[str] = None
    company_name: Optional[str] = None
    status: str = "ACTIVE"
    has_pending_change: bool = False
    pending_change_info: Optional[str] = None
    privacy_accepted_at: Optional[datetime] = None
    contract_accepted_at: Optional[datetime] = None
    created_at: datetime


class PortalInvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    date: str
    provider_name: str
    oc_number: Optional[str] = None
    base_amount: float
    iva_amount: float
    final_total: float
    currency: str
    status: str
    rejection_reason: Optional[str] = None
    file_url: Optional[str] = None
    is_autoinvoice: bool = False
    company_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeleteInvoiceRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class SummaryResponse(BaseModel):
    pending_amount: float
    paid_this_month: float
    total_invoices: int
    unread_notifications: int = 0


class DataChangeRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=300)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)


class IbanChangeRequest(BaseModel):
    new_iban: str = Field(min_length=10, max_length=50)


class DeactivationRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


# ============================================
# LEGAL DOCUMENTS SCHEMAS (FEAT-06)
# ============================================

class LegalDocumentResponse(BaseModel):
    id: int
    type: str
    version: int
    title: str
    file_size: Optional[int] = None
    is_generic: bool
    target_supplier_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LegalDocumentDetailResponse(LegalDocumentResponse):
    """Includes content HTML — used for modal display."""
    content: Optional[str] = None
    file_url: Optional[str] = None


class PendingDocumentResponse(BaseModel):
    id: int
    type: str
    title: str
    version: int


class AcceptedDocumentResponse(BaseModel):
    id: int
    type: str
    title: str
    version: int
    accepted_at: datetime


class MyDocumentsResponse(BaseModel):
    pending: list[PendingDocumentResponse]
    accepted: list[AcceptedDocumentResponse]


class SupplierDocumentsResponse(BaseModel):
    """Admin view: docs for a specific supplier."""
    supplier_id: int
    supplier_name: str
    is_influencer: bool
    pending: list[PendingDocumentResponse]
    accepted: list[AcceptedDocumentResponse]


# FEAT-06 Phase 2 schemas

class DocumentStatsResponse(BaseModel):
    id: int
    type: str
    title: str
    version: int
    created_at: datetime
    total_applicable: int
    total_accepted: int


class PendingSupplierResponse(BaseModel):
    id: int
    name: str
    nif_cif: Optional[str] = None
    oc_number: Optional[str] = None
    created_at: datetime
    last_activity: Optional[datetime] = None


class InfluencerContractInfo(BaseModel):
    id: int
    name: str
    nif_cif: Optional[str] = None
    oc_number: Optional[str] = None
    contract_version: Optional[int] = None
    contract_type: Optional[str] = None  # "generic" or "custom"
    contract_doc_id: Optional[int] = None


class BossInfluencerDocStatus(BaseModel):
    """Full document status for a single influencer — used by BOSS contracts view."""
    id: int
    name: str
    nif_cif: Optional[str] = None
    oc_number: Optional[str] = None
    contract_version: Optional[int] = None
    contract_type: Optional[str] = None
    contract_accepted: bool = False
    autocontrol_version: Optional[int] = None
    autocontrol_accepted: bool = False
    privacy_version: Optional[int] = None
    privacy_accepted: bool = False
    terms_version: Optional[int] = None
    terms_accepted: bool = False


class RegistrationDocumentResponse(BaseModel):
    """Document for step 4 registration — includes content HTML."""
    id: int
    type: str
    title: str
    version: int
    content: Optional[str] = None
    file_url: Optional[str] = None


class AutoInvoiceRequest(BaseModel):
    company_id: int
    supplier_id: int
    invoice_number: str = Field(min_length=1, max_length=50)
    date: str = Field(min_length=1, max_length=20)
    concept: str = Field(min_length=1, max_length=1000)
    base_amount: float = Field(gt=0)
    iva_percentage: float = Field(ge=0, le=1)
    irpf_percentage: float = Field(ge=0, le=1)
    oc_number: str = Field(min_length=1, max_length=100)
    gastos_base: float = Field(default=0, ge=0)
    gastos_iva_percentage: float = Field(default=0, ge=0, le=1)
