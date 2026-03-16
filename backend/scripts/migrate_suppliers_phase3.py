"""
Migración Fase 3 — Tablas de invitaciones y refresh tokens de proveedores.
Idempotente. Compatible PostgreSQL + SQLite.

Uso:
    cd backend
    python -m scripts.migrate_suppliers_phase3
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import inspect
from config.database import engine
from app.models.database import Base
from app.models.suppliers import (  # noqa: F401 - register tables
    SupplierInvitation, SupplierRefreshToken,
)


def table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def run_migration():
    inspector = inspect(engine)
    is_postgres = "postgresql" in str(engine.url)

    print(f"Motor: {'PostgreSQL' if is_postgres else 'SQLite'}")

    new_tables = ["supplier_invitations", "supplier_refresh_tokens"]
    for tname in new_tables:
        if table_exists(inspector, tname):
            print(f"  [SKIP] Tabla '{tname}' ya existe")
        else:
            print(f"  [CREATE] Tabla '{tname}'")

    Base.metadata.create_all(bind=engine)

    print("\n=== Migración Fase 3 completada ===")


if __name__ == "__main__":
    run_migration()
