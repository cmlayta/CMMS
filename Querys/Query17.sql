ALTER TABLE actividades_mantenimiento
ADD CONSTRAINT fk_actividad_ot_fija
FOREIGN KEY (plan_id)
REFERENCES actividades_ot_fijas(id)
ON DELETE CASCADE;