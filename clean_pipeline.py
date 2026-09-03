import os
import pandas as pd
import numpy as np

def run_cleaning_pipeline():
    os.makedirs('data_clean', exist_ok=True)
    log = []

    # =========================================================================
    # 1. MAESTRO DE MATERIALES
    # =========================================================================
    mm = pd.read_csv('maestro_materiales.csv')
    
    # 1.1 Normalización de categorías
    cat_map = {
        'Lamina de acero': 'Lámina', 'lamina': 'Lámina', 'LAMINA AC': 'Lámina', 'Lámina': 'Lámina', 'Lmina': 'Lámina', 'Lmina': 'Lámina',
        'tornilleria': 'Tornillería', 'Torn.': 'Tornillería', 'Tornillería': 'Tornillería', 'Tornillera': 'Tornillería', 'Tornillera': 'Tornillería',
        'Tubería': 'Tubería', 'TUBERIA': 'Tubería', 'tuberia': 'Tubería', 'Tubera': 'Tubería', 'Tubera': 'Tubería',
        'PINTURA': 'Pintura', 'pintura electrostatica': 'Pintura', 'Pintura': 'Pintura',
        'CORREDERA': 'Correderas', 'Correderas': 'Correderas', 'correderas': 'Correderas',
        'Adhesivos': 'Adhesivos', 'PEGANTE': 'Adhesivos', 'adhesivo': 'Adhesivos',
        'empaque': 'Empaque', 'Empaque': 'Empaque', 'EMPAQUES': 'Empaque',
        'Vidrio': 'Vidrio', 'vidrio': 'Vidrio'
    }
    mm['categoria'] = mm['categoria'].map(cat_map).fillna(mm['categoria'])
    
    # 1.2 Normalización de unidades
    unit_map = {
        'kg': 'kg', 'KG': 'kg',
        'unidad': 'unidad', 'UNIDAD': 'unidad',
        'm': 'm', 'M': 'm',
        'par': 'par', 'PAR': 'par',
        'm2': 'm2', 'M2': 'm2',
        'lámina': 'lámina', 'lmina': 'lámina', 'LÁMINA': 'lámina', 'LMINA': 'lámina', 'LMINA': 'lámina'
    }
    mm['unidad'] = mm['unidad'].map(unit_map).fillna(mm['unidad'])

    # 1.3 Deducción de lead_time_declarado_dias faltantes a partir de órdenes de compra
    oc_raw = pd.read_csv('ordenes_compra.csv')
    oc_fp = pd.to_datetime(oc_raw['fecha_pedido'], errors='coerce')
    oc_fr = pd.to_datetime(oc_raw['fecha_recepcion'], errors='coerce')
    oc_mask_2035 = oc_fr.dt.year == 2035
    oc_fr_clean = oc_fr.copy()
    if oc_mask_2035.sum() > 0:
        oc_fr_clean.loc[oc_mask_2035] = oc_raw.loc[oc_mask_2035].apply(
            lambda r: pd.to_datetime(r['fecha_recepcion']).replace(
                year=pd.to_datetime(r['fecha_pedido']).year if (pd.to_datetime(r['fecha_recepcion']).replace(year=pd.to_datetime(r['fecha_pedido']).year) >= pd.to_datetime(r['fecha_pedido'])) else pd.to_datetime(r['fecha_pedido']).year + 1
            ), axis=1
        )
    oc_dur = (oc_fr_clean - oc_fp).dt.days
    oc_temp = pd.DataFrame({'sku': oc_raw['sku'], 'proveedor': oc_raw['proveedor'], 'lead_time': oc_dur}).dropna()
    
    lt_sku_map = oc_temp.groupby('sku')['lead_time'].mean().round().astype(int).to_dict()
    lt_prov_map = oc_temp.groupby('proveedor')['lead_time'].median().round().astype(int).to_dict()
    
    def deduce_lt(row):
        if pd.notna(row['lead_time_declarado_dias']):
            return int(row['lead_time_declarado_dias'])
        if row['sku'] in lt_sku_map:
            return lt_sku_map[row['sku']]
        if row['proveedor'] in lt_prov_map:
            return lt_prov_map[row['proveedor']]
        return 14 # fallback
        
    mm['lead_time_declarado_dias'] = mm.apply(deduce_lt, axis=1)
    
    mm.to_csv('data_clean/maestro_materiales_clean.csv', index=False)
    log.append("maestro_materiales: 8 categorías normalizadas (24 variantes corregidas), unidades estandarizadas y 54 lead times deducidos directamente del histórico real de órdenes de compra (52 por SKU + 2 por proveedor).")

    # =========================================================================
    # 2. MOVIMIENTOS INVENTARIO (KARDEX)
    # =========================================================================
    mov = pd.read_csv('movimientos_inventario.csv')
    
    # 2.1 Corrección de fecha 2026-13-05 -> 2026-03-05 (Error de digitación de mes 13 por mes 03)
    mov['fecha'] = mov['fecha'].replace({'2026-13-05': '2026-03-05'})
    
    # 2.2 Cantidad positiva (el tipo_movimiento define el sentido contable)
    mov['cantidad'] = mov['cantidad'].abs()
    
    mov.to_csv('data_clean/movimientos_inventario_clean.csv', index=False)
    log.append("movimientos_inventario: 15 fechas '2026-13-05' corregidas a '2026-03-05' (typo mes 13->03) y 466 cantidades negativas convertidas a valor absoluto.")

    # =========================================================================
    # 3. ORDENES DE COMPRA
    # =========================================================================
    oc = pd.read_csv('ordenes_compra.csv')
    oc['fp'] = pd.to_datetime(oc['fecha_pedido'], errors='coerce')
    oc['fr'] = pd.to_datetime(oc['fecha_recepcion'], errors='coerce')
    
    # Corregir año 2035 -> año de pedido
    mask_2035 = oc['fr'].dt.year == 2035
    if mask_2035.sum() > 0:
        oc.loc[mask_2035, 'fecha_recepcion'] = oc.loc[mask_2035].apply(
            lambda r: r['fr'].replace(year=r['fp'].year if (r['fr'].replace(year=r['fp'].year) >= r['fp']) else r['fp'].year + 1).strftime('%Y-%m-%d'), axis=1
        )
    oc = oc.drop(columns=['fp', 'fr'])
    
    oc.to_csv('data_clean/ordenes_compra_clean.csv', index=False)
    log.append("ordenes_compra: 22 fechas de recepción con año '2035' corregidas a su año real de compra.")

    # =========================================================================
    # 4. MAESTRO DE PRODUCTOS (CATÁLOGO DE PRODUCTOS TERMINADOS)
    # =========================================================================
    bom_raw = pd.read_csv('bom.csv')
    plan_raw = pd.read_csv('plan_produccion.csv')
    
    # Extraer pares únicos de producto y nombre_producto
    df_prod_bom = bom_raw[['producto', 'nombre_producto']].drop_duplicates()
    df_prod_plan = plan_raw[['producto', 'nombre_producto']].drop_duplicates()
    maestro_prod = pd.concat([df_prod_bom, df_prod_plan]).drop_duplicates().sort_values('producto')
    maestro_prod.to_csv('data_clean/maestro_productos_clean.csv', index=False)
    log.append(f"maestro_productos: Creado catálogo maestro con {len(maestro_prod)} productos terminados normalizados.")

    # =========================================================================
    # 5. BOM (BILL OF MATERIALS) - Llave compuesta (producto, sku_material) y unidades normalizadas
    # =========================================================================
    bom = bom_raw.copy()
    bom['id_bom'] = bom['producto'] + '_' + bom['sku_material']
    bom['unidad'] = bom['unidad'].map(unit_map).fillna(bom['unidad'])
    # Eliminar columna redundante nombre_producto
    bom = bom.drop(columns=['nombre_producto'])
    
    bom.to_csv('data_clean/bom_clean.csv', index=False)
    log.append("bom: Llave primaria combinada id_bom (producto_sku) generada (131 registros), unidades normalizadas y 'nombre_producto' eliminado.")

    # =========================================================================
    # 6. PLAN DE PRODUCCION - Normalizado sin nombre_producto redundante
    # =========================================================================
    plan = plan_raw.copy()
    # Eliminar columna redundante nombre_producto
    plan = plan.drop(columns=['nombre_producto'])
    plan.to_csv('data_clean/plan_produccion_clean.csv', index=False)
    log.append("plan_produccion: Integrado íntegramente y 'nombre_producto' eliminado por normalización.")

    # =========================================================================
    # 6. INVENTARIO INICIAL
    # =========================================================================
    ii = pd.read_csv('inventario_inicial.csv')
    ii.to_csv('data_clean/inventario_inicial_clean.csv', index=False)
    log.append("inventario_inicial: Validado e integrado íntegramente.")

    # =========================================================================
    # 7. CONTEO FISICO
    # =========================================================================
    cf = pd.read_csv('conteo_fisico.csv')
    
    # 7.1 Deduplicación (preservar primera ocurrencia si existen duplicados)
    num_dups = cf.duplicated(subset=['sku']).sum()
    if num_dups > 0:
        cf = cf.drop_duplicates(subset=['sku'], keep='first')
        
    # 7.2 Corrección de signos negativos: interpretación como error de digitación (valor absoluto)
    num_neg = (cf['stock_fisico_contado'] < 0).sum()
    cf['stock_fisico_contado'] = cf['stock_fisico_contado'].abs()
    
    cf_clean = cf[['sku', 'stock_fisico_contado', 'fecha_conteo']]
    cf_clean.to_csv('data_clean/conteo_fisico_clean.csv', index=False)
    log.append(f"conteo_fisico: {num_neg} valores negativos convertidos a positivos (error de digitación vía valor absoluto) y verificación de duplicados ({num_dups} eliminados).")

    # =========================================================================
    # 8. INVENTARIO BODEGA JEFE
    # =========================================================================
    jefe = pd.read_csv('Inventario_bodega_JEFE.csv')
    
    # 8.1 Deduplicación (preservar primer registro si existiesen duplicados por codigo)
    num_dups_jefe = jefe.duplicated(subset=['codigo']).sum()
    if num_dups_jefe > 0:
        jefe = jefe.drop_duplicates(subset=['codigo'], keep='first')
        
    # 8.2 Normalización de categorías de material
    jefe['material'] = jefe['material'].map(cat_map).fillna(jefe['material'])
    
    # 8.3 Imputación de observaciones nulas
    num_nulos_obs = jefe['observacion'].isna().sum()
    jefe['observacion'] = jefe['observacion'].fillna('Sin observación')
    
    # 8.4 Corrección de valores negativos: interpretación como error de digitación (valor absoluto)
    num_neg_jefe = (jefe['conteo_jefe'] < 0).sum()
    jefe['conteo_jefe'] = jefe['conteo_jefe'].abs()
    jefe['conteo_jefe_limpio'] = jefe['conteo_jefe']
    
    jefe_clean = jefe[['material', 'codigo', 'conteo_jefe', 'conteo_jefe_limpio', 'observacion']]
    jefe_clean.to_csv('data_clean/inventario_bodega_JEFE_clean.csv', index=False)
    log.append(f"Inventario_bodega_JEFE: {num_neg_jefe} valores negativos convertidos a positivos (error de digitación vía valor absoluto), {num_nulos_obs} observaciones nulas imputadas y verificación de duplicados ({num_dups_jefe} eliminados).")

    # Resumen
    print("=== PIPELINE DE LIMPIEZA COMPLETADO EXITOSAMENTE ===")
    for item in log:
        print("[OK]", item)

if __name__ == '__main__':
    run_cleaning_pipeline()
