from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
import os
import secrets
import string
from dotenv import load_dotenv

from config.database import get_db
from app.models.database import User, RefreshToken, UserRole

load_dotenv()

# VULN-001: SECRET_KEY obligatoria — sin valor por defecto
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required. Set it before starting the server.")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
# SEC-H1: Token de acceso corto (30min). El refresh token (7 días) renueva automáticamente.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# auto_error=False: return None instead of 403 when no token — we handle it as 401 below
security = HTTPBearer(auto_error=False)

# SEC-C3: Hash dummy para timing-attack protection en login
# Pre-generado para no recalcular en cada request
_DUMMY_HASH = pwd_context.hash("dummy-timing-attack-protection")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def _generate_token(length=64):
    """Genera token aleatorio seguro para refresh tokens"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def create_refresh_token(db: Session, user_id: int) -> str:
    """Create a new refresh token and store it in the database"""
    token = _generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()

    return token

def validate_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    """Validate a refresh token and return it if valid"""
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.expires_at > datetime.now(timezone.utc),
        RefreshToken.revoked_at == None
    ).first()

    return refresh_token

def revoke_refresh_token(db: Session, token: str) -> bool:
    """Revoke a refresh token"""
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.revoked_at == None
    ).first()

    if refresh_token:
        refresh_token.revoked_at = datetime.now(timezone.utc)
        db.commit()
        return True
    return False

def revoke_all_user_refresh_tokens(db: Session, user_id: int):
    """Revoke all refresh tokens for a user"""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at == None
    ).update({"revoked_at": datetime.now(timezone.utc)})
    db.commit()

def authenticate_user(db: Session, identifier: str, password: str):
    """
    Authenticate a user by email OR username

    Args:
        identifier: Can be either email or username
        password: User's password

    Returns:
        User object if authenticated, False otherwise
    """
    # SEC-C2: Normalizar email a lowercase para búsqueda (username se mantiene case-sensitive)
    identifier_lower = identifier.lower()
    user = db.query(User).filter(
        or_(
            User.email == identifier_lower,
            User.username == identifier
        )
    ).first()

    if not user:
        # SEC-C3: Ejecutar verify contra hash dummy para igualar tiempo de respuesta
        # Evita timing attacks que permiten enumerar usuarios válidos
        pwd_context.verify(password, _DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # auto_error=False means credentials is None when no Authorization header
    if credentials is None:
        raise credentials_exception

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # SEC-C2: Normalizar email a lowercase para búsqueda JWT
    user = db.query(User).options(joinedload(User.companies)).filter(User.email == email.lower()).first()
    if user is None:
        raise credentials_exception

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current admin user"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_current_admin_or_boss_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user if ADMIN or BOSS."""
    if current_user.role not in (UserRole.ADMIN, UserRole.BOSS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
