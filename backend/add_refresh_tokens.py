"""
Script de migración: Crear tabla refresh_tokens
================================================
Ejecutar en Railway o local para añadir la tabla de refresh tokens.

Uso:
    python add_refresh_tokens.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text, inspect

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dazz_producciones.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def run_migration():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "refresh_tokens" in existing_tables:
        print("✅ Tabla refresh_tokens ya existe. No se necesita migración.")
        return

    print("🔄 Creando tabla refresh_tokens...")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE refresh_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR NOT NULL UNIQUE,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                revoked_at TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE INDEX ix_refresh_tokens_token ON refresh_tokens(token)
        """))

        conn.execute(text("""
            CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id)
        """))

    print("✅ Tabla refresh_tokens creada correctamente")
    print("✅ Índices creados: ix_refresh_tokens_token, ix_refresh_tokens_user_id")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Error en migración: {str(e)}")
        sys.exit(1)
