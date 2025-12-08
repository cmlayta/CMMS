CREATE TABLE actividades_mantenimiento (
    id INT AUTO_INCREMENT PRIMARY KEY,

    orden_trabajo_id INT NULL,
    plan_id INT NULL,

    codigo_actividad VARCHAR(50),
    descripcion TEXT,

    prioridad ENUM('Baja','Media','Alta','Critica'),

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
    ),

    duracion_estimada DECIMAL(6,2),

    tipo_trabajo ENUM('Preventivo','Correctivo'),

    -- Relaciones
    CONSTRAINT fk_actividad_ot
        FOREIGN KEY (orden_trabajo_id)
        REFERENCES ordenes_trabajo(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_actividad_plan
        FOREIGN KEY (plan_id)
        REFERENCES planes_mantenimiento(id)
        ON DELETE CASCADE
);
