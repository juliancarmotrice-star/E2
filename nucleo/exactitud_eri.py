"""
Módulo de Auditoría de Exactitud de Registro de Inventario (ERI) - E2 SAS
Responsabilidad: Reconciliación tridimensional (Kardex vs Conteo Físico vs Cuaderno Jefe)
y cuantificación de desalineación patrimonial.

Contrato:
- Entrada: filtros opcionales (solo descuadrados, límite, N top desalineados)
- Salida: dict con resumen global o list[dict] con diagnóstico por SKU
"""

from typing import Any, Dict, List, Optional
from nucleo.datos import consultar


def obtener_diagnostico_eri(
    solo_descuadrados: bool = False,
    limite: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retorna el diagnóstico tridimensional de inventarios fila por fila.
    
    Args:
        solo_descuadrados: Si es True, filtra únicamente registros con discrepancia
        limite: Límite opcional de filas

    Returns:
        Lista de diccionarios con SKU, saldos teóricos, físicos, cuaderno, discrepancia y desalineación COP
    """
    filtros = {}
    if solo_descuadrados:
        filtros["estado_eri"] = "like.*Descuadrado*"

    return consultar(
        objeto="vista_diagnostico_eri_inventarios",
        filtros=filtros if filtros else None,
        limite=limite,
        orden="desalineacion_dinero_cop.desc"
    )


def obtener_resumen_eri() -> Dict[str, Any]:
    """
    Retorna el resumen agregado de Exactitud de Registro de Inventario (KPI ERI).
    Consume `vista_resumen_eri_inventarios`.
    """
    filas = consultar("vista_resumen_eri_inventarios")
    
    resumen = {
        "categorias": {},
        "total_general": None
    }

    for f in filas:
        tipo = f.get("tipo_rotacion")
        data = {
            "total_skus": f.get("total_skus"),
            "skus_exactos": f.get("skus_exactos"),
            "skus_descuadrados": f.get("skus_descuadrados"),
            "eri_porcentaje_exactitud": f.get("eri_porcentaje_exactitud"),
            "pct_error_discrepancia": f.get("pct_error_discrepancia"),
            "desalineacion_contable_bruta": f.get("desalineacion_contable_bruta")
        }
        if tipo == "TOTAL GENERAL":
            resumen["total_general"] = data
        else:
            resumen["categorias"][tipo] = data

    return resumen


def obtener_top_desalineados(n: int = 10) -> List[Dict[str, Any]]:
    """
    Retorna los N SKUs con mayor impacto patrimonial absoluto por discrepancia de inventario.
    """
    return consultar(
        objeto="vista_diagnostico_eri_inventarios",
        limite=n,
        orden="desalineacion_dinero_cop.desc"
    )


if __name__ == "__main__":
    print("Probando módulo nucleo.exactitud_eri...")
    res = obtener_resumen_eri()
    tg = res.get("total_general") or {}
    print(f"ERI Global: {tg.get('eri_porcentaje_exactitud')} ({tg.get('skus_exactos')}/{tg.get('total_skus')} SKUs exactos)")
    print(f"Desalineación Contable Bruta: {tg.get('desalineacion_contable_bruta')}")
    top3 = obtener_top_desalineados(3)
    print("\nTop 3 SKUs más desalineados:")
    for item in top3:
        print(f" - {item.get('sku')} ({item.get('descripcion')}): Discrepancia {item.get('discrepancia_formato')} -> {item.get('desalineacion_dinero_formato')}")
