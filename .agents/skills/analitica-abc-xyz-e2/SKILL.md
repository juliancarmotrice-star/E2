---
name: analitica-abc-xyz-e2
description: >-
  Aplica la clasificación paramétrica ABC (Pareto por valor de consumo 80/15/5)
  y segmentación XYZ (variabilidad de demanda) para E2 SAS.
  Utilícese para identificar SKUs estratégicos Clase A, aislar los 301 SKUs de
  Plata Muerta Clase C y orientar políticas de inventario diferenciadas.
---

# Motor de Segmentación ABC - XYZ y Plata Muerta — E2 SAS

Este skill estandariza la segmentación multicriterio de las 420 materias primas de **E2 SAS** según su impacto financiero y predictibilidad operativa.

---

## 📌 Parámetros de Clasificación de Pareto

La clasificación ABC monetaria se basa en el **Valor Total Consumido** en el horizonte de 21 meses:
$$\text{Valor Consumido} = \text{Consumo Total (unidades)} \times \text{Costo Unitario (COP)}$$

| Categoría ABC | Umbral de Participación Acumulada | Descripción y Política de Gestión |
|:---:|:---:|---|
| **🅰️ Clase A** | **`0.0%` a `80.0%`** | **Insumos Estratégicos:** Representan el 80% del valor. Requieren control diario, conteo cíclico estricto y negociación prioritaria con proveedores. |
| **🅱️ Clase B** | **`80.0%` a `95.0%`** | **Insumos Intermedios:** 15% del valor. Control quincenal/mensual y reposición por $EOQ$ estándar. |
| **🅲 Clase C** | **`95.0%` a `100.0%`** | **Insumos Marginales / Plata Muerta:** 5% del valor. Incluye 301 SKUs sin ningún movimiento en 21 meses ($3.550M COP inmovilizados). |

---

## 📊 Segmentación por Variabilidad de Demanda (XYZ)

La clasificación XYZ mide la estabilidad del consumo mensual mediante el **Coeficiente de Variación ($CV$)**:
$$CV = \frac{\sigma_{\text{demanda}}}{\bar{d}_{\text{demanda}}}$$

| Clase XYZ | Criterio de Variabilidad | Comportamiento | Estrategia de Reposición |
|:---:|:---:|---|---|
| **X** | $CV \le 0.50$ | Demanda estable y predecible | Reposición automática por $EOQ / ROP$ con bajo Stock de Seguridad. |
| **Y** | $0.50 < CV \le 1.00$ | Demanda moderadamente variable | Reposición con $SS$ dinámico ajustado por variabilidad de proveedor. |
| **Z** | $CV > 1.00$ o intermitente | Demanda errática / sin consumo | Reposición bajo pedido (JIT / Make to Order). Congelar stock de seguridad. |

---

## 🧊 Protocolo para SKUs de "Plata Muerta" (Inmovilizados)

Si un material tiene $\text{Consumo} = 0$:
1. **Clasificación:** Automáticamente asignado como **Clase C / Z (Plata Muerta)**.
2. **Costo de Posesión:** Calcular $H \times \text{Saldo Valorizado} = 0.25 \times (\text{Stock} \times C_u)$.
3. **Regla de Compra:** **BLOQUEO TOTAL**. Queda estrictamente prohibido emitir o sugerir nuevas Órdenes de Compra.
4. **Acción Operativa:** El Agente debe sugerir al Jefe de Planta:
   - Reutilización en nuevos diseños de mobiliario.
   - Devolución / canje a proveedores.
   - Venta como chatarra o remate para liberar espacio físico en bodega.

---

## 🗄️ Consulta Oficial en Supabase

```sql
SELECT 
    sku,
    descripcion,
    categoria,
    costo_unitario_formato,
    consumo_unidades_total,
    valor_consumo_formato,
    pct_participacion_individual,
    pct_participacion_acumulada,
    clasificacion_abc,
    tipo_rotacion
FROM public.vista_clasificacion_abc
ORDER BY valor_consumo_cop DESC;
```
