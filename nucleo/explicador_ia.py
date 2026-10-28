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
    Genera un dictamen y justificación ejecutiva profunda, orgánica y estructurada para
    asistir al decisor humano en la gestión de compras y abastecimiento de E2 SAS.
    
    Aplica la tesis del curso:
    'Fórmula para el número; IA para la explicación y justificación ejecutiva.'
    """
    sku = propuesta.get("sku", "N/A")
    descripcion = propuesta.get("descripcion", "Material")
    categoria = propuesta.get("categoria", "Insumo")
    clase_abc = propuesta.get("clasificacion_abc", "C")
    cantidad = float(propuesta.get("cantidad_sugerida") or 0.0)
    inversion = float(propuesta.get("inversion_cop") or 0.0)
    unidad = propuesta.get("unidad", "und")

    stock_kardex = float(propuesta.get("stock_actual_kardex") or 0.0)
    rop = float(propuesta.get("rop_punto_reorden") or 0.0)
    eoq = float(propuesta.get("eoq_lote_economico") or cantidad)
    posicion = float(propuesta.get("posicion_inventario") or stock_kardex)

    descuadre_eri = propuesta.get("descuadre_eri", False)
    discrepancia_und = float(propuesta.get("discrepancia_unidades") or 0.0)
    desalineacion_cop = float(propuesta.get("desalineacion_cop") or 0.0)
    sla_cat_pct = float(propuesta.get("sla_categoria_pct") or 100.0)
    criterios_parada = propuesta.get("criterio_parada", "APROBACION_ESTANDAR")
    umbral = float(propuesta.get("umbral_monto") or 20_000_000.0)

    requiere_verif = "REQUIERE_VERIFICACION_FISICA" in criterios_parada
    requiere_gerencia = "REQUIERE_AUTORIZACION_GERENCIAL" in criterios_parada
    riesgo_mora = "PROVEEDOR_ALTO_RIESGO_MORA" in criterios_parada

    # 1. Dictamen Ejecutivo (lenguaje técnico, claro y humano)
    if requiere_verif and requiere_gerencia:
        dictamen = "Validación en Patio Obligatoria · Desfase Físico e Inversión Mayor"
        color_dictamen = "red"
        icono = "🛑"
        accion = "Detener la emisión automática. Realizar un arqueo visual en almacén para descartar saldo fantasma y tramitar visto bueno previo de Gerencia."
    elif requiere_verif:
        dictamen = "Autorización Condicionada · Discrepancia entre Sistema y Almacén"
        color_dictamen = "orange"
        icono = "⚠️"
        accion = "Comprobar el inventario físico real antes de formalizar la orden para evitar comprar por duplicado ante un descuadre en Kardex."
    elif requiere_gerencia:
        dictamen = "Autorización Gerencial Requerida · Desembolso Superior al Umbral"
        color_dictamen = "blue"
        icono = "💼"
        accion = f"El inventario en bodega es conforme, pero la orden ($ {inversion:,.0f} COP) supera la autonomía de compras ($ {umbral:,.0f} COP). Requiere firma de Gerencia."
    elif riesgo_mora:
        dictamen = "Aprobación con Seguimiento Estrecho · Proveedor con Demora Crítica"
        color_dictamen = "orange"
        icono = "🚚"
        accion = f"Colocar la orden de inmediato con fecha de anticipación extendida; la categoría {categoria} tiene antecedentes de mora en entregas. Coordinar seguimiento temprano."
    else:
        dictamen = "Aprobación Estándar Recomendada · Parámetros Conformados"
        color_dictamen = "green"
        icono = "✅"
        accion = "Emitir la Orden de Compra de manera rutinaria; el ítem cumple satisfactoriamente los controles de inventario, proveedor y presupuesto."

    # 2. Diagnóstico Operativo (Párrafo narrativo orgánico)
    if stock_kardex <= 0:
        diagnostico_narrativo = (
            f"El material se encuentra en **situación de quiebre o agotamiento inminente**, con un saldo registrado de "
            f"**{stock_kardex:,.0f} {unidad}** frente a un Punto de Reorden calculado de **{rop:,.0f} {unidad}**. "
            f"Para restablecer la cobertura de seguridad al 95% y abastecer la demanda programada de la categoría **{categoria}**, "
            f"el modelo determinístico $(s, Q)$ recomienda reordenar **{cantidad:,.0f} {unidad}** con un valor proyectado de "
            f"**$ {inversion:,.0f} COP**."
        )
    else:
        diagnostico_narrativo = (
            f"El saldo disponible (**{stock_kardex:,.0f} {unidad}**) ha perforado el Punto de Reorden (**{rop:,.0f} {unidad}**), "
            f"activando la ventana óptima de abastecimiento. Para salvaguardar la continuidad en planta sin incurrir en sobreinventario, "
            f"el sistema sugiere emitir una orden por **{cantidad:,.0f} {unidad}** (Inversión estimada: **$ {inversion:,.0f} COP**)."
        )

    # 3. Puntos Clave de Control (Estructurados y concisos)
    puntos_clave = []
    items_html = []

    # Factor 1: Importancia Estratégica ABC
    if clase_abc == "A":
        f1_txt = "Material Estratégico (Clase A): Concentra la mayor inversión económica. Un desabastecimiento paraliza líneas críticas de ensamble."
        f1_badge = "<span style='background:#EFF6FF; color:#1D4ED8; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.75rem;'>Clase A · Estratégico</span>"
    elif clase_abc == "B":
        f1_txt = "Material de Control Intermedio (Clase B): Rotación y costo balanceados. Se abastece bajo lote económico para proteger flujo de caja."
        f1_badge = "<span style='background:#FFF7ED; color:#C2410C; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.75rem;'>Clase B · Control</span>"
    else:
        f1_txt = "Material Operativo (Clase C): Menor impacto unitario. El objetivo es mantener stock mínimo sin saturar espacio en bodega."
        f1_badge = "<span style='background:#FEFCE8; color:#854D0E; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.75rem;'>Clase C · Operativo</span>"
    puntos_clave.append(f1_txt)
    items_html.append(f"<div style='margin-bottom:8px; line-height:1.5;'>{f1_badge} <span style='font-size:0.88rem; color:#334155; margin-left:6px;'>{f1_txt.split(': ', 1)[1]}</span></div>")

    # Factor 2: Exactitud de Inventario (ERI)
    if descuadre_eri:
        f2_txt = f"Auditoría de Almacén (ERI Descuadrado): Existe una discrepancia de {discrepancia_und:+,.0f} {unidad} entre Kardex y conteo físico ($ {desalineacion_cop:,.0f} COP en desalineación patrimonial). Es prudente verificar en piso si el material falta físicamente o si es un desajuste de registro."
        f2_badge = "<span style='background:#FEF2F2; color:#B91C1C; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.75rem;'>Auditoría ERI · Discrepancia</span>"
    else:
        f2_txt = "Auditoría de Almacén (ERI Conforme): El saldo teórico coincide con el conteo físico en bodega (0 descuadre patrimonial)."
        f2_badge = "<span style='background:#F0FDF4; color:#15803D; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.75rem;'>Auditoría ERI · Conforme</span>"
    puntos_clave.append(f2_txt)
    items_html.append(f"<div style='margin-bottom:8px; line-height:1.5;'>{f2_badge} <span style='font-size:0.88rem; color:#334155; margin-left:6px;'>{f2_txt.split(': ', 1)[1]}</span></div>")

    # Factor 3: Confiabilidad del Proveedor (SLA)
    if sla_cat_pct < 20.0:
        f3_txt = f"Comportamiento de Entrega (SLA Crítico): La categoría '{categoria}' tiene un cumplimiento histórico a tiempo de apenas {sla_cat_pct:.1f}%. El proveedor habitual tiende a demorarse más días de lo prometido, requiriendo seguimiento preventivo."
        f3_badge = f"<span style='background:#FEF2F2; color:#B91C1C; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.75rem;'>SLA Crítico · {sla_cat_pct:.1f}% OTD</span>"
    elif sla_cat_pct < 60.0:
        f3_txt = f"Comportamiento de Entrega (SLA Moderado): Cumplimiento histórico del {sla_cat_pct:.1f}% en '{categoria}'. Se aconseja confirmar fecha de despacho con el proveedor."
        f3_badge = f"<span style='background:#FFFBEB; color:#B45309; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.75rem;'>SLA Regular · {sla_cat_pct:.1f}% OTD</span>"
    else:
        f3_txt = f"Comportamiento de Entrega (SLA Estable): Cumplimiento confiable del {sla_cat_pct:.1f}% en la categoría '{categoria}'."
        f3_badge = f"<span style='background:#F0FDF4; color:#15803D; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.75rem;'>SLA Estable · {sla_cat_pct:.1f}% OTD</span>"
    puntos_clave.append(f3_txt)
    items_html.append(f"<div style='margin-bottom:8px; line-height:1.5;'>{f3_badge} <span style='font-size:0.88rem; color:#334155; margin-left:6px;'>{f3_txt.split(': ', 1)[1]}</span></div>")

    # Factor 4: Control de Desembolso
    if inversion >= umbral:
        f4_txt = f"Gobernanza de Compras: La inversión proyectada ($ {inversion:,.0f} COP) supera el umbral de autorización rutinaria de $ {umbral:,.0f} COP."
        f4_badge = "<span style='background:#EFF6FF; color:#1E40AF; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.75rem;'>Control Financiero</span>"
        puntos_clave.append(f4_txt)
        items_html.append(f"<div style='margin-bottom:8px; line-height:1.5;'>{f4_badge} <span style='font-size:0.88rem; color:#334155; margin-left:6px;'>{f4_txt.split(': ', 1)[1]}</span></div>")

    # 4. Formateo de Memo en Markdown y en HTML
    memo_markdown = f"{diagnostico_narrativo}\n\n**Factores Clave de Control:**\n" + "\n".join(f"- {p}" for p in puntos_clave)

    # Conversión para HTML limpio
    diag_html = diagnostico_narrativo
    while "**" in diag_html:
        diag_html = diag_html.replace("**", "<strong>", 1)
        diag_html = diag_html.replace("**", "</strong>", 1)

    memo_html = f"""
    <div style="font-size:0.9rem; color:#1E293B; line-height:1.65; margin-bottom:14px;">
        {diag_html}
    </div>
    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; padding:12px 14px; margin-bottom:12px;">
        <div style="font-size:0.72rem; font-weight:800; color:#64748B; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:10px;">
            Diagnóstico Integral (Auditoría ERI / SLA / ABC / Finanzas)
        </div>
        {''.join(items_html)}
    </div>
    """

    return {
        "sku": sku,
        "dictamen": f"{icono} {dictamen}",
        "color": color_dictamen,
        "memo_ejecutivo": memo_markdown,
        "memo_html": memo_html,
        "puntos_clave": puntos_clave,
        "accion_recomendada": accion
    }


# Alias de compatibilidad para endpoints de API
explicar_decision_compra = generar_explicacion_ejecutiva


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
