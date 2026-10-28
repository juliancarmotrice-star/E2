"""
Orquestador del Sistema de Gestión de Inventarios y Producción 4.0 - E2 SAS
Archivo: orquestador.py

Arquitectura Transaccional:
1. Las propuestas de compra se calculan y exploran en memoria (pipeline determinístico).
2. La base de datos NO se ensucia con borradores masivos.
3. Al momento de la APROBACIÓN HUMANA se ejecuta la transacción en Supabase:
   - Se crea la Orden de Compra oficial en `public.ordenes_compra` (con nuevo consecutivo OC-XXXX).
   - Se registra la propuesta auditada en `public.propuestas_compra` vinculada a la OC generada.
4. Al momento del RECHAZO se registra en `public.propuestas_compra` con motivo de rechazo (sin generar OC).
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import nucleo.datos as datos
import nucleo.clasificacion_abc as abc
import nucleo.exactitud_eri as eri
import nucleo.reposicion_eoq_rop as reposicion
import nucleo.sla_proveedores as sla
import nucleo.explosion_mrp as mrp


# Umbrales calibrados por Ingeniería (Slide 33)
UMBRAL_ALTO_VALOR_DEFAULT_COP = 20_000_000.0  # $20M COP por orden individual
SLA_MINIMO_CONFIANZA_PCT = 20.0                # SLA menor a 20% es proveedor de alto riesgo


def generar_id_corrida() -> str:
    """Genera un identificador único con timestamp para auditar cada ciclo de recomendaciones."""
    return datetime.now().strftime("RUN-%Y%m%d-%H%M%S")


def obtener_siguiente_codigo_oc() -> str:
    """
    Obtiene el consecutivo más alto en ordenes_compra y genera el siguiente código (ej. OC-6472).
    """
    todas = datos.consultar("ordenes_compra", columnas="orden_compra")
    max_num = 0
    for oc in todas:
        codigo = str(oc.get("orden_compra") or "")
        if codigo.startswith("OC-"):
            try:
                num = int(codigo.replace("OC-", ""))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass

    nuevo_num = max_num + 1 if max_num > 0 else 7000
    return f"OC-{nuevo_num}"


def obtener_proveedor_habitual(sku: str) -> str:
    """
    Obtiene el proveedor histórico más reciente para un SKU en ordenes_compra.
    """
    ocs = datos.consultar(
        "ordenes_compra",
        filtros={"sku": f"eq.{sku}"},
        columnas="proveedor",
        orden="fecha_pedido.desc",
        limite=1
    )
    if ocs and ocs[0].get("proveedor"):
        return ocs[0]["proveedor"]
    return "PROV-GENERAL"


def obtener_lead_time_material(sku: str) -> int:
    """
    Obtiene el Lead Time declarado del material para proyectar la fecha promesa de entrega.
    """
    mats = datos.consultar(
        "maestro_materiales",
        filtros={"sku": f"eq.{sku}"},
        columnas="lead_time_declarado_dias",
        limite=1
    )
    if mats and mats[0].get("lead_time_declarado_dias") is not None:
        try:
            return int(mats[0]["lead_time_declarado_dias"])
        except ValueError:
            pass
    return 15


def generar_propuestas_reposicion(
    umbral_alto_valor_cop: float = UMBRAL_ALTO_VALOR_DEFAULT_COP
) -> Dict[str, Any]:
    """
    Calcula en memoria el pipeline de compras sugeridas y evalúa criterios de parada.
    NO modifica la base de datos hasta que el usuario decida.
    """
    corrida_id = generar_id_corrida()
    fecha_corrida_iso = datetime.now().isoformat()

    # 1. Diagnóstico ERI (Auditoría de Veracidad de Saldos)
    diagnostico_eri = eri.obtener_diagnostico_eri()
    mapa_eri = {d["sku"]: d for d in diagnostico_eri}

    # 2. Desempeño de Proveedores (SLA)
    sla_categorias = sla.obtener_metricas_sla_por_categoria()
    mapa_sla_cat = {c["categoria"]: c for c in sla_categorias}

    # 3. Plan de Reposición Determinístico (EOQ / ROP)
    plan_compras = reposicion.obtener_plan_compras_sugeridas()
    items_a_ordenar = plan_compras.get("items", [])

    propuestas: List[Dict[str, Any]] = []
    conteo_paradas = {
        "REQUIERE_VERIFICACION_FISICA": 0,
        "REQUIERE_AUTORIZACION_GERENCIAL": 0,
        "PROVEEDOR_ALTO_RIESGO_MORA": 0,
        "APROBACION_ESTANDAR": 0
    }

    for idx, item in enumerate(items_a_ordenar, start=1):
        sku = item.get("sku")
        costo_u = float(item.get("costo_unitario") or 0.0)
        cantidad = float(item.get("cantidad_sugerida_pedir") or item.get("eoq_lote_economico") or 0.0)
        inversion = float(item.get("inversion_eoq_cop") or (cantidad * costo_u))
        categoria = item.get("categoria", "")

        # Cruzar con ERI
        info_eri = mapa_eri.get(sku, {})
        descuadre_eri = abs(float(info_eri.get("discrepancia_unidades") or 0.0)) > 0
        desalineacion_cop = float(info_eri.get("desalineacion_dinero_cop") or 0.0)

        # Cruzar con SLA
        info_sla = mapa_sla_cat.get(categoria, {})
        sla_cat_pct = float(info_sla.get("sla_cumplimiento_pct") or 100.0)

        # Evaluar Criterios de Parada (Slide 33)
        criterios_parada = []
        if descuadre_eri:
            criterios_parada.append("REQUIERE_VERIFICACION_FISICA")
            conteo_paradas["REQUIERE_VERIFICACION_FISICA"] += 1

        if inversion >= umbral_alto_valor_cop:
            criterios_parada.append("REQUIERE_AUTORIZACION_GERENCIAL")
            conteo_paradas["REQUIERE_AUTORIZACION_GERENCIAL"] += 1

        if sla_cat_pct < SLA_MINIMO_CONFIANZA_PCT:
            criterios_parada.append("PROVEEDOR_ALTO_RIESGO_MORA")
            conteo_paradas["PROVEEDOR_ALTO_RIESGO_MORA"] += 1

        if not criterios_parada:
            criterio_principal = "APROBACION_ESTANDAR"
            conteo_paradas["APROBACION_ESTANDAR"] += 1
        else:
            criterio_principal = " | ".join(criterios_parada)

        # Contexto operacional del modelo determinístico EOQ / ROP
        stock_actual = float(item.get("stock_actual_kardex_und") or item.get("stock_actual_kardex") or 0.0)
        rop_val = float(item.get("rop_punto_reorden_und") or item.get("punto_reorden_rop") or 0.0)
        eoq_val = float(item.get("eoq_lote_economico_und") or item.get("eoq_lote_economico") or 0.0)
        ss_val = float(item.get("stock_seguridad_und") or item.get("stock_seguridad_ss") or 0.0)
        posicion = float(item.get("posicion_inventario") or stock_actual)
        semaforo_crudo = str(item.get("estado_semaforo") or item.get("semaforo_inventario") or "Alerta")
        semaforo_limpio = semaforo_crudo.replace("🔴 ", "").replace("🟡 ", "").replace("🟢 ", "").replace("🔵 ", "").strip()
        discrepancia_und = float(info_eri.get("discrepancia_unidades") or 0.0)

        # Motivo ejecutivo ordenado y técnico
        if descuadre_eri:
            motivo = f"Bajo ROP ({stock_actual:,.0f} vs {rop_val:,.0f} und) · {semaforo_limpio} · Descuadre ERI: {info_eri.get('discrepancia_formato', f'{discrepancia_und:+,.0f} und')}"
        else:
            motivo = f"Bajo ROP ({stock_actual:,.0f} vs {rop_val:,.0f} und) · {semaforo_limpio} · Kardex verificado"

        propuesta = {
            "propuesta_temp_id": idx,
            "corrida_id": corrida_id,
            "sku": sku,
            "descripcion": item.get("descripcion"),
            "categoria": categoria,
            "clasificacion_abc": item.get("clasificacion_abc"),
            "cantidad_sugerida": cantidad,
            "unidad": "und",
            "costo_unitario": costo_u,
            "inversion_cop": inversion,
            "motivo_orden": motivo,
            "criterio_parada": criterio_principal,
            "es_estandar": criterio_principal == "APROBACION_ESTANDAR",
            "descuadre_eri": descuadre_eri,
            "discrepancia_unidades": discrepancia_und,
            "desalineacion_cop": desalineacion_cop,
            "sla_categoria_pct": sla_cat_pct,
            "stock_actual_kardex": stock_actual,
            "rop_punto_reorden": rop_val,
            "eoq_lote_economico": eoq_val,
            "stock_seguridad": ss_val,
            "posicion_inventario": posicion,
            "estado_semaforo": semaforo_limpio,
            "umbral_monto": umbral_alto_valor_cop
        }
        propuestas.append(propuesta)

    inversion_total = sum(p["inversion_cop"] for p in propuestas)

    # Instrumentación B4.02: Asentar corrida en la bitácora de la base de datos
    try:
        import nucleo.analisis_cambios as ac
        ac.asentar_corrida_en_bitacora(
            corrida_id=corrida_id,
            total_propuestas=len(propuestas),
            inversion_total_cop=round(inversion_total, 2),
            conteo_paradas=conteo_paradas,
            duracion_ms=180
        )
    except Exception as e:
        print(f"[ALERTA ORQUESTADOR] No se pudo asentar corrida en bitacora: {e}")

    return {
        "corrida_id": corrida_id,
        "fecha_corrida": fecha_corrida_iso,
        "total_propuestas": len(propuestas),
        "inversion_total_cop": round(inversion_total, 2),
        "inversion_total_formato": f"$ {inversion_total:,.2f} COP",
        "conteo_paradas": conteo_paradas,
        "propuestas": propuestas
    }


def aprobar_propuesta(
    propuesta: Dict[str, Any],
    decidido_por: str = "Planeador de Compras",
    comentarios: Optional[str] = None
) -> Dict[str, Any]:
    """
    TRANSACCIÓN DE APROBACIÓN:
    1. Genera una Orden de Compra oficial en Supabase (`public.ordenes_compra`).
    2. Registra la propuesta aprobada en `public.propuestas_compra` enlazando la OC.
    """
    sku = propuesta["sku"]
    cantidad = int(round(float(propuesta.get("cantidad_sugerida") or 0)))
    costo_u = int(round(float(propuesta.get("costo_unitario") or 0)))
    inversion = round(float(propuesta.get("inversion_cop") or (cantidad * costo_u)), 2)

    # 1. Obtener parámetros de la OC
    nuevo_codigo_oc = obtener_siguiente_codigo_oc()
    proveedor = obtener_proveedor_habitual(sku)
    lt_dias = obtener_lead_time_material(sku)

    hoy = datetime.now().date()
    fecha_pedido_str = hoy.strftime("%Y-%m-%d")
    fecha_promesa_str = (hoy + timedelta(days=lt_dias)).strftime("%Y-%m-%d")

    # 2. Insertar en public.ordenes_compra (Orden abierta / en tránsito)
    registro_oc = {
        "orden_compra": nuevo_codigo_oc,
        "fecha_pedido": fecha_pedido_str,
        "sku": sku,
        "cantidad": cantidad,
        "proveedor": proveedor,
        "fecha_promesa": fecha_promesa_str,
        "fecha_recepcion": None,  # Queda en tránsito
        "costo_unitario": costo_u
    }

    try:
        datos.insertar("ordenes_compra", [registro_oc])
    except Exception as e:
        raise RuntimeError(f"Fallo al crear orden de compra en ordenes_compra: {e}") from e

    # 3. Insertar en public.propuestas_compra (Auditoría de decisión)
    ahora_iso = datetime.now().isoformat()
    registro_propuesta = {
        "corrida_id": propuesta.get("corrida_id", generar_id_corrida()),
        "sku": sku,
        "descripcion": propuesta.get("descripcion"),
        "categoria": propuesta.get("categoria"),
        "clasificacion_abc": propuesta.get("clasificacion_abc"),
        "cantidad_sugerida": cantidad,
        "unidad": propuesta.get("unidad", "und"),
        "costo_unitario": costo_u,
        "inversion_cop": inversion,
        "motivo_orden": propuesta.get("motivo_orden"),
        "criterio_parada": propuesta.get("criterio_parada"),
        "estado_decision": "APROBADA",
        "decidido_por": decidido_por,
        "fecha_decision": ahora_iso,
        "orden_compra_generada": nuevo_codigo_oc,
        "comentarios": comentarios or f"Aprobada por {decidido_por}. Generada {nuevo_codigo_oc}"
    }

    try:
        datos.insertar("propuestas_compra", [registro_propuesta])
    except Exception as e:
        print(f"[ADVERTENCIA] La OC {nuevo_codigo_oc} fue creada pero falló el log en propuestas_compra: {e}")

    return {
        "exito": True,
        "sku": sku,
        "orden_compra_generada": nuevo_codigo_oc,
        "proveedor": proveedor,
        "fecha_pedido": fecha_pedido_str,
        "fecha_promesa": fecha_promesa_str,
        "cantidad": cantidad,
        "inversion_cop": inversion
    }


def rechazar_propuesta(
    propuesta: Dict[str, Any],
    decidido_por: str = "Planeador de Compras",
    motivo: Optional[str] = None
) -> Dict[str, Any]:
    """
    TRANSACCIÓN DE RECHAZO:
    Registra en `public.propuestas_compra` que la sugerencia fue RECHAZADA por el planeador.
    NO genera ninguna orden en `ordenes_compra`.
    """
    sku = propuesta["sku"]
    cantidad = float(propuesta.get("cantidad_sugerida") or 0)
    costo_u = float(propuesta.get("costo_unitario") or 0)
    inversion = float(propuesta.get("inversion_cop") or (cantidad * costo_u))

    ahora_iso = datetime.now().isoformat()
    registro_propuesta = {
        "corrida_id": propuesta.get("corrida_id", generar_id_corrida()),
        "sku": sku,
        "descripcion": propuesta.get("descripcion"),
        "categoria": propuesta.get("categoria"),
        "clasificacion_abc": propuesta.get("clasificacion_abc"),
        "cantidad_sugerida": cantidad,
        "unidad": propuesta.get("unidad", "und"),
        "costo_unitario": costo_u,
        "inversion_cop": inversion,
        "motivo_orden": propuesta.get("motivo_orden"),
        "criterio_parada": propuesta.get("criterio_parada"),
        "estado_decision": "RECHAZADA",
        "decidido_por": decidido_por,
        "fecha_decision": ahora_iso,
        "orden_compra_generada": None,
        "comentarios": motivo or f"Rechazada por {decidido_por}"
    }

    datos.insertar("propuestas_compra", [registro_propuesta])
    return {
        "exito": True,
        "sku": sku,
        "estado": "RECHAZADA",
        "motivo": motivo
    }


def consultar_historial_propuestas(limite: int = 100) -> List[Dict[str, Any]]:
    """
    Lee las propuestas decididas (aprobadas y rechazadas) almacenadas en Supabase.
    """
    return datos.consultar(
        objeto="propuestas_compra",
        limite=limite,
        orden="fecha_decision.desc"
    )


def consultar_ordenes_recientes(limite: int = 20) -> List[Dict[str, Any]]:
    """
    Lee las órdenes de compra más recientes en Supabase.
    """
    return datos.consultar(
        objeto="ordenes_compra",
        limite=limite,
        orden="orden_compra.desc"
    )


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("==================================================")
    print("  ORQUESTADOR TRANSACCIONAL (E2 SAS)")
    print("==================================================")

    res = generar_propuestas_reposicion()
    print(f"Corrida: {res['corrida_id']}")
    print(f"Propuestas en memoria: {res['total_propuestas']}")
    print(f"Siguiente OC a emitir: {obtener_siguiente_codigo_oc()}")
    print("Base de datos limpia y lista para recibir aprobaciones.")
