---
name: exactitud-inventarios-eri-e2
description: >-
  Audita la Exactitud en el Registro de Inventario (ERI) y reconciliación
  tridimensional (Kardex teórico vs Conteo Físico Oficial vs Cuaderno del Jefe)
  para E2 SAS. Utilícese para validar la veracidad de los saldos de stock,
  cuantificar la desalineación contable y evitar compras basadas en saldos fantasma.
---

# Motor de Auditoría y Exactitud de Inventario (ERI) — E2 SAS

Este skill estandariza el cálculo del **ERI (Exactitud en el Registro de Inventario)** y la detección de brechas contables y físicas en la bodega de **E2 SAS**.

---

## 📌 Reconciliación Tridimensional de Inventario

Para cada uno de los 420 SKUs válidos, el sistema contrasta 3 fuentes de información independientes:

```
                      RECONCILIACIÓN TRIDIMENSIONAL
                    ┌───────────────────────────────┐
                    │ 1. KARDEX TEÓRICO DEL ERP     │
                    │ Saldo = Inicial + E - S + A   │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
       ┌────────────────────────────┴────────────────────────────┐
       │                                                         │
       ▼                                                         ▼
┌───────────────────────────────┐         ┌───────────────────────────────┐
│ 2. CONTEO FÍSICO OFICIAL      │ ◄─────► │ 3. CUADERNO DEL JEFE          │
│ Auditoría física completa     │         │ Verificación manual paralela  │
└───────────────────────────────┘         └───────────────────────────────┘
```

---

## 📐 Fórmulas Determinísticas de Exactitud

### 1. Kardex Teórico Reconstruido
$$\text{Stock Kardex}_i = \text{Stock Inicial}_i + \sum \text{Entradas}_i - \sum \text{Salidas}_i + \sum \text{Ajustes}_i$$

### 2. Discrepancia Física y Desalineación Monetaria
$$\text{Discrepancia (und)}_i = \text{Stock Físico}_i - \text{Stock Kardex}_i$$
$$\text{Desalineación Contable Bruta (\$ COP)}_i = |\text{Discrepancia}_i| \times \text{Costo Unitario}_i$$

### 3. Exactitud ERI a Nivel SKU (Binaria Estricta)
$$\text{ERI Global (\%)} = \frac{\sum_{i=1}^{N} \mathbb{I}(\text{Stock Kardex}_i = \text{Stock Físico}_i)}{N} \times 100$$

---

## 📊 Línea Base Diagnosticada (Fase E1)

| Segmento de Inventario | Total SKUs | SKUs Exactos | SKUs Descuadrados | ERI Exactitud | Desalineación Contable Bruta |
|---|:---:|:---:|:---:|:---:|:---:|
| **SKUs Activos (En Rotación)** | **119** | **0** | **119** | **`0.00 %`** | **`$ 48.760.853.889 COP`** |
| **SKUs Inactivos (Plata Muerta)** | **301** | **282** | **19** | **`93.69 %`** | **`$ 32.069.616 COP`** |
| **TOTAL GENERAL** | **420** | **282** | **138** | **`67.14 %`** | **`$ 48.792.923.505 COP`** |

> **Nota metodológica para el Agente:** Si un usuario o directivo menciona que el ERI debería rondar el **75%**, explicar que el 75% es la aproximación teórica que se obtiene al asumir que los 301 inactivos están cuadrados ($301/400 = 75.25\%$) o al aplicar una tolerancia física del $\pm 10\%$. Nuestro cálculo del **67.14%** es la exactitud binaria 100% estricta tras descubrir 19 inactivos con mermas físicas no registradas.

---

## 🗄️ Consultas Oficiales en Supabase

### A. Resumen Ejecutivo
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

### B. Detalle de SKUs con Mayor Descuadre Monetario
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

---

## 🚫 Reglas Operativas para el Agente IA

1. **Advertencia de Incertidumbre:** Al recomendar una Orden de Compra para un SKU con $\text{estado\_eri} = \text{'Descuadrado'}$, el Agente **debe incluir** la nota:
   > ⚠️ *Advertencia ERI: El SKU presenta discrepancia entre Kardex ($K$) y Piso ($F$). Se requiere validar físicamente el lote antes de radicar la orden.*
2. **Cero Tolerancia a Negativos Fantasma:** Si el Kardex del ERP muestra saldos negativos debido a consumos sin recepción previa, el Agente debe usar el **Conteo Físico Oficial** como base para el cálculo del stock disponible.
