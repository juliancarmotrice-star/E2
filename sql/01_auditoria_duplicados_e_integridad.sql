-- ==============================================================================
-- PROYECTO E2 SAS - ÉNFASIS 2 (PRODUCCIÓN 4.0)
-- ARCHIVO: sql/01_auditoria_duplicados_e_integridad.sql
-- DESCRIPCIÓN: Diagnóstico de duplicados, integridad referencial y saneamiento de catálogo
-- ==============================================================================

-- 1. CONTEO GENERAL DE FILAS POR TABLA
SELECT 
    'maestro_productos' AS tabla, COUNT(*) AS total_registros FROM public.maestro_productos
UNION ALL
SELECT 'maestro_materiales', COUNT(*) FROM public.maestro_materiales
UNION ALL
SELECT 'inventario_inicial', COUNT(*) FROM public.inventario_inicial
UNION ALL
SELECT 'conteo_fisico', COUNT(*) FROM public.conteo_fisico
UNION ALL
SELECT 'inventario_bodega_JEFE', COUNT(*) FROM public."inventario_bodega_JEFE"
UNION ALL
SELECT 'bom', COUNT(*) FROM public.bom
UNION ALL
SELECT 'plan_produccion', COUNT(*) FROM public.plan_produccion
UNION ALL
SELECT 'ordenes_compra', COUNT(*) FROM public.ordenes_compra
UNION ALL
SELECT 'movimientos_inventarios', COUNT(*) FROM public.movimientos_inventarios
ORDER BY total_registros DESC;


-- 2. AUDITORÍA DE DUPLICADOS EN TODAS LAS TABLAS
-- A. Detección de duplicados exactos en plan_produccion
SELECT 'plan_produccion - duplicados exactos' AS prueba, COUNT(*) AS total_duplicados
FROM (
    SELECT periodo, producto, cantidad_planeada, cantidad_real, COUNT(*)
    FROM public.plan_produccion
    GROUP BY periodo, producto, cantidad_planeada, cantidad_real
    HAVING COUNT(*) > 1
) s
UNION ALL
-- B. Detección de duplicados de clave natural (periodo, producto) en plan_produccion
SELECT 'plan_produccion - par (periodo, producto) duplicado', COUNT(*)
FROM (
    SELECT periodo, producto, COUNT(*)
    FROM public.plan_produccion
    GROUP BY periodo, producto
    HAVING COUNT(*) > 1
) s
UNION ALL
-- C. Detección de duplicados en BOM (producto, sku_material)
SELECT 'bom - par (producto, sku_material) duplicado', COUNT(*)
FROM (
    SELECT producto, sku_material, COUNT(*)
    FROM public.bom
    GROUP BY producto, sku_material
    HAVING COUNT(*) > 1
) s
UNION ALL
-- D. Detección de transacciones duplicadas en Kardex
SELECT 'movimientos_inventarios - transacciones identicas', COUNT(*)
FROM (
    SELECT fecha, sku, tipo_movimiento, cantidad, bodega, responsable, COUNT(*)
    FROM public.movimientos_inventarios
    GROUP BY fecha, sku, tipo_movimiento, cantidad, bodega, responsable
    HAVING COUNT(*) > 1
) s
UNION ALL
-- E. Detección de órdenes de compra duplicadas
SELECT 'ordenes_compra - ordenes identicas', COUNT(*)
FROM (
    SELECT fecha_pedido, sku, cantidad, proveedor, fecha_promesa, fecha_recepcion, costo_unitario, COUNT(*)
    FROM public.ordenes_compra
    GROUP BY fecha_pedido, sku, cantidad, proveedor, fecha_promesa, fecha_recepcion, costo_unitario
    HAVING COUNT(*) > 1
) s
UNION ALL
-- F. Detección de descripciones duplicadas en maestro de materiales
SELECT 'maestro_materiales - descripciones compartidas', COUNT(*)
FROM (
    SELECT descripcion, COUNT(*)
    FROM public.maestro_materiales
    GROUP BY descripcion
    HAVING COUNT(*) > 1
) s;


-- 3. AISLAMIENTO DE LOS 20 SKUS SINTÉTICOS / DUPLICADOS EN MAESTRO_MATERIALES
SELECT 
    sku, 
    descripcion, 
    categoria, 
    unidad, 
    costo_unitario, 
    proveedor,
    lead_time_declarado_dias
FROM public.maestro_materiales
WHERE sku LIKE 'MP-9%' OR descripcion LIKE '%(dup)%'
ORDER BY sku;


-- 4. VERIFICACIÓN DE INTEGRIDAD REFERENCIAL (Comprobar que no hay huérfanos con MP-9xxx)
SELECT 'movimientos_inventarios -> MP-9xxx' AS relacion, COUNT(*) AS referencias_invalidas
FROM public.movimientos_inventarios WHERE sku LIKE 'MP-9%'
UNION ALL
SELECT 'ordenes_compra -> MP-9xxx', COUNT(*)
FROM public.ordenes_compra WHERE sku LIKE 'MP-9%'
UNION ALL
SELECT 'bom -> MP-9xxx', COUNT(*)
FROM public.bom WHERE sku_material LIKE 'MP-9%'
UNION ALL
SELECT 'inventario_inicial -> MP-9xxx', COUNT(*)
FROM public.inventario_inicial WHERE sku LIKE 'MP-9%'
UNION ALL
SELECT 'conteo_fisico -> MP-9xxx', COUNT(*)
FROM public.conteo_fisico WHERE sku LIKE 'MP-9%';


-- 5. SCRIPT DE DEPURACIÓN SEGURA DE LOS 20 DUPLICADOS SINTÉTICOS
-- (Descomentar para ejecutar)
-- DELETE FROM public.maestro_materiales WHERE sku LIKE 'MP-9%' OR descripcion LIKE '%(dup)%';

-- Validación post-eliminación: debe arrojar exactamente 420 SKUs reales
-- SELECT COUNT(*) AS skus_reales_limpios FROM public.maestro_materiales;
