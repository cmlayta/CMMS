ALTER TABLE ordenes_trabajo
ADD COLUMN equipo_id INT;
ALTER TABLE ordenes_trabajo
ADD CONSTRAINT fk_equipo
FOREIGN KEY (equipo_id) REFERENCES equipos(id);