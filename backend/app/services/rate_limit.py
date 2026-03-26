"""
Unified rate limiter for all routes.
Uses X-Forwarded-For to get real client IP behind Railway proxy.
"""

from fastapi import Request
from slowapi import Limiter


def get_real_client_ip(request: Request) -> str:
    """Key function for rate limiting behind Railway proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    headers_enabled=True,
)
