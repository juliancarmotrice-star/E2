---
name: sla-proveedores-mrp-e2
description: >-
  Audita el Nivel de Servicio de Entrega de Proveedores (SLA a tiempo y mora real)
  y calcula la explosión de necesidades netas de materiales (MRP a partir del BOM
  y Plan Maestro de Producción MPS) para E2 SAS.
---

# Motor de Suministro (SLA de Proveedores) y Explosión MRP — E2 SAS

Este skill estandariza la evaluación estadística del abastecimiento externo y la planificación de materiales requeridos para la fabricación de mobiliario metálico en **E2 SAS**.

---

## 📌 1. Auditoría de SLA y Lead Time de Proveedores

El SLA evalúa la confiabilidad temporal de los proveedores sobre las Órdenes de Compra cerradas:

### A. Fórmulas de Suministro
$$\text{SLA de Entrega (\%)} = \frac{\text{OCs con } \text{fecha\_recepcion} \le \text{fecha\_promesa}}{\text{Total OCs cerradas}} \times 100$$
$$\text{Lead Time Real (días)} = \text{fecha\_recepcion} - \text{fecha\_pedido}$$
$$\text{Mora en Pedidos Tardíos (días)} = \text{fecha\_recepcion} - \text{fecha\_promesa} \quad (\text{para } \text{recepción} > \text{promesa})$$

### B. Línea Base Diagnosticada por Familia de Materiales

| Familia de Material | OCs Cerradas | OCs a Tiempo | OCs Tardías | SLA de Cumplimiento | Lead Time Real | Lead Time ERP | Desfase |
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

## 🏭 2. Plan Maestro de Producción (MPS) y Explosión BOM (MRP)

### A. Cumplimiento del Plan de Producción
$$\text{Adherencia al MPS (\%)} = \frac{\sum \text{Cantidad Real Producida}}{\sum \text{Cantidad Planeada}} \times 100 = \mathbf{97.29\%}$$
* **Incumplimiento:** En 19 de los 21 meses evaluados, la planta no alcanzó la meta de ensamble de producto terminado debido a quiebres de lámina y herrajes (753 unidades PT no fabricadas).

### B. Explosión Determinística de Materiales (BOM)
Para cualquier mes o lote programado en el MPS:
$$\text{Requerimiento Bruto}_{sku} = \sum_{p \in \text{Productos}} \left( \text{PlanMPS}_{p} \times \text{BOM}_{p, sku} \right)$$
$$\text{Necesidad Neta}_{sku} = \max\left(0, \text{Requerimiento Bruto}_{sku} + SS_{sku} - \text{Stock Disponible}_{sku}\right)$$

---

## 🗄️ Consultas Oficiales en Supabase

### A. Consulta de SLA por Categoría
```sql
SELECT 
    m.categoria,
    COUNT(oc.orden_compra) AS total_oc_cerradas,
    COUNT(CASE WHEN oc.fecha_recepcion <= oc.fecha_promesa THEN 1 END) AS ordenes_a_tiempo,
    COUNT(CASE WHEN oc.fecha_recepcion > oc.fecha_promesa THEN 1 END) AS ordenes_retrasadas,
    ROUND((COUNT(CASE WHEN oc.fecha_recepcion <= oc.fecha_promesa THEN 1 END)::numeric / COUNT(oc.orden_compra) * 100), 2) || ' %' AS sla_cumplimiento_pct,
    ROUND(AVG(oc.fecha_recepcion - oc.fecha_pedido)::numeric, 1) || ' d' AS lead_time_real,
    ROUND(AVG(m.lead_time_declarado_dias)::numeric, 1) || ' d' AS lead_time_erp
FROM public.ordenes_compra oc
JOIN public.maestro_materiales m ON oc.sku = m.sku
WHERE oc.fecha_recepcion IS NOT NULL
GROUP BY m.categoria
ORDER BY sla_cumplimiento_pct ASC;
```

### B. Explosión BOM para un Periodo del MPS
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
