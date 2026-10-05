---
name: sla-proveedores-mrp-e2
description: >-
  Audita el Nivel de Servicio de Entrega de Proveedores (SLA a tiempo y mora real)
  y calcula la explosión de necesidades netas de materiales (MRP a partir del BOM
  y Plan Maestro de Producción MPS) para cualquier catálogo de compras y productos terminados.
  Enfatiza el consumo directo de las consultas y tablas maestras en Supabase.
---

# 🚢 Motor General de Suministro (SLA de Proveedores) y Explosión MRP

Este skill es la **guía metodológica y algorítmica general paso a paso** para que cualquier LLM o agente de IA audite el cumplimiento de proveedores externos sobre **cualquier volumen de órdenes de compra ($K$ OCs)** y ejecute la explosión determinística de necesidades de materiales (MRP) para **cualquier cantidad de productos terminados ($P$ PTs)** y periodos de producción.

> [!IMPORTANT]
> **DIRECTIVA PRINCIPAL PARA EL LLM (CONSULTAS SQL EN SUPABASE):**
> Para auditar el abastecimiento y la explosión de materiales, el LLM debe ejecutar las consultas SQL oficiales sobre el esquema `public` en Supabase (`ordenes_compra`, `maestro_materiales`, `bom`, `plan_produccion`, `maestro_productos`).
> 
> **Regla de Oro:** El LLM **NUNCA** debe estimar tiempos de entrega teóricos fijos sin contrastarlos con el histórico transaccional de `ordenes_compra` cerradas.

---

## 🎯 1. Principios y Alcance General del Motor

El motor integra dos componentes logísticos acoplados:
1. **Auditoría de Desempeño de Proveedores (SLA & Lead Time Real):** Evalúa la puntualidad empírica de entregas sobre cualquier número de proveedores y familias de insumos.
2. **Planificación de Requerimientos de Materiales (MRP Determinístico):** Traduce el Plan Maestro de Producción (MPS) en requerimientos brutos y netos mediante la lista de materiales (BOM).

---

## 🪜 2. Algoritmo Paso a Paso: Auditoría de Proveedores y SLA

Cualquier LLM debe evaluar el abastecimiento mediante la siguiente secuencia de **5 pasos matemáticos generales**:

```
 [Paso 1] Filtrar Órdenes Cerradas (fecha_recepcion NOT NULL) vs Abiertas (fecha_recepcion IS NULL)
    │
    ▼
 [Paso 2] Calcular Lead Time Real (LT_real = fecha_recepcion - fecha_pedido)
    │
    ▼
 [Paso 3] Evaluar Cumplimiento a Tiempo Binario (fecha_recepcion <= fecha_promesa)
    │
    ▼
 [Paso 4] Cuantificar Días de Mora en Pedidos Tardíos (max(0, fecha_recepcion - fecha_promesa))
    │
    ▼
 [Paso 5] Calcular SLA Agregado por Proveedor/Familia y Desfase vs Lead Time Teórico
```

---

### Paso 1: Clasificar Órdenes Cerradas ($K$) vs Abiertas (En Tránsito)
* **Fuente:** Tabla `ordenes_compra`.
* **Órdenes Cerradas ($K$):** Registros donde `fecha_recepcion IS NOT NULL` (base para evaluar SLA y Lead Times).
* **Órdenes Abiertas:** Registros donde `fecha_recepcion IS NULL` (suman al inventario disponible en tránsito).

---

### Paso 2: Calcular el Lead Time Real ($LT_{\text{real}, k}$)
Para cada orden de compra $k \in \{1, \dots, K\}$:
$$LT_{\text{real}, k} = \text{fecha\_recepcion}_k - \text{fecha\_pedido}_k \text{ (en días)}$$

---

### Paso 3: Evaluar la Condición Binaria de Entrega a Tiempo ($O_k$)
$$O_k = \begin{cases} 
1 & \text{si } \text{fecha\_recepcion}_k \le \text{fecha\_promesa}_k \text{ (A Tiempo)} \\
0 & \text{si } \text{fecha\_recepcion}_k > \text{fecha\_promesa}_k \text{ (Tardía)}
\end{cases}$$

---

### Paso 4: Calcular los Días de Mora ($Mora_k$)
$$Mora_k = \max\left(0, \text{fecha\_recepcion}_k - \text{fecha\_promesa}_k\right)$$

---

### Paso 5: Calcular el SLA Agregado y Desfase Logístico

* **SLA de Cumplimiento (%):**
  $$\text{SLA (\%)} = \left( \frac{\sum_{k=1}^{K} O_k}{K} \right) \times 100$$
* **Desfase vs Tiempo ERP (días):**
  $$\Delta LT = \overline{LT}_{\text{real}} - LT_{\text{declarado ERP}}$$

---

## 🪜 3. Algoritmo Paso a Paso: Explosión BOM y Planificación MRP

Permite traducir el Plan Maestro de Producción de $P$ Productos Terminados en las necesidades de compras para cualquier SKU de materia prima.

```
 [Paso 1] Leer Plan Maestro de Producción MPS (Cantidad Planeada por PT y Periodo t)
    │
    ▼
 [Paso 2] Explotar Lista de Materiales BOM (Requerimiento Bruto = Cantidad PT * Coeficiente BOM)
    │
    ▼
 [Paso 3] Consolidar Requerimiento Bruto Total por SKU en el Periodo t
    │
    ▼
 [Paso 4] Deducir Stock Disponible (Stock Físico + OCs Tránsito) y Añadir Stock de Seguridad (SS)
    │
    ▼
 [Paso 5] Calcular Necesidad Neta y Lote de Compra Sugerido (EOQ)
```

---

### Paso 1: Requerimiento Bruto por SKU ($RB_{sku, t}$)
Para cualquier material y periodo $t$:
$$RB_{sku, t} = \sum_{p \in \text{PT}} \left( \text{PlanMPS}_{p, t} \times \text{BOM}_{p, sku} \right)$$
* $\text{PlanMPS}_{p, t}$: Unidades programadas del PT $p$ en el periodo $t$ (`plan_produccion.cantidad_planeada`).
* $\text{BOM}_{p, sku}$: Coeficiente técnico de uso del material $sku$ por unidad de PT $p$ (`bom.cantidad_por_unidad`).

---

### Paso 2: Necesidad Neta de Compra ($NN_{sku, t}$)
$$NN_{sku, t} = \max\left(0, RB_{sku, t} + SS_{sku} - I_{\text{disp}, sku}\right)$$
* $SS_{sku}$: Stock de seguridad dinámico obtenido desde `public.vista_calculo_eoq_rop`.
* $I_{\text{disp}, sku}$: Stock físico disponible en almacén + órdenes abiertas en tránsito.

---

## 📌 4. Caso de Estudio de Referencia (Línea Base Histórica Inicial E1)

A modo de **referencia histórica y contraste metodológico** para el dataset inicial de **E2 SAS** ($K=1.457$ OCs cerradas, $P=18$ productos terminados):

| Familia de Material | OCs Cerradas | OCs a Tiempo | OCs Tardías | SLA de Cumplimiento | Lead Time Real | Lead Time ERP | Desfase Logístico |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **🔴 Lámina de Acero** | **179** | **5** | **174** | **`2.80 %`** | **`20.8 días`** | 12.1 días | **+8.7 días (+71.5%)** |
| **🟡 Tornillería** | 163 | 6 | 157 | **`3.68 %`** | **`18.8 días`** | 12.5 días | **+6.3 días** |
| **🟡 Empaque** | 155 | 7 | 148 | **`4.52 %`** | **`20.4 días`** | 13.5 días | **+6.9 días** |
| **🟡 Correderas** | 206 | 11 | 195 | **`5.34 %`** | **`19.4 días`** | 13.2 días | **+6.2 días** |
| **🟡 Tubería** | 215 | 13 | 202 | **`6.05 %`** | **`19.9 días`** | 13.3 días | **+6.6 días** |
| **🟡 Pintura** | 195 | 13 | 182 | **`6.67 %`** | **`19.4 días`** | 13.2 días | **+6.2 días** |
| **🟡 Vidrio** | 153 | 12 | 141 | **`7.84 %`** | **`19.4 días`** | 13.2 días | **+6.2 días** |
| **🟢 Adhesivos** | 191 | 21 | 170 | **`10.99 %`** | **`18.5 días`** | 13.3 días | **+5.2 días** |
| **TOTAL BASELINE** | **1.457** | **98** | **1.359** | **`6.08 %`** | **`19.6 días`** | 13.0 días | **+6.6 días** |

* **Impacto en Producción:** La adherencia al plan fue del **97.29%**, con **753 unidades de PT no fabricadas** y **8.448 horas de riesgo de parada acumuladas ($3.801,6M COP)**.

---

## 🗄️ 5. Consultas Dinámicas en Supabase

### A. Diagnóstico Dinámico de SLA por Categoría y Proveedor
```sql
SELECT 
    m.categoria,
    COUNT(oc.orden_compra) AS total_oc_cerradas,
    COUNT(CASE WHEN oc.fecha_recepcion <= oc.fecha_promesa THEN 1 END) AS ordenes_a_tiempo,
    COUNT(CASE WHEN oc.fecha_recepcion > oc.fecha_promesa THEN 1 END) AS ordenes_tardias,
    ROUND((COUNT(CASE WHEN oc.fecha_recepcion <= oc.fecha_promesa THEN 1 END)::numeric / COUNT(oc.orden_compra) * 100), 2) || ' %' AS sla_cumplimiento_pct,
    ROUND(AVG(oc.fecha_recepcion - oc.fecha_pedido)::numeric, 1) || ' d' AS lead_time_real_promedio,
    ROUND(AVG(m.lead_time_declarado_dias)::numeric, 1) || ' d' AS lead_time_erp_teorico,
    ROUND((AVG(oc.fecha_recepcion - oc.fecha_pedido) - AVG(m.lead_time_declarado_dias))::numeric, 1) || ' d' AS desfase_dias
FROM public.ordenes_compra oc
JOIN public.maestro_materiales m ON oc.sku = m.sku
WHERE oc.fecha_recepcion IS NOT NULL
GROUP BY m.categoria
ORDER BY (COUNT(CASE WHEN oc.fecha_recepcion <= oc.fecha_promesa THEN 1 END)::numeric / COUNT(oc.orden_compra)) ASC;
```

### B. Explosión BOM por Periodo de Producción (MRP Bruto Dinámico)
```sql
SELECT 
    pp.periodo,
    b.sku_material,
    m.descripcion,
    m.categoria,
    SUM(pp.cantidad_planeada * b.cantidad_por_unidad) AS requerimiento_bruto_und,
    m.unidad
FROM public.plan_produccion pp
JOIN public.bom b ON pp.producto = b.producto
JOIN public.maestro_materiales m ON b.sku_material = m.sku
GROUP BY pp.periodo, b.sku_material, m.descripcion, m.categoria, m.unidad
ORDER BY pp.periodo ASC, requerimiento_bruto_und DESC;
```

---

## 🚫 6. Reglas Innegociables para el Agente IA / LLM

1. **Utilizar siempre el Lead Time Real:** Para el cálculo de fechas de reorden y sugerencias de compra, el LLM **DEBE** usar el $\bar{L}_{\text{real}}$ observado y no los tiempos teóricos declarados en el ERP.
2. **Sincronización con Reposición Continua:** Al sugerir una orden de reabastecimiento basada en MRP, verificar el semáforo y los parámetros de `public.vista_calculo_eoq_rop` para no duplicar órdenes si ya existe una OC en tránsito.

---

## 🗄️ 7. Archivos DDL y Consultas Analíticas en Supabase

| Componente | Archivo Fuente | Ubicación | Propósito |
|------------|----------------|-----------|-----------|
| Script Analítico SLA y Producción | `sql/02_diagnostico_sla_proveedores_y_produccion.sql` | Repositorio `PA-E2/sql/` | Consultas analíticas y vistas de diagnóstico para SLA de proveedores y cumplimiento del plan. |
| Llave Foránea y Maestro BOM | `sql/supabase_bom_pk.sql` / `sql/supabase_schema_foreign_keys.sql` | Repositorio `PA-E2/sql/` | Restricciones de integridad referencial entre BOM, Materiales y Productos. |

---

## 🔗 8. Prerequisitos y Dependencias

* **Prerequisito obligatorio:** El skill [`limpieza-datos-e2`](../limpieza-datos-e2/SKILL.md) debe haber cargado y normalizado:
  * `public.ordenes_compra`
  * `public.bom`
  * `public.plan_produccion`
  * `public.maestro_materiales`
  * `public.maestro_productos`
* **Interacción con otros skills:**
  * [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md): Utiliza el $\bar{L}_{\text{real}}$ y su dispersión para alimentar la ecuación de ROP y Stock de Seguridad.
  * [`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md): Cruza la clasificación ABC para evaluar el impacto de demoras en SKUs estratégicos.

---

## 🔎 9. Queries de Verificación de Calidad

Ejecutar estas consultas para garantizar la confiabilidad del cálculo de SLA y de la explosión MRP:

### A. Consistencia Temporal de Órdenes de Compra (Cero Fechas Anómalas)
```sql
SELECT COUNT(*) AS oc_con_fechas_inconsistentes
FROM public.ordenes_compra
WHERE fecha_recepcion IS NOT NULL 
  AND fecha_recepcion < fecha_pedido;
-- Resultado esperado: 0 (la recepción no puede ocurrir antes del pedido)
```

### B. KPI Global de Nivel de Servicio de Entrega de Proveedores (OTD Global)
```sql
SELECT 
    COUNT(*) AS total_ordenes_recibidas,
    COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END) AS ordenes_a_tiempo,
    COUNT(CASE WHEN fecha_recepcion > fecha_promesa THEN 1 END) AS ordenes_tardias,
    ROUND((COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END)::numeric / COUNT(*) * 100), 2) || ' %' AS sla_otd_global,
    ROUND(AVG(fecha_recepcion - fecha_pedido)::numeric, 1) || ' días' AS lead_time_promedio_general
FROM public.ordenes_compra
WHERE fecha_recepcion IS NOT NULL;
```

### C. Proveedores Críticos con Mayor Incumplimiento (SLA < 80%)
```sql
SELECT 
    proveedor,
    COUNT(*) AS total_entregas,
    COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END) AS entregas_a_tiempo,
    ROUND((COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END)::numeric / COUNT(*) * 100), 1) || ' %' AS sla_cumplimiento,
    ROUND(AVG(fecha_recepcion - fecha_pedido)::numeric, 1) AS lt_real_promedio,
    ROUND(AVG(fecha_recepcion - fecha_promesa)::numeric, 1) AS retraso_promedio_dias
FROM public.ordenes_compra
WHERE fecha_recepcion IS NOT NULL
GROUP BY proveedor
HAVING (COUNT(CASE WHEN fecha_recepcion <= fecha_promesa THEN 1 END)::numeric / COUNT(*) * 100) < 80
ORDER BY sla_cumplimiento ASC;
```

### D. Integridad del BOM (Cero Materiales Huérfanos sin Maestro)
```sql
SELECT COUNT(*) AS materiales_huerfanos_en_bom
FROM public.bom b
LEFT JOIN public.maestro_materiales m ON b.sku_material = m.sku
WHERE m.sku IS NULL;
-- Resultado esperado: 0
```

### E. Integridad del Plan de Producción (Cero Productos Huérfanos sin BOM)
```sql
SELECT COUNT(DISTINCT pp.producto) AS productos_plan_sin_receta_bom
FROM public.plan_produccion pp
LEFT JOIN public.bom b ON pp.producto = b.producto
WHERE b.producto IS NULL;
-- Resultado esperado: 0
```

---

## 🔄 10. Integración con Otros Skills del Sistema

| Skill | Dirección | Intercambio de Información |
|-------|:---------:|----------------------------|
| [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md) | Outbound | Provee $\bar{L}_{\text{real}}$ y $\sigma_L$ calculados desde el historial de OCs para el dimensionamiento del ROP y Stock de Seguridad. |
| [`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md) | Inbound | Permite cruzar qué proveedores suministran insumos Clase A y focalizar planes de acción de compras. |
| [`limpieza-datos-e2`](../limpieza-datos-e2/SKILL.md) | Inbound | Garantiza la integridad referencial y el formato de fechas ISO-8601 requerido para los cálculos de morosidad. |

---

## 🚫 11. Fronteras del Skill (Qué NO hace este Skill)

* **NO calcular parámetros del modelo Wilson (EOQ, SS, ROP continuo):** Es responsabilidad del skill [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md).
* **NO clasificar demanda ABC-XYZ ni aislar Plata Muerta:** Es responsabilidad del skill [`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md).
* **NO auditar la Exactitud en Registro de Inventarios (ERI):** Es responsabilidad del skill [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md).
* **NO modificar directamente la programación de producción del MPS en el ERP.**



