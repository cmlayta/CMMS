ALTER TABLE actividades_ot_fijas
  ADD COLUMN codigo_actividad VARCHAR(50) NULL AFTER ot_fija_id,
  ADD COLUMN prioridad ENUM('Baja','Media','Alta','Critica') NOT NULL DEFAULT 'Media' AFTER codigo_actividad,
  ADD COLUMN frecuencia_new ENUM(
        'Diaria',
        'Semanal',
        'Quincenal',
        'Mensual',
        'Trimestral',
        'Semestral',
        'Anual',
        'Personalizada'
  ) NULL AFTER prioridad,
  ADD COLUMN dia_semana TINYINT NULL COMMENT '1=Lunes .. 7=Domingo' AFTER frecuencia_new,
  ADD COLUMN semana_mes TINYINT NULL COMMENT '1..5 (p.ej. segunda semana)' AFTER dia_semana,
  ADD COLUMN dia_mes TINYINT NULL COMMENT '1..31' AFTER semana_mes;
