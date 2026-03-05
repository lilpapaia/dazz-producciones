from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
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
from app.services.exchange_rate import get_historical_exchange_rate, convert_to_eur
from app.services.geographic_classifier import classify_geography

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/extract", response_model=schemas.AIExtractionResponse)
async def extract_ticket(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract data from ticket/invoice using Claude AI
    This is a preview endpoint - doesn't save to database yet
    """
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Use JPG, PNG or PDF."
        )
    
    # Save file temporarily
    file_path = UPLOAD_DIR / f"temp_{current_user.id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Extract data using Claude AI
        extracted_data = extract_ticket_data(str(file_path), file.content_type)
        
        # Check for errors
        if "error" in extracted_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI extraction failed: {extracted_data.get('error')}"
            )
        
        return extracted_data
    
    finally:
        # Clean up temp file
        if file_path.exists():
            file_path.unlink()

@router.post("/{project_id}/upload", response_model=schemas.TicketResponse, status_code=status.HTTP_201_CREATED)
async def upload_ticket(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a ticket/invoice and auto-extract data with AI
    Con soporte para moneda extranjera automático
    """
    
    # Check if project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Use JPG, PNG or PDF."
        )
    
    # Create project-specific directory
    project_dir = UPLOAD_DIR / f"project_{project_id}"
    project_dir.mkdir(exist_ok=True)
    
    # Save file permanently
    file_path = project_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Extract data using Claude AI
        extracted_data = extract_ticket_data(str(file_path), file.content_type)
        
        # Check for errors
        if "error" in extracted_data:
            # Still save the ticket but with empty data
            ticket = Ticket(
                project_id=project_id,
                file_path=str(file_path),
                file_name=file.filename,
                date="",
                provider="Error en extracción",
                base_amount=0.0,
                iva_amount=0.0,
                iva_percentage=0.0,
                total_with_iva=0.0,
                final_total=0.0,
                type="ticket",
                is_reviewed=False,
                is_foreign=False,
                currency="EUR"
            )
        else:
            # ============================================
            # PROCESAR FACTURA INTERNACIONAL
            # ============================================
            is_foreign = extracted_data.get("is_foreign", False)
            currency = extracted_data.get("currency", "EUR")
            country_code = extracted_data.get("country_code", "ES")
            
            # Clasificar geografía
            geo_classification = classify_geography(country_code)
            
            # Valores por defecto (EUR nacional)
            exchange_rate = None
            exchange_rate_date = None
            foreign_amount = None
            foreign_total = None
            foreign_tax_amount = None
            foreign_tax_eur = None
            
            # Si es internacional y NO es EUR, obtener tasa
            if is_foreign and currency != "EUR":
                # Parse fecha de la factura para obtener tasa histórica
                try:
                    # Formato: DD/MM/YYYY
                    date_str = extracted_data.get("date", "")
                    if date_str and "/" in date_str:
                        day, month, year = date_str.split("/")
                        invoice_date = datetime(int(year), int(month), int(day)).date()
                        
                        # Obtener tasa histórica
                        exchange_rate = get_historical_exchange_rate(
                            from_currency=currency,
                            to_currency="EUR",
                            rate_date=invoice_date
                        )
                        
                        if exchange_rate:
                            exchange_rate_date = invoice_date
                            
                            # Guardar importes en divisa original
                            foreign_amount = extracted_data.get("foreign_amount")
                            foreign_total = extracted_data.get("foreign_total")
                            foreign_tax_amount = extracted_data.get("foreign_tax_amount")
                            
                            # Convertir IVA extranjero a EUR para estadísticas
                            if foreign_tax_amount:
                                foreign_tax_eur = foreign_tax_amount * exchange_rate
                            
                            print(f"✅ Factura internacional: {currency} → EUR")
                            print(f"   Tasa ({invoice_date}): {exchange_rate}")
                            print(f"   IVA reclamable: {foreign_tax_eur}€")
                        
                except Exception as e:
                    print(f"⚠️ Error procesando tasa de cambio: {str(e)}")
            
            # Si es EUR pero internacional (UE), también guardar IVA reclamable
            elif is_foreign and currency == "EUR":
                foreign_amount = extracted_data.get("base_amount", 0.0)
                foreign_total = extracted_data.get("final_total", 0.0)
                foreign_tax_amount = extracted_data.get("iva_amount", 0.0)
                foreign_tax_eur = extracted_data.get("iva_amount", 0.0)
                exchange_rate = 1.0  # EUR a EUR
            
            # ============================================
            
            # Create ticket with extracted data
            ticket = Ticket(
                project_id=project_id,
                file_path=str(file_path),
                file_name=file.filename,
                # Campos básicos
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
                # Campos internacionales
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
        
        # Update project totals
        project.tickets_count += 1
        project.total_amount += ticket.final_total
        
        db.commit()
        db.refresh(ticket)
        
        return ticket
    
    except Exception as e:
        # If anything fails, delete the file
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process ticket: {str(e)}"
        )

@router.get("/{project_id}/tickets", response_model=List[schemas.TicketResponse])
async def get_project_tickets(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all tickets for a project"""
    
    # Check if project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    tickets = db.query(Ticket).filter(Ticket.project_id == project_id).all()
    return tickets


@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific ticket by ID"""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Check permissions
    project = db.query(Project).filter(Project.id == ticket.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return ticket


@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_update: schemas.TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a ticket (for manual corrections)"""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Check permissions
    project = db.query(Project).filter(Project.id == ticket.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update fields
    old_total = ticket.final_total
    update_data = ticket_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)
    
    # Update project total if amount changed
    if "final_total" in update_data:
        project.total_amount = project.total_amount - old_total + ticket.final_total
    
    db.commit()
    db.refresh(ticket)
    
    return ticket

@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a ticket"""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Check permissions
    project = db.query(Project).filter(Project.id == ticket.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update project totals
    project.tickets_count -= 1
    project.total_amount -= ticket.final_total
    
    # Delete file
    file_path = Path(ticket.file_path)
    if file_path.exists():
        file_path.unlink()
    
    db.delete(ticket)
    db.commit()
    
    return None
