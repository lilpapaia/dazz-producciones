from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Date,
    ForeignKey, Text, Enum, LargeBinary, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.models.database import Base


# ============================================
# ENUMS - PROVEEDORES
# ============================================

class SupplierType(str, enum.Enum):
    INFLUENCER = "INFLUENCER"
    GENERAL = "GENERAL"
    MIXED = "MIXED"


class SupplierStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    NEW = "NEW"
    DEACTIVATED = "DEACTIVATED"


class InvoiceStatus(str, enum.Enum):
    PENDING = "PENDING"
    OC_PENDING = "OC_PENDING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    REJECTED = "REJECTED"
    DELETE_REQUESTED = "DELETE_REQUESTED"


class NotificationRecipientType(str, enum.Enum):
    ADMIN = "ADMIN"
    SUPPLIER = "SUPPLIER"


class NotificationEventType(str, enum.Enum):
    NEW_INVOICE = "NEW_INVOICE"
    REGISTRATION = "REGISTRATION"
    APPROVED = "APPROVED"
    PAID = "PAID"
    REJECTED = "REJECTED"
    DELETED = "DELETED"
    OC_LINKED = "OC_LINKED"
    IA_REJECTED = "IA_REJECTED"


# ============================================
# TABLA: SUPPLIER_OCS (OCs de influencers)
# ============================================

class SupplierOC(Base):
    __tablename__ = "supplier_ocs"

    id = Column(Integer, primary_key=True, index=True)
    oc_number = Column(String, unique=True, nullable=False, index=True)
    talent_name = Column(String, nullable=False)
    legal_name = Column(String, nullable=True)
    nif_cif = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relaciones
    company = relationship("Company")
    suppliers = relationship("Supplier", back_populates="oc")


# ============================================
# TABLA: SUPPLIERS (proveedores registrados)
# ============================================

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    email_hash = Column(String, nullable=True, index=True)
    hashed_password = Column(String, nullable=False)
    nif_cif = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    iban_encrypted = Column(LargeBinary, nullable=True)
    bank_cert_url = Column(String, nullable=True)
    supplier_type = Column(Enum(SupplierType), default=SupplierType.GENERAL, nullable=False)
    status = Column(Enum(SupplierStatus), default=SupplierStatus.NEW, nullable=False)
    oc_id = Column(Integer, ForeignKey("supplier_ocs.id", ondelete="SET NULL"), nullable=True)
    gdpr_consent = Column(Boolean, default=False, nullable=False)
    gdpr_consent_at = Column(DateTime, nullable=True)
    notes_internal = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    oc = relationship("SupplierOC", back_populates="suppliers")
    invoices = relationship("SupplierInvoice", back_populates="supplier", cascade="all, delete-orphan")


# ============================================
# TABLA: SUPPLIER_INVOICES (facturas del portal)
# ============================================

class SupplierInvoice(Base):
    __tablename__ = "supplier_invoices"
    __table_args__ = (
        UniqueConstraint("supplier_id", "invoice_number", name="uq_supplier_invoice_number"),
        # PERF-M2: Índice compuesto para queries frecuentes (list invoices por supplier + status)
        Index("ix_supplier_invoices_supplier_status", "supplier_id", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String, nullable=False)
    date = Column(String, nullable=False)
    # LOGIC-M2: date_parsed now mapped in ORM (column created via ALTER TABLE IF NOT EXISTS at startup)
    date_parsed = Column(Date, nullable=True)
    provider_name = Column(String, nullable=False)
    nif_cif = Column(String, nullable=True)
    iban = Column(String, nullable=True)
    oc_number = Column(String, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    base_amount = Column(Float, nullable=False)
    iva_percentage = Column(Float, nullable=False)
    iva_amount = Column(Float, nullable=False)
    irpf_percentage = Column(Float, default=0.0)
    irpf_amount = Column(Float, default=0.0)
    final_total = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    is_foreign = Column(Boolean, default=False)
    file_url = Column(String, nullable=False)
    # file_pages — added via ALTER TABLE in upload endpoint (not in ORM to avoid startup crash)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING, nullable=False, index=True)
    rejection_reason = Column(Text, nullable=True)
    delete_reason = Column(Text, nullable=True)
    ia_validation_result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    supplier = relationship("Supplier", back_populates="invoices")
    project = relationship("Project")
    company = relationship("Company")


# ============================================
# TABLA: SUPPLIER_NOTIFICATIONS
# ============================================

class SupplierNotification(Base):
    __tablename__ = "supplier_notifications"
    __table_args__ = (
        # PERF-M2: Índice compuesto para queries de notificaciones no leídas por destinatario
        Index("ix_notifications_recipient_read", "recipient_type", "recipient_id", "is_read"),
    )

    id = Column(Integer, primary_key=True, index=True)
    recipient_type = Column(Enum(NotificationRecipientType), nullable=False)
    recipient_id = Column(Integer, nullable=False, index=True)
    event_type = Column(Enum(NotificationEventType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    related_invoice_id = Column(Integer, ForeignKey("supplier_invoices.id", ondelete="SET NULL"), nullable=True)
    related_supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ============================================
# TABLA: SUPPLIER_INVITATIONS (tokens invitación 72h)
# ============================================

class SupplierInvitation(Base):
    __tablename__ = "supplier_invitations"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # supplier_type — added via ALTER TABLE (not in ORM to avoid startup crash)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ============================================
# TABLA: SUPPLIER_REFRESH_TOKENS (sesiones proveedor)
# ============================================

class SupplierRefreshToken(Base):
    __tablename__ = "supplier_refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    revoked_at = Column(DateTime, nullable=True)

    supplier = relationship("Supplier")
