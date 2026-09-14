-- ==============================================================================
-- PROYECTO E2 SAS - ÉNFASIS 2 (PRODUCCIÓN 4.0)
-- PAQUETE DE CONSULTAS ANALÍTICAS, AUDITORÍA Y LÍNEA BASE EN SQL (SUPABASE)
-- ==============================================================================

-- ==============================================================================
-- 1. AUDITORÍA GENERAL Y CONTEO DE REGISTROS POR TABLA
-- ==============================================================================

SELECT 'maestro_productos' AS tabla, COUNT(*) AS total_registros FROM public.maestro_productos
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


-- ==============================================================================
-- 2. RECONSTRUCCIÓN DEL KARDEX Y SALDO TEÓRICO AL CORTE (2026-03-31)
-- Reconcilia Saldo Inicial + Entradas - Salidas + Ajustes
-- ==============================================================================

WITH resumen_movimientos AS (
    SELECT 
        sku,
        COALESCE(SUM(CASE WHEN tipo_movimiento = 'entrada' THEN cantidad ELSE 0 END), 0) AS total_entradas,
        COALESCE(SUM(CASE WHEN tipo_movimiento = 'salida' THEN cantidad ELSE 0 END), 0) AS total_salidas,
        COALESCE(SUM(CASE WHEN tipo_movimiento = 'ajuste' THEN cantidad ELSE 0 END), 0) AS total_ajustes
    FROM public.movimientos_inventarios
    GROUP BY sku
)
SELECT 
    m.sku,
    m.descripcion,
    m.categoria,
    m.costo_unitario,
    COALESCE(ii.stock_inicial, 0) AS stock_inicial,
    COALESCE(rm.total_entradas, 0) AS total_entradas,
    COALESCE(rm.total_salidas, 0) AS total_salidas,
    COALESCE(rm.total_ajustes, 0) AS total_ajustes,
    (COALESCE(ii.stock_inicial, 0) + COALESCE(rm.total_entradas, 0) - COALESCE(rm.total_salidas, 0) + COALESCE(rm.total_ajustes, 0)) AS stock_teorico_final,
    ((COALESCE(ii.stock_inicial, 0) + COALESCE(rm.total_entradas, 0) - COALESCE(rm.total_salidas, 0) + COALESCE(rm.total_ajustes, 0)) * m.costo_unitario) AS valor_stock_final_cop
FROM public.maestro_materiales m
LEFT JOIN public.inventario_inicial ii ON m.sku = ii.sku
LEFT JOIN resumen_movimientos rm ON m.sku = rm.sku
ORDER BY valor_stock_final_cop DESC;


-- ==============================================================================
-- 3. VALIDACIÓN DE QUEJA 1: LEAD TIME REAL VS TEÓRICO Y RETRASOS DE PROVEEDORES
-- Evalúa la discrepancia entre el Lead Time declarado y el real por categoría
-- ==============================================================================

SELECT 
    m.categoria,
    COUNT(oc.orden_compra) AS total_ordenes_cerradas,
    ROUND(AVG(m.lead_time_declarado_dias)::numeric, 1) AS lead_time_declarado_promedio,
    ROUND(AVG(oc.fecha_recepcion - oc.fecha_pedido)::numeric, 1) AS lead_time_real_promedio,
    ROUND(AVG((oc.fecha_recepcion - oc.fecha_pedido) - m.lead_time_declarado_dias)::numeric, 1) AS desfase_dias_promedio,
    ROUND((COUNT(CASE WHEN oc.fecha_recepcion > oc.fecha_promesa THEN 1 END)::numeric / COUNT(oc.orden_compra) * 100), 1) AS porcentaje_retrasos_promesa,
    ROUND((COUNT(CASE WHEN (oc.fecha_recepcion - oc.fecha_pedido) > m.lead_time_declarado_dias THEN 1 END)::numeric / COUNT(oc.orden_compra) * 100), 1) AS porcentaje_retraso_vs_teorico
FROM public.ordenes_compra oc
JOIN public.maestro_materiales m ON oc.sku = m.sku
WHERE oc.fecha_recepcion IS NOT NULL
GROUP BY m.categoria
ORDER BY porcentaje_retraso_vs_teorico DESC;


-- ==============================================================================
-- 4. VALIDACIÓN DE QUEJA 2: ANÁLISIS ABC DE ROTACIÓN E INVENTARIO INMOVILIZADO
-- Identifica SKUs sin movimiento (plata muerta) y concentración de valor Pareto
-- ==============================================================================

WITH consumo_por_sku AS (
    SELECT 
        m.sku,
        m.descripcion,
        m.categoria,
        m.costo_unitario,
        COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'salida' THEN mov.cantidad ELSE 0 END), 0) AS unidades_consumidas,
        COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'salida' THEN mov.cantidad ELSE 0 END), 0) * m.costo_unitario AS valor_consumo_cop
    FROM public.maestro_materiales m
    LEFT JOIN public.movimientos_inventarios mov ON m.sku = mov.sku
    GROUP BY m.sku, m.descripcion, m.categoria, m.costo_unitario
),
total_global AS (
    SELECT SUM(valor_consumo_cop) AS total_valor_consumo FROM consumo_por_sku
)
SELECT 
    c.sku,
    c.descripcion,
    c.categoria,
    c.unidades_consumidas,
    c.valor_consumo_cop,
    ROUND((c.valor_consumo_cop / tg.total_valor_consumo * 100)::numeric, 2) AS porcentaje_consumo,
    CASE 
        WHEN c.unidades_consumidas = 0 THEN 'Plata Muerta (Sin Movimiento)'
        WHEN c.valor_consumo_cop >= 50000000 THEN 'Clase A (Alto Valor)'
        WHEN c.valor_consumo_cop >= 10000000 THEN 'Clase B (Valor Medio)'
        ELSE 'Clase C (Bajo Valor)'
    END AS clasificacion_rotacion
FROM consumo_por_sku c, total_global tg
ORDER BY c.valor_consumo_cop DESC;


-- ==============================================================================
-- 5. VALIDACIÓN DE QUEJA 3: EXACTITUD DE REGISTROS DE INVENTARIO (IRA)
-- Discrepancia entre Kardex Teórico, Conteo Físico Oficial y Bodega Jefe
-- ==============================================================================

WITH kardex_calc AS (
    SELECT 
        m.sku,
        (COALESCE(ii.stock_inicial, 0) + 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'entrada' THEN mov.cantidad ELSE 0 END), 0) - 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'salida' THEN mov.cantidad ELSE 0 END), 0) + 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'ajuste' THEN mov.cantidad ELSE 0 END), 0)) AS stock_teorico
    FROM public.maestro_materiales m
    LEFT JOIN public.inventario_inicial ii ON m.sku = ii.sku
    LEFT JOIN public.movimientos_inventarios mov ON m.sku = mov.sku
    GROUP BY m.sku, ii.stock_inicial
)
SELECT 
    m.sku,
    m.descripcion,
    m.categoria,
    ROUND(k.stock_teorico::numeric, 0) AS stock_teorico_kardex,
    cf.stock_fisico_contado AS stock_conteo_fisico,
    bj.conteo_jefe AS stock_jefe_bodega,
    (cf.stock_fisico_contado - ROUND(k.stock_teorico::numeric, 0)) AS descuadre_fisico_vs_kardex,
    CASE 
        WHEN cf.stock_fisico_contado = ROUND(k.stock_teorico::numeric, 0) THEN 'Exacto (Cuadrado)'
        ELSE 'Descuadrado'
    END AS estado_ira
FROM public.maestro_materiales m
JOIN kardex_calc k ON m.sku = k.sku
LEFT JOIN public.conteo_fisico cf ON m.sku = cf.sku
LEFT JOIN public."inventario_bodega_JEFE" bj ON m.sku = bj.codigo
ORDER BY ABS(cf.stock_fisico_contado - ROUND(k.stock_teorico::numeric, 0)) DESC;


-- Resumen Global de Exactitud de Registros (KPI IRA):
WITH comparacion_ira AS (
    SELECT 
        m.sku,
        (COALESCE(ii.stock_inicial, 0) + 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'entrada' THEN mov.cantidad ELSE 0 END), 0) - 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'salida' THEN mov.cantidad ELSE 0 END), 0) + 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'ajuste' THEN mov.cantidad ELSE 0 END), 0)) AS stock_teorico,
        cf.stock_fisico_contado
    FROM public.maestro_materiales m
    JOIN public.inventario_inicial ii ON m.sku = ii.sku
    JOIN public.conteo_fisico cf ON m.sku = cf.sku
    LEFT JOIN public.movimientos_inventarios mov ON m.sku = mov.sku
    GROUP BY m.sku, ii.stock_inicial, cf.stock_fisico_contado
)
SELECT 
    COUNT(*) AS total_skus_evaluados,
    COUNT(CASE WHEN stock_fisico_contado = ROUND(stock_teorico::numeric, 0) THEN 1 END) AS skus_exactos,
    ROUND((COUNT(CASE WHEN stock_fisico_contado = ROUND(stock_teorico::numeric, 0) THEN 1 END)::numeric / COUNT(*) * 100), 2) AS porcentaje_ira_exactitud
FROM comparacion_ira;


-- ==============================================================================
-- 6. VALIDACIÓN DE QUEJA 4: EXPLOSIÓN DE MATERIALES (BOM) Y DEMANDA POR PRODUCTO
-- Demanda acumulada de insumos para Archivadores y Estanterías
-- ==============================================================================

SELECT 
    mp.producto,
    mp.nombre_producto,
    b.sku_material,
    mm.descripcion AS descripcion_material,
    mm.categoria AS categoria_material,
    b.cantidad_por_unidad,
    b.unidad,
    SUM(pp.cantidad_real) AS total_unidades_fabricadas,
    SUM(pp.cantidad_real * b.cantidad_por_unidad) AS consumo_total_teorico_material
FROM public.plan_produccion pp
JOIN public.maestro_productos mp ON pp.producto = mp.producto
JOIN public.bom b ON mp.producto = b.producto
JOIN public.maestro_materiales mm ON b.sku_material = mm.sku
WHERE mp.nombre_producto ILIKE '%Archivador%' OR mp.nombre_producto ILIKE '%Estanter%'
GROUP BY mp.producto, mp.nombre_producto, b.sku_material, mm.descripcion, mm.categoria, b.cantidad_por_unidad, b.unidad
ORDER BY mp.nombre_producto, consumo_total_teorico_material DESC;


-- ==============================================================================
-- 7. ÓRDENES DE COMPRA EN TRÁNSITO (INVENTARIO EN CURSO)
-- Muestra las 74 órdenes abiertas para el cálculo de reposición
-- ==============================================================================

SELECT 
    oc.orden_compra,
    oc.fecha_pedido,
    oc.fecha_promesa,
    oc.sku,
    m.descripcion AS descripcion_material,
    m.categoria,
    oc.cantidad,
    oc.proveedor,
    oc.costo_unitario,
    (oc.cantidad * oc.costo_unitario) AS valor_orden_transito_cop
FROM public.ordenes_compra oc
JOIN public.maestro_materiales m ON oc.sku = m.sku
WHERE oc.fecha_recepcion IS NULL
ORDER BY oc.fecha_pedido ASC;
