---
name: limpieza-datos-e2
description: >-
  Aplica el protocolo canónico de limpieza, normalización a 3FN e ingesta de datos
  para E2 SAS. Utilícese al procesar nuevos archivos CSV en datos_iniciales, ejecutar
  o modificar python/clean_pipeline.py, auditar integridad referencial y cargar
  datos_limpios en Supabase.
---

# Protocolo Canónico de Limpieza, Normalización 3FN e Ingesta — E2 SAS

Este skill documenta y estandariza el **protocolo completo, reproducible y no destructivo** de saneamiento de datos para **E2 SAS (Capa 1: Ingesta & Gobernanza)**. 

Cualquier nuevo lote de datos periódicos (semanal, mensual o anual) debe someterse **exactamente a este mismo conjunto de transformaciones y validaciones** antes de ser cargado en la base de datos de PostgreSQL en Supabase.

**Regla de Oro:** Queda terminantemente prohibido limpiar archivos a mano en Excel, modificar las fuentes originales en `datos_iniciales/` o insertar registros sin pasar por `clean_pipeline.py`.

---

## 🔄 1. Ciclo de Ejecución e Idempotencia

```
    ┌──────────────────────────────────────────────┐
    │ 1. ARCHIVOS FUENTE CRUDOS                    │
    │ Copiados intactos a: datos_iniciales/        │
    └──────────────────────┬───────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │ 2. PIPELINE DETERMINÍSTICO EN PYTHON         │
    │ Ejecutar: python python/clean_pipeline.py    │
    └──────────────────────┬───────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │ 3. CONJUNTO DE DATOS NORMALIZADO (3FN)       │
    │ Generado en: datos_limpios/*_clean.csv       │
    └──────────────────────┬───────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │ 4. CARGA MASIVA Y VALIDACIÓN EN SUPABASE     │
    │ Ejecutar: python python/upload_to_supabase.py│
    └──────────────────────────────────────────────┘
```

---

## 📋 2. Catálogo Maestro de Reglas de Transformación por Tabla

### 2.1 `maestro_materiales.csv` ➔ `maestro_materiales_clean.csv`
* **Normalización de 8 Familias de Materiales (24 variantes léxicas detectadas):**
  * `Lamina de acero`, `lamina`, `LAMINA AC`, `Lámina`, `Lmina` $\rightarrow$ **`Lámina`**
  * `tornilleria`, `Torn.`, `Tornillería`, `Tornillera` $\rightarrow$ **`Tornillería`**
  * `Tubería`, `TUBERIA`, `tuberia`, `Tubera` $\rightarrow$ **`Tubería`**
  * `PINTURA`, `pintura electrostatica`, `Pintura` $\rightarrow$ **`Pintura`**
  * `CORREDERA`, `Correderas`, `correderas` $\rightarrow$ **`Correderas`**
  * `Adhesivos`, `PEGANTE`, `adhesivo` $\rightarrow$ **`Adhesivos`**
  * `empaque`, `Empaque`, `EMPAQUES` $\rightarrow$ **`Empaque`**
  * `Vidrio`, `vidrio` $\rightarrow$ **`Vidrio`**
* **Normalización de Unidades de Medida:**
  * Mapeo estricto a minúsculas canónicas: `kg`, `unidad`, `m`, `par`, `m2`, `lámina`.
* **Triangulación y Deducción Empírica de Lead Times Nulos (54 SKUs faltantes):**
  * *Paso 1 (52 SKUs):* Calcular el promedio de duración real observado en `ordenes_compra.csv` para ese SKU específico ($\text{fecha\_recepcion} - \text{fecha\_pedido}$).
  * *Paso 2 (2 SKUs sin compras históricas: `MP-0232` y `MP-0398`):* Imputar con la mediana de entrega del proveedor asignado (`PROV-02` = 21 días, `PROV-25` = 17 días).
  * *Paso 3 (Fallback general):* 14 días.
  * *Prohibición:* No usar el Lead Time teórico estático de 15 días declarado en folleto para láminas.
* **Depuración de Duplicados:** Filtrar registros espurios o de prueba (`MP-9...` / `(dup)`).

---

### 2.2 `movimientos_inventario.csv` ➔ `movimientos_inventario_clean.csv` (Kardex)
* **Corrección de Fechas Trasladadas / Typo de Mes 13 (`2026-13-05`):**
  * 15 transacciones del operador `OP-99` con fecha `2026-13-05` (mes 13 inexistente) se corrigen a **`2026-03-05`** (5 de marzo de 2026), encajando en la ventana de auditoría de 21 meses.
* **Sentido Contable y Valor Absoluto en Cantidades:**
  * 466 cantidades registradas con signo negativo (440 salidas y 26 ajustes) se convierten a valor positivo mediante **`|cantidad|`**.
  * El sentido contable (débito/crédito) lo define estrictamente la columna `tipo_movimiento` (`entrada`, `salida`, `ajuste`).

---

### 2.3 `ordenes_compra.csv` ➔ `ordenes_compra_clean.csv`
* **Corrección de Años Corruptos (Año `2035`):**
  * 22 órdenes con `fecha_recepcion` en el año `2035` se reasignan al año real de colocación del pedido (`2024`, `2025` o `2026`), asegurando que $\text{fecha\_recepcion} \ge \text{fecha\_pedido}$.
* **Tratamiento de Órdenes Abiertas / En Tránsito (`fecha_recepcion = NaN`):**
  * **NUNCA BORRAR** las 74 órdenes sin fecha de recepción: representan inventario en tránsito mandatorio para la posición neta de inventario y el cálculo del $ROP$.
  * Separar analíticamente: OCs cerradas evalúan SLA de proveedores; OCs abiertas suman al stock disponible.

---

### 2.4 `bom.csv` y `maestro_productos.csv` (Normalización a 3FN)
* **Creación de Entidad Maestra de Productos Terminados (`maestro_productos_clean.csv`):**
  * Se extraen los 18 productos terminados únicos de E2 SAS (`producto`, `nombre_producto`) creando una entidad dimensional padre.
* **Estructuración del BOM (`bom_clean.csv`):**
  * Generación de **Llave Primaria Compuesta Única:** `id_bom = producto + '_' + sku_material` (131 recetas).
  * Eliminación del atributo redundante `nombre_producto` para cumplir con la **Tercera Forma Normal (3FN)**.
  * Estandarización léxica de la columna `unidad`.

---

### 2.5 `plan_produccion.csv` ➔ `plan_produccion_clean.csv`
* **Desacoplamiento 3FN:**
  * Eliminación del atributo redundante `nombre_producto` (vinculado por FK hacia `maestro_productos`).
* **Estandarización Temporal:**
  * Validación de la columna `periodo` como fecha ISO (`YYYY-MM-01`, primer día de cada mes).

---

### 2.6 `inventario_inicial.csv` ➔ `inventario_inicial_clean.csv`
* **Preservación Inmutable de la "Tabla Madre":**
  * Se conserva 100% íntegra (420 SKUs).
  * Actúa como el ancla histórica inalterable para reconstruir el Kardex teórico:
    $$\text{Stock Kardex}(t) = \text{Stock Inicial} + \sum \text{Entradas} - \sum \text{Salidas} + \sum \text{Ajustes}$$

---

### 2.7 `conteo_fisico.csv` ➔ `conteo_fisico_clean.csv`
* **Saneamiento de Cantidades Negativas:**
  * 94 registros con valores negativos (hasta -18,018 unidades) se convierten a positivo mediante **`|stock_fisico_contado|`** (corrección de error de digitación de signo en terminal portátil).
* **Deduplicación:**
  * Verificación de unicidad por `sku`, preservando el primer registro válido.

---

### 2.8 `Inventario_bodega_JEFE.csv` ➔ `inventario_bodega_JEFE_clean.csv`
* **Rol Oficial en el Sistema:**
  * **Fuente Auxiliar de Verificación y Auditoría de Piso** (no es tabla transaccional primaria del ERP).
* **Transformaciones:**
  * Mapeo de la columna `codigo` a `sku`.
  * Conversión de 32 valores negativos a positivos mediante **`|conteo_jefe|`**.
  * Imputación de 23 observaciones nulas a `'Sin observación'`.
  * Estandarización de familias en la columna `material` usando el `cat_map`.
  * Deduplicación por `codigo`.

---

## 🚦 3. Checklist de Verificación Post-Limpieza (Integridad Referencial)

Antes de autorizar la subida a Supabase, el script verifica:
1. ✅ **Cero Claves Huérfanas:** Todo `sku_material` en `bom`, `ordenes_compra` y `movimientos_inventarios` existe en `maestro_materiales`.
2. ✅ **Cero Productos Huérfanos:** Todo `producto` en `bom` y `plan_produccion` existe en `maestro_productos`.
3. ✅ **Cero Nulos en Parámetros Críticos:** 100% de los SKUs tienen `costo_unitario` y `lead_time_declarado_dias` poblados.
4. ✅ **Cero Fechas Inválidas:** Formatos `YYYY-MM-DD` validados sin meses superiores a 12.

---

## 🚫 4. Fronteras del Skill (Qué NO hace este Skill)

* **NO calcular ROP, SS, EOQ:** Es responsabilidad del skill [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md).
* **NO calcular ERI / Desalineación Contable:** Es responsabilidad del skill [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md).
* **NO calcular segmentación ABC-XYZ:** Es responsabilidad del skill [`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md).
* **NO auditar SLA de proveedores:** Es responsabilidad del skill [`sla-proveedores-mrp-e2`](../sla-proveedores-mrp-e2/SKILL.md).

Este skill entrega los datos **100% limpios y normalizados a 3FN** para que los motores determinísticos posteriores consuman una fuente de verdad libre de inconsistencias.
