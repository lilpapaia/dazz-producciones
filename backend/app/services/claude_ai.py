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
    
    # Prompt optimizado para facturas españolas
    prompt = """Analiza esta factura o ticket español y extrae la siguiente información en formato JSON.

IMPORTANTE: Devuelve SOLO el JSON, sin explicaciones ni texto adicional.

Campos a extraer:
- date: Fecha de la factura (formato DD/MM/YYYY)
- provider: Nombre del proveedor/empresa
- invoice_number: Número de factura (si existe)
- base_amount: Base imponible (importe sin IVA)
- iva_percentage: Porcentaje de IVA (0.21 para 21%, 0.10 para 10%, etc.)
- iva_amount: Cantidad de IVA en euros
- total_with_iva: Total con IVA
- irpf_percentage: Porcentaje de IRPF si aplica (0.15 para 15%, 0 si no hay)
- irpf_amount: Cantidad retenida de IRPF en euros (0 si no hay)
- final_total: Total final (total_with_iva - irpf_amount)
- type: "factura" si tiene número de factura y NIF/CIF, "ticket" si es un ticket simple
- phone: Teléfono del proveedor (solo si es factura y está visible)
- email: Email del proveedor (solo si es factura y está visible)
- contact_name: Nombre de contacto o departamento (solo si es factura y está visible)
- confidence: Nivel de confianza en la extracción (0.0 a 1.0)

CÁLCULOS:
- iva_amount = base_amount * iva_percentage
- total_with_iva = base_amount + iva_amount
- irpf_amount = base_amount * irpf_percentage (si aplica)
- final_total = total_with_iva - irpf_amount

Si no encuentras algún campo, usa null para strings y 0.0 para números.

FORMATO DE RESPUESTA (JSON puro, sin markdown):
{
  "date": "15/02/2026",
  "provider": "MediaMarkt España",
  "invoice_number": "F-2026-1234",
  "base_amount": 195.04,
  "iva_percentage": 0.21,
  "iva_amount": 40.96,
  "total_with_iva": 236.00,
  "irpf_percentage": 0.0,
  "irpf_amount": 0.0,
  "final_total": 236.00,
  "type": "factura",
  "phone": "+34 912 345 678",
  "email": "facturas@mediamarkt.es",
  "contact_name": "Dpto. Facturación",
  "confidence": 0.95
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
