
import csv
import mysql.connector

# Conexión a la BD
cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Layta.123',
    database='basedatos'
)
cursor = cnx.cursor()

with open("ListadeArtículos20250822.csv", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)  # Saltar encabezado si lo tiene
    for row in reader:
        codigo = row[1].strip()  # Columna 2 -> "Número de artículo"
        precio_str = row[4].strip()  # Columna 5 -> precio

        # 🔹 Quitar separadores de miles
        precio_str = precio_str.replace(",", "")  

        try:
            precio = float(precio_str)  # Convertir a número válido
        except ValueError:
            print(f"⚠️ Error en fila {row}: {precio_str} no es un número válido")
            continue

        # Actualizar en la BD
        cursor.execute("""
            UPDATE repuestos
            SET precio = %s
            WHERE codigo = %s
        """, (precio, codigo))

cnx.commit()
cursor.close()
cnx.close()

print("✅ Precios actualizados correctamente.")
