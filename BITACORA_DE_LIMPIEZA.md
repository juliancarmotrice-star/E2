# 📋 Bitácora Técnica de Calidad, Limpieza y Reconciliación de Datos — E2 SAS
> **Fase E1 — Diagnóstico y Línea Base**  
> **Proyecto:** Optimización de la Gestión de Inventarios y Reposición  
> **Asignatura:** Producción 4.0 / Énfasis 2 — Universidad de Medellín  
> **Referencia Técnica:** Pistas y Orientaciones de Retroalimentación Docente (`WhatsApp Ptt 2026-08-26`)

---

## 📌 1. Resumen Ejecutivo de Calidad de Datos

Se ejecutó una auditoría exhaustiva, reproducible y no destructiva sobre los **8 conjuntos de datos** suministrados por la dirección de **E2 SAS**. El diagnóstico identificó inconsistencias de formato, valores físicamente imposibles, anomalías de calendario, dispersión de nomenclatura y errores de digitación transaccional.

Todas las transformaciones se ejecutaron mediante un pipeline automatizado en Python ([`clean_pipeline.py`](clean_pipeline.py)), preservando las fuentes originales intactas y generando el conjunto de datos normalizado en [`data_clean/`](data_clean/).

### Matriz Global de Hallazgos y Tratamiento por Dataset

| # | Archivo / Dataset | Total Filas | Registros con Defectos | % Afectación | Principales Anomalías Detectadas | Pista / Criterio Docente Aplicado | Tratamiento / Regla de Transformación | Severidad |
|---|---|:---:|:---:|:---:|---|---|---|:---:|
| **1** | `maestro_materiales.csv` | 440 | 54 nulos + 24 variantes | 12.3% | 54 SKUs sin lead time declarado; 24 variantes léxicas en 8 familias; 41 outliers de costo. | Estandarizar categorías y deducir valores faltantes por familia/proveedor. | Imputación de lead times con mediana por categoría y mapeo canónico de 8 familias de materiales. | 🟡 MEDIA |
| **2** | `movimientos_inventario.csv` | 16,195 | 466 neg. + 15 fechas | 3.0% | 466 cantidades negativas (440 salidas, 26 ajustes); 15 fechas `2026-13-05` (mes 13 inexistente). | Fechas trasladadas `YYYY-DD-MM`; la cantidad debe ser positiva pues el tipo define el signo. | Inversión de fecha a `2026-05-13` y aplicación de valor absoluto $\lvert \text{cantidad} \rvert$. | 🔴 ALTA |
| **3** | `ordenes_compra.csv` | 1,471 | 22 fechas + 74 nulas | 6.5% | 22 órdenes con año de recepción `2035`; 74 órdenes en tránsito (`fecha_recepcion = NaN`). | No mezclar compras abiertas con cerradas; corregir typo de año 2035 al año de pedido. | Corrección de año `2035` a año de compra (`2024/2025`); partición metodológica de órdenes abiertas. | 🔴 ALTA |
| **4** | `bom.csv` | 131 | 131 vacíos + 12 unidades | 100% (ID) | Columna `ID_bom` 100% nula; dispersión de mayúsculas/minúsculas en unidades; atributo descriptivo `nombre_producto` redundante. | Crear llave compuesta `producto + material`, estandarizar unidades y normalizar eliminando redundancias descriptivas (3FN). | Generación de PK `id_bom`, unificación de unidades canónicas y eliminación de `nombre_producto` (migrado a `maestro_productos`). | 🟡 MEDIA |
| **5** | `conteo_fisico.csv` | 420 | 94 negativos | 22.4% | 94 SKUs con stock contado registrado con signo negativo (hasta -18,018 unidades). | El inventario físico no puede ser negativo; las unidades negativas se interpretan como error de digitación de signo. | Conversión de negativos a positivos mediante valor absoluto $\lvert \text{stock\_fisico\_contado} \rvert$ y verificación/eliminación de duplicados. | 🔴 CRÍTICA |
| **6** | `Inventario_bodega_JEFE.csv` | 120 | 32 neg. + 23 nulos | 45.8% | 32 existencias registradas con signo negativo (hasta -17,263); 23 notas vacías; vocabulario informal (`faltante??`, `pedir ya`, `sobra`). | Definir rol como verificación auxiliar; los negativos corresponden a errores de digitación en la libreta física. | Conversión de negativos a positivos vía $\lvert \text{conteo\_jefe} \rvert$, imputación de 23 observaciones nulas con `'Sin observación'`, normalización de categorías y deduplicación. | 🔴 CRÍTICA |
| **7** | `inventario_inicial.csv` | 420 | 0 | 0.0% | Estructura 100% íntegra. Saldos base entre 200 y 600 unidades al 2024-07-01. | **"Tabla Madre"**: Línea base perfecta para reconstruir toda la trazabilidad transaccional. | Conservación íntegra; tipificación formal de fecha y saldo como ancla del Kardex. | 🟢 LIMPIO |
| **8** | `plan_produccion.csv` | 378 | Redundancia 3FN | N/A | Atributo `nombre_producto` repetido en 378 filas; redundante con la entidad de productos. | Normalizar modelo relacional eliminando atributos descriptivos foráneos (Tercera Forma Normal - 3FN). | Eliminación de `nombre_producto` de la tabla de hechos; validación de integridad referencial con `maestro_productos`. | 🟢 LIMPIO |
| **9** | `maestro_productos.csv` *(Nueva)* | 18 | 0 | 0.0% | Inexistencia previa de entidad dimensional de Productos Terminados (PT). | Diseñar y poblar la entidad maestra de PT como padre de `bom` y `plan_produccion`. | Creación de tabla maestra con los 18 productos únicos de E2 SAS (`producto`, `nombre_producto`). | 🟢 NUEVA / 3FN |

---

## 🎧 2. Directrices y Pistas Técnicas del Docente (Sesión de Retroalimentación)

Con base en el análisis de la retroalimentación técnica suministrada por el docente (`WhatsApp Ptt 2026-08-26`), se incorporaron y validaron formalmente las siguientes directrices metodológicas:

```mermaid
mindmap
  root((Pistas Técnicas Docente))
    Inventario Inicial
      Tabla Madre 100% limpia
      Ancla para reconstruir trazabilidad
    Conteo Fisico y Negativos
      Imposibilidad física de stock negativo
      Desfase transaccional muelle vs ERP
      Deducción vía Kardex teórico
    Fechas Corruptas
      Formato trasladado YYYY-DD-MM a YYYY-MM-DD
      Typo de año 2035 a año de pedido
      Separar órdenes abiertas de cerradas
    Movimientos Kardex
      Valor absoluto en cantidades
      El tipo de movimiento define sentido contable
    BOM
      Crear PK compuesta producto + SKU
      Estandarizar unidades
    Inventario Bodega Jefe
      Justificar rol en el modelo
      Fuente de verificación paralela
      Análisis de descuadre IRA
```

### 2.1 Pista 1: Reconstrucción Deductiva mediante la "Tabla Madre" (`inventario_inicial.csv`)
* **Diagnóstico Docente:** `inventario_inicial.csv` es perfecta y actúa como la *tabla madre* de la empresa. Frente a conteos físicos negativos o saldos exorbitantes (como 19,000 cuando el stock máximo de catálogo es 500), la solución no es adivinar, sino deducir analíticamente reconciliando el inventario inicial con los movimientos históricos de entradas, salidas y ajustes.
* **Implementación:** Se utilizó el saldo al 2024-07-01 como condición inicial inmutable para recalcular el Kardex cronológico exacto de cada SKU.

### 2.2 Pista 2: Separación Metodológica de Órdenes de Compra (Abiertas vs. Cerradas)
* **Diagnóstico Docente:** En `ordenes_compra.csv` existen 74 órdenes sin fecha de recepción (`NaN`) que no deben descartarse como error ni mezclarse en el cálculo de Lead Times o cumplimiento del proveedor (OTIF).
* **Implementación:** 
  1. **Órdenes Cerradas (`fecha_recepcion` no nula):** Utilizadas exclusivamente para medir el Lead Time real ($LT_{\text{real}} = \text{Fecha Recepción} - \text{Fecha Pedido}$) y la tasa de entregas a tiempo.
  2. **Órdenes Abiertas (`fecha_recepcion = NaN`):** Tipificadas como *Inventario en Tránsito / Pedidos Pendientes*, insumo fundamental para el cálculo del punto de reorden ($ROP$) y la posición neta de inventario.

### 2.3 Pista 3: Corrección de Fechas Trasladadas y Años Anómalos
* **Diagnóstico Docente:**
  * En `movimientos_inventario.csv`, las fechas con mes `13` (ej. `2026-13-05`) obedecen a un formato trasladado donde se digitó año, día y mes (`YYYY-DD-MM`). Dado que no existe el mes 13, la fecha real es `2026-05-13` (13 de mayo de 2026).
  * En `ordenes_compra.csv`, las 22 órdenes con recepción en el año `2035` son errores de digitación del año sobre órdenes emitidas en 2024 y 2025.
* **Implementación:** Inversión algorítmica de día/mes para registros corruptos de mayo de 2026 y reasignación del año de recepción al año de pedido preservando mes y día.

### 2.4 Pista 4: Sentido Contable y Valor Absoluto en Movimientos de Kardex
* **Diagnóstico Docente:** En `movimientos_inventario.csv`, registrar cantidades negativas en transacciones de salida o ajuste es un error de digitación redundante, pues la naturaleza de la operación (débito/crédito) ya la define la columna `tipo_movimiento`.
* **Implementación:** Transformación de todas las cantidades a valor absoluto $\lvert \text{cantidad} \rvert$, garantizando que la fórmula de balance opere de manera determinística:
$$\text{Stock}(t) = \text{Stock}(t-1) + \mathbb{I}_{\{\text{entrada}\}} \cdot Q - \mathbb{I}_{\{\text{salida}\}} \cdot Q \pm \mathbb{I}_{\{\text{ajuste}\}} \cdot Q$$

### 2.5 Pista 5: Llave Primaria Compuesta y Unidades en BOM
* **Diagnóstico Docente:** La tabla de recetas (`bom.csv`) carece de llave primaria simple y tiene inconsistencias de mayúsculas/minúsculas en unidades. La llave debe construirse con la combinación estructural del producto terminado y la materia prima.
* **Implementación:** Creación de la clave sintética `ID_bom = producto || '_' || sku_material` y normalización léxica de unidades (`kg`, `unidad`, `m`, `par`, `m2`, `lámina`).

### 2.6 Pista 6: Definición y Justificación del Rol de `Inventario_bodega_JEFE.csv`
* **Diagnóstico Docente:** Es mandatorio definir y justificar el rol que juega esta tabla dentro de la arquitectura relacional y el modelo analítico.
* **Implementación y Justificación Arquitectónica:**
  1. **No es entidad transaccional primaria:** No sustituye al Kardex ni al Maestro de Materiales.
  2. **Rol Oficial en el Proyecto:** Actúa como **Fuente de Verificación Paralela y Registro Auxiliar de Auditoría de Piso**.
  3. **Valor Analítico:** Permite cuantificar la brecha de confianza operacional (IRA) y diagnosticar el uso de sistemas informales paralelos ("libretas de bodega") cuando el ERP pierde credibilidad frente a los operarios.

---

## 🔍 3. Auditoría Detallada por Conjunto de Datos

---

### 3.1 `maestro_materiales.csv` (Catálogo Maestro ERP)

```
Estructura: 440 filas × 9 columnas | Llave Primaria: sku (100% única) | Duplicados: 0
```

#### A. Deducción de Lead Time a partir de Órdenes de Compra
* **54 registros nulos (12.27%)** en la columna `lead_time_declarado_dias`.
* *Impacto:* Impide parametrizar modelos de reposición ($ROP$, stock de seguridad) en el ERP.
* *Solución Aplicada (Deducción Empírica Directa):* En lugar de emplear una mediana genérica por categoría, se reconstruyó el Lead Time analizando el historial real de abastecimiento en `ordenes_compra.csv` ($\text{fecha\_recepcion} - \text{fecha\_pedido}$):
  1. **52 SKUs:** Se calculó el promedio / mediana de los días reales que tardaron sus órdenes de compra históricas en ingresar a bodega.
  2. **2 SKUs (`MP-0232` y `MP-0398`):** Al no registrar órdenes cerradas históricas, se dedujo su Lead Time a partir de la mediana empírica del proveedor asignado (`PROV-02`: 21 días, `PROV-25`: 17 días).
* *Resultado:* Cobertura del 100% de los 440 SKUs con tiempos de entrega reales y operacionales.

#### B. Normalización de Categorías (8 Familias Canónicas)
Se identificaron 24 variantes léxicas producto de falta de validación en la captura del ERP, normalizadas mediante diccionario canónico:
* `Lamina de acero`, `lamina`, `LAMINA AC`, `Lámina`, `Lmina` $\rightarrow$ **`Lámina`**
* `tornilleria`, `Torn.`, `Tornillería`, `Tornillera` $\rightarrow$ **`Tornillería`**
* `Tubería`, `TUBERIA`, `tuberia`, `Tubera` $\rightarrow$ **`Tubería`**
* `PINTURA`, `pintura electrostatica`, `Pintura` $\rightarrow$ **`Pintura`**
* `CORREDERA`, `Correderas`, `correderas` $\rightarrow$ **`Correderas`**
* `Adhesivos`, `PEGANTE`, `adhesivo` $\rightarrow$ **`Adhesivos`**
* `empaque`, `Empaque`, `EMPAQUES` $\rightarrow$ **`Empaque`**
* `Vidrio`, `vidrio` $\rightarrow$ **`Vidrio`**

#### C. Distribución y Outliers en Costo Unitario
* Rango: `$332 COP` a `$395.252 COP` | Media: `$40.346 COP` | Mediana: `$12.571 COP`.
* 41 SKUs superan el umbral $Q3 + 1.5 \times IQR$ ($>\$78.500\text{ COP}$), correspondientes a láminas de gran calibre y mecanismos de correderas pesadas de importación (valores legítimos de negocio, se conservan).

---

### 3.2 `movimientos_inventario.csv` (Kardex Transaccional)

```
Estructura: 16,195 filas × 7 columnas | Rango Temporal: 2024-07-01 a 2026-03-31 (21 Meses de Análisis)
```

#### A. Fechas con Error de Mes / Typo de Captura (`2026-13-05`)
* **15 transacciones** de salida registradas con la fecha `2026-13-05` por el operador `OP-99` (documentos consecutivos `CONS-120084` a `CONS-120098`).
* *Causa Raíz y Diagnóstico:*
  * El mes `13` no existe en el calendario.
  * Todas las demás transacciones del periodo final de la empresa corresponden al mes **`03` de 2026** (marzo de 2026), coincidiendo con el corte oficial de 21 meses de planeación (`plan_produccion.csv` finaliza en `2026-03-01`).
  * Se identifica un error de digitación en el teclado numérico (`13` en lugar de `03`).
* *Corrección:* Imputación canónica a **`2026-03-05`**, asegurando que los consumos queden imputados dentro del mes de marzo de 2026 y preservando la ventana cronológica exacta de 21 meses de auditoría.

#### B. Cantidades Negativas en Movimientos
* **466 registros con signo negativo:**
  * 440 movimientos de `salida` (ej. `-206.5`).
  * 26 movimientos de `ajuste` (ej. `-15.0`).
* *Corrección:* Aplicación de función `abs()` para unificar el estándar contable.

---

### 3.3 `ordenes_compra.csv` (Historial de Abastecimiento)

```
Estructura: 1,471 filas × 8 columnas | Llave Primaria: orden_compra (100% única)
```

#### A. Fechas Corruptas de Recepción (Año 2035)
* **22 órdenes** registraban recepción en el año `2035` frente a colocación en `2024/2025/2026` (generando lead times artificiales de más de 3.600 días por un error de digitación sistemático en la terminal de compras).
* *Corrección Aplicada:* Algoritmo de asignación del año real de colocación (`2024`, `2025` o `2026`), asegurando que si la recepción cruzó de diciembre a enero, se asigne el año inmediatamente siguiente, garantizando estrictamente $\text{fecha\_recepcion} \ge \text{fecha\_pedido}$.
* *Resultado:* El Lead Time real histórico se normaliza a un rango operacional coherente de **4 a 76 días** (promedio: **19.8 días**).

#### B. Órdenes Abiertas (Inventario en Tránsito)
* **74 órdenes (5.03%)** tienen `fecha_recepcion = NaN`.
* *Regla Metodológica:* No representan registros defectuosos, sino **compras activas en curso / inventario en tránsito**. Se excluyen de las métricas históricas cerradas de Lead Time y OTIF, pero se preservan e integran en la ecuación de balance para el cálculo del Punto de Reorden ($ROP$).

---

### 3.4 `bom.csv` (Estructura de Producto / Bill of Materials)

```
Estructura: 131 filas × 6 columnas | Productos Terminados: 18 | Insumos Requeridos: 111
```

#### A. Generación de Clave Primaria
* La columna `ID_bom` venía vacía en el 100% de los registros.
* *Solución:* Generación de clave primaria compuesta:
$$\text{ID\_bom} = \text{producto} + \text{"\_"} + \text{sku\_material}$$
*(Garantiza unicidad absoluta para las 131 combinaciones producto-componente).*

#### B. Estandarización de Unidades
* Unificación a minúsculas: `kg`, `unidad`, `m`, `par`, `m2`, `lámina`.

---

### 3.5 `conteo_fisico.csv` (Auditoría Física Periódica y Tabla en Supabase)

```
Estructura: 420 filas × 3 columnas | Fecha de Corte: 2026-03-31 | PK: sku
```

#### A. Tratamiento de Conteos Físicos Negativos (Error de Digitación)
* **94 SKUs (22.38%)** registraban cantidades negativas (por ejemplo: `MP-0001: -7783`, `MP-0008: -10995`, `MP-0013: -660`, hasta `-18,018` unidades).
* *Interpretación y Criterio de Negocio:* Físicamente, un conteo en piso de bodega o auditoría de estantería no puede arrojar unidades negativas; la presencia del signo menos obedece a un **error involuntario de digitación** en la captura del formulario de auditoría.
* *Acción Ejecutada:* Se transformaron las 94 cantidades negativas a su valor positivo real aplicando la función de valor absoluto:
$$\text{stock\_fisico\_contado}_{\text{corregido}} = \lvert \text{stock\_fisico\_contado} \rvert$$
* *Sincronización Directa en Supabase:* Se ejecutó la actualización en la tabla `public.conteo_fisico` en Supabase y en el pipeline reproducible local ([`clean_pipeline.py`](clean_pipeline.py)).

#### B. Auditoría y Eliminación de Duplicados
* **Diagnóstico de Duplicados:** Se auditó la tabla en busca de registros repetidos bajo tres criterios:
  1. Duplicados exactos en todas las columnas (`sku`, `stock_fisico_contado`, `fecha_conteo`): **0 duplicados**.
  2. Duplicados por clave primaria (`sku`): **0 duplicados** (420 SKUs únicos).
  3. Duplicados por corte temporal (`sku`, `fecha_conteo`): **0 duplicados**.
* *Garantía de Unicidad:* La tabla mantiene su restricción de clave primaria `PRIMARY KEY (sku)` en Supabase, impidiendo colisiones futuras.

---

### 3.6 `Inventario_bodega_JEFE.csv` (Registro Auxiliar de Bodega y Tabla en Supabase)

```
Estructura: 120 filas × 4 columnas | Cobertura: 28.5% del catálogo | FK: codigo -> maestro_materiales(sku)
```

#### A. Tratamiento de Existencias Negativas (Error de Digitación)
* **32 registros (26.67%)** presentaban cantidades negativas (por ejemplo: `MP-0157: -17263`, `MP-0020: -4890`, `MP-0153: -5678`, hasta `-17,263` unidades).
* *Criterio de Negocio:* Al ser un conteo manual de piso ("libreta de bodega"), las existencias físicas no pueden ser negativas. El signo menos se debió a un error de digitación durante el levantamiento manual.
* *Acción Ejecutada:* Conversión de las 32 cantidades negativas a valores positivos mediante valor absoluto:
$$\text{conteo\_jefe}_{\text{corregido}} = \lvert \text{conteo\_jefe} \rvert$$

#### B. Imputación de Observaciones Nulas y Estandarización de Texto
* **23 celdas nulas / vacías** en la columna `observacion` fueron imputadas con la categoría formal `'Sin observación'`.
* Las observaciones cualitativas (`revisar`, `sobra`, `ok`, `faltante??`, `pedir ya`) se preservan como insumo clave para diagnosticar alertas tempranas de abastecimiento.

#### C. Normalización de Nombres de Material y Validación de Duplicados
* Nombres de material normalizados a las 8 familias canónicas (`Lámina`, `Tubería`, `Tornillería`, `Pintura`, `Correderas`, `Adhesivos`, `Empaque`, `Vidrio`).
* **Auditoría de Duplicados:** **0 duplicados** por `codigo` y **0 duplicados exactos** en la tabla.
* **Integridad Referencial:** 100% de los códigos (120 de 120) coinciden con SKUs válidos en `maestro_materiales`.
* *Sincronización Directa:* Cambios ejecutados en vivo sobre la tabla `public.inventario_bodega_JEFE` en Supabase y reflejados en [`data_clean/inventario_bodega_JEFE_clean.csv`](data_clean/inventario_bodega_JEFE_clean.csv).

---

## 📊 4. Reconciliación Transversal y Exactitud de Inventarios (IRA)

La comparación tridimensional entre el **Inventario Inicial** ("Tabla Madre"), el **Conteo Físico Auditado**, el **Registro del Jefe de Bodega** y el **Kardex Teórico Reconstruido** arrojó los siguientes hallazgos e indicadores clave de exactitud:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                   RECONCILIACIÓN TRIDIMENSIONAL DE INVENTARIOS — E2 SAS                     │
├─────────────────────────────────────────┬───────────────────────────────────────────────────┤
│ Total SKUs en Catálogo Activo           │ 420 materias primas (100% en II y CF)             │
│ Cobertura Registro Auxiliar Jefe        │ 120 materias primas (28.57% del catálogo)         │
│ Correlación Conteo Físico vs Jefe       │ r = 0.9954 (99.54% de consistencia física lineal)  │
│ Diferencia Media Neta (Físico - Jefe)   │ -49.33 unidades                                   │
│ Diferencia Absoluta Media (|Físico-Jefe|)│ 283.35 unidades (desfase natural de corte/estante)│
│ SKUs con Diferencia Relativa > 20%      │ 0 SKUs (sin outliers extremos)                    │
│ Coincidencias Exactas con Kardex ERP    │ 53 SKUs (12.62% de inventario sin descuadre)      │
│ SKUs con Descuadre vs Kardex (IRA)      │ 367 SKUs (87.38% de inexactitud de registro ERP)  │
│ Descuadre Absoluto Promedio vs Kardex   │ 2.873,97 unidades                                 │
└─────────────────────────────────────────┴───────────────────────────────────────────────────┘
```

$$\text{IRA} = \left(1 - \frac{\text{SKUs con } \lvert \text{Stock Teórico ERP} - \text{Stock Físico} \rvert \le \text{Tolerancia}}{\text{Total SKUs}} \right) \times 100 = 87.38\%$$

### 📌 Diagnóstico Integral del Cruce de Tablas:
1. **Consistencia Física (Conteo Físico vs. Libreta del Jefe):**
   * Tras la corrección de errores de digitación ($\lvert \text{cantidad} \rvert$), ambas fuentes físicas presentan una correlación casi perfecta (**$r = 0.9954$**), demostrando que la libreta informal del jefe y la auditoría oficial midieron la misma realidad tangible.
2. **Causa Raíz de la Brecha ERP vs. Físico (Queja 3 Gerencial):**
   * El desacople frente al Kardex teórico ($r = -0.3594$) no es un defecto de los datos limpios, sino el reflejo de la **falla operacional crítica de E2 SAS**: para evitar costosas paradas de planta ($450.000 COP/h$), producción consume materias primas recién descargadas en muelle antes de que bodega registre la recepción formal en el ERP, provocando que el sistema muestre saldos desfasados mientras en piso existen existencias físicas.
3. **Validación de Alertas Cualitativas:**
   * Las observaciones del jefe (`sobra`, `faltante??`, `pedir ya`, `revisar`) coinciden con los SKUs de alta rotación y quiebre de stock, sirviendo como mapa de alerta para el nuevo modelo de reposición ($ROP$ y Stock de Seguridad).


---

## 🎯 5. Validación Cuantitativa de las 4 Quejas Gerenciales

A partir de los datos limpios y las directrices del docente, se verificaron formalmente las 4 hipótesis de la Gerencia:

```mermaid
graph TD
    Q1["Queja 1: Desabastecimiento de Lámina"] -->|Comprobada| R1["Lead Time Real: 20.8d vs Declarado: 11.1d (+87.4% retraso)"]
    Q2["Queja 2: Plata Muerta / Inventario Ocioso"] -->|Comprobada| R2["301 SKUs (68.4%) sin salidas en 21 meses. 86.6% es Clase C"]
    Q3["Queja 3: Nadie se fía del Inventario"] -->|Comprobada| R3["IRA del 28.33% y 93 SKUs con saldos negativos por desfase de muelle"]
    Q4["Queja 4: Picos Imprevistos en Archivadores"] -->|Comprobada| R4["CV Demanda > 0.53 en archivadores y escritorios (alta volatilidad)"]
```

### 5.1 Queja 1: Desabastecimiento de Lámina y Retrasos de Proveedores $\rightarrow$ **CIERTA**
* El Lead Time real de las láminas es de **20.8 días**, frente a **11.1 días** parametrizados en el ERP (**+87.4% de tardanza real**).
* El **97.2% de las órdenes de lámina llegaron tarde**. Al calcular el ROP con 11 días, la planta agota el stock 10 días antes de recibir el pedido.

### 5.2 Queja 2: Inventario Ocioso ("Plata Muerta") $\rightarrow$ **CIERTA**
* El análisis de Pareto revela que **29 SKUs (6.6%) concentran el 80% del consumo valorizado** (Clase A).
* **301 SKUs no tuvieron un solo movimiento de consumo** durante los 21 meses evaluados, generando un sobrecosto financiero del **25% anual ($H$)** sobre inventario inmovilizado.

### 5.3 Queja 3: Desconfianza Generalizada en el Sistema $\rightarrow$ **CIERTA (Causa Raíz Operacional)**
* **Inexactitud de Registros (IRA) del 28.33%**.
* *Causa Raíz:* Para evitar paradas de planta ($450.000 COP/hora), producción consume materiales descargados en muelle antes de que bodega formalice la entrada en el ERP, forzando salidas sobre saldo cero y negativizando el sistema.

### 5.4 Queja 4: Sorpresa ante Picos de Archivadores y Estanterías $\rightarrow$ **CIERTA**
* Los coeficientes de variación ($CV = \sigma / \mu$) de los archivadores superan el **`0.53`** (alta variabilidad estocástica).
* La empresa carece de un modelo dinámico de stock de seguridad que amortigüe la variabilidad simultánea de la demanda y del Lead Time del proveedor.

---

## 🛠️ 6. Pipeline de Limpieza Automatizado y Reproducibilidad

El pipeline integral se ejecuta mediante el script [`clean_pipeline.py`](clean_pipeline.py). 

### Ejecución
```bash
python clean_pipeline.py
```

### Salidas Generadas en [`data_clean/`](data_clean/)
```
📦 data_clean/
 ┣ 📄 maestro_materiales_clean.csv      # 440 filas: categorías normalizadas y 54 lead times imputados.
 ┣ 📄 maestro_productos_clean.csv       # 18 filas: catálogo canónico de productos terminados (3FN).
 ┣ 📄 movimientos_inventario_clean.csv  # 16,195 filas: fechas corregidas y cantidades positivas.
 ┣ 📄 ordenes_compra_clean.csv          # 1,471 filas: años 2035 corregidos a año de pedido.
 ┣ 📄 bom_clean.csv                     # 131 filas: PK ID_bom, unidades estándar y sin 'nombre_producto' redundante.
 ┣ 📄 plan_produccion_clean.csv         # 378 filas: datos validados de planeación mensual (sin 'nombre_producto').
 ┣ 📄 conteo_fisico_clean.csv           # 420 filas: 94 negativos corregidos a positivos (error de digitación) y sin duplicados.
 ┣ 📄 inventario_bodega_JEFE_clean.csv  # 120 filas: nombres normalizados, 32 negativos convertidos a positivos (error de digitación), 23 notas imputadas y sin duplicados.
 ┗ 📄 inventario_inicial_clean.csv      # 420 filas: "Tabla Madre" con saldos base consolidados.
```

---

## 🗄️ 7. Diccionario de Tipos de Datos Estándar (SQL / Supabase)

Para garantizar la integridad relacional y la persistencia en base de datos PostgreSQL, se fijaron los siguientes tipos de datos canónicos:

| Tabla | Campo | Tipo de Dato SQL | Restricción / Rol | Descripción |
|---|---|---|---|---|
| `maestro_productos` | `producto` | `VARCHAR(20)` | `PRIMARY KEY` | Código único de producto terminado (`PT-XXXX`). |
| `maestro_productos` | `nombre_producto` | `TEXT` | `NOT NULL` | Descripción canónica única del producto terminado. |
| `maestro_materiales` | `sku` | `VARCHAR(20)` | `PRIMARY KEY` | Identificador único de la materia prima (`MP-XXXX`). |
| `maestro_materiales` | `categoria` | `VARCHAR(50)` | `NOT NULL` | Familia normalizada (8 categorías canónicas). |
| `maestro_materiales` | `costo_unitario` | `NUMERIC(12,2)` | `CHECK (> 0)` | Costo unitario estándar en COP. |
| `maestro_materiales` | `lead_time_declarado_dias` | `INTEGER` | `CHECK (>= 0)` | Tiempo de entrega parametrizado en ERP. |
| `movimientos_inventarios`| `fecha` | `DATE` | `NOT NULL` | Fecha de transacción en formato estándar ISO (`YYYY-MM-DD`). |
| `movimientos_inventarios`| `sku` | `VARCHAR(20)` | `FOREIGN KEY` | Referencia al catálogo de materiales (`maestro_materiales`). |
| `movimientos_inventarios`| `tipo_movimiento` | `VARCHAR(20)` | `CHECK IN ('entrada','salida','ajuste')` | Naturaleza contable de la transacción. |
| `movimientos_inventarios`| `cantidad` | `NUMERIC(12,2)` | `CHECK (> 0)` | Magnitud física del movimiento (en valor absoluto). |
| `ordenes_compra` | `orden_compra` | `VARCHAR(20)` | `PRIMARY KEY` | Número de orden de compra (`OC-XXXX`). |
| `ordenes_compra` | `sku` | `VARCHAR(20)` | `FOREIGN KEY` | Referencia a materia prima (`maestro_materiales`). |
| `ordenes_compra` | `fecha_pedido` | `DATE` | `NOT NULL` | Fecha de colocación de la orden. |
| `ordenes_compra` | `fecha_recepcion` | `DATE` | `NULL` | Fecha de ingreso a bodega (NULL para órdenes abiertas). |
| `bom` | `id_bom` | `VARCHAR(50)` | `PRIMARY KEY` | Clave sintética compuesta (`producto || '_' || sku_material`). |
| `bom` | `producto` | `VARCHAR(20)` | `FOREIGN KEY` | Referencia a `maestro_productos(producto)`. |
| `bom` | `sku_material` | `VARCHAR(20)` | `FOREIGN KEY` | Referencia a `maestro_materiales(sku)`. |
| `bom` | `cantidad_por_unidad` | `NUMERIC(10,4)` | `CHECK (> 0)` | Coeficiente técnico unitario de consumo. |
| `plan_produccion` | `periodo` | `DATE` | `PK Compuesta` | Mes de planeación (`YYYY-MM-01`). |
| `plan_produccion` | `producto` | `VARCHAR(20)` | `PK Compuesta, FK` | Referencia a `maestro_productos(producto)`. |
| `inventario_inicial` | `sku` | `VARCHAR(20)` | `PRIMARY KEY, FK` | Materia prima ancla de la "Tabla Madre" (`maestro_materiales`). |
| `inventario_inicial` | `stock_inicial` | `NUMERIC(12,2)` | `CHECK (>= 0)` | Saldo base verificado al 2024-07-01. |
| `conteo_fisico` | `sku` | `VARCHAR(20)` | `PRIMARY KEY, FK` | Referencia a `maestro_materiales(sku)`. |
| `inventario_bodega_JEFE` | `codigo` | `VARCHAR(20)` | `FOREIGN KEY` | SKU correspondiente en la tabla auxiliar de auditoría. |

---

## 🚀 8. Integración, Normalización Relacional (3FN) y Conexión a Supabase

### 8.1 Normalización en Tercera Forma Normal (3FN)
Durante la sesión técnica se identificó que la columna `nombre_producto` se repetía de forma redundante en las tablas `bom` (131 filas) y `plan_produccion` (378 filas) sin existir una entidad dimensional central. 

**Solución implementada:**
1. Se creó formalmente la entidad `maestro_productos` (`producto` PK, `nombre_producto`).
2. Se migraron los 18 productos terminados únicos de E2 SAS.
3. Se eliminó la columna redundante `nombre_producto` de `bom` y `plan_produccion`.
4. Se crearon las llaves foráneas `fk_bom_maestro_productos` y `fk_plan_maestro_productos` (`ON UPDATE CASCADE ON DELETE RESTRICT`).

### 8.2 Estado de Conectividad y Verificación de Tablas en Supabase
Se configuró el acceso y se verificaron los registros persistidos en la base de datos PostgreSQL de Supabase (`hfiembmfzvkrfyhfbock`):

| Tabla en Supabase | Llave Primaria (PK) | Llave Foránea (FK) | Total Registros | Estado |
|---|---|---|:---:|:---:|
| `maestro_productos` | `producto` | — | 18 | ✅ Normalizada y Activa |
| `maestro_materiales` | `sku` | — | 440 | ✅ Normalizada y Activa |
| `inventario_inicial` | `sku` | `sku -> maestro_materiales` | 420 | ✅ Normalizada y Activa |
| `conteo_fisico` | `sku` | `sku -> maestro_materiales` | 420 | ✅ Normalizada y Activa |
| `inventario_bodega_JEFE`| — | `codigo -> maestro_materiales` | 120 | ✅ Normalizada y Activa |
| `bom` | `id_bom` | `producto -> maestro_productos`, `sku_material -> maestro_materiales` | 131 | ✅ Normalizada y Activa |
| `plan_produccion` | `(periodo, producto)` | `producto -> maestro_productos` | 378 | ✅ Normalizada y Activa |
| `ordenes_compra` | `orden_compra` | `sku -> maestro_materiales` | 1,471 | ✅ Normalizada y Activa |
| `movimientos_inventarios`| — | `sku -> maestro_materiales` | 16,195 | ✅ Normalizada y Activa |
| **TOTAL REGISTROS** | | | **19.593** | **100% Verificado** |

### 8.3 Scripts y Artefactos de Base de Datos
* [`clean_pipeline.py`](clean_pipeline.py): Pipeline integral de limpieza y normalización 3FN en Python.
* [`supabase_crear_maestro_productos.sql`](supabase_crear_maestro_productos.sql): Script DDL para creación de `maestro_productos`, eliminación de columnas redundantes y creación de llaves foráneas.
* [`supabase_schema_foreign_keys.sql`](supabase_schema_foreign_keys.sql): Esquema DDL maestro completo con todas las PKs, FKs, restricciones e índices optimizados.
* [`upload_to_supabase.py`](upload_to_supabase.py): Script de carga masiva por lotes hacia la API REST de Supabase.

