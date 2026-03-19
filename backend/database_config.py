"""
Configuración de base de datos que funciona tanto en local como en Railway

AUTOMÁTICO:
- En local: Usa SQLite (dazz_producciones.db)
- En Railway: Usa PostgreSQL ($DATABASE_URL)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Detectar si estamos en Railway (tiene DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # PRODUCCIÓN: PostgreSQL en Railway
    print("🚀 Usando PostgreSQL (Railway)")
    
    # Railway a veces usa 'postgres://' pero SQLAlchemy necesita 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    # LOCAL: SQLite
    print("💻 Usando SQLite (local)")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./dazz_producciones.db"

# Crear engine con configuración apropiada
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite: check_same_thread False
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PERF-M4: PostgreSQL con pool configurado para Railway (2 workers gunicorn)
    # pool_size=5 x 2 workers = 10 conexiones base, max_overflow=10 x 2 = 20 extras
    # pool_pre_ping: verifica conexión antes de usar (Railway cierra idle connections)
    # pool_recycle: recicla conexiones cada 5min (previene conexiones zombie)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
    )

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
