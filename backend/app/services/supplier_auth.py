"""
Autenticación JWT para proveedores (separada de users).

Los proveedores tienen su propia tabla, su propio JWT con type=supplier,
y sus propios refresh tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from config.database import get_db
from app.models.suppliers import Supplier, SupplierRefreshToken

# QUAL-2: Import shared password utils from auth.py (single CryptContext)
from app.services.auth import verify_password, get_password_hash, _DUMMY_HASH, _generate_token  # noqa: F401 — re-exported

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required.")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
SUPPLIER_ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hora (doc sección 11c)
SUPPLIER_REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()


def create_supplier_access_token(supplier_id: int, email: str) -> str:
    """Crea JWT para proveedor con type=supplier para diferenciar de users."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=SUPPLIER_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": f"supplier:{supplier_id}",
        "email": email,
        "type": "supplier",
        "exp": expire,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_supplier_refresh_token(db: Session, supplier_id: int) -> str:
    token = _generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=SUPPLIER_REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token = SupplierRefreshToken(
        supplier_id=supplier_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()
    return token


def validate_supplier_refresh_token(db: Session, token: str) -> Optional[SupplierRefreshToken]:
    return db.query(SupplierRefreshToken).filter(
        SupplierRefreshToken.token == token,
        SupplierRefreshToken.expires_at > datetime.now(timezone.utc),
        SupplierRefreshToken.revoked_at == None,
    ).first()


def revoke_supplier_refresh_token(db: Session, token: str, supplier_id: int = None) -> bool:
    query = db.query(SupplierRefreshToken).filter(
        SupplierRefreshToken.token == token,
        SupplierRefreshToken.revoked_at == None,
    )
    if supplier_id is not None:
        query = query.filter(SupplierRefreshToken.supplier_id == supplier_id)
    rt = query.first()
    if rt:
        rt.revoked_at = datetime.now(timezone.utc)
        db.commit()
        return True
    return False


def invalidate_all_supplier_tokens(db: Session, supplier_id: int):
    """Revoca todos los refresh tokens de un proveedor (al desactivar cuenta)."""
    db.query(SupplierRefreshToken).filter(
        SupplierRefreshToken.supplier_id == supplier_id,
        SupplierRefreshToken.revoked_at == None,
    ).update({"revoked_at": datetime.now(timezone.utc)})
    db.commit()


def rotate_supplier_refresh_token(db: Session, old_token: str) -> tuple[Supplier, str]:
    """
    Single-use refresh rotation for suppliers. Mirrors auth.rotate_refresh_token.
    Reuse of a revoked token revokes ALL the supplier's sessions.
    """
    rt = db.query(SupplierRefreshToken).filter(SupplierRefreshToken.token == old_token).first()
    if not rt:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    now = datetime.now(timezone.utc)

    if rt.revoked_at is not None:
        invalidate_all_supplier_tokens(db, rt.supplier_id)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh token already used — all sessions revoked for safety"
        )

    expires_aware = rt.expires_at.replace(tzinfo=timezone.utc) if rt.expires_at.tzinfo is None else rt.expires_at
    if expires_aware < now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")

    supplier = db.query(Supplier).filter(Supplier.id == rt.supplier_id).first()
    if not supplier or not supplier.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Supplier not found or inactive")

    rt.revoked_at = now
    new_token = _generate_token()
    new_expires_at = now + timedelta(days=SUPPLIER_REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(SupplierRefreshToken(
        supplier_id=supplier.id,
        token=new_token,
        expires_at=new_expires_at,
    ))
    db.commit()

    return supplier, new_token


async def get_current_supplier(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Supplier:
    """Dependency FastAPI: extrae proveedor del JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verificar que es un token de proveedor
        token_type = payload.get("type")
        if token_type != "supplier":
            raise credentials_exception

        sub = payload.get("sub", "")
        if not sub.startswith("supplier:"):
            raise credentials_exception

        supplier_id = int(sub.split(":")[1])
    except (JWTError, ValueError, IndexError):
        raise credentials_exception

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise credentials_exception

    return supplier


async def get_current_active_supplier(
    supplier: Supplier = Depends(get_current_supplier),
) -> Supplier:
    """Verifica que el proveedor esté activo."""
    if not supplier.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated"
        )
    return supplier
