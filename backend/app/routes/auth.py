import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
import secrets
import os

logger = logging.getLogger(__name__)

from config.database import get_db
from app.models import schemas
from app.models.database import User, PasswordResetToken, Company, UserCompany
from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_admin_user,
    get_current_active_user,
    create_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    revoke_all_user_refresh_tokens,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    _generate_token,
)
from app.services.email import send_set_password_email, send_forgot_password_email

# LOGGING CRÍTICO
from app.services.critical_logger import log_login_failed

# Rate limiting
from app.services.rate_limit import limiter, get_real_client_ip

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

router = APIRouter(prefix="/auth", tags=["Authentication"])

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

    NUEVO: Ahora asigna empresas al usuario según company_ids
    """
    logger.info(f"Registrando usuario: {user.email}, role: {user.role}, empresas: {user.company_ids}")

    # SEC-C2: Normalizar email a lowercase antes de buscar y guardar
    normalized_email = user.email.lower()

    # Verificar si el email ya existe
    db_user = db.query(User).filter(User.email == normalized_email).first()
    if db_user:
        logger.warning(f"Email ya registrado: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Verificar si el username ya existe (si se proporcionó)
    if user.username:
        existing_username = db.query(User).filter(User.username == user.username).first()
        if existing_username:
            logger.warning(f"Username ya registrado: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Validar que las empresas existan (1 query en batch)
    if user.company_ids:
        existing = db.query(Company.id).filter(Company.id.in_(user.company_ids)).all()
        existing_ids = {c[0] for c in existing}
        missing = set(user.company_ids) - existing_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa(s) con ID {missing} no encontrada(s)"
            )

    # Crear usuario en BD
    if not user.password or not user.password.strip():
        user.password = secrets.token_urlsafe(16)

    try:
        hashed_password = get_password_hash(user.password)
        role_value = user.role.value if hasattr(user.role, 'value') else user.role

        db_user = User(
            name=user.name,
            email=normalized_email,
            username=user.username,
            hashed_password=hashed_password,
            role=role_value
        )

        db.add(db_user)
        db.flush()  # Generate db_user.id without committing

        # Asignar empresas al usuario (same transaction)
        if user.company_ids:
            for company_id in user.company_ids:
                user_company = UserCompany(
                    user_id=db_user.id,
                    company_id=company_id
                )
                db.add(user_company)
            logger.info(f"{len(user.company_ids)} empresa(s) asignada(s) a {user.email}")
        else:
            logger.warning(f"Usuario creado SIN empresas asignadas: {user.email}")

        db.commit()  # Atomic: user + companies in one transaction
        db.refresh(db_user)
        logger.info(f"Usuario creado: {user.email} (ID: {db_user.id})")

    except Exception as e:
        db.rollback()
        # VULN-006: Logear error real internamente, devolver mensaje genérico
        logger.error(f"Error al crear usuario en BD: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear usuario"
        )

    # IMPORTANTE: A partir de aquí, el usuario YA ESTÁ CREADO
    # Si algo falla, NO hacemos rollback - solo loggeamos el error

    # Intentar generar token y enviar email (NO CRÍTICO)
    email_sent = False
    token_created = False

    try:
        # Generar token
        token = _generate_token(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        reset_token = PasswordResetToken(
            user_id=db_user.id,
            token=token,
            expires_at=expires_at
        )

        db.add(reset_token)
        db.commit()
        token_created = True

        # VULN-014: No logear el token, ni parcial ni completo
        logger.info(f"Token set-password generado para {user.email} (expira en 24h)")

        # Intentar enviar email
        try:
            logger.info(f"Enviando email a {user.email}...")
            send_set_password_email(
                user_name=user.name,
                user_email=user.email,
                token=token
            )
            email_sent = True
            logger.info(f"Email enviado correctamente a {user.email}")

        except Exception as email_error:
            # Email falló pero NO es crítico
            logger.warning(f"Error al enviar email (usuario creado OK): {str(email_error)}")
            # NO hacer raise - continuar normalmente

    except Exception as token_error:
        # Error al crear token, tampoco es crítico
        logger.warning(f"Error al generar token (usuario creado OK): {str(token_error)}")
        # NO hacer rollback del usuario - solo no tiene token

    # Log final del resultado
    if token_created and email_sent:
        logger.info(f"Usuario creado + Token + Email OK: {user.email}")
    elif token_created and not email_sent:
        logger.warning(f"Usuario creado + Token OK, pero email NO enviado: {user.email}")
    else:
        logger.warning(f"Usuario creado pero sin token/email: {user.email}")

    # Refrescar para obtener las relaciones (empresas)
    db.refresh(db_user)

    # SIEMPRE devolver el usuario creado (esto es lo importante)
    return db_user


@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    user_credentials: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """Login con logging crítico de intentos fallidos y account lockout"""

    # SEC-H2: Verificar lockout ANTES de intentar autenticar
    # Buscar usuario por email/username para comprobar bloqueo
    from sqlalchemy import or_
    identifier_lower = user_credentials.identifier.lower()
    target_user = db.query(User).filter(
        or_(User.email == identifier_lower, User.username == user_credentials.identifier)
    ).first()

    if target_user and target_user.locked_until:
        if target_user.locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account temporarily locked due to too many failed attempts. Try again in 15 minutes."
            )
        else:
            # Lock expirado, resetear
            target_user.failed_login_attempts = 0
            target_user.locked_until = None
            db.commit()

    # Intentar autenticar
    user = authenticate_user(db, user_credentials.identifier, user_credentials.password)

    if not user:
        # SEC-H2: Incrementar intentos fallidos si el usuario existe
        if target_user:
            target_user.failed_login_attempts = (target_user.failed_login_attempts or 0) + 1
            if target_user.failed_login_attempts >= 5:
                target_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                logger.warning(f"Account locked for user id={target_user.id} after 5 failed attempts")
            db.commit()

        client_ip = get_real_client_ip(request)
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

    # SEC-H2: Login exitoso — resetear contador
    if user.failed_login_attempts and user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

    # Login exitoso - crear access token + refresh token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    # VULN-009: Crear refresh token
    refresh_token = create_refresh_token(db, user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/refresh", response_model=schemas.RefreshTokenResponse)
async def refresh_access_token(
    request_body: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Renovar access token usando un refresh token válido"""
    refresh_token = validate_refresh_token(db, request_body.refresh_token)

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado"
        )

    # Obtener usuario
    user = db.query(User).filter(User.id == refresh_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )

    # Crear nuevo access token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    request_body: schemas.LogoutRequest,
    db: Session = Depends(get_db)
):
    """Revocar refresh token (logout)"""
    revoked = revoke_refresh_token(db, request_body.refresh_token)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token no encontrado o ya revocado"
        )

    return {"message": "Sesión cerrada correctamente"}


@router.post("/set-password", response_model=schemas.SetPasswordResponse)
@limiter.limit("5/minute")
async def set_password(
    request: Request,
    response: Response,
    payload: schemas.SetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint para que el usuario elija su contraseña con un token
    """
    # VULN-014: No logear el token
    logger.info("Intentando set password...")

    # Buscar token válido
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == payload.token,
        PasswordResetToken.expires_at > datetime.now(timezone.utc),
        PasswordResetToken.used_at == None
    ).first()

    if not reset_token:
        logger.warning("Token invalido, expirado o ya usado")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido, expirado o ya usado"
        )

    # Obtener usuario
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        logger.warning("Usuario no encontrado para set-password")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Actualizar contraseña
    try:
        user.hashed_password = get_password_hash(payload.new_password)
        reset_token.used_at = datetime.now(timezone.utc)

        db.commit()

        # SEC-H3: Revocar todos los refresh tokens tras cambio de contraseña
        revoke_all_user_refresh_tokens(db, user.id)
        logger.info(f"Contrasena actualizada y tokens revocados para: {user.email}")

        return schemas.SetPasswordResponse(
            message="Contraseña actualizada correctamente. Ya puedes iniciar sesión.",
            success=True
        )

    except Exception as e:
        db.rollback()
        # VULN-006: Logear error real, devolver genérico
        logger.error(f"Error al actualizar contrasena: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar contraseña"
        )


@router.post("/forgot-password")
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    response: Response,
    payload: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint para solicitar reset de contraseña.
    Siempre devuelve éxito (por seguridad, no revelar si el email existe)
    """
    logger.info(f"Solicitud reset password para: {payload.email}")

    # SEC-C2: Normalizar email a lowercase
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if not user:
        # Por seguridad, no revelar que el email no existe
        logger.info(f"Reset solicitado para email inexistente (no revelado al usuario)")
        return {"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}

    try:
        # Invalidar tokens anteriores de este usuario
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at == None
        ).update({"used_at": datetime.now(timezone.utc)})

        # Generar nuevo token
        token = _generate_token(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hora para reset

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )

        db.add(reset_token)
        db.commit()

        # VULN-014: No logear el token
        logger.info(f"Token reset generado para: {user.email}")

        # Enviar email
        try:
            send_forgot_password_email(
                user_name=user.name,
                user_email=user.email,
                token=token
            )
            logger.info(f"Email reset enviado a: {user.email}")
        except Exception as email_error:
            logger.warning(f"Error enviando email de reset: {str(email_error)}")
            # No fallar - el usuario puede intentar de nuevo

    except Exception as e:
        logger.error(f"Error en forgot-password: {str(e)}")
        # No revelar el error al usuario

    return {"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}


# VULN-016: Solo disponible en development
if ENVIRONMENT != "production":
    @router.post("/register-first-admin", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
    @limiter.limit("3/hour")
    async def register_first_admin(
        request: Request,
        response: Response,
        user: schemas.UserCreate,
        db: Session = Depends(get_db)
    ):
        """Crear primer admin (solo funciona si no hay usuarios y NO en producción)"""
        existing_users = db.query(User).count()
        if existing_users > 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Users already exist. Use regular registration."
            )

        hashed_password = get_password_hash(user.password)
        db_user = User(
            name=user.name,
            email=user.email.lower(),
            username=user.username,
            hashed_password=hashed_password,
            role="ADMIN"
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
