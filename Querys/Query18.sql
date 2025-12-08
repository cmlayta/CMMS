CREATE TABLE solicitudes_repuestos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    tecnico VARCHAR(100) NOT NULL,
    maquina TEXT NOT NULL,            -- La máquina/sitio escrito por el técnico
    descripcion TEXT NOT NULL,        -- Detalle del repuesto solicitado
    imagen_path VARCHAR(255),         -- Ruta del archivo (si adjunta imagen)
    estado ENUM('pendiente','visto','resuelto') DEFAULT 'pendiente'
);
