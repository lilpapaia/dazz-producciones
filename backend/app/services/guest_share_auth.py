"""
Autenticación JWT para invitados externos (FEAT-09).

Un externo (freelance, sin cuenta User) accede a UN proyecto vía link + PIN.
Patrón clonado de supplier_auth.py pero más simple:
- JWT con type="guest", sub="guest:<token_id>", project_id embebido.
- SIN refresh token: el access token vive 4h; al expirar se re-introduce el PIN.
- La sesión se revalida en cada request contra project_share_tokens
  (is_active + expires_at + locked_until) → revocar el link corta sesiones vivas.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config.database import get_db
from app.models.database import ProjectShareToken

# Reutilizar utils de password (bcrypt) y config JWT de auth.py — fuente única.
from app.services.auth import (  # noqa: F401 — verify_password/get_password_hash re-exportados
    verify_password,
    get_password_hash,
    SECRET_KEY,
    ALGORITHM,
)

# El access token del invitado dura 4h (sin refresh). Al expirar, re-introduce PIN.
GUEST_ACCESS_TOKEN_EXPIRE_HOURS = 4

# auto_error=False: devuelve None en vez de 403 si falta el header — lo tratamos como 401.
security = HTTPBearer(auto_error=False)


def generate_share_token() -> str:
    """Token único para la URL del link. secrets.token_urlsafe(48) → 64 chars."""
    return secrets.token_urlsafe(48)


def generate_pin() -> str:
    """PIN de 6 dígitos (100000–999999) criptográficamente seguro."""
    return str(secrets.randbelow(900000) + 100000)


def create_guest_access_token(token_id: int, project_id: int, guest_name: str) -> str:
    """Crea JWT de invitado con type=guest para diferenciarlo de users/suppliers."""
    expire = datetime.now(timezone.utc) + timedelta(hours=GUEST_ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": f"guest:{token_id}",
        "type": "guest",
        "project_id": project_id,
        "guest_name": guest_name,
        "exp": expire,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """La BD guarda UTC naive; re-adjuntamos tzinfo para comparar con un now aware."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


async def get_current_guest(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """
    Dependency FastAPI para endpoints /guest.

    Decodifica el JWT, valida que es de tipo guest y revalida la fila
    project_share_tokens en cada request (is_active, expires_at, locked_until).

    Devuelve: {"token_id", "project_id", "guest_name", "share_token": ProjectShareToken}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "guest":
            raise credentials_exception

        sub = payload.get("sub", "")
        if not sub.startswith("guest:"):
            raise credentials_exception

        token_id = int(sub.split(":")[1])
    except (JWTError, ValueError, IndexError):
        raise credentials_exception

    share_token = db.query(ProjectShareToken).filter(ProjectShareToken.id == token_id).first()
    if share_token is None:
        raise credentials_exception

    now = datetime.now(timezone.utc)

    # Revocado por el responsable → corta sesiones vivas inmediatamente.
    if not share_token.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El enlace ha sido revocado",
        )

    # Link caducado.
    if _as_utc(share_token.expires_at) <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El enlace ha caducado",
        )

    # Bloqueo temporal por intentos de PIN fallidos.
    locked_until = _as_utc(share_token.locked_until)
    if locked_until and locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Acceso bloqueado temporalmente por intentos fallidos",
        )

    return {
        "token_id": share_token.id,
        "project_id": share_token.project_id,
        "guest_name": share_token.guest_name,
        "share_token": share_token,
    }


def can_guest_access_project(project_id_from_request: int, guest_session: dict) -> bool:
    """
    Anti-IDOR: el invitado SOLO puede tocar el proyecto de su token.
    El project_id de autoridad es el del JWT/sesión, nunca el del request.
    """
    return project_id_from_request == guest_session["project_id"]
