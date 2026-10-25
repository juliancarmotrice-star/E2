-- =============================================================================
-- SQL MIGRATION: 05_instrumentacion_y_bitacoras.sql
-- Proyecto: Énfasis II · Producción 4.0 · E2 SAS
-- Referencia: Diapositivas B4_02 (Del Archivo al Registro e Instrumentación)
-- =============================================================================

-- 1. Bitácora de Ingesta y Carga de Datos (Rendición de Cuentas B4.02)
-- Registra cada intento de carga con filas leídas, aceptadas, rechazadas y motivos.
CREATE TABLE IF NOT EXISTS public.bitacora_cargas (
    id BIGSERIAL PRIMARY KEY,
    fecha_carga TIMESTAMPTZ DEFAULT NOW(),
    archivo_origen TEXT NOT NULL,
    tabla_destino TEXT NOT NULL,
    filas_leidas INT NOT NULL DEFAULT 0,
    filas_cargadas INT NOT NULL DEFAULT 0,
    filas_rechazadas INT NOT NULL DEFAULT 0,
    detalle_rechazos JSONB DEFAULT '[]'::jsonb,
    es_idempotente BOOLEAN DEFAULT TRUE,
    duracion_ms INT DEFAULT 0,
    usuario_carga TEXT DEFAULT 'SISTEMA_INGESTA_B4'
);

-- 2. Bitácora de Corridas del Sistema e Instrumentación Telemetría (Slide 10-11 B4.02)
-- Registra el desempeño autónomo del sistema: trabajo ahorrado, paradas activadas y decisiones humanas.
CREATE TABLE IF NOT EXISTS public.bitacora_corridas (
    corrida_id TEXT PRIMARY KEY,
    fecha_corrida TIMESTAMPTZ DEFAULT NOW(),
    total_propuestas INT NOT NULL DEFAULT 0,
    inversion_total_cop NUMERIC DEFAULT 0,
    conteo_paradas JSONB DEFAULT '{}'::jsonb,
    propuestas_aprobadas INT DEFAULT 0,
    propuestas_rechazadas INT DEFAULT 0,
    duracion_ms INT DEFAULT 0,
    usuario TEXT DEFAULT 'Operador Producción 4.0'
);

-- Índices de consulta rápida
CREATE INDEX IF NOT EXISTS idx_bitacora_cargas_fecha ON public.bitacora_cargas(fecha_carga DESC);
CREATE INDEX IF NOT EXISTS idx_bitacora_corridas_fecha ON public.bitacora_corridas(fecha_corrida DESC);
