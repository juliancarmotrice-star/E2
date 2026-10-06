"""
Tablero de Control y Supervisión de Operaciones - E2 SAS (Producción 4.0)
Archivo: app.py
Tecnología: Streamlit (Ejecución Local)

Arquitectura Transaccional:
- INTERACCIÓN: Muestra propuestas calculadas en memoria y recopila decisiones humanas.
- AL APROBAR:
    1. Inserta la Orden de Compra oficial en Supabase (public.ordenes_compra).
    2. Registra la propuesta aprobada en Supabase (public.propuestas_compra) con su código de OC.
- AL RECHAZAR:
    Registra la propuesta rechazada en Supabase con su justificación para auditoría (sin generar OC).
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import orquestador
import nucleo.exactitud_eri as eri
import nucleo.clasificacion_abc as abc
import nucleo.sla_proveedores as sla
import nucleo.explosion_mrp as mrp
import nucleo.reposicion_eoq_rop as reposicion

# Configuración de página
st.set_page_config(
    page_title="Sistema de Producción 4.0 · E2 SAS",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge-rojo {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🏭 Sistema de Gestión y Reposición 4.0</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">E2 SAS · Ingeniería Industrial · Producción 4.0 · Universidad de Medellín</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# BARRA LATERAL (CONTROL Y CONFIGURACIÓN DEL ORQUESTADOR)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/factory.png", width=70)
    st.header("⚙️ Panel de Control")
    usuario_activo = st.text_input("Usuario / Cargo:", value="Julian (Jefe de Producción)")
    
    st.divider()
    st.subheader("Criterios de Parada")
    umbral_monto = st.number_input(
        "Umbral Alto Valor (COP)",
        min_value=1_000_000,
        max_value=100_000_000,
        value=20_000_000,
        step=1_000_000,
        help="Protección de caja: Órdenes que superen este valor requieren autorización gerencial."
    )
    
    st.divider()
    st.markdown("### 🔄 Orquestación")
    if st.button("🚀 Recalcular Recomendaciones", type="primary", use_container_width=True):
        with st.spinner("Ejecutando orquestador y recalculando en memoria..."):
            res = orquestador.generar_propuestas_reposicion(umbral_alto_valor_cop=float(umbral_monto))
            st.session_state["propuestas_activas"] = res["propuestas"]
            st.session_state["conteo_paradas"] = res["conteo_paradas"]
            st.session_state["inversion_total_formato"] = res["inversion_total_formato"]
            st.success(f"Corrida completada: {res['corrida_id']} ({res['total_propuestas']} sugerencias)")

# Inicializar recomendaciones en memoria si no existen
if "propuestas_activas" not in st.session_state:
    res_init = orquestador.generar_propuestas_reposicion(umbral_alto_valor_cop=float(umbral_monto))
    st.session_state["propuestas_activas"] = res_init["propuestas"]
    st.session_state["conteo_paradas"] = res_init["conteo_paradas"]
    st.session_state["inversion_total_formato"] = res_init["inversion_total_formato"]

# ------------------------------------------------------------------------------
# CARGA DE INDICADORES CLAVE (KARDEX / ERI / SLA / REPOSICIÓN)
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
    st.error(f"Error cargando KPIs desde Supabase: {e}")
    st.stop()

# ------------------------------------------------------------------------------
# TARJETAS DE INDICADORES (SLIDE 39)
# ------------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        label="🎯 Exactitud de Inventario (ERI)",
        value=eri_tg.get("eri_porcentaje_exactitud", "N/A"),
        delta=f"{eri_tg.get('skus_exactos')}/{eri_tg.get('total_skus')} SKUs conformes",
        delta_color="normal"
    )

with c2:
    st.metric(
        label="🚚 Nivel de Servicio Proveedores (SLA)",
        value=kpi_sla.get("sla_global_formato", "N/A"),
        delta=f"Mora prom: {kpi_sla.get('mora_promedio_cuando_tarde_dias')} días",
        delta_color="inverse"
    )

with c3:
    st.metric(
        label="📊 Concentración Pareto (Clase A)",
        value=f"{kpi_abc['clases']['A']['pct_valor']}%",
        delta=f"{kpi_abc['clases']['A']['total_skus']} SKUs estratégicos",
        delta_color="normal"
    )

with c4:
    propuestas_pendientes = st.session_state.get("propuestas_activas", [])
    st.metric(
        label="🛒 Propuestas Pendientes por Decidir",
        value=f"{len(propuestas_pendientes)} SKUs",
        delta=st.session_state.get("inversion_total_formato", "N/A"),
        delta_color="off"
    )

st.markdown("---")

# ------------------------------------------------------------------------------
# NAVEGACIÓN POR PESTAÑAS
# ------------------------------------------------------------------------------
tab_propuestas, tab_historial, tab_eri, tab_abc, tab_sla, tab_mrp = st.tabs([
    "📋 Tablero de Decisiones (Reposición)",
    "📜 Historial Transaccional (Supabase)",
    "🔍 Auditoría ERI (Kardex vs Físico)",
    "🏷️ Matriz ABC & Plata Muerta",
    "⏱️ SLA de Proveedores",
    "💥 Explosión MRP (BOM × MPS)"
])

# ==============================================================================
# TAB 1: TABLERO DE DECISIONES TRANSACCIONAL (HUMAN-IN-THE-LOOP)
# ==============================================================================
with tab_propuestas:
    st.subheader("Sugerencias de Compra Calculadas en Memoria")
    st.caption("Revise los motivos y criterios de parada. Al aprobar, se inserta transaccionalmente la OC en `ordenes_compra` y se registra en `propuestas_compra`.")

    propuestas_mem = st.session_state.get("propuestas_activas", [])

    if not propuestas_mem:
        st.success("🎉 ¡Excelente trabajo! No hay propuestas pendientes por decidir en esta sesión.")
        if st.button("Recargar catálogo de sugerencias"):
            res = orquestador.generar_propuestas_reposicion(umbral_alto_valor_cop=float(umbral_monto))
            st.session_state["propuestas_activas"] = res["propuestas"]
            st.rerun()
    else:
        df_p = pd.DataFrame(propuestas_mem)

        # Filtros en pantalla
        f1, f2, f3 = st.columns(3)
        with f1:
            filtro_clase = st.selectbox("Filtrar por Clase ABC", ["TODOS", "A", "B", "C"], index=0)
        with f2:
            filtro_parada = st.selectbox("Criterio de Parada", ["TODOS", "REQUIERE_VERIFICACION_FISICA", "REQUIERE_AUTORIZACION_GERENCIAL", "PROVEEDOR_ALTO_RIESGO_MORA", "APROBACION_ESTANDAR"], index=0)
        with f3:
            siguiente_oc = orquestador.obtener_siguiente_codigo_oc()
            st.info(f"**Próxima Orden de Compra:** `{siguiente_oc}`")

        df_filtrado = df_p.copy()
        if filtro_clase != "TODOS":
            df_filtrado = df_filtrado[df_filtrado["clasificacion_abc"] == filtro_clase]
        if filtro_parada != "TODOS":
            df_filtrado = df_filtrado[df_filtrado["criterio_parada"].str.contains(filtro_parada, na=False)]

        st.markdown(f"**Mostrando {len(df_filtrado)} de {len(propuestas_mem)} recomendaciones pendientes**")

        columnas_ver = [
            "propuesta_temp_id", "sku", "descripcion", "categoria", 
            "clasificacion_abc", "cantidad_sugerida", "costo_unitario", 
            "inversion_cop", "criterio_parada", "motivo_orden"
        ]
        st.dataframe(
            df_filtrado[columnas_ver].style.format({
                "cantidad_sugerida": "{:,.0f}",
                "costo_unitario": "$ {:,.0f}",
                "inversion_cop": "$ {:,.0f}"
            }),
            use_container_width=True,
            height=320
        )

        st.divider()
        st.subheader("✍️ Ejecución Transaccional (Aprobar / Rechazar)")
        
        col_acc1, col_acc2 = st.columns([2, 1])
        with col_acc1:
            st.markdown("#### Decisión sobre SKU Específico")
            sku_seleccionado = st.selectbox(
                "Seleccionar Ítem para Decidir:",
                options=df_filtrado["sku"].tolist() if not df_filtrado.empty else [],
                format_func=lambda s: f"[{s}] {df_filtrado[df_filtrado['sku']==s]['descripcion'].values[0]} | Inversión: $ {df_filtrado[df_filtrado['sku']==s]['inversion_cop'].values[0]:,.0f} COP | Parada: {df_filtrado[df_filtrado['sku']==s]['criterio_parada'].values[0]}"
            )
            comentario_decision = st.text_input(
                "Observaciones / Justificación de la decisión:",
                placeholder="Ej: Conteo físico verificado en bodega. Se autoriza emisión de OC."
            )
            
            b1, b2 = st.columns(2)
            with b1:
                if st.button("✅ Aprobar y Generar Orden de Compra", type="primary", use_container_width=True, disabled=df_filtrado.empty):
                    if sku_seleccionado:
                        # Buscar la propuesta completa
                        prop_data = next((p for p in propuestas_mem if p["sku"] == sku_seleccionado), None)
                        if prop_data:
                            with st.spinner("Generando OC en `ordenes_compra` y registrando en `propuestas_compra`..."):
                                res_tx = orquestador.aprobar_propuesta(
                                    propuesta=prop_data,
                                    decidido_por=usuario_activo,
                                    comentarios=comentario_decision
                                )
                                # Remover de pendientes
                                st.session_state["propuestas_activas"] = [
                                    p for p in propuestas_mem if p["sku"] != sku_seleccionado
                                ]
                                st.success(f"🎉 ¡Transacción Exitosa! Se creó la Orden **{res_tx['orden_compra_generada']}** para **{res_tx['sku']}** (Proveedor: {res_tx['proveedor']}, Inversión: $ {res_tx['inversion_cop']:,.0f} COP)")
                                st.rerun()

            with b2:
                if st.button("❌ Rechazar Sugerencia", use_container_width=True, disabled=df_filtrado.empty):
                    if sku_seleccionado:
                        prop_data = next((p for p in propuestas_mem if p["sku"] == sku_seleccionado), None)
                        if prop_data:
                            with st.spinner("Registrando rechazo en `propuestas_compra`..."):
                                res_rx = orquestador.rechazar_propuesta(
                                    propuesta=prop_data,
                                    decidido_por=usuario_activo,
                                    motivo=comentario_decision or "Rechazada por el planeador"
                                )
                                st.session_state["propuestas_activas"] = [
                                    p for p in propuestas_mem if p["sku"] != sku_seleccionado
                                ]
                                st.warning(f"Propuesta para **{res_rx['sku']}** RECHAZADA y registrada en auditoría.")
                                st.rerun()

        with col_acc2:
            st.markdown("#### Aprobación en Lote")
            st.info("Solo aplica a propuestas en estado **APROBACION_ESTANDAR** (sin descuadres ERI ni alertas).")
            estandar_count = len([p for p in propuestas_mem if p.get("es_estandar")])
            st.write(f"Órdenes estándar disponibles: **{estandar_count}**")

            if st.button("⚡ Aprobar Órdenes Estándar", use_container_width=True, disabled=estandar_count == 0):
                aprobadas = 0
                for p in list(propuestas_mem):
                    if p.get("es_estandar"):
                        orquestador.aprobar_propuesta(p, decidido_por=usuario_activo, comentarios="Aprobación en lote estándar")
                        aprobadas += 1
                st.session_state["propuestas_activas"] = [p for p in propuestas_mem if not p.get("es_estandar")]
                st.success(f"Se generaron {aprobadas} órdenes de compra en lote exitosamente.")
                st.rerun()

# ==============================================================================
# TAB 2: HISTORIAL TRANSACCIONAL EN SUPABASE
# ==============================================================================
with tab_historial:
    st.subheader("Auditoría de Decisiones y Órdenes Creadas en Supabase")
    st.caption("Lectura en tiempo real de las tablas `public.propuestas_compra` y `public.ordenes_compra`.")

    col_h1, col_h2 = st.columns(2)
    
    with col_h1:
        st.markdown("#### 📋 Registro de Propuestas Decididas (`propuestas_compra`)")
        try:
            hist_prop = orquestador.consultar_historial_propuestas(limite=30)
            if hist_prop:
                df_h = pd.DataFrame(hist_prop)
                st.dataframe(
                    df_h[[
                        "id", "sku", "clasificacion_abc", "cantidad_sugerida", 
                        "inversion_cop", "estado_decision", "orden_compra_generada", 
                        "decidido_por", "comentarios"
                    ]].style.format({
                        "cantidad_sugerida": "{:,.0f}",
                        "inversion_cop": "$ {:,.0f}"
                    }),
                    use_container_width=True,
                    height=350
                )
            else:
                st.info("Aún no se han tomado decisiones en Supabase. Aprueba o rechaza una propuesta en la primera pestaña.")
        except Exception as e:
            st.error(f"Error consultando propuestas_compra: {e}")

    with col_h2:
        st.markdown("#### 🚚 Órdenes de Compra en Tránsito (`ordenes_compra`)")
        try:
            ocs_recientes = orquestador.consultar_ordenes_recientes(limite=30)
            if ocs_recientes:
                df_ocs = pd.DataFrame(ocs_recientes)
                st.dataframe(
                    df_ocs[[
                        "orden_compra", "fecha_pedido", "sku", "cantidad", 
                        "proveedor", "fecha_promesa", "fecha_recepcion", "costo_unitario"
                    ]].style.format({
                        "cantidad": "{:,.0f}",
                        "costo_unitario": "$ {:,.0f}"
                    }),
                    use_container_width=True,
                    height=350
                )
        except Exception as e:
            st.error(f"Error consultando ordenes_compra: {e}")

# ==============================================================================
# TAB 3: AUDITORÍA ERI
# ==============================================================================
with tab_eri:
    st.subheader("Auditoría de Exactitud en el Registro de Inventario (ERI)")
    st.caption("Reconciliación tridimensional: Kardex Teórico vs Conteo Físico Oficial vs Cuaderno del Jefe")
    st.markdown(f"**Desalineación Contable Bruta Total:** `{eri_tg.get('desalineacion_contable_bruta')}`")
    
    top_descuadres = eri.obtener_top_desalineados(15)
    df_eri_top = pd.DataFrame(top_descuadres)
    st.markdown("#### Top 15 SKUs con Mayor Desalineación Patrimonial")
    st.dataframe(
        df_eri_top[[
            "sku", "descripcion", "categoria", "costo_unitario", 
            "stock_teorico_kardex", "stock_fisico_oficial", "stock_cuaderno_jefe", 
            "discrepancia_unidades", "desalineacion_dinero_cop", "estado_eri"
        ]].style.format({
            "costo_unitario": "$ {:,.0f}",
            "stock_teorico_kardex": "{:,.2f}",
            "stock_fisico_oficial": "{:,.2f}",
            "stock_cuaderno_jefe": "{:,.2f}",
            "discrepancia_unidades": "{:,.2f}",
            "desalineacion_dinero_cop": "$ {:,.0f}"
        }),
        use_container_width=True
    )

# ==============================================================================
# TAB 4: MATRIZ ABC & PLATA MUERTA
# ==============================================================================
with tab_abc:
    st.subheader("Clasificación Estratégica ABC y Análisis de Rotación")
    abc_c1, abc_c2, abc_c3 = st.columns(3)
    with abc_c1:
        st.markdown(f"**Clase A:** {kpi_abc['clases']['A']['total_skus']} SKUs ({kpi_abc['clases']['A']['pct_skus']}%)")
        st.caption(f"Valor: ${kpi_abc['clases']['A']['valor_consumo_cop']:,.2f} COP ({kpi_abc['clases']['A']['pct_valor']}%)")
    with abc_c2:
        st.markdown(f"**Clase B:** {kpi_abc['clases']['B']['total_skus']} SKUs ({kpi_abc['clases']['B']['pct_skus']}%)")
        st.caption(f"Valor: ${kpi_abc['clases']['B']['valor_consumo_cop']:,.2f} COP ({kpi_abc['clases']['B']['pct_valor']}%)")
    with abc_c3:
        st.markdown(f"**Clase C:** {kpi_abc['clases']['C']['total_skus']} SKUs ({kpi_abc['clases']['C']['pct_skus']}%)")
        st.caption(f"Valor: ${kpi_abc['clases']['C']['valor_consumo_cop']:,.2f} COP ({kpi_abc['clases']['C']['pct_valor']}%)")

    st.divider()
    st.markdown("#### SKUs Inmovilizados (Plata Muerta)")
    pm = abc.obtener_plata_muerta()
    st.warning(f"Se identificaron **{len(pm)} SKUs sin ningún movimiento de salida** en todo el historial.")
    if pm:
        df_pm = pd.DataFrame(pm)
        st.dataframe(df_pm[["sku", "descripcion", "categoria", "costo_unitario", "clasificacion_abc"]].style.format({"costo_unitario": "$ {:,.0f}"}), use_container_width=True)

# ==============================================================================
# TAB 5: SLA DE PROVEEDORES
# ==============================================================================
with tab_sla:
    st.subheader("Auditoría de Nivel de Servicio de Entrega de Proveedores (OTD)")
    st.caption("Evaluación de cumplimiento de fecha promesa y desfase de Lead Time Real vs Declarado en ERP")
    cats_sla = sla.obtener_metricas_sla_por_categoria()
    df_cats_sla = pd.DataFrame(cats_sla)
    st.dataframe(
        df_cats_sla[[
            "categoria", "total_oc_cerradas", "a_tiempo", "retrasadas", 
            "sla_cumplimiento_formato", "mora_promedio_dias", "lead_time_erp_dias", 
            "lead_time_real_dias", "desfase_dias"
        ]],
        use_container_width=True
    )

# ==============================================================================
# TAB 6: EXPLOSIÓN MRP
# ==============================================================================
with tab_mrp:
    st.subheader("Explosión de Materiales (BOM) y Requerimientos Netos")
    st.caption("Proyección de demanda de insumos cruzada con el Plan Maestro de Producción (MPS)")
    mrp_neto = mrp.obtener_requerimientos_netos_mrp()
    df_mrp = pd.DataFrame(mrp_neto)
    st.markdown(f"**Total insumos evaluados:** {len(df_mrp)} | **Insumos con déficit neto:** {len(df_mrp[df_mrp['tiene_deficit']==True])}")
    st.dataframe(
        df_mrp[[
            "sku_material", "descripcion", "categoria", "unidad", 
            "requerimiento_bruto", "stock_disponible", "requerimiento_neto", 
            "deficit_valor_cop", "tiene_deficit"
        ]].style.format({
            "requerimiento_bruto": "{:,.2f}",
            "stock_disponible": "{:,.2f}",
            "requerimiento_neto": "{:,.2f}",
            "deficit_valor_cop": "$ {:,.0f}"
        }),
        use_container_width=True
    )
