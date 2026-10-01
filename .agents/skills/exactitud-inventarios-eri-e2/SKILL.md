---
name: exactitud-inventarios-eri-e2
description: >-
  Audita la Exactitud en el Registro de Inventario (ERI) y reconciliación
  tridimensional (Kardex teórico vs Conteo Físico Oficial vs Cuaderno del Jefe)
  para cualquier catálogo de materias primas (N SKUs).
  Utilícese para validar la veracidad de los saldos de stock, cuantificar la desalineación
  contable y evitar compras basadas en saldos fantasma.
  Enfatiza el consumo directo de las vistas analíticas de Supabase.
---

# 🔍 Motor General de Auditoría y Exactitud de Inventario (ERI)

Este skill es la **guía metodológica y algorítmica general paso a paso** para que cualquier LLM o agente de IA audite la veracidad de los saldos de inventario, calcule la Exactitud en el Registro de Inventario (**ERI**) y cuantifique la desalineación contable sobre **cualquier catálogo de $N$ materias primas** y **cualquier volumen de movimientos transaccionales**.

> [!IMPORTANT]
> **DIRECTIVA PRINCIPAL PARA EL LLM (CONSULTA DE VISTAS ANALÍTICAS):**
> La base de datos en Supabase cuenta con **vistas analíticas precalculadas y optimizadas**:
> * **`public.vista_resumen_eri_inventarios`**: Métricas globales dinámicas y resumen por tipo de rotación (activos vs inactivos).
> * **`public.vista_diagnostico_eri_inventarios`**: Detalle fila por fila para la totalidad de los $N$ SKUs con saldos reconciliados, discrepancias en unidades, desalineación en COP y estado de semáforo.
> 
> **Regla de Oro:** El LLM **NUNCA** debe calcular o reconstruir el ERI manualmente desde tablas crudas si puede consultar estas vistas directamente mediante SQL en Supabase.

---

## 🎯 1. Principio de Reconciliación Tridimensional

La auditoría de exactitud contrasta de forma continua **3 fuentes de información independientes** para cada uno de los $N$ SKUs registrados:

```
                       RECONCILIACIÓN TRIDIMENSIONAL GENERAL
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
 │  2. CONTEO FÍSICO OFICIAL     │ ◄─────► │  3. AUDITORÍA / CONTROL PISO  │
 │  Auditoría física (Piso)      │         │  Verificación manual paralela │
 └───────────────────────────────┘         └───────────────────────────────┘
```

1. **Kardex Teórico del ERP ($K_i$):** Saldo lógico acumulado desde el inicio del registro histórico.
2. **Conteo Físico Oficial ($F_i$):** Auditoría física en piso de almacén (`conteo_fisico`).
3. **Control Auxiliar de Piso ($J_i$):** Registros independientes o conteos del jefe de patio (`inventario_bodega_JEFE`).

---

## 🪜 2. Algoritmo Paso a Paso: Auditoría ERI y Desalineación Contable

Cualquier LLM debe ejecutar y validar la exactitud siguiendo estrictamente estos **5 pasos matemáticos generales**:

```
 [Paso 1] Reconstruir Saldo de Kardex Teórico por SKU (K_i = Inicial + E - S + A)
    │
    ▼
 [Paso 2] Cruzar con Conteo Físico Oficial (F_i) y Control Auxiliar (J_i)
    │
    ▼
 [Paso 3] Calcular Discrepancia Física en Unidades (Δ_i = F_i - K_i)
    │
    ▼
 [Paso 4] Valorizar la Desalineación Contable Bruta (M_i = |Δ_i| * Costo_Unitario_i)
    │
    ▼
 [Paso 5] Calcular ERI Global Binario y Evaluar Semáforo de Incertidumbre
```

---

### Paso 1: Reconstruir el Kardex Teórico ($K_i$)
Para cada SKU $i \in \{1, 2, \dots, N\}$:
$$\text{Stock Kardex}_i = \text{Stock Inicial}_i + \sum \text{Entradas}_i - \sum \text{Salidas}_i + \sum \text{Ajustes}_i$$
* **Fuente:** Tabla `inventario_inicial` cruzada dinámicamente con `movimientos_inventarios`.
* **Regla contable:** Las salidas restan, las entradas suman y los ajustes suman/restan según su naturaleza.

---

### Paso 2: Cruzar con Fuentes Físicas de Verificación ($F_i$ y $J_i$)
* $F_i$: Conteo físico oficial (`conteo_fisico.stock_fisico_contado`).
* $J_i$: Conteo auxiliar de bodega (`inventario_bodega_JEFE.conteo_jefe`).

---

### Paso 3: Calcular la Discrepancia en Unidades ($\Delta_i$)
$$\Delta_i = F_i - K_i = \text{Stock Físico}_i - \text{Stock Kardex}_i$$
* **$\Delta_i = 0$:** Registro perfectamente cuadrado (**Exacto**).
* **$\Delta_i > 0$:** Sobrante físico (Excedente en bodega no registrado en el sistema contable).
* **$\Delta_i < 0$:** Faltante físico / Merma (Pérdida física o consumo no reportado).

---

### Paso 4: Cuantificar la Desalineación Contable Bruta ($M_i$)
Mide el error patrimonial absoluto en dinero ($COP$):
$$M_i = |\Delta_i| \times C_{u, i} = |\text{Stock Físico}_i - \text{Stock Kardex}_i| \times \text{Costo Unitario}_i$$
* **Desalineación Contable Total del Catálogo:**
  $$M_{\text{total}} = \sum_{i=1}^{N} M_i$$

---

### Paso 5: Calcular el Porcentaje de Exactitud ERI

#### A. Exactitud Binaria Estricta (Norma Estándar APICS):
Un SKU es exacto si y solo si la discrepancia es estrictamente cero ($\Delta_i = 0$):
$$\text{ERI Global (\%)} = \left( \frac{\sum_{i=1}^{N} \mathbb{I}(\Delta_i = 0)}{N} \right) \times 100$$
*(Donde $N = \text{COUNT(*)}$ es el número total dinámico de SKUs evaluados).*

#### B. Exactitud con Tolerancia Operativa ($\pm 10\%$):
$$\text{ERI Tolerante (\%)} = \left( \frac{\sum_{i=1}^{N} \mathbb{I}(|\Delta_i| \le 0.10 \times K_i)}{N} \right) \times 100$$

---

## 📌 3. Caso de Estudio de Referencia (Línea Base Histórica Inicial E1)

A modo de **referencia histórica y contraste metodológico** para el dataset inicial de **E2 SAS** ($N=420$ SKUs auditados):

| Segmento de Inventario | Total SKUs | SKUs Exactos | SKUs Descuadrados | ERI Exactitud Binaria | Desalineación Contable Bruta | Diagnóstico Crítico |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **🔴 SKUs Activos (En Rotación)** | **119** | **0** | **119** | **`0.00 %`** | **`$ 48.760.853.889 COP`** | 100% de los materiales activos presentaban descuadre físico. |
| **🟢 SKUs Inactivos (Plata Muerta)** | **301** | **282** | **19** | **`93.69 %`** | **`$ 32.069.616 COP`** | 19 SKUs con mermas físicas no reportadas. |
| **TOTAL BASELINE** | **420** | **282** | **138** | **`67.14 %`** | **`$ 48.792.923.505 COP`** | **Línea base de arranque auditada.** |

> [!NOTE]
> **Aclaración sobre el "75% de ERI":**
> El valor del $75.25\%$ proviene de aproximaciones teóricas que asumían que todos los inactivos estaban cuadrados ($301 / 400 = 75.25\%$) o de tolerancias del $\pm 10\%$. El cálculo riguroso binario sobre los 420 SKUs arrojó **`67.14%`** debido a las mermas físicas detectadas.

---

## 🗄️ 4. Consultas a las Vistas Analíticas en Supabase (Dinámicas)

### A. Resumen Ejecutivo Dinámico de Exactitud
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

### B. Top SKUs con Mayor Desalineación Monetaria
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

### C. Ficha de Auditoría Individual para Cualquier SKU
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
WHERE sku = 'MP-0001'; -- Reemplazar dinámicamente por cualquier SKU
```

---

## 🚦 5. Semáforo y Reglas de Decisión para el Agente IA

| Estado ERI | Condición Lógica | Acción Inmediata del Agente IA |
|---|---|---|
| **🟢 `Cuadrado (Exacto)`** | $\Delta_i = 0$ | Operación regular. El stock del Kardex es confiable para planificar compras y MRP. |
| **🔴 `Descuadrado - Faltante Fisico`** | $\Delta_i < 0$ | **ADVERTENCIA OBLIGATORIA:** Hay menos material físico en piso del que dice el sistema. Si se evalúa compra, usar el Conteo Físico como stock base para evitar desabastecimiento. |
| **🟡 `Descuadrado - Sobrante Fisico`** | $\Delta_i > 0$ | **ALERTA DE SOBRESTOCK:** Hay más material físico del registrado. Bloquear compras inmediatas hasta realizar ajuste contable de entrada para no sobrecomprar. |

### 🚫 Reglas Innegociables para el LLM:
1. **Advertencia de Incertidumbre en Órdenes de Compra:** Cuando se sugiera una orden de compra para un SKU con estado `Descuadrado`, el LLM **DEBE incluir**:
   > ⚠️ *Advertencia ERI: El SKU presenta discrepancia entre Kardex ($K$) y Piso ($F$). Se requiere validar físicamente el lote en bodega antes de radicar la orden.*
2. **Cero Compras Basadas en Negativos Fantasma:** Si el Kardex muestra saldo negativo por consumos sin ingreso previo, tomar el **Conteo Físico Oficial** como saldo disponible real.

