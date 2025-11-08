SET SQL_SAFE_UPDATES = 0;

UPDATE repuestos
SET tipo = CASE
    WHEN nombre LIKE '%tornillo%' THEN 'Mecánico'
    WHEN nombre LIKE '%tuerca%' THEN 'Mecánico'
    WHEN nombre LIKE '%arandela%' THEN 'Mecánico'
    WHEN nombre LIKE '%resorte%' THEN 'Mecánico'
    WHEN nombre LIKE '%rodamiento%' THEN 'Mecánico'
    WHEN nombre LIKE '%eje%' THEN 'Mecánico'
    WHEN nombre LIKE '%cadena%' THEN 'Mecánico'
    WHEN nombre LIKE '%faja%' THEN 'Mecánico'
    WHEN nombre LIKE '%sprocket%' THEN 'Mecánico'

    WHEN nombre LIKE '%racor%' THEN 'Neumático'
    WHEN nombre LIKE '%cilindro%' THEN 'Neumático'
    WHEN nombre LIKE '%manómetro%' THEN 'Neumático'
    WHEN nombre LIKE '%válvula%' THEN 'Neumático'
    WHEN nombre LIKE '%filtro%' THEN 'Neumático'
    WHEN nombre LIKE '%regulador%' THEN 'Neumático'
    WHEN nombre LIKE '%lubricador%' THEN 'Neumático'
    WHEN nombre LIKE '%conector%' THEN 'Neumático'
    WHEN nombre LIKE '%manguera%' THEN 'Neumático'
    WHEN nombre LIKE '%boquilla%' THEN 'Neumático'

    WHEN nombre LIKE '%fuente%' THEN 'Electrónico'
    WHEN nombre LIKE '%tarjeta%' THEN 'Electrónico'
    WHEN nombre LIKE '%sensor%' THEN 'Electrónico'
    WHEN nombre LIKE '%variador%' THEN 'Electrónico'
    WHEN nombre LIKE '%transformador%' THEN 'Electrónico'
    WHEN nombre LIKE '%condensador%' THEN 'Electrónico'
    WHEN nombre LIKE '%electro válvula%' THEN 'Electrónico'
    WHEN nombre LIKE '%bobina%' THEN 'Electrónico'
    WHEN nombre LIKE '%interruptor%' THEN 'Electrónico'
    WHEN nombre LIKE '%presostato%' THEN 'Electrónico'
    WHEN nombre LIKE '%relay%' THEN 'Electrónico'
    ELSE 'Indefinido'
END;

SET SQL_SAFE_UPDATES = 1;
