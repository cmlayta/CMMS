ALTER TABLE actividades_ot_fijas
  ADD CONSTRAINT chk_dia_semana CHECK (dia_semana IS NULL OR (dia_semana BETWEEN 1 AND 7)),
  ADD CONSTRAINT chk_semana_mes CHECK (semana_mes IS NULL OR (semana_mes BETWEEN 1 AND 5)),
  ADD CONSTRAINT chk_dia_mes CHECK (dia_mes IS NULL OR (dia_mes BETWEEN 1 AND 31));
