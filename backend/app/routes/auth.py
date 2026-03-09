from fastapi import APIRouter, Depends, HTTPException, status, Request
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
from app.services.email import send_set_password_email, send_forgot_password_email

# LOGGING CRÍTICO
from app.services.critical_logger import log_login_failed

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
    """
    Crear nuevo usuario (solo admin)
    
    IMPORTANTE: Este endpoint SIEMPRE devuelve el usuario creado,
    incluso si falla el envío del email. El admin puede reenviar el email manualmente.
    """
    print(f"📝 Intentando crear usuario: {user.email}, role: {user.role}")
    
    # Verificar si el email ya existe
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        print(f"❌ Email ya registrado: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )
    
    # Verificar si el username ya existe (si se proporcionó)
    if user.username:
        existing_username = db.query(User).filter(User.username == user.username).first()
        if existing_username:
            print(f"❌ Username ya registrado: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Username already taken"
            )
    
    # Crear usuario en BD
    try:
        hashed_password = get_password_hash(user.password)
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
        
        print(f"✅ Usuario creado exitosamente: {user.email} (ID: {db_user.id})")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear usuario en BD: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al crear usuario: {str(e)}"
        )
    
    # IMPORTANTE: A partir de aquí, el usuario YA ESTÁ CREADO
    # Si algo falla, NO hacemos rollback - solo loggeamos el error
    
    # Intentar generar token y enviar email (NO CRÍTICO)
    email_sent = False
    token_created = False
    
    try:
        # Generar token
        token = generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        reset_token = PasswordResetToken(
            user_id=db_user.id,
            token=token,
            expires_at=expires_at
        )
        
        db.add(reset_token)
        db.commit()
        token_created = True
        
        print(f"✅ Token generado: {token[:10]}... (expira en 24h)")
        
        # Intentar enviar email (con timeout implícito de SMTP)
        try:
            print(f"📧 Intentando enviar email a {user.email}...")
            send_set_password_email(
                user_name=user.name,
                user_email=user.email,
                token=token
            )
            email_sent = True
            print(f"✅ Email enviado correctamente a {user.email}")
            
        except Exception as email_error:
            # Email falló pero NO es crítico
            print(f"⚠️ Error al enviar email (usuario creado OK): {str(email_error)}")
            # NO hacer raise - continuar normalmente
            
    except Exception as token_error:
        # Error al crear token, tampoco es crítico
        print(f"⚠️ Error al generar token (usuario creado OK): {str(token_error)}")
        # NO hacer rollback del usuario - solo no tiene token
    
    # Log final del resultado
    if token_created and email_sent:
        print(f"🎉 Usuario creado + Token generado + Email enviado: {user.email}")
    elif token_created and not email_sent:
        print(f"⚠️ Usuario creado + Token generado, pero email NO enviado: {user.email}")
    else:
        print(f"⚠️ Usuario creado pero sin token/email: {user.email}")
    
    # SIEMPRE devolver el usuario creado (esto es lo importante)
    return db_user


@router.post("/login", response_model=schemas.Token)
async def login(
    user_credentials: schemas.UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login con logging crítico de intentos fallidos"""
    
    # Intentar autenticar
    user = authenticate_user(db, user_credentials.identifier, user_credentials.password)
    
    if not user:
        # Obtener IP del cliente
        client_ip = request.client.host if request.client else "unknown"
        
        # LOGGING CRÍTICO AMARILLO - Login fallido
        log_login_failed(
            identifier=user_credentials.identifier,
            ip_address=client_ip,
            reason="Credenciales inválidas"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Login exitoso - crear token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/set-password", response_model=schemas.SetPasswordResponse)
async def set_password(request: schemas.SetPasswordRequest, db: Session = Depends(get_db)):
    """
    Endpoint para que el usuario elija su contraseña con un token
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


@router.post("/forgot-password")
async def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Endpoint para solicitar reset de contraseña.
    Siempre devuelve éxito (por seguridad, no revelar si el email existe)
    """
    print(f"🔐 Solicitud de reset password para: {request.email}")
    
    # Buscar usuario
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # Por seguridad, no revelar que el email no existe
        print(f"⚠️ Email no encontrado: {request.email} (no revelamos al usuario)")
        return {"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}
    
    try:
        # Invalidar tokens anteriores de este usuario
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at == None
        ).update({"used_at": datetime.utcnow()})
        
        # Generar nuevo token
        token = generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hora para reset
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        
        db.add(reset_token)
        db.commit()
        
        print(f"✅ Token de reset generado para: {user.email}")
        
        # Enviar email
        try:
            send_forgot_password_email(
                user_name=user.name,
                user_email=user.email,
                token=token
            )
            print(f"✅ Email de reset enviado a: {user.email}")
        except Exception as email_error:
            print(f"⚠️ Error enviando email de reset: {str(email_error)}")
            # No fallar - el usuario puede intentar de nuevo
        
    except Exception as e:
        print(f"❌ Error en forgot-password: {str(e)}")
        # No revelar el error al usuario
    
    return {"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}


@router.post("/register-first-admin", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_first_admin(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Crear primer admin (solo funciona si no hay usuarios)"""
    existing_users = db.query(User).count()
    if existing_users > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Users already exist. Use regular registration."
        )
    
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
