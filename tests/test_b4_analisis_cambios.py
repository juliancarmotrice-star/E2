import unittest
import pandas as pd
import nucleo.analisis_cambios as cambios


class TestB4AnalisisCambiosEIngesta(unittest.TestCase):
    """
    Pruebas unitarias de las directivas B4_02:
    - Auditoría de cambios post-limpieza
    - Protocolo de ingesta en 5 pasos (validar, normalizar, reportar, escribir)
    - Verificación de idempotencia y carga acumulativa
    - Instrumentación y telemetría autónoma
    """

    def test_auditoria_cambios_detallados(self):
        auditoria = cambios.auditar_cambios_detallados()
        self.assertIn('total_errores_corregidos', auditoria)
        self.assertGreaterEqual(auditoria['total_errores_corregidos'], 700)
        self.assertIn('maestro_materiales', auditoria['resumen_por_tabla'])
        self.assertIn('movimientos_inventarios', auditoria['resumen_por_tabla'])
        self.assertIn('ordenes_compra', auditoria['resumen_por_tabla'])

    def test_ingesta_5_pasos_rechazo_columnas(self):
        # Archivo inválido sin columnas requeridas
        df_invalido = pd.DataFrame([{'col_falsa': 123}])
        res = cambios.ejecutar_ingesta_5_pasos('maestro_materiales', df_invalido, 'test_invalido.csv')
        self.assertFalse(res['exito'])
        self.assertEqual(res['paso_fallido'], 'VALIDAR')
        self.assertEqual(res['filas_cargadas'], 0)

    def test_contraste_cruzado_maestro_en_ordenes(self):
        # Simular intento de cargar Maestro de Materiales en Órdenes de Compra
        df_maestro = pd.DataFrame([
            {'sku': 'MP-0001', 'descripcion': 'Lámina Cold Rolled', 'categoria': 'Lámina', 'unidad': 'lámina', 'costo_unitario': 150000}
        ])
        res = cambios.ejecutar_ingesta_5_pasos(
            tabla_destino='ordenes_compra',
            df_entrante=df_maestro,
            nombre_archivo='test_maestro_en_ordenes.csv'
        )
        # Debe fallar el contraste y no agregar filas
        self.assertFalse(res['exito'])
        self.assertTrue(res.get('contraste_fallido'))
        self.assertEqual(res['filas_cargadas'], 0)
        self.assertEqual(res['filas_rechazadas'], 1)
        self.assertIn('Error de contraste', res['mensaje'])
        self.assertIn('Maestro de Materiales', res['tipo_detectado'])

    def test_ingesta_5_pasos_reporte_cuentas(self):
        # Lote de prueba con datos para normalizar
        df_test = pd.DataFrame([
            {'sku': 'MP-TEST1', 'descripcion': 'Lámina Test', 'categoria': 'lamina', 'unidad': 'KG', 'costo_unitario': 10000},
            {'sku': 'MP-TEST2', 'descripcion': 'Tornillo Test', 'categoria': 'tornilleria', 'unidad': 'UNIDAD', 'costo_unitario': 150}
        ])
        res = cambios.ejecutar_ingesta_5_pasos('maestro_materiales', df_test, 'test_valido.csv')
        self.assertTrue(res['exito'])
        self.assertEqual(res['reporte']['filas_leidas'], 2)
        self.assertEqual(res['reporte']['filas_cargadas'], 2)
        self.assertEqual(res['reporte']['filas_rechazadas'], 0)
        # Verificar normalización
        datos_norm = res['datos_listos_para_base']
        self.assertEqual(datos_norm[0]['categoria'], 'Lámina')
        self.assertEqual(datos_norm[0]['unidad'], 'kg')
        self.assertEqual(datos_norm[1]['categoria'], 'Tornillería')
        self.assertEqual(datos_norm[1]['unidad'], 'unidad')

    def test_idempotencia_y_acumulacion(self):
        resultado = cambios.simular_prueba_idempotencia_acumulativa('maestro_materiales')
        self.assertTrue(resultado['prueba_idempotencia']['pasa_idempotencia'])
        self.assertTrue(resultado['prueba_acumulativa']['pasa_acumulativo'])

    def test_telemetria_instrumentacion(self):
        telemetria = cambios.obtener_telemetria_instrumentacion()
        self.assertIn('instrumento_1_carga', telemetria)
        self.assertIn('instrumento_2_corrida', telemetria)
        self.assertIn('instrumento_3_paradas', telemetria)
        self.assertIn('instrumento_4_decision', telemetria)
        self.assertIn('instrumento_5_costo', telemetria)

    def test_rechazo_archivo_vacio(self):
        # Archivo vacío sin filas no puede ser cargado
        df_vacio = pd.DataFrame()
        res = cambios.ejecutar_ingesta_5_pasos('maestro_materiales', df_vacio, 'test_archivo_vacio.csv')
        self.assertFalse(res['exito'])
        self.assertEqual(res['paso_fallido'], 'VALIDAR')
        self.assertEqual(res['filas_cargadas'], 0)
        self.assertIn('vacío', res['mensaje'].lower())

    def test_rechazo_hoja_incorrecta_especifica(self):
        # Intentar cargar estructura de movimientos_inventarios en la hoja específica de maestro_materiales
        df_mov = pd.DataFrame([
            {'fecha': '2026-03-01', 'sku': 'MP-0001', 'tipo_movimiento': 'entrada', 'cantidad': 100, 'documento': 'DOC-123', 'bodega': 'BOD-01', 'responsable': 'OP-01'}
        ])
        res = cambios.ejecutar_ingesta_5_pasos('maestro_materiales', df_mov, 'test_movimientos_hoja_incorrecta.csv')
        self.assertFalse(res['exito'])
        self.assertTrue(res.get('contraste_fallido'))
        self.assertEqual(res['filas_cargadas'], 0)
        self.assertIn('hoja', res['mensaje'].lower())

    def test_rechazo_idempotencia_hoja_ya_cargada(self):
        # Cargar un lote que ya existe en el dataset debe ser DENEGADO por idempotencia
        p_clean = cambios.obtener_ruta_limpia('maestro_materiales_clean.csv')
        df_existente = pd.read_csv(p_clean).head(5)
        res = cambios.ejecutar_ingesta_5_pasos('maestro_materiales', df_existente, 'test_maestro_ya_cargado.csv', modo_idempotente=True)
        self.assertFalse(res['exito'])
        self.assertTrue(res.get('denegada_por_idempotencia'))
        self.assertEqual(res['paso_fallido'], 'IDEMPOTENCIA')
        self.assertEqual(res['filas_cargadas'], 0)
        self.assertIn('idempotencia', res['mensaje'].lower())

    def test_ingesta_no_duplicada_ejecuta_modulo_limpieza(self):
        # Cuando se carga un CSV con SKUs nuevos (no duplicados) y datos sucios (ej. categorías y unidades no estándar, costo negativo),
        # el modelo debe ejecutar el módulo de limpieza, sanear los valores y registrar las correcciones.
        df_sucio_nuevo = pd.DataFrame([
            {
                'sku': 'MP-NUEVO-9999',
                'descripcion': 'Lámina galvanizada calibre 18',
                'categoria': 'Lamina de acero',  # Variante sucia
                'unidad': 'KG',  # Unidad en mayúsculas
                'costo_unitario': -12500,  # Negativo
                'lead_time_declarado_dias': None  # Nulo
            }
        ])
        res = cambios.ejecutar_ingesta_5_pasos(
            tabla_destino='maestro_materiales',
            df_entrante=df_sucio_nuevo,
            nombre_archivo='test_nuevo_material_sucio.csv',
            modo_idempotente=True,
            persistir_en_bd=False
        )
        self.assertTrue(res['exito'])
        self.assertEqual(res['filas_cargadas'], 1)
        self.assertEqual(res['filas_duplicadas'], 0)

        # Verificar que el módulo de limpieza saneó los datos
        datos_listos = res['datos_listos_para_base']
        self.assertEqual(len(datos_listos), 1)
        registro_limpio = datos_listos[0]
        self.assertEqual(registro_limpio['categoria'], 'Lámina')
        self.assertEqual(registro_limpio['unidad'], 'kg')
        self.assertEqual(registro_limpio['costo_unitario'], 12500)
        self.assertEqual(registro_limpio['lead_time_declarado_dias'], 14)

        # Verificar reporte de auditoría del módulo de limpieza
        rep = res['reporte']
        self.assertGreater(rep['total_correcciones_limpieza'], 0)
        self.assertTrue(len(rep['transformaciones_limpieza']) > 0)

    def test_conteo_fisico_idempotencia_compuesta(self):
        # Valida que un nuevo conteo físico con fecha posterior para SKUs existentes NO sea bloqueado
        # por idempotencia errónea de solo SKU, sino que sea aceptado por clave compuesta (sku, fecha_conteo).
        df_cf_nuevo = pd.DataFrame([
            {'sku': 'MP-0001', 'stock_fisico_contado': 520, 'fecha_conteo': '2026-08-31'},
            {'sku': 'MP-0002', 'stock_fisico_contado': 1850, 'fecha_conteo': '2026-08-31'}
        ])
        llaves_existentes_marzo = {'MP-0001||2026-03-31', 'MP-0002||2026-03-31'}
        
        # 1. Carga de nuevo conteo en agosto: debe ser EXITOSA (0 duplicados detectados)
        res_nuevo = cambios.ejecutar_ingesta_5_pasos(
            tabla_destino='conteo_fisico',
            df_entrante=df_cf_nuevo,
            nombre_archivo='conteo_fisico_2026-08.csv',
            modo_idempotente=True,
            persistir_en_bd=False,
            llaves_existentes_override=llaves_existentes_marzo
        )
        self.assertTrue(res_nuevo['exito'])
        self.assertEqual(res_nuevo['filas_cargadas'], 2)
        self.assertEqual(res_nuevo['filas_duplicadas'], 0)

        # 2. Recarga del MISMO conteo de agosto: debe ser DENEGADA por idempotencia
        llaves_con_agosto = llaves_existentes_marzo | {'MP-0001||2026-08-31', 'MP-0002||2026-08-31'}
        res_recarga = cambios.ejecutar_ingesta_5_pasos(
            tabla_destino='conteo_fisico',
            df_entrante=df_cf_nuevo,
            nombre_archivo='conteo_fisico_2026-08.csv',
            modo_idempotente=True,
            persistir_en_bd=False,
            llaves_existentes_override=llaves_con_agosto
        )
        self.assertFalse(res_recarga['exito'])
        self.assertTrue(res_recarga.get('denegada_por_idempotencia'))
        self.assertEqual(res_recarga['paso_fallido'], 'IDEMPOTENCIA')
        self.assertEqual(res_recarga['filas_cargadas'], 0)


if __name__ == '__main__':
    unittest.main()
