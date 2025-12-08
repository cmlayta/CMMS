CREATE TABLE ordenes_trabajo_fijas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_ot VARCHAR(20) NOT NULL,

    equipo_id INT NOT NULL,
    tipo_mantenimiento VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    tecnico VARCHAR(100) NOT NULL,
    observaciones TEXT,

    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
