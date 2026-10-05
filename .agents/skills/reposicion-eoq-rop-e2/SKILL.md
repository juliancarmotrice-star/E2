---
name: reposicion-eoq-rop-e2
description: >-
  Calcula de forma determinística los parámetros del modelo de reposición continua (EOQ,
  ROP y Stock de Seguridad con nivel de servicio Z=95%) para cualquier catálogo de materias primas (N SKUs).
  Utilícese para emitir sugerencias de compra, evaluar semáforos de stock,
  cuantificar inversión y prevenir quiebres de materiales sin alucinaciones.
  Enfatiza el consumo directo de la vista analítica vista_calculo_eoq_rop en Supabase.
---

# ⚙️ Motor General de Reposición Determinística (EOQ / ROP / SS)

Este skill es la **guía metodológica y algorítmica general paso a paso** para que cualquier LLM o agente de IA calcule y audite los parámetros del modelo de inventarios de revisión continua $(s, Q)$ sobre **cualquier catálogo de $N$ materias primas** y **cualquier horizonte temporal**.

> [!IMPORTANT]
> **DIRECTIVA PRINCIPAL PARA EL LLM (CONSULTA DE LA VISTA ANALÍTICA):**
> La base de datos en Supabase cuenta con la vista analítica oficial y precalculada:
> * **`public.vista_calculo_eoq_rop`**: Contiene para la totalidad de los $N$ SKUs del catálogo el cálculo determinístico de $EOQ$, $SS$, $ROP$, stock disponible, semáforo de inventario, inversión requerida en COP y la acción operativa sugerida.
> 
> **Regla de Oro:** El LLM **NUNCA** debe calcular $EOQ$, $ROP$ o $SS$ a mano o de memoria si puede consultar directamente `public.vista_calculo_eoq_rop` en Supabase.

---

## 📌 1. Parámetros Económicos Generales del Negocio

El modelo de revisión continua $(s, Q)$ está gobernado por variables financieras y operativas parametrizables:

| Parámetro Financiero / Operativo | Símbolo | Valor Estándar | Unidad | Significado / Justificación |
|---|:---:|:---:|:---:|---|
| **Costo de emisión por Orden de Compra** | $S$ | **`$ 80.000`** | COP / orden | Costo administrativo de colocación, seguimiento y recepción. |
| **Tasa anual de posesión de inventario** | $H$ | **`25.0 %`** ($0.25$) | Anual | Costo de oportunidad del capital, almacenamiento, seguros y deterioro. |
| **Nivel de Servicio al Cliente deseado** | $SL$ | **`95.0 %`** | Probabilidad | Probabilidad de no sufrir quiebre durante el ciclo de reorden. |
| **Factor de seguridad normal estándar** | $Z$ | **`1.64485`** | Adimensional | Valor $Z$ de la distribución normal estándar ($Z_{0.95}$). |
| **Costo de parada de línea por quiebre** | $C_{\text{parada}}$ | **`$ 450.000`** | COP / hora | Costo por mano de obra improductiva y retraso en entregas. |
| **Días hábiles laborales por año** | $T_{\text{laboral}}$ | **`300`** | Días / año | Días laborables anuales estándar para cálculo de demanda diaria. |

---

## 🪜 2. Algoritmo Paso a Paso: Modelo Continuo $(s, Q)$ para $N$ SKUs

Cualquier LLM debe comprender y validar el cálculo mediante esta secuencia de **8 pasos determinísticos generales**:

```
 [Paso 1] Anualizar Demanda (D_i = Q_i * 365 / T_días) y Calcular Tasa Diaria (d̄_i = D_i / T_laboral)
    │
    ▼
 [Paso 2] Calcular Lote Económico de Pedido (EOQ_i = sqrt(2*D_i*S / (H*Cu_i)))
    │
    ▼
 [Paso 3] Obtener Lead Time Real Medio (L̄_i) y Desviación (σ_L_i) de Proveedores
    │
    ▼
 [Paso 4] Calcular Stock de Seguridad Dinámico (SS_i = Z * σ_L_i * d̄_i)
    │
    ▼
 [Paso 5] Calcular Punto de Reorden (ROP_i = d̄_i * L̄_i + SS_i)
    │
    ▼
 [Paso 6] Evaluar Posición Neta de Stock Disponible (Físico + OCs en Tránsito)
    │
    ▼
 [Paso 7] Asignar Semáforo de Estado (CRITICO_QUIEBRE, ALERTA_REORDEN, NORMAL, PLATA_MUERTA)
    │
    ▼
 [Paso 8] Cuantificar Inversión del Lote en Moneda Local (Inversión = EOQ_i * Cu_i)
```

---

### Paso 1: Anualización de Demanda ($D_i$) y Demanda Diaria ($\bar{d}_i$)
Para cualquier SKU $i \in \{1, 2, \dots, N\}$ con horizonte histórico observado de $T_{\text{dias}}$:
* **Demanda Anual ($D_i$):**
  $$D_i = Q_{\text{consumo}, i} \times \left(\frac{365}{T_{\text{dias}}}\right)$$
* **Demanda Diaria Laboral ($\bar{d}_i$):**
  $$\bar{d}_i = \frac{D_i}{T_{\text{laboral}}}$$
* *Regla para SKUs inactivos:* Si $Q_{\text{consumo}, i} = 0 \implies D_i = 0 \land \bar{d}_i = 0$.

---

### Paso 2: Lote Económico de Pedido ($EOQ_i$)
$$EOQ_i = \begin{cases} 
\left\lceil \sqrt{\frac{2 \cdot D_i \cdot S}{H \cdot C_{u, i}}} \right\rceil & \text{si } D_i > 0 \\
0 & \text{si } D_i = 0 \text{ (Plata Muerta)}
\end{cases}$$
* Redondeo: Entero superior ($\lceil \dots \rceil$), mínimo 1 unidad si $D_i > 0$.

---

### Paso 3: Estadísticos del Lead Time de Proveedores ($\bar{L}_i$ y $\sigma_{L, i}$)
Calculados dinámicamente sobre las órdenes de compra cerradas para el material o su familia:
* $\bar{L}_i$: Promedio del Lead Time real observado en días ($\text{fecha\_recepcion} - \text{fecha\_pedido}$).
* $\sigma_{L, i}$: Desviación estándar muestral del Lead Time real.

---

### Paso 4: Stock de Seguridad Dinámico ($SS_i$)
Protege contra la variabilidad de entrega del proveedor durante el ciclo logístico:
$$SS_i = \begin{cases}
\left\lceil Z \cdot \sigma_{L, i} \cdot \bar{d}_i \right\rceil & \text{si } D_i > 0 \\
0 & \text{si } D_i = 0 \text{ (Plata Muerta)}
\end{cases}$$

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

---

### Paso 7: Asignación Dinámica del Semáforo de Inventario

| Semáforo de Estado | Condición Matemática | Diagnóstico Operativo | Acción Inmediata Sugerida | Prioridad |
|---|---|---|---|:---:|
| **🔴 `1_CRITICO_QUIEBRE`** | $I_{\text{disp}, i} \le SS_i$ | Stock por debajo del colchón de seguridad. Riesgo inminente de parada ($450k/h). | **EMITIR OC URGENTE por $EOQ_i$.** Notificar a Compras para despacho exprés. | **P0 (Máxima)** |
| **🟡 `2_ALERTA_REORDEN`** | $SS_i < I_{\text{disp}, i} \le ROP_i$ | Inventario dentro de la ventana de reorden regular. | **EMITIR OC REGULAR por $EOQ_i$.** Programar entrega con Lead Time normal. | **P1 (Alta)** |
| **🟢 `3_NORMAL`** | $I_{\text{disp}, i} > ROP_i$ | Stock suficiente para cubrir la demanda durante el ciclo. | **NO ORDENAR.** Monitorear ritmo de consumo regular. | **P2 (Informativa)** |
| **🧊 `4_PLATA_MUERTA`** | $D_i = 0$ | Material inmovilizado sin consumo histórico. | **BLOQUEO TOTAL DE COMPRAS ($EOQ=0, ROP=0$).** Plan de remate/canje. | **P3 (Control)** |

---

### Paso 8: Cuantificación Financiera del Pedido ($Inv_i$)
$$\text{Inversión en } EOQ_i = EOQ_i \times C_{u, i} \text{ (en COP)}$$

---

## 📌 3. Caso de Estudio de Referencia (Línea Base Histórica Inicial E1)

A modo de **referencia histórica de validación** sobre el dataset inicial de **E2 SAS** ($N=420$ SKUs):
* **Parámetros aplicados:** $S = \$80.000\text{ COP}$, $H = 25\%$, $SL = 95\%$ ($Z=1.64485$), $T_{\text{laboral}} = 300\text{ días}$.
* **Plata Muerta aislada:** 301 de 420 referencias con $EOQ = 0$ y $ROP = 0$.
* **Insumos críticos en quiebre:** Láminas y tuberías de alta rotación con stock físico por debajo del $SS$.

---

## 🗄️ 4. Consultas a la Vista Analítica en Supabase (Dinámicas)

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

### B. Resumen Dinámico por Semáforo (% Calculado en Tiempo Real)
```sql
SELECT 
    semaforo_inventario,
    COUNT(*) AS total_skus,
    TO_CHAR(ROUND((COUNT(*)::numeric / SUM(COUNT(*)) OVER() * 100), 2), 'FM990.00') || ' %' AS pct_catalogo_dinamico,
    '$ ' || TO_CHAR(SUM(inversion_eoq_cop), 'FM999,999,999,990') || ' COP' AS inversion_total_sugerida_cop
FROM public.vista_calculo_eoq_rop
GROUP BY semaforo_inventario
ORDER BY semaforo_inventario ASC;
```

### C. Ficha Técnica de Reposición para Cualquier SKU
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
WHERE sku = 'MP-0001'; -- Reemplazar dinámicamente por cualquier SKU
```

---

## 🚫 5. Reglas Innegociables para el Agente IA / LLM

1. **NO recalcular de memoria:** Siempre respaldar las cifras consultando `public.vista_calculo_eoq_rop`.
2. **Cero compras en Plata Muerta:** Si el SKU está en `4_PLATA_MUERTA`, la sugerencia de compra debe ser estrictamente cero.
3. **Advertencia de Incertidumbre ERI:** Si el SKU a comprar tiene discrepancia física en `public.vista_diagnostico_eri_inventarios`, agregar siempre la nota:
   > ⚠️ *Nota de Validación ERI: Validar conteo físico en bodega antes de autorizar la orden de compra.*

---

## 🗄️ 6. Archivo DDL de la Vista en Supabase

| Vista | Archivo DDL Fuente | Ubicación | Propósito |
|-------|-------------------|-----------|-----------|
| `public.vista_calculo_eoq_rop` | `sql/04_vistas_calculo_eoq_rop.sql` | Repositorio `PA-E2/sql/` | Cálculo determinístico de Demanda Diaria, Lead Time Real, SS (Z=95%), ROP, EOQ, Inversión y Semáforo de Reposición. |

> [!NOTE]
> La vista consolida automáticamente los parámetros del modelo de Wilson ($S = \$50.000$ COP/pedido, $H = 20\%$ anual del costo unitario, $Z = 1.645$ para 95% de nivel de servicio). Al ingresar nuevos movimientos o recepciones de órdenes, los saldos y semáforos se recalculan sin fricción.

---

## 🔗 7. Prerequisitos y Dependencias

* **Prerequisito obligatorio:** El skill [`limpieza-datos-e2`](../limpieza-datos-e2/SKILL.md) debe haber cargado:
  * `public.maestro_materiales`
  * `public.movimientos_inventarios`
  * `public.inventario_inicial`
  * `public.ordenes_compra`
* **Dependencia analítica previa:**
  * [`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md): Demanda anualizada y segmentación de rotación.
  * [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md): Verificación de saldos en piso antes de gatillar compras.
  * [`sla-proveedores-mrp-e2`](../sla-proveedores-mrp-e2/SKILL.md): Lead time real histórico ($\bar{L}_{\text{real}}$ y $\sigma_L$).

---

## 🔎 8. Queries de Verificación de Calidad

Ejecutar estas consultas para auditar la validez matemática y lógica de los parámetros calculados:

### A. Verificar Semáforos Lógicos (Ningún Stock $\le$ ROP en Verde)
```sql
SELECT COUNT(*) AS inconsistencias_semaforo
FROM public.vista_calculo_eoq_rop
WHERE (stock_actual_disponible_und <= rop_punto_reorden_und AND semaforo_inventario = '🟢 VERDE (Stock Óptimo)')
   OR (stock_actual_disponible_und > rop_punto_reorden_und AND semaforo_inventario = '🔴 ROJO (Reorden Inmediato)');
-- Resultado esperado: 0 (las reglas de semáforo deben cumplirse estrictamente)
```

### B. Validar Aislamiento de Plata Muerta (Cero Compras Sugeridas)
```sql
SELECT COUNT(*) AS plata_muerta_con_compras
FROM public.vista_calculo_eoq_rop
WHERE demanda_anual_und = 0 
  AND (eoq_lote_economico_und > 0 OR accion_sugerida LIKE '%COMPRAR%');
-- Resultado esperado: 0
```

### C. Cuantificar Presupuesto Requerido para Compras Críticas (Semáforo Rojo)
```sql
SELECT 
    COUNT(*) AS total_skus_a_comprar,
    ROUND(SUM(inversion_eoq_cop)::numeric, 2) AS inversion_total_presupuestada_cop,
    TO_CHAR(SUM(inversion_eoq_cop), '$999,999,999,999') AS inversion_formateada
FROM public.vista_calculo_eoq_rop
WHERE semaforo_inventario LIKE '🔴%';
```

### D. Distribución del Catálogo por Estado de Semáforo
```sql
SELECT 
    semaforo_inventario,
    COUNT(*) AS total_skus,
    ROUND((COUNT(*)::numeric / (SELECT COUNT(*) FROM public.vista_calculo_eoq_rop) * 100), 1) || ' %' AS pct_catalogo
FROM public.vista_calculo_eoq_rop
GROUP BY semaforo_inventario
ORDER BY total_skus DESC;
```

### E. Integridad de Parámetros Clave (Cero Nulos en EOQ/ROP para SKUs Activos)
```sql
SELECT COUNT(*) AS parametros_nulos
FROM public.vista_calculo_eoq_rop
WHERE demanda_anual_und > 0 
  AND (eoq_lote_economico_und IS NULL OR rop_punto_reorden_und IS NULL OR stock_seguridad_und IS NULL);
-- Resultado esperado: 0
```

---

## 🔄 9. Integración con Otros Skills del Sistema

| Skill | Dirección | Flujo de Información |
|-------|:---------:|----------------------|
| [`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md) | Inbound | Provee la clasificación ABC para jerarquizar atención ejecutiva en SKUs A. |
| [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md) | Inbound | Provee alertas de faltante/sobrante para ajustar el stock base disponible antes de calcular la orden. |
| [`sla-proveedores-mrp-e2`](../sla-proveedores-mrp-e2/SKILL.md) | Outbound/Inbound | EOQ/ROP define el tamaño de lote sugerido ($Q$) y punto de reorden continuo, complementando la explosión MRP por periodos. |

---

## 🚫 10. Fronteras del Skill (Qué NO hace este Skill)

* **NO emitir órdenes de compra automáticamente al ERP:** Este skill entrega la recomendación determinística, tamaño de lote e inversión; la autorización recae en compras.
* **NO calcular variaciones ERI:** Es responsabilidad del skill [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md).
* **NO realizar limpieza ni corrección de datos crudos:** Es responsabilidad del skill [`limpieza-datos-e2`](../limpieza-datos-e2/SKILL.md).
* **NO planificar requerimientos de materiales basados en órdenes de producción finitas:** La explosión MRP dependiente corresponde a [`sla-proveedores-mrp-e2`](../sla-proveedores-mrp-e2/SKILL.md).



