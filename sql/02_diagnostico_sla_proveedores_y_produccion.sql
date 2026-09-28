-- ==============================================================================
-- PROYECTO E2 SAS - ÉNFASIS 2 (PRODUCCIÓN 4.0)
-- ARCHIVO: sql/02_diagnostico_sla_proveedores_y_produccion.sql
-- DESCRIPCIÓN: Consultas de cálculo de SLA (Nivel de Servicio y Entregas de Proveedores) 
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
    ROUND((COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END)::numeric / COUNT(CASE WHEN fecha_recepcion IS NOT NULL THEN 1 END) * 100), 2) AS sla_global_proveedores_pct,
    ROUND(AVG(CASE WHEN fecha_recepcion > fecha_promesa THEN fecha_recepcion - fecha_promesa END)::numeric, 2) AS dias_mora_promedio_cuando_tarde,
    ROUND(AVG(fecha_recepcion - fecha_pedido)::numeric, 2) AS lead_time_real_promedio_dias
FROM public.ordenes_compra;


-- ==============================================================================
-- 2. SLA DE PROVEEDORES DESGLOSADO POR CATEGORÍA DE MATERIAL
-- ==============================================================================

SELECT 
    m.categoria,
    COUNT(oc.orden_compra) AS total_ordenes_cerradas,
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
-- 3. SLA Y RANKING DE CUMPLIMIENTO POR CADA PROVEEDOR (TOP 10 MÁS CRÍTICOS)
-- ==============================================================================

SELECT 
    proveedor,
    COUNT(orden_compra) AS total_ordenes_cerradas,
    COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END) AS ordenes_a_tiempo,
    COUNT(CASE WHEN fecha_recepcion > fecha_promesa THEN 1 END) AS ordenes_retrasadas,
    ROUND((COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END)::numeric / COUNT(orden_compra) * 100), 2) || ' %' AS sla_proveedor_pct,
    ROUND(AVG(fecha_recepcion - fecha_promesa)::numeric, 1) || ' d' AS retraso_promedio_dias,
    ROUND(AVG(fecha_recepcion - fecha_pedido)::numeric, 1) || ' d' AS lead_time_real_promedio
FROM public.ordenes_compra
WHERE fecha_recepcion IS NOT NULL
GROUP BY proveedor
ORDER BY ROUND((COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END)::numeric / COUNT(orden_compra) * 100), 2) ASC, retraso_promedio_dias DESC
LIMIT 10;


-- ==============================================================================
-- 4. CÁLCULO DE ERI (EXACTITUD EN EL REGISTRO DE INVENTARIO) Y DESALINEACIÓN CONTABLE
-- ==============================================================================

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
),
comparacion_eri AS (
    SELECT 
        k.sku,
        k.descripcion,
        k.categoria,
        k.costo_unitario,
        k.total_consumo,
        k.stock_teorico_kardex,
        COALESCE(cf.stock_fisico_contado, 0) AS stock_fisico_contado,
        COALESCE(bj.conteo_jefe, 0) AS stock_cuaderno_jefe,
        ABS(COALESCE(cf.stock_fisico_contado, 0) - k.stock_teorico_kardex) AS descuadre_absoluto_unidades,
        (ABS(COALESCE(cf.stock_fisico_contado, 0) - k.stock_teorico_kardex) * k.costo_unitario) AS descuadre_absoluto_cop,
        CASE 
            WHEN k.stock_teorico_kardex = COALESCE(cf.stock_fisico_contado, 0) THEN 1 
            ELSE 0 
        END AS es_exacto,
        CASE 
            WHEN k.total_consumo > 0 THEN 'Activo (En Rotación)' 
            ELSE 'Inactivo (Plata Muerta)' 
        END AS tipo_rotacion
    FROM kardex_calc k
    LEFT JOIN public.conteo_fisico cf ON k.sku = cf.sku
    LEFT JOIN public."inventario_bodega_JEFE" bj ON k.sku = bj.codigo
)
SELECT 
    tipo_rotacion,
    COUNT(*) AS total_skus,
    SUM(es_exacto) AS skus_exactos,
    COUNT(*) - SUM(es_exacto) AS skus_descuadrados,
    ROUND((SUM(es_exacto)::numeric / COUNT(*) * 100), 2) || ' %' AS eri_porcentaje_exactitud,
    ROUND(((COUNT(*) - SUM(es_exacto))::numeric / COUNT(*) * 100), 2) || ' %' AS pct_error_discrepancia,
    '$ ' || TO_CHAR(SUM(descuadre_absoluto_cop), 'FM999,999,999,990') || ' COP' AS desalineacion_contable_bruta
FROM comparacion_eri
GROUP BY tipo_rotacion
UNION ALL
SELECT 
    'TOTAL GENERAL' AS tipo_rotacion,
    COUNT(*) AS total_skus,
    SUM(es_exacto) AS skus_exactos,
    COUNT(*) - SUM(es_exacto) AS skus_descuadrados,
    ROUND((SUM(es_exacto)::numeric / COUNT(*) * 100), 2) || ' %' AS eri_porcentaje_exactitud,
    ROUND(((COUNT(*) - SUM(es_exacto))::numeric / COUNT(*) * 100), 2) || ' %' AS pct_error_discrepancia,
    '$ ' || TO_CHAR(SUM(descuadre_absoluto_cop), 'FM999,999,999,990') || ' COP' AS desalineacion_contable_bruta
FROM comparacion_eri;


-- ==============================================================================
-- 5. SLA DE PRODUCCIÓN (CUMPLIMIENTO DE METAS DEL MPS)
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
