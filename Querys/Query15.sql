DELIMITER $$

CREATE TRIGGER actividades_ad
AFTER DELETE ON actividades_mantenimiento
FOR EACH ROW
BEGIN

    UPDATE ordenes_trabajo
    SET duracion_estimada_total = (
        SELECT IFNULL(SUM(
            duracion_estimada * 
            (LENGTH(dias_mes) - LENGTH(REPLACE(dias_mes, ',', '')) + 1)
        ), 0)
        FROM actividades_mantenimiento
        WHERE orden_trabajo_id = OLD.orden_trabajo_id
    )
    WHERE id = OLD.orden_trabajo_id;

END$$
DELIMITER ;
