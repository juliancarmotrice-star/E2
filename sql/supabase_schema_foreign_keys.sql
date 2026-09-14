-- ==============================================================================
-- PROYECTO E2 SAS - GESTIÓN DE INVENTARIOS Y REPOSICIÓN (PRODUCCIÓN 4.0)
-- Script Completo: Catálogo de Productos, Llaves Primarias, Llaves Foráneas e Índices
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. CATÁLOGO MAESTRO DE PRODUCTOS TERMINADOS (Entidad Maestra de PT)
-- Necesaria para normalizar la relación 1:N con 'bom' y 1:N con 'plan_produccion'
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.maestro_productos (
    producto text PRIMARY KEY,
    nombre_producto text NOT NULL
);

-- Deshabilitar RLS para permitir transaccionalidad
ALTER TABLE public.maestro_productos DISABLE ROW LEVEL SECURITY;

-- Poblar catálogo de los 18 Productos Terminados de E2 SAS
INSERT INTO public.maestro_productos (producto, nombre_producto) VALUES
    ('PT-ESC-STD', 'Escritorio estándar'),
    ('PT-ESC-EJE', 'Escritorio ejecutivo'),
    ('PT-ESC-L', 'Escritorio en L'),
    ('PT-ESC-GER', 'Escritorio gerencial'),
    ('PT-ARCH-4G', 'Archivador 4 gavetas'),
    ('PT-ARCH-2G', 'Archivador 2 gavetas'),
    ('PT-ARCH-ROD', 'Archivador rodante'),
    ('PT-EST-5N', 'Estantería 5 niveles'),
    ('PT-EST-3N', 'Estantería 3 niveles'),
    ('PT-EST-IND', 'Estantería industrial'),
    ('PT-SIL-OPE', 'Silla operativa'),
    ('PT-SIL-INT', 'Silla interlocutora'),
    ('PT-SIL-GER', 'Silla gerencial'),
    ('PT-MOD-REC', 'Módulo recepción'),
    ('PT-MOD-CAL', 'Módulo call center'),
    ('PT-LOCK-12', 'Lockers 12 puertas'),
    ('PT-MESA-JUN', 'Mesa de juntas'),
    ('PT-BIB-MET', 'Biblioteca metálica')
ON CONFLICT (producto) DO UPDATE SET nombre_producto = EXCLUDED.nombre_producto;


-- ------------------------------------------------------------------------------
-- 2. ASEGURAR LLAVES PRIMARIAS (PRIMARY KEYS)
-- ------------------------------------------------------------------------------

-- 2.1 Maestro de Materiales (Catálogo de Materias Primas)
ALTER TABLE public.maestro_materiales DROP CONSTRAINT IF EXISTS maestro_materiales_pkey CASCADE;
ALTER TABLE public.maestro_materiales ADD CONSTRAINT maestro_materiales_pkey PRIMARY KEY (sku);

-- 2.2 Órdenes de Compra (Histórico de adquisiciones de MP)
ALTER TABLE public.ordenes_compra DROP CONSTRAINT IF EXISTS ordenes_compra_pkey CASCADE;
ALTER TABLE public.ordenes_compra ADD CONSTRAINT ordenes_compra_pkey PRIMARY KEY (orden_compra);

-- 2.3 Inventario Inicial (Saldo base por material)
ALTER TABLE public.inventario_inicial DROP CONSTRAINT IF EXISTS inventario_inicial_pkey CASCADE;
ALTER TABLE public.inventario_inicial ADD CONSTRAINT inventario_inicial_pkey PRIMARY KEY (sku);

-- 2.4 Conteo Físico (Auditoría física de inventario)
ALTER TABLE public.conteo_fisico DROP CONSTRAINT IF EXISTS conteo_fisico_pkey CASCADE;
ALTER TABLE public.conteo_fisico ADD CONSTRAINT conteo_fisico_pkey PRIMARY KEY (sku);

-- 2.5 Plan de Producción (Plan vs Real mensual por Producto)
ALTER TABLE public.plan_produccion DROP CONSTRAINT IF EXISTS plan_produccion_pkey CASCADE;
ALTER TABLE public.plan_produccion ADD CONSTRAINT plan_produccion_pkey PRIMARY KEY (periodo, producto);

-- 2.6 Bill of Materials (BOM - Lista de Materiales por Producto)
ALTER TABLE public.bom DROP CONSTRAINT IF EXISTS bom_pkey CASCADE;
ALTER TABLE public.bom ADD COLUMN IF NOT EXISTS id_bom text GENERATED ALWAYS AS (producto || '_' || sku_material) STORED;
ALTER TABLE public.bom ADD CONSTRAINT bom_pkey PRIMARY KEY (id_bom);


-- ------------------------------------------------------------------------------
-- 3. CREACIÓN DE LLAVES FORÁNEAS (FOREIGN KEYS)
-- ------------------------------------------------------------------------------

-- A. RELACIONES HACIA MAESTRO DE MATERIALES (sku)
-- 3.1 Movimientos de Inventario (Kardex) -> Maestro de Materiales
ALTER TABLE public.movimientos_inventarios DROP CONSTRAINT IF EXISTS fk_movimientos_maestro;
ALTER TABLE public.movimientos_inventarios 
ADD CONSTRAINT fk_movimientos_maestro 
FOREIGN KEY (sku) REFERENCES public.maestro_materiales(sku) 
ON UPDATE CASCADE ON DELETE RESTRICT;

-- 3.2 Órdenes de Compra -> Maestro de Materiales
ALTER TABLE public.ordenes_compra DROP CONSTRAINT IF EXISTS fk_ordenes_compra_maestro;
ALTER TABLE public.ordenes_compra 
ADD CONSTRAINT fk_ordenes_compra_maestro 
FOREIGN KEY (sku) REFERENCES public.maestro_materiales(sku) 
ON UPDATE CASCADE ON DELETE RESTRICT;

-- 3.3 Lista de Materiales (BOM) -> Maestro de Materiales (Insumos/Materias Primas)
ALTER TABLE public.bom DROP CONSTRAINT IF EXISTS fk_bom_maestro;
ALTER TABLE public.bom 
ADD CONSTRAINT fk_bom_maestro 
FOREIGN KEY (sku_material) REFERENCES public.maestro_materiales(sku) 
ON UPDATE CASCADE ON DELETE RESTRICT;

-- 3.4 Inventario Inicial -> Maestro de Materiales
ALTER TABLE public.inventario_inicial DROP CONSTRAINT IF EXISTS fk_inv_inicial_maestro;
ALTER TABLE public.inventario_inicial 
ADD CONSTRAINT fk_inv_inicial_maestro 
FOREIGN KEY (sku) REFERENCES public.maestro_materiales(sku) 
ON UPDATE CASCADE ON DELETE RESTRICT;

-- 3.5 Conteo Físico -> Maestro de Materiales
ALTER TABLE public.conteo_fisico DROP CONSTRAINT IF EXISTS fk_conteo_fisico_maestro;
ALTER TABLE public.conteo_fisico 
ADD CONSTRAINT fk_conteo_fisico_maestro 
FOREIGN KEY (sku) REFERENCES public.maestro_materiales(sku) 
ON UPDATE CASCADE ON DELETE RESTRICT;

-- 3.6 Inventario Bodega Jefe -> Maestro de Materiales
ALTER TABLE public."inventario_bodega_JEFE" DROP CONSTRAINT IF EXISTS fk_bodega_jefe_maestro;
ALTER TABLE public."inventario_bodega_JEFE" 
ADD CONSTRAINT fk_bodega_jefe_maestro 
FOREIGN KEY (codigo) REFERENCES public.maestro_materiales(sku) 
ON UPDATE CASCADE ON DELETE RESTRICT;


-- B. RELACIONES DE PRODUCTOS TERMINADOS (producto)
-- 3.7 Plan de Producción -> Maestro de Productos
ALTER TABLE public.plan_produccion DROP CONSTRAINT IF EXISTS fk_plan_producto;
ALTER TABLE public.plan_produccion DROP CONSTRAINT IF EXISTS fk_plan_maestro_productos;
ALTER TABLE public.plan_produccion 
ADD CONSTRAINT fk_plan_maestro_productos 
FOREIGN KEY (producto) REFERENCES public.maestro_productos(producto) 
ON UPDATE CASCADE ON DELETE RESTRICT;

-- 3.8 BOM -> Maestro de Productos
ALTER TABLE public.bom DROP CONSTRAINT IF EXISTS fk_bom_producto;
ALTER TABLE public.bom DROP CONSTRAINT IF EXISTS fk_bom_maestro_productos;
ALTER TABLE public.bom 
ADD CONSTRAINT fk_bom_maestro_productos 
FOREIGN KEY (producto) REFERENCES public.maestro_productos(producto) 
ON UPDATE CASCADE ON DELETE RESTRICT;

-- 3.9 Eliminación de 'nombre_producto' redundante en BOM y Plan de Producción
ALTER TABLE public.bom DROP COLUMN IF EXISTS nombre_producto;
ALTER TABLE public.plan_produccion DROP COLUMN IF EXISTS nombre_producto;


-- ------------------------------------------------------------------------------
-- 4. ÍNDICES DE RENDIMIENTO (Buenas Prácticas Postgres)
-- ------------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_movimientos_sku ON public.movimientos_inventarios (sku);
CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON public.movimientos_inventarios (fecha);

CREATE INDEX IF NOT EXISTS idx_ordenes_compra_sku ON public.ordenes_compra (sku);
CREATE INDEX IF NOT EXISTS idx_ordenes_compra_fechas ON public.ordenes_compra (fecha_pedido, fecha_recepcion);

CREATE INDEX IF NOT EXISTS idx_bom_sku_material ON public.bom (sku_material);
CREATE INDEX IF NOT EXISTS idx_bom_producto ON public.bom (producto);

CREATE INDEX IF NOT EXISTS idx_plan_produccion_periodo ON public.plan_produccion (periodo);
CREATE INDEX IF NOT EXISTS idx_plan_produccion_producto ON public.plan_produccion (producto);

CREATE INDEX IF NOT EXISTS idx_bodega_jefe_codigo ON public."inventario_bodega_JEFE" (codigo);
