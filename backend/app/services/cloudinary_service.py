"""
Servicio Cloudinary para almacenamiento de tickets/facturas
- Imágenes: convierte a WebP automáticamente CON MEJORAS DE CALIDAD
- PDFs: convierte páginas a imágenes WebP + guarda PDF original
- Compresión inteligente para archivos grandes
"""

import logging
import cloudinary
import cloudinary.uploader
import os
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

# VULN-002: Credenciales obligatorias — sin valores hardcodeados
_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
_api_key = os.getenv("CLOUDINARY_API_KEY")
_api_secret = os.getenv("CLOUDINARY_API_SECRET")

if not all([_cloud_name, _api_key, _api_secret]):
    raise RuntimeError(
        "Cloudinary credentials are required. "
        "Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET environment variables."
    )

cloudinary.config(
    cloud_name=_cloud_name,
    api_key=_api_key,
    api_secret=_api_secret,
    secure=True
)


def compress_if_needed(image_path: str, max_size_mb: float = 2.0) -> str:
    """
    Comprime una imagen si es muy grande, devuelve el path (original o comprimido).
    
    Args:
        image_path: Path a la imagen
        max_size_mb: Tamaño máximo en MB
    
    Returns:
        str: Path a la imagen (puede ser la misma u otra comprimida)
    """
    file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
    
    # Si es pequeña, no hacer nada
    if file_size_mb <= max_size_mb:
        return image_path
    
    logger.info(f"Comprimiendo {file_size_mb:.2f}MB → objetivo {max_size_mb}MB")
    
    # Comprimir
    img = Image.open(image_path)
    
    # Redimensionar si es muy grande
    max_dimension = 1920
    if img.width > max_dimension or img.height > max_dimension:
        ratio = min(max_dimension / img.width, max_dimension / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convertir a RGB si es necesario
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Guardar comprimido
    base, ext = os.path.splitext(image_path)
    compressed_path = f"{base}_compressed.jpg"
    quality = 85
    
    while quality > 20:
        img.save(compressed_path, "JPEG", quality=quality, optimize=True)
        new_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
        
        if new_size_mb <= max_size_mb:
            logger.info(f"Comprimido a {new_size_mb:.2f}MB (quality={quality})")
            return compressed_path
        
        quality -= 10
    
    # Si no se logra, devolver lo mejor posible
    logger.warning(f"Comprimido a {new_size_mb:.2f}MB (quality mínima)")
    return compressed_path


def upload_image(file_path: str, public_id: str, folder: str = None) -> dict:
    """
    Sube imagen a Cloudinary con MEJORAS AUTOMÁTICAS

    Transformaciones aplicadas:
    - Mejora de nitidez (sharpen)
    - Auto-contraste
    - Auto-rotación (tickets torcidos)
    - Compresión WebP inteligente
    """
    upload_kwargs = dict(
        public_id=public_id,
        resource_type="image",
        format="webp",
        transformation=[
            {"width": 2048, "height": 2048, "crop": "limit"},
            {"effect": "sharpen:100"},
            {"effect": "auto_contrast"},
            {"angle": "auto"},
            {"quality": "auto:best"}
        ],
        access_mode="public",
        overwrite=True,
    )
    if folder:
        upload_kwargs["folder"] = folder

    result = cloudinary.uploader.upload(file_path, **upload_kwargs)

    logger.info("Imagen mejorada automáticamente (nitidez + contraste + rotación)")

    return {"url": result["secure_url"], "public_id": result["public_id"]}


def upload_pdf_original(file_path: str, public_id: str, folder: str = None) -> dict:
    """Sube PDF original para descarga (solo si <9MB)"""
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    if file_size_mb > 9:
        logger.warning(f"PDF muy grande ({file_size_mb:.2f}MB), no se subirá el original")
        return None

    upload_kwargs = dict(
        public_id=public_id + "_original",
        resource_type="auto",
        access_mode="public",
        overwrite=True,
    )
    if folder:
        upload_kwargs["folder"] = folder

    result = cloudinary.uploader.upload(file_path, **upload_kwargs)
    return {"url": result["secure_url"], "public_id": result["public_id"]}


def upload_ticket_file(file_path: str, file_name: str, project_id: int, project_oc: str = None) -> dict:
    """
    Procesa y sube un archivo a Cloudinary.

    - Imágenes JPG/PNG → WebP en Cloudinary CON MEJORAS AUTOMÁTICAS
    - PDFs → convierte cada página a WebP + guarda PDF original

    Returns dict con:
      - url: URL de la primera imagen (o única)
      - pages: lista de URLs de todas las páginas (para PDFs multipágina)
      - pdf_url: URL del PDF original para descarga (solo PDFs)
    """
    import uuid as _uuid
    file_ext = Path(file_name).suffix.lower()
    is_pdf = file_ext == '.pdf'
    oc_slug = (project_oc or f"project_{project_id}").replace(' ', '_')
    folder = f"dazz-producciones/{oc_slug}"
    short_id = _uuid.uuid4().hex[:8]
    clean_name = Path(file_name).stem.replace(' ', '_')[:50]
    public_id = f"{clean_name}_{short_id}"

    if is_pdf:
        logger.info(f"Procesando PDF: {file_name}")
        
        # Verificar tamaño del PDF
        pdf_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # Usar DPI más bajo si el PDF es grande (escaneos)
        dpi = 150 if pdf_size_mb > 5 else 200
        logger.info(f"Tamaño: {pdf_size_mb:.2f}MB → usando DPI={dpi}")
        
        # 1. Convertir páginas a imágenes
        from pdf2image import convert_from_path
        pages = convert_from_path(file_path, dpi=dpi)
        
        page_urls = []
        temp_files = []  # Para limpiar después
        
        for i, page_img in enumerate(pages):
            # Guardar página como JPG temporal
            temp_page_path = f"{file_path}_page_{i+1}.jpg"
            page_img.save(temp_page_path, "JPEG", quality=90)
            temp_files.append(temp_page_path)
            
            try:
                # Comprimir si es muy grande
                final_path = compress_if_needed(temp_page_path, max_size_mb=2.5)
                if final_path != temp_page_path:
                    temp_files.append(final_path)
                
                # Subir página a Cloudinary como WebP CON MEJORAS
                result = upload_image(final_path, f"{public_id}_page_{i+1}", folder=folder)
                page_urls.append(result["url"])
                logger.info(f"Página {i+1}/{len(pages)} subida y mejorada")
            except Exception as e:
                logger.error(f"Error en página {i+1}: {str(e)}")
                raise
        
        # Limpiar archivos temporales
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Temp file cleanup failed: {e}")

        # 2. Subir PDF original para descarga (si no es muy grande)
        pdf_result = upload_pdf_original(file_path, public_id, folder=folder)
        pdf_url = pdf_result["url"] if pdf_result else None
        
        return {
            "url": page_urls[0] if page_urls else None,
            "pages": page_urls,
            "pdf_url": pdf_url,
            "public_id": public_id,
            "is_pdf": True,
            "page_count": len(pages)
        }
    else:
        # Imagen normal
        logger.info(f"Procesando imagen: {file_name}")
        
        # Comprimir si es muy grande
        final_path = compress_if_needed(file_path, max_size_mb=3.0)
        temp_compressed = final_path if final_path != file_path else None
        
        try:
            result = upload_image(final_path, public_id, folder=folder)
            logger.info("Imagen subida y mejorada")
            
            return {
                "url": result["url"],
                "pages": [result["url"]],
                "pdf_url": None,
                "public_id": result["public_id"],
                "is_pdf": False,
                "page_count": 1
            }
        finally:
            # Limpiar archivo comprimido temporal
            if temp_compressed and os.path.exists(temp_compressed):
                try:
                    os.remove(temp_compressed)
                except Exception as e:
                    logger.warning(f"Temp compressed file cleanup failed: {e}")


def delete_ticket_files(file_pages_json: str = None, pdf_url: str = None) -> bool:
    """
    Elimina todos los archivos de un ticket de Cloudinary.
    
    Args:
        file_pages_json: JSON string con lista de URLs de páginas
        pdf_url: URL del PDF original (si existe)
    
    Returns:
        bool: True si todo se eliminó correctamente
    """
    import json
    
    deleted_count = 0
    
    # Eliminar páginas de imágenes
    if file_pages_json:
        try:
            pages = json.loads(file_pages_json)
            for page_url in pages:
                try:
                    public_id = extract_public_id_from_url(page_url)
                    if public_id:
                        cloudinary.uploader.destroy(public_id)
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Error eliminando imagen {page_url}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error procesando páginas: {str(e)}")
    
    # Eliminar PDF original
    if pdf_url:
        try:
            public_id = extract_public_id_from_url(pdf_url)
            if public_id:
                cloudinary.uploader.destroy(public_id, resource_type="raw")
                deleted_count += 1
        except Exception as e:
            logger.warning(f"Error eliminando PDF {pdf_url}: {str(e)}")

    logger.info(f"Eliminados {deleted_count} archivos de Cloudinary")
    return deleted_count > 0


def extract_public_id_from_url(url: str) -> str:
    """
    Extrae el public_id de una URL de Cloudinary
    
    Ejemplo:
    https://res.cloudinary.com/dyjpek4q8/image/upload/v1234/dazz-producciones/project_4/ticket_1.webp
    → dazz-producciones/project_4/ticket_1
    """
    try:
        # Separar por '/'
        parts = url.split('/')
        
        # Encontrar 'upload' o 'raw' en la URL
        upload_index = -1
        for i, part in enumerate(parts):
            if part == 'upload':
                upload_index = i
                break
        
        if upload_index == -1:
            return None
        
        # El public_id está después de 'upload/vXXXX/'
        # Saltar version (vXXXX)
        path_parts = parts[upload_index + 2:]
        
        # Unir el resto y quitar extensión
        public_id = '/'.join(path_parts)
        public_id = public_id.rsplit('.', 1)[0]  # Quitar .webp, .jpg, etc
        
        return public_id
    except Exception as e:
        logger.warning(f"Error extrayendo public_id de {url}: {str(e)}")
        return None


