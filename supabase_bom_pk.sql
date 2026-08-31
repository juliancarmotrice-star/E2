-- ==============================================================================
-- Proyecto E2 SAS - Énfasis 2 (Producción 4.0)
-- Script: Definición de Llave Primaria para la tabla 'bom'
-- ==============================================================================

-- OPCIÓN 1 (Recomendada con Columna 'id_bom' como Llave Primaria):
-- Combina el identificador de producto y el SKU de la materia prima.
-- Utiliza una columna generada 'STORED' para que se mantenga siempre sincronizada
-- y corresponda exactamente con la columna 'ID_bom' de bom.csv.

-- Paso 1: Si ya existiera alguna constraint previa, la eliminamos de forma segura
ALTER TABLE public.bom DROP CONSTRAINT IF EXISTS bom_pkey;

-- Paso 2A: Si prefieres la combinación con el CÓDIGO de producto (ej: 'PT-ESC-STD_MP-0019'):
ALTER TABLE public.bom 
ADD COLUMN IF NOT EXISTS id_bom text 
GENERATED ALWAYS AS (producto || '_' || sku_material) STORED;

-- Asignar id_bom como Primary Key:
ALTER TABLE public.bom ADD CONSTRAINT bom_pkey PRIMARY KEY (id_bom);

-- ==============================================================================
-- OPCIÓN 2 (Alternativa: Llave Primaria Compuesta estándar en PostgreSQL):
-- Sin agregar columnas adicionales, define la clave primaria sobre las 2 columnas existentes.
-- ==============================================================================
/*
ALTER TABLE public.bom DROP CONSTRAINT IF EXISTS bom_pkey;
ALTER TABLE public.bom ADD CONSTRAINT bom_pkey PRIMARY KEY (producto, sku_material);
*/

-- ==============================================================================
-- OPCIÓN 3 (Si deseas la combinación literal con 'nombre_producto'):
-- (ej: 'Escritorio estándar_MP-0019')
-- ==============================================================================
/*
ALTER TABLE public.bom DROP CONSTRAINT IF EXISTS bom_pkey;
ALTER TABLE public.bom 
ADD COLUMN IF NOT EXISTS id_bom text 
GENERATED ALWAYS AS (nombre_producto || '_' || sku_material) STORED;
ALTER TABLE public.bom ADD CONSTRAINT bom_pkey PRIMARY KEY (id_bom);
*/
