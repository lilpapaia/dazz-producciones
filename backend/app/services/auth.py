from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import secrets
import string

from config.database import get_db
from app.models import schemas
from app.models.database import User, PasswordResetToken
from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.services.email import send_set_password_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

def generate_token(length=32):
    """Generar token aleatorio seguro"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    print(f"📝 Intentando crear usuario: {user.email}, role: {user.role}")
    
    # Verificar si el email ya existe
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        print(f"❌ Email ya registrado: {user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Verificar si el username ya existe (si se proporcionó)
    if user.username:
        existing_username = db.query(User).filter(User.username == user.username).first()
        if existing_username:
            print(f"❌ Username ya registrado: {user.username}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    
    # Crear usuario
    try:
        hashed_password = get_password_hash(user.password)
        
        # Convertir role a string si es un Enum
        role_value = user.role.value if hasattr(user.role, 'value') else user.role
        
        db_user = User(
            name=user.name, 
            email=user.email,
            username=user.username,
            hashed_password=hashed_password, 
            role=role_value
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"✅ Usuario creado exitosamente: {user.email}")
        
        # Generar token para set password
        try:
            token = generate_token()
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            reset_token = PasswordResetToken(
                user_id=db_user.id,
                token=token,
                expires_at=expires_at
            )
            db.add(reset_token)
            db.commit()
            print(f"✅ Token generado: {token[:10]}...")
            
            # Enviar email con link para set password
            try:
                print(f"📧 Intentando enviar email de set password a {user.email}...")
                send_set_password_email(
                    user_name=user.name,
                    user_email=user.email,
                    token=token
                )
                print(f"✅ Email enviado correctamente")
            except Exception as e:
                print(f"⚠️ No se pudo enviar email (pero el usuario fue creado): {str(e)}")
                # NO fallar si el email no se puede enviar
                
        except Exception as e:
            print(f"⚠️ Error al generar token o enviar email: {str(e)}")
            # Continuar aunque falle el email
        
        return db_user
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al crear usuario: {str(e)}"
        )

@router.post("/login", response_model=schemas.Token)
async def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_credentials.identifier, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/set-password", response_model=schemas.SetPasswordResponse)
async def set_password(request: schemas.SetPasswordRequest, db: Session = Depends(get_db)):
    """
    Endpoint para que el usuario elija su contraseña con un token
    
    Args:
        request: {token, new_password}
    
    Returns:
        {message, success}
    """
    print(f"🔑 Intentando set password con token: {request.token[:10]}...")
    
    # Buscar token válido
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.expires_at > datetime.utcnow(),
        PasswordResetToken.used_at == None
    ).first()
    
    if not reset_token:
        print(f"❌ Token inválido, expirado o ya usado")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido, expirado o ya usado"
        )
    
    # Obtener usuario
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        print(f"❌ Usuario no encontrado")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar contraseña
    try:
        user.hashed_password = get_password_hash(request.new_password)
        
        # Marcar token como usado
        reset_token.used_at = datetime.utcnow()
        
        db.commit()
        print(f"✅ Contraseña actualizada para usuario: {user.email}")
        
        return schemas.SetPasswordResponse(
            message="Contraseña actualizada correctamente. Ya puedes iniciar sesión.",
            success=True
        )
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al actualizar contraseña: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar contraseña: {str(e)}"
        )

@router.post("/register-first-admin", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_first_admin(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_users = db.query(User).count()
    if existing_users > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Users already exist. Use regular registration.")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        name=user.name, 
        email=user.email,
        username=user.username,
        hashed_password=hashed_password, 
        role="admin"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
