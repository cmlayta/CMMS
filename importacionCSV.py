import pandas as pd
import mysql.connector

# === CONFIGURACIÓN ===
ruta_csv = r"C:\Users\Proyectos 2\Desktop\CMMS\mantenimiento_cmms\ListadeArtículos20251107.csv"  # <-- cambia esta ruta
host = "192.168.0.122"
user = "layta"
password = "Layta.123"
database = "basedatos"

# === LEER EL CSV ===
df = pd.read_csv(ruta_csv, sep=",", encoding='utf-8')
print("Columnas encontradas:", df.columns.tolist())

# === CONEXIÓN A MYSQL ===
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)
cursor = conn.cursor()

# === FUNCIÓN PARA CONVERTIR PRECIO DE FORMA SEGURA ===
def limpiar_precio(valor):
    if pd.isna(valor):
        return 0.0
    try:
        # Elimina espacios, reemplaza coma decimal o separador de miles
        v = str(valor).strip().replace(',', '').replace(' ', '')
        return float(v)
    except:
        return 0.0

# === RECORRER E INSERTAR ===
for _, fila in df.iterrows():
    codigo = str(fila["Número de artículo"]).strip() if not pd.isna(fila["Número de artículo"]) else None
    nombre = str(fila["Descripción del artículo"]).strip() if not pd.isna(fila["Descripción del artículo"]) else None
    ubicacion = str(fila["Ubicacion"]).strip() if not pd.isna(fila["Ubicacion"]) else None

    # Convertir stock y precio con control de errores
    try:
        stock = int(float(str(fila["En stock"]).replace(',', '').strip())) if not pd.isna(fila["En stock"]) else 0
    except:
        stock = 0

    precio = limpiar_precio(fila["Último precio de compra"])

    # Valores por defecto
    tipo = "Indefinido"
    comercial = "Indefinido"
    proveniencia = "Indefinido"
    proveedor = "Indefinido"
    codigo_fabricante = "Indefinido"
    stock_minimo = 0

    # Evitar filas vacías
    if codigo or nombre:
        cursor.execute("""
            INSERT INTO repuestos 
            (codigo, nombre, tipo, ubicacion, stock, comercial, proveniencia, proveedor, codigo_fabricante, stock_minimo, precio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            codigo, nombre, tipo, ubicacion, stock, comercial, proveniencia, proveedor, codigo_fabricante, stock_minimo, precio
        ))

# === GUARDAR Y CERRAR ===
conn.commit()
cursor.close()
conn.close()

print("✅ Datos importados exitosamente a la tabla 'repuestos'.")
