from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from pathlib import Path
from datetime import datetime

from config.database import get_db
from app.models import schemas
from app.models.database import User, Project, Ticket
from app.services.auth import get_current_active_user
from app.services.claude_ai import extract_ticket_data
from app.services.cloudinary_service import upload_ticket_file, delete_ticket_file
from app.services.exchange_rate import get_historical_exchange_rate
from app.services.geographic_classifier import classify_geography

router = APIRouter(prefix="/tickets", tags=["Tickets"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/{project_id}/upload", response_model=schemas.TicketResponse, status_code=status.HTTP_201_CREATED)
async def upload_ticket(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    allowed_types = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type {file.content_type} not allowed.")

    # Guardar temporalmente para procesamiento con IA
    temp_path = UPLOAD_DIR / f"temp_{current_user.id}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 1. Extraer datos con Claude AI
        extracted_data = extract_ticket_data(str(temp_path), file.content_type)

        if "error" in extracted_data:
            # Subir a Cloudinary aunque falle IA
            cloudinary_result = upload_ticket_file(str(temp_path), file.filename, project_id)
            ticket = Ticket(
                project_id=project_id,
                file_path=cloudinary_result["url"],
                file_name=file.filename,
                date="", provider="Error en extracción",
                base_amount=0.0, iva_amount=0.0, iva_percentage=0.0,
                total_with_iva=0.0, final_total=0.0,
                type="ticket", is_reviewed=False,
                is_foreign=False, currency="EUR"
            )
        else:
            # 2. Subir a Cloudinary (convierte a WebP si es imagen)
            cloudinary_result = upload_ticket_file(str(temp_path), file.filename, project_id)

            # 3. Procesar datos internacionales
            is_foreign = extracted_data.get("is_foreign", False)
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
                        exchange_rate = get_historical_exchange_rate(
                            from_currency=currency, to_currency="EUR", rate_date=invoice_date
                        )
                        if exchange_rate:
                            exchange_rate_date = invoice_date
                            foreign_amount = extracted_data.get("foreign_amount")
                            foreign_total = extracted_data.get("foreign_total")
                            foreign_tax_amount = extracted_data.get("foreign_tax_amount")
                            if foreign_tax_amount:
                                foreign_tax_eur = foreign_tax_amount * exchange_rate
                except Exception as e:
                    print(f"⚠️ Error procesando tasa: {str(e)}")

            elif is_foreign and currency == "EUR":
                foreign_amount = extracted_data.get("base_amount", 0.0)
                foreign_total = extracted_data.get("final_total", 0.0)
                foreign_tax_amount = extracted_data.get("iva_amount", 0.0)
                foreign_tax_eur = extracted_data.get("iva_amount", 0.0)
                exchange_rate = 1.0

            # 4. Crear ticket con URL de Cloudinary
            ticket = Ticket(
                project_id=project_id,
                file_path=cloudinary_result["url"],   # URL permanente Cloudinary
                file_name=file.filename,
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
                is_reviewed=False
            )

        db.add(ticket)
        project.tickets_count += 1
        project.total_amount += ticket.final_total
        db.commit()
        db.refresh(ticket)
        return ticket

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process ticket: {str(e)}")
    finally:
        # Eliminar archivo temporal siempre
        if temp_path.exists():
            temp_path.unlink()


@router.get("/{project_id}/tickets", response_model=List[schemas.TicketResponse])
async def get_project_tickets(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return db.query(Ticket).filter(Ticket.project_id == project_id).all()


@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    project = db.query(Project).filter(Project.id == ticket.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return ticket


@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
async def update_ticket(ticket_id: int, ticket_update: schemas.TicketUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    project = db.query(Project).filter(Project.id == ticket.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    old_total = ticket.final_total
    update_data = ticket_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)
    if "final_total" in update_data:
        project.total_amount = project.total_amount - old_total + ticket.final_total
    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    project = db.query(Project).filter(Project.id == ticket.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    # Eliminar de Cloudinary si es una URL de Cloudinary
    if ticket.file_path and "cloudinary.com" in ticket.file_path:
        try:
            # Extraer public_id de la URL
            parts = ticket.file_path.split("/upload/")
            if len(parts) > 1:
                public_id = parts[1].split(".")[0]  # Sin extensión
                resource_type = "raw" if ticket.file_name.endswith(".pdf") else "image"
                delete_ticket_file(public_id, resource_type)
        except Exception as e:
            print(f"⚠️ No se pudo eliminar de Cloudinary: {str(e)}")

    project.tickets_count -= 1
    project.total_amount -= ticket.final_total
    db.delete(ticket)
    db.commit()
    return None
