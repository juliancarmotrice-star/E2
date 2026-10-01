---
name: exactitud-inventarios-eri-e2
description: >-
  Audita la Exactitud en el Registro de Inventario (ERI) y reconciliación
  tridimensional (Kardex teórico vs Conteo Físico Oficial vs Cuaderno del Jefe)
  para E2 SAS. Utilícese para validar la veracidad de los saldos de stock,
  cuantificar la desalineación contable y evitar compras basadas en saldos fantasma.
  Enfatiza el consumo directo de las vistas analíticas de Supabase.
---

# 🔍 Motor de Auditoría y Exactitud de Inventario (ERI) — E2 SAS

Este skill es la **guía canónica de razonamiento paso a paso** para que cualquier LLM o agente de IA audite la veracidad de los saldos de inventario, calcule la Exactitud en el Registro de Inventario (**ERI**) y cuantifique la desalineación contable en **E2 SAS**.

> [!IMPORTANT]
> **DIRECTIVA PRINCIPAL PARA EL LLM (CONSULTA DE VISTAS ANALÍTICAS):**
> La base de datos en Supabase cuenta con **vistas analíticas precalculadas y optimizadas**:
> * **`public.vista_resumen_eri_inventarios`**: Métricas globales y resumen por tipo de rotación (activos vs inactivos).
> * **`public.vista_diagnostico_eri_inventarios`**: Detalle fila por fila de los 420 SKUs con saldos reconciliados, discrepancias en unidades, desalineación en COP y estado de semáforo.
> 
> **Regla de Oro:** El LLM **NUNCA** debe calcular o reconstruir el ERI manualmente desde tablas crudas si puede consultar estas vistas directamente mediante SQL en Supabase.

---

## 🎯 1. Contexto y Reconciliación Tridimensional

En **E2 SAS**, la exactitud del inventario se audita contrastando **3 fuentes de información independientes** para cada uno de los 420 SKUs:

```
                       RECONCILIACIÓN TRIDIMENSIONAL
                     ┌───────────────────────────────┐
                     │  1. KARDEX TEÓRICO DEL ERP    │
                     │  Saldo = Inicial + E - S + A  │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
        ┌────────────────────────────┴────────────────────────────┐
        │                                                         │
        ▼                                                         ▼
 ┌───────────────────────────────┐         ┌───────────────────────────────┐
 │  2. CONTEO FÍSICO OFICIAL     │ ◄─────► │  3. CUADERNO DEL JEFE         │
 │  Auditoría física (Piso)      │         │  Control manual paralelo      │
 └───────────────────────────────┘         └───────────────────────────────┘
```

1. **Kardex Teórico del ERP:** Reconstruido dinámicamente desde el inventario inicial más todas las transacciones históricas de entradas, salidas y ajustes.
2. **Conteo Físico Oficial:** Auditoría física general al cierre del periodo de 21 meses (`conteo_fisico`).
3. **Cuaderno del Jefe de Planta:** Registros independientes de control físico de bodega paralela (`inventario_bodega_JEFE`).

---

## 🪜 2. Algoritmo Paso a Paso: Auditoría ERI y Desalineación Contable

Cualquier LLM debe comprender y seguir la siguiente secuencia de **5 pasos determinísticos**:

```
 [Paso 1] Reconstruir Saldo de Kardex Teórico por SKU
    │
    ▼
 [Paso 2] Cruzar con Conteo Físico Oficial y Cuaderno del Jefe
    │
    ▼
 [Paso 3] Calcular Discrepancia Física en Unidades (Stock Físico - Stock Kardex)
    │
    ▼
 [Paso 4] Valorizar la Desalineación Contable Bruta en COP (|Discrepancia| * Costo Unitario)
    │
    ▼
 [Paso 5] Evaluar Exactitud ERI (Binaria Estricta vs Tolerante) y Semáforo de Riesgo
```

---

### Paso 1: Reconstruir el Kardex Teórico ($K_i$)
Para cada SKU $i \in \{1, \dots, 420\}$:
$$\text{Stock Kardex}_i = \text{Stock Inicial}_i + \sum \text{Entradas}_i - \sum \text{Salidas}_i + \sum \text{Ajustes}_i$$
* **Fuente:** Tabla `inventario_inicial` cruzada con `movimientos_inventarios`.
* **Cuidado con signos:** En `movimientos_inventarios` las salidas deben restar y las entradas sumar. Si hay cantidades absolutas, aplicar la regla contable según `tipo_movimiento`.

---

### Paso 2: Cruzar con Auditoría Física ($F_i$) y Bodega Jefe ($J_i$)
* $F_i$: `conteo_fisico.stock_fisico_contado` (Auditoría oficial).
* $J_i$: `inventario_bodega_JEFE.conteo_jefe` (Conteo paralelo para 120 SKUs críticos).

---

### Paso 3: Calcular la Discrepancia en Unidades ($\Delta_i$)
$$\Delta_i = F_i - K_i = \text{Stock Físico}_i - \text{Stock Kardex}_i$$
* **$\Delta_i = 0$:** Registro perfectamente cuadrado (**Exacto**).
* **$\Delta_i > 0$:** Sobrante físico (Excedente en bodega no registrado en ERP).
* **$\Delta_i < 0$:** Faltante físico / Merma (Pérdida física o consumo no reportado).

---

### Paso 4: Cuantificar la Desalineación Contable Bruta ($M_i$)
La desalineación monetaria mide el error contable absoluto en pesos colombianos ($COP$):
$$M_i = |\Delta_i| \times C_{u, i} = |\text{Stock Físico}_i - \text{Stock Kardex}_i| \times \text{Costo Unitario}_i$$
* **Desalineación Contable Total del Sistema:**
  $$M_{\text{total}} = \sum_{i=1}^{N} M_i \quad (\approx \mathbf{\$48.792.923.505 \text{ COP}})$$

---

### Paso 5: Calcular el Porcentaje de Exactitud ERI

#### A. Exactitud Binaria Estricta (Norma Internacional APICS / Oficial E2 SAS):
Un SKU es exacto si y solo si la discrepancia es estrictamente cero ($\Delta_i = 0$):
$$\text{ERI Global (\%)} = \left( \frac{\sum_{i=1}^{N} \mathbb{I}(\Delta_i = 0)}{N} \right) \times 100$$
*(Donde $\mathbb{I}$ es la función indicadora: 1 si es exacto, 0 si está descuadrado).*

#### B. Exactitud con Tolerancia Operativa ($\pm 10\%$):
$$\text{ERI Tolerante (\%)} = \left( \frac{\sum_{i=1}^{N} \mathbb{I}(|\Delta_i| \le 0.10 \times K_i)}{N} \right) \times 100$$

---

## 📊 3. Línea Base Diagnosticada (Fase E1 — AS-IS)

Al consultar las vistas analíticas, el LLM debe reportar la siguiente verdad fundamental de los datos:

| Segmento de Inventario | Total SKUs | SKUs Exactos | SKUs Descuadrados | ERI Exactitud Binaria | Desalineación Contable Bruta | Diagnóstico Crítico |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **🔴 SKUs Activos (En Rotación)** | **119** | **0** | **119** | **`0.00 %`** | **`$ 48.760.853.889 COP`** | **100% de los materiales activos están descuadrados** |
| **🟢 SKUs Inactivos (Plata Muerta)** | **301** | **282** | **19** | **`93.69 %`** | **`$ 32.069.616 COP`** | 19 SKUs con mermas físicas no reportadas |
| **TOTAL GENERAL** | **420** | **282** | **138** | **`67.14 %`** | **`$ 48.792.923.505 COP`** | **$48.792M COP de incertidumbre contable** |

> [!NOTE]
> **Aclaración sobre el "75% de ERI" mencionado en juntas:**
> Si un usuario o directivo afirma que el ERI debería ser del **75.25%**, el LLM debe explicar con solvencia técnica:
> 1. El $75.25\%$ proviene de asumir ingenuamente que los 301 inactivos están $100\%$ cuadrados ($301 / 400 = 75.25\%$) o de aplicar una banda de tolerancia del $\pm 10\%$.
> 2. El valor real, auditado con precisión binaria de $1$ unidad sobre los 420 SKUs, es **`67.14%`** porque se descubrieron 19 SKUs inactivos con fugas/mermas físicas reales.

---

## 🗄️ 4. Consultas a las Vistas Analíticas en Supabase (Uso Mandatorio)

El LLM debe utilizar las siguientes consultas predefinidas:

### A. Resumen Ejecutivo de Exactitud (KPIs Clave)
```sql
SELECT 
    tipo_rotacion,
    total_skus,
    skus_exactos,
    skus_descuadrados,
    eri_porcentaje_exactitud,
    desalineacion_contable_bruta
FROM public.vista_resumen_eri_inventarios;
```

### B. Top 20 SKUs con Mayor Riesgo y Desalineación Monetaria
```sql
SELECT 
    sku,
    descripcion,
    categoria,
    costo_unitario_formato,
    stock_kardex_formato,
    stock_fisico_formato,
    discrepancia_formato,
    desalineacion_dinero_formato,
    estado_eri,
    tipo_rotacion
FROM public.vista_diagnostico_eri_inventarios
WHERE estado_eri LIKE 'Descuadrado%'
ORDER BY desalineacion_dinero_cop DESC
LIMIT 20;
```

### C. Consulta Individual de un SKU Específico
```sql
SELECT 
    sku,
    descripcion,
    categoria,
    costo_unitario_formato,
    stock_inicial_und,
    entradas_total_und,
    salidas_total_und,
    stock_kardex_formato,
    stock_fisico_formato,
    stock_jefe_formato,
    discrepancia_formato,
    desalineacion_dinero_formato,
    estado_eri
FROM public.vista_diagnostico_eri_inventarios
WHERE sku = 'MP-0001'; -- Reemplazar por el SKU consultado
```

---

## 🚦 5. Semáforo y Reglas de Decisión para el Agente IA

| Estado ERI | Condición en Vista | Acción Inmediata del Agente IA |
|---|---|---|
| **🟢 `Cuadrado (Exacto)`** | $\Delta_i = 0$ | Operación regular. El stock del Kardex es confiable para planificar compras y MRP. |
| **🔴 `Descuadrado - Faltante Fisico`** | $\Delta_i < 0$ | **ADVERTENCIA OBLIGATORIA:** Hay menos material físico en piso del que dice el sistema. Si se evalúa compra, usar el Conteo Físico como stock base para evitar desabastecimiento. |
| **🟡 `Descuadrado - Sobrante Fisico`** | $\Delta_i > 0$ | **ALERTA DE SOBRESTOCK:** Hay más material físico del registrado. Bloquear compras inmediatas hasta realizar ajuste contable de entrada para no sobrecomprar. |

### 🚫 Reglas Innegociables para el LLM:
1. **Advertencia de Incertidumbre en Órdenes de Compra:** Cuando se sugiera una orden de compra para un SKU con estado `Descuadrado`, el LLM **DEBE incluir**:
   > ⚠️ *Advertencia ERI: El SKU presenta discrepancia entre Kardex ($K$) y Piso ($F$). Se requiere validar físicamente el lote en bodega antes de radicar la orden.*
2. **Cero Compras Basadas en Negativos Fantasma:** Si el Kardex muestra saldo negativo por consumos sin ingreso previo, tomar el **Conteo Físico Oficial** como saldo disponible real.

