-- ==============================================================================
-- PROYECTO E2 SAS - ÉNFASIS 2 (PRODUCCIÓN 4.0)
-- ARCHIVO: sql/02_diagnostico_sla_proveedores_y_produccion.sql
-- DESCRIPCIÓN: Consultas de cálculo de SLA (OTIF proveedores, retrasos y plan de manufactura)
-- ==============================================================================

-- ==============================================================================
-- 1. SLA GLOBAL DE PROVEEDORES (ON-TIME DELIVERY vs FECHA PROMESA)
-- ==============================================================================

SELECT 
    COUNT(*) AS total_ordenes_registradas,
    COUNT(CASE WHEN fecha_recepcion IS NOT NULL THEN 1 END) AS ordenes_cerradas,
    COUNT(CASE WHEN fecha_recepcion IS NULL THEN 1 END) AS ordenes_abiertas_en_transito,
    COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END) AS entregas_a_tiempo_promesa,
    COUNT(CASE WHEN fecha_recepcion > fecha_promesa THEN 1 END) AS entregas_tardias_promesa,
    ROUND((COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END)::numeric / COUNT(CASE WHEN fecha_recepcion IS NOT NULL THEN 1 END) * 100), 2) AS sla_otif_global_pct,
    ROUND(AVG(CASE WHEN fecha_recepcion > fecha_promesa THEN fecha_recepcion - fecha_promesa END)::numeric, 2) AS dias_retraso_promedio_cuando_tarde,
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
    ROUND((COUNT(CASE WHEN oc.fecha_recepcion <= oc.fecha_promesa THEN 1 END)::numeric / COUNT(oc.orden_compra) * 100), 2) AS sla_otif_pct,
    ROUND(AVG(oc.fecha_recepcion - oc.fecha_promesa)::numeric, 1) AS desviacion_promedio_promesa_dias,
    ROUND(AVG(m.lead_time_declarado_dias)::numeric, 1) AS lead_time_teorico_dias,
    ROUND(AVG(oc.fecha_recepcion - oc.fecha_pedido)::numeric, 1) AS lead_time_real_dias,
    ROUND(AVG((oc.fecha_recepcion - oc.fecha_pedido) - m.lead_time_declarado_dias)::numeric, 1) AS desfase_vs_teorico_dias
FROM public.ordenes_compra oc
JOIN public.maestro_materiales m ON oc.sku = m.sku
WHERE oc.fecha_recepcion IS NOT NULL
GROUP BY m.categoria
ORDER BY sla_otif_pct ASC, desfase_vs_teorico_dias DESC;


-- ==============================================================================
-- 3. SLA Y RANKING DE CUMPLIMIENTO POR CADA UNO DE LOS 35 PROVEEDORES
-- ==============================================================================

SELECT 
    proveedor,
    COUNT(orden_compra) AS total_ordenes_cerradas,
    COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END) AS ordenes_a_tiempo,
    COUNT(CASE WHEN fecha_recepcion > fecha_promesa THEN 1 END) AS ordenes_retrasadas,
    ROUND((COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END)::numeric / COUNT(orden_compra) * 100), 2) AS sla_otif_pct,
    ROUND(AVG(fecha_recepcion - fecha_promesa)::numeric, 1) AS retraso_promesa_promedio_dias,
    ROUND(AVG(fecha_recepcion - fecha_pedido)::numeric, 1) AS lead_time_real_promedio_dias
FROM public.ordenes_compra
WHERE fecha_recepcion IS NOT NULL
GROUP BY proveedor
ORDER BY sla_otif_pct ASC, retraso_promesa_promedio_dias DESC;


-- ==============================================================================
-- 4. SLA DE PRODUCCIÓN (ADHERENCIA AL PLAN MAESTRO DE MANUFACTURA)
-- ==============================================================================

SELECT 
    COUNT(*) AS total_meses_producto,
    SUM(cantidad_planeada) AS total_unidades_planeadas,
    SUM(cantidad_real) AS total_unidades_reales,
    ROUND((SUM(cantidad_real)::numeric / SUM(cantidad_planeada) * 100), 2) AS adherencia_produccion_volumen_pct,
    COUNT(CASE WHEN cantidad_real >= cantidad_planeada THEN 1 END) AS metas_cumplidas_count,
    COUNT(CASE WHEN cantidad_real < cantidad_planeada THEN 1 END) AS metas_incumplidas_count,
    ROUND((COUNT(CASE WHEN cantidad_real >= cantidad_planeada THEN 1 END)::numeric / COUNT(*) * 100), 2) AS sla_cumplimiento_metas_pct
FROM public.plan_produccion;
