"""
Agrega las columnas faltantes a la tabla plan.
Uso: python migrate_plan_columns.py
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'agrodev.db')


def migrar():
    if not os.path.exists(DB_PATH):
        print(f"❌ No se encontró la DB: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Verificar columnas actuales
    cur.execute("PRAGMA table_info(plan)")
    columnas_actuales = [row[1] for row in cur.fetchall()]
    print(f"Columnas actuales: {columnas_actuales}\n")
    
    columnas_nuevas = {
        'limite_inventario': 'INTEGER DEFAULT 50',
        'limite_registros': 'INTEGER DEFAULT 10',
        'limite_gastos': 'INTEGER DEFAULT 10',
    }
    
    for col, tipo in columnas_nuevas.items():
        if col in columnas_actuales:
            print(f"  ✓ {col} ya existe")
            continue
        
        try:
            cur.execute(f"ALTER TABLE plan ADD COLUMN {col} {tipo}")
            print(f"  ✅ {col} agregada")
        except sqlite3.OperationalError as e:
            print(f"  ❌ Error al agregar {col}: {e}")
    
    conn.commit()
    
    # Verificar resultado
    cur.execute("PRAGMA table_info(plan)")
    columnas_finales = [row[1] for row in cur.fetchall()]
    print(f"\nColumnas finales: {columnas_finales}")
    
    # Actualizar valores de los planes existentes (ya tienen valores default)
    cur.execute("SELECT id, nombre_plan FROM plan")
    planes = cur.fetchall()
    print(f"\nPlanes en DB: {planes}")
    
    conn.close()
    print("\n✅ Migración completada")


if __name__ == '__main__':
    migrar()