-- ==============================================================================
-- PROYECTO E2 SAS - ÉNFASIS 2 (PRODUCCIÓN 4.0)
-- ARCHIVO: sql/04_vistas_calculo_eoq_rop.sql
-- DESCRIPCIÓN: Vista analítica determinística de Lote Económico (EOQ), Stock de 
--              Seguridad (SS) y Punto de Reorden (ROP) con Nivel de Servicio al 95% (Z = 1.64485)
--              Incluye columnas numéricas y columnas formateadas ($ COP, separadores de miles y unidades).
-- ==============================================================================

-- 1. CREACIÓN O REEMPLAZO DE LA VISTA DINÁMICA DE REPOSICIÓN (EOQ & ROP)
CREATE OR REPLACE VIEW public.vista_calculo_eoq_rop AS
WITH periodo_analisis AS (
    -- Rango de días en el histórico de movimientos para anualización precisa (Jul 2024 - Mar 2026: 639 días)
    SELECT 
        GREATEST(1, MAX(fecha) - MIN(fecha) + 1) AS dias_historial
    FROM public.movimientos_inventarios
),
consumo_diario AS (
    -- Agrupación del consumo diario por SKU (salidas efectivas del Kardex)
    SELECT 
        sku,
        fecha,
        SUM(cantidad) AS consumo_dia
    FROM public.movimientos_inventarios
    WHERE tipo_movimiento = 'salida'
    GROUP BY sku, fecha
),
stats_demanda AS (
    -- Cálculo de Media y Desviación Estándar de la Demanda Diaria y Anualizada
    SELECT 
        m.sku,
        COALESCE(SUM(cd.consumo_dia), 0) AS total_consumo,
        COALESCE(SUM(cd.consumo_dia * cd.consumo_dia), 0) AS sum_sq_consumo,
        p.dias_historial,
        COALESCE(SUM(cd.consumo_dia), 0) / p.dias_historial AS d_promedio_diario,
        ROUND((COALESCE(SUM(cd.consumo_dia), 0) * (365.0 / p.dias_historial))::numeric, 2) AS d_anual,
        CASE 
            WHEN COALESCE(SUM(cd.consumo_dia), 0) = 0 THEN 0
            ELSE SQRT(GREATEST(0, (COALESCE(SUM(cd.consumo_dia * cd.consumo_dia), 0) - (COALESCE(SUM(cd.consumo_dia), 0) * COALESCE(SUM(cd.consumo_dia), 0) / p.dias_historial)) / (p.dias_historial - 1)))
        END AS sigma_d_diario
    FROM public.maestro_materiales m
    CROSS JOIN periodo_analisis p
    LEFT JOIN consumo_diario cd ON m.sku = cd.sku
    WHERE m.sku NOT LIKE 'MP-9%' AND m.descripcion NOT LIKE '%(dup)%'
    GROUP BY m.sku, p.dias_historial
),
stats_lead_time AS (
    -- Lead Time real promedio y variabilidad por SKU basado en órdenes de compra cerradas
    SELECT 
        m.sku,
        COUNT(oc.orden_compra) AS total_oc_cerradas,
        COALESCE(AVG(oc.fecha_recepcion - oc.fecha_pedido), m.lead_time_declarado_dias) AS lt_promedio_dias,
        COALESCE(STDDEV_SAMP(oc.fecha_recepcion - oc.fecha_pedido), 0) AS sigma_lt_dias
    FROM public.maestro_materiales m
    LEFT JOIN public.ordenes_compra oc ON m.sku = oc.sku AND oc.fecha_recepcion IS NOT NULL
    WHERE m.sku NOT LIKE 'MP-9%' AND m.descripcion NOT LIKE '%(dup)%'
    GROUP BY m.sku, m.lead_time_declarado_dias
),
kardex_saldo AS (
    -- Reconciliación del saldo final teórico en Kardex
    SELECT 
        m.sku,
        (COALESCE(ii.stock_inicial, 0) + 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'entrada' THEN mov.cantidad ELSE 0 END), 0) - 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'salida' THEN mov.cantidad ELSE 0 END), 0) + 
         COALESCE(SUM(CASE WHEN mov.tipo_movimiento = 'ajuste' THEN mov.cantidad ELSE 0 END), 0)) AS stock_actual_kardex
    FROM public.maestro_materiales m
    LEFT JOIN public.inventario_inicial ii ON m.sku = ii.sku
    LEFT JOIN public.movimientos_inventarios mov ON m.sku = mov.sku
    WHERE m.sku NOT LIKE 'MP-9%' AND m.descripcion NOT LIKE '%(dup)%'
    GROUP BY m.sku, ii.stock_inicial
),
ordenes_transito AS (
    -- Órdenes de compra abiertas (pendientes de recepción por el proveedor)
    SELECT 
        sku,
        COALESCE(SUM(cantidad), 0) AS ordenes_en_transito
    FROM public.ordenes_compra
    WHERE fecha_recepcion IS NULL
    GROUP BY sku
),
calculo_base AS (
    SELECT 
        m.sku,
        m.descripcion,
        m.categoria,
        m.costo_unitario,
        m.lead_time_declarado_dias,
        COALESCE(abc.clasificacion_abc, 'C') AS clasificacion_abc,
        sd.total_consumo AS unidades_consumidas_total,
        sd.d_anual AS demanda_anual_unidades,
        ROUND(sd.d_promedio_diario::numeric, 4) AS demanda_diaria_promedio,
        ROUND(sd.sigma_d_diario::numeric, 4) AS sigma_demanda_diaria,
        slt.total_oc_cerradas,
        ROUND(slt.lt_promedio_dias::numeric, 2) AS lead_time_promedio_dias,
        ROUND(slt.sigma_lt_dias::numeric, 2) AS sigma_lead_time_dias,
        '95.0%'::varchar AS nivel_servicio_objetivo,
        1.64485::numeric AS factor_z,
        80000.0::numeric AS costo_emision_orden_s_cop,
        25.0::numeric AS tasa_mantenimiento_anual_h_pct,
        ROUND((m.costo_unitario * 0.25)::numeric, 2) AS costo_mantenimiento_unitario_h_cop,
        -- FÓRMULA EOQ: √( (2 * D * S) / H ) donde H = 0.25 * Costo
        CASE 
            WHEN sd.d_anual = 0 OR m.costo_unitario = 0 THEN 0
            ELSE CEIL(SQRT((2.0 * sd.d_anual * 80000.0) / (0.25 * m.costo_unitario)))
        END AS eoq_lote_economico,
        -- DESVIACIÓN ESTÁNDAR COMBINADA EN EL LEAD TIME: σ_DL = √( L * σ_d^2 + d^2 * σ_L^2 )
        CASE 
            WHEN sd.d_anual = 0 THEN 0
            ELSE ROUND(SQRT((slt.lt_promedio_dias * (sd.sigma_d_diario * sd.sigma_d_diario)) + ((sd.d_promedio_diario * sd.d_promedio_diario) * (slt.sigma_lt_dias * slt.sigma_lt_dias)))::numeric, 4)
        END AS sigma_periodo_entrega_dl,
        -- STOCK DE SEGURIDAD (SS): Z * σ_DL (Z = 1.64485 para 95% de nivel de servicio)
        CASE 
            WHEN sd.d_anual = 0 THEN 0
            ELSE CEIL(1.64485 * SQRT((slt.lt_promedio_dias * (sd.sigma_d_diario * sd.sigma_d_diario)) + ((sd.d_promedio_diario * sd.d_promedio_diario) * (slt.sigma_lt_dias * slt.sigma_lt_dias))))
        END AS stock_seguridad_ss,
        -- DEMANDA ESPERADA EN TIEMPO DE ENTREGA: d * L
        ROUND((sd.d_promedio_diario * slt.lt_promedio_dias)::numeric, 2) AS demanda_durante_lead_time,
        -- PUNTO DE REORDEN (ROP): (d * L) + SS
        CASE 
            WHEN sd.d_anual = 0 THEN 0
            ELSE CEIL((sd.d_promedio_diario * slt.lt_promedio_dias) + (1.64485 * SQRT((slt.lt_promedio_dias * (sd.sigma_d_diario * sd.sigma_d_diario)) + ((sd.d_promedio_diario * sd.d_promedio_diario) * (slt.sigma_lt_dias * slt.sigma_lt_dias)))))
        END AS punto_reorden_rop,
        -- Saldo en Kardex, Órdenes Abiertas y Posición de Inventario
        COALESCE(k.stock_actual_kardex, 0) AS stock_actual_kardex,
        COALESCE(t.ordenes_en_transito, 0) AS ordenes_en_transito,
        (COALESCE(k.stock_actual_kardex, 0) + COALESCE(t.ordenes_en_transito, 0)) AS posicion_inventario
    FROM public.maestro_materiales m
    JOIN stats_demanda sd ON m.sku = sd.sku
    JOIN stats_lead_time slt ON m.sku = slt.sku
    LEFT JOIN public.vista_clasificacion_abc abc ON m.sku = abc.sku
    LEFT JOIN kardex_saldo k ON m.sku = k.sku
    LEFT JOIN ordenes_transito t ON m.sku = t.sku
    WHERE m.sku NOT LIKE 'MP-9%' AND m.descripcion NOT LIKE '%(dup)%'
)
SELECT 
    cb.sku,
    cb.descripcion,
    cb.categoria,
    cb.clasificacion_abc,
    -- Métricas Numéricas de Entrada y Costos
    cb.costo_unitario,
    '$ ' || TO_CHAR(cb.costo_unitario, 'FM999,999,999,990') AS costo_unitario_formato,
    cb.lead_time_declarado_dias,
    cb.lead_time_promedio_dias,
    cb.sigma_lead_time_dias,
    cb.unidades_consumidas_total,
    cb.demanda_anual_unidades,
    TO_CHAR(cb.demanda_anual_unidades, 'FM999,999,990.00') || ' und' AS demanda_anual_formato,
    cb.demanda_diaria_promedio,
    cb.sigma_demanda_diaria,
    cb.nivel_servicio_objetivo,
    cb.factor_z,
    cb.costo_emision_orden_s_cop,
    '$ ' || TO_CHAR(cb.costo_emision_orden_s_cop, 'FM999,999,999,990') AS costo_emision_orden_formato,
    cb.tasa_mantenimiento_anual_h_pct,
    cb.costo_mantenimiento_unitario_h_cop,
    '$ ' || TO_CHAR(cb.costo_mantenimiento_unitario_h_cop, 'FM999,999,999,990.00') AS costo_mantenimiento_unitario_formato,
    -- Cálculos de Lote Económico (EOQ)
    cb.eoq_lote_economico,
    TO_CHAR(cb.eoq_lote_economico, 'FM999,999') || ' und' AS eoq_formato,
    CASE 
        WHEN cb.eoq_lote_economico = 0 THEN 0
        ELSE ROUND((cb.demanda_anual_unidades / cb.eoq_lote_economico)::numeric, 2)
    END AS numero_ordenes_anuales_optimo,
    CASE 
        WHEN cb.demanda_anual_unidades = 0 OR cb.eoq_lote_economico = 0 THEN 0
        ELSE ROUND(((365.0 * cb.eoq_lote_economico) / cb.demanda_anual_unidades)::numeric, 1)
    END AS frecuencia_pedido_dias,
    -- Cálculos de Stock de Seguridad (SS) y Punto de Reorden (ROP)
    cb.demanda_durante_lead_time,
    cb.sigma_periodo_entrega_dl,
    cb.stock_seguridad_ss,
    TO_CHAR(cb.stock_seguridad_ss, 'FM999,999') || ' und' AS stock_seguridad_formato,
    ROUND((cb.stock_seguridad_ss * cb.costo_unitario)::numeric, 2) AS valor_stock_seguridad_cop,
    '$ ' || TO_CHAR(cb.stock_seguridad_ss * cb.costo_unitario, 'FM999,999,999,990') || ' COP' AS valor_stock_seguridad_formato,
    cb.punto_reorden_rop,
    TO_CHAR(cb.punto_reorden_rop, 'FM999,999') || ' und' AS punto_reorden_formato,
    ROUND((cb.punto_reorden_rop * cb.costo_unitario)::numeric, 2) AS valor_rop_cop,
    '$ ' || TO_CHAR(cb.punto_reorden_rop * cb.costo_unitario, 'FM999,999,999,990') || ' COP' AS valor_rop_formato,
    (cb.punto_reorden_rop + cb.eoq_lote_economico) AS stock_maximo_sugerido,
    TO_CHAR(cb.punto_reorden_rop + cb.eoq_lote_economico, 'FM999,999') || ' und' AS stock_maximo_formato,
    -- Estado Físico y Posición de Inventario
    cb.stock_actual_kardex,
    TO_CHAR(cb.stock_actual_kardex, 'FM999,999,990.00') || ' und' AS stock_actual_formato,
    cb.ordenes_en_transito,
    TO_CHAR(cb.ordenes_en_transito, 'FM999,999,990') || ' und' AS ordenes_transito_formato,
    cb.posicion_inventario,
    TO_CHAR(cb.posicion_inventario, 'FM999,999,990.00') || ' und' AS posicion_inventario_formato,
    ROUND((cb.posicion_inventario * cb.costo_unitario)::numeric, 2) AS valor_posicion_cop,
    '$ ' || TO_CHAR(cb.posicion_inventario * cb.costo_unitario, 'FM999,999,999,990') || ' COP' AS valor_posicion_formato,
    -- Semáforo de Reposición Dinámico
    CASE 
        WHEN cb.demanda_anual_unidades = 0 THEN '🔵 Plata Muerta'
        WHEN cb.posicion_inventario <= cb.stock_seguridad_ss THEN '🔴 Quiebre Inminente'
        WHEN cb.posicion_inventario <= cb.punto_reorden_rop THEN '🟡 Reorden Requerido'
        WHEN cb.posicion_inventario <= (cb.punto_reorden_rop + cb.eoq_lote_economico) THEN '🟢 Zona Segura'
        ELSE '🔵 Sobreabastecimiento'
    END AS estado_semaforo,
    -- Disparador y Cantidad Sugerida a Pedir
    CASE 
        WHEN cb.demanda_anual_unidades > 0 AND cb.posicion_inventario <= cb.punto_reorden_rop THEN TRUE
        ELSE FALSE
    END AS requiere_orden_compra,
    CASE 
        WHEN cb.demanda_anual_unidades > 0 AND cb.posicion_inventario <= cb.punto_reorden_rop THEN 
            GREATEST(cb.eoq_lote_economico, (cb.punto_reorden_rop + cb.eoq_lote_economico) - cb.posicion_inventario)
        ELSE 0
    END AS cantidad_sugerida_pedir,
    TO_CHAR(
        CASE 
            WHEN cb.demanda_anual_unidades > 0 AND cb.posicion_inventario <= cb.punto_reorden_rop THEN 
                GREATEST(cb.eoq_lote_economico, (cb.punto_reorden_rop + cb.eoq_lote_economico) - cb.posicion_inventario)
            ELSE 0
        END, 
        'FM999,999,990'
    ) || ' und' AS cantidad_sugerida_pedir_formato,
    -- Acción Operativa Recomendada
    CASE 
        WHEN cb.demanda_anual_unidades = 0 THEN 'Liquidación / Depuración de Catálogo (Sin Movimiento)'
        WHEN cb.posicion_inventario <= cb.stock_seguridad_ss THEN 'EMITIR ORDEN URGENTE: Posición bajo Stock de Seguridad'
        WHEN cb.posicion_inventario <= cb.punto_reorden_rop THEN 'EMITIR ORDEN DE COMPRA: Posición alcanzó Punto de Reorden'
        WHEN cb.posicion_inventario <= (cb.punto_reorden_rop + cb.eoq_lote_economico) THEN 'OPERACIÓN NORMAL: No requiere reposición en este ciclo'
        ELSE 'SUSPENDER COMPRAS: Exceso de inventario sobre stock máximo'
    END AS accion_operativa_sugerida
FROM calculo_base cb
ORDER BY 
    CASE 
        WHEN cb.demanda_anual_unidades = 0 THEN 5
        WHEN cb.posicion_inventario <= cb.stock_seguridad_ss THEN 1
        WHEN cb.posicion_inventario <= cb.punto_reorden_rop THEN 2
        WHEN cb.posicion_inventario <= (cb.punto_reorden_rop + cb.eoq_lote_economico) THEN 3
        ELSE 4
    END,
    cb.demanda_anual_unidades DESC;


-- ==============================================================================
-- 2. CONSULTAS DE PRUEBA Y CONSUMO CON FORMATEO EJECUTIVO
-- ==============================================================================

-- A. Resumen ejecutivo de distribución del Semáforo de Reposición
SELECT 
    estado_semaforo,
    COUNT(*) AS total_skus,
    TO_CHAR(ROUND((COUNT(*)::numeric / (SELECT count(*) FROM public.vista_calculo_eoq_rop) * 100), 2), 'FM990.00') || ' %' AS pct_skus,
    '$ ' || TO_CHAR(SUM(valor_posicion_cop), 'FM999,999,999,990') || ' COP' AS valor_posicion_total_cop
FROM public.vista_calculo_eoq_rop
GROUP BY estado_semaforo
ORDER BY total_skus DESC;

-- B. Top 20 SKUs con requerimiento urgente de Orden de Compra (Críticos Clase A y B)
SELECT 
    sku,
    descripcion,
    categoria,
    clasificacion_abc,
    costo_unitario_formato,
    demanda_anual_formato,
    stock_actual_formato,
    posicion_inventario_formato,
    stock_seguridad_formato,
    punto_reorden_formato,
    eoq_formato,
    cantidad_sugerida_pedir_formato,
    valor_posicion_formato,
    estado_semaforo,
    accion_operativa_sugerida
FROM public.vista_calculo_eoq_rop
WHERE requiere_orden_compra = TRUE
ORDER BY 
    CASE WHEN clasificacion_abc = 'A' THEN 1 WHEN clasificacion_abc = 'B' THEN 2 ELSE 3 END,
    demanda_anual_unidades DESC
LIMIT 20;

-- C. Resumen de políticas por Categoría de Material con totales en millones/pesos
SELECT 
    categoria,
    COUNT(*) AS total_skus_activos,
    COUNT(CASE WHEN requiere_orden_compra THEN 1 END) AS skus_a_comprar,
    ROUND(AVG(lead_time_promedio_dias)::numeric, 1) || ' d' AS lead_time_promedio,
    TO_CHAR(SUM(demanda_anual_unidades), 'FM999,999,990') || ' und' AS demanda_anual_total,
    '$ ' || TO_CHAR(SUM(valor_stock_seguridad_cop), 'FM999,999,999,990') || ' COP' AS valor_stock_seguridad_total,
    '$ ' || TO_CHAR(SUM(valor_rop_cop), 'FM999,999,999,990') || ' COP' AS valor_rop_total
FROM public.vista_calculo_eoq_rop
WHERE demanda_anual_unidades > 0
GROUP BY categoria
ORDER BY SUM(demanda_anual_unidades) DESC;
