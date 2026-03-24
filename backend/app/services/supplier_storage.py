"""
Storage service for supplier PDFs.

- Invoice PDFs → Cloudinary (dazz-suppliers/invoices/) — public upload + page images
- Bank certificates → Cloudflare R2 (bank-certs/) — signed URLs 15min

Cloudinary credentials reuse the existing project config (CLOUDINARY_CLOUD_NAME, etc.).
R2 credentials: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_ENDPOINT.
"""

import logging
import os
import uuid
import shutil
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

from app.services.validators import sanitize_filename
from app.services.cloudinary_service import compress_if_needed

import cloudinary
import cloudinary.uploader
import cloudinary.utils
import boto3
from botocore.config import Config as BotoConfig
from fastapi import UploadFile

# ============================================
# LOCAL FALLBACK (for temp files before upload)
# ============================================

UPLOAD_DIR = os.path.join("uploads", "suppliers")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================
# CLOUDINARY — Invoice PDFs
# ============================================
# Config is already loaded globally by cloudinary_service.py at startup.
# We just use cloudinary.uploader directly.

CLOUDINARY_FOLDER = "dazz-suppliers/invoices"
PAGES_FOLDER = "dazz-suppliers/pages"


def save_invoice_pdf(file: UploadFile, supplier_id: int, contents: bytes = None) -> Dict[str, Any]:
    """
    Upload supplier invoice PDF to Cloudinary (public) + generate page images.

    Same pattern as cloudinary_service.upload_ticket_file:
    1. Upload PDF original as raw/public
    2. Convert each page to WebP image via pdf2image + upload_image
    3. Return dict with public_id, url, pages[], page_count

    Args:
        file: FastAPI UploadFile (PDF)
        supplier_id: Supplier ID for folder organization
        contents: Pre-read bytes (avoids consuming file stream twice)

    Returns:
        dict: {"public_id", "url", "pages": [url1, ...], "page_count": int}
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    short_id = uuid.uuid4().hex[:8]
    clean_name = os.path.splitext(sanitize_filename(file.filename or "invoice"))[0][:40]
    file_name = f"{clean_name}_{timestamp}_{short_id}"
    folder = f"{CLOUDINARY_FOLDER}/{supplier_id}"
    pages_folder = f"{PAGES_FOLDER}/{supplier_id}"

    temp_path = os.path.join(UPLOAD_DIR, f"tmp_{short_id}.pdf")
    temp_files = []

    try:
        # Write PDF to temp file
        with open(temp_path, "wb") as out:
            if contents:
                out.write(contents)
            else:
                shutil.copyfileobj(file.file, out)

        # 1. Upload PDF original (public, raw)
        result = cloudinary.uploader.upload(
            temp_path,
            public_id=file_name,
            folder=folder,
            resource_type="raw",
            type="upload",
            overwrite=False,
        )
        returned_id = result.get("public_id", f"{folder}/{file_name}")
        pdf_url = result.get("secure_url", "")
        logger.info(f"Cloudinary PDF upload OK: {returned_id}")

        # 2. Convert pages to images (same as upload_ticket_file)
        page_urls = []
        try:
            from pdf2image import convert_from_path

            pdf_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            dpi = 150 if pdf_size_mb > 5 else 200

            pages = convert_from_path(temp_path, dpi=dpi)

            for i, page_img in enumerate(pages):
                temp_page_path = os.path.join(UPLOAD_DIR, f"tmp_{short_id}_page_{i + 1}.jpg")
                page_img.save(temp_page_path, "JPEG", quality=90)
                temp_files.append(temp_page_path)

                final_path = compress_if_needed(temp_page_path, max_size_mb=2.5)
                if final_path != temp_page_path:
                    temp_files.append(final_path)

                raw_result = cloudinary.uploader.upload(
                    final_path,
                    public_id=f"{file_name}_page_{i + 1}",
                    folder=pages_folder,
                    resource_type="image",
                    format="webp",
                    transformation=[
                        {"width": 2048, "height": 2048, "crop": "limit"},
                        {"quality": "auto:best"},
                    ],
                    overwrite=True,
                )
                page_urls.append(raw_result["secure_url"])
                logger.info(f"Page {i + 1}/{len(pages)} uploaded")

        except Exception as e:
            logger.warning(f"Page image generation failed: {e}")
            # PDF upload succeeded — pages are optional

        return {
            "public_id": returned_id,
            "url": pdf_url,
            "pages": page_urls,
            "page_count": len(page_urls),
        }

    finally:
        # Cleanup all temp files
        for tf in [temp_path] + temp_files:
            try:
                if os.path.exists(tf):
                    os.remove(tf)
            except OSError:
                pass


def get_invoice_pdf_url(public_id: str) -> str:
    """
    Get public URL for a supplier invoice PDF.

    Args:
        public_id: Cloudinary public_id returned by save_invoice_pdf()

    Returns:
        Public URL (no signing needed — type=upload)
    """
    url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type="raw",
        type="upload",
        secure=True,
    )
    return url


def delete_invoice_pdf(file_url: str) -> bool:
    """Delete an invoice PDF from Cloudinary. Accepts URL or public_id."""
    if not file_url:
        return False

    try:
        # Extract public_id from URL if needed
        if file_url.startswith("http"):
            from app.services.cloudinary_service import extract_public_id_from_url
            pid = extract_public_id_from_url(file_url)
        else:
            pid = file_url

        if not pid:
            return False

        # Raw resources include extension in public_id
        if not pid.endswith(".pdf"):
            pid = f"{pid}.pdf"

        cloudinary.uploader.destroy(pid, resource_type="raw", type="upload")
        logger.info(f"Cloudinary delete OK: {pid}")
        return True
    except Exception as e:
        logger.error(f"Cloudinary delete error: {e}")
        return False


# ============================================
# CLOUDFLARE R2 — Bank Certificates
# ============================================

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "bank-certs")
# Construir endpoint desde account_id si no se proporciona explícitamente
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
if not R2_ENDPOINT and R2_ACCOUNT_ID:
    R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

SIGNED_URL_EXPIRY = 900  # 15 minutes (RGPD requirement)


def _get_r2_client():
    """Create boto3 S3 client configured for Cloudflare R2."""
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        raise RuntimeError(
            "R2 credentials not configured. "
            "Set R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY."
        )

    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=BotoConfig(
            signature_version="s3v4",
            region_name="auto",
        ),
    )


def _sanitize_nif_for_key(nif_cif: Optional[str]) -> str:
    """Sanitize NIF/CIF for use in R2 object key — alphanumeric only."""
    if not nif_cif:
        return "unknown"
    import re
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', nif_cif.strip())
    return cleaned[:20] if cleaned else "unknown"


def save_bank_cert(file: UploadFile, supplier_id: int, contents: bytes = None,
                   nif_cif: Optional[str] = None, tipo: str = "initial") -> str:
    """
    Upload bank certificate PDF to Cloudflare R2.

    Structure: bank_certs/{supplier_id}/{timestamp}_{tipo}_{nif}.pdf
    NEVER deletes previous certs — all versions kept for RGPD/Hacienda.

    Args:
        file: FastAPI UploadFile (PDF)
        supplier_id: Supplier ID
        contents: Pre-read bytes (avoids consuming file stream twice)
        nif_cif: NIF/CIF for filename (sanitized)
        tipo: "initial" for registration, "update" for IBAN changes

    Returns:
        R2 object key (NOT a public URL — use get_bank_cert_url to get signed URL)
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_nif = _sanitize_nif_for_key(nif_cif)
    object_key = f"bank_certs/{supplier_id}/{timestamp}_{tipo}_{safe_nif}.pdf"

    short_id = uuid.uuid4().hex[:8]
    temp_path = os.path.join(UPLOAD_DIR, f"tmp_bank_{short_id}.pdf")
    try:
        with open(temp_path, "wb") as out:
            if contents:
                out.write(contents)
            else:
                shutil.copyfileobj(file.file, out)

        file_size = os.path.getsize(temp_path)
        logger.info(f"R2 upload attempt: key={object_key}, size={file_size}B, "
                     f"endpoint={'SET' if R2_ENDPOINT else 'MISSING'}, "
                     f"bucket={R2_BUCKET_NAME}, "
                     f"access_key={'SET' if R2_ACCESS_KEY_ID else 'MISSING'}")

        client = _get_r2_client()
        try:
            client.upload_file(
                temp_path,
                R2_BUCKET_NAME,
                object_key,
                ExtraArgs={"ContentType": "application/pdf"},
            )
        except Exception as e:
            logger.error(f"R2 upload FAILED: {type(e).__name__}: {e}")
            raise

        logger.info(f"R2 upload OK: {object_key}")
        return object_key

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def get_bank_cert_url(object_key: str) -> str:
    """
    Generate a signed URL for a bank certificate (15min expiry).

    This is the ONLY way to access bank certs — no permanent public URLs.
    Each call generates a fresh URL that expires in 15 minutes.

    Args:
        object_key: R2 object key returned by save_bank_cert()

    Returns:
        Pre-signed URL valid for 15 minutes
    """
    client = _get_r2_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": R2_BUCKET_NAME,
            "Key": object_key,
        },
        ExpiresIn=SIGNED_URL_EXPIRY,
    )
    return url


    # delete_bank_cert removed — RGPD requires all bank certificates to be retained
