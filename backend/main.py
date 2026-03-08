from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os


from database_config import engine
from app.models.database import Base
from app.routes import users, auth, projects, tickets, statistics

# ============================================
# 🔒 RATE LIMITING
# ============================================
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    headers_enabled=True
)

# Create FastAPI app
app = FastAPI(
    title="Dazz Creative - Sistema Gestión Gastos",
    description="API para gestión de proyectos y tickets/facturas con IA",
    version="1.0.0",
    redirect_slashes=False
)

# Añadir limiter al state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================
# 🔒 CONFIGURACIÓN SEGURA DE CORS
# ============================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Orígenes permitidos - SOLO TUS DOMINIOS
ALLOWED_ORIGINS = [
    "https://dazz-producciones.vercel.app",  # Producción
]

# En desarrollo también permitir localhost
if ENVIRONMENT == "development":
    ALLOWED_ORIGINS.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for file access
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tickets.router)
app.include_router(users.router)
app.include_router(statistics.router)

@app.get("/")
@limiter.limit("10 per minute")  # Límite específico para este endpoint
async def root(request: Request):
    return {
        "message": "Dazz Creative - API Sistema Gestión Gastos",
        "version": "1.0.0",
        "status": "running",
        "environment": ENVIRONMENT
    }

@app.get("/health")
@limiter.limit("30 per minute")
async def health_check(request: Request):
    return {"status": "healthy"}


# ============================================
# 🧪 ENDPOINTS DE TEST - SOLO EN DESARROLLO
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
    print("✅ Base de datos inicializada")
    print(f"🔒 Modo: {ENVIRONMENT}")
    print(f"🌐 CORS permitido para: {ALLOWED_ORIGINS}")
    print(f"🛡️ Rate limiting: Activo (200/día, 50/hora)")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
