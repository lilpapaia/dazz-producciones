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
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from pathlib import Path


# ============================================
# CONSTANTES
# ============================================

# Extensiones permitidas para uploads (compatible con sistema actual)
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

# Tamaño máximo de archivo
# Nota: Frontend comprime imágenes >3MB automáticamente
# PDFs NO se comprimen y pueden ser grandes (hasta 20-30MB)
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10MB para imágenes (después de compresión frontend)
MAX_PDF_SIZE = 30 * 1024 * 1024     # 30MB para PDFs (sin compresión)

# MIME types permitidos (compatible con sistema actual)
# Incluye variantes de dispositivos móviles y navegadores antiguos
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/jpg',        # Algunas apps usan image/jpg
    'image/pjpeg',      # Progressive JPEG (IE, dispositivos antiguos)
    'image/x-jpeg',     # Variante JPEG (algunos dispositivos Android)
    'image/png',
    'image/x-png',      # Variante PNG (navegadores antiguos)
    'image/heic',       # iPhone fotos modernas
    'image/heif',       # iPhone fotos modernas (variante)
    'image/webp',       # Capturas Chrome/Android
    'application/pdf',
    'application/octet-stream',  # Fallback genérico de algunos dispositivos
}

# Caracteres peligrosos para path traversal
DANGEROUS_PATH_CHARS = ['..', '~', '/', '\\']


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
    
    # Validar extensión (con fallback a content_type si filename no tiene extensión)
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS

    file_ext = Path(file.filename).suffix.lower()

    # Fallback: si no hay extensión, inferir del content_type
    if not file_ext:
        _MIME_TO_EXT = {
            'image/jpeg': '.jpg', 'image/jpg': '.jpg', 'image/pjpeg': '.jpg', 'image/x-jpeg': '.jpg',
            'image/png': '.png', 'image/x-png': '.png',
            'image/heic': '.heic', 'image/heif': '.heif',
            'image/webp': '.webp',
            'application/pdf': '.pdf',
        }
        inferred = _MIME_TO_EXT.get((file.content_type or "").lower())
        if inferred:
            file_ext = inferred

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión '{file_ext or '(ninguna)'}' no permitida. Permitidas: {', '.join(sorted(allowed_extensions))}"
        )

    # Validar MIME type (normalizar a lowercase — algunos dispositivos envían Image/Jpeg)
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_MIME_TYPES:
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
    cleaned = iban.strip().upper().replace(" ", "").replace("-", "").replace(".", "")

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


