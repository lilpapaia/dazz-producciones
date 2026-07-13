"""
Lógica de negocio de tickets compartida entre empleados (tickets.py) y
externos (guest_share.py). FEAT-09 Fase 5.

Extraído verbatim de los handlers de tickets.py para mantener una sola fuente
de verdad. Los GUARDS (permisos, PAGADO ADMIN, from_supplier_portal, estado del
proyecto) quedan en cada endpoint — aquí solo va la mecánica de la mutación.
"""

import json
import asyncio
import hashlib
import logging
import secrets
from pathlib import Path
from datetime import datetime

from anthropic import APIStatusError, APITimeoutError, RateLimitError, APIError
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import update, case
from sqlalchemy.orm import Session

from config.constants import MATH_TOLERANCE, MIN_AI_CONFIDENCE
from app.models.database import Project, Ticket
from app.services.claude_ai import extract_ticket_data
from app.services.cloudinary_service import upload_ticket_file
from app.services.exchange_rate import get_historical_exchange_rate
from app.services.geographic_classifier import classify_geography
from app.services.validators import validate_file_upload, sanitize_filename

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def _safe_delete_cloudinary(cloudinary_result: dict | None) -> None:
    """Borra los archivos ya subidos a Cloudinary si algo falla después. No lanza."""
    if not cloudinary_result:
        return
    try:
        from app.services.cloudinary_service import delete_ticket_files
        delete_ticket_files(
            json.dumps(cloudinary_result.get("pages", [])),
            cloudinary_result.get("pdf_url"),
        )
    except Exception as e:
        logger.error(f"Cloudinary cleanup failed: {e}")


async def process_ticket_upload(
    file: UploadFile,
    project: Project,
    db: Session,
    *,
    uploaded_by_guest_name: str = None,
    guest_share_token_id: int = None,
) -> dict:
    """Procesa la subida de un ticket: validación, dedup, Cloudinary, IA, creación.

    Lógica EXACTA de tickets.upload_ticket. Devuelve
    {"ticket": Ticket, "duplicate_invoice_warning": dict|None}.
    Los campos guest se setean en el ticket creado si vienen.
    El caller ya validó permisos y estado del proyecto.
    """
    project_id = project.id

    # VULN-004/005: validación robusta (magic bytes, tamaño, MIME) en vez de manual
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

    # Nombre temporal único (token aleatorio — sirve para empleado y para guest)
    safe_filename = sanitize_filename(file.filename)
    temp_path = UPLOAD_DIR / f"temp_{secrets.token_hex(8)}_{safe_filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(file_contents)

    cloudinary_result = None
    try:
        # FIX-1: cada paso tiene su propio manejo de error con mensaje específico.
        # PERF-M1: Offload Cloudinary upload (2-5s) al thread pool
        try:
            cloudinary_result = await asyncio.to_thread(upload_ticket_file, str(temp_path), file.filename, project_id, project.creative_code)
        except Exception as e:
            logger.error(f"Error subiendo a Cloudinary: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al subir archivo al servidor. Reintenta en unos minutos")

        # 2. Extraer datos con Claude AI (usando primera página/imagen)
        ai_file_path = str(temp_path)
        ai_mime = file.content_type

        # PERF-M1: Offload AI extraction (3-10s) al thread pool
        # FIX-1: distinguir tipos de fallo de la IA para dar un mensaje útil al usuario.
        try:
            extracted_data = await asyncio.to_thread(extract_ticket_data, ai_file_path, ai_mime, file.filename)
        except RateLimitError as e:
            _safe_delete_cloudinary(cloudinary_result)
            logger.error(f"Error IA (rate limit): {str(e)}")
            raise HTTPException(status_code=500, detail="Demasiadas peticiones a la IA. Espera un momento y reintenta")
        except APITimeoutError as e:
            _safe_delete_cloudinary(cloudinary_result)
            logger.error(f"Error IA (timeout): {str(e)}")
            raise HTTPException(status_code=500, detail="La IA tardó demasiado. Reintenta en unos minutos")
        except APIStatusError as e:
            _safe_delete_cloudinary(cloudinary_result)
            logger.error(f"Error IA (status {getattr(e, 'status_code', '?')}): {str(e)}")
            if "credit balance too low" in str(e).lower():
                raise HTTPException(status_code=500, detail="Sin créditos en el servicio de IA. Contacta con el administrador")
            raise HTTPException(status_code=500, detail="Error al procesar con IA. Reintenta o contacta con el administrador")
        except APIError as e:
            _safe_delete_cloudinary(cloudinary_result)
            logger.error(f"Error IA (api): {str(e)}")
            raise HTTPException(status_code=500, detail="Error al procesar con IA. Reintenta o contacta con el administrador")

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
                date="Sin fecha", provider="Error en extracción",
                base_amount=0.0, iva_amount=0.0, iva_percentage=0.0,
                total_with_iva=0.0, final_total=0.0,
                notes="Error en extracción IA",
                type="ticket", is_reviewed=False, is_foreign=False, currency="EUR",
                uploaded_by_guest_name=uploaded_by_guest_name,
                guest_share_token_id=guest_share_token_id,
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
            if final > 0 and abs(expected - final) > max(MATH_TOLERANCE, final * 0.005):
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
                date=extracted_data.get("date") or "Sin fecha",
                provider=extracted_data.get("provider") or "Sin proveedor",
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
                is_reviewed=False,
                uploaded_by_guest_name=uploaded_by_guest_name,
                guest_share_token_id=guest_share_token_id,
            )

        db.add(ticket)
        # T5: Error de IA (final_total=0) → no sumar al proyecto
        project_update = {"last_uploaded_file": file.filename}
        if "error" not in extracted_data:
            project_update["tickets_count"] = Project.tickets_count + 1
            project_update["total_amount"] = Project.total_amount + ticket.final_total
        db.execute(update(Project).where(Project.id == project_id).values(**project_update))
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            # LOGIC-M4: Si falla el commit a BD, limpiar archivos ya subidos a Cloudinary
            _safe_delete_cloudinary(cloudinary_result)
            # FIX-1: mensaje específico de fallo al guardar
            logger.error(f"Error al guardar ticket en BD: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al guardar el ticket. Reintenta")
        db.refresh(ticket)
        # FIX-2: la IA no pudo extraer datos → el ticket se crea igual, pero avisamos
        # para que el frontend lo marque en ámbar en vez de verde de éxito.
        ia_warning = "error" in extracted_data or "Error" in str(extracted_data.get("provider") or "")
        return {
            "ticket": ticket,
            "duplicate_invoice_warning": duplicate_invoice_warning,
            "ia_warning": ia_warning,
            "ia_message": "La IA no pudo extraer datos. Revisa el ticket manualmente" if ia_warning else None,
        }

    except HTTPException:
        raise  # Errores específicos (Cloudinary/IA/BD) o de validación — ya con cleanup propio
    except Exception as e:
        # BUG-24: Cleanup Cloudinary if upload succeeded but later processing failed
        _safe_delete_cloudinary(cloudinary_result)
        # VULN-006: Logear error real, devolver genérico (fallback #7)
        logger.error(f"Error procesando ticket: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al procesar ticket")
    finally:
        if temp_path.exists():
            temp_path.unlink()


def apply_ticket_update(ticket: Ticket, update_data: dict, db: Session, *, is_admin: bool = False) -> Ticket:
    """Aplica una edición a un ticket. Lógica EXACTA de tickets.update_ticket.

    El caller ya validó existencia y permisos. update_data = model_dump(exclude_unset=True).
    """
    old_total = ticket.final_total
    old_suplido = ticket.is_suplido or False
    was_error = (ticket.provider == "Error en extracción" and old_total == 0.0)
    # SEC: no-ADMIN no puede mutar invoice_status/payment_status en tickets del portal
    if ticket.from_supplier_portal and not is_admin:
        update_data.pop("invoice_status", None)
        update_data.pop("payment_status", None)
    for key, value in update_data.items():
        setattr(ticket, key, value)
    new_suplido = ticket.is_suplido or False

    # Determine project total adjustment based on is_suplido transition + amount change
    amount_diff = 0.0
    count_diff = 0
    if was_error and ticket.final_total > 0 and not new_suplido:
        # T5: Error ticket becoming valid and not suplido → add to total
        count_diff = 1
        amount_diff = ticket.final_total
    elif old_suplido and new_suplido:
        # Was suplido, stays suplido → no change to project total regardless of amount
        pass
    elif not old_suplido and new_suplido:
        # Becoming suplido → subtract old amount from project total
        amount_diff = -old_total
    elif old_suplido and not new_suplido:
        # Leaving suplido → add new amount to project total
        amount_diff = ticket.final_total
    elif "final_total" in update_data:
        # Normal case: not suplido, amount changed → apply diff
        amount_diff = ticket.final_total - old_total

    if amount_diff != 0 or count_diff != 0:
        new_total = Project.total_amount + amount_diff
        db.execute(update(Project).where(Project.id == ticket.project_id).values(
            tickets_count=Project.tickets_count + count_diff,
            total_amount=case(
                (new_total > 0, new_total),
                else_=0,
            ),
        ))
    db.commit()
    db.refresh(ticket)
    return ticket


def delete_ticket_record(ticket: Ticket, db: Session) -> None:
    """Borra un ticket (Cloudinary + BD) y decrementa totales con floor a 0.

    Lógica EXACTA de tickets.delete_ticket (SIN los guards — esos van en el endpoint).
    """
    ticket_id = ticket.id
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
    # BUG-69: Si es suplido, su importe nunca fue sumado al total
    is_error_ticket = (ticket.provider == "Error en extracción" and ticket.final_total == 0.0)
    is_suplido = ticket.is_suplido or False
    decrement = 0 if is_error_ticket else 1
    amount_to_subtract = 0.0 if (is_error_ticket or is_suplido) else ticket.final_total
    db.execute(update(Project).where(Project.id == ticket.project_id).values(
        tickets_count=case(
            (Project.tickets_count > decrement, Project.tickets_count - decrement),
            else_=0,
        ),
        total_amount=case(
            (Project.total_amount > amount_to_subtract, Project.total_amount - amount_to_subtract),
            else_=0,
        ),
    ))
    db.delete(ticket)
    db.commit()
