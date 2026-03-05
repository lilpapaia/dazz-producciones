import os
import cloudinary
import cloudinary.uploader
from pdf2image import convert_from_path
from PIL import Image
import io
import tempfile

# Configuración de Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def compress_image(image: Image.Image, max_size_mb: float = 2.0, quality: int = 85) -> bytes:
    """
    Comprime una imagen PIL a menos de max_size_mb.
    
    Args:
        image: Imagen PIL
        max_size_mb: Tamaño máximo en MB
        quality: Calidad JPEG inicial (0-100)
    
    Returns:
        bytes: Imagen comprimida en formato JPEG
    """
    # Redimensionar si es muy grande (máximo 1920px en cualquier dimensión)
    max_dimension = 1920
    if image.width > max_dimension or image.height > max_dimension:
        ratio = min(max_dimension / image.width, max_dimension / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convertir RGBA a RGB si es necesario
    if image.mode == 'RGBA':
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Comprimir iterativamente hasta cumplir el tamaño objetivo
    max_size_bytes = max_size_mb * 1024 * 1024
    current_quality = quality
    
    while current_quality > 20:
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=current_quality, optimize=True)
        size = buffer.tell()
        
        if size <= max_size_bytes:
            buffer.seek(0)
            return buffer.read()
        
        # Reducir calidad gradualmente
        current_quality -= 5
    
    # Si no se logra, devolver con calidad mínima
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=20, optimize=True)
    buffer.seek(0)
    return buffer.read()


def upload_ticket_file(file_path: str, ticket_id: int, file_type: str):
    """
    Sube un archivo de ticket a Cloudinary.
    
    Para imágenes: las comprime y convierte a WebP
    Para PDFs: convierte cada página a imagen comprimida, sube como WebP individual
    
    Args:
        file_path: Ruta al archivo temporal
        ticket_id: ID del ticket
        file_type: Tipo MIME del archivo
    
    Returns:
        dict con:
        - file_pages: lista de URLs de las páginas (imágenes)
        - pdf_url: URL del PDF original (solo si es PDF y <8MB)
    """
    result = {
        "file_pages": [],
        "pdf_url": None
    }
    
    # Verificar tamaño del archivo
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    if file_type == "application/pdf":
        # Convertir PDF a imágenes con DPI reducido para escaneos
        # DPI=150 es suficiente para lectura (vs 200 por defecto)
        print(f"Converting PDF to images (DPI=150, file size: {file_size_mb:.2f}MB)...")
        images = convert_from_path(file_path, dpi=150)
        
        print(f"PDF has {len(images)} pages. Compressing and uploading...")
        
        # Subir cada página comprimida
        for i, image in enumerate(images, 1):
            # Comprimir imagen agresivamente (máximo 2MB por página)
            compressed_data = compress_image(image, max_size_mb=2.0, quality=80)
            
            # Subir a Cloudinary desde bytes
            upload_result = cloudinary.uploader.upload(
                compressed_data,
                folder=f"tickets/{ticket_id}",
                public_id=f"page_{i}",
                format="webp",  # Cloudinary convierte a WebP
                quality="auto:good",  # Compresión adicional de Cloudinary
                resource_type="image"
            )
            
            result["file_pages"].append(upload_result["secure_url"])
            print(f"  Page {i}/{len(images)} uploaded: {upload_result['bytes'] / 1024:.1f}KB")
        
        # Solo subir PDF original si es <8MB (para descarga)
        if file_size_mb < 8:
            print(f"Uploading original PDF ({file_size_mb:.2f}MB) for download...")
            pdf_upload = cloudinary.uploader.upload(
                file_path,
                folder=f"tickets/{ticket_id}",
                public_id="original_pdf",
                resource_type="raw"
            )
            result["pdf_url"] = pdf_upload["secure_url"]
        else:
            print(f"PDF too large ({file_size_mb:.2f}MB), skipping original upload")
    
    else:
        # Es una imagen
        print(f"Processing image ({file_size_mb:.2f}MB)...")
        
        # Abrir y comprimir imagen
        image = Image.open(file_path)
        compressed_data = compress_image(image, max_size_mb=2.5, quality=85)
        
        # Subir a Cloudinary
        upload_result = cloudinary.uploader.upload(
            compressed_data,
            folder=f"tickets/{ticket_id}",
            public_id="image",
            format="webp",
            quality="auto:good",
            resource_type="image"
        )
        
        result["file_pages"] = [upload_result["secure_url"]]
        print(f"Image uploaded: {upload_result['bytes'] / 1024:.1f}KB")
    
    return result


def upload_image(file_path: str, folder: str, public_id: str = None):
    """
    Sube una imagen genérica a Cloudinary (comprimida).
    
    Args:
        file_path: Ruta al archivo
        folder: Carpeta en Cloudinary
        public_id: ID público (opcional)
    
    Returns:
        dict con secure_url y public_id
    """
    # Comprimir antes de subir
    image = Image.open(file_path)
    compressed_data = compress_image(image, max_size_mb=2.5, quality=85)
    
    upload_params = {
        "folder": folder,
        "format": "webp",
        "quality": "auto:good",
        "resource_type": "image"
    }
    
    if public_id:
        upload_params["public_id"] = public_id
    
    result = cloudinary.uploader.upload(compressed_data, **upload_params)
    
    return {
        "secure_url": result["secure_url"],
        "public_id": result["public_id"]
    }


def upload_pdf_original(file_path: str, ticket_id: int):
    """
    Sube un PDF original para descarga (solo si <8MB).
    
    Args:
        file_path: Ruta al PDF
        ticket_id: ID del ticket
    
    Returns:
        URL del PDF o None si es muy grande
    """
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    if file_size_mb >= 8:
        return None
    
    result = cloudinary.uploader.upload(
        file_path,
        folder=f"tickets/{ticket_id}",
        public_id="original_pdf",
        resource_type="raw"
    )
    
    return result["secure_url"]


def delete_ticket_file(file_pages: list, pdf_url: str = None):
    """
    Elimina archivos de ticket de Cloudinary.
    
    Args:
        file_pages: Lista de URLs de páginas
        pdf_url: URL del PDF original (opcional)
    """
    # Extraer public_id de las URLs y eliminar
    for url in file_pages:
        try:
            # Formato: https://res.cloudinary.com/cloud/image/upload/v123/tickets/1/page_1.webp
            parts = url.split("/")
            # Obtener todo después de "upload/"
            upload_index = parts.index("upload")
            # Quitar versión (v123) y obtener path relativo
            public_id_parts = parts[upload_index + 2:]  # Salta "upload" y "vXXX"
            public_id = "/".join(public_id_parts).rsplit(".", 1)[0]  # Quita extensión
            
            cloudinary.uploader.destroy(public_id, resource_type="image")
        except Exception as e:
            print(f"Error deleting {url}: {e}")
    
    # Eliminar PDF original si existe
    if pdf_url:
        try:
            parts = pdf_url.split("/")
            upload_index = parts.index("upload")
            public_id_parts = parts[upload_index + 2:]
            public_id = "/".join(public_id_parts).rsplit(".", 1)[0]
            
            cloudinary.uploader.destroy(public_id, resource_type="raw")
        except Exception as e:
            print(f"Error deleting PDF {pdf_url}: {e}")
