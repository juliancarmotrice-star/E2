---
name: reposicion-eoq-rop-e2
description: >-
  Calcula de forma determinística los parámetros de reposición continua (EOQ,
  ROP y Stock de Seguridad con nivel de servicio Z=95%) para E2 SAS.
  Utilícese para emitir sugerencias de compra, evaluar semáforos de stock,
  cuantificar inversión y prevenir quiebres de materiales sin alucinaciones.
---

# Motor de Reposición Determinística (EOQ / ROP / SS) — E2 SAS

Este skill estandariza el cálculo del modelo de inventarios de revisión continua $(s, Q)$ para las 420 materias primas de **E2 SAS**.
**Regla de oro:** El agente **NUNCA** calcula fórmulas matemáticas de memoria; consulta la vista SQL en Supabase o ejecuta el script determinístico.

---

## 📌 Parámetros Económicos Oficiales del Negocio

Los cálculos utilizan estrictamente los parámetros financieros acordados para E2 SAS:

| Parámetro | Símbolo | Valor Oficial | Unidad |
|---|:---:|:---:|:---:|
| Costo de emisión por Orden de Compra | $S$ | **`$ 80.000`** | COP / orden |
| Tasa anual de posesión de inventario | $H$ | **`25.0 %`** ($0.25$) | Anual |
| Nivel de Servicio deseado | $SL$ | **`95.0 %`** | Probabilidad de no quiebre |
| Factor de seguridad normal estándar | $Z$ | **`1.64485`** | Adimensional ($Z_{0.95}$) |
| Costo de parada de planta por desabastecimiento | $C_{\text{parada}}$ | **`$ 450.000`** | COP / hora |
| Días laborales anuales | $T_{\text{año}}$ | **`300`** | Días laborables / año |

---

## 📐 Fórmulas Matemáticas Determinísticas

### 1. Lote Económico de Pedido ($EOQ$)
Calcula la cantidad óptima que minimiza el costo total de ordenar y mantener:
$$EOQ = \sqrt{\frac{2 \cdot D \cdot S}{H \cdot C_u}}$$
* $D$: Demanda anual del material en unidades ($\text{Consumo histórico} \times \frac{12}{21}$).
* $C_u$: Costo unitario del material en COP (`maestro_materiales.costo_unitario`).
* Redondeo: $\lceil EOQ \rceil$ (entero superior, mínimo 1 unidad).

### 2. Stock de Seguridad ($SS$) con Variabilidad de Lead Time
$$SS = Z \cdot \sigma_L \cdot \bar{d}$$
* $\bar{d} = \frac{D}{300}$: Demanda promedio diaria.
* $\sigma_L$: Desviación estándar del Lead Time real observado en órdenes de compra del SKU.
* $Z = 1.64485$ ($95\%$ de Nivel de Servicio).

### 3. Punto de Reorden ($ROP$)
Indica el nivel de inventario que dispara una nueva orden de compra:
$$ROP = (\bar{d} \cdot \bar{L}) + SS$$
* $\bar{L}$: Lead time promedio real observado en días (`fecha_recepcion - fecha_pedido`).

---

## 🚦 Semáforo de Estado de Inventario

El stock disponible se evalúa contra los umbrales determinísticos:
$$\text{Stock Disponible} = \text{Stock Físico / Kardex} + \text{OCs en Tránsito}$$

| Estado / Semáforo | Condición Matemática | Acción Sugerida | Prioridad |
|---|---|---|:---:|
| **🔴 `CRITICO_QUIEBRE`** | $\text{Stock Disponible} \le SS$ | Emitir OC inmediata por $EOQ$. Notificar a Compras por riesgo inminente de parada ($450k/h). | **Máxima (P0)** |
| **🟡 `ALERTA_REORDEN`** | $SS < \text{Stock Disponible} \le ROP$ | Emitir OC por $EOQ$. Pedido regular dentro de ventana logística. | **Alta (P1)** |
| **🟢 `NORMAL`** | $\text{Stock Disponible} > ROP$ | No comprar. Monitorear consumo. | **Informativa (P2)** |

---

## 🗄️ Fuente de Verdad en Base de Datos

La vista oficial en Supabase PostgreSQL es:
```sql
SELECT 
    sku,
    descripcion,
    categoria,
    costo_unitario_formato,
    stock_actual_disponible_und,
    eoq_lote_economico_und,
    stock_seguridad_und,
    rop_punto_reorden_und,
    semaforo_inventario,
    inversion_eoq_formato,
    accion_sugerida
FROM public.vista_calculo_eoq_rop
ORDER BY semaforo_inventario ASC, inversion_eoq_cop DESC;
```

---

## 🚫 Restricciones Estrictas para el Agente IA

1. **NO calcular $EOQ$ ni $ROP$ a mano:** Si se requiere un valor, consultar `public.vista_calculo_eoq_rop`.
2. **NO recomendar compras para SKUs Inactivos (Plata Muerta):** Si un SKU tiene demanda anual $D=0$, el $EOQ$ es $0$ y la recomendación es congelar compras.
3. **Validar incertidumbre de ERI antes de ordenar:** Si el SKU presenta alta discrepancia física vs Kardex, la recomendación de compra debe incluir la advertencia: *"Verificar conteo físico en bodega antes de radicar OC"*.
