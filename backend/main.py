from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os
import logging

# DEUDA-M1: Configurar logging antes de importar módulos
from app.services.log_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

from database_config import engine
from app.models.database import Base
from app.routes import users, auth, projects, tickets, statistics, companies
from app.routes import suppliers as suppliers_admin, supplier_portal, autoinvoice
from app.services.rate_limit import limiter

# Create FastAPI app
app = FastAPI(
    title="Dazz Creative - Sistema Gestión Gastos",
    description="API para gestión de proyectos y tickets/facturas con IA",
    version="2.0.0",
    redirect_slashes=False
)

# Añadir limiter al state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================
# 🔒 VULN-015: SECURITY HEADERS MIDDLEWARE
# ============================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# SEC-M4 / SEC-H4: Decisión arquitectónica sobre tokens y CSRF.
#
# Los tokens JWT se almacenan en localStorage (no cookies). Esto significa:
# - CSRF no es un vector de ataque (el navegador no adjunta tokens automáticamente)
# - El riesgo teórico es XSS → robo de token desde localStorage
# - Mitigaciones XSS actuales: CORS restrictivo, security headers, React auto-escaping,
#   sanitize_string(), no se usa dangerouslySetInnerHTML
# - Migrar a cookies HttpOnly requeriría ~8-12h de cambios cross-stack (backend cookies +
#   frontend eliminar localStorage + implementar CSRF tokens) con alto riesgo de regresión
# - Con 3-5 usuarios internos y sin contenido de terceros (ads, widgets, analytics JS),
#   el riesgo XSS real es muy bajo
# - Reconsiderar si se añade contenido de terceros o se abre a usuarios públicos

# ============================================
# 🔒 CONFIGURACIÓN SEGURA DE CORS
# ============================================
# VULN-011: Default "production", no "development"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Orígenes permitidos - SOLO TUS DOMINIOS
SUPPLIER_PORTAL_URL = os.getenv("SUPPLIER_PORTAL_URL", "https://providers.dazzcreative.com")
ALLOWED_ORIGINS = [
    "https://dazz-producciones.vercel.app",  # Producción DAZZ
    SUPPLIER_PORTAL_URL,                     # Portal proveedores (env var)
]

# En desarrollo también permitir localhost
if ENVIRONMENT == "development":
    ALLOWED_ORIGINS.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ])

# VULN-017: Restringir métodos y headers CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Email-Sent", "X-Email-Error", "Content-Disposition"],
)

# VULN-003: Eliminado mount de /uploads (archivos van a Cloudinary)
# El directorio uploads/ sigue existiendo para archivos temporales
# pero NO se expone como ruta pública
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tickets.router)
app.include_router(users.router)
app.include_router(statistics.router)
app.include_router(companies.router)
app.include_router(suppliers_admin.router)
app.include_router(autoinvoice.router)
app.include_router(supplier_portal.router)

@app.get("/")
@limiter.limit("10 per minute")
async def root(request: Request):
    return {
        "message": "Dazz Creative - API Sistema Gestión Gastos",
        "version": "2.0.0",
        "status": "running",
        "environment": ENVIRONMENT
    }

@app.get("/health")
@limiter.limit("30 per minute")
async def health_check(request: Request):
    return {"status": "healthy"}


# ============================================
# 🧪 ENDPOINTS DE TEST - SOLO EN DESARROLLO
# SEC-H6: Seguro porque ENVIRONMENT defaulta a "production" (línea 69).
# Solo se registran si ENVIRONMENT es exactamente "development".
# Cualquier otro valor (o variable no seteada) los excluye.
# ============================================
if ENVIRONMENT == "development":
    @app.get("/test-brevo")
    @limiter.limit("5 per hour")
    async def test_brevo(request: Request):
        """Prueba la conexión con Brevo API."""
        from app.services.email import test_brevo_connection
        return test_brevo_connection()

    @app.get("/test-brevo/send")
    @limiter.limit("3 per hour")
    async def test_brevo_send(
        request: Request,
        email_to: str = Query(..., alias="email", description="Email destino")
    ):
        """Envía un email de prueba con Brevo."""
        from app.services.email import send_email

        try:
            send_email(
                to_email=email_to,
                subject="✅ Test Brevo desde Railway",
                html_content="""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <div style="max-width: 500px; margin: 0 auto; border: 2px solid #4CAF50; border-radius: 10px; padding: 20px;">
                        <h1 style="color: #4CAF50;">¡Funciona! 🎉</h1>
                        <p>Este email se ha enviado desde Railway usando Brevo API.</p>
                        <p>La configuración es correcta.</p>
                    </div>
                </body>
                </html>
                """
            )
            return {"success": True, "message": "Email enviado", "to": email_to}
        except Exception as e:
            return {"success": False, "message": str(e), "to": email_to}


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

    # Migraciones idempotentes al arrancar (todas <1ms si ya existen)
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            # PERF-M2: Índices compuestos
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_supplier_invoices_supplier_status "
                "ON supplier_invoices (supplier_id, status)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_notifications_recipient_read "
                "ON supplier_notifications (recipient_type, recipient_id, is_read)"
            ))
            # LOGIC-M2: Columna date_parsed (ahora mapeada en ORM)
            conn.execute(text(
                "ALTER TABLE supplier_invoices ADD COLUMN IF NOT EXISTS date_parsed DATE"
            ))
            # Autoinvoice flag
            conn.execute(text(
                "ALTER TABLE supplier_invoices ADD COLUMN IF NOT EXISTS is_autoinvoice BOOLEAN DEFAULT FALSE"
            ))
            # SEC-H2: Columnas account lockout
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0"
            ))
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP"
            ))
            # supplier_type ya no se mapea en ORM — hacer nullable con default
            conn.execute(text(
                "ALTER TABLE suppliers ALTER COLUMN supplier_type DROP NOT NULL"
            ))
            conn.execute(text(
                "ALTER TABLE suppliers ALTER COLUMN supplier_type SET DEFAULT 'GENERAL'"
            ))
            # Facturas sin OC: oc_number nullable para OC_PENDING
            conn.execute(text(
                "ALTER TABLE supplier_invoices ALTER COLUMN oc_number DROP NOT NULL"
            ))
            # Pending actions: IBAN change + cert verification
            conn.execute(text(
                "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS pending_iban_encrypted BYTEA"
            ))
            conn.execute(text(
                "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS ia_cert_verified BOOLEAN DEFAULT TRUE"
            ))
            # SEC-7: OC unique constraint (partial index — allows multiple NULLs)
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_suppliers_oc_id "
                "ON suppliers (oc_id) WHERE oc_id IS NOT NULL"
            ))
            # SEC-5: NIF unique constraint (case-insensitive partial index)
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_suppliers_nif_cif "
                "ON suppliers (UPPER(nif_cif)) WHERE nif_cif IS NOT NULL"
            ))
            # BUG-5: Notification metadata for structured data
            conn.execute(text(
                "ALTER TABLE supplier_notifications ADD COLUMN IF NOT EXISTS extra_data TEXT"
            ))
            # BUG-6: Pending bank cert URL on supplier
            conn.execute(text(
                "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS pending_bank_cert_url VARCHAR"
            ))
            # Detección duplicados: hash de archivo
            conn.execute(text(
                "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS file_hash VARCHAR(32)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_tickets_file_hash ON tickets (file_hash)"
            ))
            conn.commit()
        except Exception:
            pass  # SQLite u otros motores pueden no soportar IF NOT EXISTS

    logger.info("Base de datos inicializada")
    logger.info(f"Modo: {ENVIRONMENT}")
    logger.info(f"CORS permitido para: {ALLOWED_ORIGINS}")
    logger.info("Rate limiting: Activo (200/dia, 50/hora)")
    logger.info("Security headers: Activo")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
