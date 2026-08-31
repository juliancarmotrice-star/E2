import pandas as pd
import numpy as np
import json

def audit_dataset():
    report = {}

    # -------------------------------------------------------------
    # 1. MAESTRO DE MATERIALES
    # -------------------------------------------------------------
    mm = pd.read_csv('maestro_materiales.csv')
    mm_issues = {
        'total_rows': len(mm),
        'nulls': mm.isnull().sum().to_dict(),
        'duplicates': mm.duplicated().sum(),
        'sku_duplicates': mm['sku'].duplicated().sum(),
        'negative_or_zero_cost': mm[mm['costo_unitario'] <= 0][['sku', 'costo_unitario']].to_dict(orient='records'),
        'invalid_stock_thresholds': mm[mm['stock_min'] > mm['stock_max']][['sku', 'stock_min', 'stock_max']].to_dict(orient='records'),
        'negative_lead_time': mm[mm['lead_time_declarado_dias'] <= 0][['sku', 'lead_time_declarado_dias']].to_dict(orient='records'),
        'categories': mm['categoria'].value_counts().to_dict(),
        'units': mm['unidad'].value_counts().to_dict(),
        'providers': mm['proveedor'].value_counts().to_dict(),
    }
    # Outliers in cost
    q1 = mm['costo_unitario'].quantile(0.25)
    q3 = mm['costo_unitario'].quantile(0.75)
    iqr = q3 - q1
    upper_cost = q3 + 3 * iqr # extreme outliers
    mm_issues['cost_extreme_outliers'] = mm[mm['costo_unitario'] > upper_cost][['sku', 'descripcion', 'categoria', 'costo_unitario']].to_dict(orient='records')
    report['maestro_materiales'] = mm_issues

    # -------------------------------------------------------------
    # 2. MOVIMIENTOS INVENTARIO
    # -------------------------------------------------------------
    mov = pd.read_csv('movimientos_inventario.csv')
    mov_issues = {
        'total_rows': len(mov),
        'nulls': mov.isnull().sum().to_dict(),
        'duplicates': mov.duplicated().sum(),
        'negative_or_zero_quantity': mov[mov['cantidad'] <= 0][['fecha', 'sku', 'tipo_movimiento', 'cantidad', 'documento']].to_dict(orient='records'),
        'tipos_movimiento': mov['tipo_movimiento'].value_counts().to_dict(),
        'bodegas': mov['bodega'].value_counts().to_dict(),
        'responsables': mov['responsable'].value_counts().to_dict(),
        'date_range': {'min': str(mov['fecha'].min()), 'max': str(mov['fecha'].max())}
    }
    # Outliers in quantity
    q1_m = mov['cantidad'].quantile(0.25)
    q3_m = mov['cantidad'].quantile(0.75)
    iqr_m = q3_m - q1_m
    mov_issues['quantity_extreme_outliers_count'] = int((mov['cantidad'] > (q3_m + 5 * iqr_m)).sum())
    mov_issues['quantity_max'] = float(mov['cantidad'].max())
    mov_issues['quantity_min'] = float(mov['cantidad'].min())
    report['movimientos_inventario'] = mov_issues

    # -------------------------------------------------------------
    # 3. ORDENES DE COMPRA
    # -------------------------------------------------------------
    oc = pd.read_csv('ordenes_compra.csv')
    oc['fecha_pedido_dt'] = pd.to_datetime(oc['fecha_pedido'], errors='coerce')
    oc['fecha_promesa_dt'] = pd.to_datetime(oc['fecha_promesa'], errors='coerce')
    oc['fecha_recepcion_dt'] = pd.to_datetime(oc['fecha_recepcion'], errors='coerce')
    oc['lead_time_real'] = (oc['fecha_recepcion_dt'] - oc['fecha_pedido_dt']).dt.days
    oc['lead_time_prometido'] = (oc['fecha_promesa_dt'] - oc['fecha_pedido_dt']).dt.days
    oc['retraso_entrega'] = (oc['fecha_recepcion_dt'] - oc['fecha_promesa_dt']).dt.days

    oc_issues = {
        'total_rows': len(oc),
        'nulls': oc.isnull().sum().to_dict(),
        'duplicates': oc.duplicated().sum(),
        'orden_compra_duplicates': oc['orden_compra'].duplicated().sum(),
        'negative_or_zero_quantity': oc[oc['cantidad'] <= 0][['orden_compra', 'sku', 'cantidad']].to_dict(orient='records'),
        'negative_or_zero_cost': oc[oc['costo_unitario'] <= 0][['orden_compra', 'sku', 'costo_unitario']].to_dict(orient='records'),
        'recepcion_before_pedido': oc[oc['lead_time_real'] < 0][['orden_compra', 'fecha_pedido', 'fecha_recepcion', 'lead_time_real']].to_dict(orient='records'),
        'promesa_before_pedido': oc[oc['lead_time_prometido'] < 0][['orden_compra', 'fecha_pedido', 'fecha_promesa']].to_dict(orient='records'),
        'unreceived_orders': int(oc['fecha_recepcion'].isnull().sum()),
        'providers': oc['proveedor'].value_counts().to_dict()
    }
    report['ordenes_compra'] = oc_issues

    # -------------------------------------------------------------
    # 4. BOM (BILL OF MATERIALS)
    # -------------------------------------------------------------
    bom = pd.read_csv('bom.csv')
    bom_issues = {
        'total_rows': len(bom),
        'nulls': bom.isnull().sum().to_dict(),
        'duplicates': bom.duplicated().sum(),
        'empty_id_bom': int(bom['ID_bom'].isnull().sum()),
        'negative_or_zero_qty': bom[bom['cantidad_por_unidad'] <= 0][['producto', 'sku_material', 'cantidad_por_unidad']].to_dict(orient='records'),
        'units': bom['unidad'].value_counts().to_dict(),
        'products_count': int(bom['producto'].nunique())
    }
    report['bom'] = bom_issues

    # -------------------------------------------------------------
    # 5. PLAN DE PRODUCCION
    # -------------------------------------------------------------
    plan = pd.read_csv('plan_produccion.csv')
    plan_issues = {
        'total_rows': len(plan),
        'nulls': plan.isnull().sum().to_dict(),
        'duplicates': plan.duplicated().sum(),
        'negative_planned': plan[plan['cantidad_planeada'] < 0][['periodo', 'producto', 'cantidad_planeada']].to_dict(orient='records'),
        'negative_real': plan[plan['cantidad_real'] < 0][['periodo', 'producto', 'cantidad_real']].to_dict(orient='records'),
        'zero_planned': int((plan['cantidad_planeada'] == 0).sum()),
        'zero_real': int((plan['cantidad_real'] == 0).sum()),
        'periods': plan['periodo'].value_counts().to_dict(),
        'products_count': int(plan['producto'].nunique())
    }
    report['plan_produccion'] = plan_issues

    # -------------------------------------------------------------
    # 6. INVENTARIO INICIAL
    # -------------------------------------------------------------
    ii = pd.read_csv('inventario_inicial.csv')
    ii_issues = {
        'total_rows': len(ii),
        'nulls': ii.isnull().sum().to_dict(),
        'duplicates': ii.duplicated().sum(),
        'sku_duplicates': ii['sku'].duplicated().sum(),
        'negative_stock': ii[ii['stock_inicial'] < 0][['sku', 'stock_inicial']].to_dict(orient='records'),
        'zero_stock': int((ii['stock_inicial'] == 0).sum()),
        'dates': ii['fecha'].value_counts().to_dict()
    }
    report['inventario_inicial'] = ii_issues

    # -------------------------------------------------------------
    # 7. CONTEO FISICO
    # -------------------------------------------------------------
    cf = pd.read_csv('conteo_fisico.csv')
    cf_issues = {
        'total_rows': len(cf),
        'nulls': cf.isnull().sum().to_dict(),
        'duplicates': cf.duplicated().sum(),
        'sku_duplicates': cf['sku'].duplicated().sum(),
        'negative_stock': cf[cf['stock_fisico_contado'] < 0][['sku', 'stock_fisico_contado']].to_dict(orient='records'),
        'negative_stock_count': int((cf['stock_fisico_contado'] < 0).sum()),
        'zero_stock': int((cf['stock_fisico_contado'] == 0).sum()),
        'dates': cf['fecha_conteo'].value_counts().to_dict()
    }
    report['conteo_fisico'] = cf_issues

    # -------------------------------------------------------------
    # 8. INVENTARIO BODEGA JEFE
    # -------------------------------------------------------------
    jefe = pd.read_csv('Inventario_bodega_JEFE.csv')
    jefe_issues = {
        'total_rows': len(jefe),
        'nulls': jefe.isnull().sum().to_dict(),
        'duplicates': jefe.duplicated().sum(),
        'codigo_duplicates': jefe['codigo'].duplicated().sum(),
        'negative_stock': jefe[jefe['conteo_jefe'] < 0][['material', 'codigo', 'conteo_jefe', 'observacion']].to_dict(orient='records'),
        'negative_stock_count': int((jefe['conteo_jefe'] < 0).sum()),
        'materials_naming': jefe['material'].value_counts().to_dict(),
        'observations': jefe['observacion'].value_counts().to_dict()
    }
    report['inventario_bodega_jefe'] = jefe_issues

    with open('audit_summary.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print('Audit summary saved successfully to audit_summary.json')

audit_dataset()
