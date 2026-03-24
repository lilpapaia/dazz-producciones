"""
Servicio de IA para extracción y validación de facturas de proveedores.

Usa Claude Sonnet para extraer datos de PDFs y valida contra la BD:
- NIF/CIF del proveedor
- IBAN del proveedor
- OC existente en proyectos
- Empresa correcta según prefijo OC
- Coherencia matemática
- Duplicados

Fase 2 del módulo de proveedores.
"""

import anthropic
import json
import base64
import os
import re
from datetime import date as date_type
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.models.database import Company, Project
from app.models.suppliers import Supplier, SupplierOC, SupplierInvoice
from app.services.encryption import decrypt_iban

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-6"

# ============================================
# MAPEO PREFIJO OC → EMPRESA
# Ordenado de más largo a más corto para longest-prefix-match
# ============================================

OC_PREFIX_MAP = [
    ("CRESTUDIOBCN", "DAZZ CREATIVE"),
    ("CRESTUDIOMAD", "DAZZ CREATIVE"),
    ("OC-MGMTINT",   "DAZZLE MGMT"),
    ("CRPROD",        "DAZZ CREATIVE"),
    ("CRREP",         "DAZZ CREATIVE"),
    ("CRMKT",         "DAZZ CREATIVE"),
    ("CRAI",          "DAZZ CREATIVE"),
    ("HDMKT",         "DIGITAL ADVERTISING SOCIAL SERVICES, S.L."),
    ("BRMKT",         "DAZZLE AGENCY, S.L."),
    ("HDM",           "DIGITAL ADVERTISING SOCIAL SERVICES, S.L."),
    ("BR",            "DAZZLE AGENCY, S.L."),
]

MATH_TOLERANCE = 0.02  # 2 céntimos de tolerancia en validación matemática


# ============================================
# EXTRACCIÓN DE DATOS CON CLAUDE SONNET
# ============================================

EXTRACTION_PROMPT = """Analiza esta factura PDF de un proveedor y extrae los datos en formato JSON.

IMPORTANTE: Devuelve SOLO el JSON, sin explicaciones ni texto adicional.

CAMPOS A EXTRAER:

- invoice_number: Número de factura (obligatorio)
- date: Fecha de factura en formato DD/MM/YYYY (obligatorio, convertir desde cualquier idioma)
- provider: Nombre o razón social del emisor (obligatorio)
- nif_cif: NIF/CIF/VAT del emisor (obligatorio — puede ser formato español o internacional)
- iban: IBAN del emisor (si aparece en la factura, puede ser null)
- oc_number: Número de OC / orden de compra / purchase order (buscar en toda la factura, obligatorio)
- base_amount: Base imponible (obligatorio)
- iva_percentage: Porcentaje IVA como decimal (0.21 para 21%)
- iva_amount: Importe IVA
- irpf_percentage: Porcentaje IRPF como decimal (0.15 para 15%, 0 si no hay)
- irpf_amount: Importe IRPF (0 si no hay)
- final_total: Total final de la factura (base + IVA - IRPF)
- currency: Código divisa (EUR, USD, GBP, etc.)
- is_foreign: true si NO es factura española peninsular/Baleares
- confidence: Nivel de confianza de 0.0 a 1.0

NOTAS IMPORTANTES:
- El OC puede aparecer como "OC", "Orden de compra", "Purchase Order", "PO", "Pedido", "Referencia" o similar.
- Formatos de OC conocidos: CRPROD2026XXX, CRREP2026XXX, CRAI2026XXX, CRMKT2026XXX, CRESTUDIOBCN2026XXX, CRESTUDIOMAD2026XXX, HDM2026XXX, HDMKT2026XXX, BR2026XXX, BRMKT2026XXX, OC-MGMTINT2026XXX
- El NIF/CIF puede ser español (12345678A), europeo (NL003216633B26), o internacional (20-38258898-4).
- Si no encuentras un campo, usa null para strings y 0.0 para números.

EJEMPLO RESPUESTA:
{
  "invoice_number": "2026/045",
  "date": "15/03/2026",
  "provider": "EVENTS BRANCH, S.L.",
  "nif_cif": "B67515783",
  "iban": "ES12 1234 5678 9012 3456 7890",
  "oc_number": "OC-MGMTINT2026037",
  "base_amount": 1500.00,
  "iva_percentage": 0.21,
  "iva_amount": 315.00,
  "irpf_percentage": 0.15,
  "irpf_amount": 225.00,
  "final_total": 1590.00,
  "currency": "EUR",
  "is_foreign": false,
  "confidence": 0.95
}"""


def extract_supplier_invoice(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Extrae datos de una factura PDF de proveedor usando Claude Sonnet.

    Args:
        file_path: Ruta al archivo PDF
        file_type: MIME type (application/pdf)

    Returns:
        Dict con datos extraídos o {"error": ..., "confidence": 0.0} si falla
    """
    with open(file_path, "rb") as f:
        file_data = f.read()

    base64_data = base64.b64encode(file_data).decode("utf-8")

    media_type = "application/pdf" if file_type == "application/pdf" else file_type

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document" if media_type == "application/pdf" else "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
    )

    response_text = message.content[0].text.strip()

    # Limpiar markdown si Claude lo envuelve
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse AI response",
            "raw_response": response_text,
            "confidence": 0.0,
        }


# ============================================
# RESOLUCIÓN DE EMPRESA POR PREFIJO OC
# ============================================

def resolve_company_from_oc(oc_number: str, db: Session) -> Optional[int]:
    """
    Mapea un OC a su company_id usando el prefijo.
    Usa longest-prefix-match para evitar ambigüedad (BR vs BRMKT).

    Returns:
        company_id o None si no hay match
    """
    if not oc_number:
        return None

    oc_upper = oc_number.strip().upper()

    for prefix, company_name in OC_PREFIX_MAP:
        if oc_upper.startswith(prefix.upper()):
            company = db.query(Company).filter(Company.name == company_name).first()
            return company.id if company else None

    return None


def _get_company_name_from_oc(oc_number: str) -> Optional[str]:
    """Devuelve el nombre de empresa esperado para un OC, sin consultar BD."""
    if not oc_number:
        return None

    oc_upper = oc_number.strip().upper()

    for prefix, company_name in OC_PREFIX_MAP:
        if oc_upper.startswith(prefix.upper()):
            return company_name

    return None


# ============================================
# VALIDACIONES CONTRA BD
# ============================================

def validate_supplier_invoice(
    extracted_data: Dict[str, Any],
    supplier_id: int,
    db: Session,
) -> Dict[str, Any]:
    """
    Valida los datos extraídos por IA contra la BD del proveedor.

    Args:
        extracted_data: Datos extraídos por extract_supplier_invoice()
        supplier_id: ID del proveedor que sube la factura
        db: Sesión de BD

    Returns:
        {
            "valid": bool,          # True si pasa todas las validaciones bloqueantes
            "errors": [...],        # Validaciones que bloquean la subida
            "warnings": [...],      # Avisos no bloqueantes
            "oc_status": str,       # "FOUND" | "OC_PENDING" | "INVALID_PREFIX"
            "company_id": int|None, # Empresa deducida del OC
            "project_id": int|None, # Proyecto vinculado al OC (si existe)
        }
    """
    errors: List[str] = []
    warnings: List[str] = []
    oc_status = "FOUND"
    company_id = None
    project_id = None

    # --- Cargar proveedor ---
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        return {
            "valid": False,
            "errors": ["Proveedor no encontrado en la BD"],
            "warnings": [],
            "oc_status": "INVALID_PREFIX",
            "company_id": None,
            "project_id": None,
        }

    # --- 1. PDF legible ---
    confidence = extracted_data.get("confidence", 0.0)
    if confidence < 0.5:
        errors.append(
            f"PDF no legible o datos insuficientes (confianza: {confidence:.0%})"
        )

    required_fields = ["invoice_number", "date", "provider", "nif_cif", "base_amount", "final_total", "oc_number"]
    missing = [f for f in required_fields if not extracted_data.get(f)]
    if missing:
        errors.append(f"Campos obligatorios no detectados en el PDF: {', '.join(missing)}")

    # --- 2. NIF/CIF coincide ---
    extracted_nif = _normalize_nif(extracted_data.get("nif_cif"))
    supplier_nif = _normalize_nif(supplier.nif_cif)

    if extracted_nif and supplier_nif:
        if extracted_nif != supplier_nif:
            errors.append(
                f"NIF/CIF de la factura ({extracted_data.get('nif_cif')}) "
                f"no coincide con el registrado ({supplier.nif_cif})"
            )
    elif extracted_nif and not supplier_nif:
        warnings.append("El proveedor no tiene NIF/CIF registrado — no se pudo validar")

    # --- 3. IBAN coincide (warning, no bloquea) ---
    extracted_iban = _normalize_iban(extracted_data.get("iban"))
    supplier_iban = None
    if supplier.iban_encrypted:
        supplier_iban = _normalize_iban(decrypt_iban(supplier.iban_encrypted))

    iban_match = None  # None = not checked, True = match, False = mismatch
    if extracted_iban and supplier_iban:
        if extracted_iban != supplier_iban:
            iban_match = False
            warnings.append("IBAN on invoice does not match the registered IBAN")
        else:
            iban_match = True
    elif extracted_iban and not supplier_iban:
        warnings.append("Supplier has no IBAN registered — could not validate")

    # --- 4. OC existe y empresa correcta ---
    oc_number = (extracted_data.get("oc_number") or "").strip()

    if oc_number:
        if supplier.oc_id:
            # Proveedor con OC permanente: verificar si coincide
            oc_match = db.query(SupplierOC).filter(
                SupplierOC.oc_number.ilike(oc_number)
            ).first()

            if oc_match and oc_match.id == supplier.oc_id:
                # OC permanente del proveedor — OK
                oc_status = "FOUND"
                company_id = oc_match.company_id
            else:
                # No es su OC permanente — intentar como proyecto
                oc_status, company_id, project_id = _resolve_oc_as_project(
                    oc_number, db, errors
                )
        else:
            # Sin OC permanente — resolver como proyecto
            oc_status, company_id, project_id = _resolve_oc_as_project(
                oc_number, db, errors
            )

    # --- 4b. Fecha parseable ---
    raw_date = extracted_data.get("date", "")
    parsed_date = parse_invoice_date(raw_date)
    if raw_date and not parsed_date:
        warnings.append(
            f"La fecha '{raw_date}' no se pudo interpretar automáticamente — "
            f"el admin deberá verificarla manualmente"
        )

    # --- 5. Cálculos correctos ---
    base = extracted_data.get("base_amount", 0.0) or 0.0
    iva = extracted_data.get("iva_amount", 0.0) or 0.0
    irpf = extracted_data.get("irpf_amount", 0.0) or 0.0
    final = extracted_data.get("final_total", 0.0) or 0.0

    expected_total = base + iva - irpf
    if abs(expected_total - final) > MATH_TOLERANCE and final > 0:
        warnings.append(
            f"Incoherencia matemática: base ({base:.2f}) + IVA ({iva:.2f}) "
            f"- IRPF ({irpf:.2f}) = {expected_total:.2f}, "
            f"pero el total es {final:.2f}"
        )

    # --- 6. Factura duplicada ---
    invoice_number = extracted_data.get("invoice_number")
    if invoice_number:
        duplicate = db.query(SupplierInvoice).filter(
            SupplierInvoice.supplier_id == supplier_id,
            SupplierInvoice.invoice_number == invoice_number,
        ).first()
        if duplicate:
            errors.append(
                f"Factura duplicada: ya existe una factura con número '{invoice_number}' "
                f"de este proveedor (ID: {duplicate.id})"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "oc_status": oc_status,
        "company_id": company_id,
        "project_id": project_id,
        "date_parsed": parsed_date,
        "iban_match": iban_match,
    }


# ============================================
# UTILIDADES DE NORMALIZACIÓN
# ============================================

def _resolve_oc_as_project(
    oc_number: str, db: Session, errors: List[str]
) -> tuple:
    """
    Resolve OC as a DAZZ project.

    Returns:
        (oc_status, company_id, project_id)
    """
    expected_company_name = _get_company_name_from_oc(oc_number)

    if expected_company_name is None:
        errors.append(
            f"El prefijo del OC '{oc_number}' no corresponde a ninguna empresa registrada"
        )
        return "INVALID_PREFIX", None, None

    company_id = resolve_company_from_oc(oc_number, db)

    project = db.query(Project).filter(
        Project.creative_code.ilike(oc_number)
    ).first()

    if project:
        return "FOUND", company_id, project.id

    errors.append(
        f"OC '{oc_number}' does not exist as a project in DAZZ Producciones. "
        f"The project must be created before submitting the invoice."
    )
    return "NOT_FOUND", company_id, None


CERT_IBAN_PROMPT = """Analyze this bank certificate PDF and extract the IBAN number.
Return ONLY a JSON object with a single field:
{"iban": "ESXX XXXX XXXX XXXX XXXX XXXX"}
If no IBAN is found, return: {"iban": null}
No explanations, no markdown."""

CERT_VALIDATION_PROMPT = """Analyze this PDF document and determine:

1. Is this a BANK CERTIFICATE (certificado de titularidad bancaria)?
   - A bank certificate proves ownership of a bank account
   - It is NOT an invoice, payslip, tax form, bank statement, or any other document
   - It typically contains: bank name/logo, account holder name, IBAN, and a statement of ownership

2. Extract the IBAN number if present

3. Extract the NIF/CIF/VAT number of the account holder if present

Return ONLY a JSON object:
{
  "is_bank_certificate": true or false,
  "iban": "ESXX XXXX XXXX XXXX XXXX XXXX" or null,
  "nif": "12345678A" or null,
  "confidence": "high", "medium", or "low"
}

- confidence "high": clearly a bank certificate with readable data
- confidence "medium": looks like a bank certificate but some data is hard to read
- confidence "low": unclear document type or very poor quality

No explanations, no markdown — ONLY the JSON."""


def extract_iban_from_cert(file_path: str) -> Optional[str]:
    """
    Extract IBAN from a bank certificate PDF using Claude.
    Legacy function — kept for backward compatibility.

    Returns:
        IBAN string or None if not found/not parseable
    """
    result = extract_bank_cert_data(file_path)
    return result.get("iban") if result else None


def extract_bank_cert_data(file_path: str) -> Dict[str, Any]:
    """
    Analyze a bank certificate PDF using Claude.
    Verifies document type, extracts IBAN and NIF.

    Returns:
        {is_bank_certificate, iban, nif, confidence} or empty dict if parse fails
    """
    with open(file_path, "rb") as f:
        file_data = f.read()

    base64_data = base64.b64encode(file_data).decode("utf-8")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": base64_data},
                },
                {"type": "text", "text": CERT_VALIDATION_PROMPT},
            ],
        }],
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {}


def _normalize_nif(nif: Optional[str]) -> Optional[str]:
    """Normaliza NIF/CIF para comparación: quita espacios, guiones, puntos, prefijo ES, uppercase."""
    if not nif:
        return None
    normalized = nif.strip().upper().replace(" ", "").replace("-", "").replace(".", "")
    # Remove ES prefix (common in EU invoices: ES12345678A → 12345678A)
    if normalized.startswith("ES") and len(normalized) > 2 and normalized[2:3].isdigit():
        normalized = normalized[2:]
    return normalized if normalized else None


def _normalize_iban(iban: Optional[str]) -> Optional[str]:
    """Normaliza IBAN para comparación: quita espacios, uppercase."""
    if not iban:
        return None
    return iban.strip().upper().replace(" ", "")


# ============================================
# PARSEO ROBUSTO DE FECHAS
# ============================================

# Meses en español e inglés para parseo de formatos textuales
_MONTH_NAMES = {
    # Español
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    # English
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "apr": 4, "aug": 8,
}


def parse_invoice_date(date_str: Optional[str]) -> Optional[date_type]:
    """
    Parse invoice date string into a date object.

    Tries multiple formats (ordered by likelihood from Claude IA output):
      1. DD/MM/YYYY  (IA default, Spanish invoices)
      2. YYYY-MM-DD  (ISO)
      3. DD-MM-YYYY
      4. DD.MM.YYYY
      5. D Month YYYY / DD de Month de YYYY  (Spanish/English textual)
      6. Month D, YYYY  (English textual)
      7. MM/DD/YYYY  (US — only if DD/MM fails or month > 12)

    Returns:
        date object or None if unparseable
    """
    if not date_str or not isinstance(date_str, str):
        return None

    s = date_str.strip()
    if not s:
        return None

    # --- Numeric formats with separators ---
    for sep in ["/", "-", "."]:
        parts = s.split(sep)
        if len(parts) == 3:
            try:
                a, b, c = [int(p.strip()) for p in parts]
            except ValueError:
                continue

            # YYYY-MM-DD (ISO: first part is 4 digits)
            if a > 1900:
                try:
                    return date_type(a, b, c)
                except ValueError:
                    continue

            # DD/MM/YYYY or DD-MM-YYYY (European: last part is 4 digits)
            if c > 1900:
                # Try DD/MM/YYYY first
                try:
                    return date_type(c, b, a)
                except ValueError:
                    pass
                # Fallback MM/DD/YYYY (US)
                try:
                    return date_type(c, a, b)
                except ValueError:
                    continue

    # --- Textual formats: "15 de marzo de 2026", "15 marzo 2026", "March 15, 2026" ---
    s_lower = s.lower()
    # Remove common filler words
    s_clean = s_lower.replace(" de ", " ").replace(" del ", " ").replace(",", " ")
    # Collapse multiple spaces
    s_clean = re.sub(r"\s+", " ", s_clean).strip()
    tokens = s_clean.split()

    if len(tokens) >= 3:
        # Try: D MONTH YYYY
        month_num = _MONTH_NAMES.get(tokens[1])
        if month_num:
            try:
                day = int(tokens[0])
                year = int(tokens[2])
                if year < 100:
                    year += 2000
                return date_type(year, month_num, day)
            except (ValueError, IndexError):
                pass

        # Try: MONTH D YYYY (English: "March 15 2026")
        month_num = _MONTH_NAMES.get(tokens[0])
        if month_num:
            try:
                day = int(tokens[1])
                year = int(tokens[2])
                if year < 100:
                    year += 2000
                return date_type(year, month_num, day)
            except (ValueError, IndexError):
                pass

    return None


def format_date_for_response(d) -> str:
    """Format a date (Date object or legacy string) as DD/MM/YYYY for API responses."""
    if d is None:
        return ""
    if isinstance(d, date_type):
        return d.strftime("%d/%m/%Y")
    # Legacy string — return as-is
    return str(d)
