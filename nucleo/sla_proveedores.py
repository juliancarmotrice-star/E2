"""
Módulo de Auditoría de Nivel de Servicio de Proveedores (SLA) - E2 SAS
Responsabilidad: Auditoría de cumplimiento de entregas (OTD), mora real y desfase de Lead Time vs ERP.

Contrato:
- Entrada: filtros opcionales (proveedor)
- Salida: dict global o list[dict] de métricas agrupadas por proveedor o por categoría de material
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from nucleo.datos import consultar


def _parse_fecha(fecha_str: Optional[str]) -> Optional[datetime]:
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str[:10], "%Y-%m-%d")
    except Exception:
        return None


def obtener_resumen_global_sla() -> Dict[str, Any]:
    """
    Calcula el KPI consolidado de SLA/OTD a nivel empresarial.
    """
    ordenes = consultar("ordenes_compra")
    total_registradas = len(ordenes)
    cerradas = []
    abiertas = []

    for oc in ordenes:
        if oc.get("fecha_recepcion"):
            cerradas.append(oc)
        else:
            abiertas.append(oc)

    a_tiempo = 0
    tardias = 0
    moras_dias = []
    lead_times_dias = []

    for oc in cerradas:
        f_ped = _parse_fecha(oc.get("fecha_pedido"))
        f_prom = _parse_fecha(oc.get("fecha_promesa"))
        f_rec = _parse_fecha(oc.get("fecha_recepcion"))

        if f_rec and f_ped:
            lead_times_dias.append((f_rec - f_ped).days)

        if f_rec and f_prom:
            if f_rec <= f_prom:
                a_tiempo += 1
            else:
                tardias += 1
                moras_dias.append((f_rec - f_prom).days)

    total_cerradas = len(cerradas)
    sla_pct = round((a_tiempo / total_cerradas * 100), 2) if total_cerradas > 0 else 0.0
    mora_prom = round(sum(moras_dias) / len(moras_dias), 2) if moras_dias else 0.0
    lt_prom = round(sum(lead_times_dias) / len(lead_times_dias), 2) if lead_times_dias else 0.0

    return {
        "total_ordenes_registradas": total_registradas,
        "ordenes_cerradas": total_cerradas,
        "ordenes_abiertas_en_transito": len(abiertas),
        "entregas_a_tiempo": a_tiempo,
        "entregas_tardias": tardias,
        "sla_global_pct": sla_pct,
        "sla_global_formato": f"{sla_pct:.2f} %",
        "mora_promedio_cuando_tarde_dias": mora_prom,
        "lead_time_real_promedio_dias": lt_prom
    }


def obtener_metricas_sla_proveedores(proveedor: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retorna el desempeño de entregas desglosado por proveedor.
    """
    filtros = {"proveedor": f"eq.{proveedor}"} if proveedor else None
    ordenes = consultar("ordenes_compra", filtros=filtros)

    agrupado: Dict[str, Dict[str, Any]] = {}

    for oc in ordenes:
        prov = oc.get("proveedor") or "DESCONOCIDO"
        if prov not in agrupado:
            agrupado[prov] = {
                "proveedor": prov,
                "total_ordenes": 0,
                "ordenes_cerradas": 0,
                "ordenes_abiertas": 0,
                "a_tiempo": 0,
                "tardias": 0,
                "moras": [],
                "lead_times": []
            }

        agrupado[prov]["total_ordenes"] += 1
        if not oc.get("fecha_recepcion"):
            agrupado[prov]["ordenes_abiertas"] += 1
            continue

        agrupado[prov]["ordenes_cerradas"] += 1
        f_ped = _parse_fecha(oc.get("fecha_pedido"))
        f_prom = _parse_fecha(oc.get("fecha_promesa"))
        f_rec = _parse_fecha(oc.get("fecha_recepcion"))

        if f_rec and f_ped:
            agrupado[prov]["lead_times"].append((f_rec - f_ped).days)

        if f_rec and f_prom:
            if f_rec <= f_prom:
                agrupado[prov]["a_tiempo"] += 1
            else:
                agrupado[prov]["tardias"] += 1
                agrupado[prov]["moras"].append((f_rec - f_prom).days)

    resultados = []
    for prov, d in agrupado.items():
        cerradas = d["ordenes_cerradas"]
        sla_pct = round((d["a_tiempo"] / cerradas * 100), 2) if cerradas > 0 else 0.0
        mora_prom = round(sum(d["moras"]) / len(d["moras"]), 1) if d["moras"] else 0.0
        lt_prom = round(sum(d["lead_times"]) / len(d["lead_times"]), 1) if d["lead_times"] else 0.0

        resultados.append({
            "proveedor": prov,
            "total_ordenes": d["total_ordenes"],
            "ordenes_cerradas": cerradas,
            "ordenes_abiertas": d["ordenes_abiertas"],
            "a_tiempo": d["a_tiempo"],
            "tardias": d["tardias"],
            "sla_cumplimiento_pct": sla_pct,
            "sla_cumplimiento_formato": f"{sla_pct:.2f} %",
            "mora_promedio_dias": mora_prom,
            "lead_time_real_promedio_dias": lt_prom
        })

    # Ordenar por SLA ascendente (los peores primero)
    resultados.sort(key=lambda x: x["sla_cumplimiento_pct"])
    return resultados


def obtener_metricas_sla_por_categoria() -> List[Dict[str, Any]]:
    """
    Retorna el desempeño de entregas y desfase de Lead Time por categoría de material.
    Cruza ordenes_compra con maestro_materiales.
    """
    ordenes = consultar("ordenes_compra")
    materiales = consultar("maestro_materiales", columnas="sku,categoria,lead_time_declarado_dias")
    mapa_mat = {m["sku"]: m for m in materiales}

    agrupado: Dict[str, Dict[str, Any]] = {}

    for oc in ordenes:
        if not oc.get("fecha_recepcion"):
            continue

        sku = oc.get("sku")
        mat = mapa_mat.get(sku, {})
        cat = mat.get("categoria") or "Sin Categoría"
        lt_erp = float(mat.get("lead_time_declarado_dias") or 0.0)

        if cat not in agrupado:
            agrupado[cat] = {
                "categoria": cat,
                "total_oc_cerradas": 0,
                "a_tiempo": 0,
                "tardias": 0,
                "moras": [],
                "lead_times_erp": [],
                "lead_times_reales": []
            }

        agrupado[cat]["total_oc_cerradas"] += 1
        agrupado[cat]["lead_times_erp"].append(lt_erp)

        f_ped = _parse_fecha(oc.get("fecha_pedido"))
        f_prom = _parse_fecha(oc.get("fecha_promesa"))
        f_rec = _parse_fecha(oc.get("fecha_recepcion"))

        if f_rec and f_ped:
            agrupado[cat]["lead_times_reales"].append((f_rec - f_ped).days)

        if f_rec and f_prom:
            if f_rec <= f_prom:
                agrupado[cat]["a_tiempo"] += 1
            else:
                agrupado[cat]["tardias"] += 1
                agrupado[cat]["moras"].append((f_rec - f_prom).days)

    resultados = []
    for cat, d in agrupado.items():
        cerradas = d["total_oc_cerradas"]
        sla_pct = round((d["a_tiempo"] / cerradas * 100), 2) if cerradas > 0 else 0.0
        mora_prom = round(sum(d["moras"]) / len(d["moras"]), 1) if d["moras"] else 0.0
        lt_erp_prom = round(sum(d["lead_times_erp"]) / len(d["lead_times_erp"]), 1) if d["lead_times_erp"] else 0.0
        lt_real_prom = round(sum(d["lead_times_reales"]) / len(d["lead_times_reales"]), 1) if d["lead_times_reales"] else 0.0
        desfase = round(lt_real_prom - lt_erp_prom, 1)

        resultados.append({
            "categoria": cat,
            "total_oc_cerradas": cerradas,
            "a_tiempo": d["a_tiempo"],
            "retrasadas": d["tardias"],
            "sla_cumplimiento_pct": sla_pct,
            "sla_cumplimiento_formato": f"{sla_pct:.2f} %",
            "mora_promedio_dias": mora_prom,
            "lead_time_erp_dias": lt_erp_prom,
            "lead_time_real_dias": lt_real_prom,
            "desfase_dias": desfase
        })

    resultados.sort(key=lambda x: x["sla_cumplimiento_pct"])
    return resultados


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Probando módulo nucleo.sla_proveedores...")
    glob = obtener_resumen_global_sla()
    print(f"Total Órdenes: {glob['total_ordenes_registradas']} (Cerradas: {glob['ordenes_cerradas']}, Abiertas: {glob['ordenes_abiertas_en_transito']})")
    print(f"SLA Global: {glob['sla_global_formato']} ({glob['entregas_a_tiempo']} a tiempo vs {glob['entregas_tardias']} tardías)")
    print(f"Mora promedio cuando tarde: {glob['mora_promedio_cuando_tarde_dias']} días")
    print(f"Lead Time real promedio: {glob['lead_time_real_promedio_dias']} días")

    cats = obtener_metricas_sla_por_categoria()
    print(f"\nCategorías evaluadas: {len(cats)}")
    for c in cats[:3]:
        print(f" - {c['categoria']}: SLA {c['sla_cumplimiento_formato']} | LT ERP: {c['lead_time_erp_dias']}d vs Real: {c['lead_time_real_dias']}d (Desfase: {c['desfase_dias']}d)")
