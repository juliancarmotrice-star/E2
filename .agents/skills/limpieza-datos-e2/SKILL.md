---
name: limpieza-datos-e2
description: >-
  Applies the canonical E2 SAS data-cleaning protocol to raw CSVs. Use when
  ingesting new files into datos_iniciales, running or changing
  python/clean_pipeline.py, normalizing to 3FN, or loading datos_limpios into
  Supabase. Never invent ad-hoc cleaning; reuse the same rules for every table
  and every new load.
---

# Limpieza de datos E2 SAS

Toda carga nueva (Kardex, OC, BOM, conteos) entra al **mismo protocolo**. No limpiar a mano en Excel, no saltarse tablas, no subir CSV crudo a Supabase.

Ejecutable canónico: `python python/clean_pipeline.py`  
Entrada: `datos_iniciales/` (intacta). Salida: `datos_limpios/*_clean.csv`. Carga: `python python/upload_to_supabase.py`.

## Ciclo obligatorio

1. Copiar los CSV nuevos a `datos_iniciales/` con los nombres canónicos (no renombrar columnas ad hoc).
2. Correr `clean_pipeline.py` completo (las 8 fuentes + `maestro_productos`).
3. Revisar el log `[OK]` y comparar filas vs bitácora si el volumen cambió.
4. Solo entonces `upload_to_supabase.py`.
5. La siguiente carga **repite desde el paso 1**. No hay pipeline “rápido”.

## Nombres canónicos de entrada

| Archivo | Notas |
|---|---|
| `maestro_materiales.csv` | SKU, categoría, unidad, costo, LT, stock min/max |
| `movimientos_inventario.csv` | Kardex |
| `ordenes_compra.csv` | Cerradas vs abiertas (`fecha_recepcion` nula = tránsito) |
| `bom.csv` | Puede traer `nombre_producto` redundante |
| `plan_produccion.csv` | Idem |
| `inventario_inicial.csv` | Tabla madre; no alterar saldos |
| `conteo_fisico.csv` | Auditoría IRA |
| `Inventario_bodega_JEFE.csv` | Cuaderno paralelo; columna `codigo` |

## Reglas por tabla (no improvisar)

- **Categorías y unidades:** usar los `cat_map` / `unit_map` de `clean_pipeline.py` (8 familias). Extender el mapa si aparece un sinónimo nuevo; no crear una novena familia sin documentarlo en la bitácora.
- **Lead time nulo:** imputar media de LT real por SKU desde OC; si no hay, mediana por proveedor; fallback 14. No usar el LT teórico de 15 días de lámina.
- **Kardex:** cantidad = `|cantidad|`. El sentido lo da `tipo_movimiento`. Fechas `2026-13-05` → el pipeline vigente corrige a `2026-03-05`; no mezclar otro criterio en la misma carga.
- **OC:** año de recepción `2035` → año del `fecha_pedido` (o +1 si la fecha quedaría antes del pedido). **No borrar** las  OC sin recepción: son tránsito para ROP.
- **BOM / plan:** generar `id_bom = producto + '_' + sku_material`; quitar `nombre_producto`; crear/actualizar `maestro_productos_clean.csv` con pares únicos.
- **Inventario inicial:** copiar íntegro. Es el ancla del Kardex teórico.
- **Conteo físico y bodega jefe:** `|stock|` / `|conteo_jefe|`; deduplicar por `sku` / `codigo`; observaciones nulas del jefe → `Sin observación`.

## Qué no va en este skill

No calcular **ROP, SS, EOQ** (motor de reposición).  
No calcular **IRA** (motor de exactitud: Kardex vs físico vs jefe).  
No calcular **ABC-XYZ** (motor de segmentación / plata muerta).  
Esos motores leen `datos_limpios` / Supabase **después** de este ciclo.

## Si el código y la bitácora discrepan

Gana `clean_pipeline.py` para la corrida. Documenta la diferencia en `informes/BITACORA_DE_LIMPIEZA.md` y cambia el pipeline en un solo lugar para la siguiente carga.
