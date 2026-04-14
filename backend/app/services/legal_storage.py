"""
Storage service for legal document PDFs in Cloudflare R2.

Reuses the same R2 bucket and credentials as bank certificates (supplier_storage.py).
Path structure: legal_docs/{type}/{version}_{timestamp}.pdf
For personalized contracts: legal_docs/contracts/{supplier_id}_{timestamp}.pdf
"""

import logging
import os
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def save_legal_doc(file_path: str, doc_type: str, version: int,
                   supplier_id: int = None) -> str:
    """
    Upload legal document PDF to Cloudflare R2.

    Args:
        file_path: Local path to the PDF file
        doc_type: Document type (PRIVACY, CONTRACT, AUTOCONTROL, DECLARATION)
        version: Document version number
        supplier_id: For personalized contracts only

    Returns:
        R2 object key (NOT a public URL)
    """
    from app.services.supplier_storage import _get_r2_client, R2_BUCKET_NAME

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    doc_type_lower = doc_type.lower()

    if supplier_id and doc_type_lower == "contract":
        object_key = f"legal_docs/contracts/{supplier_id}_{timestamp}_{short_id}.pdf"
    else:
        object_key = f"legal_docs/{doc_type_lower}/v{version}_{timestamp}_{short_id}.pdf"

    client = _get_r2_client()
    try:
        client.upload_file(
            file_path,
            R2_BUCKET_NAME,
            object_key,
            ExtraArgs={"ContentType": "application/pdf"},
        )
    except Exception as e:
        logger.error(f"R2 legal doc upload FAILED: {type(e).__name__}: {e}")
        raise

    logger.info(f"R2 legal doc upload OK: {object_key}")
    return object_key


def get_legal_doc_url(object_key: str) -> str:
    """
    Generate a signed URL for a legal document PDF (15min expiry).

    Args:
        object_key: R2 object key returned by save_legal_doc()

    Returns:
        Pre-signed URL valid for 15 minutes
    """
    from app.services.supplier_storage import (
        _get_r2_client, R2_BUCKET_NAME, SIGNED_URL_EXPIRY,
    )

    client = _get_r2_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": R2_BUCKET_NAME, "Key": object_key},
        ExpiresIn=SIGNED_URL_EXPIRY,
    )
    return url


def delete_legal_doc(object_key: str) -> bool:
    """
    Delete a legal document from R2 (cleanup only).

    Args:
        object_key: R2 object key

    Returns:
        True if deleted, False on error
    """
    if not object_key:
        return False

    from app.services.supplier_storage import _get_r2_client, R2_BUCKET_NAME

    try:
        client = _get_r2_client()
        client.delete_object(Bucket=R2_BUCKET_NAME, Key=object_key)
        logger.info(f"R2 legal doc delete OK: {object_key}")
        return True
    except Exception as e:
        logger.error(f"R2 legal doc delete error: {e}")
        return False
