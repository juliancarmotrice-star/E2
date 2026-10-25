"""
Tablero de Control de Abastecimiento y Operaciones - E2 SAS (Producción 4.0)
Archivo: app.py
Tecnología: Streamlit (Interfaz Ejecutiva Minimalista) + Persistencia en Supabase
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime

import orquestador
import nucleo.exactitud_eri as eri
import nucleo.clasificacion_abc as abc
import nucleo.sla_proveedores as sla
import nucleo.explosion_mrp as mrp
import nucleo.reposicion_eoq_rop as reposicion
import nucleo.explicador_ia as explicador
import nucleo.analisis_cambios as cambios

# Configuración de página
st.set_page_config(
    page_title="E2 SAS · Control de Abastecimiento",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS Minimalistas y Profesionales
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }
    
    /* Fondo limpio y márgenes compactos */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1380px !important;
    }
    
    /* Encabezado minimalista */
    .brand-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 0.8rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid #E2E8F0;
    }
    .brand-title {
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #0F172A;
    }
    .brand-subtitle {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 400;
    }
    .brand-badge {
        font-size: 0.75rem;
        padding: 0.25rem 0.6rem;
        background: #F1F5F9;
        color: #334155;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    
    /* Métricas minimalistas */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em;
    }
    
    /* Pestañas limpias y delgadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: transparent;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 1.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        padding: 0 16px;
        background-color: transparent;
        border-radius: 6px 6px 0 0;
        color: #64748B;
        font-weight: 500;
        font-size: 0.88rem;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #0F172A !important;
    }
    
    /* Memorando IA minimalista */
    .memo-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .memo-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .memo-body {
        font-size: 0.9rem;
        color: #334155;
        line-height: 1.5;
    }
    
    /* Botones de acción */
    button[kind="primary"] {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }
    
    /* Tablas compactas */
    [data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# PARÁMETROS GLOBALES EN MEMORIA
# ------------------------------------------------------------------------------
if "umbral_monto" not in st.session_state:
    st.session_state["umbral_monto"] = 20_000_000.0

if "usuario_activo" not in st.session_state:
    st.session_state["usuario_activo"] = "Julian (Jefe de Producción)"

# Inicializar propuestas en memoria si no existen
if "propuestas_activas" not in st.session_state:
    res_init = orquestador.generar_propuestas_reposicion(umbral_alto_valor_cop=st.session_state["umbral_monto"])
    st.session_state["propuestas_activas"] = res_init["propuestas"]
    st.session_state["conteo_paradas"] = res_init["conteo_paradas"]
    st.session_state["inversion_total_formato"] = res_init["inversion_total_formato"]

# ------------------------------------------------------------------------------
# CARGA DE INDICADORES BASE
# ------------------------------------------------------------------------------
@st.cache_data(ttl=30)
def cargar_kpis_base():
    res_eri = eri.obtener_resumen_eri()
    res_sla = sla.obtener_resumen_global_sla()
    res_abc = abc.obtener_resumen_pareto()
    plan_compras = reposicion.obtener_plan_compras_sugeridas()
    return res_eri, res_sla, res_abc, plan_compras

try:
    kpi_eri, kpi_sla, kpi_abc, kpi_plan = cargar_kpis_base()
    eri_tg = kpi_eri.get("total_general") or {}
except Exception as e:
    st.error(f"Error consultando Supabase: {e}")
    st.stop()

# ------------------------------------------------------------------------------
# ENCABEZADO MINIMALISTA
# ------------------------------------------------------------------------------
propuestas_pendientes = st.session_state.get("propuestas_activas", [])

st.markdown(f"""
<div class="brand-header">
    <div>
        <div class="brand-title">E2 SAS · Control de Abastecimiento & Producción 4.0</div>
        <div class="brand-subtitle">Motor determinístico de reposición con supervisión humana y gobernanza de ingesta (B4_02)</div>
    </div>
    <div style="display: flex; gap: 8px; align-items: center;">
        <span class="brand-badge">Operador: {st.session_state['usuario_activo']}</span>
        <span class="brand-badge">Base: Supabase (PostgreSQL)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4 MÉTRICAS EJECUTIVAS ESENCIALES (SIN RUIDO)
# ------------------------------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        label="Exactitud Inventario (ERI)",
        value=eri_tg.get("eri_porcentaje_exactitud", "74.3%"),
        delta=f"{eri_tg.get('skus_exactos', 312)}/{eri_tg.get('total_skus', 420)} SKUs exactos"
    )

with m2:
    st.metric(
        label="Inversión Sugerida Reorden",
        value=st.session_state.get("inversion_total_formato", "$ 0 COP"),
        delta=f"{len(propuestas_pendientes)} ítems bajo ROP",
        delta_color="off"
    )

with m3:
    st.metric(
        label="Cumplimiento Proveedores (SLA)",
        value=kpi_sla.get("sla_global_formato", "11.7%"),
        delta=f"Mora prom: {kpi_sla.get('mora_promedio_cuando_tarde_dias', 0)} días",
        delta_color="inverse"
    )

with m4:
    st.metric(
        label="Concentración Estratégica (Clase A)",
        value=f"{kpi_abc['clases']['A']['pct_valor']}%",
        delta=f"{kpi_abc['clases']['A']['total_skus']} SKUs clave (Pareto)"
    )

# ------------------------------------------------------------------------------
# ESTRUCTURA DE 3 PESTAÑAS PRINCIPALES
# ------------------------------------------------------------------------------
tab_decisiones, tab_ingesta, tab_diagnostico = st.tabs([
    "⚡ Consola de Decisiones (Reposición)",
    "📥 Ingesta 5 Pasos & Control de Datos",
    "📊 Diagnóstico & Control Patrimonial"
])

# ==============================================================================
# PESTAÑA 1: CONSOLA DE DECISIONES DE REPOSICIÓN
# ==============================================================================
with tab_decisiones:
    if not propuestas_pendientes:
        st.info("🎉 No hay propuestas de reposición pendientes por decidir en este momento.")
        if st.button("Recalcular Sugerencias de Compra", type="primary"):
            res = orquestador.generar_propuestas_reposicion(umbral_alto_valor_cop=st.session_state["umbral_monto"])
            st.session_state["propuestas_activas"] = res["propuestas"]
            st.session_state["conteo_paradas"] = res["conteo_paradas"]
            st.session_state["inversion_total_formato"] = res["inversion_total_formato"]
            st.rerun()
    else:
        df_p = pd.DataFrame(propuestas_pendientes)

        # Barra compacta de filtros y control
        fc1, fc2, fc3, fc4 = st.columns([1.2, 1.8, 1.2, 1.2])
        with fc1:
            filtro_clase = st.selectbox("Clase ABC:", ["TODAS", "A", "B", "C"], index=0)
        with fc2:
            filtro_parada = st.selectbox(
                "Criterio de Parada:",
                ["TODOS", "REQUIERE_VERIFICACION_FISICA", "REQUIERE_AUTORIZACION_GERENCIAL", "PROVEEDOR_ALTO_RIESGO_MORA", "APROBACION_ESTANDAR"],
                index=0
            )
        with fc3:
            siguiente_oc = orquestador.obtener_siguiente_codigo_oc()
            st.markdown(f"<div style='font-size:0.75rem; color:#64748B; font-weight:600; text-transform:uppercase;'>Próxima OC</div><div style='font-size:1.1rem; font-weight:700; color:#0F172A;'>{siguiente_oc}</div>", unsafe_allow_html=True)
        with fc4:
            if st.button("↻ Recalcular", use_container_width=True):
                res = orquestador.generar_propuestas_reposicion(umbral_alto_valor_cop=st.session_state["umbral_monto"])
                st.session_state["propuestas_activas"] = res["propuestas"]
                st.session_state["conteo_paradas"] = res["conteo_paradas"]
                st.session_state["inversion_total_formato"] = res["inversion_total_formato"]
                st.rerun()

        # Filtrar propuestas
        df_filtrado = df_p.copy()
        if filtro_clase != "TODAS":
            df_filtrado = df_filtrado[df_filtrado["clasificacion_abc"] == filtro_clase]
        if filtro_parada != "TODOS":
            df_filtrado = df_filtrado[df_filtrado["criterio_parada"].str.contains(filtro_parada, na=False)]

        # Tabla limpia de recomendaciones
        cols_mostrar = [
            "propuesta_temp_id", "sku", "descripcion", "categoria",
            "clasificacion_abc", "cantidad_sugerida", "costo_unitario",
            "inversion_cop", "criterio_parada", "motivo_orden"
        ]
        st.dataframe(
            df_filtrado[cols_mostrar].style.format({
                "cantidad_sugerida": "{:,.0f}",
                "costo_unitario": "$ {:,.0f}",
                "inversion_cop": "$ {:,.0f}"
            }),
            use_container_width=True,
            height=260
        )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Panel de decisión ejecutiva
        col_eval, col_lote = st.columns([2.2, 1.1])
        with col_eval:
            st.markdown("##### Decisión Individual con Asistencia IA")
            sku_seleccionado = st.selectbox(
                "Seleccionar ítem para decisión:",
                options=df_filtrado["sku"].tolist() if not df_filtrado.empty else [],
                format_func=lambda s: f"[{s}] {df_filtrado[df_filtrado['sku']==s]['descripcion'].values[0]} · Inversión: $ {df_filtrado[df_filtrado['sku']==s]['inversion_cop'].values[0]:,.0f} COP"
            )

            prop_data = next((p for p in propuestas_pendientes if p["sku"] == sku_seleccionado), None) if sku_seleccionado else None

            if prop_data:
                memo = explicador.generar_explicacion_ejecutiva(prop_data)
                
                # Card de Justificación Minimalista
                st.markdown(f"""
                <div class="memo-card">
                    <div class="memo-title">{memo['dictamen']}</div>
                    <div class="memo-body">{memo['memo_ejecutivo']}</div>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; color: #0369A1; font-weight: 500;">
                        → <strong>Directriz:</strong> {memo['accion_recomendada']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            obs_decision = st.text_input("Observación humana (opcional):", placeholder="Ej: Conteo físico verificado. Se autoriza compra.")

            b_apr, b_rec = st.columns(2)
            with b_apr:
                if st.button("✓ Aprobar y Generar OC", type="primary", use_container_width=True, disabled=df_filtrado.empty):
                    if prop_data:
                        res_tx = orquestador.aprobar_propuesta(
                            propuesta=prop_data,
                            decidido_por=st.session_state["usuario_activo"],
                            comentarios=obs_decision
                        )
                        st.session_state["propuestas_activas"] = [p for p in propuestas_pendientes if p["sku"] != sku_seleccionado]
                        st.success(f"Orden creada: **{res_tx['orden_compra_generada']}** para **{res_tx['sku']}** (Inversión: $ {res_tx['inversion_cop']:,.0f} COP)")
                        st.rerun()

            with b_rec:
                if st.button("✕ Rechazar Sugerencia", type="secondary", use_container_width=True, disabled=df_filtrado.empty):
                    if prop_data:
                        res_rx = orquestador.rechazar_propuesta(
                            propuesta=prop_data,
                            decidido_por=st.session_state["usuario_activo"],
                            motivo=obs_decision or "Rechazada en revisión"
                        )
                        st.session_state["propuestas_activas"] = [p for p in propuestas_pendientes if p["sku"] != sku_seleccionado]
                        st.warning(f"Sugerencia para {res_rx['sku']} rechazada y asentada en auditoría.")
                        st.rerun()

        with col_lote:
            st.markdown("##### Aprobación Rápida")
            estandar_count = len([p for p in propuestas_pendientes if p.get("es_estandar")])
            st.markdown(f"""
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:0.9rem; font-size:0.85rem; color:#475569; margin-bottom:0.8rem;">
                Órdenes estándar libres de riesgo ERI/SLA: <strong>{estandar_count}</strong>
            </div>
            """, unsafe_allow_html=True)

            if st.button("⚡ Aprobar Estándar en Lote", use_container_width=True, disabled=estandar_count == 0):
                aprobadas = 0
                for p in list(propuestas_pendientes):
                    if p.get("es_estandar"):
                        orquestador.aprobar_propuesta(p, decidido_por=st.session_state["usuario_activo"], comentarios="Aprobación estándar en lote")
                        aprobadas += 1
                st.session_state["propuestas_activas"] = [p for p in propuestas_pendientes if not p.get("es_estandar")]
                st.success(f"Se emitieron {aprobadas} órdenes estándar en Supabase.")
                st.rerun()

        # Historial reciente
        with st.expander("Ver Órdenes Recientes Creadas en Supabase (`ordenes_compra`)"):
            try:
                ocs_recientes = orquestador.consultar_ordenes_recientes(limite=20)
                if ocs_recientes:
                    st.dataframe(
                        pd.DataFrame(ocs_recientes)[["orden_compra", "fecha_pedido", "sku", "cantidad", "proveedor", "fecha_promesa", "costo_unitario"]].style.format({
                            "cantidad": "{:,.0f}",
                            "costo_unitario": "$ {:,.0f}"
                        }),
                        use_container_width=True
                    )
            except Exception as e:
                st.caption(f"Sin registros recientes: {e}")

# ==============================================================================
# PESTAÑA 2: INGESTA EN 5 PASOS & CONTROL DE IDEMPOTENCIA
# ==============================================================================
with tab_ingesta:
    st.markdown("##### Ingesta de Datos e Idempotencia (Protocolo B4_02)")
    st.caption("Validación estricta de hoja destino, chequeo de datos obligatorios y denegación de planillas duplicadas.")

    c_ing_form, c_ing_status = st.columns([1.1, 1.2])

    with c_ing_form:
        opciones_tablas = list(cambios.ESQUEMAS_HOJAS.keys())
        tabla_seleccionada = st.selectbox(
            "Hoja / Entidad Destino:",
            opciones_tablas,
            format_func=lambda x: f"{x} — {cambios.ESQUEMAS_HOJAS.get(x, {}).get('nombre', x)}"
        )

        meta_sel = cambios.ESQUEMAS_HOJAS.get(tabla_seleccionada, {})
        st.markdown(f"<div style='font-size:0.8rem; color:#64748B; margin-bottom:0.5rem;'>Requeridas: <code>{', '.join(meta_sel.get('requeridas', []))}</code> | Clave: <code>{', '.join(meta_sel.get('clave_primaria', []))}</code></div>", unsafe_allow_html=True)

        archivo_subido = st.file_uploader(
            "Seleccionar planilla CSV:",
            type=["csv"],
            label_visibility="collapsed"
        )

        c_sub1, c_sub2 = st.columns([1.2, 1])
        with c_sub1:
            btn_procesar = st.button(
                "📥 Procesar Ingesta en DB",
                type="primary",
                disabled=(archivo_subido is None),
                use_container_width=True
            )
        with c_sub2:
            persistir_db = st.checkbox("Persistir en Supabase", value=True)

        st.markdown("---")
        st.markdown("<div style='font-size:0.85rem; font-weight:600; color:#334155;'>Validación en 10 Minutos (Taller B4_02)</div>", unsafe_allow_html=True)
        if st.button("🔬 Probar Idempotencia & Acumulación", use_container_width=True):
            with st.spinner("Comprobando doble carga y lote incremental..."):
                st.session_state["res_taller_b4"] = cambios.simular_prueba_idempotencia_acumulativa(tabla_seleccionada)

    with c_ing_status:
        st.markdown("<div style='font-size:0.85rem; font-weight:600; color:#334155; margin-bottom: 0.5rem;'>Estado de la Carga & Rendición de Cuentas</div>", unsafe_allow_html=True)
        
        # Procesamiento de archivo subido
        if archivo_subido is not None and btn_procesar:
            try:
                df_up = pd.read_csv(archivo_subido)
                res_ing = cambios.ejecutar_ingesta_5_pasos(
                    tabla_destino=tabla_seleccionada,
                    df_entrante=df_up,
                    nombre_archivo=archivo_subido.name,
                    usuario=st.session_state["usuario_activo"],
                    modo_idempotente=True,
                    persistir_en_bd=persistir_db
                )
                st.session_state["ultimo_reporte_ingesta"] = res_ing
            except Exception as e:
                st.error(f"Error procesando CSV: {e}")

        res_ing = st.session_state.get("ultimo_reporte_ingesta")
        if res_ing:
            rep = res_ing.get("reporte") or {}
            
            if res_ing.get("denegada_por_idempotencia"):
                st.error("🛑 CARGA DENEGADA POR IDEMPOTENCIA")
                st.write(res_ing.get("mensaje"))
                c_k1, c_k2, c_k3 = st.columns(3)
                c_k1.metric("Leídas", rep.get("filas_leidas", 0))
                c_k2.metric("Duplicados Detectados", rep.get("filas_duplicadas_detectadas", 0))
                c_k3.metric("Nuevas Agregadas", 0)
                st.caption("🔒 El sistema detectó que los registros ya existen en la base de datos. Se bloqueó la carga para evitar duplicar información.")

            elif res_ing.get("contraste_fallido"):
                st.error("🛑 RECHAZADA: HOJA ESPECÍFICA / ESQUEMA NO COINCIDE")
                st.write(res_ing.get("mensaje"))
                st.caption("🔒 El archivo no pertenece a la entidad seleccionada o carece de las columnas obligatorias.")

            elif not res_ing.get("exito"):
                st.error("🛑 RECHAZADA: ARCHIVO SIN INFORMACIÓN")
                st.write(res_ing.get("mensaje"))

            else:
                st.success(f"✓ Carga y Saneamiento Exitoso en {res_ing.get('duracion_ms', 0)} ms")
                c_k1, c_k2, c_k3, c_k4 = st.columns(4)
                c_k1.metric("Leídas", rep.get("filas_leidas", 0))
                c_k2.metric("Saneadas (Limpieza)", rep.get("total_correcciones_limpieza", 0))
                c_k3.metric("Nuevas Cargadas", rep.get("filas_cargadas", 0))
                c_k4.metric("Duplicados Omitidos", rep.get("filas_duplicadas_omitidas", 0))

                transf = rep.get("transformaciones_limpieza", [])
                if transf:
                    with st.expander("Ver Acciones del Módulo de Limpieza (3FN & Saneamiento)", expanded=True):
                        for t in transf:
                            st.markdown(f"- 🧹 {t}")

                st.caption(f"Planilla: {rep.get('archivo')} → {rep.get('tabla_destino')} | Tasa Aceptación: {rep.get('tasa_aceptacion_pct', 0)}%")
        else:
            st.info("Seleccione una entidad, suba un archivo CSV y haga clic en 'Procesar Ingesta en DB' para someterlo al protocolo de 5 pasos.")

        # Resultado del Taller de 10 minutos
        res_t = st.session_state.get("res_taller_b4")
        if res_t:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.markdown(f"**Resultado del Test de Idempotencia:** `{res_t['conclusion_taller']}`")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.caption(f"1. Doble Carga: {'✓ Denegada (0 agregadas)' if res_t['prueba_idempotencia']['pasa_idempotencia'] else '✕ Duplicó'}")
            with t_col2:
                st.caption(f"2. Incremental: {'✓ Acumulada (+ nuevos SKUs)' if res_t['prueba_acumulativa']['pasa_acumulativo'] else '✕ Falló'}")

# ==============================================================================
# PESTAÑA 3: DIAGNÓSTICO & CONTROL PATRIMONIAL (SIN GRÁFICOS INÚTILES)
# ==============================================================================
with tab_diagnostico:
    st.markdown("##### Diagnóstico Esencial de la Cadena de Suministro")
    st.caption("Consolidación tabular de alta densidad: veracidad de inventario (ERI), Pareto (ABC), desempeño de proveedores (SLA) y necesidades de materiales (MRP).")

    diag_sel = st.radio(
        "Área de diagnóstico:",
        ["Exactitud de Inventario (ERI)", "Clasificación ABC & Plata Muerta", "Nivel de Servicio Proveedores (SLA)", "Explosión de Materiales (MRP)"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if diag_sel == "Exactitud de Inventario (ERI)":
        d1, d2 = st.columns([1, 2.5])
        with d1:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:1rem;">
                <div style="font-size:0.8rem; font-weight:600; color:#64748B;">RESUMEN DE VERACIDAD</div>
                <div style="font-size:1.6rem; font-weight:700; color:#0F172A; margin:0.3rem 0;">{eri_tg.get('eri_porcentaje_exactitud', '74.3%')}</div>
                <div style="font-size:0.85rem; color:#334155;">SKUs Cuadrados: <strong>{eri_tg.get('skus_exactos', 0)}</strong></div>
                <div style="font-size:0.85rem; color:#EF4444;">SKUs Descuadrados: <strong>{eri_tg.get('skus_descuadrados', 0)}</strong></div>
                <div style="font-size:0.85rem; color:#64748B; margin-top:0.4rem;">Desalineación Total:<br><strong>{eri_tg.get('desalineacion_contable_bruta', '$ 0 COP')}</strong></div>
            </div>
            """, unsafe_allow_html=True)
        with d2:
            st.markdown("<div style='font-size:0.85rem; font-weight:600; color:#0F172A; margin-bottom:0.4rem;'>Top SKUs con Mayor Desalineación Patrimonial (Kardex vs Conteo Físico)</div>", unsafe_allow_html=True)
            top_descuadres = eri.obtener_top_desalineados(12)
            st.dataframe(
                pd.DataFrame(top_descuadres)[[
                    "sku", "descripcion", "categoria", "costo_unitario",
                    "stock_teorico_kardex", "stock_fisico_oficial", "stock_cuaderno_jefe",
                    "discrepancia_unidades", "desalineacion_dinero_cop", "estado_eri"
                ]].style.format({
                    "costo_unitario": "$ {:,.0f}",
                    "stock_teorico_kardex": "{:,.1f}",
                    "stock_fisico_oficial": "{:,.1f}",
                    "stock_cuaderno_jefe": "{:,.1f}",
                    "discrepancia_unidades": "{:,.1f}",
                    "desalineacion_dinero_cop": "$ {:,.0f}"
                }),
                use_container_width=True,
                height=280
            )

    elif diag_sel == "Clasificación ABC & Plata Muerta":
        a1, a2, a3 = st.columns(3)
        with a1:
            st.markdown(f"**Clase A (80% Valor):** {kpi_abc['clases']['A']['total_skus']} SKUs ({kpi_abc['clases']['A']['pct_skus']}%)<br><small style='color:#64748B;'>${kpi_abc['clases']['A']['valor_consumo_cop']:,.0f} COP</small>", unsafe_allow_html=True)
        with a2:
            st.markdown(f"**Clase B (15% Valor):** {kpi_abc['clases']['B']['total_skus']} SKUs ({kpi_abc['clases']['B']['pct_skus']}%)<br><small style='color:#64748B;'>${kpi_abc['clases']['B']['valor_consumo_cop']:,.0f} COP</small>", unsafe_allow_html=True)
        with a3:
            st.markdown(f"**Clase C (5% Valor):** {kpi_abc['clases']['C']['total_skus']} SKUs ({kpi_abc['clases']['C']['pct_skus']}%)<br><small style='color:#64748B;'>${kpi_abc['clases']['C']['valor_consumo_cop']:,.0f} COP</small>", unsafe_allow_html=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.85rem; font-weight:600; color:#B91C1C;'>SKUs Inmovilizados de Plata Muerta (Cero Salidas en Historial)</div>", unsafe_allow_html=True)
        pm = abc.obtener_plata_muerta()
        if pm:
            st.dataframe(
                pd.DataFrame(pm)[["sku", "descripcion", "categoria", "costo_unitario", "clasificacion_abc"]].style.format({
                    "costo_unitario": "$ {:,.0f}"
                }),
                use_container_width=True,
                height=260
            )
        else:
            st.caption("No se detectaron ítems inmovilizados.")

    elif diag_sel == "Nivel de Servicio Proveedores (SLA)":
        cats_sla = sla.obtener_metricas_sla_por_categoria()
        df_sla = pd.DataFrame(cats_sla)
        st.markdown("<div style='font-size:0.85rem; font-weight:600; color:#0F172A; margin-bottom:0.4rem;'>Cumplimiento OTD y Desfase de Lead Time por Familia de Proveedores</div>", unsafe_allow_html=True)
        st.dataframe(
            df_sla[[
                "categoria", "total_oc_cerradas", "a_tiempo", "retrasadas",
                "sla_cumplimiento_formato", "mora_promedio_dias", "lead_time_erp_dias",
                "lead_time_real_dias", "desfase_dias"
            ]],
            use_container_width=True,
            height=300
        )

    elif diag_sel == "Explosión de Materiales (MRP)":
        mrp_neto = mrp.obtener_requerimientos_netos_mrp()
        df_mrp = pd.DataFrame(mrp_neto)
        con_deficit = len(df_mrp[df_mrp["tiene_deficit"] == True])
        st.markdown(f"<div style='font-size:0.85rem; font-weight:600; color:#0F172A; margin-bottom:0.4rem;'>Explosión Neta BOM × MPS ({con_deficit} materiales en déficit)</div>", unsafe_allow_html=True)
        st.dataframe(
            df_mrp[[
                "sku_material", "descripcion", "categoria", "unidad",
                "requerimiento_bruto", "stock_disponible", "requerimiento_neto",
                "deficit_valor_cop", "tiene_deficit"
            ]].style.format({
                "requerimiento_bruto": "{:,.1f}",
                "stock_disponible": "{:,.1f}",
                "requerimiento_neto": "{:,.1f}",
                "deficit_valor_cop": "$ {:,.0f}"
            }),
            use_container_width=True,
            height=300
        )
