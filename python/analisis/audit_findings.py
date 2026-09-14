import os
import pandas as pd
import numpy as np
import json
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR)) if os.path.basename(os.path.dirname(CURRENT_DIR)) in ['python', 'src', 'scripts'] else os.path.dirname(CURRENT_DIR)
RAW_DIR = os.path.join(BASE_DIR, 'datos_iniciales')
RESULTS_DIR = os.path.join(BASE_DIR, 'resultados_auditoria')

def get_raw_path(filename):
    p = os.path.join(RAW_DIR, filename)
    return p if os.path.exists(p) else os.path.join(BASE_DIR, filename)

def convert_np(obj):
    if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_np(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_np(i) for i in obj]
    return obj

def audit():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    report = {}

    # =========================================================================
    # 1. MAESTRO DE MATERIALES
    # =========================================================================
    mm = pd.read_csv(get_raw_path('maestro_materiales.csv'))
    
    # 1.1 Nulos y duplicados
    nulls_mm = mm.isnull().sum().to_dict()
    dup_rows_mm = int(mm.duplicated().sum())
    dup_sku_mm = int(mm['sku'].duplicated().sum())

    # 1.2 Reglas de negocio e imposibles
    neg_cost_mm = mm[mm['costo_unitario'] <= 0]
    stock_inv_mm = mm[mm['stock_min'] > mm['stock_max']]
    stock_equal_mm = mm[mm['stock_min'] == mm['stock_max']]
    neg_lead_mm = mm[mm['lead_time_declarado_dias'] <= 0]

    # 1.3 Outliers en Costo Unitario (IQR)
    q1_c = mm['costo_unitario'].quantile(0.25)
    q3_c = mm['costo_unitario'].quantile(0.75)
    iqr_c = q3_c - q1_c
    outliers_cost = mm[(mm['costo_unitario'] < (q1_c - 1.5 * iqr_c)) | (mm['costo_unitario'] > (q3_c + 1.5 * iqr_c))]

    # 1.4 Inconsistencias de texto
    cat_counts = mm['categoria'].value_counts().to_dict()
    unit_counts = mm['unidad'].value_counts().to_dict()
    prov_counts = mm['proveedor'].value_counts().to_dict()

    report['maestro_materiales'] = {
        'total_registros': len(mm),
        'nulos': nulls_mm,
        'duplicados_completos': dup_rows_mm,
        'duplicados_sku': dup_sku_mm,
        'costos_menor_igual_cero': len(neg_cost_mm),
        'costos_menor_igual_cero_detalle': neg_cost_mm[['sku', 'descripcion', 'costo_unitario']].to_dict(orient='records'),
        'stock_min_mayor_stock_max': len(stock_inv_mm),
        'stock_min_mayor_stock_max_detalle': stock_inv_mm[['sku', 'stock_min', 'stock_max']].to_dict(orient='records'),
        'stock_min_igual_stock_max': len(stock_equal_mm),
        'lead_time_declarado_invalido': len(neg_lead_mm),
        'lead_time_declarado_invalido_detalle': neg_lead_mm[['sku', 'lead_time_declarado_dias']].to_dict(orient='records'),
        'outliers_costo_total': len(outliers_cost),
        'outliers_costo_detalle': outliers_cost[['sku', 'descripcion', 'categoria', 'costo_unitario']].to_dict(orient='records'),
        'categorias_distribucion': cat_counts,
        'unidades_distribucion': unit_counts,
        'proveedores_distribucion': prov_counts
    }

    # =========================================================================
    # 2. MOVIMIENTOS INVENTARIO (KARDEX)
    # =========================================================================
    mov = pd.read_csv(get_raw_path('movimientos_inventario.csv'))
    nulls_mov = mov.isnull().sum().to_dict()
    dup_rows_mov = int(mov.duplicated().sum())
    neg_qty_mov = mov[mov['cantidad'] <= 0]
    tipos_mov = mov['tipo_movimiento'].value_counts().to_dict()
    bodegas_mov = mov['bodega'].value_counts().to_dict()
    resp_mov = mov['responsable'].value_counts().to_dict()

    # Outliers en cantidad movida
    q1_qm = mov['cantidad'].quantile(0.25)
    q3_qm = mov['cantidad'].quantile(0.75)
    iqr_qm = q3_qm - q1_qm
    outliers_qty_mov = mov[mov['cantidad'] > (q3_qm + 3 * iqr_qm)]

    report['movimientos_inventario'] = {
        'total_registros': len(mov),
        'nulos': nulls_mov,
        'duplicados_completos': dup_rows_mov,
        'cantidades_menor_igual_cero': len(neg_qty_mov),
        'cantidades_menor_igual_cero_detalle': neg_qty_mov.to_dict(orient='records'),
        'tipos_movimiento': tipos_mov,
        'bodegas': bodegas_mov,
        'responsables_total': len(resp_mov),
        'outliers_cantidad_total': len(outliers_qty_mov),
        'outliers_cantidad_max': float(mov['cantidad'].max()),
        'estadisticas_cantidad': {'min': float(mov['cantidad'].min()), 'max': float(mov['cantidad'].max()), 'media': float(mov['cantidad'].mean()), 'mediana': float(mov['cantidad'].median())},
        'rango_fechas': {'min': str(mov['fecha'].min()), 'max': str(mov['fecha'].max())}
    }

    # =========================================================================
    # 3. ORDENES DE COMPRA
    # =========================================================================
    oc = pd.read_csv(get_raw_path('ordenes_compra.csv'))
    nulls_oc = oc.isnull().sum().to_dict()
    dup_rows_oc = int(oc.duplicated().sum())
    dup_oc_id = int(oc['orden_compra'].duplicated().sum())
    neg_qty_oc = oc[oc['cantidad'] <= 0]
    neg_cost_oc = oc[oc['costo_unitario'] <= 0]

    oc['fecha_pedido_dt'] = pd.to_datetime(oc['fecha_pedido'], errors='coerce')
    oc['fecha_promesa_dt'] = pd.to_datetime(oc['fecha_promesa'], errors='coerce')
    oc['fecha_recepcion_dt'] = pd.to_datetime(oc['fecha_recepcion'], errors='coerce')
    oc['lead_time_real'] = (oc['fecha_recepcion_dt'] - oc['fecha_pedido_dt']).dt.days
    oc['lead_time_prometido'] = (oc['fecha_promesa_dt'] - oc['fecha_pedido_dt']).dt.days
    oc['dias_retraso'] = (oc['fecha_recepcion_dt'] - oc['fecha_promesa_dt']).dt.days

    fechas_anomalas = oc[oc['lead_time_real'] < 0]
    fechas_promesa_anomalas = oc[oc['lead_time_prometido'] < 0]
    ordenes_sin_recepcion = oc[oc['fecha_recepcion'].isnull()]

    # Cruce de costo OC vs Maestro Materiales
    oc_merged = oc.merge(mm[['sku', 'costo_unitario', 'lead_time_declarado_dias']], on='sku', suffixes=('_oc', '_maestro'))
    oc_merged['dif_costo_pct'] = ((oc_merged['costo_unitario_oc'] - oc_merged['costo_unitario_maestro']) / oc_merged['costo_unitario_maestro']) * 100
    oc_merged['dif_lead_time_dias'] = oc_merged['lead_time_real'] - oc_merged['lead_time_declarado_dias']

    report['ordenes_compra'] = {
        'total_registros': len(oc),
        'nulos': nulls_oc,
        'duplicados_completos': dup_rows_oc,
        'duplicados_id_oc': dup_oc_id,
        'cantidades_menor_igual_cero': len(neg_qty_oc),
        'costos_menor_igual_cero': len(neg_cost_oc),
        'fechas_recepcion_anterior_a_pedido': len(fechas_anomalas),
        'fechas_recepcion_anterior_a_pedido_detalle': fechas_anomalas[['orden_compra', 'sku', 'fecha_pedido', 'fecha_recepcion', 'lead_time_real']].to_dict(orient='records'),
        'fechas_promesa_anterior_a_pedido': len(fechas_promesa_anomalas),
        'ordenes_pendientes_sin_recepcion': len(ordenes_sin_recepcion),
        'estadisticas_lead_time_real': {
            'min': float(oc['lead_time_real'].min()),
            'max': float(oc['lead_time_real'].max()),
            'media': float(oc['lead_time_real'].mean()),
            'mediana': float(oc['lead_time_real'].median())
        },
        'estadisticas_retraso_entrega': {
            'entregas_con_retraso_total': int((oc['dias_retraso'] > 0).sum()),
            'entregas_a_tiempo_o_antes': int((oc['dias_retraso'] <= 0).sum()),
            'retraso_max_dias': float(oc['dias_retraso'].max()),
            'retraso_promedio_dias': float(oc['dias_retraso'].mean())
        },
        'discrepancias_costo_oc_vs_maestro': {
            'compras_con_precio_diferente_al_maestro': int((oc_merged['dif_costo_pct'].abs() > 1.0).sum()),
            'max_desviacion_pct': float(oc_merged['dif_costo_pct'].abs().max()),
            'promedio_desviacion_pct': float(oc_merged['dif_costo_pct'].abs().mean())
        }
    }

    # =========================================================================
    # 4. BOM (BILL OF MATERIALS)
    # =========================================================================
    bom = pd.read_csv(get_raw_path('bom.csv'))
    nulls_bom = bom.isnull().sum().to_dict()
    dup_rows_bom = int(bom.duplicated().sum())
    neg_qty_bom = bom[bom['cantidad_por_unidad'] <= 0]
    
    # Inconsistencias de unidades en BOM vs Maestro
    bom_merged = bom.merge(mm[['sku', 'unidad']], left_on='sku_material', right_on='sku', suffixes=('_bom', '_maestro'))
    bom_merged['unidad_bom_norm'] = bom_merged['unidad_bom'].str.strip().str.upper()
    bom_merged['unidad_maestro_norm'] = bom_merged['unidad_maestro'].str.strip().str.upper()
    unit_mismatches = bom_merged[bom_merged['unidad_bom_norm'] != bom_merged['unidad_maestro_norm']]

    report['bom'] = {
        'total_registros': len(bom),
        'nulos': nulls_bom,
        'duplicados_completos': dup_rows_bom,
        'cantidades_menor_igual_cero': len(neg_qty_bom),
        'unidades_distribucion_bom': bom['unidad'].value_counts().to_dict(),
        'discrepancias_unidades_bom_vs_maestro': len(unit_mismatches),
        'discrepancias_unidades_detalle': unit_mismatches[['producto', 'sku_material', 'unidad_bom', 'unidad_maestro']].to_dict(orient='records'),
        'estadisticas_consumo_por_unidad': {
            'min': float(bom['cantidad_por_unidad'].min()),
            'max': float(bom['cantidad_por_unidad'].max()),
            'media': float(bom['cantidad_por_unidad'].mean())
        }
    }

    # =========================================================================
    # 5. PLAN DE PRODUCCION
    # =========================================================================
    plan = pd.read_csv(get_raw_path('plan_produccion.csv'))
    nulls_plan = plan.isnull().sum().to_dict()
    dup_rows_plan = int(plan.duplicated().sum())
    neg_plan = plan[plan['cantidad_planeada'] < 0]
    neg_real = plan[plan['cantidad_real'] < 0]
    zero_plan = plan[plan['cantidad_planeada'] == 0]
    zero_real = plan[plan['cantidad_real'] == 0]
    
    plan['desviacion_cumplimiento'] = plan['cantidad_real'] - plan['cantidad_planeada']
    plan['cumplimiento_pct'] = (plan['cantidad_real'] / plan['cantidad_planeada']) * 100

    report['plan_produccion'] = {
        'total_registros': len(plan),
        'nulos': nulls_plan,
        'duplicados_completos': dup_rows_plan,
        'cantidades_planeadas_negativas': len(neg_plan),
        'cantidades_reales_negativas': len(neg_real),
        'cantidades_planeadas_cero': len(zero_plan),
        'cantidades_reales_cero': len(zero_real),
        'estadisticas_cumplimiento': {
            'produccion_menor_a_planeada': int((plan['cantidad_real'] < plan['cantidad_planeada']).sum()),
            'produccion_igual_a_planeada': int((plan['cantidad_real'] == plan['cantidad_planeada']).sum()),
            'produccion_mayor_a_planeada': int((plan['cantidad_real'] > plan['cantidad_planeada']).sum()),
            'cumplimiento_promedio_pct': float(plan['cumplimiento_pct'].mean()),
            'cumplimiento_min_pct': float(plan['cumplimiento_pct'].min()),
            'cumplimiento_max_pct': float(plan['cumplimiento_pct'].max())
        }
    }

    # =========================================================================
    # 6. INVENTARIO INICIAL
    # =========================================================================
    ii = pd.read_csv(get_raw_path('inventario_inicial.csv'))
    nulls_ii = ii.isnull().sum().to_dict()
    dup_rows_ii = int(ii.duplicated().sum())
    dup_sku_ii = int(ii['sku'].duplicated().sum())
    neg_stock_ii = ii[ii['stock_inicial'] < 0]
    zero_stock_ii = ii[ii['stock_inicial'] == 0]

    report['inventario_inicial'] = {
        'total_registros': len(ii),
        'nulos': nulls_ii,
        'duplicados_completos': dup_rows_ii,
        'duplicados_sku': dup_sku_ii,
        'stock_inicial_negativo': len(neg_stock_ii),
        'stock_inicial_cero': len(zero_stock_ii),
        'estadisticas_stock_inicial': {
            'min': int(ii['stock_inicial'].min()),
            'max': int(ii['stock_inicial'].max()),
            'media': float(ii['stock_inicial'].mean()),
            'mediana': float(ii['stock_inicial'].median())
        }
    }

    # =========================================================================
    # 7. CONTEO FISICO (AUDITORIA FISICA)
    # =========================================================================
    cf = pd.read_csv(get_raw_path('conteo_fisico.csv'))
    nulls_cf = cf.isnull().sum().to_dict()
    dup_rows_cf = int(cf.duplicated().sum())
    dup_sku_cf = int(cf['sku'].duplicated().sum())
    neg_stock_cf = cf[cf['stock_fisico_contado'] < 0]
    zero_stock_cf = cf[cf['stock_fisico_contado'] == 0]

    report['conteo_fisico'] = {
        'total_registros': len(cf),
        'nulos': nulls_cf,
        'duplicados_completos': dup_rows_cf,
        'duplicados_sku': dup_sku_cf,
        'stock_fisico_negativo_total': len(neg_stock_cf),
        'stock_fisico_negativo_detalle': neg_stock_cf.head(15).to_dict(orient='records'),
        'stock_fisico_cero': len(zero_stock_cf),
        'estadisticas_conteo_fisico': {
            'min': int(cf['stock_fisico_contado'].min()),
            'max': int(cf['stock_fisico_contado'].max()),
            'media': float(cf['stock_fisico_contado'].mean())
        }
    }

    # =========================================================================
    # 8. INVENTARIO BODEGA JEFE (REGISTRO MANUAL)
    # =========================================================================
    jefe = pd.read_csv(get_raw_path('Inventario_bodega_JEFE.csv'))
    nulls_jefe = jefe.isnull().sum().to_dict()
    dup_rows_jefe = int(jefe.duplicated().sum())
    dup_cod_jefe = int(jefe['codigo'].duplicated().sum())
    neg_stock_jefe = jefe[jefe['conteo_jefe'] < 0]
    
    mat_names = jefe['material'].value_counts().to_dict()
    obs_counts = jefe['observacion'].value_counts().to_dict()

    report['inventario_bodega_jefe'] = {
        'total_registros': len(jefe),
        'nulos': nulls_jefe,
        'duplicados_completos': dup_rows_jefe,
        'duplicados_codigo': dup_cod_jefe,
        'conteo_jefe_negativo_total': len(neg_stock_jefe),
        'conteo_jefe_negativo_detalle': neg_stock_jefe.head(15).to_dict(orient='records'),
        'nombres_materiales_distribucion': mat_names,
        'observaciones_distribucion': obs_counts,
        'estadisticas_conteo_jefe': {
            'min': int(jefe['conteo_jefe'].min()),
            'max': int(jefe['conteo_jefe'].max()),
            'media': float(jefe['conteo_jefe'].mean())
        }
    }

    # =========================================================================
    # 9. AUDITORIA TRANSVERSAL: RECONCILIACION KARDEX VS FISICO VS JEFE
    # =========================================================================
    mov_entradas = mov[mov['tipo_movimiento'] == 'entrada'].groupby('sku')['cantidad'].sum().rename('entradas')
    mov_salidas = mov[mov['tipo_movimiento'] == 'salida'].groupby('sku')['cantidad'].sum().rename('salidas')
    mov_ajustes = mov[mov['tipo_movimiento'] == 'ajuste'].groupby('sku')['cantidad'].sum().rename('ajustes')

    rec = ii[['sku', 'stock_inicial']].copy()
    rec = rec.merge(mov_entradas, on='sku', how='left').fillna(0)
    rec = rec.merge(mov_salidas, on='sku', how='left').fillna(0)
    rec = rec.merge(mov_ajustes, on='sku', how='left').fillna(0)
    rec['stock_teorico_kardex'] = rec['stock_inicial'] + rec['entradas'] - rec['salidas'] + rec['ajustes']

    rec = rec.merge(cf[['sku', 'stock_fisico_contado']], on='sku', how='left')
    rec = rec.merge(jefe[['codigo', 'conteo_jefe', 'observacion']], left_on='sku', right_on='codigo', how='left')

    rec['discrepancia_kardex_vs_fisico'] = rec['stock_fisico_contado'] - rec['stock_teorico_kardex']
    rec['discrepancia_kardex_vs_jefe'] = rec['conteo_jefe'] - rec['stock_teorico_kardex']
    rec['discrepancia_fisico_vs_jefe'] = rec['conteo_jefe'] - rec['stock_fisico_contado']

    kardex_negativo = rec[rec['stock_teorico_kardex'] < 0]
    exact_match_fisico = rec[rec['discrepancia_kardex_vs_fisico'] == 0]
    mismatch_fisico = rec[rec['discrepancia_kardex_vs_fisico'] != 0]

    report['reconciliacion_inventario'] = {
        'total_skus_evaluados': len(rec),
        'skus_con_stock_teorico_negativo_en_kardex': len(kardex_negativo),
        'skus_con_stock_teorico_negativo_detalle': kardex_negativo[['sku', 'stock_inicial', 'entradas', 'salidas', 'ajustes', 'stock_teorico_kardex']].head(10).to_dict(orient='records'),
        'skus_con_coincidencia_exacta_kardex_fisico': len(exact_match_fisico),
        'skus_con_discrepancia_kardex_fisico': len(mismatch_fisico),
        'ira_inexactitud_registros_pct': float((len(mismatch_fisico) / len(rec)) * 100),
        'discrepancia_kardex_fisico_stats': {
            'min': float(rec['discrepancia_kardex_vs_fisico'].min()),
            'max': float(rec['discrepancia_kardex_vs_fisico'].max()),
            'media_absoluta': float(rec['discrepancia_kardex_vs_fisico'].abs().mean())
        }
    }

    clean_report = convert_np(report)
    output_path = os.path.join(RESULTS_DIR, 'audit_findings.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(clean_report, f, indent=2, ensure_ascii=False)
    print(f'Audit findings successfully saved to {output_path}')
    return clean_report

if __name__ == '__main__':
    audit()
