-- ==============================================================================
-- PROYECTO E2 SAS - MIGRACIÓN FINAL: MAESTRO DE PRODUCTOS Y RLS
-- ==============================================================================

-- 1. Deshabilitar RLS en maestro_productos para habilitar lectura/escritura pública
ALTER TABLE public.maestro_productos DISABLE ROW LEVEL SECURITY;

-- 2. Asegurar el catálogo completo de los 18 productos terminados
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

-- 3. Verificación de registros
SELECT producto, nombre_producto FROM public.maestro_productos ORDER BY producto;
