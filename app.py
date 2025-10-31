from collections import Counter
from datetime import datetime, timedelta
from io import BytesIO
import os
import base64
import mysql.connector
import tempfile
import pandas as pd
from fpdf import FPDF
from matplotlib.figure import Figure
from flask import Flask, render_template, request, redirect, url_for, session, send_file

app = Flask(__name__)
app.secret_key = 'clave_super_secreta_123'

DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'basedatos.db')

def connect_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Layta.123',
        database='basedatos'
    )

@app.before_request
def proteger_rutas():

    rutas_libres = ['login', 'registro', 'static']
    if not session.get('usuario') and request.endpoint not in rutas_libres:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        con = connect_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM usuarios WHERE usuario=%s AND contrasena=%s", (usuario, contrasena))
        user = cur.fetchone()
        con.close()
        if user:
            session['usuario'] = user[1]
            session['rol'] = user[3]
            return redirect(url_for('inicio'))
        else:
            return "Credenciales inválidas"
    return render_template('login.html')
                                                                                                                                                                                    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

CLAVE_REGISTRO = "clave123"  # Clave requerida para permitir el registro

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        rol = request.form['rol']
        clave_ingresada = request.form['clave_admin']

        if clave_ingresada != CLAVE_REGISTRO:
            return render_template('registro.html', error="Clave de registro incorrecta.")

        con = connect_db()
        cur = con.cursor()
        try:
            cur.execute("INSERT INTO usuarios (usuario, contrasena, rol) VALUES (%s, %s, %s)",
                        (usuario, contrasena, rol))
            con.commit()
        except mysql.connector.IntegrityError:
            return render_template('registro.html', error="El usuario ya existe.")
        finally:
            con.close()

        return redirect(url_for('login'))

    return render_template('registro.html')


@app.route('/')

def inicio():
    return render_template('inicio.html', usuario=session.get('usuario'), rol=session.get('rol'))

# ------------------ REPUESTOS ------------------
@app.route('/repuestos')
def ver_repuestos():
    q = request.args.get('q', '')  # Recupera el valor del buscador si existe
    con = connect_db()
    cur = con.cursor()
    
    if q:
        cur.execute("""
            SELECT * FROM repuestos 
            WHERE codigo_fabricante LIKE %s OR nombre LIKE %s OR tipo LIKE %s OR ubicacion LIKE %s 
            OR proveniencia LIKE %s OR proveedor LIKE %s OR precio LIKE %s
        """, (f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%'))
    else:
        cur.execute("SELECT * FROM repuestos")
    
    repuestos = cur.fetchall()
    con.close()
    return render_template('ver_repuestos.html', repuestos=repuestos)

@app.route('/repuestos/agregar', methods=['GET', 'POST'])
def agregar_repuesto():
    con = connect_db()
    cur = con.cursor()
    if request.method == 'POST':
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        ubicacion = request.form['ubicacion']
        stock = int(request.form['stock'])
        comercial = request.form['comercial']
        proveniencia = request.form['proveniencia']
        proveedor = request.form['proveedor']
        codigo_fabricante = request.form['codigo_fabricante']
        stock_minimo = int(request.form['stock_minimo'])
        precio = float(request.form['precio'])  # NUEVO CAMPO

        cur.execute("""
            INSERT INTO repuestos 
            (codigo, nombre, tipo, ubicacion, stock, comercial, proveniencia, proveedor, codigo_fabricante, stock_minimo, precio) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (codigo, nombre, tipo, ubicacion, stock, comercial, proveniencia, proveedor, codigo_fabricante, stock_minimo, precio))
        con.commit()
        con.close()
        return redirect(url_for('ver_repuestos'))
    return render_template('agregar_repuesto.html')

@app.route('/repuestos/editar/<int:id>', methods=['GET', 'POST'])
def editar_repuesto(id):
    con = connect_db()
    cur = con.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        codigo = request.form['codigo']
        stock = int(request.form['stock'])
        comercial = request.form['comercial']
        proveniencia = request.form['proveniencia']
        proveedor = request.form['proveedor']
        codigo_fabricante = request.form['codigo_fabricante']
        stock_minimo = int(request.form['stock_minimo'])
        precio = float(request.form['precio'])  # NUEVO CAMPO

        cur.execute("""
            UPDATE repuestos 
            SET nombre=%s, codigo=%s, stock=%s, comercial=%s, proveniencia=%s, proveedor=%s, codigo_fabricante=%s, stock_minimo=%s, precio=%s 
            WHERE id=%s
        """, (nombre, codigo, stock, comercial, proveniencia, proveedor, codigo_fabricante, stock_minimo, precio, id))
        con.commit()
        con.close()
        return redirect(url_for('ver_repuestos'))

    cur.execute("SELECT * FROM repuestos WHERE id=%s", (id,))
    repuesto = cur.fetchone()
    con.close()
    return render_template('editar_repuesto.html', repuesto=repuesto)

@app.route('/repuestos/ingreso/<int:id>', methods=['GET', 'POST'])
def ingreso_repuesto(id):
    if request.method == 'POST':
        stock = int(request.form['stock'])
        usuario = session.get('usuario')
        con = connect_db()
        cur = con.cursor()
        cur.execute("UPDATE repuestos SET stock = stock + %s WHERE id = %s", (stock, id))
        cur.execute("INSERT INTO movimientos (repuesto_id, tipo_movimiento, stock, tecnico) VALUES (%s, 'ingreso', %s, %s)",
                    (id, stock, usuario))
        con.commit()
        con.close()
        return redirect(url_for('ver_repuestos'))
    return render_template('movimiento_repuesto.html', tipo='ingreso')

@app.route('/repuestos/salida/<int:id>', methods=['GET', 'POST'])
def salida_repuesto(id):
    con = connect_db()
    cur = con.cursor()

    if request.method == 'POST':
        stock = int(request.form['stock'])
        equipo_id = int(request.form['equipo_id']) 
        usuario = session.get('usuario')
        cur.execute("SELECT nombre FROM equipos WHERE id = %s", (equipo_id,))
        nombre_equipo = cur.fetchone()[0]
        cur.execute("SELECT stock FROM repuestos WHERE id = %s", (id,))
        actual = cur.fetchone()[0]

        if actual < stock:
            con.close()
            return "No hay suficientes repuestos"
        from datetime import datetime

        cur.execute("""
            INSERT INTO movimientos (repuesto_id, tipo_movimiento, stock, tecnico, maquina, fecha)
            VALUES (%s, 'salida', %s, %s, %s, %s)
        """, (id, stock, usuario, nombre_equipo, datetime.now()))
        cur.execute("UPDATE repuestos SET stock = stock - %s WHERE id = %s", (stock, id))
        con.commit()
        con.close()
        return redirect(url_for('ver_repuestos'))

    # Solo si GET: cargar equipos
    cur.execute("SELECT id, nombre FROM equipos")
    equipos = cur.fetchall()
    con.close()
    return render_template('salida_repuesto.html', equipos=equipos)

@app.route('/repuestos/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_repuesto(id):
    con = connect_db()
    cur = con.cursor()
    cur.execute('SELECT * FROM repuestos WHERE id = %s', (id,))
    repuesto = cur.fetchone()

    if request.method == 'POST':
        cur.execute('DELETE FROM repuestos WHERE id = %s', (id,))
        con.commit()
        con.close()
        return redirect(url_for('ver_repuestos'))

    con.close()
    return render_template('eliminar_repuesto.html', repuesto=repuesto)

@app.route('/repuestos/alertas_stock')
def alertas_stock():
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM repuestos WHERE stock < stock_minimo")
    repuestos_bajo_stock = cur.fetchall()
    con.close()
    return render_template('alertas_stock.html', repuestos=repuestos_bajo_stock)

# ------------------ EQUIPOS ------------------
@app.route('/equipos')
def ver_equipos():
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM equipos")
    equipos = cur.fetchall()
    con.close()
    return render_template('ver_equipos.html', equipos=equipos)

@app.route('/equipos/agregar', methods=['GET', 'POST'])
def agregar_equipo():
    if request.method == 'POST':
        nombre = request.form['nombre']
        codigo = request.form['codigo']
        categoria = request.form['categoria']
        modelo = request.form['modelo']
        marca = request.form['marca']
        fecha_ingreso = request.form['fecha_ingreso']
        con = connect_db()
        cur = con.cursor()
        cur.execute("INSERT INTO equipos (nombre, codigo, categoria, modelo, marca, fecha_ingreso) VALUES (%s, %s, %s, %s, %s, %s)",
                    (nombre, codigo, categoria, modelo, marca,fecha_ingreso))
        con.commit()
        con.close()
        return redirect(url_for('ver_equipos'))
    return render_template('agregar_equipo.html')

@app.route('/equipos/editar/<int:id>', methods=['GET', 'POST'])
def editar_equipo(id):
    con = connect_db()
    cur = con.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        codigo = request.form['codigo']
        categoria = request.form['categoria']
        modelo = request.form['modelo']
        marca = request.form['marca']
        cur.execute("UPDATE equipos SET nombre=%s, codigo=%s, categoria=%s, modelo=%s, marca=%s WHERE id=%s",
                    (nombre, codigo, categoria, modelo, marca, id))
        con.commit()
        con.close()
        return redirect(url_for('ver_equipos'))
    cur.execute("SELECT * FROM equipos WHERE id=%s", (id,))
    equipo = cur.fetchone()
    con.close()
    return render_template('editar_equipo.html', equipo=equipo)

@app.route('/equipos/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_equipo(id):
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM equipos WHERE id=%s", (id,))
    equipo = cur.fetchone()
    if request.method == 'POST':
        cur.execute("DELETE FROM equipos WHERE id=%s", (id,))
        con.commit()
        con.close()
        return redirect(url_for('ver_equipos'))
    con.close()
    return render_template('eliminar_equipo.html', equipo=equipo)

@app.route('/equipos/<int:equipo_id>/detalle')
def detalle_equipo(equipo_id):
    con = connect_db()
    cur = con.cursor()

    # Obtener los datos del equipo
    cur.execute("SELECT * FROM equipos WHERE id = %s", (equipo_id,))
    equipo = cur.fetchone()

    # Repuestos asociados al equipo con su ID, nombre, cantidad, comentario
    cur.execute("""
        SELECT er.id, r.nombre, er.cantidad, er.comentario
        FROM equipo_repuestos er
        JOIN repuestos r ON er.repuesto_id = r.id
        WHERE er.equipo_id = %s
    """, (equipo_id,))
    repuestos_equipo = cur.fetchall()

    # Todos los repuestos disponibles para mostrar en el select
    cur.execute("SELECT id, nombre FROM repuestos")
    todos_repuestos = cur.fetchall()

    # Historial de movimientos de salida de repuestos para este equipo
    cur.execute("""
        SELECT m.id, r.nombre, m.stock, m.fecha, m.tecnico
        FROM movimientos m
        JOIN repuestos r ON m.repuesto_id = r.id
        WHERE m.maquina = (SELECT nombre FROM equipos WHERE id = %s)
        AND m.tipo_movimiento = 'salida'
        ORDER BY m.fecha DESC
    """, (equipo_id,))
    historial_salidas = cur.fetchall()

    con.close()
    return render_template('detalle_equipo.html',
                           equipo=equipo,
                           repuestos_equipo=repuestos_equipo,
                           todos_repuestos=todos_repuestos,
                           historial_salidas=historial_salidas,
                           equipo_id=equipo_id)

@app.route('/equipos/<int:equipo_id>/asociar_repuesto', methods=['POST'])
def asociar_repuesto_equipo(equipo_id):
    repuesto_id = request.form['repuesto_id']
    cantidad = request.form['cantidad']
    comentario = request.form['comentario']

    con = connect_db()
    cur = con.cursor()
    cur.execute("INSERT INTO equipo_repuestos (equipo_id, repuesto_id, cantidad, comentario) VALUES (%s, %s, %s, %s)",
                (equipo_id, repuesto_id, cantidad, comentario))
    con.commit()
    con.close()
    return redirect(url_for('detalle_equipo', equipo_id=equipo_id))

@app.route('/equipos/<int:equipo_id>/eliminar_asociacion/<int:asociacion_id>', methods=['POST'])
def eliminar_asociacion_repuesto(equipo_id, asociacion_id):
    con = connect_db()
    cur = con.cursor()
    cur.execute("DELETE FROM equipo_repuestos WHERE id = %s", (asociacion_id,))
    con.commit()
    con.close()
    return redirect(url_for('detalle_equipo', equipo_id=equipo_id))

#----------------------REPORTES-------------------------
@app.route('/reporte_salida', methods=['GET', 'POST'])
def reporte_salida():
    con = connect_db()
    cur = con.cursor(dictionary=True)
    
    # Listas para filtros
    cur.execute("SELECT DISTINCT nombre FROM equipos")
    equipos_lista = [row['nombre'] for row in cur.fetchall()]
    cur.execute("SELECT DISTINCT tipo FROM repuestos")
    tipos_lista = [row['tipo'] for row in cur.fetchall()]
    
    filtros = {
        'equipos': [],
        'tipos': [],
        'fecha_inicio': '',
        'fecha_fin': ''
    }
    
    datos = []
    total_repuestos = 0
    etiquetas = []
    valores = []
    
    if request.method == 'POST':
        filtros['equipos'] = request.form.getlist('equipos')
        filtros['tipos'] = request.form.getlist('tipos')
        filtros['fecha_inicio'] = request.form.get('fecha_inicio')
        filtros['fecha_fin'] = request.form.get('fecha_fin')
        exportar = request.form.get('exportar')  # 'excel' o 'pdf'
        
        # "Todos"
        if 'todos' in filtros['equipos'] or set(filtros['equipos']) == set(equipos_lista):
            filtros['equipos'] = []
        if 'todos' in filtros['tipos'] or set(filtros['tipos']) == set(tipos_lista):
            filtros['tipos'] = []
        
        fecha_inicio = None
        fecha_fin = None
        try:
            if filtros['fecha_inicio']:
                fecha_inicio = datetime.strptime(filtros['fecha_inicio'], '%Y-%m-%d')
            if filtros['fecha_fin']:
                fecha_fin = datetime.strptime(filtros['fecha_fin'], '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            fecha_inicio = fecha_fin = None

        query = """
        SELECT 
            r.nombre AS repuesto,
            r.tipo,
            m.stock AS cantidad,
            m.id AS movimiento,
            m.fecha,
            m.maquina
        FROM movimientos m
        JOIN repuestos r ON m.repuesto_id = r.id
        WHERE m.tipo_movimiento = 'salida'
        """
        params = []
        
        if filtros['equipos']:
            query += " AND m.maquina IN (%s) " % ','.join(['%s']*len(filtros['equipos']))
            params.extend(filtros['equipos'])
        
        if filtros['tipos']:
            query += " AND r.tipo IN (%s) " % ','.join(['%s']*len(filtros['tipos']))
            params.extend(filtros['tipos'])
        
        if fecha_inicio and fecha_fin:
            query += " AND m.fecha BETWEEN %s AND %s "
            params.extend([fecha_inicio, fecha_fin])
        elif fecha_inicio:
            query += " AND m.fecha >= %s "
            params.append(fecha_inicio)
        elif fecha_fin:
            query += " AND m.fecha <= %s "
            params.append(fecha_fin)
        
        query += " ORDER BY m.fecha DESC"
        
        cur.execute(query, params)
        datos = cur.fetchall()
        total_repuestos = sum(d['cantidad'] for d in datos)
        
        # Gráfico
        conteo_por_maquina = {}
        for d in datos:
            maquina = d['maquina'] or 'Sin máquina'
            conteo_por_maquina[maquina] = conteo_por_maquina.get(maquina, 0) + d['cantidad']
        etiquetas = list(conteo_por_maquina.keys())
        valores = list(conteo_por_maquina.values())
        # === Exportar a Excel ===
        if exportar == 'excel':
            df = pd.DataFrame(datos)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Salidas')
            output.seek(0)
            return send_file(output, download_name='reporte_salidas.xlsx', as_attachment=True)

        # === Exportar a PDF ===
        elif exportar == 'pdf':
            from fpdf import FPDF
            import base64
            from matplotlib.figure import Figure
            import tempfile

            # Crear gráfico y guardarlo en memoria
            fig = Figure()
            ax = fig.subplots()
            ax.bar(etiquetas, valores, color='skyblue')
            ax.set_title("Cantidad de Repuestos por Equipo")
            ax.set_xlabel("Equipo")
            ax.set_ylabel("Cantidad")
            fig.tight_layout()

            img_buffer = BytesIO()
            fig.savefig(img_buffer, format='png')
            img_buffer.seek(0)

            # Clase PDF personalizada
            class PDF(FPDF):
                def header(self):
                    self.set_font("Arial", "B", 12)
                    self.cell(0, 10, "Reporte de Salidas de Repuestos", ln=1, align="C")
                    self.ln(5)

            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)

            # Escribir los datos del reporte
            for row in datos:
                pdf.multi_cell(
                    0, 8,
                    f"{row['fecha']} - {row['repuesto']} ({row['tipo']}) - "
                    f"{row['cantidad']} - {row['maquina'] or 'Sin máquina'}",
                    border=0, align='L'
                )

            # Guardar gráfico temporal y añadirlo al PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                tmp_img.write(img_buffer.getvalue())
                tmp_img.flush()
                pdf.image(tmp_img.name, x=10, w=pdf.w - 20)

            # Generar PDF final
            pdf_output = BytesIO()
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            pdf_output.write(pdf_bytes)
            pdf_output.seek(0)

            return send_file(pdf_output, download_name='reporte_salidas.pdf', as_attachment=True)

    con.close()
    return render_template('reporte_salida.html', datos=datos, total=total_repuestos,
                           equipos_lista=equipos_lista, tipos_lista=tipos_lista,
                           filtros=filtros, etiquetas=etiquetas, valores=valores)

@app.route('/reportes')
def menu_reportes():
    return render_template('menu_reportes.html')

@app.route('/reporte_ingreso', methods=['GET', 'POST'])
def reporte_ingreso():
    con = connect_db()
    cur = con.cursor(dictionary=True)

    # Filtros: solo tipo y fechas (no por equipo)
    cur.execute("SELECT DISTINCT tipo FROM repuestos")
    tipos_lista = [row['tipo'] for row in cur.fetchall()]

    filtros = {
        'tipos': [],
        'fecha_inicio': '',
        'fecha_fin': ''
    }

    datos = []
    total_repuestos = 0
    etiquetas = []
    valores = []

    if request.method == 'POST':
        filtros['tipos'] = request.form.getlist('tipos')
        filtros['fecha_inicio'] = request.form.get('fecha_inicio')
        filtros['fecha_fin'] = request.form.get('fecha_fin')
        exportar = request.form.get('exportar')

        # “Todos”
        if 'todos' in filtros['tipos'] or set(filtros['tipos']) == set(tipos_lista):
            filtros['tipos'] = []

        # Rango de fechas
        fecha_inicio = None
        fecha_fin = None
        try:
            if filtros['fecha_inicio']:
                fecha_inicio = datetime.strptime(filtros['fecha_inicio'], '%Y-%m-%d')
            if filtros['fecha_fin']:
                fecha_fin = datetime.strptime(filtros['fecha_fin'], '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            pass

        # Consulta principal (sin máquina)
        query = """
        SELECT 
            r.nombre AS repuesto,
            r.tipo,
            m.stock AS cantidad,
            m.id AS movimiento,
            m.fecha,
            m.tecnico
        FROM movimientos m
        JOIN repuestos r ON m.repuesto_id = r.id
        WHERE m.tipo_movimiento = 'ingreso'
        """
        params = []

        if filtros['tipos']:
            query += " AND r.tipo IN (%s)" % ','.join(['%s'] * len(filtros['tipos']))
            params.extend(filtros['tipos'])

        if fecha_inicio and fecha_fin:
            query += " AND m.fecha BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        elif fecha_inicio:
            query += " AND m.fecha >= %s"
            params.append(fecha_inicio)
        elif fecha_fin:
            query += " AND m.fecha <= %s"
            params.append(fecha_fin)

        query += " ORDER BY m.fecha DESC"

        cur.execute(query, params)
        datos = cur.fetchall()
        total_repuestos = sum(d['cantidad'] for d in datos)

        # Conteo por técnico (quién hizo el ingreso)
        conteo_por_tecnico = {}
        for d in datos:
            tecnico = d['tecnico'] or 'Sin técnico'
            conteo_por_tecnico[tecnico] = conteo_por_tecnico.get(tecnico, 0) + d['cantidad']

        etiquetas = list(conteo_por_tecnico.keys())
        valores = list(conteo_por_tecnico.values())
               # === Exportar a Excel ===
        if exportar == 'excel':
            df = pd.DataFrame(datos)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Ingresos')
            output.seek(0)
            return send_file(output, download_name='reporte_ingresos.xlsx', as_attachment=True)

        # === Exportar a PDF ===
        elif exportar == 'pdf':
            from fpdf import FPDF
            import base64
            from matplotlib.figure import Figure
            import tempfile

            # Crear gráfico y guardarlo en memoria
            fig = Figure()
            ax = fig.subplots()
            ax.bar(etiquetas, valores, color='mediumseagreen')
            ax.set_title("Cantidad de Repuestos Ingresados por Técnico")
            ax.set_xlabel("Técnico")
            ax.set_ylabel("Cantidad")
            fig.tight_layout()

            img_buffer = BytesIO()
            fig.savefig(img_buffer, format='png')
            img_buffer.seek(0)

            class PDF(FPDF):
                def header(self):
                    self.set_font("Arial", "B", 12)
                    self.cell(0, 10, "Reporte de Ingreso de Repuestos", ln=1, align="C")
                    self.ln(5)

            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)

            for row in datos:
                pdf.multi_cell(
                    0, 8,
                    f"{row['fecha']} - {row['repuesto']} ({row['tipo']}) - "
                    f"{row['cantidad']} - {row['tecnico'] or 'Sin técnico'}",
                    border=0, align='L'
                )

            # Guardar gráfico temporal y agregarlo al PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                tmp_img.write(img_buffer.getvalue())
                tmp_img.flush()
                pdf.image(tmp_img.name, x=10, w=pdf.w - 20)

            # Generar PDF final
            pdf_output = BytesIO()
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            pdf_output.write(pdf_bytes)
            pdf_output.seek(0)

            return send_file(pdf_output, download_name='reporte_ingresos.pdf', as_attachment=True)

    con.close()
    return render_template('reporte_ingreso.html', datos=datos, total=total_repuestos,
                           tipos_lista=tipos_lista, filtros=filtros,
                           etiquetas=etiquetas, valores=valores)

@app.route('/reporte_movimiento', methods=['GET', 'POST'])
def reporte_movimiento():
    con = connect_db()
    cur = con.cursor(dictionary=True)

    # Listas para filtros
    cur.execute("SELECT DISTINCT nombre FROM repuestos")
    repuestos_lista = [row['nombre'] for row in cur.fetchall()]
    cur.execute("SELECT DISTINCT tipo FROM repuestos")
    tipos_lista = [row['tipo'] for row in cur.fetchall()]
    cur.execute("SELECT DISTINCT nombre FROM equipos")
    equipos_lista = [row['nombre'] for row in cur.fetchall()]

    filtros = {
        'repuesto': '',
        'tipos': [],
        'equipos': [],
        'fecha_inicio': '',
        'fecha_fin': ''
    }

    datos = []
    total_ingresos = 0
    total_salidas = 0
    total_stock = 0
    grafico_base64 = None

    if request.method == 'POST':
        filtros['repuesto'] = request.form.get('repuesto', '')
        filtros['tipos'] = request.form.getlist('tipos')
        filtros['equipos'] = request.form.getlist('equipos')
        filtros['fecha_inicio'] = request.form.get('fecha_inicio', '')
        filtros['fecha_fin'] = request.form.get('fecha_fin', '')
        exportar = request.form.get('exportar')

        # Filtros vacíos
        if 'todos' in filtros['tipos'] or set(filtros['tipos']) == set(tipos_lista):
            filtros['tipos'] = []
        if 'todos' in filtros['equipos'] or set(filtros['equipos']) == set(equipos_lista):
            filtros['equipos'] = []

        # Fechas
        fecha_inicio = None
        fecha_fin = None
        try:
            if filtros['fecha_inicio']:
                fecha_inicio = datetime.strptime(filtros['fecha_inicio'], '%Y-%m-%d')
            if filtros['fecha_fin']:
                fecha_fin = datetime.strptime(filtros['fecha_fin'], '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            pass

        # Consulta principal
        query = """
        SELECT
            r.nombre AS repuesto,
            r.tipo,
            m.tipo_movimiento,
            m.stock AS cantidad,
            m.fecha,
            m.maquina
        FROM movimientos m
        JOIN repuestos r ON m.repuesto_id = r.id
        WHERE 1 = 1
        """
        params = []

        if filtros['repuesto']:
            query += " AND r.nombre LIKE %s"
            params.append('%' + filtros['repuesto'] + '%')
        if filtros['tipos']:
            query += " AND r.tipo IN (%s)" % ','.join(['%s'] * len(filtros['tipos']))
            params.extend(filtros['tipos'])
        if filtros['equipos']:
            query += " AND m.maquina IN (%s)" % ','.join(['%s'] * len(filtros['equipos']))
            params.extend(filtros['equipos'])
        if fecha_inicio and fecha_fin:
            query += " AND m.fecha BETWEEN %s AND %s "
            params.extend([fecha_inicio, fecha_fin])
        elif fecha_inicio:
            query += " AND m.fecha >= %s "
            params.append(fecha_inicio)
        elif fecha_fin:
            query += " AND m.fecha <= %s "
            params.append(fecha_fin)

        query += " ORDER BY m.fecha DESC"
        cur.execute(query, params)
        datos = cur.fetchall()

        # Totales
        for d in datos:
            if d['tipo_movimiento'] == 'ingreso':
                total_ingresos += d['cantidad']
            elif d['tipo_movimiento'] == 'salida':
                total_salidas += d['cantidad']

        # ✅ Stock actual desde la tabla repuestos
        stock_query = "SELECT SUM(stock) AS total_stock FROM repuestos WHERE 1=1"
        stock_params = []
        if filtros['repuesto']:
            stock_query += " AND nombre LIKE %s"
            stock_params.append('%' + filtros['repuesto'] + '%')
        if filtros['tipos']:
            stock_query += " AND tipo IN (%s)" % ','.join(['%s'] * len(filtros['tipos']))
            stock_params.extend(filtros['tipos'])
        cur.execute(stock_query, stock_params)
        total_stock = cur.fetchone()['total_stock'] or 0

        # Gráfico
        conteo_por_maquina = {}
        for d in datos:
            maquina = 'Ingresos' if d['tipo_movimiento'] == 'ingreso' else d['maquina'] or 'Sin máquina'
            conteo_por_maquina[maquina] = conteo_por_maquina.get(maquina, 0) + d['cantidad']

        if conteo_por_maquina:
            fig = Figure()
            ax = fig.subplots()
            ax.bar(list(conteo_por_maquina.keys()), list(conteo_por_maquina.values()), color='skyblue')
            ax.set_title("Cantidad de Repuestos por Equipo")
            ax.set_xlabel("Equipo")
            ax.set_ylabel("Cantidad")
            fig.tight_layout()

            img = BytesIO()
            fig.savefig(img, format='png')
            img.seek(0)
            grafico_base64 = base64.b64encode(img.read()).decode('utf-8')

        # Exportar Excel
        if exportar == 'excel':
            df = pd.DataFrame(datos)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Movimientos')
            output.seek(0)
            con.close()
            return send_file(output, download_name='reporte_movimientos.xlsx', as_attachment=True)

        # Exportar PDF
        elif exportar == 'pdf':
            class PDF(FPDF):
                def header(self):
                    self.set_font("Arial", "B", 12)
                    self.cell(0, 10, "Reporte de Movimientos de Repuestos", ln=1, align="C")
                    self.ln(5)

            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)

            for row in datos:
                pdf.cell(0, 8, f"{row['fecha']} - {row['repuesto']} ({row['tipo']}) - {row['tipo_movimiento']} - {row['cantidad']} - {row['maquina']}", ln=1)

            # ✅ Guardar gráfico temporal antes de insertarlo
            if grafico_base64:
                temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                temp_img.write(base64.b64decode(grafico_base64))
                temp_img.close()
                pdf.image(temp_img.name, x=10, w=180)
                os.remove(temp_img.name)

            pdf_output = BytesIO()
            pdf.output(pdf_output)
            pdf_output.seek(0)
            con.close()
            return send_file(pdf_output, download_name='reporte_movimientos.pdf', as_attachment=True)

    con.close()
    return render_template('reporte_movimiento.html',
                           datos=datos,
                           total_stock=total_stock,
                           total_salidas=total_salidas,
                           total_ingresos=total_ingresos,
                           repuestos_lista=repuestos_lista,
                           tipos_lista=tipos_lista,
                           equipos_lista=equipos_lista,
                           filtros=filtros,
                           grafico_base64=grafico_base64)
#--------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)