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
    # PostgreSQL: sin check_same_thread
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
