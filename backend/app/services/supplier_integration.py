"""
INT-1: Supplier invoice ↔ DAZZ Producciones project integration.

Three helpers that bridge the supplier portal with the main expense tracker:
- get_or_create_project_for_oc  — resolve OC → project (auto-create for permanent OCs)
- create_ticket_from_supplier_invoice — map approved invoice → DAZZ ticket
- delete_ticket_for_invoice — cascade-delete or void the linked ticket
"""

import logging
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import case, update
from sqlalchemy.orm import Session

from app.models.database import (
    Company, OCPrefix, Project, ProjectStatus, Ticket, TicketType,
)
from app.models.suppliers import Supplier, SupplierInvoice
from app.services.exchange_rate import get_historical_exchange_rate
from app.services.geographic_classifier import classify_geography
from app.services.supplier_ai import format_date_for_response

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Resolve OC number → Project (auto-create for permanent OCs)
# ---------------------------------------------------------------------------

def get_or_create_project_for_oc(
    db: Session,
    oc_number: str,
    admin_user,
    supplier: Supplier,
) -> Project:
    """Find the project that matches *oc_number*, or auto-create one for
    permanent OC prefixes (e.g. MGMTINT influencer talents).

    Raises HTTPException(400) when:
    - The project exists but is closed.
    - The OC belongs to a non-permanent prefix and no project exists yet.
    - The OC prefix is not recognised at all.
    """

    # 1. Try to find an existing project by creative_code
    project = db.query(Project).filter(
        Project.creative_code.ilike(oc_number)
    ).first()

    if project:
        if project.status == ProjectStatus.CERRADO:
            raise HTTPException(
                400,
                f"El proyecto {oc_number} esta cerrado. Reabrelo antes de aprobar.",
            )
        return project

    # 2. No project found — resolve OC prefix to decide what to do
    oc_lower = oc_number.lower()
    oc_prefix: OCPrefix | None = None

    if oc_lower.startswith("oc-"):
        active_prefixes = db.query(OCPrefix).filter(OCPrefix.active == True).all()
        for p in active_prefixes:
            if oc_lower.startswith(f"oc-{p.prefix.lower()}"):
                oc_prefix = p
                break

    if oc_prefix is None:
        raise HTTPException(
            400,
            f"OC no reconocido: {oc_number}. Crea el proyecto primero en DAZZ Producciones.",
        )

    if not oc_prefix.permanent_oc:
        raise HTTPException(
            400,
            f"No existe proyecto para el OC {oc_number}. Crealo primero en DAZZ Producciones.",
        )

    # 3. Permanent OC — auto-create project
    billing_company = db.query(Company).filter(
        Company.id == oc_prefix.billing_company_id
    ).first()
    billing_name = billing_company.name if billing_company else ""

    year = oc_prefix.year_format or str(datetime.now(timezone.utc).year)

    # Build client_data from supplier fiscal info
    client_parts = [supplier.name]
    if supplier.address:
        client_parts.append(supplier.address)
    if supplier.phone:
        client_parts.append(supplier.phone)
    client_data = "\n".join(client_parts)

    project = Project(
        year=year,
        send_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        creative_code=oc_number,
        company=billing_name,
        owner_company_id=oc_prefix.company_id,
        owner_id=admin_user.id,
        responsible=admin_user.username or admin_user.name,
        invoice_type=f"TALENT{year}",
        description=supplier.name,
        status=ProjectStatus.EN_CURSO,
        client_data=client_data,
        client_email=supplier.email,
        other_invoice_data=supplier.nif_cif,
    )
    db.add(project)
    db.flush()

    logger.info(
        "Auto-created project %s (id=%s) for permanent OC %s — supplier %s",
        project.creative_code, project.id, oc_number, supplier.name,
    )
    return project


# ---------------------------------------------------------------------------
# 2. Create a DAZZ Ticket from an approved supplier invoice
# ---------------------------------------------------------------------------

def create_ticket_from_supplier_invoice(
    db: Session,
    invoice: SupplierInvoice,
    supplier: Supplier,
    project: Project,
) -> Ticket:
    """Map all relevant fields from a supplier invoice into a DAZZ ticket,
    add it to the session, and atomically update the project totals.

    The caller is responsible for calling ``db.commit()``.
    """

    # Guard: never create a duplicate
    existing = db.query(Ticket.id).filter(
        Ticket.supplier_invoice_id == invoice.id
    ).first()
    if existing:
        logger.warning(
            "Ticket already exists for supplier_invoice %s (ticket %s) — skipping",
            invoice.id, existing[0],
        )
        return db.query(Ticket).filter(Ticket.id == existing[0]).first()

    ticket = Ticket(
        project_id=project.id,
        # Provider info from supplier
        provider=supplier.name,
        email=supplier.email,
        phone=supplier.phone,
        contact_name=supplier.name,
        # Invoice data
        date=format_date_for_response(invoice.date),
        invoice_number=invoice.invoice_number,
        po_notes=invoice.oc_number,
        # Amounts
        base_amount=invoice.base_amount,
        iva_amount=invoice.iva_amount,
        iva_percentage=invoice.iva_percentage,
        total_with_iva=round(invoice.base_amount + invoice.iva_amount, 2),
        irpf_percentage=invoice.irpf_percentage or 0,
        irpf_amount=invoice.irpf_amount or 0,
        final_total=invoice.final_total,
        # Currency
        currency=invoice.currency or "EUR",
        is_foreign=invoice.is_foreign or False,
        # File — reuse Cloudinary URL, no duplication
        file_path=invoice.file_url or "",
        file_name=f"{invoice.invoice_number}.pdf",
        file_pages=invoice.file_pages,
        # Status
        invoice_status="RECIBIDO",
        payment_status="PENDIENTE",
        type=TicketType.FACTURA,
        is_reviewed=True,
        # Supplier link
        from_supplier_portal=True,
        supplier_id=supplier.id,
        supplier_invoice_id=invoice.id,
        is_autoinvoice=invoice.is_autoinvoice or False,
        # Traceability
        notes="Auto: factura proveedor",
    )

    # Foreign currency conversion (same logic as tickets.py upload)
    if invoice.is_foreign and invoice.currency and invoice.currency != "EUR":
        ticket.foreign_amount = invoice.base_amount
        ticket.foreign_total = invoice.final_total
        ticket.foreign_tax_amount = invoice.iva_amount
        ticket.country_code = getattr(invoice, "country_code", None)
        ticket.geo_classification = (
            classify_geography(ticket.country_code) if ticket.country_code else "INTERNACIONAL"
        )
        rate_date = invoice.date_parsed
        if not rate_date and invoice.date:
            try:
                parts = invoice.date.split("-")
                rate_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except Exception:
                rate_date = None
        rate = get_historical_exchange_rate(invoice.currency, "EUR", rate_date)
        if rate:
            ticket.exchange_rate = rate
            ticket.exchange_rate_date = rate_date
            ticket.base_amount = round(invoice.base_amount * rate, 2)
            ticket.iva_amount = round(invoice.iva_amount * rate, 2)
            ticket.total_with_iva = round(ticket.base_amount + ticket.iva_amount, 2)
            ticket.irpf_amount = round((invoice.irpf_amount or 0) * rate, 2)
            ticket.final_total = round(invoice.final_total * rate, 2)
            ticket.foreign_tax_eur = round(invoice.iva_amount * rate, 2)
    elif invoice.is_foreign and invoice.currency == "EUR":
        # Foreign but EUR (e.g. EU country)
        ticket.foreign_amount = invoice.base_amount
        ticket.foreign_total = invoice.final_total
        ticket.foreign_tax_amount = invoice.iva_amount
        ticket.foreign_tax_eur = invoice.iva_amount
        ticket.exchange_rate = 1.0
        ticket.country_code = getattr(invoice, "country_code", None)
        ticket.geo_classification = (
            classify_geography(ticket.country_code) if ticket.country_code else "UE"
        )

    db.add(ticket)

    # Atomically update project counters (use ticket.final_total which may be EUR-converted)
    db.execute(
        update(Project)
        .where(Project.id == project.id)
        .values(
            tickets_count=Project.tickets_count + 1,
            total_amount=Project.total_amount + ticket.final_total,
        )
    )

    db.flush()

    logger.info(
        "Ticket created for supplier invoice %s (%s) -> project %s (id=%s)",
        invoice.invoice_number, invoice.final_total,
        project.creative_code, project.id,
    )
    return ticket


# ---------------------------------------------------------------------------
# 3. Delete or void the linked DAZZ ticket when a supplier invoice is removed
# ---------------------------------------------------------------------------

def delete_ticket_for_invoice(db: Session, supplier_invoice_id: int) -> None:
    """Find the DAZZ ticket linked to *supplier_invoice_id* and hard-delete it.

    The parent project totals are decremented atomically.
    The caller is responsible for calling ``db.commit()``.
    """

    ticket = db.query(Ticket).filter(
        Ticket.supplier_invoice_id == supplier_invoice_id
    ).first()

    if ticket is None:
        return

    project_id = ticket.project_id
    amount = ticket.final_total or 0

    db.delete(ticket)
    logger.info("Ticket %s deleted (cascade from supplier invoice %s)", ticket.id, supplier_invoice_id)

    # Atomically decrement project counters
    if project_id:
        db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(
                tickets_count=case(
                    (Project.tickets_count > 1, Project.tickets_count - 1),
                    else_=0,
                ),
                total_amount=case(
                    (Project.total_amount > amount, Project.total_amount - amount),
                    else_=0,
                ),
            )
        )

    db.flush()
