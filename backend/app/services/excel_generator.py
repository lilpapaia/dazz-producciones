from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime
from typing import List, Dict
import os

def generate_project_excel(project_data: Dict, tickets: List[Dict], output_path: str) -> str:
    """
    Generate Excel file with exact format for accounting
    
    Args:
        project_data: Dictionary with project header data
        tickets: List of ticket dictionaries
        output_path: Path where to save the Excel file
        
    Returns:
        Path to the generated Excel file
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
    sheet.cell(row=3, column=1, value=int(project_data.get('year', '2026')))
    sheet.cell(row=3, column=2, value=project_data.get('send_date', ''))
    sheet.cell(row=3, column=3, value=project_data.get('creative_code', ''))
    sheet.cell(row=3, column=4, value=project_data.get('company', ''))
    sheet.cell(row=3, column=5, value=project_data.get('responsible', ''))
    sheet.cell(row=3, column=6, value=project_data.get('invoice_type', ''))
    sheet.cell(row=3, column=7, value=project_data.get('description', ''))
    
    # IMPORTE BRUTO TOTAL - Fórmula suma de todos los tickets
    if tickets:
        last_row = 5 + len(tickets)
        sheet.cell(row=3, column=8, value=f'=SUM(K6:K{last_row})')
    else:
        sheet.cell(row=3, column=8, value=0)
    
    sheet.cell(row=3, column=9, value=project_data.get('other_invoice_data', ''))
    sheet.cell(row=3, column=10, value=project_data.get('client_data', ''))
    sheet.cell(row=3, column=11, value=project_data.get('client_email', ''))
    sheet.cell(row=3, column=12, value=project_data.get('client_oc', ''))  # OC de cliente
    
    # === FILA 4: Link proyecto SharePoint ===
    sheet.cell(row=4, column=1, value="LINK A PROYECTO:")
    sheet.cell(row=4, column=1).font = Font(bold=True)
    sheet.cell(row=4, column=2, value=project_data.get('project_link', ''))
    
    # === FILA 5: Encabezados de tickets ===
    headers_row5 = [
        "FECHA SU FACTURA",       # A
        "Proveedor - Nombre",      # B
        "Nº FACTURA PROVEEDOR",    # C
        "PO SI APLICA",            # D
        "IMPORTE",                 # E (base_amount)
        "TIPO",                    # F (iva_amount)
        "TIPO IVA",                # G (iva_percentage)
        "TOTAL",                   # H (total_with_iva)
        "TIPO IRPF",               # I (irpf_percentage)
        "RETENCION",               # J (irpf_amount)
        "TOTAL",                   # K (final_total)
        "ESTATUS FACTURA",         # L
        "ESTATUS PAGO",            # M
        "TELEFONO",                # N
        "EMAIL",                   # O
        "NOMBRE",                  # P (contacto)
        "ESTATUS EN CONTABILIDAD", # Q
        "nº de GASTO",             # R
        "ESTATUS PAGO",            # S (duplicado - contabilidad)
        "LINK",                    # T
        "COMO SE PAGÓ",            # U
        "FECHA PAGO"               # V
    ]
    
    for col, header in enumerate(headers_row5, start=1):
        cell = sheet.cell(row=5, column=col, value=header)
        cell.font = Font(bold=True, size=10)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    
    # === FILA 6+: Tickets individuales ===
    for idx, ticket in enumerate(tickets, start=6):
        sheet.cell(row=idx, column=1, value=ticket.get('date', ''))  # A: Fecha
        sheet.cell(row=idx, column=2, value=ticket.get('provider', ''))  # B: Proveedor
        sheet.cell(row=idx, column=3, value=ticket.get('invoice_number', ''))  # C: Nº factura
        sheet.cell(row=idx, column=4, value=ticket.get('po_notes', ''))  # D: PO/Notas
        sheet.cell(row=idx, column=5, value=ticket.get('base_amount', 0))  # E: Base imponible
        sheet.cell(row=idx, column=6, value=ticket.get('iva_amount', 0))  # F: IVA cantidad
        sheet.cell(row=idx, column=7, value=ticket.get('iva_percentage', 0))  # G: IVA %
        sheet.cell(row=idx, column=8, value=ticket.get('total_with_iva', 0))  # H: Total con IVA
        sheet.cell(row=idx, column=9, value=ticket.get('irpf_percentage', 0))  # I: IRPF %
        sheet.cell(row=idx, column=10, value=ticket.get('irpf_amount', 0))  # J: IRPF cantidad
        sheet.cell(row=idx, column=11, value=ticket.get('final_total', 0))  # K: Total final
        sheet.cell(row=idx, column=12, value=ticket.get('invoice_status', ''))  # L: Estatus factura
        sheet.cell(row=idx, column=13, value=ticket.get('payment_status', ''))  # M: Estatus pago
        
        # Solo para facturas (no tickets)
        if ticket.get('type') == 'factura':
            sheet.cell(row=idx, column=14, value=ticket.get('phone', ''))  # N: Teléfono
            sheet.cell(row=idx, column=15, value=ticket.get('email', ''))  # O: Email
            sheet.cell(row=idx, column=16, value=ticket.get('contact_name', ''))  # P: Nombre contacto
    
    # === Ajustar anchos de columnas ===
    column_widths = {
        'A': 15, 'B': 25, 'C': 18, 'D': 20, 'E': 12, 'F': 10, 'G': 10, 'H': 12,
        'I': 10, 'J': 12, 'K': 12, 'L': 18, 'M': 18, 'N': 15, 'O': 30, 'P': 20,
        'Q': 25, 'R': 12, 'S': 18, 'T': 15, 'U': 18, 'V': 15
    }
    
    for col_letter, width in column_widths.items():
        sheet.column_dimensions[col_letter].width = width
    
    # Guardar archivo
    wb.save(output_path)
    return output_path


def create_project_excel_from_db(project, tickets, output_dir: str = "excel_generated") -> str:
    """
    Create Excel from database project and tickets
    
    Args:
        project: SQLAlchemy Project object
        tickets: List of SQLAlchemy Ticket objects
        output_dir: Directory to save Excel files
        
    Returns:
        Path to generated Excel file
    """
    
    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare project data
    project_data = {
        'year': project.year,
        'send_date': project.send_date,
        'creative_code': project.creative_code,
        'company': project.company,
        'responsible': project.responsible,
        'invoice_type': project.invoice_type,
        'description': project.description,
        'other_invoice_data': project.other_invoice_data,
        'client_oc': project.client_oc,
        'client_data': project.client_data,
        'client_email': project.client_email,
        'project_link': project.project_link
    }
    
    # Prepare tickets data
    tickets_data = []
    for ticket in tickets:
        tickets_data.append({
            'date': ticket.date,
            'provider': ticket.provider,
            'invoice_number': ticket.invoice_number,
            'po_notes': ticket.po_notes,
            'base_amount': ticket.base_amount,
            'iva_amount': ticket.iva_amount,
            'iva_percentage': ticket.iva_percentage,
            'total_with_iva': ticket.total_with_iva,
            'irpf_percentage': ticket.irpf_percentage,
            'irpf_amount': ticket.irpf_amount,
            'final_total': ticket.final_total,
            'invoice_status': ticket.invoice_status,
            'payment_status': ticket.payment_status,
            'type': ticket.type,
            'phone': ticket.phone,
            'email': ticket.email,
            'contact_name': ticket.contact_name
        })
    
    # Generate filename
    safe_code = project.creative_code.replace('/', '-').replace('\\', '-')
    filename = f"{safe_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    output_path = os.path.join(output_dir, filename)
    
    # Generate Excel
    return generate_project_excel(project_data, tickets_data, output_path)
