"""
Sistema de Logging para Dazz Producciones
==========================================

Registra:
- Login attempts (exitosos y fallidos)
- Accesos a endpoints críticos
- Cambios en datos importantes
- Errores HTTP
- Performance de requests

Los logs se guardan en archivos rotativos y se muestran en consola
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import os

# Crear directorio de logs si no existe
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configuración de formato
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================
# CONFIGURAR LOGGERS
# ============================================

def setup_logger(
    name: str,
    log_file: str,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Crea un logger con archivo rotativo y consola
    
    Args:
        name: Nombre del logger
        log_file: Archivo donde guardar logs
        level: Nivel mínimo de logging
        max_bytes: Tamaño máximo del archivo (default 10MB)
        backup_count: Número de archivos de respaldo
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar duplicados
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Handler para archivo (rotativo)
    file_handler = RotatingFileHandler(
        LOG_DIR / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola (solo en desarrollo)
    if os.getenv("ENVIRONMENT", "development") == "development":
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


# ============================================
# LOGGERS ESPECÍFICOS
# ============================================

# Logger general de aplicación
app_logger = setup_logger("app", "app.log")

# Logger de autenticación (crítico)
auth_logger = setup_logger("auth", "auth.log", level=logging.INFO)

# Logger de acceso a endpoints
access_logger = setup_logger("access", "access.log", level=logging.INFO)

# Logger de errores
error_logger = setup_logger("error", "error.log", level=logging.ERROR)

# Logger de cambios en datos
audit_logger = setup_logger("audit", "audit.log", level=logging.INFO)


# ============================================
# FUNCIONES DE LOGGING
# ============================================

def log_login_attempt(
    identifier: str, 
    success: bool, 
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Registra intento de login
    
    Args:
        identifier: Email o username
        success: Si fue exitoso
        ip_address: IP del cliente
        user_agent: User agent del navegador
    """
    status = "SUCCESS" if success else "FAILED"
    message = f"Login {status} | User: {identifier}"
    
    if ip_address:
        message += f" | IP: {ip_address}"
    
    if user_agent:
        # Acortar user agent
        ua_short = user_agent[:50] + "..." if len(user_agent) > 50 else user_agent
        message += f" | UA: {ua_short}"
    
    if success:
        auth_logger.info(message)
    else:
        auth_logger.warning(message)


def log_logout(user_email: str, ip_address: Optional[str] = None):
    """Registra logout de usuario"""
    message = f"Logout | User: {user_email}"
    if ip_address:
        message += f" | IP: {ip_address}"
    auth_logger.info(message)


def log_endpoint_access(
    method: str,
    path: str,
    user_email: Optional[str] = None,
    status_code: int = 200,
    response_time: Optional[float] = None
):
    """
    Registra acceso a endpoint
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Path del endpoint
        user_email: Usuario autenticado
        status_code: Código HTTP respuesta
        response_time: Tiempo de respuesta en ms
    """
    message = f"{method} {path} | Status: {status_code}"
    
    if user_email:
        message += f" | User: {user_email}"
    
    if response_time:
        message += f" | Time: {response_time:.0f}ms"
    
    # Log según código de respuesta
    if status_code < 400:
        access_logger.info(message)
    elif status_code < 500:
        access_logger.warning(message)
    else:
        access_logger.error(message)


def log_error(
    error_type: str,
    message: str,
    user_email: Optional[str] = None,
    endpoint: Optional[str] = None,
    details: Optional[dict] = None
):
    """
    Registra error
    
    Args:
        error_type: Tipo de error (ValidationError, HTTPException, etc.)
        message: Mensaje de error
        user_email: Usuario que generó el error
        endpoint: Endpoint donde ocurrió
        details: Detalles adicionales
    """
    log_msg = f"{error_type}: {message}"
    
    if user_email:
        log_msg += f" | User: {user_email}"
    
    if endpoint:
        log_msg += f" | Endpoint: {endpoint}"
    
    if details:
        log_msg += f" | Details: {details}"
    
    error_logger.error(log_msg)


def log_data_change(
    action: str,
    resource: str,
    resource_id: int,
    user_email: str,
    changes: Optional[dict] = None
):
    """
    Registra cambios en datos (audit trail)
    
    Args:
        action: CREATE, UPDATE, DELETE
        resource: Tipo de recurso (Project, Ticket, User)
        resource_id: ID del recurso
        user_email: Usuario que hizo el cambio
        changes: Diccionario con campos cambiados
    """
    message = f"{action} {resource} #{resource_id} | User: {user_email}"
    
    if changes:
        # Ocultar campos sensibles
        safe_changes = {
            k: v for k, v in changes.items() 
            if k not in ['password', 'hashed_password', 'token']
        }
        if safe_changes:
            message += f" | Changes: {safe_changes}"
    
    audit_logger.info(message)


def log_file_upload(
    filename: str,
    size_bytes: int,
    user_email: str,
    resource: str,
    resource_id: int
):
    """Registra subida de archivo"""
    size_mb = size_bytes / (1024 * 1024)
    message = (
        f"File Upload | File: {filename} | Size: {size_mb:.2f}MB | "
        f"User: {user_email} | {resource} #{resource_id}"
    )
    audit_logger.info(message)


def log_critical_action(
    action: str,
    user_email: str,
    details: Optional[str] = None
):
    """
    Registra acción crítica (eliminar proyecto, cambiar roles, etc.)
    
    Args:
        action: Descripción de la acción
        user_email: Usuario que la realizó
        details: Detalles adicionales
    """
    message = f"CRITICAL: {action} | User: {user_email}"
    if details:
        message += f" | {details}"
    
    audit_logger.warning(message)


# ============================================
# INICIALIZACIÓN
# ============================================

def initialize_logging():
    """Inicializar sistema de logging"""
    app_logger.info("=" * 60)
    app_logger.info("Sistema de Logging Inicializado")
    app_logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    app_logger.info(f"Directorio logs: {LOG_DIR.absolute()}")
    app_logger.info("=" * 60)


# Inicializar al importar
initialize_logging()
