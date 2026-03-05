"""
Servicio Cloudinary para almacenamiento de tickets/facturas
- Imágenes: convierte a WebP automáticamente
- PDFs: convierte páginas a imágenes WebP + guarda PDF original
"""

import cloudinary
import cloudinary.uploader
import os
from pathlib import Path

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dyjpek4q8"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "869752186781145"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

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
    """Sube PDF original para descarga"""
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
        # 1. Convertir páginas a imágenes
        from pdf2image import convert_from_path
        pages = convert_from_path(file_path, dpi=150)
        
        page_urls = []
        for i, page_img in enumerate(pages):
            # Guardar página como JPG temporal
            temp_page_path = f"{file_path}_page_{i+1}.jpg"
            page_img.save(temp_page_path, "JPEG", quality=85)
            
            try:
                # Subir página a Cloudinary como WebP
                result = upload_image(temp_page_path, f"{public_id}_page_{i+1}")
                page_urls.append(result["url"])
                print(f"✅ Página {i+1}/{len(pages)} subida: {result['url']}")
            finally:
                # Limpiar temp
                if os.path.exists(temp_page_path):
                    os.remove(temp_page_path)
        
        # 2. Subir PDF original para descarga
        pdf_result = upload_pdf_original(file_path, public_id)
        
        return {
            "url": page_urls[0] if page_urls else None,
            "pages": page_urls,
            "pdf_url": pdf_result["url"],
            "public_id": public_id,
            "is_pdf": True,
            "page_count": len(pages)
        }
    else:
        # Imagen normal → WebP
        result = upload_image(file_path, public_id)
        return {
            "url": result["url"],
            "pages": [result["url"]],
            "pdf_url": None,
            "public_id": result["public_id"],
            "is_pdf": False,
            "page_count": 1
        }


def delete_ticket_file(public_id: str, resource_type: str = "image") -> bool:
    """Elimina un archivo de Cloudinary"""
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result.get("result") == "ok"
    except Exception as e:
        print(f"⚠️ Error eliminando de Cloudinary: {str(e)}")
        return False
