"""
Script para crear la tabla password_reset_tokens
Ejecutar UNA SOLA VEZ

Uso:
    python create_tokens_table.py
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Obtener DATABASE_URL de las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: No se encontró DATABASE_URL en las variables de entorno")
    print("   Asegúrate de tener el archivo .env o las variables configuradas")
    exit(1)

print("🔧 Conectando a PostgreSQL...")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("✅ Conexión exitosa")
        print("📝 Creando tabla password_reset_tokens...")
        
        # Crear la tabla
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token TEXT NOT NULL UNIQUE,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                used_at TIMESTAMP NULL
            )
        """))
        
        print("✅ Tabla creada")
        print("📝 Creando índices...")
        
        # Crear índices
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token 
            ON password_reset_tokens(token)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id 
            ON password_reset_tokens(user_id)
        """))
        
        print("✅ Índices creados")
        
        # Commit de los cambios
        conn.commit()
        
        print("\n🎉 ¡Tabla password_reset_tokens creada exitosamente!")
        print("\n📋 Estructura de la tabla:")
        print("   - id (SERIAL PRIMARY KEY)")
        print("   - user_id (INTEGER FK → users)")
        print("   - token (TEXT UNIQUE)")
        print("   - expires_at (TIMESTAMP)")
        print("   - created_at (TIMESTAMP)")
        print("   - used_at (TIMESTAMP NULL)")
        print("\n✅ Puedes verificar en Railway → PostgreSQL → Data → password_reset_tokens")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nPosibles causas:")
    print("1. DATABASE_URL incorrecta o no configurada")
    print("2. No tienes permisos para crear tablas")
    print("3. La tabla ya existe (en ese caso, está bien)")
    exit(1)
