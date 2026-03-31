import logging
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import update
from typing import List
import asyncio
import os, json
from pathlib import Path
from datetime import datetime

from config.database import get_db
from config.constants import MATH_TOLERANCE, MIN_AI_CONFIDENCE
from app.models import schemas
from app.models.database import User, Project, Ticket
from app.services.auth import get_current_active_user
from app.services.permissions import can_access_project
from app.services.claude_ai import extract_ticket_data
from app.services.cloudinary_service import upload_ticket_file
from app.services.exchange_rate import get_historical_exchange_rate
from app.services.geographic_classifier import classify_geography
# VULN-004/005: Integrar validadores
from app.services.validators import validate_file_upload, sanitize_filename

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["Tickets"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/{project_id}/upload", response_model=schemas.TicketUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_ticket(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # VULN-004/005: Usar validate_file_upload en lugar de validación manual de content_type
    logger.info(f"Upload ticket: filename='{file.filename}', content_type='{file.content_type}', size={file.size}")
    await validate_file_upload(file)

    # Leer contenido para hash + guardar temp
    file_contents = await file.read()
    file_hash = hashlib.sha256(file_contents).hexdigest()
    await file.seek(0)

    # 1. Detección duplicado por hash — BLOQUEA (antes de IA = ahorra tokens)
    existing = db.query(Ticket).filter(
        Ticket.project_id == project_id,
        Ticket.file_hash == file_hash
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "duplicate_hash",
                "ticket_id": existing.id,
                "message": f"Este archivo ya fue subido anteriormente (ticket #{existing.id})"
            }
        )

    # VULN-004/005: Usar sanitize_filename para el nombre del archivo temporal
    safe_filename = sanitize_filename(file.filename)
    temp_path = UPLOAD_DIR / f"temp_{current_user.id}_{safe_filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(file_contents)

    try:
        # PERF-M1: Offload Cloudinary upload (2-5s) al thread pool
        cloudinary_result = await asyncio.to_thread(upload_ticket_file, str(temp_path), file.filename, project_id, project.creative_code)

        # 2. Extraer datos con Claude AI (usando primera página/imagen)
        ai_file_path = str(temp_path)
        ai_mime = file.content_type

        # PERF-M1: Offload AI extraction (3-10s) al thread pool
        extracted_data = await asyncio.to_thread(extract_ticket_data, ai_file_path, ai_mime, file.filename)

        # 3. Procesar moneda extranjera
        is_foreign = extracted_data.get("is_foreign", False) if "error" not in extracted_data else False
        currency = extracted_data.get("currency", "EUR")
        country_code = extracted_data.get("country_code", "ES")
        geo_classification = classify_geography(country_code)

        exchange_rate = None
        exchange_rate_date = None
        foreign_amount = None
        foreign_total = None
        foreign_tax_amount = None
        foreign_tax_eur = None

        if is_foreign and currency != "EUR":
            try:
                date_str = extracted_data.get("date", "")
                if date_str and "/" in date_str:
                    day, month, year = date_str.split("/")
                    invoice_date = datetime(int(year), int(month), int(day)).date()
                    # PERF-M1: Offload exchange rate API call al thread pool
                    exchange_rate = await asyncio.to_thread(get_historical_exchange_rate, currency, "EUR", invoice_date)
                    if exchange_rate:
                        exchange_rate_date = invoice_date
                        foreign_amount = extracted_data.get("foreign_amount") or extracted_data.get("base_amount", 0.0)
                        foreign_total = extracted_data.get("foreign_total") or extracted_data.get("final_total", 0.0)
                        foreign_tax_amount = extracted_data.get("foreign_tax_amount") or extracted_data.get("iva_amount", 0.0)
                        if foreign_tax_amount:
                            foreign_tax_eur = round(foreign_tax_amount * exchange_rate, 2)
                        # Recalcular importes EUR desde divisa original × tasa cambio
                        extracted_data["base_amount"] = round(foreign_amount * exchange_rate, 2) if foreign_amount else 0.0
                        extracted_data["iva_amount"] = round(foreign_tax_amount * exchange_rate, 2) if foreign_tax_amount else 0.0
                        extracted_data["total_with_iva"] = round(extracted_data["base_amount"] + extracted_data["iva_amount"], 2)
                        extracted_data["final_total"] = round(foreign_total * exchange_rate, 2) if foreign_total else 0.0
            except Exception as e:
                logger.warning(f"Error tasa cambio: {str(e)}")
        elif is_foreign and currency == "EUR":
            foreign_amount = extracted_data.get("base_amount", 0.0)
            foreign_total = extracted_data.get("final_total", 0.0)
            foreign_tax_amount = extracted_data.get("iva_amount", 0.0)
            foreign_tax_eur = extracted_data.get("iva_amount", 0.0)
            exchange_rate = 1.0

        # 4. Detección duplicado por invoice_number — WARNING (deja pasar)
        duplicate_invoice_warning = None
        invoice_number = extracted_data.get("invoice_number") if "error" not in extracted_data else None
        if invoice_number:
            dup_invoice = db.query(Ticket).filter(
                Ticket.project_id == project_id,
                Ticket.invoice_number == invoice_number
            ).first()
            if dup_invoice:
                duplicate_invoice_warning = {
                    "ticket_id": dup_invoice.id,
                    "invoice_number": invoice_number
                }

        # 5. Crear ticket
        if "error" in extracted_data:
            ticket = Ticket(
                project_id=project_id,
                file_path=cloudinary_result["url"],
                file_name=file.filename,
                file_pages=json.dumps(cloudinary_result.get("pages", [])),
                pdf_url=cloudinary_result.get("pdf_url"),
                file_hash=file_hash,
                date="", provider="Error en extracción",
                base_amount=0.0, iva_amount=0.0, iva_percentage=0.0,
                total_with_iva=0.0, final_total=0.0,
                notes="Error en extracción IA",
                type="ticket", is_reviewed=False, is_foreign=False, currency="EUR"
            )
        else:
            # T1/T2/T3: Validaciones post-IA
            ai_warnings = []

            # T1: Validación matemática (±0.02€)
            base = extracted_data.get("base_amount", 0.0) or 0.0
            iva = extracted_data.get("iva_amount", 0.0) or 0.0
            irpf = extracted_data.get("irpf_amount", 0.0) or 0.0
            final = extracted_data.get("final_total", 0.0) or 0.0
            expected = round(base + iva - irpf, 2)
            if final > 0 and abs(expected - final) > MATH_TOLERANCE:
                ai_warnings.append(f"Incoherencia matemática: base({base}) + IVA({iva}) - IRPF({irpf}) = {expected}, pero total = {final}")

            # T2: Confidence threshold
            confidence = extracted_data.get("confidence", 1.0) or 1.0
            if confidence < MIN_AI_CONFIDENCE:
                ai_warnings.append(f"Baja confianza IA: {confidence:.0%}")

            # T3: Campos obligatorios
            if not extracted_data.get("provider"):
                ai_warnings.append("Proveedor no detectado")
            if not extracted_data.get("date"):
                ai_warnings.append("Fecha no detectada")
            if not extracted_data.get("final_total"):
                ai_warnings.append("Total no detectado")

            ticket = Ticket(
                project_id=project_id,
                file_path=cloudinary_result["url"],
                file_name=file.filename,
                file_pages=json.dumps(cloudinary_result.get("pages", [])),
                pdf_url=cloudinary_result.get("pdf_url"),
                file_hash=file_hash,
                date=extracted_data.get("date", ""),
                provider=extracted_data.get("provider", ""),
                invoice_number=extracted_data.get("invoice_number"),
                base_amount=extracted_data.get("base_amount", 0.0),
                iva_amount=extracted_data.get("iva_amount", 0.0),
                iva_percentage=extracted_data.get("iva_percentage", 0.0),
                total_with_iva=extracted_data.get("total_with_iva", 0.0),
                irpf_percentage=extracted_data.get("irpf_percentage", 0.0),
                irpf_amount=extracted_data.get("irpf_amount", 0.0),
                final_total=extracted_data.get("final_total", 0.0),
                type=extracted_data.get("type", "ticket"),
                phone=extracted_data.get("phone"),
                email=extracted_data.get("email"),
                contact_name=extracted_data.get("contact_name"),
                is_foreign=is_foreign,
                currency=currency,
                country_code=country_code,
                geo_classification=geo_classification,
                foreign_amount=foreign_amount,
                foreign_total=foreign_total,
                foreign_tax_amount=foreign_tax_amount,
                foreign_tax_eur=foreign_tax_eur,
                exchange_rate=exchange_rate,
                exchange_rate_date=exchange_rate_date,
                ia_warnings="\n".join(ai_warnings) if ai_warnings else None,
                is_reviewed=False
            )

        db.add(ticket)
        # T5: Error de IA (final_total=0) → no sumar al proyecto
        if "error" not in extracted_data:
            db.execute(update(Project).where(Project.id == project_id).values(
                tickets_count=Project.tickets_count + 1,
                total_amount=Project.total_amount + ticket.final_total,
            ))
        try:
            db.commit()
        except Exception:
            db.rollback()
            # LOGIC-M4: Si falla el commit a BD, limpiar archivos ya subidos a Cloudinary
            try:
                from app.services.cloudinary_service import delete_ticket_files
                delete_ticket_files(
                    json.dumps(cloudinary_result.get("pages", [])),
                    cloudinary_result.get("pdf_url")
                )
            except Exception as e:
                logger.error(f"Cloudinary cleanup failed after DB rollback: {e}")
            raise
        db.refresh(ticket)
        return {
            "ticket": ticket,
            "duplicate_invoice_warning": duplicate_invoice_warning
        }

    except HTTPException:
        raise  # Re-raise HTTPExceptions from validators as-is
    except Exception as e:
        # VULN-006: Logear error real, devolver genérico
        logger.error(f"Error procesando ticket: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al procesar ticket")
    finally:
        if temp_path.exists():
            temp_path.unlink()


@router.get("/{project_id}/tickets", response_model=List[schemas.TicketResponse])
async def get_project_tickets(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return db.query(Ticket).filter(Ticket.project_id == project_id).all()


@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    ticket = db.query(Ticket).options(joinedload(Ticket.project)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    project = ticket.project
    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return ticket


@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
async def update_ticket(ticket_id: int, ticket_update: schemas.TicketUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    ticket = db.query(Ticket).options(joinedload(Ticket.project)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    project = ticket.project
    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    old_total = ticket.final_total
    was_error = (ticket.provider == "Error en extracción" and old_total == 0.0)
    update_data = ticket_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)
    if "final_total" in update_data:
        diff = ticket.final_total - old_total
        # T5: Si era ticket de error (no sumado al proyecto), sumar count + total completo
        count_diff = 1 if was_error and ticket.final_total > 0 else 0
        db.execute(update(Project).where(Project.id == ticket.project_id).values(
            tickets_count=Project.tickets_count + count_diff,
            total_amount=Project.total_amount + diff,
        ))
    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    ticket = db.query(Ticket).options(joinedload(Ticket.project)).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    project = ticket.project
    if not can_access_project(current_user, project, db):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 1. BORRAR ARCHIVOS DE CLOUDINARY PRIMERO
    try:
        from app.services.cloudinary_service import delete_ticket_files
        delete_ticket_files(ticket.file_pages, ticket.pdf_url)
        logger.info(f"Archivos de Cloudinary eliminados para ticket {ticket_id}")
    except Exception as e:
        logger.warning(f"Error eliminando archivos de Cloudinary: {str(e)}")
        # Continuar aunque falle (evitar bloqueo)

    # 2. BORRAR DE BASE DE DATOS
    # T5: Si era ticket de error (nunca se sumó), no restar count
    is_error_ticket = (ticket.provider == "Error en extracción" and ticket.final_total == 0.0)
    db.execute(update(Project).where(Project.id == ticket.project_id).values(
        tickets_count=Project.tickets_count - (0 if is_error_ticket else 1),
        total_amount=Project.total_amount - ticket.final_total,
    ))
    db.delete(ticket)
    db.commit()
    return None
