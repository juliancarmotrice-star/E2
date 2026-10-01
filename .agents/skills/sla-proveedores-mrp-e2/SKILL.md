---
name: sla-proveedores-mrp-e2
description: >-
  Audita el Nivel de Servicio de Entrega de Proveedores (SLA a tiempo y mora real)
  y calcula la explosión de necesidades netas de materiales (MRP a partir del BOM
  y Plan Maestro de Producción MPS) para E2 SAS.
  Enfatiza el consumo directo de las consultas y tablas maestras en Supabase.
---

# 🚢 Motor de Suministro (SLA de Proveedores) y Explosión MRP — E2 SAS

Este skill es la **guía canónica de razonamiento paso a paso** para que cualquier LLM o agente de IA audite el cumplimiento de proveedores externos, cuantifique el riesgo de parada de planta y ejecute la explosión de materiales (MRP) a partir de la lista BOM de **E2 SAS**.

> [!IMPORTANT]
> **DIRECTIVA PRINCIPAL PARA EL LLM (CONSULTAS SQL EN SUPABASE):**
> Para auditar el abastecimiento y la explosión de materiales, el LLM debe ejecutar las consultas SQL oficiales sobre el esquema `public` en Supabase (`ordenes_compra`, `maestro_materiales`, `bom`, `plan_produccion`, `maestro_productos`).
> 
> **Regla de Oro:** El LLM **NUNCA** debe estimar tiempos de entrega teóricos sin contrastarlos con el histórico de `ordenes_compra` cerradas.

---

## 🎯 1. Contexto Operativo y Diagnóstico de Suministro

En **E2 SAS**, el abastecimiento de materias primas enfrenta un cuello de botella crítico:
1. **Colapso en SLA de Proveedores:** El cumplimiento general de entrega a tiempo es de apenas **`6.08%`** (1,359 de 1,457 pedidos llegaron tarde).
2. **Crisis en Lámina de Acero:** El SLA en lámina es de apenas **`2.80%`** con un Lead Time real promedio de **`20.8 días`** frente a los **`12.1 días`** declarados en el ERP (**+71.5% de desfase**).
3. **Incumplimiento en Ensamble de PT:** La falta de láminas y herrajes causó incumplimiento del Plan de Producción en 19 de los 21 meses evaluados (**753 unidades de PT no fabricadas** y **8,448 horas de riesgo de parada acumuladas = $3,801.6M COP**).

---

## 🪜 2. Algoritmo Paso a Paso: Auditoría de Proveedores y SLA

Cualquier LLM debe evaluar el abastecimiento mediante la siguiente secuencia de **5 pasos determinísticos**:

```
 [Paso 1] Filtrar Órdenes Cerradas (fecha_recepcion NOT NULL)
    │
    ▼
 [Paso 2] Calcular Lead Time Real (fecha_recepcion - fecha_pedido)
    │
    ▼
 [Paso 3] Evaluar Cumplimiento a Tiempo (fecha_recepcion <= fecha_promesa)
    │
    ▼
 [Paso 4] Cuantificar Días de Mora (fecha_recepcion - fecha_promesa)
    │
    ▼
 [Paso 5] Calcular SLA Porcentual y Desfase vs Lead Time Teórico del ERP
```

---

### Paso 1: Filtrar Órdenes de Compra Cerradas vs Abiertas
* **Fuente:** Tabla `ordenes_compra`.
* **Órdenes Cerradas:** Registros donde `fecha_recepcion IS NOT NULL` ($N = 1,457$ órdenes).
* **Órdenes Abiertas (En Tránsito):** Registros donde `fecha_recepcion IS NULL` ($N = 74$ órdenes activas).

---

### Paso 2: Calcular el Lead Time Real ($LT_{\text{real}}$)
Para cada orden de compra $k$:
$$LT_{\text{real}, k} = \text{fecha\_recepcion}_k - \text{fecha\_pedido}_k \text{ (en días)}$$

---

### Paso 3: Evaluar la Condición Binaria de Entrega a Tiempo ($O_k$)
$$O_k = \begin{cases} 
1 & \text{si } \text{fecha\_recepcion}_k \le \text{fecha\_promesa}_k \text{ (A Tiempo)} \\
0 & \text{si } \text{fecha\_recepcion}_k > \text{fecha\_promesa}_k \text{ (Tardía)}
\end{cases}$$

---

### Paso 4: Calcular los Días de Mora en Pedidos Tardíos ($Mora_k$)
$$Mora_k = \max\left(0, \text{fecha\_recepcion}_k - \text{fecha\_promesa}_k\right)$$

---

### Paso 5: Calcular el SLA Agregado y Desfase Logístico

* **SLA de Cumplimiento (%):**
  $$\text{SLA (\%)} = \left( \frac{\sum_{k=1}^{K} O_k}{K} \right) \times 100$$
* **Desfase vs ERP (días):**
  $$\Delta LT = \overline{LT}_{\text{real}} - LT_{\text{declarado ERP}}$$

---

### 📊 Scorecard de Proveedores por Familia (Línea Base E1)

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
| **TOTAL GENERAL** | **1.457** | **98** | **1.359** | **`6.08 %`** | **`19.6 días`** | 13.0 días | **+6.6 días** |

---

## 🪜 3. Algoritmo Paso a Paso: Explosión BOM y Planificación MRP

Permite traducir el Plan Maestro de Producción de Productos Terminados (MPS) en las necesidades brutas y netas de materias primas.

```
 [Paso 1] Leer Plan Maestro de Producción MPS (Cantidad Planeada por PT y Periodo)
    │
    ▼
 [Paso 2] Explotar Lista de Materiales BOM (Requerimiento Bruto = Cantidad PT * Coeficiente BOM)
    │
    ▼
 [Paso 3] Consolidar Requerimiento Bruto Total por SKU
    │
    ▼
 [Paso 4] Deducir Stock Disponible (Stock Físico + OCs Tránsito) y Añadir Stock Seguridad (SS)
    │
    ▼
 [Paso 5] Calcular Necesidad Neta y Lote de Compra Sugerido (EOQ)
```

---

### Paso 1: Requerimiento Bruto por SKU ($RB_{sku, t}$)
Para un periodo o mes $t$:
$$RB_{sku, t} = \sum_{p \in \text{PT}} \left( \text{PlanMPS}_{p, t} \times \text{BOM}_{p, sku} \right)$$
* $\text{PlanMPS}_{p, t}$: Unidades del producto terminado $p$ a fabricar en el mes $t$ (`plan_produccion.cantidad_planeada`).
* $\text{BOM}_{p, sku}$: Consumo unitario del material $sku$ por cada unidad de producto $p$ (`bom.cantidad_por_unidad`).

---

### Paso 2: Necesidad Neta de Compra ($NN_{sku, t}$)
$$NN_{sku, t} = \max\left(0, RB_{sku, t} + SS_{sku} - I_{\text{disp}, sku}\right)$$
* $SS_{sku}$: Stock de seguridad dinámico obtenido desde `public.vista_calculo_eoq_rop`.
* $I_{\text{disp}, sku}$: Stock físico en bodega + órdenes en tránsito.

---

## 🗄️ 4. Consultas Oficiales en Supabase

### A. Diagnóstico de SLA por Categoría y Proveedor
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

### B. Explosión BOM por Periodo de Producción (MRP Bruto)
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

## 🚫 5. Reglas Innegociables para el Agente IA / LLM

1. **Utilizar siempre el Lead Time Real:** Para el cálculo de fechas de reorden y sugerencias de compra, el LLM **DEBE** usar el $\bar{L}_{\text{real}}$ observado ($20.8$ días en lámina) y no los $12.1$ días teóricos del ERP.
2. **Sincronización con Reposición Continua:** Al sugerir una orden de reabastecimiento basada en MRP, verificar el semáforo y los parámetros de `public.vista_calculo_eoq_rop` para no duplicar órdenes si ya existe una OC en tránsito.

