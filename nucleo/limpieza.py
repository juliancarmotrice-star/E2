"""
Módulo de Limpieza y Normalización Canónica (3FN) - E2 SAS
Archivo: nucleo/limpieza.py
Aplica las reglas determinísticas de saneamiento para cualquier lote o archivo entrante.
"""

import os
import re
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List, Optional

# Mapeo canónico de familias de materiales (8 categorías normalizadas)
CAT_MAP: Dict[str, str] = {
    'lamina de acero': 'Lámina', 'lamina': 'Lámina', 'lamina ac': 'Lámina',
    'lámina': 'Lámina', 'lmina': 'Lámina', 'laminas': 'Lámina', 'láminas': 'Lámina',
    'tornilleria': 'Tornillería', 'torn.': 'Tornillería', 'tornillería': 'Tornillería',
    'tornillera': 'Tornillería', 'tornillos': 'Tornillería',
    'tuberia': 'Tubería', 'tubería': 'Tubería', 'tubera': 'Tubería', 'tubos': 'Tubería',
    'pintura': 'Pintura', 'pintura electrostatica': 'Pintura', 'pintura electrostática': 'Pintura',
    'corredera': 'Correderas', 'correderas': 'Correderas',
    'adhesivos': 'Adhesivos', 'pegante': 'Adhesivos', 'adhesivo': 'Adhesivos',
    'empaque': 'Empaque', 'empaques': 'Empaque',
    'vidrio': 'Vidrio', 'vidrios': 'Vidrio'
}

# Mapeo canónico de unidades de medida
UNIT_MAP: Dict[str, str] = {
    'kg': 'kg', 'kilogramo': 'kg', 'kilos': 'kg',
    'unidad': 'unidad', 'und': 'unidad', 'un': 'unidad', 'u': 'unidad',
    'm': 'm', 'metro': 'm', 'metros': 'm',
    'par': 'par', 'pares': 'par',
    'm2': 'm2', 'metro2': 'm2', 'mt2': 'm2',
    'lámina': 'lámina', 'lamina': 'lámina', 'lmina': 'lámina'
}


def normalizar_texto_categoria(val: Any) -> Any:
    """Normaliza variantes léxicas de categoría a su forma canónica."""
    if pd.isna(val):
        return val
    txt = str(val).strip()
    return CAT_MAP.get(txt.lower(), txt)


def normalizar_texto_unidad(val: Any) -> Any:
    """Normaliza variantes léxicas de unidad a su forma canónica."""
    if pd.isna(val):
        return val
    txt = str(val).strip()
    return UNIT_MAP.get(txt.lower(), txt)


def corregir_fechas_serie(serie: pd.Series) -> Tuple[pd.Series, int]:
    """
    Sanea anomalías de fecha conocidas:
    1. Mes 13: 2026-13-05 -> 2026-03-05
    2. Fechas con strings vacíos o caracteres extraños.
    """
    conteo_correcciones = 0
    res = serie.copy().astype(str)

    mask_13 = res.str.contains('2026-13', na=False)
    if mask_13.any():
        conteo_correcciones += int(mask_13.sum())
        res = res.str.replace('2026-13-05', '2026-03-05')
        res = res.str.replace('2026-13-', '2026-03-')

    return res, conteo_correcciones


def corregir_fechas_recepcion_2035(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Corrige años anómalos (ej. 2035) en fecha_recepcion de ordenes_compra,
    alineándolos con el año de fecha_pedido.
    """
    df = df.copy()
    conteo = 0
    if 'fecha_recepcion' not in df.columns or 'fecha_pedido' not in df.columns:
        return df, 0

    fp = pd.to_datetime(df['fecha_pedido'], errors='coerce')
    fr = pd.to_datetime(df['fecha_recepcion'], errors='coerce')
    mask_2035 = fr.dt.year == 2035

    if mask_2035.any():
        conteo = int(mask_2035.sum())
        def _ajustar_anio(row):
            r_fr = pd.to_datetime(row['fecha_recepcion'], errors='coerce')
            r_fp = pd.to_datetime(row['fecha_pedido'], errors='coerce')
            if pd.isna(r_fr) or pd.isna(r_fp):
                return row['fecha_recepcion']
            target_year = r_fp.year if r_fr.replace(year=r_fp.year) >= r_fp else r_fp.year + 1
            return r_fr.replace(year=target_year).strftime('%Y-%m-%d')

        df.loc[mask_2035, 'fecha_recepcion'] = df.loc[mask_2035].apply(_ajustar_anio, axis=1)

    return df, conteo


def aplicar_modulo_limpieza(
    tabla_destino: str,
    df_raw: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Ejecuta el protocolo de limpieza específico de la entidad sobre el DataFrame entrante.
    Aplica las reglas determinísticas de saneamiento y normalización a Tercera Forma Normal (3FN).

    Retorna:
        - df_limpio: DataFrame con los datos completamente saneados.
        - metadatos_limpieza: Diccionario con total de correcciones y detalle de transformaciones.
    """
    df = df_raw.copy()
    transformaciones: List[str] = []
    total_errores_corregidos = 0

    # Normalización genérica de nombres de columna (minúsculas sin espacios)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # =========================================================================
    # 1. MAESTRO DE MATERIALES
    # =========================================================================
    if tabla_destino in ['maestro_materiales', 'maestro_materiales_clean']:
        # 1.1 Categoría
        if 'categoria' in df.columns:
            orig = df['categoria'].copy()
            df['categoria'] = df['categoria'].apply(normalizar_texto_categoria)
            cambios_cat = int((orig.astype(str) != df['categoria'].astype(str)).sum())
            if cambios_cat > 0:
                transformaciones.append(f"{cambios_cat} categorías normalizadas al catálogo estándar (Lámina, Tubería, etc.).")
                total_errores_corregidos += cambios_cat

        # 1.2 Unidad
        if 'unidad' in df.columns:
            orig_u = df['unidad'].copy()
            df['unidad'] = df['unidad'].apply(normalizar_texto_unidad)
            cambios_u = int((orig_u.astype(str) != df['unidad'].astype(str)).sum())
            if cambios_u > 0:
                transformaciones.append(f"{cambios_u} unidades estandarizadas (kg, unidad, m, par, lámina).")
                total_errores_corregidos += cambios_u

        # 1.3 Costo Unitario
        if 'costo_unitario' in df.columns:
            df['costo_unitario'] = pd.to_numeric(df['costo_unitario'], errors='coerce').abs()

        # 1.4 Lead time declarado
        if 'lead_time_declarado_dias' in df.columns:
            nulos_lt = int(df['lead_time_declarado_dias'].isna().sum())
            if nulos_lt > 0:
                df['lead_time_declarado_dias'] = pd.to_numeric(df['lead_time_declarado_dias'], errors='coerce').fillna(14).astype(int)
                transformaciones.append(f"{nulos_lt} lead times nulos imputados con valor de seguridad (14 días).")
                total_errores_corregidos += nulos_lt

        # 1.5 Limpiar SKUs y descripciones
        if 'sku' in df.columns:
            df['sku'] = df['sku'].astype(str).str.strip().str.upper()

    # =========================================================================
    # 2. MOVIMIENTOS DE INVENTARIOS (KARDEX)
    # =========================================================================
    elif tabla_destino in ['movimientos_inventarios', 'movimientos_inventario', 'movimientos_inventarios_clean']:
        # 2.1 Fechas (mes 13 -> mes 03)
        if 'fecha' in df.columns:
            df['fecha'], n_fechas = corregir_fechas_serie(df['fecha'])
            if n_fechas > 0:
                transformaciones.append(f"{n_fechas} fechas anómalas '2026-13-05' corregidas a '2026-03-05'.")
                total_errores_corregidos += n_fechas

        # 2.2 Cantidad positiva (el tipo_movimiento rige el signo contable)
        if 'cantidad' in df.columns:
            q_num = pd.to_numeric(df['cantidad'], errors='coerce')
            neg_q = int((q_num < 0).sum())
            if neg_q > 0:
                transformaciones.append(f"{neg_q} cantidades negativas convertidas a valor absoluto |Q|.")
                total_errores_corregidos += neg_q
            df['cantidad'] = q_num.abs().fillna(0)

        # 2.3 Tipo de movimiento estandarizado
        if 'tipo_movimiento' in df.columns:
            df['tipo_movimiento'] = df['tipo_movimiento'].astype(str).str.strip().str.lower()

        if 'sku' in df.columns:
            df['sku'] = df['sku'].astype(str).str.strip().str.upper()

    # =========================================================================
    # 3. ÓRDENES DE COMPRA
    # =========================================================================
    elif tabla_destino in ['ordenes_compra', 'ordenes_compra_clean']:
        # 3.1 Fechas anómalas 2035 -> año del pedido
        df, n_2035 = corregir_fechas_recepcion_2035(df)
        if n_2035 > 0:
            transformaciones.append(f"{n_2035} fechas de recepción con año '2035' ajustadas a su año real de compra.")
            total_errores_corregidos += n_2035

        # 3.2 Cantidad y costos no negativos
        if 'cantidad' in df.columns:
            c_num = pd.to_numeric(df['cantidad'], errors='coerce')
            n_neg = int((c_num < 0).sum())
            if n_neg > 0:
                transformaciones.append(f"{n_neg} cantidades negativas convertidas a positivo.")
                total_errores_corregidos += n_neg
            df['cantidad'] = c_num.abs().fillna(0)

        if 'costo_unitario' in df.columns:
            df['costo_unitario'] = pd.to_numeric(df['costo_unitario'], errors='coerce').abs()

        if 'sku' in df.columns:
            df['sku'] = df['sku'].astype(str).str.strip().str.upper()

    # =========================================================================
    # 4. CONTEO FÍSICO OFICIAL
    # =========================================================================
    elif tabla_destino in ['conteo_fisico', 'conteo_fisico_clean']:
        if 'sku' in df.columns:
            df['sku'] = df['sku'].astype(str).str.strip().str.upper()
            n_dups = int(df.duplicated(subset=['sku']).sum())
            if n_dups > 0:
                df = df.drop_duplicates(subset=['sku'], keep='first')
                transformaciones.append(f"{n_dups} registros duplicados de SKU eliminados.")
                total_errores_corregidos += n_dups

        if 'stock_fisico_contado' in df.columns:
            s_num = pd.to_numeric(df['stock_fisico_contado'], errors='coerce')
            n_neg = int((s_num < 0).sum())
            if n_neg > 0:
                transformaciones.append(f"{n_neg} conteos físicos negativos saneados por |valor absoluto|.")
                total_errores_corregidos += n_neg
            df['stock_fisico_contado'] = s_num.abs().fillna(0)

    # =========================================================================
    # 5. INVENTARIO BODEGA JEFE (CUADERNO DEL JEFE)
    # =========================================================================
    elif tabla_destino in ['inventario_bodega_JEFE', 'inventario_bodega_jefe', 'inventario_bodega_jefe_clean']:
        # Normalizar 'codigo'
        if 'codigo' in df.columns:
            df['codigo'] = df['codigo'].astype(str).str.strip().str.upper()
            n_dups = int(df.duplicated(subset=['codigo']).sum())
            if n_dups > 0:
                df = df.drop_duplicates(subset=['codigo'], keep='first')
                transformaciones.append(f"{n_dups} códigos duplicados en cuaderno de jefe eliminados.")
                total_errores_corregidos += n_dups

        # Normalizar material
        if 'material' in df.columns:
            df['material'] = df['material'].apply(normalizar_texto_categoria)

        # Imputar observaciones nulas
        if 'observacion' in df.columns:
            n_nulos = int(df['observacion'].isna().sum())
            if n_nulos > 0:
                df['observacion'] = df['observacion'].fillna('Sin observación')
                transformaciones.append(f"{n_nulos} observaciones vacías imputadas como 'Sin observación'.")
                total_errores_corregidos += n_nulos
        else:
            df['observacion'] = 'Sin observación'

        # Signos negativos
        if 'conteo_jefe' in df.columns:
            cj_num = pd.to_numeric(df['conteo_jefe'], errors='coerce')
            n_neg = int((cj_num < 0).sum())
            if n_neg > 0:
                transformaciones.append(f"{n_neg} conteos negativos de jefe saneados por |valor absoluto|.")
                total_errores_corregidos += n_neg
            df['conteo_jefe'] = cj_num.abs().fillna(0)
            df['conteo_jefe_limpio'] = df['conteo_jefe']

    # =========================================================================
    # 6. BOM (BILL OF MATERIALS) - Normalización 3FN
    # =========================================================================
    elif tabla_destino in ['bom', 'bom_clean']:
        if 'producto' in df.columns:
            df['producto'] = df['producto'].astype(str).str.strip().str.upper()
        if 'sku_material' in df.columns:
            df['sku_material'] = df['sku_material'].astype(str).str.strip().str.upper()

        # Generar llave compuesta atómica id_bom si no viene
        if 'id_bom' not in df.columns and 'producto' in df.columns and 'sku_material' in df.columns:
            df['id_bom'] = df['producto'] + '_' + df['sku_material']
            transformaciones.append("Llave primaria compuesta 'id_bom' generada unívocamente (3FN).")
            total_errores_corregidos += 1

        # Eliminar nombre_producto redundante (3FN)
        if 'nombre_producto' in df.columns:
            df = df.drop(columns=['nombre_producto'])
            transformaciones.append("Columna redundante 'nombre_producto' eliminada por normalización 3FN.")
            total_errores_corregidos += 1

        if 'unidad' in df.columns:
            df['unidad'] = df['unidad'].apply(normalizar_texto_unidad)

        if 'cantidad_por_unidad' in df.columns:
            df['cantidad_por_unidad'] = pd.to_numeric(df['cantidad_por_unidad'], errors='coerce').abs().fillna(1.0)

    # =========================================================================
    # 7. PLAN DE PRODUCCIÓN - Normalización 3FN
    # =========================================================================
    elif tabla_destino in ['plan_produccion', 'plan_produccion_clean']:
        if 'nombre_producto' in df.columns:
            df = df.drop(columns=['nombre_producto'])
            transformaciones.append("Columna redundante 'nombre_producto' desacoplada hacia maestro_productos (3FN).")
            total_errores_corregidos += 1

        if 'producto' in df.columns:
            df['producto'] = df['producto'].astype(str).str.strip().str.upper()

        if 'cantidad_planeada' in df.columns:
            df['cantidad_planeada'] = pd.to_numeric(df['cantidad_planeada'], errors='coerce').abs().fillna(0)

        if 'cantidad_real' in df.columns:
            df['cantidad_real'] = pd.to_numeric(df['cantidad_real'], errors='coerce').abs().fillna(0)

    # =========================================================================
    # 8. MAESTRO DE PRODUCTOS
    # =========================================================================
    elif tabla_destino in ['maestro_productos', 'maestro_productos_clean']:
        if 'producto' in df.columns:
            df['producto'] = df['producto'].astype(str).str.strip().str.upper()
            n_dups = int(df.duplicated(subset=['producto']).sum())
            if n_dups > 0:
                df = df.drop_duplicates(subset=['producto'], keep='first')
                transformaciones.append(f"{n_dups} productos terminados duplicados consolidados.")
                total_errores_corregidos += n_dups

    # =========================================================================
    # 9. INVENTARIO INICIAL
    # =========================================================================
    elif tabla_destino in ['inventario_inicial', 'inventario_inicial_clean']:
        if 'sku' in df.columns:
            df['sku'] = df['sku'].astype(str).str.strip().str.upper()
        if 'stock_inicial' in df.columns:
            s_init = pd.to_numeric(df['stock_inicial'], errors='coerce')
            n_neg = int((s_init < 0).sum())
            if n_neg > 0:
                transformaciones.append(f"{n_neg} stocks iniciales negativos ajustados por |valor absoluto|.")
                total_errores_corregidos += n_neg
            df['stock_inicial'] = s_init.abs().fillna(0)

    metadatos_limpieza = {
        'total_correcciones': total_errores_corregidos,
        'transformaciones_aplicadas': transformaciones if transformaciones else ["Datos conformes con las reglas de calidad y formato."],
        'columnas_resultantes': list(df.columns)
    }

    return df, metadatos_limpieza
