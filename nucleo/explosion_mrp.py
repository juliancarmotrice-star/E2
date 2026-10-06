"""
Módulo de Explosión de Materiales (BOM) y Requerimientos MRP - E2 SAS
Responsabilidad: Descomposición de necesidades de materiales basada en BOM y Plan Maestro de Producción (MPS).

Contrato:
- Entrada: filtros opcionales (producto, periodo)
- Salida: list[dict] de requerimientos brutos y netos estructurados por material o por producto
"""

from typing import Any, Dict, List, Optional
from nucleo.datos import consultar


def obtener_explosion_demanda_bruta(
    producto: Optional[str] = None,
    periodo: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Calcula el requerimiento bruto de materias primas multiplicando el BOM por las unidades
    producidas en el Plan Maestro de Producción (MPS).
    
    Args:
        producto: Código de producto terminado opcional (ej. 'PT-ARCH-4G')
        periodo: Mes opcional del MPS (ej. '2024-07-01')

    Returns:
        Lista de diccionarios con sku_material, descripción, cantidad total demandada y valorización COP
    """
    filtros_mps = {}
    if producto:
        filtros_mps["producto"] = f"eq.{producto}"
    if periodo:
        filtros_mps["periodo"] = f"eq.{periodo}"

    mps = consultar("plan_produccion", filtros=filtros_mps if filtros_mps else None)
    bom = consultar("bom")
    materiales = consultar("maestro_materiales", columnas="sku,descripcion,categoria,costo_unitario")
    mapa_mat = {m["sku"]: m for m in materiales}

    # Agrupar producción por producto
    prod_por_pt: Dict[str, float] = {}
    for p in mps:
        pt = p.get("producto")
        cant = float(p.get("cantidad_real") if p.get("cantidad_real") is not None else p.get("cantidad_planeada") or 0.0)
        prod_por_pt[pt] = prod_por_pt.get(pt, 0.0) + cant

    # Acumular requerimiento bruto por SKU de material
    demanda_por_sku: Dict[str, Dict[str, Any]] = {}
    for item in bom:
        pt = item.get("producto")
        sku = item.get("sku_material")
        cant_unitaria = float(item.get("cantidad_por_unidad") or 0.0)
        unidad = item.get("unidad") or "und"

        if pt not in prod_por_pt:
            continue

        cant_producida = prod_por_pt[pt]
        consumo_teorico = cant_producida * cant_unitaria

        if sku not in demanda_por_sku:
            mat_info = mapa_mat.get(sku, {})
            costo = float(mat_info.get("costo_unitario") or 0.0)
            demanda_por_sku[sku] = {
                "sku_material": sku,
                "descripcion": mat_info.get("descripcion", "N/A"),
                "categoria": mat_info.get("categoria", "N/A"),
                "unidad": unidad,
                "costo_unitario": costo,
                "requerimiento_bruto_total": 0.0
            }

        demanda_por_sku[sku]["requerimiento_bruto_total"] += consumo_teorico

    resultados = []
    for sku, d in demanda_por_sku.items():
        req = round(d["requerimiento_bruto_total"], 2)
        val = round(req * d["costo_unitario"], 2)
        resultados.append({
            "sku_material": sku,
            "descripcion": d["descripcion"],
            "categoria": d["categoria"],
            "unidad": d["unidad"],
            "costo_unitario": d["costo_unitario"],
            "requerimiento_bruto": req,
            "requerimiento_bruto_formato": f"{req:,.2f} {d['unidad']}",
            "valor_consumo_cop": val,
            "valor_consumo_formato": f"$ {val:,.2f} COP"
        })

    resultados.sort(key=lambda x: x["valor_consumo_cop"], reverse=True)
    return resultados


def obtener_consumo_por_linea_producto() -> List[Dict[str, Any]]:
    """
    Desglosa el consumo teórico de materiales agrupado por línea de producto terminado.
    """
    mps = consultar("plan_produccion")
    bom = consultar("bom")
    productos = consultar("maestro_productos")
    mapa_pt = {p["producto"]: p.get("nombre_producto") for p in productos}

    # Sumar unidades totales fabricadas por producto
    prod_totales: Dict[str, float] = {}
    for p in mps:
        pt = p.get("producto")
        cant = float(p.get("cantidad_real") if p.get("cantidad_real") is not None else p.get("cantidad_planeada") or 0.0)
        prod_totales[pt] = prod_totales.get(pt, 0.0) + cant

    # Conteo de componentes e insumos por producto
    resumen: Dict[str, Dict[str, Any]] = {}
    for item in bom:
        pt = item.get("producto")
        if pt not in resumen:
            resumen[pt] = {
                "producto": pt,
                "nombre_producto": mapa_pt.get(pt, pt),
                "unidades_fabricadas": prod_totales.get(pt, 0.0),
                "total_componentes_bom": 0,
                "materiales": []
            }
        resumen[pt]["total_componentes_bom"] += 1
        resumen[pt]["materiales"].append({
            "sku_material": item.get("sku_material"),
            "cantidad_por_unidad": float(item.get("cantidad_por_unidad") or 0.0),
            "unidad": item.get("unidad")
        })

    lista = list(resumen.values())
    lista.sort(key=lambda x: x["unidades_fabricadas"], reverse=True)
    return lista


def obtener_requerimientos_netos_mrp() -> List[Dict[str, Any]]:
    """
    Calcula los requerimientos netos comparando la demanda bruta con la posición de inventario
    disponible (Kardex + Órdenes en tránsito de vista_calculo_eoq_rop).
    """
    brutos = obtener_explosion_demanda_bruta()
    stock_info = consultar(
        "vista_calculo_eoq_rop",
        columnas="sku,stock_actual_kardex,ordenes_en_transito,posicion_inventario"
    )
    mapa_stock = {s["sku"]: s for s in stock_info}

    netos = []
    for item in brutos:
        sku = item["sku_material"]
        st = mapa_stock.get(sku, {})
        stock_disp = float(st.get("posicion_inventario") or 0.0)
        req_bruto = item["requerimiento_bruto"]
        req_neto = max(0.0, req_bruto - stock_disp)
        costo = item["costo_unitario"]

        netos.append({
            "sku_material": sku,
            "descripcion": item["descripcion"],
            "categoria": item["categoria"],
            "unidad": item["unidad"],
            "requerimiento_bruto": req_bruto,
            "stock_disponible": round(stock_disp, 2),
            "requerimiento_neto": round(req_neto, 2),
            "requerimiento_neto_formato": f"{req_neto:,.2f} {item['unidad']}",
            "deficit_valor_cop": round(req_neto * costo, 2),
            "tiene_deficit": req_neto > 0
        })

    netos.sort(key=lambda x: x["deficit_valor_cop"], reverse=True)
    return netos


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Probando módulo nucleo.explosion_mrp...")
    bruta = obtener_explosion_demanda_bruta()
    print(f"Total materiales demandados por MPS: {len(bruta)}")
    valor_total = sum(b["valor_consumo_cop"] for b in bruta)
    print(f"Valor total demanda teórica bruta: $ {valor_total:,.2f} COP")

    print("\nTop 3 insumos con mayor demanda bruta:")
    for b in bruta[:3]:
        print(f" - {b['sku_material']} ({b['descripcion']}): {b['requerimiento_bruto_formato']} -> {b['valor_consumo_formato']}")

    lineas = obtener_consumo_por_linea_producto()
    print(f"\nLíneas de producto evaluadas: {len(lineas)}")
    for l in lineas[:3]:
        print(f" - {l['producto']} ({l['nombre_producto']}): {l['unidades_fabricadas']:,.0f} und fabricadas, {l['total_componentes_bom']} insumos en BOM")
