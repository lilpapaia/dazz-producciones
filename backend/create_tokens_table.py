"""
Script para crear la tabla password_reset_tokens
Versión 2: Recibe DATABASE_URL directamente

Uso:
    python create_tokens_table_v2.py "postgresql://postgres:PASSWORD@host:port/railway"
"""

import sys
from sqlalchemy import create_engine, text

if len(sys.argv) < 2:
    print("❌ ERROR: Debes pasar el DATABASE_URL como argumento")
    print("\nUso:")
    print('   python create_tokens_table_v2.py "postgresql://postgres:PASSWORD@host:port/railway"')
    print("\n💡 Copia el DATABASE_URL de Railway → Postgres → Variables")
    exit(1)

DATABASE_URL = sys.argv[1]

# Verificar que es PostgreSQL
if not DATABASE_URL.startswith('postgresql://') and not DATABASE_URL.startswith('postgres://'):
    print("❌ ERROR: El DATABASE_URL debe ser de PostgreSQL")
    print(f"   Recibido: {DATABASE_URL[:20]}...")
    print("   Debe empezar con: postgresql://")
    exit(1)

print("🔧 Conectando a PostgreSQL...")
print(f"   Host: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'unknown'}")

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
        print("\n✅ Verifica en Railway → PostgreSQL → Data → password_reset_tokens")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nPosibles causas:")
    print("1. DATABASE_URL incorrecta")
    print("2. No tienes permisos para crear tablas")
    print("3. La tabla ya existe (en ese caso, ignora este error)")
    exit(1)
