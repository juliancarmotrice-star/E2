---
name: analitica-abc-xyz-e2
description: >-
  Aplica la clasificación paramétrica ABC (Pareto por valor de consumo anualizado 80/15/5)
  y segmentación XYZ (variabilidad de demanda mensual por CV) para E2 SAS.
  Utilícese para identificar SKUs estratégicos Clase A, calcular la matriz cruzada ABC-XYZ,
  aislar los 301 SKUs de Plata Muerta y definir políticas diferenciadas de inventario y compras.
---

# 🧠 Motor de Analítica y Clasificación ABC-XYZ — E2 SAS

Este skill es la **guía canónica de razonamiento paso a paso** para que cualquier LLM o agente de IA comprenda, calcule, audite y aplique la segmentación multicriterio de las **420 materias primas** de **E2 SAS**.

> [!IMPORTANT]
> **DIRECTIVA PRINCIPAL PARA EL LLM (CONSULTA DE LA VISTA ANALÍTICA):**
> La base de datos en Supabase cuenta con la vista analítica oficial y precalculada:
> * **`public.vista_clasificacion_abc`**: Contiene para los 420 SKUs el valor anualizado en COP, porcentaje de participación individual, porcentaje acumulado de Pareto y la clasificación $A$, $B$ o $C$ con columnas numéricas y formateadas.
> 
> **Regla de Oro:** El LLM **NUNCA** debe calcular el Pareto a mano o de memoria si puede consultar directamente `public.vista_clasificacion_abc` en Supabase.


## 🎯 1. Contexto Operativo y Alcance del Negocio

**E2 SAS** es una empresa de manufactura de mobiliario metálico y de oficina con **18 Productos Terminados (PT)** y un catálogo de **420 SKUs de materias primas** distribuidos en 8 familias (*Lámina, Tubería, Tornillería, Pintura, Vidrio, Empaque, Adhesivos, Correderas*).

El histórico de operaciones abarca **21 meses transaccionales** (1 de julio de 2024 al 31 de marzo de 2026).

### El Dilema Central de Inventario:
1. **Hiper-concentración:** Solo **30 SKUs (7.14%)** generan el **80.16%** de todo el consumo monetario de la fábrica (**Clase A**).
2. **Plata Muerta Masiva:** **301 de 420 SKUs (71.67%)** tienen **exactamente 0 salidas** en 21 meses, inmovilizando **$3.550.022.309 COP** en bodega (53.99% del inventario inicial).

```
                             MAPA CONCEPTUAL DEL MOTOR
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                              420 SKUs TOTALES                                │
 └───────────────────────┬──────────────────────────────┬───────────────────────┘
                         │                              │
                         ▼                              ▼
            ┌──────────────────────────┐   ┌──────────────────────────┐
            │   119 SKUs ACTIVOS       │   │ 301 SKUs PLATA MUERTA    │
            │  (Salidas en 21 meses)   │   │  (Cero salidas en 21 m)  │
            └────────────┬─────────────┘   └────────────┬─────────────┘
                         │                              │
                         ▼                              ▼
            ┌──────────────────────────┐   ┌──────────────────────────┐
            │  Segmentación ABC + XYZ  │   │ Asignación Directa: CZ   │
            │ (Pareto Valor + CV Mens) │   │ (Bloqueo Total de Compra)│
            └──────────────────────────┘   └──────────────────────────┘
```

---

## 🪜 2. Algoritmo Paso a Paso: Clasificación ABC (Pareto Monetario)

Cualquier LLM debe ejecutar o razonar el cálculo ABC siguiendo estrictamente esta secuencia de **6 pasos determinísticos**:

```
 [Paso 1] Normalizar y Filtrar Salidas
    │
    ▼
 [Paso 2] Determinar Horizonte y Anualizar Demanda (D = Q * 365 / T_días)
    │
    ▼
 [Paso 3] Calcular Valor Anualizado por SKU (V_i = D_i * Costo_Unitario)
    │
    ▼
 [Paso 4] Ordenar Descendentemente y Calcular % de Participación Individual
    │
    ▼
 [Paso 5] Calcular % Acumulado de Lorenz (Suma Acumulada de Participación)
    │
    ▼
 [Paso 6] Asignar Categoría ABC con Criterio de Borde (80% / 95% / 100%)
```

---

### Paso 1: Filtrar y Consolidar Salidas por SKU
* **Fuente de datos:** Tabla `movimientos_inventarios`.
* **Filtro obligatorio:** Considerar únicamente registros donde `tipo_movimiento = 'salida'`.
* **Cálculo:** Para cada SKU $i$, sumar las cantidades absolutas despachadas:
  $$Q_{\text{consumo\_total}, i} = \sum_{\text{salidas}} |\text{cantidad}_i|$$
* *Regla para inactivos:* Si un SKU del `maestro_materiales` no tiene registros de salida, $Q_{\text{consumo\_total}, i} = 0$.
* *Filtro de limpieza:* Excluir SKUs descartados de prueba (`sku NOT LIKE 'MP-9%'` y `descripcion NOT LIKE '%(dup)%'`).

---

### Paso 2: Calcular el Factor de Anualización ($F_{\text{anual}}$)
* **Cálculo de días de historial:**
  $$T_{\text{dias}} = \max(\text{fecha}) - \min(\text{fecha}) + 1 \quad (\approx 639 \text{ días para los 21 meses})$$
* **Factor de anualización:**
  $$F_{\text{anual}} = \frac{365}{T_{\text{dias}}} \approx \frac{365}{639} \approx 0.5712$$
* **Demanda anual en unidades ($D_i$):**
  $$D_i = Q_{\text{consumo\_total}, i} \times \left(\frac{365}{T_{\text{dias}}}\right)$$

---

### Paso 3: Calcular el Valor de Consumo Anualizado ($V_i$)
* Multiplicar la demanda anualizada por el costo unitario consignado en `maestro_materiales`:
  $$V_i = D_i \times C_{u, i}$$
  *(Donde $C_{u, i}$ es el costo de adquisición unitario en COP).*

---

### Paso 4: Calcular el Total Global y Participación Individual ($p_i$)
* **Valor total del consumo anual de la fábrica:**
  $$V_{\text{total}} = \sum_{k=1}^{N} V_k \quad (\approx \$34.772.195.288 \text{ COP/año})$$
* **Participación porcentual de cada SKU:**
  $$p_i = \left( \frac{V_i}{V_{\text{total}}} \right) \times 100$$
* **Ordenamiento:** Ordenar los $N=420$ materiales de forma estrictamente **descendente** según $V_i$ ($V_1 \ge V_2 \ge \dots \ge V_N$).

---

### Paso 5: Calcular el Porcentaje Acumulado ($P_{\text{acum}, i}$)
* Para el material en la posición $i$ del ranking descendente:
  $$P_{\text{acum}, i} = \sum_{j=1}^{i} p_j = \left( \frac{\sum_{j=1}^{i} V_j}{V_{\text{total}}} \right) \times 100$$

---

### Paso 6: Asignar la Categoría ABC (Criterio de Borde 80 / 15 / 5)

La asignación se realiza mediante los siguientes umbrales con **criterio de borde inclusivo** (el SKU que cruza la frontera se incluye en la categoría superior):

| Categoría | Condición Lógica Formal | SKUs en E2 SAS | % Catálogo | % Valor Consumo |
|:---:|---|:---:|:---:|:---:|
| **🅰️ Clase A** | $P_{\text{acum}, i} \le 80.00\%$ **O** ($P_{\text{acum}, i-1} < 80.00\% \land P_{\text{acum}, i} \ge 80.00\%$) | **30 SKUs** | **7.14%** | **80.16%** |
| **🅱️ Clase B** | ($80.00\% < P_{\text{acum}, i} \le 95.00\%$) **O** ($P_{\text{acum}, i-1} < 95.00\% \land P_{\text{acum}, i} \ge 95.00\%$) | **30 SKUs** | **7.14%** | **15.09%** |
| **🅲 Clase C** | $P_{\text{acum}, i} > 95.00\%$ (Incluye todos los SKUs con consumo $= 0$) | **360 SKUs** | **85.71%** | **4.75%** |
| **TOTAL** | — | **420 SKUs** | **100.00%** | **100.00%** |

---

## 🪜 3. Algoritmo Paso a Paso: Segmentación XYZ (Variabilidad de Demanda)

La clasificación XYZ mide la **estabilidad temporal del consumo** para determinar el grado de predictibilidad y el nivel requerido de Stock de Seguridad ($SS$).

```
 [Paso 1] Construir Serie Temporal Mensual de Consumo (M = 21 meses)
    │
    ▼
 [Paso 2] Calcular Media Mensual (d̄) y Desviación Estándar Muestral (σ_d)
    │
    ▼
 [Paso 3] Calcular Coeficiente de Variación (CV = σ_d / d̄)
    │
    ▼
 [Paso 4] Asignar Categoría XYZ según Umbrales de Dispersión (X <= 0.50, Y <= 1.00, Z > 1.00)
```

---

### Paso 1: Construir la Serie de Tiempo Mensual ($d_{i, m}$)
* Dividir el periodo de 21 meses en intervalos mensuales completos $m \in \{1, 2, \dots, M\}$ ($M=21$).
* Para cada SKU $i$, calcular el consumo total del mes $m$:
  $$d_{i, m} = \sum_{\text{salidas en mes } m} |\text{cantidad}_i|$$
* > [!IMPORTANT]
  > **Regla de Cero Relleno (Zero Padding):** Si en el mes $m$ un SKU no tuvo salidas, el valor debe ser **0 (cero)**, nunca `NULL` ni omitir el mes. Omitir meses distorsiona y reduce falsamente la desviación estándar.

---

### Paso 2: Calcular Estadísticos Descriptivos
* **Consumo mensual promedio:**
  $$\bar{d}_i = \frac{1}{M} \sum_{m=1}^{M} d_{i, m}$$
* **Desviación estándar muestral mensual:**
  $$\sigma_{d, i} = \sqrt{\frac{1}{M - 1} \sum_{m=1}^{M} (d_{i, m} - \bar{d}_i)^2}$$

---

### Paso 3: Calcular el Coeficiente de Variación ($CV_i$)
$$CV_i = \frac{\sigma_{d, i}}{\bar{d}_i}$$

#### Manejo de Casos Borde y Excepciones:
1. **Si $\bar{d}_i = 0$ (Plata Muerta / Cero salidas):** El $CV_i$ es matemáticamente indefinido ($\frac{0}{0}$). **Regla:** Asignar automáticamente $CV_i = \infty \implies \textbf{Clase Z}$.
2. **Si $\sigma_{d, i} = 0 \land \bar{d}_i > 0$ (Consumo constante perfecto):** $CV_i = 0 \implies \textbf{Clase X}$.
3. **Si el SKU solo se consumió en 1 de 21 meses:** $CV_i \gg 1.0 \implies \textbf{Clase Z}$.

---

### Paso 4: Asignar la Categoría XYZ

| Clase XYZ | Criterio de Variabilidad | Comportamiento del Consumo | Predictibilidad | Estrategia de Planificación |
|:---:|:---:|---|:---:|---|
| **🟢 Clase X** | **$CV \le 0.50$** | Demanda regular, constante y con baja dispersión mes a mes. | **Muy Alta** | Reposición automática por $EOQ / ROP$ con bajo Stock de Seguridad. |
| **🟡 Clase Y** | **$0.50 < CV \le 1.00$** | Demanda con fluctuaciones moderadas, estacionalidad o lotes medianos. | **Media** | Reposición con $SS$ dinámico ajustado por variabilidad combinada ($\sigma_d$ y $\sigma_L$). |
| **🔴 Clase Z** | **$CV > 1.00$** o $\bar{d} = 0$ | Demanda errática, esporádica, baches prolongados o **nula**. | **Baja / Nula** | Fabricación bajo pedido (Make-to-Order / JIT) o **bloqueo de compras** si es inactivo. |

---

## 🗂️ 4. Matriz Combinada ABC - XYZ (Políticas Operativas 3x3)

Al cruzar ambas dimensiones, el LLM debe recomendar las siguientes políticas específicas según el cuadrante:

```
                  MATRIZ MULTICRITERIO ABC - XYZ (E2 SAS)
     ┌──────────────────────┬──────────────────────┬──────────────────────┐
     │       CLASE X        │       CLASE Y        │       CLASE Z        │
     │     (CV <= 0.50)     │   (0.50 < CV <= 1.0) │      (CV > 1.0)      │
┌────┼──────────────────────┼──────────────────────┼──────────────────────┤
│    │ AX: Joyas de Corona  │ AY: Valor Fluctuante │ AZ: Alto Riesgo      │
│ A  │ • Reposición EOQ/ROP │ • Pronósticos collab │ • Compra bajo pedido │
│    │ • Pedidos frecuentes │ • SS dinámico        │ • Sin stock especul. │
│    │ • Control diario     │ • Control semanal    │ • Auditoría lote/lote│
├────┼──────────────────────┼──────────────────────┼──────────────────────┤
│    │ BX: Valor Intermedio │ BY: Intermedio Var.  │ BZ: Intermedio Errát.│
│ B  │ • EOQ estándar       │ • Revisión periódica │ • MTO / Lote mínimo  │
│    │ • Revisión quincenal │ • SS moderado        │ • Evitar sobre-stock │
├────┼──────────────────────┼──────────────────────┼──────────────────────┤
│    │ CX: Consumo Marginal │ CY: Marginal Var.    │ CZ: PLATA MUERTA     │
│ C  │ • Sistema 2 cajones  │ • Compras agrupadas  │ • 301 SKUs BLOQUEADOS│
│    │ • Compras semestrales│ • Mínima atención    │ • Desacumular / Remat│
└────┴──────────────────────┴──────────────────────┴──────────────────────┘
```

### Detalle de Políticas Operativas por Celda:

| Celda | Descripción y Rol en E2 SAS | Política de Reposición Sugerida | Gestión de Stock de Seguridad ($SS$) | Frecuencia de Control / Conteo |
|:---:|---|---|---|---|
| **AX** | Materiales Clase A de consumo constante (ej. Láminas estándar, tubería de alta rotación). | Revisión continua $(s, Q)$ con $EOQ$ y entregas semanales/quincenales de proveedores. | $SS$ bajo calculado con variabilidad de Lead Time ($Z \cdot \sigma_L \cdot \bar{d}$). | Conteo cíclico semanal / diario. Auditoría ERI estricta. |
| **AY** | Materiales Clase A con variabilidad mensual (ej. Pintura electrostática por campañas de color). | Revisión continua $(s, S)$ combinada con el Plan Maestro de Producción (MPS). | $SS$ aumentado para absorber variabilidad de demanda y suministro. | Conteo cíclico quincenal. |
| **AZ** | Materiales Clase A de consumo esporádico (ej. Vidrio templado especial para proyectos grandes). | Compra estricta bajo pedido (*Make-to-Order / JIT*). Cero stock especulativo. | $SS = 0$. Se adquiere exclusivamente contra orden de producción en firme. | Conteo por lote al recibir y consumir. |
| **BX** | Insumos secundarios de consumo estable (ej. Tornillería estándar, empaque plástico regular). | Modelo $(s, Q)$ estándar con reposición automatizada por ERP. | $SS$ estándar ($Z=1.64485$). | Conteo cíclico mensual. |
| **BY** | Insumos secundarios con variabilidad moderada (ej. Correderas telescópicas especiales). | Revisión periódica $(R, s, S)$ mensual. | $SS$ ajustado por lote de producción. | Conteo mensual. |
| **BZ** | Insumos secundarios erráticos. | Compra contra requerimiento neto MRP al explotar el BOM. | $SS$ mínimo o nulo. | Conteo trimestral. |
| **CX** | Insumos de bajo valor y consumo continuo (ej. Tornillos genéricos, arandelas, cinta). | Sistema visual de 2 cajones (*Two-Bin*) o compra por lotes grandes para minimizar costo de orden $S$. | Stock de reserva visual simple. | Conteo semestral. |
| **CY** | Insumos de bajo valor con demanda esporádica. | Compras agrupadas por familia de material. | Stock mínimo de contingencia. | Conteo semestral / anual. |
| **CZ** | **301 SKUs de Plata Muerta** + materiales marginales sin predictibilidad. | **BLOQUEO TOTAL DE COMPRAS ($EOQ=0, ROP=0$).** Plan de depuración de catálogo. | **$SS = 0$**. Prohibido retener o recomprar. | Inventario físico anual o en remate. |

---

## 🧊 5. Protocolo Estricto para SKUs de "Plata Muerta" (Dead Stock)

### 📌 Criterio de Identificación Formal:
Un SKU se clasifica inequívocamente como **Plata Muerta** si cumple:
$$\text{Unidades Consumidas en 21 meses} = 0 \quad \land \quad \text{Stock Inicial} > 0$$

### 📊 Radiografía Cuantitativa en E2 SAS:
* **Cantidad de SKUs:** **301 SKUs** (71.67% de todo el catálogo de 420 materias primas).
* **Unidades Físicas Inmovilizadas:** **123,396 unidades**.
* **Capital Atrapado:** **$3.550.022.309 COP** (53.99% del inventario inicial de $6.574M COP).
* **Costo Anual de Posesión ($H = 25\%$ anual):**
  $$\text{Costo Posesión Anual} = \$3.550.022.309 \times 0.25 = \mathbf{\$887.505.577 \text{ COP/año}}$$
  $$\text{Costo en 21 Meses} = \$887.505.577 \times \frac{21}{12} = \mathbf{\$1.553.134.760 \text{ COP}}$$

### 🚫 Reglas Innegociables para el Agente IA / LLM:
1. **Bloqueo Inmediato de Reorden:** Si el usuario o una rutina de compras consulta por un SKU con $D=0$:
   * El LLM **NUNCA** debe sugerir una compra ni calcular un lote económico positivo.
   * Asignar estrictamente: $EOQ = 0$, $ROP = 0$, $SS = 0$, $\text{Semáforo} = \text{'PLATA\_MUERTA'}$.
2. **Propuesta de Plan de Desacumulación:** El LLM debe emitir proactivamente las siguientes 4 vías de saneamiento:
   * **Reingeniería de Producto:** Modificar BOMs de los 18 PT para sustituir insumos activos por estos saldos inmovilizados.
   * **Devolución / Canje con Proveedor:** Negociar con proveedores habituales devolución con nota crédito o canje por insumos Clase A.
   * **Venta / Remate de Lote:** Comercializar como excedente industrial o chatarra para recuperar liquidez inmediata.
   * **Liberación de M² en Bodega:** Despejar estanterías para optimizar el almacenamiento de Lámina y Tubería (Clase A).

---

## 🗄️ 6. Consultas SQL Canónicas en Supabase

### A. Consulta General del Ranking ABC
```sql
SELECT 
    sku,
    descripcion,
    categoria,
    costo_unitario_formato,
    unidades_consumidas_formato,
    consumo_anual_formato,
    valor_consumo_anual_formato,
    pct_participacion_formato,
    pct_acumulado_formato,
    clasificacion_abc
FROM public.vista_clasificacion_abc
ORDER BY valor_consumo_anual_cop DESC;
```

### B. Resumen Ejecutivo por Categoría Pareto
```sql
SELECT 
    clasificacion_abc,
    COUNT(*) AS total_skus,
    TO_CHAR(ROUND((COUNT(*)::numeric / 420 * 100), 2), 'FM990.00') || ' %' AS pct_catalogo,
    '$ ' || TO_CHAR(SUM(valor_consumo_anual_cop), 'FM999,999,999,990') || ' COP' AS valor_consumo_anual_cop,
    TO_CHAR(SUM(pct_participacion_individual), 'FM990.00') || ' %' AS pct_valor_total
FROM public.vista_clasificacion_abc
GROUP BY clasificacion_abc
ORDER BY clasificacion_abc;
```

### C. Aislamiento de SKUs de Plata Muerta
```sql
SELECT 
    m.sku,
    m.descripcion,
    m.categoria,
    '$ ' || TO_CHAR(m.costo_unitario, 'FM999,999,990') AS costo_unitario,
    i.stock_inicial AS unidades_inmovilizadas,
    '$ ' || TO_CHAR(i.stock_inicial * m.costo_unitario, 'FM999,999,999,990') || ' COP' AS capital_atrapado_cop,
    '$ ' || TO_CHAR(i.stock_inicial * m.costo_unitario * 0.25, 'FM999,999,999,990') || ' COP' AS costo_posesion_anual_cop
FROM public.maestro_materiales m
JOIN public.inventario_inicial i ON m.sku = i.sku
LEFT JOIN (
    SELECT DISTINCT sku 
    FROM public.movimientos_inventarios 
    WHERE tipo_movimiento = 'salida'
) mov ON m.sku = mov.sku
WHERE mov.sku IS NULL
  AND m.sku NOT LIKE 'MP-9%'
ORDER BY (i.stock_inicial * m.costo_unitario) DESC;
```

---

## 🤖 7. Árbol de Decisión para Razonamiento del LLM

Cuando un usuario pregunte por el análisis de un SKU o catálogo:

```
                          ¿El SKU tiene salidas > 0?
                                  │
                 ┌────────────────┴────────────────┐
                 │ SÍ                              │ NO
                 ▼                                 ▼
      Calcular V_i = D_i * C_u               SKU ES PLATA MUERTA
      Verificar % Acumulado                  • Asignar Clase C / Z
                 │                           • Bloquear compras (EOQ = 0)
      ┌──────────┼──────────┐                • Reportar capital inmovilizado
      ▼          ▼          ▼                • Sugerir plan de remate/canje
   <= 80%     <= 95%      > 95%
  Clase A    Clase B     Clase C
      │          │          │
      └──────────┬──────────┘
                 │
                 ▼
      Calcular CV Mensual (σ_d / d̄)
      ┌──────────┼──────────┐
      ▼          ▼          ▼
   CV <= 0.5   0.5<CV<=1   CV > 1.0
    Clase X     Clase Y    Clase Z
                 │
                 ▼
      Cruzar Matriz 3x3 y
      Emitir Política Operativa
```

