"""
Encryption service for sensitive data (IBANs).

Uses Fernet symmetric encryption (AES-128-CBC + HMAC).
Key must be set in environment variable ENCRYPTION_KEY.

Generate a key with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import os
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
_fernet: Optional[Fernet] = None

if _ENCRYPTION_KEY:
    try:
        _fernet = Fernet(_ENCRYPTION_KEY.encode())
    except Exception as e:
        logger.error(f"Invalid ENCRYPTION_KEY: {e}")
        _fernet = None
else:
    logger.warning("ENCRYPTION_KEY not set — IBAN encryption disabled (plaintext fallback)")


def encrypt_iban(plaintext: str) -> bytes:
    """
    Encrypt an IBAN string. Returns encrypted bytes for LargeBinary column.

    If ENCRYPTION_KEY is not configured, falls back to UTF-8 encoding
    (development/migration compatibility).
    """
    if not plaintext:
        return b""
    if _fernet:
        return _fernet.encrypt(plaintext.encode("utf-8"))
    # Fallback: plain UTF-8 (dev only — log warning once)
    logger.warning("encrypt_iban called without ENCRYPTION_KEY — storing plaintext")
    return plaintext.encode("utf-8")


def decrypt_iban(ciphertext: bytes) -> Optional[str]:
    """
    Decrypt an IBAN from LargeBinary column.

    Handles both:
    - Fernet-encrypted bytes (production)
    - Legacy plain UTF-8 bytes (pre-migration data)
    """
    if not ciphertext:
        return None

    if _fernet:
        try:
            return _fernet.decrypt(ciphertext).decode("utf-8")
        except InvalidToken:
            # Likely legacy plaintext — try UTF-8 decode
            try:
                return ciphertext.decode("utf-8")
            except (UnicodeDecodeError, AttributeError):
                return None

    # No key configured — assume plaintext
    try:
        return ciphertext.decode("utf-8")
    except (UnicodeDecodeError, AttributeError):
        return None


def is_encryption_available() -> bool:
    """Check if Fernet encryption is properly configured."""
    return _fernet is not None
