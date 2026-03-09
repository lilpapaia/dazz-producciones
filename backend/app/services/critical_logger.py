"""
Sistema de Logging Crítico - DAZZ Producciones
===============================================

Registra solo eventos críticos con formato destacado en AMARILLO
para fácil identificación en Railway Dashboard.

Eventos críticos:
- Login fallidos (intentos de hackeo)
- Errores 500 (crashes)
- Eliminaciones (proyectos, usuarios)
- Cambios de roles
- Excepciones inesperadas
"""

from datetime import datetime
from typing import Dict, Optional


class Colors:
    """Códigos ANSI para colores en terminal/Railway"""
    YELLOW = '\033[93m'   # Amarillo brillante
    BOLD = '\033[1m'      # Negrita
    RESET = '\033[0m'     # Reset a color normal


def log_critical(
    event_type: str,
    emoji: str,
    details: Dict[str, any],
    user_email: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """
    Registra evento crítico con formato destacado en AMARILLO
    
    Args:
        event_type: Tipo de evento ("LOGIN FALLIDO", "ERROR 500", etc.)
        emoji: Emoji identificador ("🚨", "🔥", "🗑️", etc.)
        details: Diccionario con detalles del evento
        user_email: Email del usuario (opcional)
        ip_address: IP del cliente (opcional)
    
    Ejemplo:
        log_critical(
            event_type="LOGIN FALLIDO",
            emoji="🚨",
            details={"intento": "3er intento en 5 min"},
            user_email="hacker@test.com",
            ip_address="45.123.45.67"
        )
    """
    
    # Inicio del color amarillo + negrita
    print(f"{Colors.YELLOW}{Colors.BOLD}", end="")
    
    # Separador
    separator = "=" * 70
    print(separator)
    
    # Header
    print(f"{emoji} [DAZZ-CRITICAL] {event_type}")
    print(separator)
    
    # Timestamp
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"Timestamp: {timestamp}")
    
    # Usuario (si existe)
    if user_email:
        print(f"Usuario: {user_email}")
    
    # IP (si existe)
    if ip_address:
        print(f"IP: {ip_address}")
    
    # Detalles adicionales
    for key, value in details.items():
        # Capitalizar primera letra de la key
        formatted_key = key.replace("_", " ").capitalize()
        print(f"{formatted_key}: {value}")
    
    # Separador final
    print(separator)
    
    # Fin del color
    print(f"{Colors.RESET}")
    
    # Línea en blanco para separación
    print()


# ============================================
# FUNCIONES DE CONVENIENCIA
# ============================================

def log_login_failed(
    identifier: str,
    ip_address: Optional[str] = None,
    reason: str = "Credenciales inválidas"
):
    """Log de intento de login fallido"""
    log_critical(
        event_type="LOGIN FALLIDO",
        emoji="🚨",
        details={"motivo": reason},
        user_email=identifier,
        ip_address=ip_address
    )


def log_error_500(
    endpoint: str,
    error_message: str,
    user_email: Optional[str] = None,
    stack_trace: Optional[str] = None
):
    """Log de error 500 (crash del servidor)"""
    details = {
        "endpoint": endpoint,
        "error": error_message
    }
    
    if stack_trace:
        # Limitar stack trace a primeras 3 líneas
        stack_lines = stack_trace.split('\n')[:3]
        details["stack"] = " | ".join(stack_lines)
    
    log_critical(
        event_type="ERROR 500 - CRASH",
        emoji="🔥",
        details=details,
        user_email=user_email
    )


def log_project_deleted(
    project_id: int,
    project_code: str,
    admin_email: str,
    tickets_count: int = 0
):
    """Log de eliminación de proyecto"""
    log_critical(
        event_type="PROYECTO ELIMINADO",
        emoji="🗑️",
        details={
            "proyecto_id": f"#{project_id}",
            "codigo": project_code,
            "tickets_eliminados": tickets_count
        },
        user_email=admin_email
    )


def log_user_deleted(
    user_id: int,
    user_email: str,
    user_role: str,
    admin_email: str
):
    """Log de eliminación de usuario"""
    log_critical(
        event_type="USUARIO ELIMINADO",
        emoji="🗑️",
        details={
            "user_id": f"#{user_id}",
            "email_eliminado": user_email,
            "rol": user_role
        },
        user_email=admin_email
    )


def log_role_changed(
    target_user_email: str,
    old_role: str,
    new_role: str,
    admin_email: str
):
    """Log de cambio de rol de usuario"""
    log_critical(
        event_type="CAMBIO DE ROL",
        emoji="👑",
        details={
            "usuario_afectado": target_user_email,
            "rol_anterior": old_role,
            "rol_nuevo": new_role
        },
        user_email=admin_email
    )


def log_exception(
    exception_type: str,
    exception_message: str,
    endpoint: Optional[str] = None,
    user_email: Optional[str] = None
):
    """Log de excepción inesperada"""
    details = {
        "tipo": exception_type,
        "mensaje": exception_message
    }
    
    if endpoint:
        details["endpoint"] = endpoint
    
    log_critical(
        event_type="EXCEPCIÓN INESPERADA",
        emoji="💥",
        details=details,
        user_email=user_email
    )


def log_file_upload_failed(
    filename: str,
    error_message: str,
    user_email: str,
    file_size_mb: Optional[float] = None
):
    """Log de fallo en subida de archivo"""
    details = {
        "archivo": filename,
        "error": error_message
    }
    
    if file_size_mb:
        details["tamaño_mb"] = f"{file_size_mb:.2f}MB"
    
    log_critical(
        event_type="ERROR UPLOAD ARCHIVO",
        emoji="📁",
        details=details,
        user_email=user_email
    )
