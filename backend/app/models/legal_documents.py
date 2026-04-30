"""
Models for the legal documents system.

Tables:
- legal_documents: Document metadata (type, version, content HTML, file_url for PDF in R2)
- supplier_document_acceptances: Tracks which supplier accepted which document and when
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.models.database import Base


class LegalDocumentType(str, enum.Enum):
    PRIVACY = "PRIVACY"
    TERMS = "TERMS"
    SUPPLIER_CONTRACT = "SUPPLIER_CONTRACT"
    INFLUENCER_CONTRACT = "INFLUENCER_CONTRACT"
    AUTOCONTROL = "AUTOCONTROL"


class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(30), nullable=False)  # PRIVACY, TERMS, SUPPLIER_CONTRACT, INFLUENCER_CONTRACT, AUTOCONTROL
    version = Column(Integer, default=1, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)  # HTML for scroll-to-accept modal
    file_url = Column(Text, nullable=True)  # R2 object key or public URL for PDF download
    file_size = Column(Integer, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_generic = Column(Boolean, default=True, nullable=False)
    target_supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    target_invitation_id = Column(Integer, ForeignKey("supplier_invitations.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    uploader = relationship("User", foreign_keys=[uploaded_by])
    target_supplier = relationship("Supplier", foreign_keys=[target_supplier_id])
    target_invitation = relationship("SupplierInvitation", foreign_keys=[target_invitation_id])
    company = relationship("Company")
    acceptances = relationship("SupplierDocumentAcceptance", back_populates="document", cascade="all, delete-orphan")


class SupplierDocumentAcceptance(Base):
    __tablename__ = "supplier_document_acceptances"
    __table_args__ = (
        UniqueConstraint("supplier_id", "document_id", name="uq_supplier_document_acceptance"),
    )

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("legal_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    accepted_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6, X-Forwarded-For behind Railway proxy

    # Relationships
    supplier = relationship("Supplier")
    document = relationship("LegalDocument", back_populates="acceptances")
