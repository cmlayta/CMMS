ALTER TABLE ordenes_trabajo
ADD COLUMN descripcion TEXT,
ADD COLUMN tecnico VARCHAR(100),
ADD COLUMN fecha_programada DATE,
ADD COLUMN observaciones TEXT;
