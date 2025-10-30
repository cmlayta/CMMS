import pandas as pd
import mysql.connector

# === CONFIGURACIÓN ===
ruta_excel = r"C:\Users\Proyectos 2\Downloads\Listas Maquinas en SAP al 18062025.xlsx"  # Cambia esta ruta
hoja = 0  # o el nombre de la hoja si no es la primera
host = "192.168.0.122"  # IP de tu servidor MySQL
user = "layta"
password = "Layta.123"
database = "basedatos"

# === LEER EL EXCEL ===
df = pd.read_excel(ruta_excel, sheet_name=hoja)

# Verifica que las columnas existan
print("Columnas encontradas:", df.columns.tolist())

# === CONEXIÓN A MYSQL ===
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)
cursor = conn.cursor()

# === INSERTAR SOLO LAS DOS COLUMNAS ===
for _, fila in df.iterrows():
    codigo = str(fila["Name"]) if not pd.isna(fila["Name"]) else None
    nombre = str(fila["Descripción"]) if not pd.isna(fila["Descripción"]) else None

    if codigo or nombre:  # Solo insertar si hay datos
        cursor.execute("""
            INSERT INTO equipos (codigo, nombre)
            VALUES (%s, %s)
        """, (codigo, nombre))

conn.commit()
cursor.close()
conn.close()

print("✅ Datos importados exitosamente.")
