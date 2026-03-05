from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os


from database_config import engine
from app.models.database import Base
from app.routes import users, auth, projects, tickets, statistics

# Create FastAPI app
app = FastAPI(
    title="Dazz Creative - Sistema Gestión Gastos",
    description="API para gestión de proyectos y tickets/facturas con IA",
    version="1.0.0",
    redirect_slashes=False  # ✅ Evita redirects 307 que rompen auth
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
async def root():
    return {
        "message": "Dazz Creative - API Sistema Gestión Gastos",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

