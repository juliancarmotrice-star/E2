-- ==============================================================================
-- SCRIPT DE LIMPIEZA Y NORMALIZACIÓN DE DATOS - E2 SAS
-- Proyecto: Optimización de la Gestión de Inventarios y Reposición
-- Base de Datos: Supabase / PostgreSQL (public)
-- ==============================================================================

-- 1. CORRECCIÓN DE FECHAS EN MOVIMIENTOS_INVENTARIO
-- Normalizar los registros ingresados con inversión de día/mes (2026-13-05 -> 2026-05-13)
UPDATE public.movimientos_inventario
SET fecha = '2026-05-13'::date
WHERE documento IN (
    'CONS-120084', 'CONS-120085', 'CONS-120086', 'CONS-120087', 'CONS-120088',
    'CONS-120089', 'CONS-120090', 'CONS-120091', 'CONS-120092', 'CONS-120093',
    'CONS-120094', 'CONS-120095', 'CONS-120096', 'CONS-120097', 'CONS-120098'
);

-- 2. CORRECCIÓN DE AÑO 2035 EN ORDENES_COMPRA
-- Corregir error tipográfico de la década (2035 -> 2024/2025/2026) respetando fecha_pedido <= fecha_recepcion
UPDATE public.ordenes_compra
SET fecha_recepcion = (
    CASE 
        WHEN EXTRACT(MONTH FROM fecha_recepcion) < EXTRACT(MONTH FROM fecha_pedido) 
            THEN (EXTRACT(YEAR FROM fecha_pedido) + 1)::text
        ELSE EXTRACT(YEAR FROM fecha_pedido)::text
    END || '-' || TO_CHAR(fecha_recepcion, 'MM-DD')
)::date
WHERE EXTRACT(YEAR FROM fecha_recepcion) = 2035;

-- 3. HOMOGENEIZACIÓN DE NOMENCLATURA EN BOM (LISTA DE MATERIALES)
-- Convertir todas las unidades de medida a minúsculas
UPDATE public.bom
SET unidad = LOWER(unidad);

-- 4. ESTANDARIZACIÓN DE CATEGORÍAS EN MAESTRO_MATERIALES
-- Consolidar las 24 variantes dispares en las 8 familias canónicas oficiales
UPDATE public.maestro_materiales
SET categoria = CASE 
    WHEN LOWER(categoria) LIKE '%adhesiv%' OR LOWER(categoria) LIKE '%pegante%' THEN 'Adhesivos'
    WHEN LOWER(categoria) LIKE '%correder%' THEN 'Correderas'
    WHEN LOWER(categoria) LIKE '%empaqu%' THEN 'Empaque'
    WHEN LOWER(categoria) LIKE '%lamin%' OR LOWER(categoria) LIKE '%lámin%' THEN 'Lámina'
    WHEN LOWER(categoria) LIKE '%pintur%' THEN 'Pintura'
    WHEN LOWER(categoria) LIKE '%torn%' THEN 'Tornillería'
    WHEN LOWER(categoria) LIKE '%tuber%' THEN 'Tubería'
    WHEN LOWER(categoria) LIKE '%vidri%' THEN 'Vidrio'
    ELSE categoria
END;

-- 5. ASIGNACIÓN DE LEAD TIMES DEDUCIDOS DESDE ÓRDENES DE COMPRA
-- Deducción del tiempo de entrega real (promedio fecha_recepcion - fecha_pedido) para los 54 SKUs con valor nulo
UPDATE public.maestro_materiales
SET lead_time_declarado_dias = CASE 
    WHEN sku = 'MP-0001' THEN 26
    WHEN sku = 'MP-0039' THEN 35
    WHEN sku = 'MP-0051' THEN 23
    WHEN sku = 'MP-0078' THEN 36
    WHEN sku = 'MP-0086' THEN 19
    WHEN sku = 'MP-0090' THEN 22
    WHEN sku = 'MP-0092' THEN 23
    WHEN sku = 'MP-0093' THEN 14
    WHEN sku = 'MP-0102' THEN 20
    WHEN sku = 'MP-0115' THEN 19
    WHEN sku = 'MP-0123' THEN 23
    WHEN sku = 'MP-0127' THEN 14
    WHEN sku = 'MP-0132' THEN 25
    WHEN sku = 'MP-0136' THEN 24
    WHEN sku = 'MP-0138' THEN 19
    WHEN sku = 'MP-0140' THEN 19
    WHEN sku = 'MP-0152' THEN 25
    WHEN sku = 'MP-0159' THEN 12
    WHEN sku = 'MP-0163' THEN 12
    WHEN sku = 'MP-0167' THEN 16
    WHEN sku = 'MP-0175' THEN 18
    WHEN sku = 'MP-0181' THEN 9
    WHEN sku = 'MP-0185' THEN 15
    WHEN sku = 'MP-0199' THEN 19
    WHEN sku = 'MP-0203' THEN 17
    WHEN sku = 'MP-0206' THEN 32
    WHEN sku = 'MP-0210' THEN 6
    WHEN sku = 'MP-0220' THEN 6
    WHEN sku = 'MP-0225' THEN 5
    WHEN sku = 'MP-0226' THEN 16
    WHEN sku = 'MP-0229' THEN 16
    WHEN sku = 'MP-0232' THEN 26
    WHEN sku = 'MP-0238' THEN 10
    WHEN sku = 'MP-0245' THEN 16
    WHEN sku = 'MP-0247' THEN 32
    WHEN sku = 'MP-0249' THEN 38
    WHEN sku = 'MP-0266' THEN 23
    WHEN sku = 'MP-0268' THEN 13
    WHEN sku = 'MP-0285' THEN 17
    WHEN sku = 'MP-0288' THEN 19
    WHEN sku = 'MP-0292' THEN 24
    WHEN sku = 'MP-0297' THEN 25
    WHEN sku = 'MP-0302' THEN 29
    WHEN sku = 'MP-0306' THEN 29
    WHEN sku = 'MP-0318' THEN 14
    WHEN sku = 'MP-0340' THEN 17
    WHEN sku = 'MP-0344' THEN 21
    WHEN sku = 'MP-0356' THEN 22
    WHEN sku = 'MP-0363' THEN 21
    WHEN sku = 'MP-0368' THEN 22
    WHEN sku = 'MP-0398' THEN 18
    WHEN sku = 'MP-0399' THEN 14
    WHEN sku = 'MP-0407' THEN 10
    WHEN sku = 'MP-0417' THEN 11
    ELSE lead_time_declarado_dias
END
WHERE lead_time_declarado_dias IS NULL;
