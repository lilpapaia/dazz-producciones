from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime
from typing import List, Dict
from io import BytesIO

def create_project_excel_bytes(project, tickets) -> bytes:
    """
    Create Excel in memory (BytesIO) and return bytes
    OPTIMIZADO PARA CLOUD + FIX para campos opcionales
    
    Args:
        project: SQLAlchemy Project object
        tickets: List of SQLAlchemy Ticket objects
        
    Returns:
        bytes: Excel file as bytes
    """
    
    wb = Workbook()
    sheet = wb.active
    sheet.title = "Hoja 1"
    
    # === FILA 2: Cabecera del proyecto ===
    headers_row2 = [
        "AÑO",
        "FECHA ENVIO FACTURAR",
        "CREATIVO",
        "EMPRESA FACTURACION",
        "QUIEN GESTIONA",
        "TIPO FACTURA",
        "DESCRIPCIÓN/CAMPAÑA/ACCIÓN",
        "IMPORTE BRUTO TOTAL",
        "OTROS DATOS FACTURA",
        "DATOS CLIENTE",
        "EMAIL CLIENTE",
        "ESTATUS",
        "LINEA FISPER"
    ]
    
    for col, header in enumerate(headers_row2, start=1):
        cell = sheet.cell(row=2, column=col, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # === FILA 3: Datos del proyecto ===
    sheet.cell(row=3, column=1, value=int(project.year) if project.year else 2026)
    sheet.cell(row=3, column=2, value=project.send_date or '')
    sheet.cell(row=3, column=3, value=project.creative_code or '')
    sheet.cell(row=3, column=4, value=project.company or '')
    sheet.cell(row=3, column=5, value=project.responsible or '')
    sheet.cell(row=3, column=6, value=project.invoice_type or '')
    sheet.cell(row=3, column=7, value=project.description or '')
    
    # IMPORTE BRUTO TOTAL
    if tickets:
        last_row = 5 + len(tickets)
        sheet.cell(row=3, column=8, value=f'=SUM(K6:K{last_row})')
    else:
        sheet.cell(row=3, column=8, value=0)
    
    sheet.cell(row=3, column=9, value=project.other_invoice_data or '')
    sheet.cell(row=3, column=10, value=project.client_data or '')
    sheet.cell(row=3, column=11, value=project.client_email or '')
    sheet.cell(row=3, column=12, value=project.client_oc or '')
    
    # === FILA 4: Link proyecto ===
    sheet.cell(row=4, column=1, value="LINK A PROYECTO:")
    sheet.cell(row=4, column=1).font = Font(bold=True)
    sheet.cell(row=4, column=2, value=project.project_link or '')
    
    # === FILA 5: Encabezados tickets ===
    headers_row5 = [
        "FECHA SU FACTURA",
        "Proveedor - Nombre",
        "Nº FACTURA PROVEEDOR",
        "PO SI APLICA",
        "IMPORTE",
        "TIPO",
        "TIPO IVA",
        "TOTAL",
        "TIPO IRPF",
        "RETENCION",
        "TOTAL",
        "ESTATUS FACTURA",
        "ESTATUS PAGO",
        "TELEFONO",
        "EMAIL",
        "NOMBRE",
        "ESTATUS EN CONTABILIDAD",
        "nº de GASTO",
        "ESTATUS PAGO",
        "LINK",
        "COMO SE PAGÓ",
        "FECHA PAGO",
        "ORIGEN"
    ]

    for col, header in enumerate(headers_row5, start=1):
        cell = sheet.cell(row=5, column=col, value=header)
        cell.font = Font(bold=True, size=10)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

    # === FILA 6+: Tickets ===
    # FIX: Usar getattr() para campos que pueden tener diferentes nombres
    for idx, ticket in enumerate(tickets, start=6):
        sheet.cell(row=idx, column=1, value=ticket.date or '')
        sheet.cell(row=idx, column=2, value=ticket.provider or '')
        sheet.cell(row=idx, column=3, value=ticket.invoice_number or '')
        
        # FIX: Campo notas puede llamarse 'notes', 'po_notes', o 'description'
        # Intenta en orden: notes → po_notes → description → vacío
        notes_value = getattr(ticket, 'notes', None) or \
                     getattr(ticket, 'po_notes', None) or \
                     getattr(ticket, 'description', '') or ''
        sheet.cell(row=idx, column=4, value=notes_value)
        
        sheet.cell(row=idx, column=5, value=ticket.base_amount or 0)
        sheet.cell(row=idx, column=6, value=ticket.iva_amount or 0)
        sheet.cell(row=idx, column=7, value=ticket.iva_percentage or 0)
        
        # total_with_iva = base + iva
        total_with_iva = (ticket.base_amount or 0) + (ticket.iva_amount or 0)
        sheet.cell(row=idx, column=8, value=total_with_iva)
        
        # IRPF (campos opcionales)
        irpf_percentage = getattr(ticket, 'irpf_percentage', 0) or 0
        irpf_amount = getattr(ticket, 'irpf_amount', 0) or 0
        sheet.cell(row=idx, column=9, value=irpf_percentage)
        sheet.cell(row=idx, column=10, value=irpf_amount)
        
        sheet.cell(row=idx, column=11, value=ticket.final_total or 0)
        sheet.cell(row=idx, column=12, value=ticket.invoice_status or '')
        sheet.cell(row=idx, column=13, value=ticket.payment_status or '')
        
        # Solo para facturas
        if ticket.type == 'factura':
            sheet.cell(row=idx, column=14, value=ticket.phone or '')
            sheet.cell(row=idx, column=15, value=ticket.email or '')
            # contact_name también puede no existir
            contact_name = getattr(ticket, 'contact_name', '') or ''
            sheet.cell(row=idx, column=16, value=contact_name)

        # INT-1: Origen del ticket
        is_supplier = getattr(ticket, 'from_supplier_portal', False)
        is_auto = getattr(ticket, 'is_autoinvoice', False)
        origin = "AUTOFACTURA" if (is_supplier and is_auto) else "PROVEEDOR" if is_supplier else "INTERNO"
        sheet.cell(row=idx, column=23, value=origin)

    # === Ajustar anchos ===
    column_widths = {
        'A': 15, 'B': 25, 'C': 18, 'D': 20, 'E': 12, 'F': 10, 'G': 10, 'H': 12,
        'I': 10, 'J': 12, 'K': 12, 'L': 18, 'M': 18, 'N': 15, 'O': 30, 'P': 20,
        'Q': 25, 'R': 12, 'S': 18, 'T': 15, 'U': 18, 'V': 15, 'W': 15
    }
    
    for col_letter, width in column_widths.items():
        sheet.column_dimensions[col_letter].width = width
    
    # === GUARDAR EN MEMORIA ===
    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)
    
    return excel_buffer.getvalue()
