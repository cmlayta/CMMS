CREATE TABLE actividades_mantenimiento (
    id INT AUTO_INCREMENT PRIMARY KEY,

    orden_trabajo_id INT NOT NULL,

    codigo_actividad VARCHAR(50) NOT NULL,

    descripcion TEXT,

    prioridad ENUM('Baja','Media','Alta','Critica') DEFAULT 'Media',

    frecuencia ENUM(
        'Diaria',
        'Semanal',
        'Quincenal',
        'Mensual',
        'Bimestral',
        'Trimestral',
        'Semestral',
        'Anual',
        'Personalizada'
    ) NOT NULL,

    duracion_estimada DECIMAL(6,2) NOT NULL, 
    -- en horas, ej: 0.50, 1.75

    tipo_trabajo ENUM('Preventivo','Correctivo') NOT NULL,

    FOREIGN KEY (orden_trabajo_id) 
        REFERENCES ordenes_trabajo(id)
        ON DELETE CASCADE
);
