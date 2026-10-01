---
name: limpieza-datos-e2
description: >-
  Aplica el protocolo canónico de limpieza, normalización a 3FN e ingesta de datos
  para E2 SAS. Utilícese al procesar nuevos archivos CSV en datos_iniciales, ejecutar
  o modificar python/clean_pipeline.py, auditar integridad referencial y cargar
  datos_limpios en Supabase.
  Enfatiza la conexión con las vistas analíticas generadas sobre los datos limpios.
---

# 🧹 Protocolo Canónico de Limpieza, Normalización 3FN e Ingesta — E2 SAS

Este skill es la **guía canónica de ingeniería y gobernanza de datos** para que cualquier LLM o agente de IA ejecute, audite y mantenga el pipeline de saneamiento y normalización a Tercera Forma Normal (3FN) para **E2 SAS (Capa 1: Ingesta & Gobernanza)**.

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

## 🪜 2. Catálogo Maestro de Reglas de Transformación por Tabla

### 2.1 `maestro_materiales.csv` ➔ `maestro_materiales_clean.csv`
1. **Normalización Léxica de 8 Familias de Materiales (24 variantes corregidas):**
   * `Lamina de acero`, `lamina`, `LAMINA AC`, `Lámina`, `Lmina` $\rightarrow$ **`Lámina`**
   * `tornilleria`, `Torn.`, `Tornillería`, `Tornillera` $\rightarrow$ **`Tornillería`**
   * `Tubería`, `TUBERIA`, `tuberia`, `Tubera` $\rightarrow$ **`Tubería`**
   * `PINTURA`, `pintura electrostatica`, `Pintura` $\rightarrow$ **`Pintura`**
   * `CORREDERA`, `Correderas`, `correderas` $\rightarrow$ **`Correderas`**
   * `Adhesivos`, `PEGANTE`, `adhesivo` $\rightarrow$ **`Adhesivos`**
   * `empaque`, `Empaque`, `EMPAQUES` $\rightarrow$ **`Empaque`**
   * `Vidrio`, `vidrio` $\rightarrow$ **`Vidrio`**
2. **Normalización de Unidades de Medida:** Mapeo canónico en minúsculas: `kg`, `unidad`, `m`, `par`, `m2`, `lámina`.
3. **Triangulación y Deducción Empírica de Lead Times Nulos (54 SKUs faltantes):**
   * *Paso A (52 SKUs):* Promedio real observado en `ordenes_compra.csv` para ese SKU ($\text{fecha\_recepcion} - \text{fecha\_pedido}$).
   * *Paso B (2 SKUs sin compras históricas: `MP-0232` y `MP-0398`):* Imputar con la mediana del proveedor asignado (`PROV-02` = 21 días, `PROV-25` = 17 días).
   * *Paso C (Fallback general):* 14 días.
4. **Depuración de Registros de Prueba:** Excluir SKUs `MP-9...` o que contengan `(dup)`.

---

### 2.2 `movimientos_inventario.csv` ➔ `movimientos_inventarios_clean.csv` (Kardex)
1. **Corrección de Fechas Corruptas / Mes 13 (`2026-13-05`):**
   * 15 transacciones del operador `OP-99` con fecha errónea `2026-13-05` se corrigen a **`2026-03-05`** (5 de marzo de 2026), dentro del horizonte de 21 meses.
2. **Conversión a Valor Absoluto en Cantidades:**
   * 466 cantidades con signo negativo (440 salidas y 26 ajustes) se convierten a valor positivo mediante **`|cantidad|`**.
   * El sentido contable queda definido estrictamente por `tipo_movimiento` (`entrada`, `salida`, `ajuste`).

---

### 2.3 `ordenes_compra.csv` ➔ `ordenes_compra_clean.csv`
1. **Corrección de Años Corruptos (Año `2035`):**
   * 22 órdenes con `fecha_recepcion` en el año 2035 se reasignan al año real de la orden (`2024`, `2025` o `2026`), garantizando $\text{fecha\_recepcion} \ge \text{fecha\_pedido}$.
2. **Preservación de Órdenes Abiertas (`fecha_recepcion = NaN`):**
   * **NUNCA ELIMINAR** las 74 órdenes abiertas: representan inventario en tránsito mandatorio para evaluar stock disponible y disparar el semáforo de reposición.

---

### 2.4 `bom.csv` y `maestro_productos.csv` (Normalización a 3FN)
1. **Extracción de Entidad Maestra de Productos Terminados (`maestro_productos_clean.csv`):**
   * Se extraen los 18 productos terminados únicos (`producto`, `nombre_producto`) creando la entidad padre.
2. **Estructuración del BOM (`bom_clean.csv`):**
   * **Llave Primaria Compuesta:** `id_bom = producto + '_' + sku_material` (131 recetas).
   * Eliminación de `nombre_producto` para cumplir con **Tercera Forma Normal (3FN)**.

---

### 2.5 `plan_produccion.csv` ➔ `plan_produccion_clean.csv`
1. **Desacoplamiento 3FN:** Eliminación del atributo redundante `nombre_producto`.
2. **Estandarización Temporal:** Validación de formato ISO `YYYY-MM-01` en columna `periodo`.

---

### 2.6 `inventario_inicial.csv` ➔ `inventario_inicial_clean.csv`
* **Preservación Inmutable de la Tabla Madre:**
  * 420 SKUs conservados 100% íntegros como ancla histórica base.

---

### 2.7 `conteo_fisico.csv` ➔ `conteo_fisico_clean.csv`
1. **Saneamiento de Signos Negativos:** 94 registros convertidos a positivo mediante **`|stock_fisico_contado|`**.
2. **Deduplicación:** Validación de unicidad de `sku`.

---

### 2.8 `Inventario_bodega_JEFE.csv` ➔ `inventario_bodega_JEFE_clean.csv`
1. **Mapeo:** Renombrar `codigo` a `sku`.
2. **Saneamiento:** Convertir 32 valores negativos a positivo mediante **`|conteo_jefe|`**.
3. **Imputación:** Llenar 23 observaciones nulas con `'Sin observación'`.
4. **Familias:** Normalizar `material` con el `cat_map`.

---

## 🚦 3. Checklist de Integridad Referencial Post-Limpieza

Antes de autorizar la ingesta en Supabase:
1. ✅ **Cero Claves Huérfanas:** Todo `sku` en `bom`, `ordenes_compra` y `movimientos_inventarios` existe en `maestro_materiales`.
2. ✅ **Cero Productos Huérfanos:** Todo `producto` en `bom` y `plan_produccion` existe en `maestro_productos`.
3. ✅ **Cero Nulos en Campos Críticos:** 100% de SKUs tienen `costo_unitario` y `lead_time_declarado_dias` poblados.
4. ✅ **Cero Fechas Inválidas:** Todas las fechas cumplen con el estándar ISO `YYYY-MM-DD` (meses $\le 12$).

---

## 🗄️ 4. Vistas Analíticas Resultantes en Supabase

Una vez cargadas las tablas limpias, se habilitan automáticamente las **4 vistas analíticas oficiales**:

| Vista Analítica | Propósito y Skill Asociado |
|---|---|
| `public.vista_clasificacion_abc` | Segmentación Pareto 80/15/5 ([`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md)) |
| `public.vista_calculo_eoq_rop` | Modelo de reposición $(s, Q)$ ([`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md)) |
| `public.vista_diagnostico_eri_inventarios` | Reconciliación tridimensional detallada ([`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md)) |
| `public.vista_resumen_eri_inventarios` | Resumen de exactitud ERI y desalineación contable ([`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md)) |

---

## 🚫 5. Fronteras del Skill (Qué NO hace este Skill)

* **NO calcular ROP, SS, EOQ:** Es responsabilidad del skill [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md).
* **NO calcular ERI / Desalineación Contable:** Es responsabilidad del skill [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md).
* **NO calcular segmentación ABC-XYZ:** Es responsabilidad del skill [`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md).
* **NO auditar SLA de proveedores:** Es responsabilidad del skill [`sla-proveedores-mrp-e2`](../sla-proveedores-mrp-e2/SKILL.md).

Este skill entrega los datos **100% limpios y normalizados a 3FN** para que los motores determinísticos posteriores consuman una fuente de verdad libre de inconsistencias.

