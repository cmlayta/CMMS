CREATE TABLE actividades_ot_fijas (
    id INT AUTO_INCREMENT PRIMARY KEY,

    ot_fija_id INT NOT NULL,

    actividad VARCHAR(255) NOT NULL,
    frecuencia VARCHAR(50) NOT NULL,
    observaciones TEXT,

    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_actividades_ot_fijas
        FOREIGN KEY (ot_fija_id)
        REFERENCES ordenes_trabajo_fijas(id)
        ON DELETE CASCADE
);
