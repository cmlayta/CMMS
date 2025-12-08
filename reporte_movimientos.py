import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

# ---------- CONFIGURACIÓN ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Layta.123',
    'database': 'basedatos',
    'port': 3306
}

EMAIL_CONFIG = {
    'remitente': 'cmlayta@gmail.com',
    'destinatario': 'proyectos@layta.gt, mantenimiento@layta.gt, rsuarezv@layta.gt',
    'password': 'fmgg kszc ymys lubo',
    'smtp': 'smtp.gmail.com',
    'puerto': 465
}

# ---------- FUNCIONES ----------

def obtener_conexion():
    return mysql.connector.connect(**DB_CONFIG)

def obtener_movimientos_semana():
    hoy = datetime.today()
    inicio_semana = hoy - timedelta(days=7)
    fin_semana = hoy.replace(hour=23, minute=59, second=59, microsecond=0)

    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("""
        SELECT m.id, r.nombre, m.tipo_movimiento, m.stock, m.fecha, m.tecnico, m.maquina
        FROM movimientos m
        JOIN repuestos r ON m.repuesto_id = r.id
        WHERE m.fecha BETWEEN %s AND %s
        ORDER BY m.fecha ASC
    """, (inicio_semana, fin_semana))

    resultados = cur.fetchall()
    con.close()
    return resultados, inicio_semana.date(), fin_semana.date()

def exportar_excel_movimientos(movimientos):
    df = pd.DataFrame(movimientos, columns=['ID', 'Repuesto', 'Tipo', 'Cantidad', 'Fecha', 'Técnico', 'Máquina'])
    ruta = 'reporte_movimientos.xlsx'
    df.to_excel(ruta, index=False)
    return ruta, df

def generar_resumen(df, inicio, fin):
    resumen = f"Resumen de movimientos del {inicio} al {fin}:\n\n"
    resumen += df.groupby(['Tipo', 'Repuesto'])['Cantidad'].sum().to_string()
    resumen += "\n\nTotal de movimientos: {}\n".format(len(df))
    return resumen

def obtener_alertas_stock():
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("SELECT nombre, tipo, stock, stock_minimo FROM repuestos WHERE stock < stock_minimo")
    datos = cur.fetchall()
    con.close()
    return datos

def exportar_excel_alertas(alertas):
    df_alertas = pd.DataFrame(alertas, columns=['Nombre', 'Tipo', 'Stock Actual', 'Stock Mínimo'])
    ruta = 'alertas_stock.xlsx'
    df_alertas.to_excel(ruta, index=False)
    return ruta

def enviar_correo(resumen, adjunto_mov, adjunto_alertas):
    msg = EmailMessage()
    msg['Subject'] = 'Resumen semanal de movimientos de repuestos'
    msg['From'] = EMAIL_CONFIG['remitente']
    msg['To'] = EMAIL_CONFIG['destinatario']
    msg.set_content(resumen)

    # Adjuntar reporte de movimientos
    with open(adjunto_mov, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application',
                           subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           filename='reporte_movimientos.xlsx')

    # Adjuntar reporte de alertas de stock
    with open(adjunto_alertas, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application',
                           subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           filename='alertas_stock.xlsx')

    with smtplib.SMTP_SSL(EMAIL_CONFIG['smtp'], EMAIL_CONFIG['puerto']) as smtp:
        smtp.login(EMAIL_CONFIG['remitente'], EMAIL_CONFIG['password'])
        smtp.send_message(msg)

# ---------- EJECUCIÓN PRINCIPAL ----------
if __name__ == '__main__':
    movimientos, inicio, fin = obtener_movimientos_semana()

    if movimientos:
        excel_mov, df_mov = exportar_excel_movimientos(movimientos)
        resumen = generar_resumen(df_mov, inicio, fin)

        alertas = obtener_alertas_stock()
        excel_alertas = exportar_excel_alertas(alertas)

        enviar_correo(resumen, excel_mov, excel_alertas)
        print("Correo enviado correctamente con reporte y alertas.")
    else:
        print("No hubo movimientos durante la semana pasada.")
