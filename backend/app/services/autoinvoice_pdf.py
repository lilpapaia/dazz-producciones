"""
PDF generation for autoinvoices using fpdf2.

Generates a professional invoice PDF in memory (BytesIO) matching the structure
of the Excel template (docs/autofactura_template.xlsx):
- Header: DAZZ logo area + AUTOFACTURA title
- Issuer data (DAZZ company)
- Recipient data (supplier)
- Invoice details (number, date, concept, OC)
- Amounts table (base, IVA, IRPF, total)
- IBAN + legal text
"""

import logging
from io import BytesIO
from fpdf import FPDF

logger = logging.getLogger(__name__)

# Colors (DAZZ brand - zinc/amber)
C_BG = (24, 24, 27)       # zinc-900
C_BORDER = (63, 63, 70)   # zinc-700
C_TEXT = (228, 228, 231)   # zinc-200
C_LABEL = (161, 161, 170)  # zinc-400
C_AMBER = (245, 158, 11)  # amber-500
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)
C_LIGHT_BG = (39, 39, 42)  # zinc-800


class AutoInvoicePDF(FPDF):
    def header(self):
        pass  # Custom header in body

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*C_LABEL)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def generate_autoinvoice_pdf(
    invoice_number: str,
    date: str,
    concept: str,
    oc_number: str,
    issuer_name: str,
    issuer_cif: str,
    issuer_address: str,
    supplier_name: str,
    supplier_nif: str,
    supplier_address: str,
    supplier_iban: str,
    base_amount: float,
    iva_percentage: float,
    iva_amount: float,
    irpf_percentage: float,
    irpf_amount: float,
    final_total: float,
    gastos_base: float = 0,
    gastos_iva_percentage: float = 0,
    gastos_iva_amount: float = 0,
    gastos_irpf_amount: float = 0,
    gastos_subtotal: float = 0,
) -> bytes:
    """
    Generate autoinvoice PDF and return as bytes.

    Returns:
        PDF file contents as bytes
    """
    pdf = AutoInvoicePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    w = pdf.w - 20  # usable width (margins 10 each side)

    # ═══ HEADER ═══
    pdf.set_fill_color(*C_AMBER)
    pdf.rect(10, 10, w, 28, "F")
    pdf.set_xy(15, 14)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*C_BLACK)
    pdf.cell(0, 10, "DAZZ GROUP", ln=False)
    pdf.set_xy(15, 26)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "SELF-BILLING INVOICE", ln=True)

    # Invoice number + date right-aligned
    pdf.set_xy(w - 60, 14)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(60, 6, invoice_number, align="R")
    pdf.set_xy(w - 60, 22)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(60, 6, date, align="R")

    y = 44

    # ═══ ISSUER + RECIPIENT side by side ═══
    col_w = w / 2 - 3

    # Issuer (left)
    pdf.set_xy(10, y)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*C_LABEL)
    pdf.cell(col_w, 5, "ISSUER", ln=True)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_BLACK)
    pdf.cell(col_w, 5, issuer_name, ln=True)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(col_w, 5, f"CIF: {issuer_cif}", ln=True)
    pdf.set_x(10)
    pdf.multi_cell(col_w, 4, issuer_address or "")

    # Recipient (right)
    pdf.set_xy(10 + col_w + 6, y)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*C_LABEL)
    pdf.cell(col_w, 5, "RECIPIENT", ln=True)
    pdf.set_x(10 + col_w + 6)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_BLACK)
    pdf.cell(col_w, 5, supplier_name, ln=True)
    pdf.set_x(10 + col_w + 6)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(col_w, 5, f"NIF/CIF: {supplier_nif or '—'}", ln=True)
    pdf.set_x(10 + col_w + 6)
    pdf.multi_cell(col_w, 4, supplier_address or "")

    y = max(pdf.get_y(), y + 30) + 8

    # ═══ CONCEPT + OC ═══
    pdf.set_xy(10, y)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*C_LABEL)
    pdf.cell(0, 5, "CONCEPT", ln=True)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_BLACK)
    pdf.multi_cell(w, 5, concept)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*C_LABEL)
    pdf.cell(0, 5, f"OC: {oc_number}", ln=True)

    y = pdf.get_y() + 8

    # ═══ AMOUNTS TABLE ═══
    pdf.set_xy(10, y)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*C_LABEL)
    pdf.cell(0, 5, "AMOUNTS", ln=True)

    table_x = 10
    label_w = w * 0.65
    val_w = w * 0.35

    def _row(label, value, bold=False, color=C_BLACK):
        pdf.set_x(table_x)
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        pdf.set_text_color(*C_BLACK)
        pdf.cell(label_w, 7, label, border="B")
        pdf.set_text_color(*color)
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        pdf.cell(val_w, 7, value, border="B", align="R", ln=True)

    _row("Base amount", f"{base_amount:,.2f} EUR")
    iva_pct_display = f"{iva_percentage * 100:.0f}%"
    _row(f"IVA ({iva_pct_display})", f"{iva_amount:,.2f} EUR")
    if irpf_amount > 0:
        irpf_pct_display = f"{irpf_percentage * 100:.0f}%"
        _row(f"IRPF ({irpf_pct_display})", f"-{irpf_amount:,.2f} EUR", color=(239, 68, 68))

    # FEAT-02: Expenses section (only if gastos_base > 0)
    if gastos_base > 0:
        pdf.ln(4)
        pdf.set_x(table_x)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*C_LABEL)
        pdf.cell(0, 5, "EXPENSES", ln=True)
        _row("Expenses base", f"{gastos_base:,.2f} EUR")
        if gastos_iva_amount > 0:
            gastos_iva_pct_display = f"{gastos_iva_percentage * 100:.0f}%"
            _row(f"Expenses IVA ({gastos_iva_pct_display})", f"{gastos_iva_amount:,.2f} EUR")
        if gastos_irpf_amount > 0:
            irpf_pct_display = f"{irpf_percentage * 100:.0f}%"
            _row(f"Expenses IRPF ({irpf_pct_display})", f"-{gastos_irpf_amount:,.2f} EUR", color=(239, 68, 68))
        _row("Expenses subtotal", f"{gastos_subtotal:,.2f} EUR", bold=True)

    pdf.ln(2)
    pdf.set_x(table_x)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*C_BLACK)
    pdf.cell(label_w, 10, "TOTAL")
    pdf.set_text_color(*C_AMBER)
    pdf.cell(val_w, 10, f"{final_total:,.2f} EUR", align="R", ln=True)

    y = pdf.get_y() + 10

    # ═══ PAYMENT DETAILS ═══
    pdf.set_xy(10, y)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*C_LABEL)
    pdf.cell(0, 5, "PAYMENT DETAILS", ln=True)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_BLACK)
    pdf.cell(0, 5, f"Bank transfer 30 days | IBAN: {supplier_iban or '—'}", ln=True)

    y = pdf.get_y() + 12

    # ═══ LEGAL TEXT ═══
    pdf.set_xy(10, y)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*C_LABEL)
    legal = (
        f"In compliance with Data Protection regulations, we inform you that your personal data "
        f"is processed by {issuer_name} for the purpose of providing our services. "
        f"You may exercise your rights of access, rectification, and deletion by contacting us."
    )
    pdf.multi_cell(w, 3.5, legal)

    # Generate bytes
    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()
