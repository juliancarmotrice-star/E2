import os
import unittest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS_LIMPIOS = os.path.join(BASE_DIR, 'datos_limpios')
SQL_DIR = os.path.join(BASE_DIR, 'sql')

class TestPipelineAndDataIntegrity(unittest.TestCase):
    def test_clean_files_exist(self):
        required_files = [
            'maestro_materiales_clean.csv',
            'maestro_productos_clean.csv',
            'bom_clean.csv',
            'inventario_inicial_clean.csv',
            'movimientos_inventario_clean.csv',
            'ordenes_compra_clean.csv',
            'plan_produccion_clean.csv',
            'conteo_fisico_clean.csv',
            'inventario_bodega_JEFE_clean.csv'
        ]
        for filename in required_files:
            path = os.path.join(DATOS_LIMPIOS, filename)
            self.assertTrue(os.path.exists(path), f"El archivo requerido no existe: {filename}")
            df = pd.read_csv(path)
            self.assertGreater(len(df), 0, f"El archivo {filename} está vacío")

    def test_maestro_materiales_integrity(self):
        path = os.path.join(DATOS_LIMPIOS, 'maestro_materiales_clean.csv')
        df = pd.read_csv(path)
        self.assertEqual(df['sku'].duplicated().sum(), 0, "Existen SKUs duplicados en maestro_materiales_clean")
        self.assertTrue((df['costo_unitario'] > 0).all(), "Existen costos menores o iguales a cero en maestro_materiales_clean")

    def test_sql_scripts_exist(self):
        sql_files = [
            'consultas_analiticas_kpis.sql',
            'supabase_bom_pk.sql',
            'supabase_crear_maestro_productos.sql',
            'supabase_schema_foreign_keys.sql'
        ]
        for sql_file in sql_files:
            path = os.path.join(SQL_DIR, sql_file)
            self.assertTrue(os.path.exists(path), f"Script SQL faltante: {sql_file}")

if __name__ == '__main__':
    unittest.main()
