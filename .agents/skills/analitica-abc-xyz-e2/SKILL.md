---
name: analitica-abc-xyz-e2
description: >-
  Aplica la metodología general de clasificación paramétrica ABC (Pareto por valor de consumo anualizado 80/15/5)
  y segmentación XYZ (variabilidad de demanda por Coeficiente de Variación) para cualquier catálogo de materias primas (N SKUs).
  Utilícese para identificar SKUs estratégicos Clase A, calcular la matriz cruzada ABC-XYZ,
  aislar SKUs inmovilizados de Plata Muerta y definir políticas diferenciadas de inventario y compras.
  Enfatiza el consumo directo de la vista analítica vista_clasificacion_abc en Supabase.
---

# 🧠 Motor General de Analítica y Clasificación ABC-XYZ

Este skill es la **guía metodológica y algorítmica general paso a paso** para que cualquier LLM o agente de IA comprenda, calcule, audite y aplique la segmentación multicriterio sobre **cualquier catálogo de materias primas ($N$ SKUs)**, **cualquier cantidad de productos terminados ($P$ PTs)** y **cualquier horizonte temporal ($T$ días / $M$ periodos)**.

> [!IMPORTANT]
> **DIRECTIVA PRINCIPAL PARA EL LLM (CONSULTA DE LA VISTA ANALÍTICA DINÁMICA):**
> La base de datos en Supabase cuenta con la vista analítica oficial, dinámica y precalculada:
> * **`public.vista_clasificacion_abc`**: Calcula automáticamente y en tiempo real el valor anualizado en COP, porcentaje de participación individual, porcentaje acumulado de Pareto y la clasificación $A$, $B$ o $C$ para la totalidad de los SKUs registrados en el catálogo.
> 
> **Regla de Oro:** El LLM **NUNCA** debe calcular el Pareto a mano, asumir tamaños fijos de catálogo o inventar cifras de memoria si puede consultar directamente `public.vista_clasificacion_abc` en Supabase.

---

## 🎯 1. Principios y Alcance General del Motor

El motor de segmentación multicriterio está diseñado para procesar de forma completamente dinámica:
* **Catálogos de $N$ materias primas** ($N$ variable: 100, 420, 500, 1.000+ SKUs).
* **Horizonte temporal dinámico de $T_{\text{dias}}$** (calculado automáticamente a partir de la fecha mínima y máxima observada en el histórico de transacciones).
* **$M$ periodos de análisis** (semanales, mensuales o trimestrales).

```
                             ARQUITECTURA GENERAL DEL MOTOR
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                     CATÁLOGO GENERAL DE N SKUs REGISTRADOS                  │
 └───────────────────────┬──────────────────────────────┬───────────────────────┘
                         │                              │
                         ▼                              ▼
            ┌──────────────────────────┐   ┌──────────────────────────┐
            │   SKUs ACTIVOS (D > 0)   │   │  SKUs INACTIVOS (D = 0)  │
            │ (Con salidas históricas) │   │     (PLATA MUERTA)       │
            └────────────┬─────────────┘   └────────────┬─────────────┘
                         │                              │
                         ▼                              ▼
            ┌──────────────────────────┐   ┌──────────────────────────┐
            │  Segmentación ABC + XYZ  │   │ Asignación Directa: CZ   │
            │ (Pareto Valor + CV Mens) │   │ (Bloqueo Total de Compra)│
            └──────────────────────────┘   └──────────────────────────┘
```

---

## 🪜 2. Algoritmo Paso a Paso: Clasificación ABC (Pareto Monetario Dinámico)

Cualquier LLM debe ejecutar o validar el cálculo ABC siguiendo estrictamente esta secuencia de **6 pasos matemáticos generales**:

```
 [Paso 1] Normalizar y Filtrar Salidas por SKU (Q_consumo_total)
    │
    ▼
 [Paso 2] Determinar Horizonte Temporal y Anualizar Demanda (D_i = Q_i * 365 / T_días)
    │
    ▼
 [Paso 3] Calcular Valor Anualizado por SKU (V_i = D_i * Costo_Unitario_i)
    │
    ▼
 [Paso 4] Ordenar Descendente y Calcular % de Participación Individual (p_i = V_i / V_total * 100)
    │
    ▼
 [Paso 5] Calcular % Acumulado de Lorenz (P_acum_i = suma(p_1 .. p_i))
    │
    ▼
 [Paso 6] Asignar Categoría ABC con Criterio de Borde Inclusivo (80% / 95% / 100%)
```

---

### Paso 1: Filtrar y Consolidar Salidas por SKU
* **Fuente de datos:** Tabla `movimientos_inventarios`.
* **Filtro obligatorio:** Considerar únicamente registros transaccionales donde `tipo_movimiento = 'salida'`.
* **Cálculo:** Para cada SKU $i \in \{1, 2, \dots, N\}$, sumar las cantidades absolutas despachadas:
  $$Q_{\text{consumo\_total}, i} = \sum_{\text{salidas}} |\text{cantidad}_i|$$
* *Regla para inactivos:* Si un SKU registrado en `maestro_materiales` no presenta salidas en la ventana analizada, $Q_{\text{consumo\_total}, i} = 0$.
* *Filtro de integridad:* Excluir códigos de prueba, duplicados o descartados por gobernanza (`sku NOT LIKE 'MP-9%'` y `descripcion NOT LIKE '%(dup)%'`).

---

### Paso 2: Calcular el Horizonte y Factor de Anualización ($F_{\text{anual}}$)
El cálculo es completamente independiente de la duración de la muestra:
* **Horizonte temporal observado en días:**
  $$T_{\text{dias}} = \max(\text{fecha}) - \min(\text{fecha}) + 1$$
* **Factor de anualización dinámico:**
  $$F_{\text{anual}} = \frac{365}{T_{\text{dias}}}$$
* **Demanda anualizada en unidades ($D_i$):**
  $$D_i = Q_{\text{consumo\_total}, i} \times F_{\text{anual}} = Q_{\text{consumo\_total}, i} \times \left(\frac{365}{T_{\text{dias}}}\right)$$

---

### Paso 3: Calcular el Valor de Consumo Anualizado ($V_i$)
Para cada uno de los $N$ materiales:
$$V_i = D_i \times C_{u, i}$$
*(Donde $C_{u, i}$ es el costo de reposición unitario en moneda local consignado en `maestro_materiales`).*

---

### Paso 4: Calcular el Total Global del Sistema y Participación Individual ($p_i$)
* **Valor total de consumo anual de la organización:**
  $$V_{\text{total}} = \sum_{k=1}^{N} V_k$$
* **Participación porcentual de cada SKU:**
  $$p_i = \left( \frac{V_i}{V_{\text{total}}} \right) \times 100$$
* **Ordenamiento:** Ordenar los $N$ materiales de forma estrictamente **descendente** según $V_i$ ($V_1 \ge V_2 \ge \dots \ge V_N$).

---

### Paso 5: Calcular la Curva de Lorenz (% Acumulado $P_{\text{acum}, i}$)
Para el material ubicado en la posición $i$ del ranking ordenado:
$$P_{\text{acum}, i} = \sum_{j=1}^{i} p_j = \left( \frac{\sum_{j=1}^{i} V_j}{V_{\text{total}}} \right) \times 100$$

---

### Paso 6: Asignar la Categoría ABC (Criterio de Borde Inclusivo)

Los umbrales de corte paramétricos estándar son **80% / 15% / 5%** con inclusión del SKU de frontera:

| Categoría ABC | Condición Lógica Formal | Significado Estratégico |
|:---:|---|---|
| **🅰️ Clase A** | $P_{\text{acum}, i} \le 80.00\%$ **O** ($P_{\text{acum}, i-1} < 80.00\% \land P_{\text{acum}, i} \ge 80.00\%$) | **Insumos Críticos / Estratégicos:** Concentran el ~80% del valor total. Requieren control diario, conteo cíclico permanente y negociación prioritaria con proveedores. |
| **🅱️ Clase B** | ($80.00\% < P_{\text{acum}, i} \le 95.00\%$) **O** ($P_{\text{acum}, i-1} < 95.00\% \land P_{\text{acum}, i} \ge 95.00\%$) | **Insumos Intermedios:** Aportan el siguiente ~15% del valor. Revisión periódica quincenal/mensual y reposición por lote económico estándar. |
| **🅲 Clase C** | $P_{\text{acum}, i} > 95.00\%$ (Incluye todos los SKUs con consumo $= 0$) | **Insumos Marginales / Inmovilizados:** Aportan el último ~5% del valor pero suelen concentrar la mayor cantidad de referencias físicas y riesgo de obsolescencia. |

---

## 🪜 3. Algoritmo Paso a Paso: Segmentación XYZ (Variabilidad de Demanda)

La clasificación XYZ evalúa la **estabilidad temporal y predictibilidad del consumo** a lo largo de $M$ periodos temporales homogéneos (ej. $M$ meses).

```
 [Paso 1] Construir Serie de Tiempo Periódica de Consumo (m = 1 .. M)
    │
    ▼
 [Paso 2] Calcular Media Periódica (d̄_i) y Desviación Estándar Muestral (σ_d_i)
    │
    ▼
 [Paso 3] Calcular Coeficiente de Variación (CV_i = σ_d_i / d̄_i)
    │
    ▼
 [Paso 4] Asignar Categoría XYZ según Umbrales (X <= 0.50, Y <= 1.00, Z > 1.00)
```

---

### Paso 1: Construir la Serie Temporal ($d_{i, m}$)
* Dividir el horizonte temporal en $M$ intervalos regulares ($m \in \{1, 2, \dots, M\}$).
* Para cada SKU $i$, agregar las salidas del periodo $m$:
  $$d_{i, m} = \sum_{\text{salidas en periodo } m} |\text{cantidad}_i|$$
* > [!IMPORTANT]
  > **Regla de Zero-Padding (Cero Relleno Obligatorio):** Si en el periodo $m$ un SKU no registró salidas, el valor **DEBE SER 0 (cero)**. Jamás omitir periodos vacíos, ya que omitirlos subestima drásticamente la desviación estándar real y oculta la intermitencia.

---

### Paso 2: Calcular Estadísticos Descriptivos
* **Consumo promedio por periodo:**
  $$\bar{d}_i = \frac{1}{M} \sum_{m=1}^{M} d_{i, m}$$
* **Desviación estándar muestral:**
  $$\sigma_{d, i} = \sqrt{\frac{1}{M - 1} \sum_{m=1}^{M} (d_{i, m} - \bar{d}_i)^2}$$

---

### Paso 3: Calcular el Coeficiente de Variación ($CV_i$)
$$CV_i = \frac{\sigma_{d, i}}{\bar{d}_i}$$

#### Casos Límite y Tratamiento de Excepciones:
1. **Si $\bar{d}_i = 0$ (Plata Muerta / Cero salidas):** Matemáticamente indefinido ($\frac{0}{0}$). **Regla:** Asignar automáticamente $CV_i = \infty \implies \textbf{Clase Z}$.
2. **Si $\sigma_{d, i} = 0 \land \bar{d}_i > 0$ (Consumo idéntico todos los periodos):** $CV_i = 0 \implies \textbf{Clase X}$.
3. **Si el material tiene consumo esporádico (ej. 1 solo periodo de $M$):** $CV_i \gg 1.0 \implies \textbf{Clase Z}$.

---

### Paso 4: Asignar la Categoría XYZ

| Clase XYZ | Criterio de Dispersión | Comportamiento del Patrón de Demanda | Predictibilidad | Estrategia de Planificación |
|:---:|:---:|---|:---:|---|
| **🟢 Clase X** | **$CV \le 0.50$** | Demanda regular, continua y altamente predecible. | **Muy Alta** | Reposición automatizada por punto de reorden $(s, Q)$ con bajo stock de seguridad. |
| **🟡 Clase Y** | **$0.50 < CV \le 1.00$** | Demanda con fluctuaciones moderadas, estacionalidad o lotes variables. | **Media** | Reposición con Stock de Seguridad dinámico ajustado por variabilidad conjunta ($\sigma_d$ y $\sigma_L$). |
| **🔴 Clase Z** | **$CV > 1.00$** o $\bar{d} = 0$ | Demanda errática, esporádica, altamente intermitente o **nula**. | **Baja / Nula** | Compra estricta bajo pedido (*Make-to-Order / JIT*) o **bloqueo de compras** si es inactivo. |

---

## 🗂️ 4. Matriz Combinada ABC - XYZ (Políticas de Gestión 3x3)

Al cruzar ambas dimensiones, el LLM debe emitir las siguientes recomendaciones operativas según la celda:

```
                  MATRIZ GENERAL MULTICRITERIO ABC - XYZ
     ┌──────────────────────┬──────────────────────┬──────────────────────┐
     │       CLASE X        │       CLASE Y        │       CLASE Z        │
     │     (CV <= 0.50)     │   (0.50 < CV <= 1.0) │      (CV > 1.0)      │
┌────┼──────────────────────┼──────────────────────┼──────────────────────┤
│    │ AX: Insumos Clave    │ AY: Alto Valor Var.  │ AZ: Alto Riesgo      │
│ A  │ • Reposición EOQ/ROP │ • Pronósticos collab │ • Compra bajo pedido │
│    │ • Pedidos frecuentes │ • SS dinámico        │ • Cero stock especul.│
│    │ • Control diario     │ • Control semanal    │ • Auditoría x lote   │
├────┼──────────────────────┼──────────────────────┼──────────────────────┤
│    │ BX: Valor Intermedio │ BY: Intermedio Var.  │ BZ: Intermedio Errát.│
│ B  │ • EOQ estándar       │ • Revisión periódica │ • MTO / Lote mínimo  │
│    │ • Revisión quincenal │ • SS moderado        │ • Evitar sobre-stock │
├────┼──────────────────────┼──────────────────────┼──────────────────────┤
│    │ CX: Consumo Marginal │ CY: Marginal Var.    │ CZ: PLATA MUERTA     │
│ C  │ • Sistema 2 cajones  │ • Compras agrupadas  │ • SKUs BLOQUEADOS    │
│    │ • Compras x volumen  │ • Mínima atención    │ • Desacumular / Remat│
└────┴──────────────────────┴──────────────────────┴──────────────────────┘
```

---

## 🧊 5. Protocolo General para SKUs de "Plata Muerta" (Dead Stock)

### 📌 Criterio de Identificación Formal:
Un SKU se clasifica inequívocamente como **Plata Muerta** si cumple:
$$\text{Consumo Total en el Horizonte Observado} = 0 \quad \land \quad \text{Stock Inicial / Físico} > 0$$

### 💰 Cuantificación Financiera Universal:
* **Capital Inmovilizado ($COP$):**
  $$\text{Capital Atrapado}_i = \text{Stock Actual}_i \times C_{u, i}$$
* **Costo Anual de Posesión ($H = 25\%$ anual):**
  $$\text{Costo Posesión Anual}_i = \text{Capital Atrapado}_i \times H$$

### 🚫 Reglas Innegociables para el LLM:
1. **Bloqueo Absoluto de Compras:** Si un SKU tiene $D=0$, el LLM **NUNCA** debe sugerir una compra ni calcular un lote económico positivo ($EOQ=0, ROP=0, SS=0$).
2. **Recomendaciones de Saneamiento:** Sugerir proactivamente:
   * Reingeniería y sustitución en listas de materiales (BOM).
   * Canje o devolución a proveedores por materiales Clase A.
   * Remate / venta como excedente o chatarra para recuperar liquidez.
   * Liberación de espacio físico en almacén.

---

## 📌 6. Caso de Estudio de Referencia (Línea Base Histórica Inicial E1)

A modo de **validación empírica y contraste histórico** para el dataset de arranque de **E2 SAS** ($N=420$ SKUs, $M=21$ meses, $P=18$ productos terminados):

| Segmento / Categoría | Total SKUs | % Catálogo | Valor Consumo Anualizado (COP) | % Consumo Total | Diagnóstico Observado |
|---|:---:|:---:|:---:|:---:|---|
| **🅰️ Clase A** | **30 SKUs** | **7.14%** | **$27.873.531.428 COP** | **80.16%** | Hiper-concentración en láminas y tuberías de alto calibre. |
| **🅱️ Clase B** | **30 SKUs** | **7.14%** | **$5.248.310.285 COP** | **15.09%** | Insumos intermedios y herrajes principales. |
| **🅲 Clase C** | **360 SKUs** | **85.71%** | **$1.650.353.575 COP** | **4.75%** | Incluye 301 SKUs de Plata Muerta ($3.550M COP inmovilizados). |
| **TOTAL BASELINE** | **420 SKUs** | **100.00%** | **$34.772.195.288 COP** | **100.00%** | Catálogo inicial auditado. |

*(Nota: Si en el futuro ingresan nuevos SKUs o periodos, la vista SQL recalculará estas métricas dinámicamente sin alterar la lógica de negocio).*

---

## 🗄️ 7. Consultas SQL Dinámicas en Supabase

### A. Consulta General del Ranking ABC (Totalmente Dinámica)
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

### B. Resumen Dinámico por Categoría Pareto (% Calculado en Tiempo Real)
```sql
SELECT 
    clasificacion_abc,
    COUNT(*) AS total_skus,
    TO_CHAR(ROUND((COUNT(*)::numeric / SUM(COUNT(*)) OVER() * 100), 2), 'FM990.00') || ' %' AS pct_catalogo_dinamico,
    '$ ' || TO_CHAR(SUM(valor_consumo_anual_cop), 'FM999,999,999,990') || ' COP' AS valor_consumo_anual_cop,
    TO_CHAR(SUM(pct_participacion_individual), 'FM990.00') || ' %' AS pct_valor_total
FROM public.vista_clasificacion_abc
GROUP BY clasificacion_abc
ORDER BY clasificacion_abc;
```

### C. Aislamiento Dinámico de Plata Muerta
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

## 🤖 8. Árbol de Decisión para Razonamiento del LLM

```
                          ¿El SKU tiene salidas registradas > 0?
                                            │
                 ┌──────────────────────────┴──────────────────────────┐
                 │ SÍ                                                  │ NO
                 ▼                                                     ▼
      Calcular V_i = D_i * C_u                               SKU ES PLATA MUERTA
      Verificar % Acumulado en Vista                         • Asignar Clase C / Z
                 │                                           • Bloquear compras (EOQ = 0)
      ┌──────────┼──────────┐                                • Reportar capital inmovilizado
      ▼          ▼          ▼                                • Sugerir plan de remate/canje
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

---

## 🗄️ 9. Archivo DDL de la Vista en Supabase

| Vista | Archivo DDL Fuente | Ubicación |
|-------|-------------------|-----------|
| `public.vista_clasificacion_abc` | `sql/03_vistas_analiticas_abc.sql` | Repositorio `PA-E2/sql/` |

> [!NOTE]
> La vista se crea con `CREATE OR REPLACE VIEW` y es completamente dinámica. Cada vez que se insertan nuevos movimientos o se actualiza el maestro de materiales, la vista recalcula automáticamente sin intervención manual.

---

## 🔗 10. Prerequisitos y Dependencias

* **Prerequisito obligatorio:** El skill [`limpieza-datos-e2`](../limpieza-datos-e2/SKILL.md) debe haberse ejecutado exitosamente con las tablas `maestro_materiales` y `movimientos_inventarios` cargadas en Supabase.
* **Tablas consumidas:** `public.maestro_materiales`, `public.movimientos_inventarios`, `public.inventario_inicial`.
* **Skills que dependen de esta:**
  * [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md): Consume la demanda anualizada ($D_i$) y el costo unitario para calcular $EOQ$.
  * [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md): Usa la clasificación ABC para priorizar auditorías de conteo cíclico en SKUs Clase A.

---

## 🔎 11. Queries de Verificación de Calidad

Ejecutar estas consultas para confirmar que la clasificación ABC es correcta y consistente:

### A. Verificar que la Suma de Participación = 100%
```sql
SELECT ROUND(SUM(pct_participacion_individual)::numeric, 2) AS suma_total_pct
FROM public.vista_clasificacion_abc;
-- Resultado esperado: ≈ 100.00
```

### B. Verificar Cortes de Pareto (Borde Inclusivo)
```sql
SELECT clasificacion_abc,
       COUNT(*) AS total_skus,
       MIN(pct_acumulado) AS pct_acum_min,
       MAX(pct_acumulado) AS pct_acum_max
FROM public.vista_clasificacion_abc
GROUP BY clasificacion_abc
ORDER BY clasificacion_abc;
-- Esperado: A max ≈ 80%, B max ≈ 95%, C max = 100%
```

### C. Verificar Total de SKUs = N del Catálogo
```sql
SELECT 
    (SELECT COUNT(*) FROM public.vista_clasificacion_abc) AS skus_en_vista,
    (SELECT COUNT(*) FROM public.maestro_materiales WHERE sku NOT LIKE 'MP-9%') AS skus_en_maestro;
-- Resultado esperado: Ambas cifras iguales
```

### D. Verificar Plata Muerta Correctamente Clasificada
```sql
SELECT COUNT(*) AS plata_muerta_no_clase_c
FROM public.vista_clasificacion_abc
WHERE valor_consumo_anual_cop = 0 AND clasificacion_abc != 'C';
-- Resultado esperado: 0 (toda Plata Muerta debe ser Clase C)
```

### E. Verificar Ordenamiento Descendente del Ranking
```sql
SELECT CASE 
    WHEN COUNT(*) = 0 THEN 'OK - Ranking ordenado correctamente'
    ELSE 'ERROR - ' || COUNT(*) || ' SKUs desordenados'
END AS check_orden
FROM (
    SELECT valor_consumo_anual_cop,
           LAG(valor_consumo_anual_cop) OVER (ORDER BY valor_consumo_anual_cop DESC) AS anterior
    FROM public.vista_clasificacion_abc
) sub
WHERE valor_consumo_anual_cop > anterior;
-- Resultado esperado: OK
```

---

## 🔄 12. Integración con Otros Skills del Sistema

| Skill Destino | Dato que Recibe de ABC-XYZ | Uso Operativo |
|---------------|---------------------------|---------------|
| [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md) | $D_i$ (Demanda anual), $C_{u,i}$ (Costo) | Cálculo de $EOQ = \sqrt{2DS/HC_u}$ |
| [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md) | Clasificación ABC | Priorización de compras: Clase A primero |
| [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md) | Clasificación ABC | Frecuencia de conteo cíclico: A=diario, B=quincenal, C=trimestral |
| [`sla-proveedores-mrp-e2`](../sla-proveedores-mrp-e2/SKILL.md) | Identificación de Plata Muerta | Bloquear órdenes de compra para SKUs con $D=0$ |

---

## 🚫 13. Fronteras del Skill (Qué NO hace este Skill)

* **NO calcular ROP, SS, EOQ:** Es responsabilidad del skill [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md).
* **NO calcular ERI / Desalineación Contable:** Es responsabilidad del skill [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md).
* **NO auditar SLA de proveedores ni explotar BOM:** Es responsabilidad del skill [`sla-proveedores-mrp-e2`](../sla-proveedores-mrp-e2/SKILL.md).
* **NO limpiar ni transformar datos crudos:** Es responsabilidad del skill [`limpieza-datos-e2`](../limpieza-datos-e2/SKILL.md).

Este skill entrega la **segmentación estratégica ABC-XYZ completa** y el **aislamiento financiero de Plata Muerta** para que los motores de reposición y auditoría prioricen recursos de forma inteligente.
