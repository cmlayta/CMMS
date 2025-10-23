
-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE NOT NULL,
    contrasena TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'tecnico'
);

-- Tabla de equipos
CREATE TABLE IF NOT EXISTS equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT
);

-- Tabla de repuestos
CREATE TABLE IF NOT EXISTS repuestos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    nombre TEXT NOT NULL,
    tipo TEXT,
    ubicacion TEXT,
    stock INTEGER DEFAULT 0
);

-- Tabla de mantenimientos
CREATE TABLE IF NOT EXISTS mantenimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER,
    descripcion TEXT,
    tipo TEXT,
    fecha_programada DATE,
    horas_uso INTEGER,
    tecnico TEXT,
    realizado INTEGER DEFAULT 0,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);

-- Tabla de movimientos de repuestos
CREATE TABLE IF NOT EXISTS movimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repuesto_id INTEGER,
    tipo_movimiento TEXT,
    cantidad INTEGER,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    tecnico TEXT,
    FOREIGN KEY (repuesto_id) REFERENCES repuestos(id)
);
