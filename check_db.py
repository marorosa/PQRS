#!/usr/bin/env python3
"""
Script para verificar la estructura de la base de datos
"""
import sqlite3
import os

# Conectar a la base de datos
db_path = "reflex.db"
if not os.path.exists(db_path):
    print(f"Base de datos {db_path} no encontrada")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("=== TABLAS EN LA BASE DE DATOS ===")
for table in tables:
    table_name = table[0]
    print(f"\nTabla: {table_name}")

    # Ver columnas
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    print("  Columnas:")
    for col in columns:
        cid, name, type_, notnull, dflt_value, pk = col
        print(f"    - {name}: {type_} {'(PK)' if pk else ''}")

conn.close()