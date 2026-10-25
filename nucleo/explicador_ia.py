"""
Módulo de Inteligencia Explicativa y Asistencia al Decisor - E2 SAS
Archivo: nucleo/explicador_ia.py

Responsabilidad:
- Aplica la tesis del curso (Slides 43-45):
  "Fórmula para el número; IA para la explicación y justificación ejecutiva."
- Transforma los datos numéricos y alertas de auditoría (ERI, ABC, SLA, EOQ/ROP) en un
  memorando ejecutivo estructurado para el planeador de producción / jefe de compras.
- Cuenta con salvaguardas deterministicas anti-alucinación: los números provienen
  estrictamente de las fórmulas ya auditadas.

Contrato:
- Entrada: propuesta (dict con parámetros de stock, ERI, SLA y criterios de parada)
- Salida: dict con dictamen, color, memo ejecutivo estructurado y acción recomendada
"""

from typing import Any, Dict, List, Optional


def generar_explicacion_ejecutiva(propuesta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera una justificación ejecutiva profunda y balanceada para asistir al decisor humano.
    
    Args:
        propuesta: Diccionario con la propuesta calculada por el orquestador.

    Returns:
        Diccionario con dictamen operativo, memo ejecutivo y recomendaciones.
    """
    sku = propuesta.get("sku", "N/A")
    descripcion = propuesta.get("descripcion", "Material")
    categoria = propuesta.get("categoria", "Insumo")
    clase_abc = propuesta.get("clasificacion_abc", "C")
    cantidad = float(propuesta.get("cantidad_sugerida") or 0.0)
    inversion = float(propuesta.get("inversion_cop") or 0.0)
    unidad = propuesta.get("unidad", "und")

    descuadre_eri = propuesta.get("descuadre_eri", False)
    desalineacion_cop = float(propuesta.get("desalineacion_cop") or 0.0)
    sla_cat_pct = float(propuesta.get("sla_categoria_pct") or 100.0)
    criterios_parada = propuesta.get("criterio_parada", "APROBACION_ESTANDAR")

    # 1. Determinar dictamen y severidad
    if "REQUIERE_VERIFICACION_FISICA" in criterios_parada and "REQUIERE_AUTORIZACION_GERENCIAL" in criterios_parada:
        dictamen = "PAUSA OBLIGATORIA · RIESGO PATRIMONIAL Y FÍSICO"
        color_dictamen = "red"
        icono = "🛑"
        accion = "NO ORDENAR A CIEGAS. Realizar conteo físico en patio y solicitar visto bueno gerencial."
    elif "REQUIERE_VERIFICACION_FISICA" in criterios_parada:
        dictamen = "AUTORIZACIÓN CONDICIONADA A CONTEO DE PISO"
        color_dictamen = "orange"
        icono = "⚠️"
        accion = "Validar conteo físico real antes de autorizar el despacho para evitar comprar stock fantasma."
    elif "REQUIERE_AUTORIZACION_GERENCIAL" in criterios_parada:
        dictamen = "AUTORIZACIÓN GERENCIAL REQUERIDA (ALTO MONTO)"
        color_dictamen = "orange"
        icono = "💼"
        accion = "El SKU es conforme en almacén pero supera el umbral de desembolso ($20M COP). Requiere firma gerencial."
    elif "PROVEEDOR_ALTO_RIESGO_MORA" in criterios_parada:
        dictamen = "APROBACIÓN CON SEGUIMIENTO INTENSIVO A PROVEEDOR"
        color_dictamen = "orange"
        icono = "🚚"
        accion = "Emitir orden con fecha de anticipación extendida; el proveedor presenta mora histórica."
    else:
        dictamen = "APROBACIÓN INMEDIATA RECOMENDADA"
        color_dictamen = "green"
        icono = "✅"
        accion = "Proceder con la emisión rutinaria de la Orden de Compra."

    # 2. Puntos clave de análisis
    puntos_clave = []
    
    # Impacto estratégico
    if clase_abc == "A":
        puntos_clave.append(f"Material Estratégico (Clase A): Concentra alto valor económico. Su agotamiento paraliza líneas de ensamble.")
    elif clase_abc == "B":
        puntos_clave.append(f"Material Intermedio (Clase B): Rotación moderada con impacto controlado en caja.")
    else:
        puntos_clave.append(f"Material Operativo (Clase C): Bajo impacto unitario; priorizar no acumular sobrestock.")

    # Condición de inventario
    puntos_clave.append(f"Propuesta determinística: Pedir {cantidad:,.0f} {unidad} con una inversión estimada de $ {inversion:,.2f} COP.")

    # Auditoría ERI
    if descuadre_eri:
        puntos_clave.append(f"Alerta de Exactitud (ERI): El registro contable presenta discrepancia física con una desalineación de $ {desalineacion_cop:,.2f} COP.")
    else:
        puntos_clave.append(f"Inventario Conforme (ERI): El Kardex teórico y el conteo físico están alineados (0 discrepancia).")

    # Fiabilidad de suministro
    if sla_cat_pct < 20.0:
        puntos_clave.append(f"Riesgo de Suministro: La categoría '{categoria}' tiene un SLA histórico de apenas {sla_cat_pct:.1f}% de cumplimiento a tiempo.")
    else:
        puntos_clave.append(f"Suministro Estable: La categoría '{categoria}' cuenta con un cumplimiento histórico del {sla_cat_pct:.1f}%.")

    # 3. Redacción del Memorando Ejecutivo
    primer_parrafo = (
        f"Se evalúa la emisión de Orden de Compra para el ítem **{sku} ({descripcion})**, clasificado como **Clase {clase_abc}** "
        f"en la categoría **{categoria}**. El modelo de reposición continua $(s, Q)$ indica necesidad de abastecimiento "
        f"por **{cantidad:,.0f} {unidad}** con un desembolso proyectado de **$ {inversion:,.2f} COP** para garantizar un Nivel de Servicio del 95%."
    )

    if descuadre_eri:
        segundo_parrafo = (
            f"**Advertencia Crítica de Control Interno:** El orquestador activó un criterio de parada porque el sistema detectó "
            f"un descuadre patrimonial en almacén valorado en $ {desalineacion_cop:,.2f} COP. Si se ordena sin verificar el piso, "
            f"se corre el riesgo de duplicar compras o asumir un falso faltante. "
        )
    else:
        segundo_parrafo = (
            f"Los registros de bodega se encuentran conformes con el Kardex oficial. "
        )

    if sla_cat_pct < 20.0:
        segundo_parrafo += (
            f"Adicionalmente, el desempeño de entrega de los proveedores de {categoria} es deficitario ({sla_cat_pct:.1f}% OTD), "
            f"por lo que se sugiere coordinar seguimiento inmediato desde la colocación de la orden."
        )

    memo_ejecutivo = f"{primer_parrafo}\n\n{segundo_parrafo}"

    return {
        "sku": sku,
        "dictamen": f"{icono} {dictamen}",
        "color": color_dictamen,
        "memo_ejecutivo": memo_ejecutivo,
        "puntos_clave": puntos_clave,
        "accion_recomendada": accion
    }


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    # Prueba unitaria del explicador
    propuesta_test = {
        "sku": "MP-0020",
        "descripcion": "Lámina calibre/ref 1",
        "categoria": "Lámina",
        "clasificacion_abc": "A",
        "cantidad_sugerida": 4970,
        "unidad": "und",
        "costo_unitario": 248445,
        "inversion_cop": 30061845.0,
        "criterio_parada": "REQUIERE_VERIFICACION_FISICA | REQUIERE_AUTORIZACION_GERENCIAL | PROVEEDOR_ALTO_RIESGO_MORA",
        "descuadre_eri": True,
        "desalineacion_cop": 2343830130.0,
        "sla_categoria_pct": 2.8
    }

    res = generar_explicacion_ejecutiva(propuesta_test)
    print("Dictamen:", res["dictamen"])
    print("\nMemo Ejecutivo:\n", res["memo_ejecutivo"])
    print("\nPuntos Clave:")
    for p in res["puntos_clave"]:
        print(" -", p)
    print("\nAcción Recomendada:", res["accion_recomendada"])
