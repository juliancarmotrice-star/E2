-- ==============================================================================
-- PROYECTO E2 SAS - ÉNFASIS 2 (PRODUCCIÓN 4.0)
-- ARCHIVO: sql/03_vistas_analiticas_abc.sql
-- DESCRIPCIÓN: Creación de la vista dinámica de clasificación ABC de inventario (Pareto)
--              con columnas numéricas, tipo de rotación y columnas formateadas ($ COP y unidades).
-- ==============================================================================

-- 1. CREACIÓN O REEMPLAZO DE LA VISTA DINÁMICA ABC
CREATE OR REPLACE VIEW public.vista_clasificacion_abc AS
WITH periodo_analisis AS (
    -- Rango de días en el histórico de movimientos para anualizar con precisión
    SELECT 
        GREATEST(1, MAX(fecha) - MIN(fecha) + 1) AS dias_historial
    FROM public.movimientos_inventarios
),
consumo_sku AS (
    SELECT 
        m.sku,
        m.descripcion,
        m.categoria,
        m.costo_unitario,
        m.lead_time_declarado_dias,
        -- Salidas totales del historial
        COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'salida' THEN mov.cantidad ELSE 0 END), 0) AS unidades_consumidas_total,
        -- Anualización del consumo a 365 días
        ROUND(
            (COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'salida' THEN mov.cantidad ELSE 0 END), 0) * (365.0 / p.dias_historial))::numeric, 
            2
        ) AS consumo_anual_unidades,
        -- Valor de consumo anualizado en COP (Consumo Anual * Costo Unitario)
        ROUND(
            (COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'salida' THEN mov.cantidad ELSE 0 END), 0) * (365.0 / p.dias_historial) * m.costo_unitario)::numeric, 
            2
        ) AS valor_consumo_anual_cop
    FROM public.maestro_materiales m
    CROSS JOIN periodo_analisis p
    LEFT JOIN public.movimientos_inventarios mov ON m.sku = mov.sku
    WHERE m.sku NOT LIKE 'MP-9%' AND m.descripcion NOT LIKE '%(dup)%'
    GROUP BY m.sku, m.descripcion, m.categoria, m.costo_unitario, m.lead_time_declarado_dias, p.dias_historial
),
total_global AS (
    SELECT SUM(valor_consumo_anual_cop) AS total_valor_anual FROM consumo_sku
),
ranking_abc AS (
    SELECT 
        c.*,
        ROUND((c.valor_consumo_anual_cop / tg.total_valor_anual * 100)::numeric, 4) AS pct_participacion_individual,
        ROUND((SUM(c.valor_consumo_anual_cop) OVER (ORDER BY c.valor_consumo_anual_cop DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / tg.total_valor_anual * 100)::numeric, 2) AS pct_acumulado_valor
    FROM consumo_sku c
    CROSS JOIN total_global tg
)
SELECT 
    r.sku,
    r.descripcion,
    r.categoria,
    -- Columnas numéricas (y alias flexibles para consultas)
    r.costo_unitario,
    r.lead_time_declarado_dias,
    r.unidades_consumidas_total,
    r.unidades_consumidas_total AS consumo_unidades_total,
    r.consumo_anual_unidades,
    r.valor_consumo_anual_cop,
    r.valor_consumo_anual_cop AS valor_consumo_cop,
    r.pct_participacion_individual,
    r.pct_acumulado_valor,
    r.pct_acumulado_valor AS pct_participacion_acumulada,
    -- Clasificación Pareto 80-15-5
    CASE 
        WHEN r.pct_acumulado_valor <= 80.00 THEN 'A'
        WHEN LAG(r.pct_acumulado_valor, 1, 0) OVER (ORDER BY r.valor_consumo_anual_cop DESC) < 80.00 AND r.pct_acumulado_valor > 80.00 THEN 'A'
        WHEN r.pct_acumulado_valor <= 95.00 THEN 'B'
        WHEN LAG(r.pct_acumulado_valor, 1, 0) OVER (ORDER BY r.valor_consumo_anual_cop DESC) < 95.00 AND r.pct_acumulado_valor > 95.00 THEN 'B'
        ELSE 'C'
    END AS clasificacion_abc,
    -- Tipo de rotación
    CASE 
        WHEN r.unidades_consumidas_total > 0 THEN 'Activo (En Rotación)'
        ELSE 'Inactivo (Plata Muerta)'
    END AS tipo_rotacion,
    -- Columnas formateadas para lectura visual ejecutiva
    '$ ' || TO_CHAR(r.costo_unitario, 'FM999,999,999,990') AS costo_unitario_formato,
    TO_CHAR(r.unidades_consumidas_total, 'FM999,999,990.00') || ' und' AS consumo_total_formato,
    TO_CHAR(r.consumo_anual_unidades, 'FM999,999,990.00') || ' und' AS consumo_anual_formato,
    '$ ' || TO_CHAR(r.valor_consumo_anual_cop, 'FM999,999,999,990') || ' COP' AS valor_consumo_anual_formato,
    '$ ' || TO_CHAR(r.valor_consumo_anual_cop, 'FM999,999,999,990') || ' COP' AS valor_consumo_formato,
    TO_CHAR(r.pct_participacion_individual, 'FM990.00') || ' %' AS pct_participacion_formato,
    TO_CHAR(r.pct_acumulado_valor, 'FM990.00') || ' %' AS pct_acumulado_formato,
    TO_CHAR(r.pct_acumulado_valor, 'FM990.00') || ' %' AS pct_participacion_acumulada_formato
FROM ranking_abc r
ORDER BY r.valor_consumo_anual_cop DESC;


-- ==============================================================================
-- 2. CONSULTAS DE PRUEBA Y CONSUMO CON FORMATEO
-- ==============================================================================

-- A. Resumen ejecutivo de distribución ABC formateado
SELECT 
    clasificacion_abc,
    COUNT(*) AS total_skus,
    TO_CHAR(ROUND((COUNT(*)::numeric / (SELECT count(*) FROM public.vista_clasificacion_abc) * 100), 2), 'FM990.00') || ' %' AS pct_skus,
    '$ ' || TO_CHAR(SUM(valor_consumo_anual_cop), 'FM999,999,999,990') || ' COP' AS valor_consumo_total_cop,
    TO_CHAR(SUM(pct_participacion_individual), 'FM990.00') || ' %' AS pct_valor_total
FROM public.vista_clasificacion_abc
GROUP BY clasificacion_abc
ORDER BY clasificacion_abc;

-- B. Top 30 SKUs Clase A formateados
SELECT 
    sku,
    descripcion,
    categoria,
    costo_unitario_formato,
    consumo_anual_formato,
    valor_consumo_anual_formato,
    pct_participacion_formato,
    pct_acumulado_formato
FROM public.vista_clasificacion_abc
WHERE clasificacion_abc = 'A'
ORDER BY valor_consumo_anual_cop DESC;
