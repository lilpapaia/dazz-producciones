"""
DEUDA-M1: Configuración centralizada de logging.

Reemplaza print() con logging estructurado.
Railway captura stdout igual, pero logging añade timestamp, nivel y módulo.
"""

import logging
import os

def setup_logging():
    """Configurar logging global. Llamar una vez al arrancar."""
    level = logging.DEBUG if os.getenv("ENVIRONMENT") == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
