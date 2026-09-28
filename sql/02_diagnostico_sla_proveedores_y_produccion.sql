-- ==============================================================================
-- PROYECTO E2 SAS - ÉNFASIS 2 (PRODUCCIÓN 4.0)
-- ARCHIVO: sql/02_diagnostico_sla_proveedores_y_produccion.sql
-- DESCRIPCIÓN: Consultas y vistas de cálculo de SLA (Nivel de Servicio y Entregas de Proveedores) 
--              y ERI (Exactitud en el Registro de Inventario / Reconciliación Tridimensional)
-- ==============================================================================

-- ==============================================================================
-- 1. SLA GLOBAL DE PROVEEDORES (CUMPLIMIENTO DE FECHA PROMESA DE ENTREGA)
-- ==============================================================================

SELECT 
    COUNT(*) AS total_ordenes_registradas,
    COUNT(CASE WHEN fecha_recepcion IS NOT NULL THEN 1 END) AS ordenes_cerradas,
    COUNT(CASE WHEN fecha_recepcion IS NULL THEN 1 END) AS ordenes_abiertas_en_transito,
    COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END) AS entregas_a_tiempo_promesa,
    COUNT(CASE WHEN fecha_recepcion > fecha_promesa THEN 1 END) AS entregas_tardias_promesa,
    ROUND((COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END)::numeric / COUNT(CASE WHEN fecha_recepcion IS NOT NULL THEN 1 END) * 100), 2) || ' %' AS sla_global_proveedores_pct,
    ROUND(AVG(CASE WHEN fecha_recepcion > fecha_promesa THEN fecha_recepcion - fecha_promesa END)::numeric, 2) || ' d' AS dias_mora_promedio_cuando_tarde,
    ROUND(AVG(fecha_recepcion - fecha_pedido)::numeric, 2) || ' d' AS lead_time_real_promedio_dias
FROM public.ordenes_compra;


-- ==============================================================================
-- 2. SLA DE PROVEEDORES DESGLOSADO POR CATEGORÍA DE MATERIAL
-- ==============================================================================

SELECT 
    m.categoria,
    COUNT(oc.orden_compra) AS total_oc_cerradas,
    COUNT(CASE WHEN oc.fecha_recepcion <= oc.fecha_promesa THEN 1 END) AS ordenes_a_tiempo,
    COUNT(CASE WHEN oc.fecha_recepcion > oc.fecha_promesa THEN 1 END) AS ordenes_retrasadas,
    ROUND((COUNT(CASE WHEN oc.fecha_recepcion <= oc.fecha_promesa THEN 1 END)::numeric / COUNT(oc.orden_compra) * 100), 2) || ' %' AS sla_cumplimiento_pct,
    ROUND(AVG(oc.fecha_recepcion - oc.fecha_promesa)::numeric, 1) || ' d' AS mora_promesa_promedio,
    ROUND(AVG(m.lead_time_declarado_dias)::numeric, 1) || ' d' AS lead_time_erp,
    ROUND(AVG(oc.fecha_recepcion - oc.fecha_pedido)::numeric, 1) || ' d' AS lead_time_real,
    ROUND(AVG((oc.fecha_recepcion - oc.fecha_pedido) - m.lead_time_declarado_dias)::numeric, 1) || ' d' AS desfase_lead_time
FROM public.ordenes_compra oc
JOIN public.maestro_materiales m ON oc.sku = m.sku
WHERE oc.fecha_recepcion IS NOT NULL
GROUP BY m.categoria
ORDER BY ROUND((COUNT(CASE WHEN oc.fecha_recepcion <= oc.fecha_promesa THEN 1 END)::numeric / COUNT(oc.orden_compra) * 100), 2) ASC;


-- ==============================================================================
-- 3. CREACIÓN DE VISTA DETALLADA DE ERI (EXACTITUD EN EL REGISTRO DE INVENTARIO)
-- ==============================================================================

CREATE OR REPLACE VIEW public.vista_diagnostico_eri_inventarios AS
WITH kardex_calc AS (
    SELECT 
        m.sku,
        m.descripcion,
        m.categoria,
        m.costo_unitario,
        (COALESCE(ii.stock_inicial, 0) + 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'entrada' THEN mov.cantidad ELSE 0 END), 0) - 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'salida' THEN mov.cantidad ELSE 0 END), 0) + 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'ajuste' THEN mov.cantidad ELSE 0 END), 0)) AS stock_teorico_kardex,
        COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'salida' THEN mov.cantidad ELSE 0 END), 0) AS total_consumo
    FROM public.maestro_materiales m
    LEFT JOIN public.inventario_inicial ii ON m.sku = ii.sku
    LEFT JOIN public.movimientos_inventarios mov ON m.sku = mov.sku
    WHERE m.sku NOT LIKE 'MP-9%' AND m.descripcion NOT LIKE '%(dup)%'
    GROUP BY m.sku, m.descripcion, m.categoria, m.costo_unitario, ii.stock_inicial
)
SELECT 
    k.sku,
    k.descripcion,
    k.categoria,
    k.costo_unitario,
    '$ ' || TO_CHAR(k.costo_unitario, 'FM999,999,999,990') AS costo_unitario_formato,
    k.stock_teorico_kardex,
    TO_CHAR(k.stock_teorico_kardex, 'FM999,999,990.00') || ' und' AS stock_kardex_formato,
    COALESCE(cf.stock_fisico_contado, 0) AS stock_fisico_oficial,
    TO_CHAR(COALESCE(cf.stock_fisico_contado, 0), 'FM999,999,990.00') || ' und' AS stock_fisico_formato,
    COALESCE(bj.conteo_jefe, 0) AS stock_cuaderno_jefe,
    TO_CHAR(COALESCE(bj.conteo_jefe, 0), 'FM999,999,990.00') || ' und' AS stock_jefe_formato,
    (COALESCE(cf.stock_fisico_contado, 0) - k.stock_teorico_kardex) AS discrepancia_unidades,
    TO_CHAR((COALESCE(cf.stock_fisico_contado, 0) - k.stock_teorico_kardex), 'FM999,999,990.00') || ' und' AS discrepancia_formato,
    ABS(COALESCE(cf.stock_fisico_contado, 0) - k.stock_teorico_kardex) AS descuadre_absoluto_unidades,
    ROUND((ABS(COALESCE(cf.stock_fisico_contado, 0) - k.stock_teorico_kardex) * k.costo_unitario)::numeric, 2) AS desalineacion_dinero_cop,
    '$ ' || TO_CHAR(ABS(COALESCE(cf.stock_fisico_contado, 0) - k.stock_teorico_kardex) * k.costo_unitario, 'FM999,999,999,990') || ' COP' AS desalineacion_dinero_formato,
    CASE 
        WHEN k.stock_teorico_kardex = COALESCE(cf.stock_fisico_contado, 0) THEN 'Exacto (Conforme ERI)' 
        ELSE 'Descuadrado (Discrepancia ERI)' 
    END AS estado_eri,
    CASE 
        WHEN k.total_consumo > 0 THEN 'Activo (En Rotación)' 
        ELSE 'Inactivo (Plata Muerta)' 
    END AS tipo_rotacion
FROM kardex_calc k
LEFT JOIN public.conteo_fisico cf ON k.sku = cf.sku
LEFT JOIN public."inventario_bodega_JEFE" bj ON k.sku = bj.codigo
ORDER BY desalineacion_dinero_cop DESC;


-- ==============================================================================
-- 4. CREACIÓN DE VISTA DE RESUMEN EJECUTIVO ERI AGREGADO
-- ==============================================================================

CREATE OR REPLACE VIEW public.vista_resumen_eri_inventarios AS
WITH resumen_agrupado AS (
    SELECT 
        tipo_rotacion,
        COUNT(*) AS total_skus,
        COUNT(CASE WHEN estado_eri LIKE 'Exacto%' THEN 1 END) AS skus_exactos,
        COUNT(CASE WHEN estado_eri LIKE 'Descuadrado%' THEN 1 END) AS skus_descuadrados,
        ROUND((COUNT(CASE WHEN estado_eri LIKE 'Exacto%' THEN 1 END)::numeric / COUNT(*) * 100), 2) AS eri_porcentaje_exactitud_num,
        ROUND((COUNT(CASE WHEN estado_eri LIKE 'Exacto%' THEN 1 END)::numeric / COUNT(*) * 100), 2) || ' %' AS eri_porcentaje_exactitud,
        ROUND((COUNT(CASE WHEN estado_eri LIKE 'Descuadrado%' THEN 1 END)::numeric / COUNT(*) * 100), 2) || ' %' AS pct_error_discrepancia,
        SUM(desalineacion_dinero_cop) AS desalineacion_contable_cop_num,
        '$ ' || TO_CHAR(SUM(desalineacion_dinero_cop), 'FM999,999,999,990') || ' COP' AS desalineacion_contable_bruta
    FROM public.vista_diagnostico_eri_inventarios
    GROUP BY tipo_rotacion
),
total_general AS (
    SELECT 
        'TOTAL GENERAL'::text AS tipo_rotacion,
        COUNT(*) AS total_skus,
        COUNT(CASE WHEN estado_eri LIKE 'Exacto%' THEN 1 END) AS skus_exactos,
        COUNT(CASE WHEN estado_eri LIKE 'Descuadrado%' THEN 1 END) AS skus_descuadrados,
        ROUND((COUNT(CASE WHEN estado_eri LIKE 'Exacto%' THEN 1 END)::numeric / COUNT(*) * 100), 2) AS eri_porcentaje_exactitud_num,
        ROUND((COUNT(CASE WHEN estado_eri LIKE 'Exacto%' THEN 1 END)::numeric / COUNT(*) * 100), 2) || ' %' AS eri_porcentaje_exactitud,
        ROUND((COUNT(CASE WHEN estado_eri LIKE 'Descuadrado%' THEN 1 END)::numeric / COUNT(*) * 100), 2) || ' %' AS pct_error_discrepancia,
        SUM(desalineacion_dinero_cop) AS desalineacion_contable_cop_num,
        '$ ' || TO_CHAR(SUM(desalineacion_dinero_cop), 'FM999,999,999,990') || ' COP' AS desalineacion_contable_bruta
    FROM public.vista_diagnostico_eri_inventarios
)
SELECT 
    tipo_rotacion,
    total_skus,
    skus_exactos,
    skus_descuadrados,
    eri_porcentaje_exactitud,
    pct_error_discrepancia,
    desalineacion_contable_bruta
FROM resumen_agrupado
UNION ALL
SELECT 
    tipo_rotacion,
    total_skus,
    skus_exactos,
    skus_descuadrados,
    eri_porcentaje_exactitud,
    pct_error_discrepancia,
    desalineacion_contable_bruta
FROM total_general;


-- ==============================================================================
-- 5. CONSULTA DE CONSUMO DIRECTO SOBRE EL RESUMEN ERI
-- ==============================================================================

SELECT 
    tipo_rotacion,
    total_skus,
    skus_exactos,
    skus_descuadrados,
    eri_porcentaje_exactitud,
    desalineacion_contable_bruta
FROM public.vista_resumen_eri_inventarios;


-- ==============================================================================
-- 6. SLA DE PRODUCCIÓN (CUMPLIMIENTO DE METAS DEL MPS)
-- ==============================================================================

SELECT 
    COUNT(*) AS total_meses_producto,
    SUM(cantidad_planeada) AS total_unidades_planeadas,
    SUM(cantidad_real) AS total_unidades_reales,
    ROUND((SUM(cantidad_real)::numeric / SUM(cantidad_planeada) * 100), 2) || ' %' AS adherencia_produccion_volumen_pct,
    COUNT(CASE WHEN cantidad_real >= cantidad_planeada THEN 1 END) AS metas_cumplidas_count,
    COUNT(CASE WHEN cantidad_real < cantidad_planeada THEN 1 END) AS metas_incumplidas_count,
    ROUND((COUNT(CASE WHEN cantidad_real >= cantidad_planeada THEN 1 END)::numeric / COUNT(*) * 100), 2) || ' %' AS sla_cumplimiento_metas_mps_pct
FROM public.plan_produccion;

