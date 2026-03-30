"""
Migración Fase 1 — Módulo de Proveedores.

Crea las 4 tablas nuevas y añade 3 columnas a tickets.
Compatible con PostgreSQL (producción) y SQLite (local).
Idempotente: se puede ejecutar múltiples veces sin error.

Uso:
    cd backend
    python -m scripts.migrate_suppliers
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text, inspect
from config.database import engine, SessionLocal
from app.models.database import Base
from app.models.suppliers import Base as SuppliersBase  # noqa: F401 - register tables


def table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    if not table_exists(inspector, table_name):
        return False
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def run_migration():
    inspector = inspect(engine)
    is_postgres = "postgresql" in str(engine.url)

    print(f"Motor: {'PostgreSQL' if is_postgres else 'SQLite'}")
    print(f"URL: {engine.url}\n")

    # --- Paso 1: Crear tablas nuevas (si no existen) ---
    new_tables = ["supplier_ocs", "suppliers", "supplier_invoices", "supplier_notifications"]
    for tname in new_tables:
        if table_exists(inspector, tname):
            print(f"  [SKIP] Tabla '{tname}' ya existe")
        else:
            print(f"  [CREATE] Tabla '{tname}'")

    # create_all solo crea tablas que no existen
    Base.metadata.create_all(bind=engine)

    # --- Paso 2: Añadir columnas a tickets ---
    new_columns = [
        ("from_supplier_portal", "BOOLEAN DEFAULT FALSE"),
        ("supplier_id", "INTEGER REFERENCES suppliers(id)"),
        ("supplier_invoice_id", "INTEGER REFERENCES supplier_invoices(id)"),
    ]

    # Refrescar inspector después de create_all
    inspector = inspect(engine)

    with engine.begin() as conn:
        for col_name, col_def in new_columns:
            if column_exists(inspector, "tickets", col_name):
                print(f"  [SKIP] Columna 'tickets.{col_name}' ya existe")
            else:
                # SQLite no soporta REFERENCES en ALTER TABLE, pero lo ignora silenciosamente
                sql = f"ALTER TABLE tickets ADD COLUMN {col_name} {col_def}"
                conn.execute(text(sql))
                print(f"  [ADD] Columna 'tickets.{col_name}'")

    # --- Paso 3: Crear índices si PostgreSQL ---
    if is_postgres:
        with engine.begin() as conn:
            indices = [
                ("idx_tickets_from_supplier_portal", "tickets", "from_supplier_portal"),
                ("idx_tickets_supplier_id", "tickets", "supplier_id"),
                ("idx_supplier_invoices_status", "supplier_invoices", "status"),
                ("idx_supplier_invoices_oc_number", "supplier_invoices", "oc_number"),
                ("idx_supplier_notifications_recipient", "supplier_notifications", "recipient_id"),
            ]
            for idx_name, tbl, col in indices:
                try:
                    conn.execute(text(
                        f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl} ({col})"
                    ))
                    print(f"  [INDEX] {idx_name}")
                except Exception:
                    print(f"  [SKIP] Index {idx_name} ya existe")

    print("\n=== Migración Fase 1 completada ===")


if __name__ == "__main__":
    run_migration()
