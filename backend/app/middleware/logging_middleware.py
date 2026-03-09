"""
Middleware de Logging para FastAPI
===================================

Registra automáticamente todos los requests HTTP
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from typing import Callable
from app.services.logging_config import log_endpoint_access


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que registra automáticamente todos los requests
    
    Captura:
    - Método HTTP
    - Path
    - Status code
    - Tiempo de respuesta
    - Usuario autenticado (si existe)
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Tiempo de inicio
        start_time = time.time()
        
        # Procesar request
        response = await call_next(request)
        
        # Calcular tiempo de respuesta
        process_time = (time.time() - start_time) * 1000  # ms
        
        # Extraer información del request
        method = request.method
        path = request.url.path
        status_code = response.status_code
        
        # NO intentar obtener usuario aquí - el middleware se ejecuta ANTES de los dependencies
        # El usuario se registrará en los endpoints específicos si es necesario
        user_email = None
        
        # Registrar solo si no es un endpoint estático
        if not path.startswith("/uploads"):
            log_endpoint_access(
                method=method,
                path=path,
                user_email=user_email,
                status_code=status_code,
                response_time=process_time
            )
        
        # Añadir header con tiempo de respuesta
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        
        return response
