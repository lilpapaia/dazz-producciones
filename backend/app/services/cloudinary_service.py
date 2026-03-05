"""
Servicio Cloudinary para almacenamiento de tickets/facturas
- Sube imágenes y PDFs a Cloudinary
- Convierte imágenes a WebP automáticamente
- URLs permanentes (no se pierden en redeploys)
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

def upload_ticket_file(file_path: str, file_name: str, project_id: int) -> dict:
    """
    Sube un archivo (imagen o PDF) a Cloudinary
    - Imágenes: convierte a WebP automáticamente
    - PDFs: sube como público para poder visualizarlos
    """
    
    file_ext = Path(file_name).suffix.lower()
    is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    is_pdf = file_ext == '.pdf'
    
    folder = f"dazz-producciones/project_{project_id}"
    clean_name = Path(file_name).stem.replace(' ', '_')[:50]
    public_id = f"{folder}/{clean_name}"
    
    try:
        if is_image:
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
                access_mode="public",  # ✅ Acceso público
                overwrite=True
            )
        elif is_pdf:
            result = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                resource_type="raw",
                access_mode="public",  # ✅ Acceso público
                overwrite=True
            )
        else:
            result = cloudinary.uploader.upload(
                file_path,
                public_id=public_id,
                resource_type="auto",
                access_mode="public",  # ✅ Acceso público
                overwrite=True
            )
        
        print(f"✅ Cloudinary upload: {file_name} → {result['secure_url']}")
        
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "resource_type": result["resource_type"],
            "format": result.get("format", file_ext),
            "size": result.get("bytes", 0)
        }
        
    except Exception as e:
        print(f"❌ Cloudinary upload failed: {str(e)}")
        raise Exception(f"Error subiendo archivo a Cloudinary: {str(e)}")


def delete_ticket_file(public_id: str, resource_type: str = "image") -> bool:
    """Elimina un archivo de Cloudinary"""
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result.get("result") == "ok"
    except Exception as e:
        print(f"⚠️ Error eliminando de Cloudinary: {str(e)}")
        return False
