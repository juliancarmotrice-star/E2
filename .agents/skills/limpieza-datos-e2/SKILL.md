---
name: limpieza-datos-e2
description: >-
  Aplica el protocolo canónico de limpieza, normalización a 3FN e ingesta de datos
  para E2 SAS. Utilícese al procesar nuevos archivos CSV en datos_iniciales, ejecutar
  o modificar python/clean_pipeline.py, auditar integridad referencial y cargar
  datos_limpios en Supabase.
---

# Protocolo de Limpieza, Normalización 3FN e Ingesta de Datos — E2 SAS

Este skill estandariza la **Capa 1 (Ingesta & Gobernanza)** de la arquitectura de E2 SAS. Toda nueva carga de datos (lotes periódicos de ERP, Kardex, Órdenes de Compra, BOM, Conteo Físico y MPS) debe procesarse bajo este protocolo determinístico estricto.

**Regla de Oro:** Queda estrictamente prohibido limpiar datos manualmente en hojas de cálculo o cargar archivos CSV crudos directamente a Supabase.

---

## 🔄 Flujo Canónico de Ingesta

```
    ┌───────────────────────────────┐
    │ 1. ARCHIVOS CSV CRUDOS        │
    │ Copiados a: datos_iniciales/  │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │ 2. PIPELINE DE LIMPIEZA       │
    │ python/clean_pipeline.py      │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │ 3. CSVs LIMPIOS (3FN)         │
    │ Guardados en: datos_limpios/  │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │ 4. CARGA A SUPABASE (POSTGRES)│
    │ python/upload_to_supabase.py  │
    └───────────────────────────────┘
```

---

## 📋 Catálogo de Fuentes de Entrada

| Archivo Crudo | Tabla Destino en Supabase | Reglas Obligatorias de Limpieza |
|---|---|---|
| `maestro_materiales.csv` | `maestro_materiales` | Estandarización a 8 familias (`cat_map`) y unidades (`unit_map`). Imputación de Lead Time por SKU/Proveedor. Eliminación de SKUs duplicados (`MP-9...` / `(dup)`). |
| `movimientos_inventario.csv` | `movimientos_inventarios` | Conversión a valores absolutos `\|cantidad\|` (el sentido lo da `tipo_movimiento`). Corrección de formato de fechas invertidas (`2026-13-05` ➔ `2026-03-05`). |
| `ordenes_compra.csv` | `ordenes_compra` | Corrección de año anómalo (`2035` ➔ año del pedido). **No borrar** OCs con `fecha_recepcion` nula (representan inventario en tránsito para $ROP$). |
| `bom.csv` | `bom` y `maestro_productos` | Generación de clave primaria compuesta `id_bom = producto + '_' + sku_material`. Separación del catálogo de productos terminados en `maestro_productos` (3FN). |
| `plan_produccion.csv` | `plan_produccion` | Desacoplamiento de nombres redundantes y validación de tipos fecha (`periodo` = primer día de mes). |
| `inventario_inicial.csv` | `inventario_inicial` | Tabla madre de anclaje histórico. Se preserva íntegra como punto de partida del Kardex. |
| `conteo_fisico.csv` | `conteo_fisico` | Aplicación de valor absoluto a cantidades negativas por digitación. Deduplicación estricta por `sku`. |
| `Inventario_bodega_JEFE.csv` | `inventario_bodega_JEFE` | Mapeo de columna `codigo` a SKU. Observaciones nulas convertidas a `'Sin observación'`. |

---

## 🛠️ Comandos de Ejecución

1. **Ejecutar Pipeline de Limpieza Completo:**
   ```bash
   python python/clean_pipeline.py
   ```
2. **Cargar Datos Normalizados a Supabase:**
   ```bash
   python python/upload_to_supabase.py
   ```

---

## 🚫 Fronteras del Skill (Qué NO va en este Skill)

* **NO calcular ROP, SS, EOQ:** Es responsabilidad del skill [`reposicion-eoq-rop-e2`](../reposicion-eoq-rop-e2/SKILL.md).
* **NO calcular ERI / Desalineación:** Es responsabilidad del skill [`exactitud-inventarios-eri-e2`](../exactitud-inventarios-eri-e2/SKILL.md).
* **NO calcular segmentación ABC-XYZ:** Es responsabilidad del skill [`analitica-abc-xyz-e2`](../analitica-abc-xyz-e2/SKILL.md).
* **NO auditar SLA de proveedores:** Es responsabilidad del skill [`sla-proveedores-mrp-e2`](../sla-proveedores-mrp-e2/SKILL.md).

Los motores analíticos consumen la base de datos **después** de que este ciclo de limpieza ha finalizado exitosamente.
