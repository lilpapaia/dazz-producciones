from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import secrets
import string

from config.database import get_db
from app.models import schemas
from app.models.database import User
from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.services.email import send_user_created_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(name=user.name, email=user.email, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    try:
        send_user_created_email(user_name=user.name, user_email=user.email, temporary_password=user.password)
    except Exception as e:
        print(f"Warning: Could not send welcome email: {str(e)}")
    return db_user

@router.post("/login", response_model=schemas.Token)
async def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/register-first-admin", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_first_admin(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_users = db.query(User).count()
    if existing_users > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Users already exist. Use regular registration.")
    hashed_password = get_password_hash(user.password)
    db_user = User(name=user.name, email=user.email, hashed_password=hashed_password, role="admin")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
