import sqlite3

def update_database():
    print("🔧 Actualizando base de datos...")
    
    conn = sqlite3.connect('dazz_producciones.db')
    cursor = conn.cursor()
    
    # Obtener columnas actuales de la tabla tickets
    cursor.execute("PRAGMA table_info(tickets)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    print(f"\n📋 Columnas actuales en tabla tickets: {', '.join(existing_columns)}")
    
    # Campos nuevos necesarios para ReviewTicket
    new_columns = {
        'invoice_status': 'TEXT',
        'payment_status': 'TEXT',
        'phone': 'TEXT',
        'email': 'TEXT',
        'contact_name': 'TEXT',
        'notes': 'TEXT'  # NOTAS - CAMPO NUEVO
    }
    
    print(f"\n🔍 Verificando campos necesarios...")
    
    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE tickets ADD COLUMN {column_name} {column_type}")
                conn.commit()
                print(f"  ✓ Añadida columna: {column_name} ({column_type})")
            except Exception as e:
                print(f"  ✗ Error añadiendo {column_name}: {e}")
        else:
            print(f"  ✓ {column_name} ya existe")
    
    # Verificar resultado final
    cursor.execute("PRAGMA table_info(tickets)")
    final_columns = [row[1] for row in cursor.fetchall()]
    
    print(f"\n📋 Columnas finales en tabla tickets:")
    for col in final_columns:
        print(f"  - {col}")
    
    conn.close()
    print("\n✅ Base de datos actualizada correctamente\n")

if __name__ == "__main__":
    update_database()
