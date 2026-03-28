"""
Autenticación JWT para proveedores (separada de users).

Los proveedores tienen su propia tabla, su propio JWT con type=supplier,
y sus propios refresh tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import secrets
import string
import os
from dotenv import load_dotenv

from config.database import get_db
from app.models.suppliers import Supplier, SupplierRefreshToken

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required.")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
SUPPLIER_ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hora (doc sección 11c)
SUPPLIER_REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_DUMMY_HASH = pwd_context.hash("dummy-timing-attack-protection")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


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


def _generate_token(length: int = 64) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


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
