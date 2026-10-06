"""
Módulo de Reposición Continua (EOQ, ROP y Stock de Seguridad) - E2 SAS
Responsabilidad: Cálculo y sugerencias de compra determinísticas con nivel de servicio 95% (Z=1.64485).

Contrato:
- Entrada: filtros opcionales (sku, semáforo, solo_ordenar)
- Salida: list[dict] con parámetros de reposición o dict con plan de compras agregado
"""

from typing import Any, Dict, List, Optional
from nucleo.datos import consultar


def obtener_parametros_reposicion(
    sku: Optional[str] = None,
    semaforo: Optional[str] = None,
    solo_ordenar: bool = False
) -> List[Dict[str, Any]]:
    """
    Retorna los parámetros de inventario y reposición de la vista calculada en Supabase.
    
    Args:
        sku: Código SKU específico (ej. 'MP-0020')
        semaforo: Filtro por color/estado ('ROJO', 'AMARILLO', 'VERDE', 'AZUL')
        solo_ordenar: Si es True, filtra únicamente SKUs con requiere_orden_compra = true

    Returns:
        Lista de diccionarios con parámetros (EOQ, SS, ROP, Stock actual, Semáforo, etc.)
    """
    filtros = {}
    if sku:
        filtros["sku"] = f"eq.{sku}"
    if semaforo:
        filtros["estado_semaforo"] = f"like.*{semaforo.upper()}*"
    if solo_ordenar:
        filtros["requiere_orden_compra"] = "eq.true"

    return consultar(
        objeto="vista_calculo_eoq_rop",
        filtros=filtros if filtros else None,
        orden="inversion_eoq_cop.desc"
    )


def consultar_sku(sku: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene los parámetros específicos de reposición para un único SKU.
    """
    resultados = obtener_parametros_reposicion(sku=sku)
    return resultados[0] if resultados else None


def obtener_plan_compras_sugeridas() -> Dict[str, Any]:
    """
    Genera el plan de compras priorizado consolidando todos los SKUs bajo punto de reorden.

    Returns:
        Diccionario con conteo de órdenes, inversión total requerida en COP y detalle por ítem
    """
    items = consultar(
        objeto="vista_calculo_eoq_rop",
        filtros={"requiere_orden_compra": "eq.true"},
        orden="clasificacion_abc.asc"
    )

    inversion_total = sum(float(item.get("inversion_eoq_cop") or 0.0) for item in items)

    conteo_semaforos = {"ROJO (Quiebre Inminente)": 0, "AMARILLO (Reordenar)": 0}
    for item in items:
        sem = (item.get("estado_semaforo") or "").lower()
        if "quiebre inminente" in sem or "rojo" in sem:
            conteo_semaforos["ROJO (Quiebre Inminente)"] += 1
        elif "reordenar" in sem or "amarillo" in sem:
            conteo_semaforos["AMARILLO (Reordenar)"] += 1

    return {
        "total_skus_a_ordenar": len(items),
        "inversion_total_cop": round(inversion_total, 2),
        "inversion_total_formato": f"$ {inversion_total:,.2f} COP",
        "conteo_urgencia": conteo_semaforos,
        "items": items
    }


if __name__ == "__main__":
    import sys
    # Forzar soporte UTF-8 en consola si es posible
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Probando modulo nucleo.reposicion_eoq_rop...")
    plan = obtener_plan_compras_sugeridas()
    print(f"SKUs a ordenar: {plan['total_skus_a_ordenar']}")
    print(f"Urgencia: {plan['conteo_urgencia']}")
    print(f"Inversion total requerida: {plan['inversion_total_formato']}")

    lamina = consultar_sku("MP-0020")
    if lamina:
        print("\nPrueba SKU MP-0020 (Lamina):")
        print(f" - ROP: {lamina.get('rop_punto_reorden_und')} und")
        print(f" - Stock Seguridad: {lamina.get('stock_seguridad_und')} und")
        print(f" - EOQ: {lamina.get('eoq_lote_economico_und')} und")
        print(f" - Semaforo: {lamina.get('estado_semaforo')}")
        print(f" - Accion: {lamina.get('accion_sugerida')}")

