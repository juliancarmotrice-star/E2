import pandas as pd
import numpy as np

# Load clean datasets
mm = pd.read_csv('datos_limpios/maestro_materiales_clean.csv')
ii = pd.read_csv('datos_limpios/inventario_inicial_clean.csv')
mov = pd.read_csv('datos_limpios/movimientos_inventario_clean.csv')
cf = pd.read_csv('datos_limpios/conteo_fisico_clean.csv')
bj = pd.read_csv('datos_limpios/inventario_bodega_JEFE_clean.csv')
oc = pd.read_csv('datos_limpios/ordenes_compra_clean.csv')
bom = pd.read_csv('datos_limpios/bom_clean.csv')

# Load raw datasets
mm_raw = pd.read_csv('datos_iniciales/maestro_materiales.csv')
ii_raw = pd.read_csv('datos_iniciales/inventario_inicial.csv')
mov_raw = pd.read_csv('datos_iniciales/movimientos_inventario.csv')
cf_raw = pd.read_csv('datos_iniciales/conteo_fisico.csv')
bj_raw = pd.read_csv('datos_iniciales/Inventario_bodega_JEFE.csv')

print("="*70)
print("INVESTIGACIÓN PROFUNDA DE ERI / IRA (¿Por qué 75% vs 67.14% vs 0%?)")
print("="*70)

# Filter out duplicate / dummy SKUs (MP-9xxx)
valid_mm = mm[~mm['sku'].str.startswith('MP-9') & ~mm['descripcion'].str.contains(r'\(dup\)', regex=True)].copy()
print(f"Total SKUs válidos en maestro_materiales: {len(valid_mm)}")

# Kardex calculation in clean data
mov_clean_sum = mov.groupby(['sku', 'tipo_movimiento'])['cantidad'].sum().unstack(fill_value=0).reset_index()
for col in ['entrada', 'salida', 'ajuste']:
    if col not in mov_clean_sum.columns:
        mov_clean_sum[col] = 0

df = valid_mm[['sku', 'categoria', 'costo_unitario']].merge(ii[['sku', 'stock_inicial']], on='sku', how='left')
df = df.merge(mov_clean_sum, on='sku', how='left').fillna(0)
df['stock_kardex'] = df['stock_inicial'] + df['entrada'] - df['salida'] + df['ajuste']
df = df.merge(cf[['sku', 'stock_fisico_contado']], on='sku', how='left')
df = df.merge(bj[['codigo', 'conteo_jefe']].rename(columns={'codigo': 'sku'}), on='sku', how='left')

df['diff_kardex_fisico'] = df['stock_fisico_contado'] - df['stock_kardex']
df['abs_diff_kardex_fisico'] = df['diff_kardex_fisico'].abs()
df['diff_dinero'] = df['abs_diff_kardex_fisico'] * df['costo_unitario']

print("\n--- 1. RESULTADOS BASE DE NUESTRO CÁLCULO ---")
exactos_global = (df['abs_diff_kardex_fisico'] == 0).sum()
print(f"Global exactos (diff == 0): {exactos_global} de {len(df)} = {exactos_global/len(df)*100:.2f}% (67.14%)")

activos = df[df['salida'] > 0]
inactivos = df[df['salida'] == 0]
exactos_activos = (activos['abs_diff_kardex_fisico'] == 0).sum()
exactos_inactivos = (inactivos['abs_diff_kardex_fisico'] == 0).sum()

print(f"SKUs Activos (con salidas): {len(activos)} SKUs. Exactos: {exactos_activos} = {exactos_activos/len(activos)*100:.2f}%")
print(f"SKUs Inactivos (sin salidas): {len(inactivos)} SKUs. Exactos: {exactos_inactivos} = {exactos_inactivos/len(inactivos)*100:.2f}% (282/301)")
print(f"Inactivos descuadrados: {len(inactivos) - exactos_inactivos} SKUs (19 SKUs sin movimiento que cambiaron de saldo)")

print("\n--- 2. HIPÓTESIS MATEMÁTICAS / OPERACIONALES PARA OBTENER ~75% ---")

# Hipótesis 1: ¿Qué pasa si el profesor calculó ERI sobre los 400 SKUs iniciales (excluyendo 20 creados o especiales)?
# 282 / 400 = 70.5%, 300 / 400 = 75.0%
print(f"H1a. 301 / 400 = {301/400*100:.2f}%")
print(f"H1b. 315 / 420 = {315/420*100:.2f}% (exactamente 75%)")

# Hipótesis 2: Tolerancia de unidades (margen de error aceptable en conteo físico)
for tol in [1, 2, 5, 10, 20, 50]:
    con_tol = (df['abs_diff_kardex_fisico'] <= tol).sum()
    print(f"H2. Con tolerancia de ±{tol} unidades: {con_tol}/{len(df)} = {con_tol/len(df)*100:.2f}%")

# Hipótesis 3: Tolerancia porcentual (|kardex - fisico| / max(kardex, fisico) <= tol%)
for pct in [0.01, 0.02, 0.05, 0.10, 0.15, 0.20]:
    # avoid div by zero
    denom = df[['stock_kardex', 'stock_fisico_contado']].abs().max(axis=1)
    denom = denom.replace(0, 1)
    rel_err = df['abs_diff_kardex_fisico'] / denom
    con_tol_pct = (rel_err <= pct).sum()
    print(f"H3. Con tolerancia porcentual de ±{pct*100:.0f}%: {con_tol_pct}/{len(df)} = {con_tol_pct/len(df)*100:.2f}%")

# Hipótesis 4: ¿Qué pasa con los datos CRUDOS (RAW) sin limpiar?
# In raw mov, how is it calculated?
mov_raw_valid = mov_raw[mov_raw['sku'].isin(valid_mm['sku'])].copy()
mov_raw_sum = mov_raw_valid.groupby(['sku', 'tipo_movimiento'])['cantidad'].sum().unstack(fill_value=0).reset_index()
for col in ['entrada', 'salida', 'ajuste']:
    if col not in mov_raw_sum.columns:
        mov_raw_sum[col] = 0

df_raw = valid_mm[['sku', 'categoria', 'costo_unitario']].merge(ii_raw[['sku', 'stock_inicial']], on='sku', how='left')
df_raw = df_raw.merge(mov_raw_sum, on='sku', how='left').fillna(0)
df_raw['stock_kardex_raw'] = df_raw['stock_inicial'] + df_raw['entrada'] - df_raw['salida'] + df_raw['ajuste']
df_raw = df_raw.merge(cf_raw[['sku', 'stock_fisico_contado']], on='sku', how='left')
exactos_raw = (df_raw['stock_kardex_raw'] == df_raw['stock_fisico_contado']).sum()
print(f"\nH4. Kardex RAW (sin limpiar negativos ni formatos) == Conteo Físico: {exactos_raw}/{len(df_raw)} = {exactos_raw/len(df_raw)*100:.2f}%")

# Hipótesis 5: ¿Qué pasa si sólo se toman Entradas de Órdenes de Compra (OC entregadas) en lugar del archivo movimientos_inventario?
oc_entregadas = oc[oc['fecha_recepcion'].notna()].groupby('sku')['cantidad'].sum().reset_index().rename(columns={'cantidad': 'oc_recibidas'})
df_oc = valid_mm[['sku']].merge(ii[['sku', 'stock_inicial']], on='sku', how='left')
df_oc = df_oc.merge(oc_entregadas, on='sku', how='left').fillna(0)
df_oc = df_oc.merge(mov_clean_sum[['sku', 'salida']], on='sku', how='left').fillna(0)
df_oc['stock_kardex_oc'] = df_oc['stock_inicial'] + df_oc['oc_recibidas'] - df_oc['salida']
df_oc = df_oc.merge(cf[['sku', 'stock_fisico_contado']], on='sku', how='left')
exactos_oc = (df_oc['stock_kardex_oc'] == df_oc['stock_fisico_contado']).sum()
print(f"H5. Kardex usando OC entregadas: {exactos_oc}/{len(df_oc)} = {exactos_oc/len(df_oc)*100:.2f}%")

# Hipótesis 6: ¿Qué pasa si la métrica de exactitud es Agregada (Volumétrica o Financiera) en lugar de SKU por SKU?
# ERI Volumétrico = 1 - (Sum|Kardex - Fisico| / Sum(Fisico))
sum_fisico = df['stock_fisico_contado'].sum()
sum_kardex = df['stock_kardex'].sum()
sum_abs_diff = df['abs_diff_kardex_fisico'].sum()
eri_volumetrico_1 = 1 - (sum_abs_diff / sum_fisico)
eri_volumetrico_2 = min(sum_kardex, sum_fisico) / max(sum_kardex, sum_fisico)

print(f"\nH6a. ERI Volumétrico Global: sum_fisico={sum_fisico:,.0f}, sum_kardex={sum_kardex:,.0f}, sum_abs_diff={sum_abs_diff:,.0f}")
print(f"     ERI Volumétrico (1 - Error/Total): {eri_volumetrico_1*100:.2f}%")
print(f"     ERI Volumétrico Ratio: {eri_volumetrico_2*100:.2f}%")

# Category breakdown
print("\n--- 3. ERI EXACTITUD POR CATEGORÍA DE MATERIAL (Kardex == Conteo Físico) ---")
for cat, grp in df.groupby('categoria'):
    exact = (grp['abs_diff_kardex_fisico'] == 0).sum()
    pct = exact / len(grp) * 100
    print(f"  - {cat:25s}: {exact:3d} / {len(grp):3d} = {pct:6.2f}%")

# Let's inspect the 19 inactives with discrepancies
print("\n--- 4. LOS 19 SKUS INACTIVOS CON DISCREPANCIA ---")
inactivos_desc = inactivos[inactivos['abs_diff_kardex_fisico'] > 0][['sku', 'categoria', 'stock_inicial', 'stock_kardex', 'stock_fisico_contado', 'diff_kardex_fisico', 'conteo_jefe']]
print(inactivos_desc.to_string())

# Let's inspect why someone might get ~75%:
# If someone assumed all 301 inactive SKUs were exact because they had no movement (301/420 = 71.67%)
# plus some SKUs within a 5-10% tolerance or rounding: 315 / 420 = 75.00% (or 311/420 = 74.05% with 10% tol)
# Or if someone calculated: 301 / 400 = 75.25% (assuming 400 total valid SKUs)

