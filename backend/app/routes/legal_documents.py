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
from app.models.database import User, UserRole, OCPrefix
from app.models.legal_documents import LegalDocument, SupplierDocumentAcceptance, LegalDocumentType
from app.models.suppliers import Supplier, SupplierOC, SupplierInvitation, SupplierInvoice
from app.models.supplier_schemas import (
    LegalDocumentResponse, LegalDocumentDetailResponse,
    PendingDocumentResponse, AcceptedDocumentResponse,
    MyDocumentsResponse, SupplierDocumentsResponse,
    DocumentStatsResponse, PendingSupplierResponse,
    InfluencerContractInfo, RegistrationDocumentResponse,
    BossInfluencerDocStatus,
)
from app.services.auth import get_current_admin_user, get_current_admin_or_boss_user
from app.services.permissions import get_user_company_ids
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
    """Return all active legal documents that apply to a given supplier.

    General supplier (oc_id IS NULL): PRIVACY + TERMS + SUPPLIER_CONTRACT (generic or custom).
    Influencer (oc_id IS NOT NULL):   PRIVACY + TERMS + INFLUENCER_CONTRACT (generic or custom) + AUTOCONTROL.
    """
    is_influencer = supplier.oc_id is not None
    all_active = db.query(LegalDocument).filter(LegalDocument.is_active == True).all()

    has_custom_inf = any(
        d.type == "INFLUENCER_CONTRACT" and d.target_supplier_id == supplier.id
        for d in all_active
    )
    has_custom_sup = any(
        d.type == "SUPPLIER_CONTRACT" and d.target_supplier_id == supplier.id
        for d in all_active
    )

    result = []
    for doc in all_active:
        if doc.type == "PRIVACY":
            if doc.is_generic:
                result.append(doc)
        elif doc.type == "TERMS":
            if doc.is_generic:
                result.append(doc)
        elif doc.type == "SUPPLIER_CONTRACT":
            if is_influencer:
                continue
            if doc.is_generic and has_custom_sup:
                continue
            if doc.target_supplier_id and doc.target_supplier_id != supplier.id:
                continue
            result.append(doc)
        elif doc.type == "INFLUENCER_CONTRACT":
            if not is_influencer:
                continue
            if doc.is_generic and has_custom_inf:
                continue
            if doc.target_supplier_id and doc.target_supplier_id != supplier.id:
                continue
            result.append(doc)
        elif doc.type == "AUTOCONTROL":
            if is_influencer and doc.is_generic:
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


def get_boss_influencer_ids(user: User, db: Session) -> set[int]:
    """Return supplier IDs of influencers whose OC prefix belongs to the BOSS's companies.
    Uses SQL LIKE for efficient matching instead of loading all OCs into Python."""
    boss_cids = get_user_company_ids(user, db)
    if not boss_cids:
        return set()

    # Get active OC prefixes for boss's companies
    prefixes = db.query(OCPrefix.prefix).filter(
        OCPrefix.company_id.in_(boss_cids),
        OCPrefix.active == True,
    ).all()
    prefix_strings = [p[0] for p in prefixes]
    if not prefix_strings:
        return set()

    # Find SupplierOC IDs whose oc_number starts with any of these prefixes (SQL LIKE)
    from sqlalchemy import or_
    oc_filters = [SupplierOC.oc_number.like(f"{p}%") for p in prefix_strings]
    matching_oc_ids = [
        row[0] for row in db.query(SupplierOC.id).filter(or_(*oc_filters)).all()
    ]
    if not matching_oc_ids:
        return set()

    # Find supplier IDs with these OCs
    return set(
        row[0] for row in db.query(Supplier.id).filter(
            Supplier.oc_id.in_(matching_oc_ids),
            Supplier.is_active == True,
        ).all()
    )


# ============================================
# ADMIN ENDPOINTS: /suppliers/legal-documents
# ============================================

@router.get("/suppliers/legal-documents", response_model=list[LegalDocumentResponse])
async def list_legal_documents(
    type: Optional[str] = Query(None, description="Filter by type: PRIVACY, TERMS, SUPPLIER_CONTRACT, INFLUENCER_CONTRACT, AUTOCONTROL"),
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
    doc_type: str = Query(..., description="PRIVACY, TERMS, SUPPLIER_CONTRACT, INFLUENCER_CONTRACT, AUTOCONTROL"),
    title: str = Query(..., max_length=200),
    content: str = Query(..., description="HTML content for the scroll-to-accept modal"),
    is_generic: bool = Query(True),
    target_supplier_id: Optional[int] = Query(None),
    company_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_or_boss_user),
):
    """Upload a new legal document PDF + HTML content (ADMIN or BOSS for INFLUENCER_CONTRACT/AUTOCONTROL)."""
    doc_type = doc_type.upper()
    if doc_type not in [t.value for t in LegalDocumentType]:
        raise HTTPException(400, detail=f"Invalid type. Must be one of: {[t.value for t in LegalDocumentType]}")

    # BOSS: only INFLUENCER_CONTRACT and AUTOCONTROL, only for their company's influencers
    if admin.role == UserRole.BOSS:
        if doc_type not in ("INFLUENCER_CONTRACT", "AUTOCONTROL"):
            raise HTTPException(403, detail="Only INFLUENCER_CONTRACT and AUTOCONTROL documents allowed")
        if target_supplier_id:
            boss_inf_ids = get_boss_influencer_ids(admin, db)
            if target_supplier_id not in boss_inf_ids:
                raise HTTPException(403, detail="This influencer is not in your company")

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


@router.get("/suppliers/legal-documents/stats", response_model=list[DocumentStatsResponse])
async def legal_document_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin_or_boss_user),
):
    """Stats per active generic document. BOSS only sees INFLUENCER_CONTRACT + AUTOCONTROL for their company."""
    from sqlalchemy import func as sqlfunc

    is_boss = user.role == UserRole.BOSS

    # Only generic documents (not personalized per-supplier)
    active_docs = db.query(LegalDocument).filter(
        LegalDocument.is_active == True,
        LegalDocument.target_supplier_id == None,
    ).all()
    if not active_docs:
        return []

    # BOSS: only INFLUENCER_CONTRACT and AUTOCONTROL
    if is_boss:
        active_docs = [d for d in active_docs if d.type in ("INFLUENCER_CONTRACT", "AUTOCONTROL")]

    # Count all active suppliers, split by influencer/general
    all_suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    influencer_ids = {s.id for s in all_suppliers if s.oc_id is not None}
    general_ids = {s.id for s in all_suppliers if s.oc_id is None}
    all_supplier_ids = influencer_ids | general_ids

    # BOSS: narrow to their company's influencers
    if is_boss:
        boss_inf_ids = get_boss_influencer_ids(user, db)
        influencer_ids = influencer_ids & boss_inf_ids

    # Pre-fetch all acceptance counts per document
    acceptance_counts = dict(
        db.query(SupplierDocumentAcceptance.document_id, sqlfunc.count(SupplierDocumentAcceptance.id))
        .filter(SupplierDocumentAcceptance.document_id.in_([d.id for d in active_docs]))
        .group_by(SupplierDocumentAcceptance.document_id)
        .all()
    )

    result = []
    for doc in active_docs:
        if doc.type in ("PRIVACY", "TERMS"):
            total = len(all_supplier_ids)
        elif doc.type == "SUPPLIER_CONTRACT":
            total = len(general_ids)
        elif doc.type in ("INFLUENCER_CONTRACT", "AUTOCONTROL"):
            total = len(influencer_ids)
        else:
            total = len(all_supplier_ids)

        result.append(DocumentStatsResponse(
            id=doc.id,
            type=doc.type,
            title=doc.title,
            version=doc.version,
            created_at=doc.created_at,
            total_applicable=total,
            total_accepted=acceptance_counts.get(doc.id, 0),
        ))

    return result


@router.get("/suppliers/legal-documents/{doc_id}/pending-suppliers", response_model=list[PendingSupplierResponse])
async def legal_document_pending_suppliers(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin_or_boss_user),
):
    """List suppliers who have NOT accepted a specific document. BOSS filtered by company."""
    doc = db.query(LegalDocument).get(doc_id)
    if not doc or not doc.is_active:
        raise HTTPException(404, detail="Document not found")

    # BOSS: can only view INFLUENCER_CONTRACT/AUTOCONTROL pending lists
    is_boss = user.role == UserRole.BOSS
    if is_boss and doc.type not in ("INFLUENCER_CONTRACT", "AUTOCONTROL"):
        raise HTTPException(403, detail="Not enough permissions")

    # Determine applicable suppliers
    all_suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()

    if doc.target_supplier_id:
        applicable = [s for s in all_suppliers if s.id == doc.target_supplier_id]
    elif doc.type in ("PRIVACY", "TERMS"):
        applicable = all_suppliers
    elif doc.type == "SUPPLIER_CONTRACT":
        applicable = [s for s in all_suppliers if s.oc_id is None]
    elif doc.type in ("INFLUENCER_CONTRACT", "AUTOCONTROL"):
        applicable = [s for s in all_suppliers if s.oc_id is not None]
    else:
        applicable = all_suppliers

    # BOSS: narrow to their company's influencers
    if is_boss:
        boss_inf_ids = get_boss_influencer_ids(user, db)
        applicable = [s for s in applicable if s.id in boss_inf_ids]

    if not applicable:
        return []

    # Get who already accepted
    accepted_supplier_ids = set(
        row[0] for row in db.query(SupplierDocumentAcceptance.supplier_id).filter(
            SupplierDocumentAcceptance.document_id == doc_id,
        ).all()
    )

    # Batch-load OC numbers to avoid N+1
    oc_ids = [s.oc_id for s in applicable if s.oc_id]
    ocs = {oc.id: oc for oc in db.query(SupplierOC).filter(SupplierOC.id.in_(oc_ids)).all()} if oc_ids else {}

    pending = []
    for s in applicable:
        if s.id in accepted_supplier_ids:
            continue
        oc = ocs.get(s.oc_id)
        pending.append(PendingSupplierResponse(
            id=s.id,
            name=s.name,
            nif_cif=s.nif_cif,
            oc_number=oc.oc_number if oc else None,
            created_at=s.created_at,
            last_activity=s.updated_at,
        ))

    return pending


@router.get("/suppliers/legal-documents/influencers", response_model=list[InfluencerContractInfo])
async def legal_document_influencers(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin_or_boss_user),
):
    """List all influencers with their current contract version info. BOSS filtered by company."""
    influencers = db.query(Supplier).filter(
        Supplier.is_active == True,
        Supplier.oc_id != None,
    ).all()

    if not influencers:
        return []

    # BOSS: filter to their company's influencers
    if user.role == UserRole.BOSS:
        boss_inf_ids = get_boss_influencer_ids(user, db)
        influencers = [s for s in influencers if s.id in boss_inf_ids]
        if not influencers:
            return []

    # Get active INFLUENCER_CONTRACT documents
    active_contracts = db.query(LegalDocument).filter(
        LegalDocument.type == "INFLUENCER_CONTRACT",
        LegalDocument.is_active == True,
    ).all()

    generic_contract = next((d for d in active_contracts if d.is_generic), None)
    custom_contracts = {d.target_supplier_id: d for d in active_contracts if d.target_supplier_id}

    # Get OC numbers in batch
    oc_ids = [s.oc_id for s in influencers if s.oc_id]
    ocs = {oc.id: oc for oc in db.query(SupplierOC).filter(SupplierOC.id.in_(oc_ids)).all()} if oc_ids else {}

    result = []
    for s in influencers:
        oc = ocs.get(s.oc_id)
        custom = custom_contracts.get(s.id)
        if custom:
            contract_version = custom.version
            contract_type = "custom"
            contract_doc_id = custom.id
        elif generic_contract:
            contract_version = generic_contract.version
            contract_type = "generic"
            contract_doc_id = generic_contract.id
        else:
            contract_version = None
            contract_type = None
            contract_doc_id = None

        result.append(InfluencerContractInfo(
            id=s.id,
            name=s.name,
            nif_cif=s.nif_cif,
            oc_number=oc.oc_number if oc else None,
            contract_version=contract_version,
            contract_type=contract_type,
            contract_doc_id=contract_doc_id,
        ))

    return result


@router.get("/suppliers/legal-documents/general-suppliers", response_model=list[InfluencerContractInfo])
async def legal_document_general_suppliers(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """List all general suppliers (no OC) with their current SUPPLIER_CONTRACT version info. ADMIN only."""
    suppliers = db.query(Supplier).filter(
        Supplier.is_active == True,
        Supplier.oc_id == None,
    ).all()

    if not suppliers:
        return []

    active_contracts = db.query(LegalDocument).filter(
        LegalDocument.type == "SUPPLIER_CONTRACT",
        LegalDocument.is_active == True,
    ).all()

    generic_contract = next((d for d in active_contracts if d.is_generic), None)
    custom_contracts = {d.target_supplier_id: d for d in active_contracts if d.target_supplier_id}

    result = []
    for s in suppliers:
        custom = custom_contracts.get(s.id)
        if custom:
            contract_version = custom.version
            contract_type = "custom"
            contract_doc_id = custom.id
        elif generic_contract:
            contract_version = generic_contract.version
            contract_type = "generic"
            contract_doc_id = generic_contract.id
        else:
            contract_version = None
            contract_type = None
            contract_doc_id = None

        result.append(InfluencerContractInfo(
            id=s.id,
            name=s.name,
            nif_cif=s.nif_cif,
            oc_number=None,
            contract_version=contract_version,
            contract_type=contract_type,
            contract_doc_id=contract_doc_id,
        ))

    return result


@router.get("/suppliers/legal-documents/boss-contracts", response_model=list[BossInfluencerDocStatus])
async def boss_contracts_view(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin_or_boss_user),
):
    """Full document status for BOSS's influencers. ADMIN sees all influencers."""
    influencers = db.query(Supplier).filter(
        Supplier.is_active == True,
        Supplier.oc_id != None,
    ).all()

    if user.role == UserRole.BOSS:
        boss_inf_ids = get_boss_influencer_ids(user, db)
        influencers = [s for s in influencers if s.id in boss_inf_ids]

    if not influencers:
        return []

    # Batch-load OCs
    oc_ids = [s.oc_id for s in influencers if s.oc_id]
    ocs = {oc.id: oc for oc in db.query(SupplierOC).filter(SupplierOC.id.in_(oc_ids)).all()} if oc_ids else {}

    # Get all active generic documents by type
    active_generic = db.query(LegalDocument).filter(
        LegalDocument.is_active == True, LegalDocument.is_generic == True,
    ).all()
    doc_by_type = {}
    for d in active_generic:
        doc_by_type[d.type] = d

    # Get custom contracts (per-influencer INFLUENCER_CONTRACT overrides)
    supplier_ids = [s.id for s in influencers]
    custom_contracts = {
        d.target_supplier_id: d
        for d in db.query(LegalDocument).filter(
            LegalDocument.type == "INFLUENCER_CONTRACT",
            LegalDocument.is_active == True,
            LegalDocument.target_supplier_id.in_(supplier_ids),
        ).all()
    }

    # Batch-load all acceptances for these suppliers
    all_acceptances = db.query(SupplierDocumentAcceptance).filter(
        SupplierDocumentAcceptance.supplier_id.in_(supplier_ids),
    ).all()
    # Map: (supplier_id, document_id) → True
    accepted_set = {(a.supplier_id, a.document_id) for a in all_acceptances}

    result = []
    for s in influencers:
        oc = ocs.get(s.oc_id)
        custom = custom_contracts.get(s.id)
        contract_doc = custom or doc_by_type.get("INFLUENCER_CONTRACT")
        autocontrol_doc = doc_by_type.get("AUTOCONTROL")
        privacy_doc = doc_by_type.get("PRIVACY")
        terms_doc = doc_by_type.get("TERMS")

        result.append(BossInfluencerDocStatus(
            id=s.id,
            name=s.name,
            nif_cif=s.nif_cif,
            oc_number=oc.oc_number if oc else None,
            contract_version=contract_doc.version if contract_doc else None,
            contract_type="custom" if custom else "generic" if contract_doc else None,
            contract_accepted=(s.id, contract_doc.id) in accepted_set if contract_doc else False,
            autocontrol_version=autocontrol_doc.version if autocontrol_doc else None,
            autocontrol_accepted=(s.id, autocontrol_doc.id) in accepted_set if autocontrol_doc else False,
            privacy_version=privacy_doc.version if privacy_doc else None,
            privacy_accepted=(s.id, privacy_doc.id) in accepted_set if privacy_doc else False,
            terms_version=terms_doc.version if terms_doc else None,
            terms_accepted=(s.id, terms_doc.id) in accepted_set if terms_doc else False,
        ))

    return result


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


# ============================================
# REGISTRATION DOCUMENTS (token-based, no auth)
# ============================================

@router.get("/portal/registration-documents", response_model=list[RegistrationDocumentResponse])
async def portal_registration_documents(
    token: str = Query(...),
    is_influencer: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Get legal documents for registration step 4.
    Uses invitation token (not supplier auth — supplier doesn't exist yet).
    Returns documents with HTML content for scroll-to-accept modals.
    """
    from datetime import timedelta

    # Validate token without consuming it
    invitation = db.query(SupplierInvitation).filter(
        SupplierInvitation.token == token,
        SupplierInvitation.used_at == None,
        SupplierInvitation.expires_at > datetime.now(timezone.utc),
    ).first()
    if not invitation:
        raise HTTPException(400, detail="Invalid or expired token")

    # Get all active documents
    all_active = db.query(LegalDocument).filter(LegalDocument.is_active == True).all()

    # Check for personalized contract linked to this invitation
    # The contract type depends on whether this invitation is for an influencer or general supplier
    contract_type_for_invite = "INFLUENCER_CONTRACT" if is_influencer else "SUPPLIER_CONTRACT"
    custom_contract = next(
        (d for d in all_active
         if d.type == contract_type_for_invite and d.target_invitation_id == invitation.id),
        None,
    )
    has_custom = custom_contract is not None

    result = []
    for doc in all_active:
        if doc.type == "PRIVACY" and doc.is_generic:
            result.append(doc)
        elif doc.type == "TERMS" and doc.is_generic:
            result.append(doc)
        elif doc.type == "SUPPLIER_CONTRACT":
            if is_influencer:
                continue
            if doc.is_generic and has_custom:
                continue  # Skip generic if custom exists for this invitation
            if doc.target_supplier_id:
                continue  # Skip supplier-targeted docs (not for registration)
            if doc.target_invitation_id and doc.target_invitation_id != invitation.id:
                continue  # Skip other invitations' custom contracts
            result.append(doc)
        elif doc.type == "INFLUENCER_CONTRACT":
            if not is_influencer:
                continue
            if doc.is_generic and has_custom:
                continue
            if doc.target_supplier_id:
                continue
            if doc.target_invitation_id and doc.target_invitation_id != invitation.id:
                continue
            result.append(doc)
        elif doc.type == "AUTOCONTROL" and doc.is_generic:
            if is_influencer:
                result.append(doc)

    return [RegistrationDocumentResponse(
        id=d.id, type=d.type, title=d.title, version=d.version,
        content=d.content, file_url=d.file_url,
    ) for d in result]
