"""
Legal documents management endpoints.

Admin endpoints: /suppliers/legal-documents (CRUD for legal docs)
Portal endpoints: /portal/documents (supplier acceptance flow)
"""

import os
import logging
import tempfile
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from config.database import get_db
from app.models.database import User
from app.models.legal_documents import LegalDocument, SupplierDocumentAcceptance, LegalDocumentType
from app.models.suppliers import Supplier
from app.models.supplier_schemas import (
    LegalDocumentResponse, LegalDocumentDetailResponse,
    PendingDocumentResponse, AcceptedDocumentResponse,
    MyDocumentsResponse, SupplierDocumentsResponse,
)
from app.services.auth import get_current_admin_user
from app.services.supplier_auth import get_current_active_supplier
from app.services.validators import validate_pdf_bytes
from app.services.rate_limit import limiter
from config.constants import MAX_SUPPLIER_PDF_SIZE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Legal Documents"])


# ============================================
# CORE LOGIC: Determine pending documents
# ============================================

def get_applicable_documents(supplier: Supplier, db: Session) -> list[LegalDocument]:
    """Return all active legal documents that apply to a given supplier."""
    is_influencer = supplier.oc_id is not None
    all_active = db.query(LegalDocument).filter(LegalDocument.is_active == True).all()

    result = []
    # Check if there's a personalized CONTRACT for this supplier
    has_custom_contract = any(
        d.type == "CONTRACT" and d.target_supplier_id == supplier.id
        for d in all_active
    )

    for doc in all_active:
        if doc.type == "PRIVACY" and doc.is_generic:
            result.append(doc)
        elif doc.type in ("CONTRACT", "AUTOCONTROL", "DECLARATION"):
            if not is_influencer:
                continue
            if doc.type == "CONTRACT":
                if doc.is_generic and has_custom_contract:
                    # Skip generic contract if a custom one exists
                    continue
                if doc.target_supplier_id and doc.target_supplier_id != supplier.id:
                    # Custom contract for a different supplier
                    continue
            result.append(doc)

    return result


def get_pending_documents(supplier: Supplier, db: Session) -> list[LegalDocument]:
    """Return active documents that the supplier has NOT accepted yet."""
    applicable = get_applicable_documents(supplier, db)
    if not applicable:
        return []

    accepted_doc_ids = set(
        row[0] for row in db.query(SupplierDocumentAcceptance.document_id).filter(
            SupplierDocumentAcceptance.supplier_id == supplier.id,
            SupplierDocumentAcceptance.document_id.in_([d.id for d in applicable]),
        ).all()
    )

    return [d for d in applicable if d.id not in accepted_doc_ids]


def get_accepted_documents(supplier: Supplier, db: Session) -> list[dict]:
    """Return documents accepted by the supplier with acceptance dates."""
    acceptances = db.query(SupplierDocumentAcceptance).filter(
        SupplierDocumentAcceptance.supplier_id == supplier.id,
    ).all()

    if not acceptances:
        return []

    # Batch query to avoid N+1
    doc_ids = [a.document_id for a in acceptances]
    docs = {d.id: d for d in db.query(LegalDocument).filter(LegalDocument.id.in_(doc_ids)).all()}

    result = []
    for acc in acceptances:
        doc = docs.get(acc.document_id)
        if doc:
            result.append({
                "id": doc.id,
                "type": doc.type,
                "title": doc.title,
                "version": doc.version,
                "accepted_at": acc.accepted_at,
            })
    return result


def _get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For (Railway proxy) or direct connection."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ============================================
# ADMIN ENDPOINTS: /suppliers/legal-documents
# ============================================

@router.get("/suppliers/legal-documents", response_model=list[LegalDocumentResponse])
async def list_legal_documents(
    type: Optional[str] = Query(None, description="Filter by type: PRIVACY, CONTRACT, AUTOCONTROL, DECLARATION"),
    active_only: bool = Query(True, description="Only active documents"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """List all legal documents (ADMIN only)."""
    q = db.query(LegalDocument)
    if type:
        q = q.filter(LegalDocument.type == type.upper())
    if active_only:
        q = q.filter(LegalDocument.is_active == True)
    return q.order_by(LegalDocument.type, LegalDocument.version.desc()).all()


@router.post("/suppliers/legal-documents", response_model=LegalDocumentResponse)
async def create_legal_document(
    request: Request,
    file: UploadFile = File(...),
    doc_type: str = Query(..., description="PRIVACY, CONTRACT, AUTOCONTROL, DECLARATION"),
    title: str = Query(..., max_length=200),
    content: str = Query(..., description="HTML content for the scroll-to-accept modal"),
    is_generic: bool = Query(True),
    target_supplier_id: Optional[int] = Query(None),
    company_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Upload a new legal document PDF + HTML content (ADMIN only)."""
    doc_type = doc_type.upper()
    if doc_type not in [t.value for t in LegalDocumentType]:
        raise HTTPException(400, detail=f"Invalid type. Must be one of: {[t.value for t in LegalDocumentType]}")

    # Validate PDF
    contents = await file.read()
    validate_pdf_bytes(contents, max_size=MAX_SUPPLIER_PDF_SIZE)

    # Determine version (auto-increment from latest active of same type/target)
    latest = db.query(LegalDocument).filter(
        LegalDocument.type == doc_type,
        LegalDocument.is_generic == is_generic,
    )
    if target_supplier_id:
        latest = latest.filter(LegalDocument.target_supplier_id == target_supplier_id)
    else:
        latest = latest.filter(LegalDocument.is_generic == True)
    latest = latest.order_by(LegalDocument.version.desc()).first()
    new_version = (latest.version + 1) if latest else 1

    # Deactivate previous active document of same type/target
    prev_active = db.query(LegalDocument).filter(
        LegalDocument.type == doc_type,
        LegalDocument.is_active == True,
    )
    if target_supplier_id:
        prev_active = prev_active.filter(LegalDocument.target_supplier_id == target_supplier_id)
    else:
        prev_active = prev_active.filter(LegalDocument.is_generic == True)
    for prev in prev_active.all():
        prev.is_active = False

    # Upload PDF to R2
    from app.services.legal_storage import save_legal_doc
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        object_key = await asyncio.to_thread(
            save_legal_doc, tmp_path, doc_type, new_version, target_supplier_id
        )
    finally:
        os.unlink(tmp_path)

    doc = LegalDocument(
        type=doc_type,
        version=new_version,
        title=title,
        content=content,
        file_url=object_key,
        file_size=len(contents),
        uploaded_by=admin.id,
        is_generic=is_generic,
        target_supplier_id=target_supplier_id,
        company_id=company_id,
        is_active=True,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    logger.info(f"Legal document created: {doc_type} v{new_version} by admin {admin.id}")
    return doc


@router.get("/suppliers/legal-documents/{doc_id}/download")
async def download_legal_document(
    doc_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Get signed download URL for a legal document PDF (ADMIN only)."""
    doc = db.query(LegalDocument).get(doc_id)
    if not doc:
        raise HTTPException(404, detail="Document not found")
    if not doc.file_url:
        raise HTTPException(404, detail="No PDF file associated with this document")

    # If file_url is a public URL (v1 migration), return directly
    if doc.file_url.startswith("http"):
        return {"url": doc.file_url}

    # Otherwise generate signed R2 URL
    from app.services.legal_storage import get_legal_doc_url
    url = get_legal_doc_url(doc.file_url)
    return {"url": url}


@router.delete("/suppliers/legal-documents/{doc_id}")
async def deactivate_legal_document(
    doc_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Soft-delete a legal document by setting is_active=False (ADMIN only)."""
    doc = db.query(LegalDocument).get(doc_id)
    if not doc:
        raise HTTPException(404, detail="Document not found")

    doc.is_active = False
    db.commit()
    logger.info(f"Legal document deactivated: {doc.type} v{doc.version} by admin {admin.id}")
    return {"message": "Document deactivated"}


@router.get("/suppliers/{supplier_id}/documents", response_model=SupplierDocumentsResponse)
async def get_supplier_documents(
    supplier_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Get pending + accepted documents for a specific supplier (ADMIN only)."""
    supplier = db.query(Supplier).get(supplier_id)
    if not supplier:
        raise HTTPException(404, detail="Supplier not found")

    pending = get_pending_documents(supplier, db)
    accepted = get_accepted_documents(supplier, db)

    return SupplierDocumentsResponse(
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        is_influencer=supplier.oc_id is not None,
        pending=[PendingDocumentResponse(
            id=d.id, type=d.type, title=d.title, version=d.version
        ) for d in pending],
        accepted=[AcceptedDocumentResponse(**a) for a in accepted],
    )


@router.post("/suppliers/legal-documents/extract-text")
@limiter.limit("10/hour")
async def extract_legal_document_text(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Extract text from a legal document PDF using Claude AI and return structured HTML.
    For phase 2 admin UI — endpoint ready, no frontend yet.
    """
    contents = await file.read()
    validate_pdf_bytes(contents, max_size=MAX_SUPPLIER_PDF_SIZE)

    import anthropic
    import base64

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = (
        "Extrae el texto completo de este documento legal. "
        "Devuélvelo en HTML estructurado con las siguientes clases CSS del portal:\n"
        '- h3: class="text-zinc-100 font-semibold text-sm mb-2"\n'
        '- p: class="text-zinc-400 text-xs leading-relaxed mb-3"\n'
        '- ul: class="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1"\n'
        '- strong dentro de listas: class="text-zinc-300"\n'
        "No inventes contenido, solo extrae lo que hay en el documento. "
        "Responde SOLO con el HTML, sin markdown ni bloques de código."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.b64encode(contents).decode("utf-8"),
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )

    html_content = response.content[0].text
    return {"html": html_content}


# ============================================
# PORTAL ENDPOINTS: /portal/documents
# ============================================

@router.get("/portal/pending-documents", response_model=list[PendingDocumentResponse])
async def portal_pending_documents(
    db: Session = Depends(get_db),
    supplier: Supplier = Depends(get_current_active_supplier),
):
    """Get documents the supplier still needs to accept."""
    pending = get_pending_documents(supplier, db)
    return [PendingDocumentResponse(
        id=d.id, type=d.type, title=d.title, version=d.version
    ) for d in pending]


@router.get("/portal/my-documents", response_model=MyDocumentsResponse)
async def portal_my_documents(
    db: Session = Depends(get_db),
    supplier: Supplier = Depends(get_current_active_supplier),
):
    """Get all documents: pending + accepted."""
    pending = get_pending_documents(supplier, db)
    accepted = get_accepted_documents(supplier, db)

    return MyDocumentsResponse(
        pending=[PendingDocumentResponse(
            id=d.id, type=d.type, title=d.title, version=d.version
        ) for d in pending],
        accepted=[AcceptedDocumentResponse(**a) for a in accepted],
    )


@router.get("/portal/legal-document/{doc_id}", response_model=LegalDocumentDetailResponse)
async def portal_get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    supplier: Supplier = Depends(get_current_active_supplier),
):
    """Get document details including HTML content for the modal."""
    doc = db.query(LegalDocument).get(doc_id)
    if not doc or not doc.is_active:
        raise HTTPException(404, detail="Document not found")

    # Verify this document applies to this supplier
    applicable = get_applicable_documents(supplier, db)
    if doc.id not in [d.id for d in applicable]:
        raise HTTPException(403, detail="This document does not apply to you")

    return doc


@router.get("/portal/legal-document/{doc_id}/download")
async def portal_download_document(
    doc_id: int,
    db: Session = Depends(get_db),
    supplier: Supplier = Depends(get_current_active_supplier),
):
    """Get signed download URL for document PDF (supplier)."""
    doc = db.query(LegalDocument).get(doc_id)
    if not doc or not doc.is_active:
        raise HTTPException(404, detail="Document not found")
    if not doc.file_url:
        raise HTTPException(404, detail="No PDF file for this document")

    # Verify this document applies to this supplier
    applicable = get_applicable_documents(supplier, db)
    if doc.id not in [d.id for d in applicable]:
        raise HTTPException(403, detail="This document does not apply to you")

    if doc.file_url.startswith("http"):
        return {"url": doc.file_url}

    from app.services.legal_storage import get_legal_doc_url
    url = get_legal_doc_url(doc.file_url)
    return {"url": url}


@router.post("/portal/accept-document/{doc_id}")
async def portal_accept_document(
    request: Request,
    doc_id: int,
    db: Session = Depends(get_db),
    supplier: Supplier = Depends(get_current_active_supplier),
):
    """Accept a legal document. Creates acceptance record with timestamp + IP."""
    doc = db.query(LegalDocument).get(doc_id)
    if not doc or not doc.is_active:
        raise HTTPException(404, detail="Document not found")

    # Verify this document applies to this supplier
    applicable = get_applicable_documents(supplier, db)
    if doc.id not in [d.id for d in applicable]:
        raise HTTPException(403, detail="This document does not apply to you")

    # Check not already accepted
    existing = db.query(SupplierDocumentAcceptance).filter_by(
        supplier_id=supplier.id, document_id=doc.id
    ).first()
    if existing:
        raise HTTPException(409, detail="Document already accepted")

    acceptance = SupplierDocumentAcceptance(
        supplier_id=supplier.id,
        document_id=doc.id,
        accepted_at=datetime.now(timezone.utc),
        ip_address=_get_client_ip(request),
    )
    db.add(acceptance)
    db.commit()

    logger.info(f"Supplier {supplier.id} accepted document {doc.id} ({doc.type} v{doc.version})")
    return {"message": "Document accepted", "document_id": doc.id, "type": doc.type}
