"""
Script de migración para añadir campos de moneda extranjera
Ejecutar ANTES de usar las nuevas funcionalidades

USO:
cd backend
python add_foreign_currency.py
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dazz_producciones.db")

def migrate_add_foreign_currency():
    """
    Añade los campos necesarios para moneda extranjera a la tabla tickets
    """
    
    print("🔄 Iniciando migración de base de datos...")
    print(f"   Database: {DATABASE_URL}")
    
    engine = create_engine(DATABASE_URL)
    
    # Comandos SQL para añadir columnas
    migrations = [
        # Campos básicos internacionales
        "ALTER TABLE tickets ADD COLUMN is_foreign BOOLEAN DEFAULT 0",
        "ALTER TABLE tickets ADD COLUMN currency VARCHAR DEFAULT 'EUR'",
        "ALTER TABLE tickets ADD COLUMN country_code VARCHAR",
        "ALTER TABLE tickets ADD COLUMN geo_classification VARCHAR",
        
        # Importes en divisa original
        "ALTER TABLE tickets ADD COLUMN foreign_amount FLOAT",
        "ALTER TABLE tickets ADD COLUMN foreign_total FLOAT",
        "ALTER TABLE tickets ADD COLUMN foreign_tax_amount FLOAT",
        
        # Tasa de cambio
        "ALTER TABLE tickets ADD COLUMN exchange_rate FLOAT",
        "ALTER TABLE tickets ADD COLUMN exchange_rate_date DATE",
        
        # IVA extranjero en EUR (para estadísticas)
        "ALTER TABLE tickets ADD COLUMN foreign_tax_eur FLOAT",
    ]
    
    with engine.connect() as connection:
        for i, sql in enumerate(migrations, 1):
            try:
                print(f"\n[{i}/{len(migrations)}] Ejecutando: {sql[:60]}...")
                connection.execute(text(sql))
                connection.commit()
                print(f"   ✅ Éxito")
            except Exception as e:
                error_msg = str(e)
                if "duplicate column" in error_msg.lower() or "already exists" in error_msg.lower():
                    print(f"   ⚠️  Columna ya existe (ok)")
                else:
                    print(f"   ❌ Error: {error_msg}")
                    print(f"   ℹ️  Continuando con siguiente columna...")
    
    print("\n✅ Migración completada!")
    print("\n📋 Campos añadidos:")
    print("   - is_foreign: ¿Es factura internacional?")
    print("   - currency: Divisa (USD, GBP, CHF, etc.)")
    print("   - country_code: Código país (US, GB, etc.)")
    print("   - geo_classification: NACIONAL/UE/INTERNACIONAL")
    print("   - foreign_amount: Base en divisa original")
    print("   - foreign_total: Total en divisa original")
    print("   - foreign_tax_amount: IVA en divisa original")
    print("   - exchange_rate: Tasa de cambio histórica")
    print("   - exchange_rate_date: Fecha de la tasa")
    print("   - foreign_tax_eur: IVA reclamable en EUR")
    
    print("\n🎯 Próximos pasos:")
    print("   1. Reiniciar backend: python main.py")
    print("   2. Probar subir factura internacional")
    print("   3. Verificar detección automática")
    
    return True


def verify_migration():
    """
    Verifica que todas las columnas se hayan añadido correctamente
    """
    
    print("\n🔍 Verificando migración...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        # Obtener información de columnas
        result = connection.execute(text("PRAGMA table_info(tickets)"))
        columns = [row[1] for row in result.fetchall()]
        
        expected_columns = [
            'is_foreign',
            'currency',
            'country_code',
            'geo_classification',
            'foreign_amount',
            'foreign_total',
            'foreign_tax_amount',
            'exchange_rate',
            'exchange_rate_date',
            'foreign_tax_eur'
        ]
        
        print("\n📊 Estado columnas:")
        all_good = True
        for col in expected_columns:
            if col in columns:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col} - FALTA")
                all_good = False
        
        if all_good:
            print("\n✅ ¡Todas las columnas están presentes!")
            return True
        else:
            print("\n⚠️  Algunas columnas faltan. Ejecuta la migración de nuevo.")
            return False


def rollback_migration():
    """
    ROLLBACK: Elimina las columnas añadidas (por si algo sale mal)
    ⚠️  CUIDADO: Esto eliminará los datos de estas columnas
    """
    
    print("\n⚠️  ROLLBACK - Eliminando columnas moneda extranjera...")
    
    response = input("¿Estás seguro? Esto eliminará datos. (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Rollback cancelado")
        return False
    
    engine = create_engine(DATABASE_URL)
    
    # SQLite no soporta DROP COLUMN directamente
    # Habría que recrear la tabla sin esas columnas
    print("ℹ️  Para SQLite, el rollback requiere recrear la tabla.")
    print("ℹ️  Mejor opción: Restaurar backup de base de datos.")
    
    return False


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("MIGRACIÓN BASE DE DATOS - MONEDA EXTRANJERA")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback_migration()
    elif len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_migration()
    else:
        # Ejecutar migración
        migrate_add_foreign_currency()
        
        # Verificar
        verify_migration()
        
        print("\n" + "=" * 60)
        print("✅ LISTO PARA USAR")
        print("=" * 60)
