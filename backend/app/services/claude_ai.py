import anthropic
import json
import base64
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-6"


def strip_markdown_json(text: str) -> str:
    """Strip markdown code block wrappers from Claude API JSON responses."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _normalize_media_type(file_type: str, filename: Optional[str] = None) -> str:
    """Normalize media type for Claude API which only accepts:
    image/jpeg, image/png, image/gif, image/webp, application/pdf.

    Strategy:
    1. Try content_type (normalized to lowercase)
    2. If generic/unknown → fall back to filename extension
    3. If still unknown → fallback image/jpeg
    """
    MIME_MAP = {
        "image/jpeg": "image/jpeg",
        "image/jpg": "image/jpeg",
        "image/png": "image/png",
        "image/gif": "image/gif",
        "image/webp": "image/webp",
        "image/heic": "image/jpeg",
        "image/heif": "image/jpeg",
        "application/pdf": "application/pdf",
    }
    EXT_MAP = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".heic": "image/jpeg",
        ".heif": "image/jpeg",
        ".pdf": "application/pdf",
    }

    normalized = (file_type or "").strip().lower()
    if normalized in MIME_MAP:
        return MIME_MAP[normalized]

    # Generic or unknown content_type → try extension
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in EXT_MAP:
            return EXT_MAP[ext]

    return "image/jpeg"


def extract_ticket_data(file_path: str, file_type: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract data from ticket/invoice using Claude AI

    MEJORAS:
    - Detecta fechas en múltiples idiomas y convierte a DD/MM/YYYY
    - Detecta automáticamente facturas internacionales
    - Extrae divisa, país, e importes originales

    Args:
        file_path: Path to the image/PDF file
        file_type: MIME type of the file
        filename: Original filename (used as fallback for type detection)

    Returns:
        Dictionary with extracted data
    """

    # Read and encode file
    with open(file_path, "rb") as f:
        file_data = f.read()

    base64_data = base64.b64encode(file_data).decode("utf-8")

    # BUG-28: Normalize media type (image/jpg → image/jpeg, HEIC → jpeg, etc.)
    media_type = _normalize_media_type(file_type, filename or file_path)
    
    # Create Claude client
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # Prompt optimizado con detección internacional
    prompt = """Analiza esta factura o ticket y extrae la siguiente información en formato JSON.

IMPORTANTE: Devuelve SOLO el JSON, sin explicaciones ni texto adicional.

🌍 DETECCIÓN DE FECHAS MULTIIDIOMA:
La fecha puede estar en CUALQUIER idioma. SIEMPRE convierte a formato DD/MM/YYYY:

Ejemplos:
- "17 de desembre de 2025" (catalán) → "17/12/2025"
- "17 de diciembre de 2025" (español) → "17/12/2025"  
- "December 17, 2025" (inglés) → "17/12/2025"
- "17 dicembre 2025" (italiano) → "17/12/2025"
- "17 décembre 2025" (francés) → "17/12/2025"
- "17 de dezembro de 2025" (portugués) → "17/12/2025"

Meses (número correspondiente):
Enero/gener/January/gennaio/janvier/janeiro = 01
Febrero/febrer/February/febbraio/février/fevereiro = 02
Marzo/març/March/marzo/mars/março = 03
Abril/abril/April/aprile/avril/abril = 04
Mayo/maig/May/maggio/mai/maio = 05
Junio/juny/June/giugno/juin/junho = 06
Julio/juliol/July/luglio/juillet/julho = 07
Agosto/agost/August/agosto/août/agosto = 08
Septiembre/setembre/September/settembre/septembre/setembro = 09
Octubre/octubre/October/ottobre/octobre/outubro = 10
Noviembre/novembre/November/novembre/novembre/novembro = 11
Diciembre/desembre/December/dicembre/décembre/dezembro = 12

🌍 DETECCIÓN AUTOMÁTICA FACTURA INTERNACIONAL - MUY IMPORTANTE:

Detecta si la factura NO es de España peninsular/Baleares:

INDICADORES DE FACTURA INTERNACIONAL:
1. Símbolo de divisa diferente a €: $, £, CHF, kr, ¥, etc.
2. Dirección del proveedor fuera de España peninsular/Baleares
3. Idioma de la factura (inglés, francés, alemán, etc.)
4. IVA con nombre extranjero: VAT, Sales Tax, MwSt, TVA, IVA (no español), IGIC (Canarias)

Si detectas cualquiera de estos indicadores:
- is_foreign: true
- currency: Divisa detectada (USD, GBP, CHF, EUR si es UE, etc.)
- country_code: Código país de 2 letras (US, GB, FR, DE, IC para Canarias, etc.)
- foreign_amount: Importe base en divisa original
- foreign_total: Total en divisa original
- foreign_tax_amount: IVA/VAT en divisa original

Ejemplos de clasificación:
- Factura de Madrid → is_foreign: false, currency: "EUR", country_code: "ES"
- Factura de Canarias (IGIC) → is_foreign: true, currency: "EUR", country_code: "IC"
- Factura de París → is_foreign: true, currency: "EUR", country_code: "FR"
- Factura de New York → is_foreign: true, currency: "USD", country_code: "US"
- Factura de Londres → is_foreign: true, currency: "GBP", country_code: "GB"

🍽️ RECARGOS DE SERVICIO — NO SON IMPUESTOS:
Staff Charge, Service Charge, Gratuity, Tip → NO son IVA/Tax.
- iva_amount = solo el impuesto real (Tax, Sales Tax, VAT, IVA)
- Si no hay línea de Tax/impuesto → iva_amount = 0, iva_percentage = 0
- final_total = SIEMPRE el total impreso en el ticket, NO lo calcules
- Ejemplo: Subtotal $9.00, Staff Charge $1.67, Tax $1.12, Total $11.79
  → base_amount = 9.00, iva_amount = 1.12, final_total = 11.79

REGLA CRÍTICA — IMPORTES SIEMPRE EN DIVISA ORIGINAL:
- Extrae los importes TAL COMO aparecen impresos en el ticket
- NUNCA conviertas a EUR — el backend lo hace automáticamente
- Si el ticket es en USD → todos los importes en USD
- base_amount = foreign_amount (mismo valor)
- final_total = foreign_total (mismo valor, el total impreso)

CAMPOS A EXTRAER:

CAMPOS BÁSICOS:
- date: Fecha (SIEMPRE DD/MM/YYYY)
- provider: Nombre del proveedor/empresa
- invoice_number: Número de factura (si existe)
- base_amount: Base imponible (en la divisa del ticket, NO convertir)
- iva_percentage: Porcentaje de IVA/VAT (0.21 para 21%, 0.20 para 20%, etc.)
- iva_amount: Cantidad de IVA/Tax real (NO incluir service charges)
- total_with_iva: Total con IVA (en la divisa del ticket)
- irpf_percentage: Porcentaje de IRPF si aplica (0.15 para 15%, 0 si no hay)
- irpf_amount: Cantidad retenida de IRPF (0 si no hay)
- final_total: Total impreso en el ticket (NUNCA calcularlo, copiar el número exacto)
- type: "factura" si tiene número de factura y NIF/CIF, "ticket" si es ticket simple

CAMPOS INTERNACIONAL (solo si is_foreign es true):
- is_foreign: true/false (¿es factura internacional?)
- currency: Código divisa (USD, GBP, CHF, EUR, etc.)
- country_code: Código país ISO 2 letras (US, GB, FR, IC, etc.)
- foreign_amount: Base imponible en divisa original
- foreign_total: Total en divisa original
- foreign_tax_amount: IVA/VAT en divisa original

CAMPOS CONTACTO (solo facturas):
- phone: Teléfono del proveedor (solo si es factura y está visible)
- email: Email del proveedor (solo si es factura y está visible)
- contact_name: Nombre de contacto (solo si es factura y está visible)

CAMPOS META:
- confidence: Nivel de confianza (0.0 a 1.0)

Si no encuentras algún campo, usa null para strings y 0.0 para números.

FORMATO DE RESPUESTA (JSON puro, sin markdown):

Ejemplo 1 - Factura nacional (España):
{
  "date": "17/12/2025",
  "provider": "Ariadna Soto Abellan",
  "invoice_number": "095",
  "base_amount": 400.00,
  "iva_percentage": 0.21,
  "iva_amount": 84.00,
  "total_with_iva": 484.00,
  "irpf_percentage": 0.15,
  "irpf_amount": 60.00,
  "final_total": 424.00,
  "type": "factura",
  "is_foreign": false,
  "currency": "EUR",
  "country_code": "ES",
  "foreign_amount": null,
  "foreign_total": null,
  "foreign_tax_amount": null,
  "phone": "+34 650 088 184",
  "email": "handycrushh@gmail.com",
  "contact_name": "Ariadna Soto Abellan",
  "confidence": 0.95
}

Ejemplo 2 - Factura USA (USD) — importes en divisa original, NO convertir:
{
  "date": "15/01/2025",
  "provider": "Amazon Web Services Inc.",
  "invoice_number": "INV-2025-00123",
  "base_amount": 500.00,
  "iva_percentage": 0.075,
  "iva_amount": 37.50,
  "total_with_iva": 537.50,
  "irpf_percentage": 0.0,
  "irpf_amount": 0.0,
  "final_total": 537.50,
  "type": "factura",
  "is_foreign": true,
  "currency": "USD",
  "country_code": "US",
  "foreign_amount": 500.00,
  "foreign_total": 537.50,
  "foreign_tax_amount": 37.50,
  "phone": "+1 206 266 1000",
  "email": "billing@aws.com",
  "contact_name": "AWS Billing",
  "confidence": 0.93
}

Ejemplo 3 - Factura Canarias (EUR con IGIC):
{
  "date": "10/02/2025",
  "provider": "Hotel Costa Teguise",
  "invoice_number": "2025/045",
  "base_amount": 850.00,
  "iva_percentage": 0.085,
  "iva_amount": 72.25,
  "total_with_iva": 922.25,
  "irpf_percentage": 0.0,
  "irpf_amount": 0.0,
  "final_total": 922.25,
  "type": "factura",
  "is_foreign": true,
  "currency": "EUR",
  "country_code": "IC",
  "foreign_amount": 850.00,
  "foreign_total": 922.25,
  "foreign_tax_amount": 72.25,
  "phone": "+34 928 123 456",
  "email": "info@hotelcostateguise.com",
  "contact_name": "Recepción",
  "confidence": 0.97
}
"""
    
    # Call Claude API
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
                            "data": base64_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    
    # Extract JSON from response
    response_text = strip_markdown_json(message.content[0].text)

    # Parse JSON
    try:
        extracted_data = json.loads(response_text)
        # Claude sometimes wraps the result in an array
        if isinstance(extracted_data, list):
            extracted_data = extracted_data[0] if extracted_data else {}
        return extracted_data
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return error
        return {
            "error": "Failed to parse AI response",
            "raw_response": response_text,
            "confidence": 0.0
        }
