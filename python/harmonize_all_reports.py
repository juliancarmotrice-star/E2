import os
import re

def clean_and_harmonize():
    files_to_process = [
        'informes/INFORME_FINAL_DIAGNOSTICO_Y_LINEA_BASE_E1.md',
        'informes/INFORME_SUSTENTACION_JUNTA_DIRECTIVA_E1.md',
        'informes/LINEA_BASE_Y_CUANTIFICACION_DE_COSTOS.md',
        'informes/INFORME_INVESTIGACION_QUEJA_GERENCIA_LAMINA.md',
        'informes/INFORME_INVESTIGACION_QUEJA_GERENCIA_INEXACTITUD_INVENTARIO.md',
        'informes/INFORME_INVESTIGACION_QUEJA_GERENCIA_PLATA_MUERTA.md',
        'informes/INFORME_CRUCE_VALORES_NULOS_E_IMPLICACIONES.md',
        'informes/DOCUMENTACION_IMPLICACIONES_CAMBIOS.md',
        'informes/DIAGNOSTICO_BASE_DE_DATOS_SUPABASE.md',
        'informes/BITACORA_DE_LIMPIEZA.md',
        'presentaciones/GUIA_PREPARACION_SUSTENTACION_DIAPOSITIVAS_E1.md',
        'presentaciones/GUIA_PREPARACION_EXPOSICION_E1.md',
        'sql/consultas_analiticas_kpis.sql'
    ]

    for filepath in files_to_process:
        if not os.path.exists(filepath):
            continue
        
        # Read file with encoding fallback
        content = None
        for enc in ['utf-8', 'utf-16', 'latin-1', 'cp1252']:
            try:
                with open(filepath, 'r', encoding=enc) as fp:
                    content = fp.read()
                break
            except Exception:
                continue
        
        if content is None:
            print(f"Failed to read: {filepath}")
            continue

        original_content = content

        # 1. Terminology: OTIF -> SLA
        content = re.sub(r'OTIF\s+—\s+On-Time In-Full', 'SLA de Entrega a Tiempo de Proveedores', content, flags=re.I)
        content = re.sub(r'OTIF\s+On-Time In-Full', 'SLA de Entrega a Tiempo', content, flags=re.I)
        content = re.sub(r'\bOTIF Global \(Entregas a Tiempo\)', 'SLA Global de Proveedores (A Tiempo)', content)
        content = re.sub(r'\bOTIF en Láminas de Acero\b', 'SLA en Láminas de Acero', content)
        content = re.sub(r'\bOTIF Proveedores de Lámina\b', 'SLA Proveedores de Lámina', content)
        content = re.sub(r'\bOTIF Proveedores\b', 'SLA Proveedores', content)
        content = re.sub(r'\bOTIF Lámina\b', 'SLA Lámina', content)
        content = re.sub(r'\bOTIF Láminas\b', 'SLA Láminas', content)
        content = re.sub(r'\bOTIF\b', 'SLA', content)

        # 2. Terminology: IRA -> ERI
        content = re.sub(r'Exactitud del Registro \(IRA\)', 'Exactitud en el Registro de Inventario (ERI)', content)
        content = re.sub(r'Exactitud del Registro \(IRA Activos\)', 'Exactitud de Registro (ERI Activos)', content)
        content = re.sub(r'Exactitud de Registro \(IRA Global\)', 'Exactitud de Registro (ERI Global)', content)
        content = re.sub(r'Exactitud de Registro \(IRA en Catálogo\)', 'Exactitud de Registro (ERI Global en Catálogo)', content)
        content = re.sub(r'Exactitud de Registro \(IRA en SKUs Activos\)', 'Exactitud de Registro (ERI en SKUs Activos)', content)
        content = re.sub(r'Exactitud de Registro \(IRA\)', 'Exactitud en el Registro de Inventario (ERI)', content)
        content = re.sub(r'Inexactitud del Registro \(IRA\)', 'Inexactitud del Registro (ERI)', content)
        content = re.sub(r'Inexactitud Crítica del Registro de Inventario - IRA', 'Inexactitud Crítica del Registro de Inventario (ERI)', content)
        content = re.sub(r'descuadre IRA', 'descuadre ERI', content)
        content = re.sub(r'conciliación IRA', 'conciliación ERI', content)
        content = re.sub(r'Auditoría IRA', 'Auditoría ERI', content)
        content = re.sub(r'auditoría IRA', 'auditoría ERI', content)
        content = re.sub(r'\bIRA\b', 'ERI', content)

        # 3. ERI Figures Harmonization: 71.67% -> 67.14% with explanation of ~75% context
        # Replace ERI Global in tables if 71.67% is presented as exact without nuance
        content = re.sub(r'\*\*71\.67%\*\*\s*\(301 de 420 SKUs\)', '**67.14%** (282 de 420 SKUs exactos; ~75% con tolerancia operativa)', content)
        content = re.sub(r'ERI del 71\.67%', 'ERI del 67.14% (exactitud binaria estricta; ~75% con tolerancia operativa)', content)

        # Save back as clean UTF-8
        with open(filepath, 'w', encoding='utf-8') as fp:
            fp.write(content)
        
        print(f"Updated: {filepath}")

if __name__ == '__main__':
    clean_and_harmonize()
