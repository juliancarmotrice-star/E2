"""
Script de Carga de Datos Limpios a Supabase (Producción 4.0 - E2 SAS)
Maneja tipos de datos, batches de inserción y lectura de claves desde .env
"""

import os
import json
import urllib.request
import pandas as pd
import numpy as np
from datetime import datetime

# Configuración de rutas
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR) if os.path.basename(CURRENT_DIR) in ['python', 'src', 'scripts'] else CURRENT_DIR
CLEAN_DIR = os.path.join(BASE_DIR, 'datos_limpios')

# Cargar variables de entorno desde .env
def load_env():
    env_vars = {}
    env_path = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars

ENV = load_env()
SUPABASE_URL = ENV.get('SUPABASE_URL', 'https://hfiembmfzvkrfyhfbock.supabase.co')
# Prefer service_role key if provided, else fallback to anon key
API_KEY = ENV.get('SUPABASE_SERVICE_ROLE_KEY') or ENV.get('SUPABASE_ANON_KEY')

def get_headers(api_key):
    return {
        'apikey': api_key,
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }

def clean_record(d):
    """Reemplaza NaN y valores no serializables por None o tipos nativos."""
    clean = {}
    for k, v in d.items():
        if pd.isna(v) or v is None:
            clean[k] = None
        elif isinstance(v, (np.integer, int)):
            clean[k] = int(v)
        elif isinstance(v, (np.floating, float)):
            clean[k] = float(v)
        elif isinstance(v, (np.bool_, bool)):
            clean[k] = bool(v)
        else:
            clean[k] = str(v)
    return clean

def insert_batch(table_name, records, api_key, batch_size=500):
    headers = get_headers(api_key)
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    total = len(records)
    inserted = 0

    print(f"\n---> Subiendo a '{table_name}' ({total} registros)...")
    
    for i in range(0, total, batch_size):
        batch = [clean_record(r) for r in records[i:i + batch_size]]
        data_bytes = json.dumps(batch).encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req) as res:
                inserted += len(batch)
                print(f"     Progreso: {inserted}/{total} registros insertados...")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            print(f"     [ERROR] Falló batch {i} a {i+len(batch)} en '{table_name}': HTTP {e.code}")
            print(f"     Detalle del error: {err_body}")
            return False
        except Exception as e:
            print(f"     [ERROR] Excepción inesperada: {e}")
            return False

    print(f"  [OK] '{table_name}' completada exitosamente ({inserted} registros).")
    return True

def run_upload():
    print("==================================================")
    print("  INICIANDO CARGA DE DATOS A SUPABASE")
    print(f"  Destino: {SUPABASE_URL}")
    print(f"  Autenticación: {'SERVICE_ROLE' if 'SUPABASE_SERVICE_ROLE_KEY' in ENV else 'ANON_KEY'}")
    print("==================================================")

    # 1. Maestro de Materiales
    df_mm = pd.read_csv(os.path.join(CLEAN_DIR, 'maestro_materiales_clean.csv'))
    mm_records = df_mm.to_dict(orient='records')
    if not insert_batch('maestro_materiales', mm_records, API_KEY):
        return

    # 2. Inventario Inicial
    df_ii = pd.read_csv(os.path.join(CLEAN_DIR, 'inventario_inicial_clean.csv'))
    ii_records = df_ii.to_dict(orient='records')
    if not insert_batch('inventario_inicial', ii_records, API_KEY):
        return

    # 3. Conteo Físico
    df_cf = pd.read_csv(os.path.join(CLEAN_DIR, 'conteo_fisico_clean.csv'))
    cf_records = df_cf[['sku', 'stock_fisico_contado', 'fecha_conteo']].to_dict(orient='records')
    if not insert_batch('conteo_fisico', cf_records, API_KEY):
        return

    # 4. Inventario Bodega JEFE
    df_jefe = pd.read_csv(os.path.join(CLEAN_DIR, 'inventario_bodega_JEFE_clean.csv'))
    # Columnas originales en la tabla: material, codigo, conteo_jefe, observacion
    jefe_records = df_jefe.copy()
    jefe_records['conteo_jefe'] = jefe_records['conteo_jefe_limpio']
    jefe_records = jefe_records[['material', 'codigo', 'conteo_jefe', 'observacion']].to_dict(orient='records')
    if not insert_batch('inventario_bodega_JEFE', jefe_records, API_KEY):
        return

    # 5. BOM (Bill of Materials)
    df_bom = pd.read_csv(os.path.join(CLEAN_DIR, 'bom_clean.csv'))
    bom_cols = [c for c in ['producto', 'nombre_producto', 'sku_material', 'cantidad_por_unidad', 'unidad'] if c in df_bom.columns]
    bom_records = df_bom[bom_cols].to_dict(orient='records')
    if not insert_batch('bom', bom_records, API_KEY):
        return

    # 6. Plan de Producción
    df_plan = pd.read_csv(os.path.join(CLEAN_DIR, 'plan_produccion_clean.csv'))
    plan_records = df_plan.to_dict(orient='records')
    if not insert_batch('plan_produccion', plan_records, API_KEY):
        return

    # 7. Órdenes de Compra
    df_oc = pd.read_csv(os.path.join(CLEAN_DIR, 'ordenes_compra_clean.csv'))
    oc_records = df_oc.to_dict(orient='records')
    if not insert_batch('ordenes_compra', oc_records, API_KEY):
        return

    # 8. Movimientos de Inventarios (Kardex - 15.545 filas)
    df_mov = pd.read_csv(os.path.join(CLEAN_DIR, 'movimientos_inventario_clean.csv'))
    mov_records = df_mov.to_dict(orient='records')
    if not insert_batch('movimientos_inventarios', mov_records, API_KEY):
        return

    print("\n==================================================")
    print("  ¡TODAS LAS TABLAS FUERON CARGADAS CON ÉXITO!")
    print("==================================================")

if __name__ == '__main__':
    run_upload()
