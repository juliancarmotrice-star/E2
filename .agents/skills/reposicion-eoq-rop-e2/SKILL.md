---
name: reposicion-eoq-rop-e2
description: >-
  Calcula de forma determinística los parámetros de reposición continua (EOQ,
  ROP y Stock de Seguridad con nivel de servicio Z=95%) para E2 SAS.
  Utilícese para emitir sugerencias de compra, evaluar semáforos de stock,
  cuantificar inversión y prevenir quiebres de materiales sin alucinaciones.
  Enfatiza el consumo directo de la vista analítica vista_calculo_eoq_rop en Supabase.
---

# ⚙️ Motor de Reposición Determinística (EOQ / ROP / SS) — E2 SAS

Este skill es la **guía canónica de razonamiento paso a paso** para que cualquier LLM o agente de IA calcule y audite los parámetros del modelo de inventarios de revisión continua $(s, Q)$ para las **420 materias primas** de **E2 SAS**.

> [!IMPORTANT]
> **DIRECTIVA PRINCIPAL PARA EL LLM (CONSULTA DE LA VISTA ANALÍTICA):**
> La base de datos en Supabase cuenta con la vista analítica oficial y precalculada:
> * **`public.vista_calculo_eoq_rop`**: Contiene para los 420 SKUs el cálculo determinístico de $EOQ$, $SS$, $ROP$, stock disponible, semáforo de inventario, inversión requerida en COP y la acción operativa sugerida.
> 
> **Regla de Oro:** El LLM **NUNCA** debe calcular $EOQ$, $ROP$ o $SS$ a mano o de memoria si puede consultar directamente `public.vista_calculo_eoq_rop` en Supabase.

---

## 📌 1. Parámetros Económicos Oficiales del Negocio

Todos los cálculos están gobernados estrictamente por las variables financieras de **E2 SAS**:

| Parámetro Financiero / Operativo | Símbolo | Valor Oficial | Unidad | Justificación / Fuente |
|---|:---:|:---:|:---:|---|
| **Costo de emisión por Orden de Compra** | $S$ | **`$ 80.000`** | COP / orden | Costo administrativo, llamadas, radicación y recepción contable. |
| **Tasa anual de posesión de inventario** | $H$ | **`25.0 %`** ($0.25$) | Anual | Costo de oportunidad (15%), bodegaje (5%), seguros (3%), deterioro (2%). |
| **Nivel de Servicio al Cliente deseado** | $SL$ | **`95.0 %`** | Probabilidad | Política de calidad para evitar paradas de ensamble. |
| **Factor de seguridad normal estándar** | $Z$ | **`1.64485`** | Adimensional | Valor $Z$ de la distribución normal estándar para $SL = 0.95$. |
| **Costo de parada de línea por quiebre** | $C_{\text{parada}}$ | **`$ 450.000`** | COP / hora | Costo de mano de obra ociosa, reprogramación y lucro cesante. |
| **Días hábiles laborales por año** | $T_{\text{año}}$ | **`300`** | Días / año | Calendario laboral estándar de planta de producción en Colombia. |

---

## 🪜 2. Algoritmo Paso a Paso: Modelo Continuo $(s, Q)$

Cualquier LLM debe comprender y validar el cálculo mediante esta secuencia de **8 pasos determinísticos**:

```
 [Paso 1] Anualizar Demanda (D) y Calcular Consumo Diario (d̄ = D / 300)
    │
    ▼
 [Paso 2] Calcular Lote Económico de Pedido (EOQ = sqrt(2*D*S / (H*Cu)))
    │
    ▼
 [Paso 3] Obtener Lead Time Real Medio (L̄) y Desviación (σ_L) de Proveedores
    │
    ▼
 [Paso 4] Calcular Stock de Seguridad Dinámico (SS = Z * σ_L * d̄)
    │
    ▼
 [Paso 5] Calcular Punto de Reorden (ROP = d̄ * L̄ + SS)
    │
    ▼
 [Paso 6] Evaluar Posición Neta de Stock Disponible (Físico + OCs en Tránsito)
    │
    ▼
 [Paso 7] Determinar Semáforo de Riesgo (CRITICO_QUIEBRE, ALERTA_REORDEN, NORMAL, PLATA_MUERTA)
    │
    ▼
 [Paso 8] Cuantificar Inversión del Lote en COP (Inversión = EOQ * Cu)
```

---

### Paso 1: Anualización de Demanda ($D_i$) y Demanda Diaria ($\bar{d}_i$)
* $Q_{\text{consumo}, i}$: Suma de salidas en los 21 meses ($T_{\text{dias}} \approx 639$ días).
* **Demanda Anual ($D_i$):**
  $$D_i = Q_{\text{consumo}, i} \times \left(\frac{365}{T_{\text{dias}}}\right)$$
* **Demanda Diaria Laboral ($\bar{d}_i$):**
  $$\bar{d}_i = \frac{D_i}{300}$$
* *Regla para SKUs inactivos:* Si $Q_{\text{consumo}, i} = 0 \implies D_i = 0 \land \bar{d}_i = 0$.

---

### Paso 2: Lote Económico de Pedido ($EOQ_i$)
Minimiza la suma de costos de pedir y costos de mantener:
$$EOQ_i = \begin{cases} 
\left\lceil \sqrt{\frac{2 \cdot D_i \cdot S}{H \cdot C_{u, i}}} \right\rceil & \text{si } D_i > 0 \\
0 & \text{si } D_i = 0 \text{ (Plata Muerta)}
\end{cases}$$
* Redondeo obligatorio: Entero techo ($\lceil \dots \rceil$), mínimo 1 unidad si $D_i > 0$.

---

### Paso 3: Estadísticos del Lead Time de Proveedores ($\bar{L}_i$ y $\sigma_{L, i}$)
* Extraer de `ordenes_compra` cerradas para el material o su categoría:
  $$\text{Lead Time Real} = \text{fecha\_recepcion} - \text{fecha\_pedido}$$
* $\bar{L}_i$: Promedio del Lead Time real observado en días ($\approx 20.8$ días en Lámina).
* $\sigma_{L, i}$: Desviación estándar muestral del Lead Time real ($\approx 4.6$ días en Lámina).

---

### Paso 4: Stock de Seguridad Dinámico ($SS_i$)
Protege contra la incertidumbre en los tiempos de entrega del proveedor durante el ciclo de reabastecimiento:
$$SS_i = \begin{cases}
\left\lceil Z \cdot \sigma_{L, i} \cdot \bar{d}_i \right\rceil & \text{si } D_i > 0 \\
0 & \text{si } D_i = 0 \text{ (Plata Muerta)}
\end{cases}$$
*(Con $Z = 1.64485$ para un $SL = 95\%$).*

---

### Paso 5: Punto de Reorden ($ROP_i$)
Nivel de inventario que dispara la colocación de una nueva orden de compra:
$$ROP_i = \begin{cases}
\left\lceil (\bar{d}_i \cdot \bar{L}_i) + SS_i \right\rceil & \text{si } D_i > 0 \\
0 & \text{si } D_i = 0 \text{ (Plata Muerta)}
\end{cases}$$

---

### Paso 6: Posición Neta de Inventario ($I_{\text{disp}, i}$)
$$\text{Stock Disponible}_i = \text{Stock Físico / Kardex}_i + \text{OCs en Tránsito (Abiertas)}_i$$
* *Nota:* Las órdenes de compra con `fecha_recepcion IS NULL` suman al inventario disponible porque ya fueron ordenadas.

---

### Paso 7: Asignación del Semáforo de Inventario

| Semáforo de Estado | Condición Matemática | Diagnóstico de Planta | Acción Operativa Inmediata | Prioridad |
|---|---|---|---|:---:|
| **🔴 `1_CRITICO_QUIEBRE`** | $I_{\text{disp}, i} \le SS_i$ | Stock por debajo del colchón de seguridad. Riesgo inminente de parada ($450k/h). | **EMITIR OC URGENTE por $EOQ_i$.** Notificar a Compras para despacho exprés. | **P0 (Máxima)** |
| **🟡 `2_ALERTA_REORDEN`** | $SS_i < I_{\text{disp}, i} \le ROP_i$ | Inventario dentro de la ventana de reorden regular. | **EMITIR OC REGULAR por $EOQ_i$.** Programar entrega con Lead Time normal. | **P1 (Alta)** |
| **🟢 `3_NORMAL`** | $I_{\text{disp}, i} > ROP_i$ | Stock suficiente para cubrir la demanda durante el ciclo. | **NO ORDENAR.** Monitorear ritmo de consumo regular. | **P2 (Informativa)** |
| **🧊 `4_PLATA_MUERTA`** | $D_i = 0$ | Material inmovilizado sin consumo en 21 meses. | **BLOQUEO TOTAL DE COMPRAS ($EOQ=0, ROP=0$).** Plan de remate/canje. | **P3 (Control)** |

---

### Paso 8: Cuantificación Financiera del Pedido ($Inv_i$)
$$\text{Inversión en } EOQ_i = EOQ_i \times C_{u, i} \text{ (en COP)}$$

---

## 🗄️ 3. Consultas a la Vista Analítica en Supabase (Uso Mandatorio)

El LLM debe consumir directamente la vista analítica `public.vista_calculo_eoq_rop`:

### A. Consultar Materiales que Requieren Compra Inmediata (Quiebre y Reorden)
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
WHERE semaforo_inventario IN ('1_CRITICO_QUIEBRE', '2_ALERTA_REORDEN')
ORDER BY semaforo_inventario ASC, inversion_eoq_cop DESC;
```

### B. Resumen Ejecutivo por Semáforo
```sql
SELECT 
    semaforo_inventario,
    COUNT(*) AS total_skus,
    TO_CHAR(ROUND((COUNT(*)::numeric / 420 * 100), 2), 'FM990.00') || ' %' AS pct_catalogo,
    '$ ' || TO_CHAR(SUM(inversion_eoq_cop), 'FM999,999,999,990') || ' COP' AS inversion_total_sugerida_cop
FROM public.vista_calculo_eoq_rop
GROUP BY semaforo_inventario
ORDER BY semaforo_inventario ASC;
```

### C. Ficha Técnica de Reposición para un SKU Individual
```sql
SELECT 
    sku,
    descripcion,
    categoria,
    costo_unitario_formato,
    demanda_anual_und,
    consumo_diario_und,
    lead_time_real_dias,
    desviacion_lt_dias,
    stock_actual_disponible_und,
    stock_seguridad_und,
    rop_punto_reorden_und,
    eoq_lote_economico_und,
    inversion_eoq_formato,
    semaforo_inventario,
    accion_sugerida
FROM public.vista_calculo_eoq_rop
WHERE sku = 'MP-0001'; -- Reemplazar por SKU
```

---

## 🚫 4. Reglas Innegociables para el Agente IA / LLM

1. **NO recalcular de memoria:** Siempre respaldar las cifras consultando `public.vista_calculo_eoq_rop`.
2. **Cero compras en Plata Muerta:** Si el SKU está en `4_PLATA_MUERTA`, la sugerencia de compra debe ser estrictamente cero.
3. **Advertencia de Incertidumbre ERI:** Si el SKU a comprar tiene discrepancia física en `public.vista_diagnostico_eri_inventarios`, agregar siempre la nota:
   > ⚠️ *Nota de Validación ERI: Validar conteo físico en bodega antes de autorizar la orden de compra.*

