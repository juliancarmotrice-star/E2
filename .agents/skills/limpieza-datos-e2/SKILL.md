---
name: limpieza-datos-e2
description: >-
  Aplica el protocolo canónico general de limpieza, normalización a 3FN e ingesta de datos
  para cualquier lote o actualización de datos maestros y transaccionales (N SKUs).
  Utilícese al procesar nuevos archivos CSV en datos_iniciales, ejecutar o modificar
  python/clean_pipeline.py, auditar integridad referencial y cargar datos_limpios en Supabase.
  Enfatiza la conexión con las vistas analíticas generadas sobre los datos limpios.
---

# 🧹 Protocolo General de Limpieza, Normalización 3FN e Ingesta

Este skill es la **guía metodológica y de ingeniería de datos general** para que cualquier LLM o agente de IA ejecute, audite y mantenga el pipeline de saneamiento, gobernanza y normalización a Tercera Forma Normal (3FN) para **cualquier volumen de materias primas ($N$ SKUs)**, transacciones u órdenes históricas.

> [!IMPORTANT]
> **DIRECTIVA PRINCIPAL PARA EL LLM (DATOS LIMPIOS Y VISTAS ANALÍTICAS):**
> Una vez ejecutado el pipeline de limpieza y cargadas las tablas en Supabase, todas las capas analíticas posteriores (ABC, ERI, EOQ, ROP, SLA, MRP) deben **consumir las vistas analíticas precalculadas**:
> * `public.vista_clasificacion_abc`
> * `public.vista_calculo_eoq_rop`
> * `public.vista_diagnostico_eri_inventarios`
> * `public.vista_resumen_eri_inventarios`
> 
> **Regla de Oro:** Queda terminantemente prohibido limpiar archivos a mano en Excel, modificar fuentes crudas en `datos_iniciales/` o insertar registros sin pasar por `clean_pipeline.py`.

---

## 🔄 1. Ciclo de Ejecución e Idempotencia

El pipeline está diseñado para ser **100% determinístico, repetible e idempotente**:

```
     ┌──────────────────────────────────────────────────────────┐
     │ 1. ARCHIVOS FUENTE CRUDOS (Inmutables)                   │
     │ Ubicación: datos_iniciales/*.csv                         │
     └────────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
     ┌──────────────────────────────────────────────────────────┐
     │ 2. PIPELINE DETERMINÍSTICO EN PYTHON                     │
     │ Ejecución: python python/clean_pipeline.py               │
     └────────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
     ┌──────────────────────────────────────────────────────────┐
     │ 3. CONJUNTO DE DATOS NORMALIZADO (3FN)                   │
     │ Generado en: datos_limpios/*_clean.csv                   │
     └────────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
     ┌──────────────────────────────────────────────────────────┐
     │ 4. INGESTA Y CREACIÓN DE VISTAS EN SUPABASE              │
     │ Ejecución: python python/upload_to_supabase.py           │
     │ DDL: sql/03_vistas_analiticas_abc.sql, 04_...            │
     └──────────────────────────────────────────────────────────┘
```

---

## 🪜 2. Catálogo Maestro de Reglas de Transformación por Entidad

### 2.1 Maestro de Materiales (`maestro_materiales_clean.csv`)
1. **Normalización Léxica de Familias de Materiales:** Mapeo mediante diccionario extensivo (`cat_map`) para consolidar variantes tipográficas a nombres canónicos (ej. `Lámina`, `Tubería`, `Tornillería`, `Pintura`, `Correderas`, `Adhesivos`, `Empaque`, `Vidrio`).
2. **Normalización de Unidades de Medida:** Mapeo en minúsculas estándar (`kg`, `unidad`, `m`, `par`, `m2`, `lámina`).
3. **Triangulación Empírica de Lead Times Nulos:**
   * *Regla A:* Si el SKU tiene compras cerradas en `ordenes_compra`, imputar con el promedio real observado ($\text{fecha\_recepcion} - \text{fecha\_pedido}$).
   * *Regla B:* Si el SKU no tiene compras pero tiene proveedor asignado, imputar con la mediana de entrega de dicho proveedor.
   * *Regla C (Fallback):* Mediana global de la categoría o valor por defecto (14 días).
4. **Filtrado de Registros Espurios:** Exclusión de SKUs de prueba (`MP-9...`) o duplicados que contengan `(dup)`.

---

### 2.2 Transacciones de Inventario / Kardex (`movimientos_inventarios_clean.csv`)
1. **Validación y Corrección de Fechas:** Asegurar que el mes cumpla $1 \le \text{mes} \le 12$. Cualquier anomalía tipográfica (ej. mes 13 `2026-13-05`) se ajusta al mes calendario lógico.
2. **Valor Absoluto en Cantidades:** Convertir cantidades negativas a valor absoluto ($|\text{cantidad}|$). El sentido contable queda gobernado exclusivamente por la columna `tipo_movimiento` (`entrada`, `salida`, `ajuste`).

---

### 2.3 Órdenes de Compra (`ordenes_compra_clean.csv`)
1. **Consistencia Temporal:** Garantizar que $\text{fecha\_recepcion} \ge \text{fecha\_pedido}$. Corregir años anómalos o de prueba.
2. **Preservación de Órdenes Abiertas:** Conservar registros con `fecha_recepcion = NaN` como inventario en tránsito mandatorio para la posición neta de reorden.

---

### 2.4 BOM y Maestro de Productos Terminados (Normalización a 3FN)
1. **Desacoplamiento Dimensional:** Extraer catálogo maestro único de productos terminados (`maestro_productos_clean.csv`) con `producto` y `nombre_producto`.
2. **Estructura Atómica del BOM:** Generar llave primaria compuesta única `id_bom = producto + '_' + sku_material` y eliminar atributos descriptivos redundantes para cumplir con la Tercera Forma Normal (3FN).

---

### 2.5 Plan de Producción (`plan_produccion_clean.csv`)
1. **Eliminación de Redundancias:** Desacoplar atributos descriptivos de producto vinculado por clave foránea.
2. **Estandarización de Periodo:** Validación de fechas ISO `YYYY-MM-01`.

---

### 2.6 Inventario Inicial (`inventario_inicial_clean.csv`)
* **Inmutabilidad del Ancla Histórica:** Conservar la totalidad de registros base sin alterar cantidades iniciales para garantizar la integridad de la reconstrucción del Kardex.

---

### 2.7 Conteo Físico Oficial (`conteo_fisico_clean.csv`)
1. **Saneamiento de Signos:** Aplicar valor absoluto $|\text{stock\_fisico\_contado}|$ para neutralizar errores de digitación de signos negativos en terminales de captura.
2. **Deduplicación:** Garantizar unicidad de registro por `sku`.

---

### 2.8 Control Auxiliar de Bodega (`inventario_bodega_JEFE_clean.csv`)
1. **Mapeo de Claves:** Estandarizar nombre de columna identificadora (`codigo` $\to$ `sku`).
2. **Saneamiento e Imputación:** Cantidades en valor absoluto, textos normalizados e imputación de observaciones vacías a `'Sin observación'`.

---

## 🚦 3. Checklist de Integridad Referencial Post-Limpieza

Antes de autorizar la ingesta en Supabase:
1. ✅ **Cero Claves Huérfanas:** Todo `sku` en `bom`, `ordenes_compra` y `movimientos_inventarios` existe en `maestro_materiales`.
2. ✅ **Cero Productos Huérfanos:** Todo `producto` en `bom` y `plan_produccion` existe en `maestro_productos`.
3. ✅ **Cero Nulos en Campos Críticos:** 100% de SKUs tienen `costo_unitario` y `lead_time_declarado_dias` poblados.
4. ✅ **Cero Fechas Inválidas:** Todas las fechas cumplen con el estándar ISO `YYYY-MM-DD` (meses $\le 12$).

---

## 🗄️ 4. Vistas Analíticas Habilitadas en Supabase

Una vez cargadas las tablas limpias, se habilitan automáticamente las **4 vistas analíticas dinámicas oficiales**:

| Vista Analítica | Propósito y Skill Asociado |
|---|---|
| `public.vista_clasificacion_abc` | Segmentación Pareto 80/15/5 ([`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md)) |
| `public.vista_calculo_eoq_rop` | Modelo de reposición $(s, Q)$ ([`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md)) |
| `public.vista_diagnostico_eri_inventarios` | Reconciliación tridimensional detallada ([`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md)) |
| `public.vista_resumen_eri_inventarios` | Resumen de exactitud ERI y desalineación contable ([`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md)) |

---

## 🛠️ 5. Scripts del Pipeline y Comandos de Ejecución

| Paso | Script | Comando de Ejecución | Propósito |
|:----:|--------|---------------------|-----------|
| 1 | `python/clean_pipeline.py` | `python python/clean_pipeline.py` | Ejecuta todas las reglas de transformación y genera `datos_limpios/*_clean.csv` |
| 2 | `python/upload_to_supabase.py` | `python python/upload_to_supabase.py` | Inserta por lotes los CSVs limpios en las tablas de Supabase |
| 3 | `sql/supabase_schema_foreign_keys.sql` | Ejecutar DDL en Supabase SQL Editor | Crea las restricciones de integridad referencial (FKs y NOT NULLs) |
| 4 | `sql/supabase_crear_maestro_productos.sql` | Ejecutar DDL en Supabase SQL Editor | Crea la tabla `maestro_productos` (catálogo de PTs) |
| 5 | `sql/supabase_bom_pk.sql` | Ejecutar DDL en Supabase SQL Editor | Establece la llave primaria compuesta en la tabla `bom` |
| 6 | `sql/03_vistas_analiticas_abc.sql` | Ejecutar DDL en Supabase SQL Editor | Crea la vista `public.vista_clasificacion_abc` |
| 7 | `sql/04_vistas_calculo_eoq_rop.sql` | Ejecutar DDL en Supabase SQL Editor | Crea las vistas `vista_calculo_eoq_rop`, `vista_diagnostico_eri_inventarios` y `vista_resumen_eri_inventarios` |

> [!NOTE]
> **Requisito previo:** Configurar credenciales en `.env` a partir de `.env.example` antes de ejecutar `upload_to_supabase.py`.

---

## 📦 6. Tablas y Archivos Generados (Mapeo CSV → Supabase)

| # | Archivo Generado en `datos_limpios/` | Tabla Destino en Supabase | Registros (Baseline N=420) | Clave Primaria |
|:-:|--------------------------------------|--------------------------|:--------------------------:|:--------------:|
| 1 | `maestro_materiales_clean.csv` | `public.maestro_materiales` | 420 SKUs | `sku` |
| 2 | `maestro_productos_clean.csv` | `public.maestro_productos` | 18 PTs | `producto` |
| 3 | `bom_clean.csv` | `public.bom` | 131 filas | `id_bom` (compuesta) |
| 4 | `movimientos_inventario_clean.csv` | `public.movimientos_inventarios` | ~16.195 registros | `documento` + `sku` + `fecha` |
| 5 | `ordenes_compra_clean.csv` | `public.ordenes_compra` | ~1.471 OCs | `orden_compra` |
| 6 | `inventario_inicial_clean.csv` | `public.inventario_inicial` | 420 filas | `sku` |
| 7 | `conteo_fisico_clean.csv` | `public.conteo_fisico` | 420 filas | `sku` |
| 8 | `inventario_bodega_JEFE_clean.csv` | `public.inventario_bodega_jefe` | Variable | `sku` |
| 9 | `plan_produccion_clean.csv` | `public.plan_produccion` | ~378 filas | `producto` + `periodo` |

---

## 🔎 7. Queries de Verificación Post-Ingesta en Supabase

Ejecutar estas consultas **después de cada carga** para confirmar que la ingesta fue exitosa y completa:

### A. Verificar Conteo de Registros por Tabla
```sql
SELECT 'maestro_materiales' AS tabla, COUNT(*) AS registros FROM public.maestro_materiales
UNION ALL SELECT 'maestro_productos', COUNT(*) FROM public.maestro_productos
UNION ALL SELECT 'bom', COUNT(*) FROM public.bom
UNION ALL SELECT 'movimientos_inventarios', COUNT(*) FROM public.movimientos_inventarios
UNION ALL SELECT 'ordenes_compra', COUNT(*) FROM public.ordenes_compra
UNION ALL SELECT 'inventario_inicial', COUNT(*) FROM public.inventario_inicial
UNION ALL SELECT 'conteo_fisico', COUNT(*) FROM public.conteo_fisico
UNION ALL SELECT 'plan_produccion', COUNT(*) FROM public.plan_produccion;
```

### B. Verificar Cero Claves Huérfanas (Integridad Referencial)
```sql
-- SKUs huérfanos en movimientos
SELECT 'mov_huerfanos' AS check_name, COUNT(*) AS problemas
FROM public.movimientos_inventarios mi
WHERE mi.sku NOT IN (SELECT sku FROM public.maestro_materiales)
UNION ALL
-- SKUs huérfanos en OCs
SELECT 'oc_huerfanos', COUNT(*)
FROM public.ordenes_compra oc
WHERE oc.sku NOT IN (SELECT sku FROM public.maestro_materiales)
UNION ALL
-- Productos huérfanos en BOM
SELECT 'bom_producto_huerfanos', COUNT(*)
FROM public.bom b
WHERE b.producto NOT IN (SELECT producto FROM public.maestro_productos)
UNION ALL
-- SKUs huérfanos en BOM
SELECT 'bom_sku_huerfanos', COUNT(*)
FROM public.bom b
WHERE b.sku_material NOT IN (SELECT sku FROM public.maestro_materiales);
-- Resultado esperado: 0 problemas en TODAS las filas
```

### C. Verificar Cero Nulos en Campos Críticos
```sql
SELECT 
    COUNT(*) FILTER (WHERE costo_unitario IS NULL) AS nulos_costo,
    COUNT(*) FILTER (WHERE lead_time_declarado_dias IS NULL) AS nulos_lead_time,
    COUNT(*) FILTER (WHERE categoria IS NULL) AS nulos_categoria,
    COUNT(*) FILTER (WHERE unidad IS NULL) AS nulos_unidad
FROM public.maestro_materiales;
-- Resultado esperado: 0 en TODAS las columnas
```

### D. Verificar Vistas Analíticas Operativas
```sql
SELECT 'vista_clasificacion_abc' AS vista, COUNT(*) AS registros 
FROM public.vista_clasificacion_abc
UNION ALL 
SELECT 'vista_calculo_eoq_rop', COUNT(*) 
FROM public.vista_calculo_eoq_rop
UNION ALL 
SELECT 'vista_diagnostico_eri_inventarios', COUNT(*) 
FROM public.vista_diagnostico_eri_inventarios
UNION ALL 
SELECT 'vista_resumen_eri_inventarios', COUNT(*) 
FROM public.vista_resumen_eri_inventarios;
-- Resultado esperado: Todas las vistas devuelven registros > 0
```

---

## 🔗 8. Prerequisitos y Dependencias

* **Prerequisitos de entrada:** Archivos CSV crudos en `datos_iniciales/` sin modificar.
* **Dependencias Python:** `pandas`, `python-dotenv`, `supabase` (ver `requirements.txt`).
* **Dependencias de infraestructura:** Proyecto Supabase activo con URL y Service Role Key configurados en `.env`.
* **Skills que dependen de esta:** TODAS las demás skills (`analitica-abc-xyz-e2`, `exactitud-inventarios-eri-e2`, `reposicion-eoq-rop-e2`, `sla-proveedores-mrp-e2`) requieren que esta skill se haya ejecutado exitosamente.

---

## 🚫 9. Fronteras del Skill (Qué NO hace este Skill)

* **NO calcular ROP, SS, EOQ:** Es responsabilidad del skill [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md).
* **NO calcular ERI / Desalineación Contable:** Es responsabilidad del skill [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md).
* **NO calcular segmentación ABC-XYZ:** Es responsabilidad del skill [`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md).
* **NO auditar SLA de proveedores:** Es responsabilidad del skill [`sla-proveedores-mrp-e2`](../sla-proveedores-mrp-e2/SKILL.md).

Este skill entrega los datos **100% limpios y normalizados a 3FN** para que los motores determinísticos posteriores consuman una fuente de verdad libre de inconsistencias sobre cualquier catálogo de $N$ materiales.


