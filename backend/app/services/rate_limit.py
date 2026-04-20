"""
Unified rate limiter for all routes.
Uses X-Forwarded-For to get real client IP behind Railway proxy.
"""

import logging
import os

from fastapi import Request
from slowapi import Limiter

logger = logging.getLogger(__name__)


def get_real_client_ip(request: Request) -> str:
    """Key function for rate limiting behind Railway proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


# MEJORA-01: shared storage across gunicorn workers. Without Redis, each worker
# has its own in-memory counters → an attacker rotating across workers doubles
# their effective rate. With REDIS_URL set, counters are shared.
_REDIS_URL = os.getenv("REDIS_URL")
if _REDIS_URL:
    _storage_uri = _REDIS_URL
    logger.info("Rate limiter using Redis backend (counters shared across workers)")
else:
    _storage_uri = "memory://"
    logger.warning(
        "REDIS_URL not set — rate limiter using in-memory storage "
        "(per-worker counters; resets on every deploy). OK for local dev, "
        "NOT recommended for production with multiple workers."
    )

limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=_storage_uri,
    headers_enabled=True,
)
