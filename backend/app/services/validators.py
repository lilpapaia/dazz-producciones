"""
Validadores de Seguridad para Inputs
=====================================

Protección contra:
- SQL Injection (ya protegido por SQLAlchemy ORM, pero validación extra)
- XSS (Cross-Site Scripting)
- File uploads maliciosos
- Email/Phone inválidos
- Path traversal
"""

import re
import html
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from pathlib import Path


# ============================================
# CONSTANTES
# ============================================

# Extensiones permitidas para uploads (compatible con sistema actual)
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

# Tamaño máximo de archivo
# Nota: Frontend comprime imágenes >3MB automáticamente
# PDFs NO se comprimen y pueden ser grandes (hasta 20-30MB)
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10MB para imágenes (después de compresión frontend)
MAX_PDF_SIZE = 30 * 1024 * 1024     # 30MB para PDFs (sin compresión)

# MIME types permitidos (compatible con sistema actual)
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/jpg',      # Algunas apps usan image/jpg
    'image/png',
    'application/pdf'
}

# Patrones de validación
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

PHONE_PATTERN = re.compile(
    r'^\+?[\d\s\-\(\)]{9,20}$'
)

# Caracteres peligrosos para path traversal
DANGEROUS_PATH_CHARS = ['..', '~', '/', '\\']


# ============================================
# VALIDACIÓN DE STRINGS
# ============================================

def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitiza string para prevenir XSS
    
    Args:
        text: String a sanitizar
        max_length: Longitud máxima permitida
    
    Returns:
        String sanitizado
    
    Raises:
        ValueError: Si el string es inválido
    """
    if not isinstance(text, str):
        raise ValueError("Input debe ser string")
    
    # Escapar HTML
    sanitized = html.escape(text.strip())
    
    # Truncar si es necesario
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_no_sql_patterns(text: str) -> bool:
    """
    DEPRECATED — No usar en validaciones nuevas.

    SQLAlchemy ORM con queries parametrizadas es la protección real contra
    SQL injection. Esta función tiene patrones incompletos (no detecta
    bypasses con comentarios, encoding, etc.) y causa falsos positivos
    (ej: una descripción con "DELETE FROM the old records" sería rechazada).

    Se mantiene por compatibilidad pero ya no se llama desde
    validate_string_input(). Si necesitas validación de input, usa
    sanitize_string() para XSS y confía en el ORM para SQL.

    Returns:
        True si es seguro según estos patrones (incompletos), False si sospechoso
    """
    # Patrones sospechosos (case-insensitive)
    dangerous_patterns = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(--)",  # Comentarios SQL
        r"(\/\*|\*\/)",  # Comentarios multi-línea
        r"(\bEXEC\b|\bEXECUTE\b)",
    ]
    
    text_upper = text.upper()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text_upper, re.IGNORECASE):
            return False
    
    return True


def validate_string_input(
    text: str,
    field_name: str,
    min_length: int = 1,
    max_length: int = 500,
    allow_special_chars: bool = True
) -> str:
    """
    Validación completa de string input
    
    Args:
        text: String a validar
        field_name: Nombre del campo (para mensajes de error)
        min_length: Longitud mínima
        max_length: Longitud máxima
        allow_special_chars: Si permite caracteres especiales
    
    Returns:
        String validado y sanitizado
    
    Raises:
        HTTPException: Si la validación falla
    """
    if not text or not isinstance(text, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} es requerido y debe ser texto"
        )
    
    text = text.strip()
    
    # Validar longitud
    if len(text) < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} debe tener al menos {min_length} caracteres"
        )
    
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} no puede tener más de {max_length} caracteres"
        )
    
    # SEC-M5: Eliminada llamada a validate_no_sql_patterns() — la protección real
    # contra SQL injection es SQLAlchemy ORM con queries parametrizadas.
    # La función regex tenía patrones incompletos y causaba falsos positivos.

    # Validar caracteres especiales si no están permitidos
    if not allow_special_chars:
        if not text.replace(" ", "").replace("-", "").replace("_", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} solo puede contener letras, números, espacios, guiones"
            )
    
    # Sanitizar
    return sanitize_string(text, max_length)


# ============================================
# VALIDACIÓN DE EMAIL
# ============================================

def validate_email(email: str) -> str:
    """
    Valida formato de email estrictamente
    
    Args:
        email: Email a validar
    
    Returns:
        Email validado en lowercase
    
    Raises:
        HTTPException: Si el email es inválido
    """
    if not email or not isinstance(email, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email es requerido"
        )
    
    email = email.strip().lower()
    
    # Validar longitud
    if len(email) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email demasiado largo"
        )
    
    # Validar formato
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de email inválido"
        )
    
    # Validar que no tenga caracteres peligrosos
    dangerous_chars = ['<', '>', '"', "'", '\\', '/', ';']
    if any(char in email for char in dangerous_chars):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email contiene caracteres no permitidos"
        )
    
    return email


# ============================================
# VALIDACIÓN DE TELÉFONO
# ============================================

def validate_phone(phone: str) -> str:
    """
    Valida formato de teléfono
    
    Args:
        phone: Teléfono a validar
    
    Returns:
        Teléfono validado
    
    Raises:
        HTTPException: Si el teléfono es inválido
    """
    if not phone or not isinstance(phone, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teléfono es requerido"
        )
    
    phone = phone.strip()
    
    # Validar formato
    if not PHONE_PATTERN.match(phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de teléfono inválido (debe tener 9-20 dígitos)"
        )

    # SEC-L2: Exigir al menos 9 dígitos efectivos (evita strings con solo guiones/paréntesis)
    digit_count = sum(c.isdigit() for c in phone)
    if digit_count < 9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Teléfono debe tener al menos 9 dígitos (tiene {digit_count})"
        )

    return phone


# ============================================
# VALIDACIÓN DE ARCHIVOS
# ============================================

async def validate_file_upload(
    file: UploadFile,
    allowed_extensions: Optional[set] = None,
    max_size: Optional[int] = None  # Si no se especifica, usa límite según tipo
) -> None:
    """
    Valida archivo subido (compatible con sistema actual de DAZZ)
    
    IMPORTANTE:
    - Imágenes: max 10MB (frontend las comprime a 3MB primero)
    - PDFs: max 30MB (NO se comprimen, pueden ser grandes)
    
    Args:
        file: Archivo a validar
        allowed_extensions: Extensiones permitidas (default: imágenes + PDF)
        max_size: Tamaño máximo en bytes (si None, usa límite según tipo)
    
    Raises:
        HTTPException: Si el archivo es inválido
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo es requerido"
        )
    
    # Validar extensión
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS
    
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión {file_ext} no permitida. Permitidas: {', '.join(allowed_extensions)}"
        )
    
    # Validar MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo {file.content_type} no permitido"
        )
    
    # Leer contenido para validar tamaño
    contents = await file.read()
    file_size = len(contents)
    
    # Resetear puntero del archivo
    await file.seek(0)
    
    # Determinar límite de tamaño según tipo de archivo
    if max_size is None:
        # Si es PDF, usar límite de PDF (30MB)
        # Si es imagen, usar límite de imagen (10MB)
        if file.content_type == 'application/pdf':
            max_size = MAX_PDF_SIZE
        else:
            max_size = MAX_IMAGE_SIZE
    
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        file_size_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo demasiado grande ({file_size_mb:.2f}MB). Máximo permitido: {max_size_mb:.0f}MB"
        )
    
    # Validar nombre de archivo (path traversal)
    if any(char in file.filename for char in DANGEROUS_PATH_CHARS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de archivo contiene caracteres peligrosos"
        )


def validate_pdf_bytes(contents: bytes, max_size: int = MAX_PDF_SIZE) -> None:
    """
    Validate pre-read PDF bytes: magic bytes + file size.

    Use this when contents have already been read from the UploadFile
    (avoids double file.read() from validate_file_upload).

    Args:
        contents: Raw file bytes
        max_size: Max allowed size in bytes (default: MAX_PDF_SIZE)

    Raises:
        HTTPException: If validation fails
    """
    if not contents or len(contents) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty or too small to be a valid PDF"
        )

    # Magic bytes: every PDF starts with %PDF
    if contents[:4] != b"%PDF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not a valid PDF (invalid magic bytes)"
        )

    if len(contents) > max_size:
        max_mb = max_size / (1024 * 1024)
        file_mb = len(contents) / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({file_mb:.1f}MB). Max allowed: {max_mb:.0f}MB"
        )


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza nombre de archivo para evitar path traversal
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        Nombre sanitizado
    """
    # Eliminar path (solo quedarse con el nombre)
    filename = Path(filename).name
    
    # Eliminar caracteres peligrosos
    filename = re.sub(r'[^\w\s\-\.]', '_', filename)
    
    # Eliminar espacios múltiples
    filename = re.sub(r'\s+', '_', filename)

    # Normalizar extensión a minúsculas (.JPG → .jpg)
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower()
    filename = f"{stem}{ext}"

    return filename


# ============================================
# VALIDACIÓN DE NÚMEROS
# ============================================

def validate_positive_number(
    value: float,
    field_name: str,
    allow_zero: bool = False
) -> float:
    """
    Valida que un número sea positivo
    
    Args:
        value: Valor a validar
        field_name: Nombre del campo
        allow_zero: Si permite cero
    
    Returns:
        Valor validado
    
    Raises:
        HTTPException: Si el valor es inválido
    """
    if not isinstance(value, (int, float)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} debe ser un número"
        )
    
    min_value = 0 if allow_zero else 0.01
    
    if value < min_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} debe ser {'mayor o igual a' if allow_zero else 'mayor que'} {min_value}"
        )
    
    return float(value)


# ============================================
# VALIDACIÓN DE IDs
# ============================================

def validate_iban_format(iban: str) -> str:
    """
    SEC-M1: Valida formato IBAN con checksum mod-97 (ISO 13616).

    Args:
        iban: IBAN string (puede tener espacios)

    Returns:
        IBAN limpio (sin espacios, uppercase)

    Raises:
        HTTPException 400 si el formato es inválido
    """
    cleaned = iban.strip().upper().replace(" ", "")

    if len(cleaned) < 15 or len(cleaned) > 34:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IBAN must be between 15 and 34 characters"
        )

    if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid IBAN format (must start with 2-letter country code + 2 check digits)"
        )

    # Mod-97 checksum: move first 4 chars to end, convert letters to numbers (A=10..Z=35)
    rearranged = cleaned[4:] + cleaned[:4]
    numeric_str = ""
    for char in rearranged:
        if char.isdigit():
            numeric_str += char
        else:
            numeric_str += str(ord(char) - ord('A') + 10)

    if int(numeric_str) % 97 != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid IBAN checksum"
        )

    return cleaned


def validate_id(value: int, field_name: str = "ID") -> int:
    """
    Valida que un ID sea válido
    
    Args:
        value: ID a validar
        field_name: Nombre del campo
    
    Returns:
        ID validado
    
    Raises:
        HTTPException: Si el ID es inválido
    """
    if not isinstance(value, int) or value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} debe ser un número entero positivo"
        )
    
    return value
