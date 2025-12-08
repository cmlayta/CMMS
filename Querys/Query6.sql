CREATE TABLE planes_mantenimiento (
  id INT AUTO_INCREMENT PRIMARY KEY,
  equipo_id INT NOT NULL,
  tecnico_id INT NOT NULL,
  nombre_plan VARCHAR(150),
  frecuencia VARCHAR(20),          -- semanal, mensual, semestral, anual

  dia_semana INT NULL,             -- 1=Lun ... 7=Dom
  semana_mes INT NULL,             -- 1 a 5
  dia_mes INT NULL,                -- 1-31
  mes_anio INT NULL,               -- 1-12 (solo anual)

  activo BOOLEAN DEFAULT 1,

  FOREIGN KEY (equipo_id) REFERENCES equipos(id),
  FOREIGN KEY (tecnico_id) REFERENCES usuarios(id)
);
