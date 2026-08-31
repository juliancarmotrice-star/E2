import pandas as pd
import numpy as np
import json

def run_deep_analysis():
    # 1. Cargar fuentes
    mm = pd.read_csv('maestro_materiales.csv')
    mov = pd.read_csv('movimientos_inventario.csv')
    oc = pd.read_csv('ordenes_compra.csv')
    bom = pd.read_csv('bom.csv')
    plan = pd.read_csv('plan_produccion.csv')
    ii = pd.read_csv('inventario_inicial.csv')
    cf = pd.read_csv('conteo_fisico.csv')
    jefe = pd.read_csv('Inventario_bodega_JEFE.csv')

    results = {}

    # -------------------------------------------------------------
    # HIPÓTESIS 1: LEAD TIMES Y DESABASTECIMIENTO DE LÁMINA
    # -------------------------------------------------------------
    oc['fp'] = pd.to_datetime(oc['fecha_pedido'], errors='coerce')
    oc['fprom'] = pd.to_datetime(oc['fecha_promesa'], errors='coerce')
    oc['fr'] = pd.to_datetime(oc['fecha_recepcion'], errors='coerce')
    
    # Corregir temporalmente las 22 fechas con año 2035 -> 2025/2024 para cálculo real
    oc_clean_dates = oc.dropna(subset=['fr', 'fp']).copy()
    mask_2035 = oc_clean_dates['fr'].dt.year == 2035
    oc_clean_dates.loc[mask_2035, 'fr'] = oc_clean_dates.loc[mask_2035].apply(
        lambda r: r['fr'].replace(year=r['fp'].year if (r['fr'].replace(year=r['fp'].year) >= r['fp']) else r['fp'].year + 1), axis=1
    )
    oc_clean_dates['lt_real_corregido'] = (oc_clean_dates['fr'] - oc_clean_dates['fp']).dt.days
    oc_clean_dates['retraso_promesa_corregido'] = (oc_clean_dates['fr'] - oc_clean_dates['fprom']).dt.days

    # Merge con categorías de maestro
    # Normalizar categorías de maestro
    cat_map = {
        'Lamina de acero': 'Lámina', 'lamina': 'Lámina', 'LAMINA AC': 'Lámina', 'Lámina': 'Lámina', 'Lmina': 'Lámina',
        'tornilleria': 'Tornillería', 'Torn.': 'Tornillería', 'Tornillería': 'Tornillería', 'Tornillera': 'Tornillería',
        'Tubería': 'Tubería', 'TUBERIA': 'Tubería', 'tuberia': 'Tubería', 'Tubera': 'Tubería',
        'PINTURA': 'Pintura', 'pintura electrostatica': 'Pintura', 'Pintura': 'Pintura',
        'CORREDERA': 'Correderas', 'Correderas': 'Correderas', 'correderas': 'Correderas',
        'Adhesivos': 'Adhesivos', 'PEGANTE': 'Adhesivos', 'adhesivo': 'Adhesivos',
        'empaque': 'Empaque', 'Empaque': 'Empaque', 'EMPAQUES': 'Empaque',
        'Vidrio': 'Vidrio', 'vidrio': 'Vidrio'
    }
    mm['categoria_norm'] = mm['categoria'].map(cat_map).fillna(mm['categoria'])
    
    oc_merged = oc_clean_dates.merge(mm[['sku', 'categoria_norm', 'lead_time_declarado_dias', 'costo_unitario']], on='sku')
    
    lt_by_cat = oc_merged.groupby('categoria_norm').agg(
        total_pedidos=('orden_compra', 'count'),
        lt_declarado_medio=('lead_time_declarado_dias', 'mean'),
        lt_real_medio=('lt_real_corregido', 'mean'),
        lt_real_mediana=('lt_real_corregido', 'median'),
        lt_real_max=('lt_real_corregido', 'max'),
        retraso_medio=('retraso_promesa_corregido', 'mean'),
        pct_pedidos_tarde=('retraso_promesa_corregido', lambda x: (x > 0).mean() * 100)
    ).to_dict(orient='index')

    results['analisis_lead_time_categorias'] = lt_by_cat

    # -------------------------------------------------------------
    # HIPÓTESIS 2: ROTACIÓN ABC / PLATA MUERTA / COSTO FINANCIERO
    # -------------------------------------------------------------
    # Consumo total histórico valorizado por SKU (salidas en Kardex * costo_unitario)
    mov_clean = mov.copy()
    mov_clean['cantidad_abs'] = mov_clean['cantidad'].abs()
    salidas_sku = mov_clean[mov_clean['tipo_movimiento'] == 'salida'].groupby('sku')['cantidad_abs'].sum().reset_index()
    salidas_sku = salidas_sku.merge(mm[['sku', 'categoria_norm', 'costo_unitario', 'stock_min', 'stock_max']], on='sku', how='right').fillna({'cantidad_abs': 0})
    salidas_sku['valor_consumo_total'] = salidas_sku['cantidad_abs'] * salidas_sku['costo_unitario']
    salidas_sku = salidas_sku.sort_values(by='valor_consumo_total', ascending=False)
    salidas_sku['consumo_acum_pct'] = (salidas_sku['valor_consumo_total'].cumsum() / salidas_sku['valor_consumo_total'].sum()) * 100

    def assign_abc(pct):
        if pct <= 80:
            return 'A'
        elif pct <= 95:
            return 'B'
        else:
            return 'C'

    salidas_sku['clasificacion_abc'] = salidas_sku['consumo_acum_pct'].apply(assign_abc)
    abc_counts = salidas_sku['clasificacion_abc'].value_counts().to_dict()
    abc_valor = salidas_sku.groupby('clasificacion_abc')['valor_consumo_total'].sum().to_dict()

    # Inventario promedio y dinero inmovilizado
    # Reconciliación de saldo final Kardex
    entradas_sku = mov_clean[mov_clean['tipo_movimiento'] == 'entrada'].groupby('sku')['cantidad_abs'].sum()
    ajustes_sku = mov_clean[mov_clean['tipo_movimiento'] == 'ajuste'].groupby('sku')['cantidad'].sum()
    
    stock_df = ii[['sku', 'stock_inicial']].merge(entradas_sku.rename('entradas'), on='sku', how='left').fillna(0)
    stock_df = stock_df.merge(salidas_sku[['sku', 'cantidad_abs', 'costo_unitario', 'clasificacion_abc', 'categoria_norm']].rename(columns={'cantidad_abs': 'salidas'}), on='sku', how='left').fillna(0)
    stock_df = stock_df.merge(ajustes_sku.rename('ajustes'), on='sku', how='left').fillna(0)
    stock_df['saldo_final_kardex'] = stock_df['stock_inicial'] + stock_df['entradas'] - stock_df['salidas'] + stock_df['ajustes']
    stock_df['valor_inventario_final'] = stock_df['saldo_final_kardex'] * stock_df['costo_unitario']
    stock_df['costo_mantenimiento_anual_H'] = stock_df['valor_inventario_final'] * 0.25

    # SKUs sin movimiento (plata muerta) o con rotación casi nula
    plata_muerta = stock_df[(stock_df['salidas'] == 0) | (stock_df['clasificacion_abc'] == 'C')]
    
    results['analisis_abc_rotacion'] = {
        'distribucion_skus': abc_counts,
        'valor_consumo_por_clase': abc_valor,
        'valor_total_inventario_final': float(stock_df['valor_inventario_final'].sum()),
        'costo_anual_mantenimiento_total_H': float(stock_df['costo_mantenimiento_anual_H'].sum()),
        'skus_sin_salidas_total': int((stock_df['salidas'] == 0).sum()),
        'plata_muerta_clase_C_valor_stock': float(stock_df[stock_df['clasificacion_abc'] == 'C']['valor_inventario_final'].sum()),
        'plata_muerta_clase_C_costo_H': float(stock_df[stock_df['clasificacion_abc'] == 'C']['costo_mantenimiento_anual_H'].sum())
    }

    # -------------------------------------------------------------
    # HIPÓTESIS 4: VARIABILIDAD DE DEMANDA Y EXPLOSIÓN BOM
    # -------------------------------------------------------------
    # Demanda por producto terminado
    plan_prod = plan.groupby('producto').agg(
        nombre=('nombre_producto', 'first'),
        media_planeada=('cantidad_planeada', 'mean'),
        std_planeada=('cantidad_planeada', 'std'),
        media_real=('cantidad_real', 'mean'),
        std_real=('cantidad_real', 'std'),
        total_planeada=('cantidad_planeada', 'sum'),
        total_real=('cantidad_real', 'sum')
    )
    plan_prod['cv_real'] = (plan_prod['std_real'] / plan_prod['media_real'])
    
    # Explosión de materiales requeridos vs compras realizadas
    # Cada mes: cantidad_real * bom['cantidad_por_unidad']
    plan_bom = plan.merge(bom, on='producto', suffixes=('_plan', '_bom'))
    plan_bom['consumo_requerido'] = plan_bom['cantidad_real'] * plan_bom['cantidad_por_unidad']
    consumo_mensual_mp = plan_bom.groupby(['periodo', 'sku_material'])['consumo_requerido'].sum().reset_index()

    # Variabilidad de productos (Archivadores y Estanterías)
    results['variabilidad_productos_cv'] = plan_prod[['nombre', 'cv_real', 'total_real']].sort_values(by='cv_real', ascending=False).to_dict(orient='index')

    with open('deep_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Deep analysis finished successfully.")

run_deep_analysis()
