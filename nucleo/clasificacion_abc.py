"""
Módulo de Clasificación ABC y Segmentación de Demanda - E2 SAS
Responsabilidad: Clasificación paramétrica Pareto (80/15/5) y aislamiento de plata muerta.

Contrato:
- Entrada: filtros opcionales (categoria, clase ABC)
- Salida: list[dict] o dict de resumen estructurado
"""

from typing import Any, Dict, List, Optional
from nucleo.datos import consultar


def obtener_clasificacion_abc(
    categoria: Optional[str] = None,
    clase: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna la clasificación ABC de todo el catálogo o filtrada por categoría / clase.
    
    Args:
        categoria: Filtro opcional por categoría (ej. 'Vidrio', 'Herrajes')
        clase: Filtro opcional por clase ('A', 'B', 'C')

    Returns:
        Lista de diccionarios con el detalle de cada SKU clasificado
    """
    filtros = {}
    if categoria:
        filtros["categoria"] = f"eq.{categoria}"
    if clase:
        filtros["clasificacion_abc"] = f"eq.{clase.upper()}"

    return consultar(
        objeto="vista_clasificacion_abc",
        filtros=filtros if filtros else None,
        orden="pct_acumulado_valor.asc"
    )


def obtener_resumen_pareto() -> Dict[str, Any]:
    """
    Calcula el resumen agregado Pareto (Clase A, B, C y Plata Muerta).

    Returns:
        Diccionario con conteos, porcentajes de SKUs y valor total anualizado por clase
    """
    skus = consultar("vista_clasificacion_abc", orden="pct_acumulado_valor.asc")
    total_skus = len(skus)
    valor_total_catalogo = sum(float(item.get("valor_consumo_anual_cop") or 0.0) for item in skus)

    resumen_clases = {"A": {"count": 0, "valor": 0.0},
                      "B": {"count": 0, "valor": 0.0},
                      "C": {"count": 0, "valor": 0.0}}
    plata_muerta = []

    for item in skus:
        clase = item.get("clasificacion_abc", "C")
        valor = float(item.get("valor_consumo_anual_cop") or 0.0)
        consumo_total = float(item.get("unidades_consumidas_total") or 0.0)

        if clase in resumen_clases:
            resumen_clases[clase]["count"] += 1
            resumen_clases[clase]["valor"] += valor

        if consumo_total == 0.0:
            plata_muerta.append(item)

    salida = {
        "total_skus": total_skus,
        "valor_total_consumo_cop": valor_total_catalogo,
        "clases": {},
        "plata_muerta": {
            "total_skus": len(plata_muerta),
            "skus": [p.get("sku") for p in plata_muerta]
        }
    }

    for c in ["A", "B", "C"]:
        cnt = resumen_clases[c]["count"]
        val = resumen_clases[c]["valor"]
        salida["clases"][c] = {
            "total_skus": cnt,
            "pct_skus": round((cnt / total_skus * 100), 2) if total_skus > 0 else 0.0,
            "valor_consumo_cop": round(val, 2),
            "pct_valor": round((val / valor_total_catalogo * 100), 2) if valor_total_catalogo > 0 else 0.0
        }

    return salida


def obtener_plata_muerta() -> List[Dict[str, Any]]:
    """
    Retorna los SKUs inmovilizados sin consumo (plata muerta).
    """
    return consultar(
        objeto="vista_clasificacion_abc",
        filtros={"unidades_consumidas_total": "eq.0"},
        orden="sku.asc"
    )


if __name__ == "__main__":
    print("Probando módulo nucleo.clasificacion_abc...")
    resumen = obtener_resumen_pareto()
    print(f"Total SKUs: {resumen['total_skus']}")
    print(f"Valor Total Consumo: ${resumen['valor_total_consumo_cop']:,.2f} COP")
    for c, data in resumen["clases"].items():
        print(f"  Clase {c}: {data['total_skus']} SKUs ({data['pct_skus']}%) -> ${data['valor_consumo_cop']:,.2f} ({data['pct_valor']}%)")
    print(f"Plata Muerta: {resumen['plata_muerta']['total_skus']} SKUs inmovilizados")
