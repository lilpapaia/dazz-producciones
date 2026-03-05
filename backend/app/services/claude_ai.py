import anthropic
import json
import base64
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def extract_ticket_data(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Extract data from ticket/invoice using Claude AI
    
    MEJORAS:
    - Detecta fechas en múltiples idiomas y convierte a DD/MM/YYYY
    - Detecta automáticamente facturas internacionales
    - Extrae divisa, país, e importes originales
    
    Args:
        file_path: Path to the image/PDF file
        file_type: MIME type of the file
        
    Returns:
        Dictionary with extracted data
    """
    
    # Read and encode file
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    base64_data = base64.b64encode(file_data).decode("utf-8")
    
    # Determine media type
    if file_type.startswith("image/"):
        media_type = file_type
    elif file_type == "application/pdf":
        media_type = "application/pdf"
    else:
        media_type = "image/jpeg"  # fallback
    
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

IMPORTANTE: Si es factura internacional, extrae TANTO los importes originales EN SU DIVISA
como los convertidos a EUR (si la factura los muestra). Si solo muestra una divisa, repite
los valores en ambos campos (foreign_amount = base_amount si solo hay una divisa).

CAMPOS A EXTRAER:

CAMPOS BÁSICOS:
- date: Fecha (SIEMPRE DD/MM/YYYY)
- provider: Nombre del proveedor/empresa
- invoice_number: Número de factura (si existe)
- base_amount: Base imponible en EUR (convertir si es necesario, o dejar original si no hay conversión)
- iva_percentage: Porcentaje de IVA/VAT (0.21 para 21%, 0.20 para 20%, etc.)
- iva_amount: Cantidad de IVA en EUR
- total_with_iva: Total con IVA en EUR
- irpf_percentage: Porcentaje de IRPF si aplica (0.15 para 15%, 0 si no hay)
- irpf_amount: Cantidad retenida de IRPF en EUR (0 si no hay)
- final_total: Total final en EUR
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

Ejemplo 2 - Factura USA (USD):
{
  "date": "15/01/2025",
  "provider": "Amazon Web Services Inc.",
  "invoice_number": "INV-2025-00123",
  "base_amount": 461.70,
  "iva_percentage": 0.075,
  "iva_amount": 34.63,
  "total_with_iva": 496.33,
  "irpf_percentage": 0.0,
  "irpf_amount": 0.0,
  "final_total": 496.33,
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
        model="claude-sonnet-4-20250514",
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
    response_text = message.content[0].text.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    response_text = response_text.strip()
    
    # Parse JSON
    try:
        extracted_data = json.loads(response_text)
        return extracted_data
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return error
        return {
            "error": "Failed to parse AI response",
            "raw_response": response_text,
            "confidence": 0.0
        }
