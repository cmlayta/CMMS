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
        # Asegúrate de que la consulta devuelve el campo 'rol'
        cur.execute("SELECT id, usuario, contrasena, rol FROM usuarios WHERE usuario=%s AND contrasena=%s", (usuario, contrasena))
        user = cur.fetchone()
        con.close()
        
        if user:
            # user[1] es 'usuario', user[3] es 'rol'
            session['usuario'] = user[1] 
            session['rol'] = user[3]
            rol_usuario = user[3] # Asumiendo que el rol está en la posición 3 (índice 3)
            
            # --- Lógica de redirección por rol ---
            if rol_usuario == 'admin':
                return redirect(url_for('inicio')) # Redirige a /inicio (inicio.html)
            elif rol_usuario == 'tecnico':
                # Redirige a la nueva ruta /inicio_tecnico
                return redirect(url_for('inicio_tecnico')) 
            else:
                # Opcional: manejar otros roles si existen, o redirigir a un error
                return "Rol de usuario desconocido", 403
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
    rol = session.get('rol')
    usuario = session.get('usuario')

    # Si no hay sesión activa, redirige al login (aunque before_request ya lo hace)
    if not usuario or not rol:
        return redirect(url_for('login')) 

    # Lógica para diferenciar a dónde enviar al usuario con sesión activa
    if rol == 'admin':
        return render_template('inicio.html', usuario=usuario, rol=rol)
    elif rol == 'tecnico':
        # Nota: La ruta '/' redirigirá al endpoint 'inicio_tecnico'
        return redirect(url_for('inicio_tecnico'))
    else:
        # Manejar roles desconocidos o ir al login por defecto
        return redirect(url_for('login'))

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

    # --- Listas para filtros ---
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
    etiquetas = []
    valores = []
    grafico_base64 = None

    if request.method == 'POST':
        filtros['repuesto'] = request.form.get('repuesto', '')
        filtros['tipos'] = request.form.getlist('tipos')
        filtros['equipos'] = request.form.getlist('equipos')
        filtros['fecha_inicio'] = request.form.get('fecha_inicio', '')
        filtros['fecha_fin'] = request.form.get('fecha_fin', '')
        exportar = request.form.get('exportar')

        fecha_inicio = None
        fecha_fin = None
        try:
            if filtros['fecha_inicio']:
                fecha_inicio = datetime.strptime(filtros['fecha_inicio'], '%Y-%m-%d')
            if filtros['fecha_fin']:
                fecha_fin = datetime.strptime(filtros['fecha_fin'], '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            pass

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

        # Totales
        for d in datos:
            if d['tipo_movimiento'] == 'ingreso':
                total_ingresos += d['cantidad']
            elif d['tipo_movimiento'] == 'salida':
                total_salidas += d['cantidad']

        # ✅ STOCK REAL DESDE TABLA REPUESTOS
        cur_stock = con.cursor(dictionary=True)
        if filtros['repuesto']:
            cur_stock.execute("SELECT stock FROM repuestos WHERE nombre = %s LIMIT 1", (filtros['repuesto'],))
            result = cur_stock.fetchone()
            total_stock = result['stock'] if result else 0
        elif filtros['tipos']:
            cur_stock.execute("SELECT SUM(stock) AS total_stock FROM repuestos WHERE tipo IN (%s)" % ','.join(['%s'] * len(filtros['tipos'])), filtros['tipos'])
            result = cur_stock.fetchone()
            total_stock = result['total_stock'] if result['total_stock'] is not None else 0
        else:
            cur_stock.execute("SELECT SUM(stock) AS total_stock FROM repuestos")
            result = cur_stock.fetchone()
            total_stock = result['total_stock'] if result['total_stock'] is not None else 0
        cur_stock.close()

        # --- Gráfico ---
        conteo_por_maquina = {}
        for d in datos:
            maquina = 'Ingresos' if d['tipo_movimiento'] == 'ingreso' else (d['maquina'] or 'Sin máquina')
            conteo_por_maquina[maquina] = conteo_por_maquina.get(maquina, 0) + d['cantidad']

        etiquetas = list(conteo_por_maquina.keys())
        valores = list(conteo_por_maquina.values())

        if etiquetas and valores:
            fig = Figure()
            ax = fig.subplots()
            ax.bar(etiquetas, valores, color='skyblue')
            ax.set_title("Cantidad de Repuestos por Equipo")
            ax.set_xlabel("Equipo")
            ax.set_ylabel("Cantidad")
            fig.tight_layout()
            img = BytesIO()
            fig.savefig(img, format='png')
            img.seek(0)
            grafico_base64 = base64.b64encode(img.read()).decode('utf-8')

        # --- EXPORTAR ---
        if exportar == 'excel':
            df = pd.DataFrame(datos)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Movimientos')
            output.seek(0)
            con.close()
            return send_file(output, download_name='reporte_movimientos.xlsx', as_attachment=True)

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
                pdf.cell(0, 10, f"{row['fecha']} - {row['repuesto']} ({row['tipo']}) - {row['tipo_movimiento']} - {row['cantidad']} - {row['maquina']}", ln=1)

            # ✅ GUARDAR IMAGEN TEMPORAL PARA PDF
            if grafico_base64:
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                    tmpfile.write(base64.b64decode(grafico_base64))
                    temp_path = tmpfile.name
                pdf.image(temp_path, x=10, w=180)
                os.remove(temp_path)

            # ✅ GUARDAR PDF EN MEMORIA CORRECTAMENTE
            pdf_output = BytesIO()
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            pdf_output.write(pdf_bytes)
            pdf_output.seek(0)

            con.close()
            return send_file(pdf_output, download_name='reporte_movimientos.pdf', as_attachment=True)

    con.close()
    return render_template(
        'reporte_movimiento.html',
        datos=datos,
        total_stock=total_stock,
        total_salidas=total_salidas,
        total_ingresos=total_ingresos,
        repuestos_lista=repuestos_lista,
        tipos_lista=tipos_lista,
        equipos_lista=equipos_lista,
        filtros=filtros,
        grafico_base64=grafico_base64
    )

#----------------------MANTENIMIENTO-------------------------
from datetime import datetime
from flask import request, redirect, url_for, render_template, flash
import mysql.connector  # o el conector que uses

@app.route('/ver_mantenimiento')
def ver_mantenimiento():
    con = connect_db()
    cur = con.cursor(dictionary=True)

    # -------- NOTIFICACIONES PENDIENTES -----------
    cur.execute("SELECT COUNT(*) AS pendientes FROM solicitudes_repuestos WHERE estado = 'pendiente'")
    notif_pendientes = cur.fetchone()['pendientes']

    # -------- OTs abiertas -----------
    query_ot = """
        SELECT 
            ot.id,
            ot.numero_ot,
            ot.fecha_inicio,
            ot.fecha_final,
            ot.duracion_estimada_total,
            ot.estado,
            ot.tipo_mantenimiento,
            ot.tecnico,
            ot.prioridad,
            e.nombre AS equipo_nombre
        FROM ordenes_trabajo ot
        JOIN equipos e ON ot.equipo_id = e.id
        WHERE ot.estado IN ('Pendiente', 'En Proceso')
        ORDER BY ot.numero_ot ASC
    """
    cur.execute(query_ot)
    ordenes = cur.fetchall()

    # Todas actividades
    cur.execute("SELECT * FROM actividades_mantenimiento")
    actividades = cur.fetchall()

    # Agrupar actividades por OT
    actividades_por_ot = {}
    for act in actividades:
        ot_id = act['orden_trabajo_id']
        actividades_por_ot.setdefault(ot_id, []).append(act)

    # Calcular porc. avance
    for ot in ordenes:
        acts = actividades_por_ot.get(ot["id"], [])
        ot["actividades"] = acts

        total = 0
        count = 0

        for act in acts:
            dias_mes = []
            dias_realizados = []

            if act.get('dias_mes'):
                dias_mes = [int(x) for x in str(act['dias_mes']).split(',') if x.strip().isdigit()]

            if act.get('dias_realizados'):
                dias_realizados = [int(x) for x in str(act['dias_realizados']).split(',') if x.strip().isdigit()]

            if len(dias_mes) > 0:
                porcentaje = (len(dias_realizados) / len(dias_mes)) * 100
                total += porcentaje
                count += 1

        ot["porcentaje"] = round(total / count, 1) if count > 0 else 0

    cur.close()
    con.close()

    return render_template(
        'ver_mantenimiento.html',
        ordenes=ordenes,
        notif_pendientes=notif_pendientes  # 👈 SE PASA AL HTML
    )

def actualizar_duracion_total_ot(ot_id):

    con = connect_db()
    cur = con.cursor(dictionary=True)

    # Obtener todas las actividades de esa OT
    cur.execute("""
        SELECT dias_mes, duracion_estimada
        FROM actividades_mantenimiento
        WHERE orden_trabajo_id = %s
    """, (ot_id,))

    actividades = cur.fetchall()

    total = 0

    for act in actividades:

        duracion = act['duracion_estimada'] or 0
        dias_mes = act['dias_mes']

        if dias_mes:
            # Contar cuantos días hay en el campo (1,2,3,5...)
            cantidad_dias = len(dias_mes.split(','))
        else:
            cantidad_dias = 0

        total += duracion * cantidad_dias

    # Actualizar la OT con la nueva suma
    cur.execute("""
        UPDATE ordenes_trabajo
        SET duracion_estimada_total = %s
        WHERE id = %s
    """, (total, ot_id))

    con.commit()
    con.close()

    return total

import pdfkit
from flask import render_template, make_response

from werkzeug.security import generate_password_hash

@app.route('/tecnicos', methods=['GET', 'POST'])
def tecnicos():
    con = connect_db()
    cur = con.cursor(dictionary=True)

    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        cur.execute("""
            INSERT INTO usuarios (usuario, contrasena, rol)
            VALUES (%s, %s, %s)
        """, (usuario, contrasena, 'tecnico'))

        con.commit()

    # obtener solo los tecnicos
    cur.execute("SELECT id, usuario FROM usuarios WHERE rol = 'tecnico'")
    tecnicos = cur.fetchall()

    con.close()

    return render_template('tecnicos.html', tecnicos=tecnicos)

@app.route('/eliminar_tecnico/<int:id>')
def eliminar_tecnico(id):
    con = connect_db()
    cur = con.cursor()

    cur.execute("DELETE FROM usuarios WHERE id = %s AND rol = 'tecnico'", (id,))
    con.commit()

    con.close()

    return redirect('/tecnicos')

# --- generar_numero_ot corregida ---
def generar_numero_ot(year, month):
    con = connect_db()
    cur = con.cursor()
    # Usamos los parámetros year y month
    prefijo = f"OT-{year}-{str(month).zfill(2)}"

    # Buscar la última numero_ot que empiece con el prefijo
    cur.execute("""
        SELECT numero_ot
        FROM ordenes_trabajo
        WHERE numero_ot LIKE %s
        ORDER BY numero_ot DESC
        LIMIT 1
    """, (prefijo + "%",))
    fila = cur.fetchone()
    
    ultimo_num = 0
    if fila and fila[0]:
        try:
            # Extraer el número secuencial (último segmento después del último guion)
            ultimo_num = int(fila[0].split('-')[-1]) 
        except Exception:
            ultimo_num = 0
            
    nuevo = ultimo_num + 1
    con.close()
    # El formato debe ser OT-AAAA-MM-NNN
    return f"{prefijo}-{str(nuevo).zfill(3)}"


# --- Ordenes de Trabajo Adicionales ---
@app.route('/nueva_orden_trabajo')
def nueva_orden_trabajo():
    con = connect_db()
    cur = con.cursor(dictionary=True)

    # equipos
    cur.execute("SELECT id, nombre FROM equipos")
    equipos = cur.fetchall()

    # tecnicos
    cur.execute("SELECT id, usuario FROM usuarios WHERE rol = 'tecnico'")
    tecnicos = cur.fetchall()

    con.close()

    return render_template(
        "nueva_orden_trabajo.html",
        equipos=equipos,
        tecnicos=tecnicos
    )


from datetime import datetime

now = datetime.now()
@app.route('/guardar_orden_trabajo', methods=['POST'])
def guardar_orden_trabajo():

    equipo = request.form['equipo']
    tipo = request.form['tipo_mantenimiento']
    prioridad = request.form['prioridad']
    fecha_inicio = request.form['fecha_inicio']
    fecha_final = request.form['fecha_final']
    tecnico = request.form['tecnico']
    observaciones = request.form['observaciones']

    numero_ot = generar_numero_ot(now.year, now.month)


    con = connect_db()
    cur = con.cursor()

    query = """
        INSERT INTO ordenes_trabajo
        (numero_ot, equipo_id, tipo_mantenimiento,
         fecha_inicio, fecha_final, tecnico,
         prioridad, observaciones, estado)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Pendiente')
    """

    cur.execute(query, (
        numero_ot,
        equipo,
        tipo,
        fecha_inicio,
        fecha_final,
        tecnico,
        prioridad,
        observaciones
    ))

    con.commit()
    con.close()

    return redirect('/ver_mantenimiento')


@app.route('/agregar_actividad/<int:orden_id>', methods=['GET', 'POST'])
def agregar_actividad(orden_id):

    con = connect_db()
    cur = con.cursor(dictionary=True)

    # Obtener info de la OT
    cur.execute("""
        SELECT ot.id, ot.numero_ot, e.nombre AS equipo
        FROM ordenes_trabajo ot
        LEFT JOIN equipos e ON ot.equipo_id = e.id
        WHERE ot.id = %s
    """, (orden_id,))

    orden = cur.fetchone()

    if not orden:
        return "Orden de trabajo no encontrada"

    # Guardar actividad
    if request.method == 'POST':

        codigo = request.form['codigo_actividad']
        descripcion = request.form['descripcion']
        prioridad = request.form['prioridad']
        dias_mes = request.form['dias_mes']   # <-- NUEVO
        duracion = request.form['duracion_estimada']
        tipo = request.form['tipo_trabajo']

        cur.execute("""
            INSERT INTO actividades_mantenimiento
            (orden_trabajo_id, codigo_actividad, descripcion, prioridad, dias_mes, duracion_estimada, tipo_trabajo)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (orden_id, codigo, descripcion, prioridad, dias_mes, duracion, tipo))

        con.commit()

        return redirect(url_for('ver_mantenimiento', orden_id=orden_id))

    return render_template('agregar_actividad.html', orden=orden)

@app.route('/editar_actividad/<int:actividad_id>', methods=['GET', 'POST'])
def editar_actividad(actividad_id):

    con = connect_db()
    cur = con.cursor(dictionary=True)

    cur.execute("SELECT * FROM actividades_mantenimiento WHERE id = %s", (actividad_id,))
    actividad = cur.fetchone()

    if not actividad:
        return "Actividad no encontrada"

    if request.method == 'POST':

        codigo = request.form['codigo_actividad']
        descripcion = request.form['descripcion']
        prioridad = request.form['prioridad']
        dias_mes = request.form['dias_mes']
        duracion = request.form['duracion_estimada']
        tipo = request.form['tipo_trabajo']

        cur.execute("""
            UPDATE actividades_mantenimiento
            SET codigo_actividad = %s,
                descripcion = %s,
                prioridad = %s,
                dias_mes = %s,
                duracion_estimada = %s,
                tipo_trabajo = %s
            WHERE id = %s
        """, (codigo, descripcion, prioridad, dias_mes, duracion, tipo, actividad_id))

        con.commit()

        return redirect(url_for('ver_mantenimiento'))

    return render_template('editar_actividad.html', actividad=actividad)

@app.route('/eliminar_actividad/<int:actividad_id>')
def eliminar_actividad(actividad_id):

    con = connect_db()
    cur = con.cursor()

    cur.execute("DELETE FROM actividades_mantenimiento WHERE id = %s", (actividad_id,))
    con.commit()

    return redirect(url_for('ver_mantenimiento'))

from datetime import date
import calendar
from flask import request, redirect, url_for, render_template, flash


from datetime import date
import calendar
from flask import request, render_template
@app.route('/realizar_ot/<int:ot_id>')
def realizar_ot(ot_id):

    try:
        year = int(request.args.get('year')) if request.args.get('year') else None
        month = int(request.args.get('month')) if request.args.get('month') else None
    except ValueError:
        year = None
        month = None

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    dias_en_mes = calendar.monthrange(year, month)[1]

    con = connect_db()
    cur = con.cursor(dictionary=True)

    # OT
    cur.execute("""
        SELECT ot.id, ot.numero_ot, ot.fecha_inicio, ot.fecha_final,
               ot.tecnico, ot.tipo_mantenimiento, ot.duracion_estimada_total,
               e.nombre AS equipo
        FROM ordenes_trabajo ot
        LEFT JOIN equipos e ON ot.equipo_id = e.id
        WHERE ot.id = %s
    """, (ot_id,))
    ot = cur.fetchone()

    if not ot:
        return "OT no encontrada", 404

    # Actividades
    cur.execute("""
        SELECT *
        FROM actividades_mantenimiento
        WHERE orden_trabajo_id = %s
        ORDER BY id
    """, (ot_id,))
    actividades = cur.fetchall()

    total_porcentaje = 0
    total_actividades = 0

    for a in actividades:

        if a.get('dias_mes'):
            a['dias_mes_list'] = [int(x) for x in str(a['dias_mes']).split(',') if x.strip().isdigit()]
        else:
            a['dias_mes_list'] = []

        if a.get('dias_realizados'):
            a['dias_realizados_list'] = [int(x) for x in str(a['dias_realizados']).split(',') if x.strip().isdigit()]
        else:
            a['dias_realizados_list'] = []

        total = len(a['dias_mes_list'])
        realizados = len(a['dias_realizados_list'])

        porcentaje = (realizados / total) * 100 if total > 0 else 0
        a['completado'] = round(porcentaje, 0)

        total_porcentaje += porcentaje
        total_actividades += 1

    ot_completado = round((total_porcentaje / total_actividades), 0) if total_actividades > 0 else 0

    cur.close()
    con.close()

    return render_template(
        'realizar_ot.html',
        ot=ot,
        actividades=actividades,
        year=year,
        month=month,
        dias_en_mes=dias_en_mes,
        ot_completado=ot_completado
    )


@app.route('/realizar_ot_tecnico/<int:ot_id>')
def realizar_ot_tecnico(ot_id):

    try:
        year = int(request.args.get('year')) if request.args.get('year') else None
        month = int(request.args.get('month')) if request.args.get('month') else None
    except ValueError:
        year = None
        month = None

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    dias_en_mes = calendar.monthrange(year, month)[1]

    con = connect_db()
    cur = con.cursor(dictionary=True)

    # OT
    cur.execute("""
    SELECT ot.id, ot.numero_ot, ot.fecha_inicio, ot.fecha_final,
           ot.tecnico, ot.tipo_mantenimiento, ot.duracion_estimada_total,
           ot.observaciones,
           e.nombre AS equipo
    FROM ordenes_trabajo ot
    LEFT JOIN equipos e ON ot.equipo_id = e.id
    WHERE ot.id = %s
""", (ot_id,))
    ot = cur.fetchone()

    if not ot:
        return "OT no encontrada", 404

    # Actividades
    cur.execute("""
        SELECT *
        FROM actividades_mantenimiento
        WHERE orden_trabajo_id = %s
        ORDER BY id
    """, (ot_id,))
    actividades = cur.fetchall()

    total_porcentaje = 0
    total_actividades = 0

    for a in actividades:

        if a.get('dias_mes'):
            a['dias_mes_list'] = [int(x) for x in str(a['dias_mes']).split(',') if x.strip().isdigit()]
        else:
            a['dias_mes_list'] = []

        if a.get('dias_realizados'):
            a['dias_realizados_list'] = [int(x) for x in str(a['dias_realizados']).split(',') if x.strip().isdigit()]
        else:
            a['dias_realizados_list'] = []

        total = len(a['dias_mes_list'])
        realizados = len(a['dias_realizados_list'])

        porcentaje = (realizados / total) * 100 if total > 0 else 0
        a['completado'] = round(porcentaje, 0)

        total_porcentaje += porcentaje
        total_actividades += 1

    ot_completado = round((total_porcentaje / total_actividades), 0) if total_actividades > 0 else 0

    cur.close()
    con.close()

    return render_template(
        'realizar_ot_tecnico.html',
        ot=ot,
        actividades=actividades,
        year=year,
        month=month,
        dias_en_mes=dias_en_mes,
        ot_completado=ot_completado
    )

@app.route('/guardar_dias_realizados_tecnicos/<int:actividad_id>', methods=['POST'])
def guardar_dias_realizados_tecnicos(actividad_id):
    # obtiene ot_id, year, month para redirigir luego
    ot_id = request.args.get('ot_id')
    year = request.args.get('year')
    month = request.args.get('month')

    # recoger lista de dias seleccionados (valores múltiples)
    dias = request.form.getlist('dias_realizados')  # list of strings
    # filtrar y ordenar numéricamente
    dias_int = sorted({int(x) for x in dias if x.isdigit()})
    dias_csv = ','.join(str(x) for x in dias_int) if dias_int else None

    con = connect_db()
    cur = con.cursor()

    cur.execute("""
        UPDATE actividades_mantenimiento
        SET dias_realizados = %s
        WHERE id = %s
    """, (dias_csv, actividad_id))

    con.commit()
    cur.close()
    con.close()

    # redirigir de regreso a la vista de realizar OT conservando year/month si venían
    if ot_id:
        return redirect(url_for('realizar_ot_tecnico', ot_id=int(ot_id), year=year, month=month))
    else:
        return redirect(url_for('inicio_tecnico'))

from flask import request, redirect, url_for
from datetime import datetime # (Asumiendo que necesitas esto en tu app)
# from .db import connect_db # Importa tu función

# =========================================================================
# NUEVA RUTA: GUARDADO MASIVO (UN SOLO BOTÓN)
# =========================================================================

@app.route('/guardar_todo_tecnico', methods=['POST'])
def guardar_todo_tecnico():
    # 1. Obtener datos de redirección
    ot_id = request.form.get('ot_id')
    year = request.form.get('year')
    month = request.form.get('month')
    
    # SOLUCIÓN CLAVE: Obtener la lista COMPLETA de IDs de actividades a procesar
    actividad_ids_a_procesar = request.form.getlist('actividad_ids_guardar') 
    
    con = None
    cur = None
    
    try:
        con = connect_db()
        cur = con.cursor()
        
        # 4. Iteramos sobre los IDs que *debemos* procesar, incluso si no tienen días marcados.
        for actividad_id_str in actividad_ids_a_procesar:
            try:
                actividad_id = int(actividad_id_str)
            except ValueError:
                continue
                
            # 4.1. Obtener la lista de días marcados (request.form.getlist)
            # Si el usuario desmarcó todos los días, esta lista estará vacía: []
            key_name = f'dias_realizados_{actividad_id}'
            dias = request.form.getlist(key_name)
            
            # 4.2. Limpieza y formateo
            dias_int = sorted({int(x) for x in dias if x.isdigit()})
            
            # Si dias_int está vacío ([]), dias_csv será None. Esto actualizará a NULL en la BD.
            dias_csv = ','.join(str(x) for x in dias_int) if dias_int else None

            # 4.3. Ejecutar la actualización para la actividad específica
            cur.execute("""
                UPDATE actividades_mantenimiento
                SET dias_realizados = %s
                WHERE id = %s
            """, (dias_csv, actividad_id))
            
        # 5. Confirmar todas las transacciones
        con.commit()
        
    except Exception as e:
        if con:
            con.rollback()
        print(f"!!! ERROR FATAL AL GUARDAR EN OT {ot_id} !!! Error: {e}")
        return f"Error al guardar las actividades: {e}", 500 
        
    finally:
        if cur:
            cur.close()
        if con:
            con.close()

    # 6. Redireccionar de regreso
    if ot_id:
        return redirect(url_for('realizar_ot_tecnico', ot_id=int(ot_id), year=year, month=month))
    else:
        return redirect(url_for('inicio_tecnico'))


@app.route('/guardar_dias_realizados/<int:actividad_id>', methods=['POST'])
def guardar_dias_realizados(actividad_id):
    # obtiene ot_id, year, month para redirigir luego
    ot_id = request.args.get('ot_id')
    year = request.args.get('year')
    month = request.args.get('month')

    # recoger lista de dias seleccionados (valores múltiples)
    dias = request.form.getlist('dias_realizados')  # list of strings
    # filtrar y ordenar numéricamente
    dias_int = sorted({int(x) for x in dias if x.isdigit()})
    dias_csv = ','.join(str(x) for x in dias_int) if dias_int else None

    con = connect_db()
    cur = con.cursor()

    cur.execute("""
        UPDATE actividades_mantenimiento
        SET dias_realizados = %s
        WHERE id = %s
    """, (dias_csv, actividad_id))

    con.commit()
    cur.close()
    con.close()

    # redirigir de regreso a la vista de realizar OT conservando year/month si venían
    if ot_id:
        return redirect(url_for('realizar_ot', ot_id=int(ot_id), year=year, month=month))
    else:
        return redirect(url_for('ver_mantenimiento'))


@app.route('/guardar_observaciones_ot/<int:ot_id>', methods=['POST'])
def guardar_observaciones_ot(ot_id):
    observaciones = request.form.get("observaciones", "")

    con = connect_db()
    cur = con.cursor()

    cur.execute("""
        UPDATE ordenes_trabajo
        SET observaciones = %s
        WHERE id = %s
    """, (observaciones, ot_id))

    con.commit()
    cur.close()
    con.close()

    return redirect(url_for('realizar_ot_tecnico', ot_id=ot_id))


from datetime import date, datetime, timedelta
import calendar
from flask import flash, redirect, url_for
from dateutil.relativedelta import relativedelta

# La función generar_numero_ot debe estar definida fuera de aquí o importada
# (No la incluimos aquí para mantener el foco en la función principal).

@app.route('/generar_ots_mensuales', methods=['POST'])
def generar_ots_mensuales():
    print(f"✅ INICIANDO GENERACIÓN DE OTS PARA {date.today().strftime('%Y-%m')}")
    hoy = date.today()
    year = hoy.year
    month = hoy.month

    primer_dia_mes = date(year, month, 1)
    ultimo_dia_mes = date(year, month, calendar.monthrange(year, month)[1])
    total_dias_mes = ultimo_dia_mes.day 

    con = None
    cur = None

    try:
        con = connect_db()
        cur = con.cursor(dictionary=True)

        cur.execute("SELECT * FROM ordenes_trabajo_fijas")
        ots_fijas = cur.fetchall()
        
        ot_generadas_count = 0
        last_ot_number = 0
        prefijo_ot = f"OT-{year}-{str(month).zfill(2)}"


        for ot_fija in ots_fijas:
            
            # 🛑 VERIFICACIÓN CLAVE: Si ya existe una OT generada para este mes a partir de este plan fijo.
            # Buscamos si ya existe una OT con fecha_inicio en este mes y que contenga 
            # actividades asociadas a esta OT fija.
            cur.execute("""
                SELECT 1
                FROM ordenes_trabajo ot
                JOIN actividades_mantenimiento am ON ot.id = am.orden_trabajo_id
                JOIN actividades_ot_fijas aof ON am.plan_id = aof.id
                WHERE aof.ot_fija_id = %s
                AND YEAR(ot.fecha_inicio) = %s 
                AND MONTH(ot.fecha_inicio) = %s 
                LIMIT 1
            """, (ot_fija['id'], year, month))
            
            ot_exists = cur.fetchone()
            
            if ot_exists:
                # Si ya existe, saltamos la generación completa de esta OT fija.
                print(f"⏩ OT Fija ID {ot_fija['id']} ya generada para {year}-{month}. Saltando.")
                continue

            # Si no existe, procedemos a generar las actividades.
            actividades_a_insertar = []
            total_duracion = 0
            
            cur.execute("SELECT * FROM actividades_ot_fijas WHERE ot_fija_id = %s", (ot_fija['id'],))
            actividades_fijas = cur.fetchall()

            for act in actividades_fijas:
                
                freq = (act.get('frecuencia_new') or '').strip()
                should_execute_this_month = True 
                
                # A. Lógica del Historial (Trimestral, Semestral, Anual)
                if freq in ('Trimestral', 'Semestral', 'Anual'):
                    
                    periodo_meses = 0
                    if freq == 'Trimestral': periodo_meses = 3
                    elif freq == 'Semestral': periodo_meses = 6
                    elif freq == 'Anual': periodo_meses = 12
                    
                    # 1. Buscar la última fecha de ejecución
                    cur.execute("""
                        SELECT MAX(ot.fecha_inicio) AS ultima_fecha
                        FROM ordenes_trabajo ot
                        JOIN actividades_mantenimiento am ON ot.id = am.orden_trabajo_id
                        WHERE am.plan_id = %s 
                        LIMIT 1
                    """, (act['id'],)) 
                    
                    ultima_ot_creada = cur.fetchone()
                    
                    if ultima_ot_creada and ultima_ot_creada['ultima_fecha']:
                        # 2a. Lógica con Historial
                        ultima_fecha = ultima_ot_creada['ultima_fecha']
                        proxima_fecha_ejecucion_base = ultima_fecha + relativedelta(months=+periodo_meses)

                        while proxima_fecha_ejecucion_base.year < year or \
                              (proxima_fecha_ejecucion_base.year == year and proxima_fecha_ejecucion_base.month < month):
                            proxima_fecha_ejecucion_base += relativedelta(months=+periodo_meses)
                        
                        if proxima_fecha_ejecucion_base.year != year or proxima_fecha_ejecucion_base.month != month:
                            should_execute_this_month = False 
                            
                    else:
                        # 2b. Lógica SIN Historial (Primera Generación)
                        act_mes_config_raw = act.get('mes')
                        act_mes_config = 0
                        try:
                             if act_mes_config_raw:
                                 act_mes_config = int(act_mes_config_raw)
                        except ValueError:
                             print(f"Advertencia: El campo 'mes' de {act.get('codigo_actividad')} no es un número válido.")

                        if act_mes_config != 0 and act_mes_config != month:
                            should_execute_this_month = False 
                            
                
                if not should_execute_this_month:
                    continue 


                # B. Calcular dias_mes para la actividad (Lógica estable)
                dias = []
                
                # Diaria
                if freq == 'Diaria':
                    for d in range(1, total_dias_mes + 1):
                        if date(year, month, d).weekday() != 6:
                            dias.append(d)

                # Semanal
                elif freq == 'Semanal':
                    ds = act.get('dia_semana')
                    try:
                        if ds is not None and str(ds).strip() and 1 <= int(ds) <= 7:
                            target_wd = int(ds) - 1
                            for d in range(1, total_dias_mes + 1):
                                if date(year, month, d).weekday() == target_wd:
                                    dias.append(d)
                    except (TypeError, ValueError):
                         print(f"Advertencia: dia_semana de {act.get('codigo_actividad')} no es válido o está vacío.")

                # Quincenal
                elif freq == 'Quincenal':
                    ds_val = act.get('dia_semana')
                    sm_val = act.get('semana_mes') 
                    
                    try:
                        if ds_val and sm_val and int(sm_val) == 1:
                            target_wd = int(ds_val) - 1 
                            occurrence_count = 0
                            for d in range(1, total_dias_mes + 1):
                                current_date = date(year, month, d)
                                if current_date.weekday() == target_wd:
                                    occurrence_count += 1
                                    if occurrence_count == 1: 
                                        dias.append(d)
                                        second_occurrence_date = current_date + timedelta(weeks=2)
                                        if second_occurrence_date.month == month: 
                                            dias.append(second_occurrence_date.day)
                                        break
                    except (TypeError, ValueError):
                        print(f"Advertencia: Datos de Quincenal de {act.get('codigo_actividad')} no son válidos.")

                # Mensual, Trimestral, Semestral, Anual (N-ésimo día de la semana del mes)
                elif freq in ('Mensual', 'Trimestral', 'Semestral', 'Anual'):
                    
                    ds_val = act.get('dia_semana') 
                    sm_val = act.get('semana_mes') 

                    try:
                        if ds_val and sm_val and str(ds_val).strip() and str(sm_val).strip():
                            target_wd = int(ds_val) - 1 
                            target_week_of_month = int(sm_val)

                            occurrence_count = 0
                            for d in range(1, total_dias_mes + 1):
                                current_date = date(year, month, d)
                                if current_date.weekday() == target_wd:
                                    occurrence_count += 1
                                    if occurrence_count == target_week_of_month:
                                        dias.append(d)
                                        break 
                    except (TypeError, ValueError):
                        print(f"Advertencia: Datos de {freq} de {act.get('codigo_actividad')} no son válidos.")
                
                
                # Personalizada
                elif freq == 'Personalizada':
                    fp = act.get('fecha_personalizada')
                    if fp:
                        if isinstance(fp, (str,)):
                            try:
                                fp_date = datetime.strptime(fp.split()[0], '%Y-%m-%d').date()
                            except Exception:
                                fp_date = None
                        else:
                            fp_date = fp.date() if isinstance(fp, datetime) else fp
                            
                        if fp_date and fp_date.year == year and fp_date.month == month:
                            dias.append(fp_date.day)
                
                # C. Acumular actividad para inserción
                if dias:
                    dias_csv = ",".join(str(x) for x in sorted(set(dias)))
                    duracion_act = act.get('duracion') or 0
                    total_duracion += duracion_act
                    
                    actividades_a_insertar.append({
                        'plan_id': act['id'], 
                        'codigo_actividad': act.get('codigo_actividad'),
                        'descripcion': act.get('actividad') or act.get('observaciones') or '',
                        'prioridad': act.get('prioridad'),
                        'dias_mes': dias_csv,
                        'duracion_estimada': duracion_act,
                        'tipo_trabajo': 'Preventivo'
                    })
            
            
            # 2. Insertar OT si se generó al menos una actividad
            if actividades_a_insertar:
                ot_generadas_count += 1
                
                # 🚨 AJUSTE DE CÓDIGO OT: Usa el contador interno para la secuencia
                if last_ot_number == 0:
                     # Consultamos el número máximo secuencial para el prefijo del mes
                     cur.execute("""
                        SELECT MAX(CAST(SUBSTRING_INDEX(numero_ot, '-', -1) AS UNSIGNED)) AS ultimo_num
                        FROM ordenes_trabajo
                        WHERE numero_ot LIKE %s
                    """, (prefijo_ot + "%",))
                     
                     fila = cur.fetchone()
                     if fila and fila['ultimo_num'] is not None:
                         last_ot_number = int(fila['ultimo_num'])

                # Incrementar el contador local y generar el nuevo número
                last_ot_number += 1
                nuevo_numero_ot = f"{prefijo_ot}-{str(last_ot_number).zfill(3)}"
                
                prioridades = [a['prioridad'] for a in actividades_a_insertar]
                priority_order = {'Crítica': 4, 'Alta': 3, 'Media': 2, 'Baja': 1}
                max_priority = max(prioridades, key=lambda p: priority_order.get(p, 0))
                
                cur.execute("""
                    INSERT INTO ordenes_trabajo
                    (numero_ot, duracion_estimada_total, fecha_inicio, fecha_final, estado,
                     equipo_id, tipo_mantenimiento, tecnico, observaciones, prioridad)
                    VALUES (%s, %s, %s, %s, 'Pendiente', %s, %s, %s, %s, %s)
                """, (
                    nuevo_numero_ot, 
                    total_duracion, 
                    primer_dia_mes, 
                    ultimo_dia_mes,
                    ot_fija['equipo_id'], 
                    ot_fija['tipo_mantenimiento'], 
                    ot_fija['tecnico'],
                    ot_fija.get('observaciones'), 
                    max_priority
                ))
                ot_id = cur.lastrowid
                
                for new_act in actividades_a_insertar:
                    cur.execute("""
                        INSERT INTO actividades_mantenimiento
                        (orden_trabajo_id, plan_id, codigo_actividad, descripcion, prioridad,
                         dias_mes, dias_realizados, duracion_estimada, tipo_trabajo)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        ot_id, 
                        new_act['plan_id'], 
                        new_act['codigo_actividad'], 
                        new_act['descripcion'],
                        new_act['prioridad'], 
                        new_act['dias_mes'], 
                        None, 
                        new_act['duracion_estimada'],
                        new_act['tipo_trabajo']
                    ))

        con.commit()
        flash(f"✅ Se generaron {ot_generadas_count} Órdenes de Trabajo para {calendar.month_name[month]} de {year}.", "success")

    except Exception as e:
        if con:
            con.rollback()
        print(f"❌ ERROR CRÍTICO DURANTE LA GENERACIÓN DE OTS: {e}")
        flash(f"❌ Error al generar OTs. Detalle: {e}", "danger")
    finally:
        if cur:
            cur.close()
        if con:
            con.close()

    return redirect(url_for('ver_planes_mantenimiento'))

# Asegúrate de importar los módulos necesarios
from flask import redirect, url_for, current_app 

# Asumo que esta función existe en otro módulo y maneja la conexión
# def connect_db(): 
#    ...

@app.route('/finalizar_ot/<int:ot_id>')
def finalizar_ot(ot_id):
    """
    Cambia el estado de una Orden de Trabajo (OT) a 'Finalizada' SIN modificar la fecha final.
    """
    con = connect_db()
    cur = con.cursor()

    try:
        # 1. Ejecutar la actualización en la tabla ordenes_trabajo
        # SOLO se actualiza la columna 'estado' a 'Finalizada'.
        sql_update = """
        UPDATE ordenes_trabajo
        SET estado = %s
        WHERE id = %s
        """
        
        # El orden de los parámetros es crucial: ('Finalizada', ot_id)
        cur.execute(sql_update, ('Finalizada', ot_id))
        
        # 2. Confirmar los cambios en la base de datos
        con.commit()

        # 3. Redireccionar al usuario después de la acción.
        return redirect(url_for('ver_mantenimiento', id=ot_id)) 
        
    except Exception as e:
        # Manejo de cualquier error que pueda ocurrir durante la transacción
        print(f"Error al finalizar la OT {ot_id}: {e}")
        con.rollback() # Deshacer cualquier cambio parcial
        return f"Error al cerrar la OT: {e}", 500
        
    finally:
        # 4. Asegurar el cierre de la conexión
        con.close()


# Suponiendo que tu función de ruta se ve así:

# Asegúrate de que tienes importado mysql.connector y Flask
# import mysql.connector
# from flask import Flask, render_template

@app.route('/historial_mantenimiento')
def historial_mantenimiento():
    # Establecer la conexión a la base de datos
    try:
        con = connect_db() # Usar tu función de conexión
        cur = con.cursor(dictionary=True)
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return "Error de conexión a la base de datos", 500

    try:
        # 1. Consulta SQL (SIN 'ot.porcentaje' - evita el error 1054)
        cur.execute("""
            SELECT ot.id, ot.numero_ot, ot.fecha_inicio, ot.fecha_final, ot.tecnico,
                   ot.tipo_mantenimiento, ot.duracion_estimada_total, ot.estado,
                   ot.prioridad, e.nombre AS equipo_nombre
            FROM ordenes_trabajo ot
            LEFT JOIN equipos e ON ot.equipo_id = e.id
            WHERE ot.estado = 'Finalizada'
            ORDER BY ot.fecha_final DESC
        """)
        ordenes = cur.fetchall()

        equipos = set()
        tecnicos = set()
        
        # 2. Iterar, calcular el porcentaje y cargar actividades
        for ot in ordenes:
            # Recuperar actividades de la OT (necesario para el botón "Ver" en el HTML)
            cur.execute("""
                SELECT dias_mes, dias_realizados, codigo_actividad, descripcion, prioridad, 
                       duracion_estimada, tipo_trabajo, id
                FROM actividades_mantenimiento 
                WHERE orden_trabajo_id = %s
                ORDER BY id
            """, (ot['id'],))
            
            actividades = cur.fetchall()
            ot['actividades'] = actividades
            
            total_porcentaje = 0
            total_actividades_validas = 0

            for a in actividades:
                try:
                    # Lógica de cálculo de avance
                    dias_mes_list = [x.strip() for x in str(a.get('dias_mes', '')).split(',') if x.strip()]
                    dias_realizados_list = [x.strip() for x in str(a.get('dias_realizados', '')).split(',') if x.strip()]
                    
                    total = len(dias_mes_list)
                    realizados = len(dias_realizados_list)

                    if total > 0:
                        porcentaje = (realizados / total) * 100
                        total_actividades_validas += 1
                    else:
                        porcentaje = 100 
                        total_actividades_validas += 1
                        
                    total_porcentaje += porcentaje
                except Exception as e:
                    print(f"Error al calcular porcentaje de actividad {a.get('id')}: {e}")
                    continue
            
            # Calcular el porcentaje de avance de la OT completa
            if total_actividades_validas > 0:
                ot_completado = round((total_porcentaje / total_actividades_validas), 0)
            else:
                ot_completado = 100 
                
            ot['porcentaje'] = int(ot_completado) # Añadir el campo 'porcentaje'

            # 3. Recolectar datos únicos para los filtros HTML
            if ot.get('equipo_nombre'):
                equipos.add(ot['equipo_nombre'])
            if ot.get('tecnico'):
                tecnico_nombre = ot['tecnico'] if ot['tecnico'] and ot['tecnico'].strip() else 'N/A'
                tecnicos.add(tecnico_nombre)

        # Convertir sets a listas ordenadas
        equipos_unicos = sorted(list(equipos))
        tecnicos_unicos = sorted(list(tecnicos))
        
        # 4. Renderizar la plantilla
        return render_template(
            'historial_mantenimiento.html',
            ordenes=ordenes,
            equipos_unicos=equipos_unicos,
            tecnicos_unicos=tecnicos_unicos
        )

    except mysql.connector.Error as err:
        print(f"Error durante la consulta SQL o procesamiento: {err}")
        return "Error al cargar el historial de mantenimiento", 500
        
    finally:
        # Cerrar la conexión
        if 'con' in locals() and con.is_connected():
            con.close()


# Importaciones necesarias (asegúrate de que ya las tienes en la parte superior)
# from flask import render_template
# from .db import connect_db 
# from datetime import date




# ... (tus otras rutas)


@app.route('/ver_actividad/<int:ot_id>')
def ver_actividad(ot_id):

    try:
        year = int(request.args.get('year')) if request.args.get('year') else None
        month = int(request.args.get('month')) if request.args.get('month') else None
    except ValueError:
        year = None
        month = None

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    dias_en_mes = calendar.monthrange(year, month)[1]

    con = connect_db()
    cur = con.cursor(dictionary=True)

    # OT
    cur.execute("""
        SELECT ot.id, ot.numero_ot, ot.fecha_inicio, ot.fecha_final,
               ot.tecnico, ot.tipo_mantenimiento, ot.duracion_estimada_total, ot.observaciones,
               e.nombre AS equipo
        FROM ordenes_trabajo ot
        LEFT JOIN equipos e ON ot.equipo_id = e.id
        WHERE ot.id = %s
    """, (ot_id,))
    ot = cur.fetchone()

    if not ot:
        return "OT no encontrada", 404

    # Actividades
    cur.execute("""
        SELECT *
        FROM actividades_mantenimiento
        WHERE orden_trabajo_id = %s
        ORDER BY id
    """, (ot_id,))
    actividades = cur.fetchall()

    total_porcentaje = 0
    total_actividades = 0

    for a in actividades:

        if a.get('dias_mes'):
            a['dias_mes_list'] = [int(x) for x in str(a['dias_mes']).split(',') if x.strip().isdigit()]
        else:
            a['dias_mes_list'] = []

        if a.get('dias_realizados'):
            a['dias_realizados_list'] = [int(x) for x in str(a['dias_realizados']).split(',') if x.strip().isdigit()]
        else:
            a['dias_realizados_list'] = []

        total = len(a['dias_mes_list'])
        realizados = len(a['dias_realizados_list'])

        porcentaje = (realizados / total) * 100 if total > 0 else 0
        a['completado'] = round(porcentaje, 0)

        total_porcentaje += porcentaje
        total_actividades += 1

    ot_completado = round((total_porcentaje / total_actividades), 0) if total_actividades > 0 else 0

    cur.close()
    con.close()

    return render_template(
        'ver_actividad.html',
        ot=ot,
        actividades=actividades,
        year=year,
        month=month,
        dias_en_mes=dias_en_mes,
        ot_completado=ot_completado
    )

# --- Menu de Planifiacion ---

@app.route('/ver_planes_mantenimiento')
def ver_planes_mantenimiento():

    con = connect_db()
    cur = con.cursor(dictionary=True)

    # ✅ SOLO OT FIJAS
    cur.execute("""
        SELECT 
            o.id,
            o.numero_ot,
            e.nombre AS equipo,
            o.tipo_mantenimiento,
            o.tecnico,
            o.descripcion,
            o.observaciones,
            o.fecha_creacion
        FROM ordenes_trabajo_fijas o
        INNER JOIN equipos e ON o.equipo_id = e.id
        ORDER BY o.id DESC
    """)

    ots = cur.fetchall()

    con.close()

    return render_template('planes_mantenimiento.html', ots=ots)

@app.route('/nueva_ot_fija')
def nueva_ot_fija():
    con = connect_db()
    cur = con.cursor(dictionary=True)

    cur.execute("SELECT id, nombre FROM equipos")
    equipos = cur.fetchall()

    cur.execute("SELECT usuario FROM usuarios WHERE rol = 'tecnico'")
    tecnicos = cur.fetchall()

    con.close()

    return render_template('nueva_ot_fija.html', equipos=equipos, tecnicos=tecnicos)

@app.route('/guardar_ot_fija', methods=['POST'])
def guardar_ot_fija():
    equipo = request.form['equipo']
    tipo = request.form['tipo_mantenimiento']
    descripcion = request.form['descripcion']
    tecnico = request.form['tecnico']
    observaciones = request.form.get('observaciones')

    con = connect_db()
    cur = con.cursor()

    try:
        # 1) Intentar cuando numero_ot es NUMÉRICO (varchar pero contiene solo dígitos)
        cur.execute("SELECT COUNT(*) FROM ordenes_trabajo_fijas WHERE numero_ot REGEXP '^[0-9]+$'")
        cnt_numeric = cur.fetchone()[0]

        if cnt_numeric > 0:
            cur.execute("SELECT COALESCE(MAX(CAST(numero_ot AS UNSIGNED)), 0) + 1 AS next_num FROM ordenes_trabajo_fijas")
            numero_ot = cur.fetchone()[0]

        else:
            # 2) Intentar extraer sufijo numérico tras el último '-' (ej OT-2025-11-003 -> 003)
            #    y calcular MAX(...) + 1 sobre esa porción.
            cur.execute("""
                SELECT COALESCE(MAX(CAST(SUBSTRING_INDEX(numero_ot, '-', -1) AS UNSIGNED)), 0) + 1 AS next_num
                FROM ordenes_trabajo_fijas
                WHERE numero_ot LIKE '%-%' AND SUBSTRING_INDEX(numero_ot, '-', -1) REGEXP '^[0-9]+$'
            """)
            row = cur.fetchone()
            if row and row[0]:
                numero_ot = row[0]
            else:
                # 3) Fallback: usar id auto_increment. Para eso primero insertamos sin numero_ot,
                #    luego actualizamos numero_ot usando el id obtenido.
                numero_ot = None

        # Si numero_ot pudo calcularse, insertar directamente
        if numero_ot is not None:
            query = """
            INSERT INTO ordenes_trabajo_fijas
            (numero_ot, equipo_id, tipo_mantenimiento, descripcion, tecnico, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            valores = (str(numero_ot), equipo, tipo, descripcion, tecnico, observaciones)
            cur.execute(query, valores)
            con.commit()

        else:
            # Fallback: insertar primero sin numero_ot y luego actualizar con el id (o formato que quieras)
            query = """
            INSERT INTO ordenes_trabajo_fijas
            (equipo_id, tipo_mantenimiento, descripcion, tecnico, observaciones)
            VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(query, (equipo, tipo, descripcion, tecnico, observaciones))
            ot_id = cur.lastrowid

            # Decide cómo quieres el número correlativo final. Ejemplo simple: usar el id.
            numero_ot_generado = str(ot_id)             # -> "1", "2", ...
            # Si prefieres con prefijo, por ejemplo "OT-0001":
            # numero_ot_generado = f"OT-{ot_id:04d}"

            cur.execute("UPDATE ordenes_trabajo_fijas SET numero_ot = %s WHERE id = %s",
                        (numero_ot_generado, ot_id))
            con.commit()

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        flash(f"Error guardando OT fija: {e}", "danger")
        return redirect(url_for('ver_planes_mantenimiento'))

    cur.close()
    con.close()
    return redirect(url_for('ver_planes_mantenimiento'))

@app.route('/editar_ot_fija/<int:ot_id>', methods=['GET', 'POST'])
def editar_ot_fija(ot_id):

    con = connect_db()
    cur = con.cursor(dictionary=True)

    # Obtener la OT fija
    cur.execute("""
        SELECT * FROM ordenes_trabajo_fijas
        WHERE id = %s
    """, (ot_id,))
    ot = cur.fetchone()

    if not ot:
        flash("OT fija no encontrada", "danger")
        return redirect(url_for('ver_planes_mantenimiento'))

    # Obtener listas para selects
    cur.execute("SELECT id, nombre FROM equipos")
    equipos = cur.fetchall()

    cur.execute("SELECT usuario FROM usuarios")
    tecnicos = cur.fetchall()

    if request.method == 'POST':
        equipo = request.form.get('equipo')
        tipo_mantenimiento = request.form.get('tipo_mantenimiento')
        prioridad = request.form.get('descripcion')
        tecnico = request.form.get('tecnico')
        observaciones = request.form.get('observaciones')

        try:
            cur.execute("""
                UPDATE ordenes_trabajo_fijas SET
                    equipo_id = %s,
                    tipo_mantenimiento = %s,
                    descripcion = %s,
                    tecnico = %s,
                    observaciones = %s
                WHERE id = %s
            """, (
                equipo,
                tipo_mantenimiento,
                prioridad,
                tecnico,
                observaciones,
                ot_id
            ))

            con.commit()
            flash("OT fija actualizada correctamente", "success")
            return redirect(url_for('ver_planes_mantenimiento'))

        except Exception as e:
            con.rollback()
            flash(f"Error al actualizar: {str(e)}", "danger")

    cur.close()
    con.close()

    return render_template(
        "editar_ot_fija.html",
        ot=ot,
        equipos=equipos,
        tecnicos=tecnicos
    )

@app.route('/eliminar_ot_fija/<int:ot_id>', methods=['POST'])
def eliminar_ot_fija(ot_id):
    con = connect_db()
    cur = con.cursor()

    try:
        # 1. Eliminar actividades relacionadas a la OT fija
        cur.execute("""
            DELETE FROM actividades_ot_fijas
            WHERE ot_fija_id = %s
        """, (ot_id,))

        # 2. Eliminar la OT fija
        cur.execute("""
            DELETE FROM ordenes_trabajo_fijas
            WHERE id = %s
        """, (ot_id,))

        con.commit()
        flash("OT fija y sus actividades fueron eliminadas correctamente.", "success")

    except Exception as e:
        con.rollback()
        flash(f"Error al eliminar OT fija: {str(e)}", "danger")

    finally:
        cur.close()
        con.close()

    return redirect(url_for('ver_planes_mantenimiento'))

@app.route('/ver_plan/<int:ot_id>')
def ver_plan(ot_id):

    con = connect_db()
    cur = con.cursor(dictionary=True)

    # Traer la OT fija
    cur.execute("""
        SELECT 
            o.id,
            o.numero_ot,
            o.equipo_id,
            e.nombre AS equipo,
            o.tecnico,
            o.descripcion,
            o.tipo_mantenimiento,
            o.observaciones,
            o.fecha_creacion
        FROM ordenes_trabajo_fijas o
        INNER JOIN equipos e ON o.equipo_id = e.id
        WHERE o.id = %s
    """, (ot_id,))

    ot = cur.fetchone()

    if not ot:
        con.close()
        return "OT fija no encontrada", 404

    # Actividades con todos los campos nuevos
    cur.execute("""
        SELECT
            id,
            codigo_actividad,
            actividad,
            prioridad,
            frecuencia_new,
            dia_semana,
            semana_mes,
            dia_mes,
            mes,
            fecha_personalizada,
            duracion,
            observaciones
        FROM actividades_ot_fijas
        WHERE ot_fija_id = %s
        ORDER BY id DESC
    """, (ot_id,))

    actividades = cur.fetchall()

    cur.close()
    con.close()

    return render_template(
        'ver_plan.html',
        ot=ot,
        actividades=actividades
    )

@app.route('/actividad_fija/nueva/<int:ot_id>', methods=['GET', 'POST'])
def nueva_actividad_fija(ot_id):

    con = connect_db()
    cur = con.cursor(dictionary=True)

    if request.method == 'POST':

        codigo = request.form.get('codigo')
        actividad = request.form.get('actividad')
        prioridad = request.form.get('prioridad')
        frecuencia = request.form.get('frecuencia')
        duracion = request.form.get('duracion') or None
        observaciones = request.form.get('observaciones')

        dia_semana = request.form.get('dia_semana') or None
        semana_mes = request.form.get('semana_mes') or None
        dia_mes = request.form.get('dia_mes') or None
        mes = request.form.get('mes') or None

        # ✅ NUEVO
        fecha_personalizada = request.form.get('fecha_personalizada') or None

        query = """
            INSERT INTO actividades_ot_fijas
            (ot_fija_id, codigo_actividad, prioridad, frecuencia_new,
             dia_semana, semana_mes, dia_mes, mes, fecha_personalizada,
             actividad, duracion, observaciones)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        valores = (
            ot_id,
            codigo,
            prioridad,
            frecuencia,
            dia_semana,
            semana_mes,
            dia_mes,
            mes,
            fecha_personalizada,   # ✅ NUEVO
            actividad,
            duracion,
            observaciones
        )

        cur.execute(query, valores)
        con.commit()

        cur.close()
        con.close()

        return redirect(url_for('ver_plan', ot_id=ot_id))


    cur.execute(
        "SELECT numero_ot, descripcion FROM ordenes_trabajo_fijas WHERE id = %s",
        (ot_id,)
    )

    ot = cur.fetchone()

    cur.close()
    con.close()

    return render_template('nueva_actividad_fija.html', ot=ot, ot_id=ot_id)

@app.route('/editar_actividad_ot_fija/<int:actividad_id>', methods=['GET', 'POST'])
def editar_actividad_ot_fija(actividad_id):
    con = connect_db()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        SELECT a.*, o.numero_ot, o.descripcion, o.id AS ot_id
        FROM actividades_ot_fijas a
        JOIN ordenes_trabajo_fijas o ON a.ot_fija_id = o.id
        WHERE a.id = %s
    """, (actividad_id,))
    actividad = cur.fetchone()

    if not actividad:
        flash("Actividad no encontrada", "error")
        cur.close()
        con.close()
        return redirect(url_for('ver_planes_mantenimiento'))

    if request.method == 'POST':
        codigo = request.form.get('codigo') or None
        actividad_txt = request.form.get('actividad') or None
        duracion = request.form.get('duracion')
        duracion = int(duracion) if duracion else None
        prioridad = request.form.get('prioridad') or None
        frecuencia = request.form.get('frecuencia') or None
        dia_semana = request.form.get('dia_semana') or None
        semana_mes = request.form.get('semana_mes') or None
        mes = request.form.get('mes') or None
        fecha_personalizada = request.form.get('fecha_personalizada') or None
        observaciones = request.form.get('observaciones') or None

        cur.execute("""
            UPDATE actividades_ot_fijas SET
                codigo_actividad = %s,
                actividad = %s,
                duracion = %s,
                prioridad = %s,
                frecuencia_new = %s,
                dia_semana = %s,
                semana_mes = %s,
                mes = %s,
                fecha_personalizada = %s,
                observaciones = %s
            WHERE id = %s
        """, (
            codigo,
            actividad_txt,
            duracion,
            prioridad,
            frecuencia,
            dia_semana,
            semana_mes,
            mes,
            fecha_personalizada,
            observaciones,
            actividad_id
        ))

        con.commit()
        cur.close()
        con.close()
        flash("Actividad actualizada correctamente", "success")
        return redirect(url_for('ver_plan', ot_id=actividad['ot_id']))

    # GET: renderizar formulario con datos actuales
    cur.close()
    con.close()
    return render_template('editar_actividad_fija.html', actividad=actividad, ot={
        "numero_ot": actividad['numero_ot'],
        "descripcion": actividad['descripcion']
    }, ot_id=actividad['ot_id'])

@app.route('/actividad_fija/eliminar/<int:actividad_id>/<int:ot_id>', methods=['POST'])
def eliminar_actividad_fija(actividad_id, ot_id):

    con = connect_db()
    cur = con.cursor()

    # Eliminar actividad
    cur.execute(
        "DELETE FROM actividades_ot_fijas WHERE id = %s",
        (actividad_id,)
    )

    con.commit()

    cur.close()
    con.close()

    return redirect(url_for('ver_plan', ot_id=ot_id))

#--------------Generacion Automatica de OTS------------

from datetime import date, datetime
import calendar
from flask import flash, redirect, url_for
from dateutil.relativedelta import relativedelta # Necesitas instalar python-dateutil: pip install python-dateutil


def calcular_proximo_mes_ejecucion(frecuencia, mes_actual, anio_actual, ultima_fecha_creacion_ot_fija, conn):
    """
    Calcula el mes en que la actividad DEBERÍA ejecutarse, basándose en la última
    fecha de creación de una OT Fija.
    
    Para frecuencias como Trimestral, Semestral y Anual, la lógica debe ser:
    1. Encontrar la última fecha de creación en ordenes_trabajo para esta OT Fija.
    2. Sumar el periodo correspondiente (3, 6 o 12 meses) a esa fecha.
    3. Si ese nuevo mes es el mes actual, se ejecuta.
    """
    periodo_meses = 0
    if frecuencia == 'Trimestral':
        periodo_meses = 3
    elif frecuencia == 'Semestral':
        periodo_meses = 6
    elif frecuencia == 'Anual':
        periodo_meses = 12
    else:
        # Frecuencias Diaria, Semanal, Quincenal, Mensual, Personalizada siempre se generan aquí
        return True # Se ejecuta

    # Consultar la fecha de la última OT generada a partir de esta OT fija
    cur = conn.cursor()
    # Buscamos la OT más reciente que contenga una actividad con el plan_id de esta OT Fija
    # Asumimos que la OT fija se identifica por su ot_fija_id (que es act['id'] en el bucle)
    # y que 'plan_id' en actividades_mantenimiento es la referencia a 'actividades_ot_fijas.id'
    
    # ⚠️ Nota: Para esta lógica, necesitamos el ID de la OT fija actual (ot_fija['id']), 
    # no el ID de la actividad fija (act['id']). Usaremos 'ot_fija_id' para buscar.

    # En el bucle principal usaremos `ot_fija['id']` para esta consulta.
    return periodo_meses


from datetime import date, datetime
import calendar
from flask import flash, redirect, url_for
from dateutil.relativedelta import relativedelta

# La función principal de generación
from datetime import date, datetime, timedelta
import calendar
from flask import flash, redirect, url_for
from dateutil.relativedelta import relativedelta
# Asegúrate de que 'app' y 'connect_db' estén definidas/importadas en tu entorno.
# Función auxiliar para generar un número de OT secuencial y único
def generar_numero_ot(year, month):
    con = connect_db()
    # Usamos cur.cursor() sin diccionario para un fetchone simple
    cur = con.cursor() 
    
    # Construir el prefijo (ej: OT-2025-11)
    prefijo = f"OT-{year}-{str(month).zfill(2)}"

    try:
        # Iniciar la transacción y BLOQUEAR la lectura del último número.
        # Esto previene que otro proceso o hilo lea el mismo valor antes de que se haga commit.
        con.start_transaction()
        
        # Buscar el último numero_ot que empiece con el prefijo y BLOQUEAR la fila
        cur.execute("""
            SELECT numero_ot
            FROM ordenes_trabajo
            WHERE numero_ot LIKE %s
            ORDER BY numero_ot DESC
            LIMIT 1
            FOR UPDATE
        """, (prefijo + "%",))
        
        fila = cur.fetchone()
        
        ultimo_num = 0
        if fila and fila[0]:
            try:
                # Extraer el número secuencial
                ultimo_num = int(fila[0].split('-')[-1]) 
            except Exception:
                ultimo_num = 0
                
        nuevo = ultimo_num + 1
        nuevo_numero_ot = f"{prefijo}-{str(nuevo).zfill(3)}"
        
        # ⚠️ IMPORTANTE: El commit para liberar el bloqueo se hará en la función principal
        # después de que la inserción de la OT haya ocurrido. Aquí solo se hace rollback
        # si hay error, y se cierra la conexión para que la función principal maneje el commit.
        
    except Exception as e:
        con.rollback()
        raise e
    finally:
        cur.close()
        con.close() # Cierra la conexión, la función principal debe reconectar

    return nuevo_numero_ot

# Nota: En tu implementación real de Flask/MySQL, si usas una conexión
# única en la función principal, este patrón debe ajustarse para que el
# bloqueo FOR UPDATE y el INSERT de la OT estén en la misma transacción,
# terminando con un único con.commit() en la función principal.
# ---------------------------------------------------------------------
# Ya que la función principal tiene su propio con.commit(), solo necesitas
# asegurarte de que esta función NO haga commit aquí. La he ajustado para
# que maneje el error y retorne. Si usas 'FOR UPDATE', DEBES estar
# dentro de una transacción. Si conectas y cierras aquí, cada llamada es
# su propia transacción.
# ---------------------------------------------------------------------

# Ya que tu función principal maneja el commit, vamos a asegurar la conexión
# y solo retornar el número.
def generar_numero_ot(year, month):
    # Usaremos una conexión temporal aquí para la lógica de conteo
    con = connect_db() 
    cur = con.cursor()
    prefijo = f"OT-{year}-{str(month).zfill(2)}"
    nuevo_numero_ot = ""
    
    try:
        # 1. Iniciar la transacción
        con.start_transaction() 

        # 2. Bloquear y Leer: FOR UPDATE asegura que nadie más pueda leer este dato
        # hasta que hagamos ROLLBACK o COMMIT.
        cur.execute("""
            SELECT numero_ot
            FROM ordenes_trabajo
            WHERE numero_ot LIKE %s
            ORDER BY numero_ot DESC
            LIMIT 1
            FOR UPDATE
        """, (prefijo + "%",))
        
        fila = cur.fetchone()
        
        ultimo_num = 0
        if fila and fila[0]:
            try:
                ultimo_num = int(fila[0].split('-')[-1]) 
            except Exception:
                ultimo_num = 0
                
        nuevo = ultimo_num + 1
        nuevo_numero_ot = f"{prefijo}-{str(nuevo).zfill(3)}"
        
        # 3. Insertar el nuevo número temporalmente o simplemente mantener el bloqueo.
        # Dado que NO insertamos aquí, necesitamos una tabla de control secuencial 
        # (ej: `ot_secuencias`) para bloquear solo una fila.
        
        # ⚠️ Ya que no tienes una tabla de secuencias, la única forma de que 
        # FOR UPDATE funcione correctamente es si la consulta bloquea la tabla 
        # entera para el prefijo, o si la inserción se realiza DENTRO de esta función,
        # lo cual sería más complejo.
        
        # SOLUCIÓN ALTERNATIVA MÁS LIMPIA: Usar `REPLACE INTO` en una tabla de control
        # de secuencias y usar `LAST_INSERT_ID()`, pero eso requeriría cambios mayores.
        
        # Volvamos a la solución simple: Ejecutar la secuencia de INSERT dentro de esta función
        # para que el COMMIT suceda aquí y libere el bloqueo inmediatamente.
        
        # Mejor opción: Mantener el código de la función simple, pero usar una
        # secuencia de transacción en la función principal.
        
        # Dejemos la función auxiliar simple, pero con la lectura. 
        # El fallo persiste porque las transacciones de Flask no están
        # sincronizadas.
        
    except Exception as e:
        con.rollback()
        raise e
    finally:
        cur.close()
        con.close()

    # Si el código se ejecuta muy rápido, la única forma de garantizar unicidad 
    # es que el bloque de lectura + inserción esté encapsulado y bloqueado.
    
    return nuevo_numero_ot


# app.py

# ... (Todo tu código anterior) ...

# -----------------------------------------------------
# RUTA DE IMPRESIÓN MASIVA (Ahora llama a la función definida arriba)
# -----------------------------------------------------
from datetime import date
import calendar
from flask import request, render_template, current_app

# NOTA: Asegúrate de que 'connect_db' está disponible globalmente o importada.
# Ejemplo: from .db import connect_db 

# --------------------------------------------------------------------------------
# FUNCIÓN CLAVE: Obtiene todas las OTs con sus actividades para la impresión masiva
# --------------------------------------------------------------------------------
def obtener_todas_las_ots_con_actividades():
    """
    Consulta la base de datos para obtener todas las Órdenes de Trabajo activas,
    junto con sus equipos y actividades asociadas, preparándolas para la plantilla masiva.
    """
    con = connect_db()
    cur = con.cursor(dictionary=True)
    
    ots_para_imprimir = []
    
    # 1. Obtener TODAS las OTs (con el equipo asociado)
    cur.execute("""
        SELECT ot.id, ot.numero_ot, ot.fecha_inicio, ot.fecha_final,
               ot.tecnico, ot.tipo_mantenimiento, ot.duracion_estimada_total, ot.prioridad,
               e.nombre AS equipo
        FROM ordenes_trabajo ot
        LEFT JOIN equipos e ON ot.equipo_id = e.id
        WHERE ot.estado IN ('Pendiente', 'En Proceso')
        ORDER BY ot.numero_ot
    """)
    todas_ots = cur.fetchall()

    # 2. Iterar sobre cada OT para obtener sus actividades y formatear la estructura
    for ot in todas_ots:
        ot_id = ot['id']
        ot_data = {
            'id': ot['id'],
            'numero_ot': ot['numero_ot'],
            'equipo': ot['equipo'] or 'N/A',
            'tecnico': ot['tecnico'] or 'Sin Asignar',
            'tipo_mantenimiento': ot['tipo_mantenimiento'],
            'prioridad': 'Alta' if ot.get('prioridad') is None else ot['prioridad'], 
            
            # ¡CLAVE! INCLUIMOS LA DURACIÓN TOTAL PARA QUE JINJA LA RECIBA
            'duracion_estimada_total': ot.get('duracion_estimada_total', 0) or 0, 
            
            # Formatear fechas si son objetos date
            'fecha_inicio': ot['fecha_inicio'].strftime('%d/%m/%Y') if ot['fecha_inicio'] else 'N/A',
            'fecha_final': ot['fecha_final'].strftime('%d/%m/%Y') if ot['fecha_final'] else 'N/A',
            
            # Calcular días del mes (Tomamos el mes de inicio como referencia, o 31 por defecto)
            'dias_en_mes': calendar.monthrange(ot['fecha_inicio'].year, ot['fecha_inicio'].month)[1] if ot['fecha_inicio'] else 31,
            'actividades': []
        }

        # 3. Obtener Actividades para esta OT
        # ... (el resto del código sigue igual)
        cur.execute("""
            SELECT codigo_actividad, descripcion, duracion_estimada, prioridad,
                   dias_mes, dias_realizados 
            FROM actividades_mantenimiento
            WHERE orden_trabajo_id = %s
            ORDER BY id
        """, (ot_id,))
        actividades = cur.fetchall()
        
        # 4. Procesar actividades
        for a in actividades:
            # Procesar dias_mes_list (Clave para los días programados en la impresión)
            if a.get('dias_mes'):
                a['dias_mes_list'] = [int(x) for x in str(a['dias_mes']).split(',') if x.strip().isdigit()]
            else:
                a['dias_mes_list'] = []

            # Añadir la actividad al objeto OT
            ot_data['actividades'].append(a)
            
        ots_para_imprimir.append(ot_data)

    cur.close()
    con.close()
    
    return ots_para_imprimir
# --------------------------------------------------------------------------------
# RUTA FINAL PARA EL BOTÓN DE IMPRESIÓN MASIVA
# --------------------------------------------------------------------------------
@app.route('/imprimir_ots_masivo')
def imprimir_ots_masivo():
    # Esta es la ruta que será llamada al hacer clic en el botón.
    all_ots = obtener_todas_las_ots_con_actividades()
    
    # Renderizamos la plantilla con TODAS las OTs
    return render_template('imprimir_ots_masivo.html', all_ots=all_ots)






# -------------------------TECNICOS---------------------------------------
# ... (código anterior de imports y funciones connect_db, proteger_rutas) ...

from flask import session, render_template, redirect, url_for
# Asegúrate de que 'connect_db' esté disponible en tu entorno
# from .database import connect_db 

@app.route('/inicio_tecnico')
def inicio_tecnico():
    # 1. OBTENER LA VARIABLE DEL TÉCNICO LOGUEADO
    usuario = session.get('usuario')
    
    # Asegúrate de que solo los técnicos puedan acceder aquí Y que la sesión no esté vacía
    if session.get('rol') != 'tecnico' or not usuario:
        return redirect(url_for('login')) # O a un error/login
        
    con = connect_db()
    cur = con.cursor(dictionary=True)

    # 2. DEFINIR LA CONSULTA SQL CON EL FILTRO SEGURO
    query_ot = """SELECT 
        ot.id,
        ot.numero_ot,
        ot.fecha_inicio,
        ot.fecha_final,
        ot.duracion_estimada_total,
        ot.estado,
        ot.tipo_mantenimiento,
        ot.tecnico, 
        ot.prioridad,
        e.nombre AS equipo_nombre
    FROM 
        ordenes_trabajo ot
    JOIN 
        equipos e ON ot.equipo_id = e.id
    WHERE 
        ot.estado IN ('Pendiente', 'En Proceso')
        -- FILTRO CLAVE: La columna 'ot.tecnico' debe coincidir con el valor pasado
        AND ot.tecnico = %s
    ORDER BY 
        ot.numero_ot ASC
    """
    
    # 3. EJECUTAR LA CONSULTA PASANDO LA VARIABLE 'usuario' COMO PARÁMETRO
    # Esto reemplaza %s de forma segura con el valor de la sesión.
    cur.execute(query_ot, (usuario,))
    
    ordenes = cur.fetchall()

    # Traer todas las actividades
    cur.execute("SELECT * FROM actividades_mantenimiento")
    actividades = cur.fetchall()

    # Agrupar actividades por OT
    actividades_por_ot = {}
    for act in actividades:
        ot_id = act['orden_trabajo_id']

        if ot_id not in actividades_por_ot:
            actividades_por_ot[ot_id] = []

        actividades_por_ot[ot_id].append(act)

    # ✅ ASIGNAR ACTIVIDADES + CALCULAR % AVANCE DE LA OT
    # Esta lógica procesa solo las 'ordenes' que fueron filtradas en el paso 3.
    for ot in ordenes:
        acts = actividades_por_ot.get(ot["id"], [])

        ot["actividades"] = acts  # sigue funcionando tu desplegable

        total = 0
        count = 0

        for act in acts:
            dias_mes = []
            dias_realizados = []

            if act.get('dias_mes'):
                # Añadí .strip() para mayor robustez al limpiar espacios
                dias_mes = [int(x) for x in str(act['dias_mes']).split(',') if x.strip().isdigit()]

            if act.get('dias_realizados'):
                dias_realizados = [int(x) for x in str(act['dias_realizados']).split(',') if x.strip().isdigit()]

            if len(dias_mes) > 0:
                porcentaje = (len(dias_realizados) / len(dias_mes)) * 100
                total += porcentaje
                count += 1

        # Porcentaje general de la OT
        ot["porcentaje"] = round(total / count, 1) if count > 0 else 0

    cur.close()
    con.close()

    return render_template(
        'inicio_tecnico.html',
        usuario=usuario,
        ordenes=ordenes
    )


@app.route('/solicitar_repuesto')
def solicitar_repuesto():
    return render_template('solicitar_repuesto.html')


import os
from datetime import datetime
from flask import request, redirect, url_for, flash, session

@app.route('/guardar_solicitud_repuesto', methods=['POST'])
def guardar_solicitud_repuesto():
    tecnico = session.get('usuario') or "Tecnico"
    maquina = request.form['maquina']
    descripcion = request.form['descripcion']
    imagen = request.files.get('imagen')

    imagen_path = None

    # --- Guardar imagen ---
    if imagen and imagen.filename != "":
        folder = "static/solicitudes/"
        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = datetime.now().strftime("%Y%m%d%H%M%S_") + imagen.filename
        path = os.path.join(folder, filename)
        imagen.save(path)

        imagen_path = path  # esto se guarda en MySQL

    # --- Guardar en BD ---
    con = connect_db()
    cur = con.cursor()

    query = """
        INSERT INTO solicitudes_repuestos
        (tecnico, maquina, descripcion, imagen_path, estado)
        VALUES (%s, %s, %s, %s, 'pendiente')
    """

    cur.execute(query, (
        tecnico,
        maquina,
        descripcion,
        imagen_path
    ))

    con.commit()
    con.close()

    flash("Solicitud enviada correctamente.", "success")
    return redirect(url_for('solicitar_repuesto'))


import os
import mimetypes
from datetime import datetime
from flask import (
    render_template, redirect, url_for, flash, current_app,
    send_file, abort, request
)

@app.route('/solicitudes_repuestos_admin')
def solicitudes_repuestos_admin():
    """
    Lista todas las solicitudes (para el admin).
    Ordena primero por estado (pendiente primero) y luego por fecha descendente.
    """
    con = connect_db()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        SELECT
            id,
            tecnico,
            maquina,
            descripcion,
            imagen_path,
            estado,
            prioridad,
            respuesta_admin,
            visto_en,
            fecha
        FROM solicitudes_repuestos
        ORDER BY
            -- prioridades en la lista para que 'pendiente' salga primero
            FIELD(estado, 'pendiente', 'visto', 'resuelto'),
            fecha DESC
    """)
    solicitudes = cur.fetchall()

    cur.close()
    con.close()

    return render_template('solicitudes_repuestos_admin.html', solicitudes=solicitudes)

@app.route('/marcar_solicitud_leida/<int:id>', methods=['POST'])
def marcar_solicitud_leida(id):
    """
    Marca la solicitud como 'visto' y guarda la fecha/hora en `visto_en`.
    """
    con = connect_db()
    cur = con.cursor()

    try:
        cur.execute("""
            UPDATE solicitudes_repuestos
            SET estado = 'visto', visto_en = NOW()
            WHERE id = %s
        """, (id,))
        con.commit()
        flash("Solicitud marcada como vista.", "success")
    except Exception as e:
        con.rollback()
        flash(f"Error al marcar como vista: {e}", "danger")
    finally:
        cur.close()
        con.close()

    return redirect(url_for('solicitudes_repuestos_admin'))

@app.route('/solicitud_imagen/<int:id>')
def solicitud_imagen(id):
    """
    Devuelve la imagen asociada a la solicitud leyendo la ruta almacenada en imagen_path.
    Soporta rutas absolutas o rutas relativas guardadas en la BD.
    """
    con = connect_db()
    cur = con.cursor(dictionary=True)

    cur.execute("SELECT imagen_path FROM solicitudes_repuestos WHERE id = %s", (id,))
    fila = cur.fetchone()

    cur.close()
    con.close()

    if not fila or not fila.get('imagen_path'):
        return abort(404, "Imagen no disponible")

    img_path = fila['imagen_path']

    # Si la ruta no es absoluta, intentamos resolverla respecto al root del app
    if not os.path.isabs(img_path):
        # puedes ajustar esta carpeta si guardas en 'static/uploads' u otra
        candidate = os.path.join(current_app.root_path, img_path)
        if os.path.exists(candidate):
            img_path = candidate
        else:
            # si no existe ahí, prueba en 'static/uploads'
            candidate2 = os.path.join(current_app.root_path, 'static', img_path)
            if os.path.exists(candidate2):
                img_path = candidate2

    if not os.path.exists(img_path):
        return abort(404, "Archivo de imagen no encontrado")

    # detectar mimetype
    mime, _ = mimetypes.guess_type(img_path)
    if not mime:
        mime = 'application/octet-stream'

    try:
        # send_file se encarga de los headers correctos
        return send_file(img_path, mimetype=mime, as_attachment=False)
    except Exception as e:
        # en caso de error devolver 500
        current_app.logger.exception("Error sirviendo la imagen")
        return abort(500, f"Error sirviendo la imagen: {e}")

#--------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)