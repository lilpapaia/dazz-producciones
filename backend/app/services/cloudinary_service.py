"""
Servicio Cloudinary para almacenamiento de tickets/facturas
- Imágenes: convierte a WebP automáticamente
- PDFs: convierte páginas a imágenes WebP + guarda PDF original
- Compresión inteligente para archivos grandes
"""

import cloudinary
import cloudinary.uploader
import os
from pathlib import Path
from PIL import Image

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dyjpek4q8"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "869752186781145"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
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
    
    print(f"  🗜️ Comprimiendo {file_size_mb:.2f}MB → objetivo {max_size_mb}MB")
    
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
    compressed_path = image_path.replace('.jpg', '_compressed.jpg')
    quality = 85
    
    while quality > 20:
        img.save(compressed_path, "JPEG", quality=quality, optimize=True)
        new_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
        
        if new_size_mb <= max_size_mb:
            print(f"  ✅ Comprimido a {new_size_mb:.2f}MB (quality={quality})")
            return compressed_path
        
        quality -= 10
    
    # Si no se logra, devolver lo mejor posible
    print(f"  ⚠️ Comprimido a {new_size_mb:.2f}MB (quality mínima)")
    return compressed_path


def upload_image(file_path: str, public_id: str) -> dict:
    """Sube imagen convirtiéndola a WebP"""
    result = cloudinary.uploader.upload(
        file_path,
        public_id=public_id,
        resource_type="image",
        format="webp",
        quality="auto:good",
        transformation=[
            {"width": 2048, "height": 2048, "crop": "limit"},
            {"quality": "auto:good"},
            {"format": "webp"}
        ],
        access_mode="public",
        overwrite=True
    )
    return {"url": result["secure_url"], "public_id": result["public_id"]}


def upload_pdf_original(file_path: str, public_id: str) -> dict:
    """Sube PDF original para descarga (solo si <9MB)"""
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    if file_size_mb > 9:
        print(f"⚠️ PDF muy grande ({file_size_mb:.2f}MB), no se subirá el original")
        return None
    
    result = cloudinary.uploader.upload(
        file_path,
        public_id=public_id + "_original",
        resource_type="auto",
        access_mode="public",
        overwrite=True
    )
    return {"url": result["secure_url"], "public_id": result["public_id"]}


def upload_ticket_file(file_path: str, file_name: str, project_id: int) -> dict:
    """
    Procesa y sube un archivo a Cloudinary.
    
    - Imágenes JPG/PNG → WebP en Cloudinary
    - PDFs → convierte cada página a WebP + guarda PDF original
    
    Returns dict con:
      - url: URL de la primera imagen (o única)
      - pages: lista de URLs de todas las páginas (para PDFs multipágina)
      - pdf_url: URL del PDF original para descarga (solo PDFs)
    """
    file_ext = Path(file_name).suffix.lower()
    is_pdf = file_ext == '.pdf'
    folder = f"dazz-producciones/project_{project_id}"
    clean_name = Path(file_name).stem.replace(' ', '_')[:50]
    public_id = f"{folder}/{clean_name}"

    if is_pdf:
        print(f"📄 Procesando PDF: {file_name}")
        
        # Verificar tamaño del PDF
        pdf_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # Usar DPI más bajo si el PDF es grande (escaneos)
        dpi = 150 if pdf_size_mb > 5 else 200
        print(f"  Tamaño: {pdf_size_mb:.2f}MB → usando DPI={dpi}")
        
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
                
                # Subir página a Cloudinary como WebP
                result = upload_image(final_path, f"{public_id}_page_{i+1}")
                page_urls.append(result["url"])
                print(f"  ✅ Página {i+1}/{len(pages)} subida")
            except Exception as e:
                print(f"  ❌ Error en página {i+1}: {str(e)}")
                raise
        
        # Limpiar archivos temporales
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        
        # 2. Subir PDF original para descarga (si no es muy grande)
        pdf_result = upload_pdf_original(file_path, public_id)
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
        print(f"🖼️ Procesando imagen: {file_name}")
        
        # Comprimir si es muy grande
        final_path = compress_if_needed(file_path, max_size_mb=3.0)
        temp_compressed = final_path if final_path != file_path else None
        
        try:
            result = upload_image(final_path, public_id)
            print(f"  ✅ Imagen subida")
            
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
                except:
                    pass


def delete_ticket_files(file_pages_json: str = None, pdf_url: str = None) -> bool:
    """
    Elimina todos los archivos de un ticket de Cloudinary.
    
    Args:
        file_pages_json: String JSON con array de URLs de páginas
        pdf_url: URL del PDF original
    
    Returns:
        bool: True si se eliminó todo correctamente
    """
    success = True
    
    # 1. Eliminar páginas (imágenes WebP)
    if file_pages_json:
        try:
            import json
            file_pages = json.loads(file_pages_json)
            
            for url in file_pages:
                try:
                    # Extraer public_id de la URL
                    # Ejemplo: https://res.cloudinary.com/cloud/image/upload/v123/dazz-producciones/project_1/file_page_1.webp
                    # public_id: dazz-producciones/project_1/file_page_1
                    
                    parts = url.split("/upload/")
                    if len(parts) == 2:
                        # Quitar versión y extensión
                        path = parts[1].split("/", 1)[1] if "/" in parts[1] else parts[1]  # Quita vXXX
                        public_id = path.rsplit(".", 1)[0]  # Quita extensión
                        
                        result = cloudinary.uploader.destroy(public_id, resource_type="image")
                        if result.get("result") != "ok":
                            print(f"⚠️ No se pudo eliminar {public_id}")
                            success = False
                        else:
                            print(f"✅ Eliminado de Cloudinary: {public_id}")
                except Exception as e:
                    print(f"⚠️ Error eliminando página {url}: {str(e)}")
                    success = False
        except Exception as e:
            print(f"⚠️ Error parseando file_pages: {str(e)}")
            success = False
    
    # 2. Eliminar PDF original (si existe)
    if pdf_url:
        try:
            parts = pdf_url.split("/upload/")
            if len(parts) == 2:
                path = parts[1].split("/", 1)[1] if "/" in parts[1] else parts[1]
                public_id = path.rsplit(".", 1)[0]
                
                result = cloudinary.uploader.destroy(public_id, resource_type="raw")
                if result.get("result") != "ok":
                    print(f"⚠️ No se pudo eliminar PDF {public_id}")
                    success = False
                else:
                    print(f"✅ PDF eliminado de Cloudinary: {public_id}")
        except Exception as e:
            print(f"⚠️ Error eliminando PDF {pdf_url}: {str(e)}")
            success = False
    
    return success


def delete_ticket_file(public_id: str, resource_type: str = "image") -> bool:
    """Elimina un archivo de Cloudinary (función legacy, usar delete_ticket_files)"""
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result.get("result") == "ok"
    except Exception as e:
        print(f"⚠️ Error eliminando de Cloudinary: {str(e)}")
        return False
