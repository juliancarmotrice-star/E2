-- ==============================================================================
-- PROYECTO E2 SAS - ÉNFASIS 2 (PRODUCCIÓN 4.0)
-- ARCHIVO: sql/03_vistas_analiticas_abc.sql
-- DESCRIPCIÓN: Vista dinámica de clasificación ABC de inventarios por consumo anualizado
--              Criterio: Valor Consumo = Consumo Anual * Costo Unitario
--              Cortes: A <= 80% | B <= 95% | C > 95%
-- ==============================================================================

-- 1. CREACIÓN O REEMPLAZO DE LA VISTA DINÁMICA ABC
CREATE OR REPLACE VIEW public.vista_clasificacion_abc AS
WITH periodo_analisis AS (
    -- Calcula el rango real de días en el histórico de movimientos para anualizar con precisión
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
        -- Valor de consumo anualizado en COP
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
    r.costo_unitario,
    r.lead_time_declarado_dias,
    r.unidades_consumidas_total,
    r.consumo_anual_unidades,
    r.valor_consumo_anual_cop,
    r.pct_participacion_individual,
    r.pct_acumulado_valor,
    CASE 
        WHEN r.pct_acumulado_valor <= 80.00 THEN 'A'
        WHEN LAG(r.pct_acumulado_valor, 1, 0) OVER (ORDER BY r.valor_consumo_anual_cop DESC) < 80.00 AND r.pct_acumulado_valor > 80.00 THEN 'A'
        WHEN r.pct_acumulado_valor <= 95.00 THEN 'B'
        WHEN LAG(r.pct_acumulado_valor, 1, 0) OVER (ORDER BY r.valor_consumo_anual_cop DESC) < 95.00 AND r.pct_acumulado_valor > 95.00 THEN 'B'
        ELSE 'C'
    END AS clasificacion_abc
FROM ranking_abc r
ORDER BY r.valor_consumo_anual_cop DESC;


-- ==============================================================================
-- 2. CONSULTAS DE PRUEBA Y CONSUMO
-- ==============================================================================

-- A. Resumen de distribución de SKUs por clasificación ABC
SELECT 
    clasificacion_abc,
    COUNT(*) AS total_skus,
    ROUND((COUNT(*)::numeric / 420 * 100), 2) AS pct_skus,
    SUM(valor_consumo_anual_cop) AS valor_consumo_total_cop,
    ROUND(SUM(pct_participacion_individual), 2) AS pct_valor_total
FROM public.vista_clasificacion_abc
GROUP BY clasificacion_abc
ORDER BY clasificacion_abc;

-- B. Top SKUs Estratégicos Clase A
SELECT 
    sku,
    descripcion,
    categoria,
    costo_unitario,
    consumo_anual_unidades,
    valor_consumo_anual_cop,
    pct_participacion_individual,
    pct_acumulado_valor
FROM public.vista_clasificacion_abc
WHERE clasificacion_abc = 'A'
ORDER BY valor_consumo_anual_cop DESC;
