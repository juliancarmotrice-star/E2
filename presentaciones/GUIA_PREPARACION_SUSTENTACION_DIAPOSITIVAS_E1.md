# 📚 Guía de Sustentación con Cálculos y Operaciones Desglosadas
## Desglose Paso a Paso: De Dónde Sale Cada Número y Cómo Explicarlo Claramente — Fase E1

> **Empresa:** E2 SAS — Mobiliario Metálico para Oficina  
> **Proyecto:** Optimización de la Gestión de Inventarios y Abastecimiento  
> **Asignatura:** Producción 4.0 / Énfasis 2 — Universidad de Medellín  
> **Fase:** E1 (Diagnóstico Operacional y Línea Base de Costos)  
> **Presentación Oficial:** `Sustentacion_Junta_Directiva_E2SAS_E1.pptx` (15 Diapositivas)  
> **PDF Oficial de Estudio:** [`GUIA_PREPARACION_SUSTENTACION_DIAPOSITIVAS_E1.pdf`](GUIA_PREPARACION_SUSTENTACION_DIAPOSITIVAS_E1.pdf) (16 Páginas)  
> **Tono y Enfoque:** Formal, respetuoso, claro y natural (sin tecnicismos enredados).

---

## 📊 Matriz Resumen de Cálculos y Resultados Clave

| Métrica / Cifra Oficial | Origen de los Datos | Cálculo Paso a Paso (Operación Exacta) | Resultado Final |
|---|---|---|:---:|
| **1. Tiempo Real de Entrega (Lámina)** | `ordenes_compra`: 107 compras cerradas de los 40 tipos de lámina. | **Suma de días:** 2.223 días en total.<br/>**Promedio:** 2.223 días / 107 órdenes = **20,78 días**. | **20.8 días** (Mediana: 19d) |
| **2. Retraso frente al Sistema (ERP)** | `maestro_materiales`: El sistema tiene configurados 12,11 días en promedio. | **Diferencia:** 20,78 días reales - 12,11 días en sistema = **+8,66 días tarde**.<br/>**Porcentaje:** (8,66 / 12,11) * 100 = **+71,52% más demorado**. | **+8.66 días (+71.5%)** de retraso |
| **3. Pedidos de Lámina a Tiempo (OTIF)** | `ordenes_compra`: Comparar fecha de entrega con fecha prometida. | **Conteo:** Solo 3 órdenes llegaron a tiempo, 104 llegaron tarde.<br/>**Porcentaje:** (3 a tiempo / 107 totales) * 100 = **2,80%** (97,20% tarde). | **2.80% a tiempo** (104 tarde) |
| **4. Riesgo de Parada de Planta** | 104 compras con retraso + Costo de parada: $450.000 COP/hora. | **1. Días de mora sumados:** 1.056 días.<br/>**2. Horas de turno:** 1.056 días * 8 horas/día = **8.448 horas**.<br/>**3. En dinero:** 8.448 horas * $450.000/hora = **$3.801.600.000 COP**. | **$3.801.600.000 COP** en riesgo |
| **5. Materiales sin Uso (Plata Muerta)** | Comparar 420 materiales iniciales con los 16.195 movimientos. | **Conteo:** 119 materiales sí se usaron, 301 materiales tuvieron CERO salidas.<br/>**Porcentaje:** (301 sin uso / 420 catálogo) * 100 = **71,67%**. | **71.67% del catálogo** (301 referencias) |
| **6. Dinero Atrapado en Plata Muerta** | Sumar el valor de las 301 referencias que no tuvieron ninguna salida. | **Plata quieta:** **$3.550.022.309 COP**.<br/>**Inventario inicial total:** **$6.574.960.449 COP**.<br/>**Porcentaje del dinero:** ($3.550M / $6.574M) * 100 = **53,99%**. | **$3.550.022.309 COP** (54% del total) |
| **7. Costo de Mantener esa Plata Quieta** | Dinero inmovilizado ($3.550M) * Tasa del 25% anual (almacenaje, capital, seguros). | **Por año:** $3.550.022.309 * 0,25 = **$887.505.577 COP/año**.<br/>**En los 21 meses:** $887.5M * 1,75 años = **$1.553.134.760 COP**. | **$887.505.577 COP/año** ($1.553M en 21m) |
| **8. Rotación Anual (ITR) y Cobertura (DSI)** | Consumo 21m: $60.851M COP.<br/>Inventario Promedio: $70.160M COP. | **Consumo al año:** ($60.851M / 21) * 12 = **$34.772M COP/año**.<br/>**Rotación:** $34.772M / $70.160M = **0,495 veces/año** (tarda 2 años en rotar).<br/>**Días de stock:** 365 días / 0,4956 = **736,5 días** (24,5 meses). | **ITR: 0.495 rot/año**<br/>**DSI: 736.5 días** |
| **9. Gasto Administrativo en Compras** | 1.471 órdenes de compra emitidas * Costo de gestión: $80.000 COP/orden. | **Multiplicación:** 1.471 órdenes * $80.000 COP = **$117.680.000 COP**. | **$117.680.000 COP** (1.471 órdenes) |
| **10. Ventas Perdidas y Margen PT (30%)** | 753 muebles que no se alcanzaron a fabricar * 30% de margen de ganancia. | **Ganancia perdida:** Cada mueble no entregado dejó de aportar el **30% de su precio de venta** a la empresa.<br/>**En Fase E2:** Es el costo de faltante $c_u$ para calibrar el stock de seguridad. | **30.0% Margen PT** (Ganancia perdida) |

---

## 🖥️ Guía de Exposición Diapositiva por Diapositiva (1 a 15)

---

### 🔹 DIAPOSITIVA 1 / 15 | APERTURA DE LA PRESENTACIÓN
## Portada: Diagnóstico Operacional — Fase E1

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Título del proyecto, empresa cliente E2 SAS (Mobiliario Metálico), 21 meses de operación auditados (julio 2024 - marzo 2026), estado: Línea Base certificada, Universidad de Medellín. |
| **🎯 Qué buscamos transmitir** | Presentar formalmente el proyecto y el equipo, dejando claro que se trata de un diagnóstico basado en datos reales de la empresa. |

#### 🗣️ Guion Verbal Sugerido (Cómo explicarlo en voz alta):
> *«Buenos días, profesores y miembros de la Junta Directiva. Hoy les presentamos el Diagnóstico Operacional y la Línea Base de la Fase E1 para E2 SAS. Nuestro objetivo fue analizar 21 meses de operación real para entender por qué se están presentando problemas de desabastecimiento en planta y exceso de materiales en bodega, y calcular con números claros cuánto le cuesta esta situación a la empresa.»*

#### 🔬 Cálculo Paso a Paso y Origen de los Números:
1. **Tiempo total analizado:**
   * Fecha de inicio en `inventario_inicial`: 01 de julio de 2024.
   * Fecha de corte en `conteo_fisico`: 31 de marzo de 2026.
   * Cálculo de meses: 6 meses de 2024 + 12 meses de 2025 + 3 meses de 2026 = **21 meses continuos** (exactamente 638 días calendario = 1,75 años).
2. **Datos evaluados:** 440 materiales en catálogo, 420 materiales con inventario inicial, 18 modelos de muebles, 131 recetas de ensamble (BOM), 16.195 movimientos de inventario y 1.471 órdenes de compra.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Por qué analizaron 21 meses y no un año completo?
* **Respuesta:** *«Porque al tomar casi dos años podemos ver tanto los meses de alta demanda (como enero y julio) como los meses más suaves, asegurándonos de que los problemas encontrados son continuos y no una casualidad.»*

---

### 🔹 DIAPOSITIVA 2 / 15 | ESTRUCTURA DE LA EXPOSICIÓN
## Agenda: Qué vamos a demostrar hoy

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | 6 bloques de la presentación: 01 Respuesta a las quejas, 02 Limpieza de datos, 03 Queja 1 (Lámina), 04 Queja 2 (Plata muerta), 05 Tablero de costos actuales, 06 Plan de mejora para la Fase E2. |
| **🎯 Qué buscamos transmitir** | Mostrar el orden de la exposición para que el jurado entienda la lógica: problema -> datos limpios -> causas encontradas -> impacto económico -> solución. |

#### 🗣️ Guion Verbal Sugerido:
> *«La presentación está organizada en seis partes: primero, les daremos la respuesta directa a las dos quejas de la gerencia; segundo, cómo corregimos los errores en los datos; tercero y cuarto, qué encontramos en la lámina y en la plata muerta; quinto, el tablero de costos actual; y finalmente, las soluciones que aplicaremos en la Fase E2.»*

#### 🔬 Organización del Trabajo:
* **Partes 1 a 4:** Diagnóstico actual (cálculo de tiempos de entrega reales, cumplimiento de proveedores, quiebres de inventario y materiales sin uso).
* **Parte 5:** Tablero de costos (cuánto dinero cuesta cada problema usando las tarifas de la empresa).
* **Parte 6:** Plan de solución (fórmulas de compras y stock de seguridad para corregir la operación).

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Cuánto tiempo tomará la presentación?
* **Respuesta:** *«Está planeada para unos 10 a 12 minutos de exposición, dejando el resto del tiempo disponible para preguntas.»*

---

### 🔹 DIAPOSITIVA 3 / 15 | CONCLUSIONES PRINCIPALES
## Resumen Ejecutivo: Las Dos Quejas son Reales y se Comprueban

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Dos tarjetas de resumen. Queja 1: Confirmada (la lámina tarda 20.8 días vs 12.1 del sistema, 2.8% a tiempo, $3.801 millones en riesgo de parada). Queja 2: Confirmada (71.7% de materiales sin uso, $3.550 millones quietos, $887.5 millones al año en costos de mantenerlos). |
| **🎯 Qué buscamos transmitir** | Dar la conclusión principal desde el primer minuto: ambas quejas de la gerencia son completamente ciertas y están demostradas con números. |

#### 🗣️ Guion Verbal Sugerido:
> *«Para responder directamente la duda de la gerencia: las dos quejas son totalmente ciertas. En la primera queja, la lámina se agota porque el proveedor se demora casi 21 días en entregar y el sistema asume que tarda 12, cumpliendo a tiempo solo el 2.8% de las veces. Esto pone en riesgo más de 3.800 millones de pesos en paradas de planta. Y en la segunda queja, 7 de cada 10 materiales no se movieron ni una sola vez en 21 meses, lo que tiene atrapados 3.550 millones de pesos que le cuestan a la empresa 887 millones de pesos al año solo por tenerlos guardados.»*

#### 🔬 Cálculo de las 4 Cifras Principales:
1. **Tiempo real de lámina:** 2.223 días sumados / 107 compras = **20,78 días** vs **12,11 días** en sistema (+71,5%).
2. **Cumplimiento de lámina:** 3 órdenes a tiempo / 107 órdenes totales = **2,80%**.
3. **Riesgo de paradas:** 1.056 días de atraso * 8 h/d = 8.448 h * $450.000/h = **$3.801.600.000 COP**.
4. **Plata muerta:** 301 materiales sin salida / 420 catálogo = **71,67%** ($3.550.022.309 COP). Costo al año (25%) = $3.550M * 0,25 = **$887.505.577 COP/año**.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Por qué están tan seguros de que las dos quejas son ciertas?
* **Respuesta:** *«Porque cruzamos las órdenes de compra con los movimientos de bodega y los datos reflejan exactamente los mismos retrasos y estancamientos que la gerencia percibía en el día a día.»*

---

### 🔹 DIAPOSITIVA 4 / 15 | CONTEXTO DEL PROBLEMA
## Contexto del Encargo: Crisis de Doble Vía

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Perfil de E2 SAS (fabricante de muebles metálicos de oficina). El problema doble: desabastecimiento de lámina y exceso de materiales quietos. Flujo de trabajo en 5 pasos y los 4 costos dados por la empresa. |
| **🎯 Qué buscamos transmitir** | Explicar la paradoja de cómo una empresa puede tener la bodega llena pero al mismo tiempo quedarse sin material para fabricar los productos más vendidos. |

#### 🗣️ Guion Verbal Sugerido:
> *«E2 SAS fabrica muebles metálicos de oficina como archivadores, escritorios y estanterías. La empresa vive una situación contradictoria: por un lado, la fábrica se queda sin lámina y tiene que frenar la producción; pero por el otro, la bodega está llena de materiales que nadie usa. Para evaluar esto formalmente, la empresa nos entregó cuatro costos oficiales: 450.000 pesos por hora de planta parada, 25% anual por mantener inventario, 80.000 pesos por gestionar cada orden de compra y un 30% de margen de ganancia en los muebles terminados.»*

#### 🔬 Los 4 Parámetros Económicos Oficiales de la Empresa:
* **1. Parada de Planta:** $450.000 COP / hora (costos fijos de planta + mano de obra que queda quieta).
* **2. Margen de Ganancia en Muebles (PT):** **30,0%** (lo que deja de ganar la empresa por cada mueble no vendido).
* **3. Costo de Mantener Inventario (H):** **25,0% anual** (15% costo del dinero + 5% bodegaje + 3% seguros + 2% deterioro).
* **4. Costo de Emitir Orden de Compra (S):** **$80.000 COP / orden** (tiempo administrativo de comprar y recibir).

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Por qué se presentan estos dos problemas opuestos al mismo tiempo?
* **Respuesta:** *«Porque las compras no se hacían mirando el consumo real ni el tiempo que tarda el proveedor, sino pidiendo por intuición y comprando lotes grandes de cosas que casi no rotan.»*

---

### 🔹 DIAPOSITIVA 5 / 15 | CALIDAD Y LIMPIEZA DE DATOS
## Sección 2 · Auditoría de Datos: Limpieza Sin Borrar Información

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Tabla con los 8 archivos, errores encontrados (fechas con mes 13, año 2035, cantidades negativas, tiempos de entrega vacíos) y cómo se corrigieron. Conclusión: 440 materiales limpios y 16.195 movimientos válidos. Cero datos borrados. |
| **🎯 Qué buscamos transmitir** | Demostrar que los datos se limpiaron con cuidado técnico, corrigiendo errores evidentes de digitación sin borrar información valiosa. |

#### 🗣️ Guion Verbal Sugerido:
> *«Antes de hacer cualquier cálculo, revisamos los 8 archivos de datos y encontramos varios errores de digitación: 15 fechas que tenían el día y el mes al revés mostrando un 'mes 13', 22 órdenes que figuraban recibidas en el año 2035, cantidades con signo negativo y 54 materiales sin tiempo de entrega. Corregimos cada error con reglas claras: invertimos las fechas trocadas, recalculamos los tiempos vacíos usando las compras anteriores y mantuvimos las órdenes abiertas como pedidos en camino. No eliminamos ningún registro a ciegas.»*

#### 🔬 Cómo se corrigieron los errores principales:
* **Mes 13:** 15 fechas como `2026-13-05` se corrigieron invirtiendo dígitos a `2026-05-13` (13 de mayo de 2026).
* **Año 2035:** 22 fechas de entrega con año equivocado se pasaron al año real de la compra (2024/2025).
* **Cantidades Negativas:** 466 movimientos en negativo se convirtieron a positivo.
* **Tiempos vacíos:** 52 materiales se calcularon con el promedio de sus compras pasadas, y 2 con el promedio de su proveedor.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Por qué no borraron las órdenes que no tenían fecha de entrega?
* **Respuesta:** *«Porque eran 74 órdenes que todavía estaban abiertas y en camino. Si las borrábamos, perdíamos de vista el material que venía en tránsito hacia la bodega.»*

---

### 🔹 DIAPOSITIVA 6 / 15 | ESTRUCTURA DE LA BASE DE DATOS
## Sección 3 · Arquitectura de Datos: Base de Datos Ordenada en PostgreSQL

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Diagrama de tablas conectadas alrededor de maestro_productos (18 muebles) y maestro_materiales (440 insumos), conectando recetas (BOM), planes, movimientos y compras. Uso de la libreta del jefe como registro auxiliar. |
| **🎯 Qué buscamos transmitir** | Demostrar que los datos quedaron organizados en una base de datos relacional sólida, sin datos repetidos y con claves que evitan errores. |

#### 🗣️ Guion Verbal Sugerido:
> *«Toda la información limpia la organizamos en una base de datos en PostgreSQL. Creamos una tabla especial para los 18 muebles terminados para no repetir sus nombres cientos de veces, conectamos cada material con sus recetas de fabricación mediante una clave única y nos aseguramos de que no existieran compras ni movimientos de materiales que no estuvieran registrados en el catálogo. La libreta de notas del jefe de bodega se usó como una guía de campo para comprobar las diferencias con el sistema.»*

#### 🔬 Cómo se estructuró la base de datos:
* **Sin datos repetidos:** Se crearon 18 productos únicos en `maestro_productos` para no repetir texto en 378 filas de producción.
* **Clave única en recetas:** Se unió el mueble con el material (`id_bom = producto + material`) en las 131 recetas.
* **Protección contra errores:** Claves foráneas para que ninguna compra o movimiento apunte a un material inexistente.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Para qué sirvió la libreta del jefe de bodega?
* **Respuesta:** *«Nos sirvió para ver qué pasaba en el piso de la bodega y confirmar que los trabajadores anotaban a mano porque el sistema no coincidía con la realidad física.»*

---

### 🔹 DIAPOSITIVA 7 / 15 | INVESTIGACIÓN DE LA QUEJA 1
## Sección 4.1 · Queja 1: Desfase en Tiempos de Entrega (12 vs 21 días)

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Tres métricas: +71.5% de retraso (el sistema dice 12.1 días, el proveedor tarda 20.8 días). 3 proveedores concentran el 36.4% de compras de lámina con 0% a tiempo. Correlación del 94.5% entre lámina y producción. |
| **🎯 Qué buscamos transmitir** | Demostrar que la culpa no es del personal de planta, sino de que el sistema de compras pide los pedidos con un tiempo irreal. |

#### 🗣️ Guion Verbal Sugerido:
> *«Al analizar la Queja 1, encontramos el motivo exacto por el que se acaba la lámina: el sistema asume que los proveedores tardan 12 días en entregar, pero en la realidad se demoran casi 21 días. Hay un desfase de casi 9 días de retraso, un 71.5% más de lo planeado. Además, los tres proveedores a los que más lámina se les compra jamás entregaron un pedido a tiempo. Y como la lámina se necesita en casi todos los muebles, cada retraso frena directamente el ensamble.»*

#### 🔬 Cálculo del retraso paso a paso:
1. **Tiempo en el sistema:** Promedio de los 40 tipos de lámina = 484,5 días / 40 = **12,11 días** (mediana: 12 días).
2. **Tiempo real del proveedor:** Suma de días en 107 compras cerradas = 2.223 días / 107 = **20,78 días** (mediana: 19 días).
3. **Diferencia de días:** $20,78 - 12,11 = \mathbf{+8,66\text{ días de retraso}}$.
4. **Porcentaje de retraso:** $(8,66 / 12,11) * 100 = \mathbf{+71,52\% \text{ más demorado}}$.
5. **Concentración en 3 proveedores:** `PROV-08` (15) + `PROV-29` (13) + `PROV-07` (11) = 39 compras de 107 (**36,45%**), los tres con 0% a tiempo.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Por qué compras no se había dado cuenta de este retraso?
* **Respuesta:** *«Porque el sistema no actualiza los tiempos de entrega automáticamente según las facturas de recepción, y nadie había hecho el seguimiento formal a los proveedores.»*

---

### 🔹 DIAPOSITIVA 8 / 15 | IMPACTO OPERATIVO DE LA QUEJA 1
## Sección 4.1 · Queja 1: Impacto en Producción (97.2% Tarde y 753 Muebles Sin Fabricar)

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | 1.167 quiebres de inventario, 9.8 días de mora promedio por pedido, caídas del plan en 19 de 21 meses, 753 muebles sin fabricar (lucro cesante: 30% margen de ganancia). |
| **🎯 Qué buscamos transmitir** | Mostrar las consecuencias reales del retraso: la fábrica no pudo cumplir sus metas de entrega a clientes. |

#### 🗣️ Guion Verbal Sugerido:
> *«Ese retraso en los pedidos afectó gravemente a la fábrica. De 107 compras de lámina, 104 llegaron tarde; es decir, el 97.2% de los pedidos estuvieron en mora, con un promedio de casi 10 días de atraso. Esto ocasionó más de 1.100 momentos de desabastecimiento en bodega y provocó que en 19 de los 21 meses la fábrica no cumpliera su plan de producción, dejando de fabricar 753 muebles. Cada mueble que no se fabricó ni se vendió significó perder directamente el 30% de ganancia que le dejaba a la empresa.»*

#### 🔬 Cálculo del impacto en la fábrica:
1. **Cumplimiento a tiempo:** 3 compras a tiempo de 107 = **2,80%**.
2. **Compras con retraso:** $107 - 3 = 104\text{ compras tarde} = \mathbf{97,20\%}$.
3. **Días de retraso promedio:** 1.056 días de mora sumados / 107 compras = **9,80 días** (o 10,15 días sobre las retrasadas).
4. **Muebles dejados de hacer:** Suma de las caídas de plan en los 19 meses = **753 muebles terminados**.
5. **Ganancia perdida (30% Margen):** 753 muebles * Precio de venta * **30% de margen** que la empresa dejó de recibir.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Cómo sabemos que los 753 muebles faltaron por culpa de la lámina?
* **Respuesta:** *«Porque revisamos los meses con caídas de producción y en más del 90% de ellos la lámina que requerían esos muebles estaba agotada o en saldo negativo en bodega.»*

---

### 🔹 DIAPOSITIVA 9 / 15 | COSTO FINANCIERO DE LA QUEJA 1
## Sección 5.3 · Queja 1: Riesgo Económico por Paradas ($3.801 Millones COP)

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Cifra: $3.801.600.000 COP en riesgo. Cálculo: 1.056 días de retraso * 8 horas/día * $450.000 COP/hora = 8.448 horas en riesgo. Impacto dual: costo de planta ($450k/h) + ventas perdidas (30% margen). |
| **🎯 Qué buscamos transmitir** | Ponerle cifra en pesos a la ineficiencia de la lámina usando la tarifa oficial de la empresa. |

#### 🗣️ Guion Verbal Sugerido:
> *«Usando el costo oficial de 450.000 pesos por hora de planta parada que nos dio la empresa, calculamos el riesgo: los 1.056 días de retraso en lámina equivalen a 8.448 horas de trabajo expuestas a detenerse, lo que da un riesgo total de 3.801 millones de pesos. Aunque el equipo de planta logró amortiguar parte del impacto trabajando horas extra y reprogramando turnos, el sobrecosto y las 753 ventas perdidas representaron un daño económico muy fuerte.»*

#### 🔬 Cálculo del dinero en riesgo paso a paso:
1. **Suma de días de retraso en lámina:** **1.056 días** de mora acumulados.
2. **Horas de trabajo expuestas:** $1.056\text{ días} \times 8\text{ horas de turno diario} = \mathbf{8.448\text{ horas}}$.
3. **Valoración en pesos:** $8.448\text{ horas} \times \$450.000\text{ COP/hora} = \mathbf{\$3.801.600.000\text{ COP}}$.
4. **Impacto financiero dual:** Los $3.801M miden el costo de la planta quieta, mientras el 30% de margen mide las ventas que no se pudieron facturar.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Por qué usaron 8 horas y no 24 horas al día?
* **Respuesta:** *«Porque la planta trabaja en una jornada ordinaria de un turno de 8 horas diarias, lo que nos da un cálculo realista y prudente.»*

---

### 🔹 DIAPOSITIVA 10 / 15 | INVESTIGACIÓN DE LA QUEJA 2
## Sección 4.2 · Queja 2: Plata Muerta (7 de Cada 10 Materiales Sin Uso)

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | 119 materiales activos vs 301 materiales quietos (123.396 unidades sin tocar, mismo saldo en 2024 que en 2026). Curva ABC: 30 materiales mueven el 80% del consumo, mientras 360 materiales ocupan espacio sin rotar. |
| **🎯 Qué buscamos transmitir** | Demostrar que la mayor parte del inventario está estancado y no aporta nada a la producción. |

#### 🗣️ Guion Verbal Sugerido:
> *«Al revisar la Queja 2, encontramos una situación muy delicada: 301 de los 420 materiales —es decir, el 71.7% de todo el catálogo— no tuvieron ni una sola salida para producción en los 21 meses. Hay más de 123.000 unidades en bodega que están exactamente igual que hace dos años. Al hacer el análisis ABC, vimos que solo 30 materiales mueven el 80% de lo que consume la fábrica, mientras cientos de referencias de poco uso llenan los pasillos y atrapan el dinero.»*

#### 🔬 Cálculo de la plata muerta paso a paso:
1. **Materiales con movimiento:** 119 referencias con al menos una salida = **28,33%**.
2. **Materiales quietos:** $420\text{ catálogo} - 119\text{ activos} = \mathbf{301\text{ referencias (71,67\%)}}$ con CERO salidas.
3. **Unidades físicas estancadas:** Suma del inventario de los 301 materiales = **123.396 unidades** (saldo idéntico en 2024 y 2026).
4. **Concentración del consumo:** 30 materiales mueven $48.778M de los $60.851M consumidos = **80,16% del consumo total**.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Por qué se compraron tantos materiales que no se usan?
* **Respuesta:** *«Por comprar cantidades mínimas grandes para buscar rebajas de precio y por crear referencias nuevas para cada pedido especial sin reutilizar las existentes.»*

---

### 🔹 DIAPOSITIVA 11 / 15 | DISTRIBUCIÓN DE LA PLATA MUERTA
## Sección 4.2 · Queja 2: $3.550 Millones Atrapados en las 8 Familias

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | $3.550.022.309 COP repartidos en las 8 familias: Adhesivos ($675M), Tubería ($596M), Empaque ($451M), Correderas ($448M), Pintura ($408M), Tornillería ($364M), Lámina ($311M), Vidrio ($293M). Total = 54% del inventario inicial. |
| **🎯 Qué buscamos transmitir** | Mostrar que la plata muerta no es un error de una sola compra, sino un problema general en todos los tipos de materiales. |

#### 🗣️ Guion Verbal Sugerido:
> *«El dinero atrapado en estos materiales sin uso suma 3.550 millones de pesos, que es más de la mitad de todo el inventario inicial de la empresa. Como pueden ver, el dinero estancado está repartido en las 8 familias: tenemos más de 670 millones en pegantes y adhesivos, casi 600 millones en tuberías, y más de 400 millones en empaques, correderas y pinturas. Esto confirma que el problema no fue de una compra puntual, sino de una falta general de control en los pedidos.»*

#### 🔬 Cálculo del dinero atrapado:
1. **Valor total del inventario inicial:** $6.574.960.449 COP.
2. **Valor de los 301 materiales quietos:** $3.550.022.309 COP.
3. **Porcentaje de capital atrapado:** $(\$3.550M / \$6.574M) * 100 = \mathbf{53,99\%}$.
4. **Suma por familias:** Adhesivos ($675M) + Tubería ($596M) + Empaque ($451M) + Correderas ($448M) + Pintura ($408M) + Tornillería ($364M) + Lámina ($311M) + Vidrio ($293M) = **$3.550.022.309 COP**.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Hay riesgo de que esos materiales se dañen?
* **Respuesta:** *«Sí, especialmente los adhesivos y las pinturas, que tienen fecha de vencimiento y probablemente gran parte de esos 1.080 millones combinados ya no sirvan para producción.»*

---

### 🔹 DIAPOSITIVA 12 / 15 | COSTO DE MANTENER LA PLATA MUERTA
## Sección 5.3 · Queja 2: Drenaje de Dinero ($887.5 Millones al Año)

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Rotación: 0.49 veces al año (tarda 2 años en dar una vuelta). Cobertura: 736.5 días = 24.5 meses de stock. Costo de mantenerlo: $887.505.577 COP/año (25% anual). Total drenado en 21 meses = $1.553 millones. Gasto en órdenes = $117.6 millones. |
| **🎯 Qué buscamos transmitir** | Explicar de forma sencilla que tener materiales guardados cuesta dinero todos los días en bodegaje, seguros y capital desaprovechado. |

#### 🗣️ Guion Verbal Sugerido:
> *«Tener 3.550 millones de pesos guardados en bodega le cuesta mucho dinero a la empresa. Aplicando la tasa oficial del 25% anual —que incluye el costo del dinero, arriendo de bodegas, seguros y deterioro—, la empresa está perdiendo 887 millones de pesos al año, acumulando más de 1.550 millones de pérdidas en los 21 meses evaluados. Además, nuestro inventario rota apenas media vez al año: tenemos material acumulado para trabajar dos años seguidos sin comprar nada, cuando lo normal en la industria son dos meses.»*

#### 🔬 Cálculo de los costos de mantener inventario:
1. **Costo al año (25%):** $\$3.550.022.309 \times 0,25 = \mathbf{\$887.505.577\text{ COP/año}}$.
2. **Pérdida en 21 meses (1,75 años):** $\$887.505.577 \times 1,75 = \mathbf{\$1.553.134.760\text{ COP}}$.
3. **Consumo del año:** $(\$60.851M / 21) * 12 = \mathbf{\$34.772.195.287\text{ COP/año}}$.
4. **Rotación anual:** $\$34.772M / \$70.160M\text{ (inventario promedio)} = \mathbf{0,4956\text{ veces/año}}$.
5. **Días de inventario:** $365\text{ días} / 0,4956 = \mathbf{736,48\text{ días}}\text{ (24,55 meses de stock)}$.
6. **Gasto en órdenes:** $1.471\text{ órdenes} \times \$80.000 = \mathbf{\$117.680.000\text{ COP}}$.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Qué compone esa tasa del 25% anual?
* **Respuesta:** *«El 15% del costo de oportunidad del dinero en el banco, el 5% de bodegaje y espacio, el 3% de seguros y manejo, y el 2% de mermas y vencimiento.»*

---

### 🔹 DIAPOSITIVA 13 / 15 | TABLERO DE INDICADORES ACTUALES
## Sección 5 · Scorecard Maestro: Cómo Estamos vs. A Dónde Queremos Llegar

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Tabla de indicadores: Entregas a tiempo de lámina (2.8% vs 95%), Desfase de tiempos (+8.7 días vs 0), Cumplimiento del plan (90.5% vs 99.5%), Rotación (0.5 vs 6 veces/año), Días de stock (736 vs 60 días), Plata muerta (54% vs 5%). |
| **🎯 Qué buscamos transmitir** | Dejar clara la foto de la empresa hoy para medir los resultados de las mejoras en las siguientes fases. |

#### 🗣️ Guion Verbal Sugerido:
> *«Este tablero resume la situación actual de E2 SAS frente a las metas que debemos alcanzar. Hoy las entregas de lámina a tiempo son de solo el 2.8% y la meta es superar el 95%; el inventario tarda 736 días en salir y debemos bajarlo a 60 días; y la plata muerta representa el 54% del inventario cuando no debería pasar del 5%. Con estos números mediremos el éxito de las soluciones que implementaremos en la Fase E2.»*

#### 🔬 Brechas a cerrar en la operación:
* **Entregas a tiempo:** $2,80\% - 95,00\% = \mathbf{-92,20\text{ puntos de déficit}}$.
* **Tiempos de entrega:** $20,78\text{ días} - 12,11\text{ días} = \mathbf{+8,66\text{ días de retraso}}$ ($+71,5\%$).
* **Rotación de inventario:** $0,4956\text{ actual vs } 6,00\text{ meta} = \mathbf{-91,74\% \text{ de lentitud}}$.
* **Días de stock:** $736,5\text{ días} - 60,0\text{ días} = \mathbf{+676,5\text{ días de sobre-stock}}$.
* **Plata muerta:** $53,99\% - 5,00\% = \mathbf{+48,99\text{ puntos de dinero inmovilizado}}$.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Es posible alcanzar una rotación de 6 veces al año?
* **Respuesta:** *«Sí, al ordenar las compras con lotes económicos y salir de los materiales que no rotan, el inventario promedio baja y la rotación sube a los niveles sanos del sector.»*

---

### 🔹 DIAPOSITIVA 14 / 15 | SOLUCIONES PROPUESTAS
## Sección 6 · Fase E2: Plan de Acción para Solucionar los Problemas

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Dos columnas de soluciones. Para la lámina: 1. Ajustar el tiempo a 21 días en el sistema, 2. Calcular puntos de reorden automáticos, 3. Fijar stock de seguridad balanceando el 30% de margen con el 25% de almacenaje, 4. Acuerdos con proveedores. Para la plata muerta: 1. Recuperar dinero devolviendo o rematando material, 2. Reducir el catálogo a 120 referencias, 3. Comprar materiales A con lotes óptimos y materiales C solo bajo pedido. |
| **🎯 Qué buscamos transmitir** | Demostrar que el equipo tiene listas las soluciones técnicas y operativas para arreglar los problemas en la siguiente fase. |

#### 🗣️ Guion Verbal Sugerido:
> *«Para la Fase E2 tenemos un plan de solución muy claro: para la lámina, vamos a actualizar el sistema para que pida con los 21 días reales, calcularemos un punto de reorden con un colchón de seguridad de 550 a 700 láminas en temporada alta y fijaremos acuerdos con los proveedores para que cumplan. Y para la plata muerta, devolveremos y remataremos los materiales quietos para recuperar entre 1.500 y 2.000 millones de pesos en efectivo, reduciremos el catálogo a 120 referencias estándar y los materiales de poco uso solo se comprarán cuando el cliente confirme el pedido.»*

#### 🔬 Soluciones y Fórmulas para la Fase E2:
1. **Nivel de servicio óptimo ($CSL^*$):** $CSL^* = \frac{c_u}{c_u + c_o}$, donde $c_u = \mathbf{30\% \text{ Margen PT}}$ y $c_o = \text{Costo Posesión } H \text{ (25\% anual)}$.
2. **Punto de Reorden:** $ROP = (\text{Consumo diario} \times \text{21 días de entrega}) + \text{Colchón de seguridad (SS)}$.
3. **Colchón de seguridad:** Cubre tanto la variación de ventas como los retrasos de entrega (sube de 100 a **550-700 láminas** en meses pico).
4. **Lote Económico ($EOQ$):** Cantidad exacta a pedir para balancear el costo de pedir ($80.000) con el de almacenar (25%).

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Se necesita software costoso o inteligencia artificial para esto?
* **Respuesta:** *«No para las reglas básicas; el punto de reorden, el lote económico y la reducción de catálogo son fórmulas directas de ingeniería que se programan directamente en la base de datos sin costos adicionales.»*

---

### 🔹 DIAPOSITIVA 15 / 15 | CIERRE DE LA PRESENTACIÓN
## En Síntesis: Conclusiones Claras con Cifras

| Dimensión | Detalle Explicativo |
|---|---|
| **📺 Qué muestra la diapositiva** | Resumen: Datos limpios, base de datos en PostgreSQL y costos claros. Tres cifras: $3.801 millones en riesgo (lámina), $3.550 millones inmovilizados (plata muerta), $887.5 millones/año de costo continuo. Agradecimiento y apertura a preguntas. |
| **🎯 Qué buscamos transmitir** | Cerrar con mucha seguridad, recordando el valor del diagnóstico y dando paso a las preguntas de la Junta. |

#### 🗣️ Guion Verbal Sugerido:
> *«Para concluir: entregamos los datos completamente limpios y organizados en PostgreSQL, comprobamos con números que las dos quejas son reales y dejamos calculada la Línea Base: 3.800 millones en riesgo por paradas y 3.550 millones en plata muerta. Con este diagnóstico claro, tenemos la base para implementar las soluciones en la Fase E2 y recuperar la rentabilidad de la empresa. Muchas gracias por su atención y quedamos atentos a sus preguntas.»*

#### 🔬 Cifras Clave de Cierre:
* **Riesgo por lámina:** $1.056\text{ días de atraso} \times 8\text{ h/d} \times \$450.000\text{ COP/h} = \mathbf{\$3.801.600.000\text{ COP}}$.
* **Plata muerta:** Suma de 301 materiales sin uso = $\mathbf{\$3.550.022.309\text{ COP}}$ (54% del inventario).
* **Costo anual de mantenerla:** $\$3.550M \times 0,25 = \mathbf{\$887.505.577\text{ COP/año}}$ ($\$1.553M$ en 21 meses).
* **Meta de mejora:** Recuperar más de **$1.500 millones en efectivo** y evitar las paradas de planta.

#### ❓ Pregunta Clave de la Junta y Cómo Responderla:
* **Pregunta:** ¿Cuál es el paso a seguir ahora?
* **Respuesta:** *«Aprobar el inicio de la Fase E2 para activar los modelos de reposición en la base de datos y comenzar el plan para salir de los materiales que no rotan.»*
