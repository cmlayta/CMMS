CREATE TABLE ordenes_trabajo (
    id INT AUTO_INCREMENT PRIMARY KEY,

    numero_ot VARCHAR(20) NOT NULL UNIQUE,  -- Ej: OT-2025-11-001

    tecnico_responsable VARCHAR(100) NOT NULL,

    duracion_estimada_total DECIMAL(6,2) DEFAULT 0, 
    -- en horas, ejemplo: 3.50 horas

    codigo_iso VARCHAR(50), 

    fecha_inicio DATE NOT NULL,
    fecha_final DATE,

    estado ENUM('Pendiente','En Proceso','Finalizada','Cancelada') DEFAULT 'Pendiente',

    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
