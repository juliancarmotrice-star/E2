"""
Pruebas Unitarias: Explicador IA y Orquestador de Reposición
Verifica la estructura orgánica, el lenguaje técnico estructurado y las salvaguardas anti-alucinación.
"""

import pytest
import nucleo.explicador_ia as exp


def test_explicador_ia_estructura_organica():
    propuesta_mock = {
        "sku": "MP-0008",
        "descripcion": "Correderas calibre/ref 39",
        "categoria": "Correderas",
        "clasificacion_abc": "A",
        "cantidad_sugerida": 2828,
        "unidad": "und",
        "costo_unitario": 310890,
        "inversion_cop": 41970150.0,
        "criterio_parada": "REQUIERE_AUTORIZACION_GERENCIAL | PROVEEDOR_ALTO_RIESGO_MORA",
        "descuadre_eri": True,
        "discrepancia_unidades": -130.0,
        "desalineacion_cop": 40415700.0,
        "sla_categoria_pct": 12.5,
        "stock_actual_kardex": -12232,
        "rop_punto_reorden": 1663,
        "eoq_lote_economico": 135,
        "posicion_inventario": -1030,
        "umbral_monto": 20000000.0
    }

    memo = exp.generar_explicacion_ejecutiva(propuesta_mock)

    # Validar campos de contrato
    assert "sku" in memo and memo["sku"] == "MP-0008"
    assert "dictamen" in memo and len(memo["dictamen"]) > 0
    assert "memo_ejecutivo" in memo and len(memo["memo_ejecutivo"]) > 0
    assert "memo_html" in memo and "<div" in memo["memo_html"]
    assert "accion_recomendada" in memo and len(memo["accion_recomendada"]) > 0
    assert "puntos_clave" in memo and len(memo["puntos_clave"]) >= 3

    # Validar que contenga menciones técnicas y comprensibles
    assert "Punto de Reorden" in memo["memo_ejecutivo"]
    assert "Clase A" in memo["memo_ejecutivo"]
    assert "ERI" in memo["memo_ejecutivo"]


def test_explicador_ia_caso_estandar():
    propuesta_estandar = {
        "sku": "MP-0050",
        "descripcion": "Tornillo ensamble 2 pulg",
        "categoria": "Tornillería",
        "clasificacion_abc": "C",
        "cantidad_sugerida": 500,
        "unidad": "und",
        "costo_unitario": 250,
        "inversion_cop": 125000.0,
        "criterio_parada": "APROBACION_ESTANDAR",
        "descuadre_eri": False,
        "discrepancia_unidades": 0.0,
        "desalineacion_cop": 0.0,
        "sla_categoria_pct": 98.0,
        "stock_actual_kardex": 120,
        "rop_punto_reorden": 250,
        "eoq_lote_economico": 500,
        "posicion_inventario": 120,
        "umbral_monto": 20000000.0
    }

    memo = exp.generar_explicacion_ejecutiva(propuesta_estandar)
    assert "Aprobación Estándar" in memo["dictamen"]
    assert memo["color"] == "green"
    assert "conforme" in memo["memo_ejecutivo"].lower()
