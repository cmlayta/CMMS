import pandas as pd
import mysql.connector
from datetime import datetime

# ---------- CONFIGURACIÓN ----------
CSV_PATH = "ActividadesOTS.csv"
    
DB_CONFIG = {
    "host": "192.168.0.122",
    "user": "root",
    "password": "Layta.123",
    "database": "basedatos"
}

# ---------- FUNCIONES ----------
def to_int_or_none(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value == "" or not value.isdigit():
        return None
    return int(value)

def to_str_or_none(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value if value != "" else None

def to_date_or_none(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    try:
        return pd.to_datetime(value).date()
    except:
        return None

# ---------- LEER CSV ----------
df = pd.read_csv(CSV_PATH)

# ---------- CONEXIÓN MYSQL ----------
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# ---------- INSERT ----------
sql = """
INSERT INTO actividades_ot_fijas (
    ot_fija_id,
    codigo_actividad,
    prioridad,
    frecuencia_new,
    dia_semana,
    semana_mes,
    mes,
    dia_mes,
    actividad,
    duracion,
    observaciones,
    fecha_creacion
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for _, row in df.iterrows():
    frecuencia = to_str_or_none(row["frecuencia_new"])

    dia_semana = to_int_or_none(row["dia_semana"])
    semana_mes = to_int_or_none(row["semana_mes"])
    mes        = to_int_or_none(row["mes"])
    dia_mes    = to_int_or_none(row["dia_mes"])

    # --------- REGLAS SEGÚN FRECUENCIA ----------
    if frecuencia == "Diaria":
        dia_semana = semana_mes = mes = dia_mes = None

    elif frecuencia in ("Semanal", "Quincenal"):
        semana_mes = mes = dia_mes = None

    elif frecuencia == "Mensual":
        dia_semana = semana_mes = mes = None

    elif frecuencia in ("Trimestral", "Semestral", "Anual"):
        dia_semana = semana_mes = None

    elif frecuencia == "Personalizada":
        dia_semana = semana_mes = mes = dia_mes = None

    values = (
        to_int_or_none(row["numero_ot"]),
        to_str_or_none(row["codigo_actividad"]),
        to_str_or_none(row["Prioridad"]),
        frecuencia,
        dia_semana,
        semana_mes,
        mes,
        dia_mes,
        to_str_or_none(row["actividad"]),
        to_int_or_none(row["duracion"]),
        to_str_or_none(row["observaciones"]),
        to_date_or_none(row["fecha_creacion"])
    )

    cursor.execute(sql, values)

conn.commit()
cursor.close()
conn.close()

print("Importación completada correctamente.")


