"""
Tablero de Control de Abastecimiento y Operaciones - E2 SAS (Producción 4.0)
Archivo: app.py
Tecnología: Streamlit (Interfaz Ejecutiva Minimalista) + Persistencia en Supabase
"""

import os
import streamlit as st
import pandas as pd
import altair as alt
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
    initial_sidebar_state="expanded"
)

# Estilos CSS — SaaS Cobalt Blue (Production 4.0) High-Contrast Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    /* ── BASE & LIENZO PRINCIPAL ── */
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
    }
    .stApp {
        background-color: #F1F5F9 !important;
    }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1380px !important;
    }

    /* ── TIPOGRAFÍA Y TEXTO OSCURO OBLIGATORIO EN CONTENIDO PRINCIPAL ── */
    [data-testid="stMainBlockContainer"] h1,
    [data-testid="stMainBlockContainer"] h2,
    [data-testid="stMainBlockContainer"] h3,
    [data-testid="stMainBlockContainer"] h4,
    [data-testid="stMainBlockContainer"] h5,
    [data-testid="stMainBlockContainer"] h6 {
        color: #0F172A !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    [data-testid="stMainBlockContainer"] p,
    [data-testid="stMainBlockContainer"] span,
    [data-testid="stMainBlockContainer"] div {
        color: #1E293B;
    }
    [data-testid="stMainBlockContainer"] label,
    [data-testid="stMainBlockContainer"] [data-testid="stWidgetLabel"] p {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stCaptionContainer"] p,
    .stCaption {
        color: #475569 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }

    /* ── BARRA LATERAL COBALT BLUE ── */
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(175deg, #162B64 0%, #1E40AF 60%, #2563EB 100%) !important;
    }
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: #DBEAFE !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
    }
    [data-testid="stSidebar"] input {
        background: rgba(255, 255, 255, 0.16) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.3) !important;
        color: #FFFFFF !important;
        border-radius: 9px !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.18) !important;
    }
    [data-testid="stSidebar"] button {
        background: rgba(255, 255, 255, 0.16) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.3) !important;
        color: #FFFFFF !important;
        border-radius: 9px !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] button:hover {
        background: rgba(255, 255, 255, 0.28) !important;
    }

    /* ── ENCABEZADO PRINCIPAL (BRAND HEADER) ── */
    .brand-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 16px;
        padding: 1.1rem 1.6rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05);
    }
    .brand-title {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        color: #0F172A !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-title .accent {
        color: #2563EB !important;
    }
    .brand-subtitle {
        font-size: 0.82rem;
        color: #475569 !important;
        font-weight: 500;
        margin-top: 3px;
    }
    .brand-badge {
        font-size: 0.74rem;
        padding: 0.3rem 0.7rem;
        background: #EFF6FF !important;
        color: #1D4ED8 !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 20px;
        font-weight: 700;
    }
    .brand-badge-green {
        font-size: 0.74rem;
        padding: 0.3rem 0.7rem;
        background: #F0FDF4 !important;
        color: #15803D !important;
        border: 1px solid #BBF7D0 !important;
        border-radius: 20px;
        font-weight: 700;
    }

    /* ── TARJETAS KPI SUPERIORES ── */
    .kpi-card {
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 16px;
        padding: 1.25rem 1.35rem;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
    }
    .kpi-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.9rem;
    }
    .kpi-icon-box {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .kpi-badge {
        font-size: 0.72rem;
        font-weight: 700;
        padding: 0.22rem 0.6rem;
        border-radius: 20px;
        letter-spacing: 0.02em;
        white-space: nowrap;
    }
    .kpi-val {
        font-size: 1.95rem;
        font-weight: 800;
        color: #0F172A !important;
        letter-spacing: -0.04em;
        line-height: 1;
        margin-bottom: 0.35rem;
    }
    .kpi-lbl {
        font-size: 0.75rem;
        font-weight: 700;
        color: #475569 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-sub {
        font-size: 0.72rem;
        color: #64748B !important;
        margin-top: 3px;
        font-weight: 500;
    }

    /* ── NATIVE METRIC (ST.METRIC) ── */
    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 0.9rem 1.1rem !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04) !important;
    }
    [data-testid="stMetricLabel"] > div,
    [data-testid="stMetricLabel"] p {
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        color: #475569 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stMetricValue"] div {
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        letter-spacing: -0.03em !important;
    }

    /* ── PESTAÑAS (TABS) ALTO CONTRASTE ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
        background: #E2E8F0 !important;
        padding: 6px !important;
        border-radius: 14px !important;
        border: 1px solid #CBD5E1 !important;
        margin-bottom: 1.4rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px !important;
        padding: 0 22px !important;
        background-color: transparent !important;
        border-radius: 10px !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] div {
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(255, 255, 255, 0.8) !important;
    }
    .stTabs [data-baseweb="tab"]:hover p,
    .stTabs [data-baseweb="tab"]:hover span {
        color: #0F172A !important;
    }
    .stTabs [aria-selected="true"] {
        background: #2563EB !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    }
    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span,
    .stTabs [aria-selected="true"] div {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* ── SELECTBOX, INPUTS Y DROPDOWNS LEGIBLES ── */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] * {
        color: #0F172A !important;
        font-weight: 600 !important;
    }
    /* Menú desplegable cuando se hace clic */
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[role="listbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.12) !important;
    }
    li[role="option"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-size: 0.88rem !important;
        padding: 10px 14px !important;
    }
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: #EFF6FF !important;
        color: #1D4ED8 !important;
        font-weight: 700 !important;
    }

    .stTextInput input,
    .stNumberInput input {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        color: #0F172A !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }
    .stTextInput input:focus,
    .stNumberInput input:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }

    /* ── FILE UPLOADER (PESTAÑA 2 INGESTA) ── */
    [data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #94A3B8 !important;
        border-radius: 14px !important;
        padding: 1.2rem !important;
    }
    [data-testid="stFileUploader"] section {
        background-color: transparent !important;
    }
    [data-testid="stFileUploader"] * {
        color: #1E293B !important;
    }
    [data-testid="stFileUploader"] small {
        color: #64748B !important;
        font-weight: 500 !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #F1F5F9 !important;
        border: 1.5px solid #CBD5E1 !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }

    /* ── RADIO BUTTONS (PESTAÑA 3 DIAGNÓSTICO) ── */
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label div {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
    }

    /* ── CHECKBOX ── */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label p {
        color: #0F172A !important;
        font-weight: 600 !important;
    }

    /* ── MEMO CARD CON ALTO CONTRASTE ── */
    .memo-card {
        background: #FFFFFF !important;
        border: 1px solid #BFDBFE !important;
        border-left: 5px solid #2563EB !important;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 10px rgba(37, 99, 235, 0.06);
    }
    .memo-title {
        font-size: 0.86rem;
        font-weight: 800;
        color: #1E3A8A !important;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .memo-body {
        font-size: 0.9rem;
        color: #1E293B !important;
        line-height: 1.65;
        font-weight: 500;
    }
    .memo-action {
        margin-top: 0.7rem;
        padding: 0.55rem 0.9rem;
        background: #EFF6FF !important;
        border-radius: 9px;
        font-size: 0.85rem;
        color: #1D4ED8 !important;
        font-weight: 700;
        border: 1px solid #BFDBFE !important;
    }

    /* ── BOTONES ── */
    div[data-testid="stButton"] button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        padding: 0.5rem 1.2rem !important;
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 3px 12px rgba(37, 99, 235, 0.28) !important;
    }
    button[kind="primary"] * {
        color: #FFFFFF !important;
    }
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border: 1.5px solid #CBD5E1 !important;
    }
    button[kind="secondary"] * {
        color: #1E293B !important;
    }

    /* ── TABLAS DATAFRAME ── */
    [data-testid="stDataFrame"] {
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
        background: #FFFFFF !important;
    }

    /* ── ALERTAS (INFO, SUCCESS, WARNING, ERROR) ── */
    [data-testid="stAlert"] {
        border-radius: 12px !important;
        font-size: 0.88rem !important;
    }
    [data-testid="stAlert"] * {
        color: inherit !important;
        font-weight: 600 !important;
    }

    /* ── EXPANDER ── */
    [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.03);
    }
    [data-testid="stExpander"] summary * {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] * {
        color: #1E293B !important;
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
# ------------------------------------------------------------------------------
# BARRA LATERAL ESTILO COBALT BLUE SAAS
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.6rem 0 1rem 0;">
        <div style="font-size: 1.35rem; font-weight: 800; color: #FFFFFF; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.5rem;">⚡</span>
            <span>E2 SAS</span>
        </div>
        <div style="font-size: 0.8rem; color: #BFDBFE; font-weight: 500; margin-top: 3px;">
            Producción 4.0 & Cadena de Suministro
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.18); border-radius: 12px; padding: 0.85rem; margin-bottom: 1.2rem;">
        <div style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: #93C5FD; font-weight: 700;">Sesión Activa</div>
        <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-top: 2px;">{st.session_state['usuario_activo']}</div>
        <div style="display: flex; align-items: center; gap: 6px; margin-top: 6px;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: #4ADE80; box-shadow: 0 0 8px #4ADE80;"></span>
            <span style="font-size: 0.75rem; color: #BBF7D0; font-weight: 600;">Supabase PostgreSQL Live</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.75rem; color:#BFDBFE; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:4px;'>Gobernanza de Compras</div>", unsafe_allow_html=True)
    nuevo_umbral = st.number_input(
        "Umbral Autorización Gerencial ($ COP):",
        min_value=1_000_000.0,
        max_value=100_000_000.0,
        value=float(st.session_state["umbral_monto"]),
        step=5_000_000.0,
        format="%f"
    )
    if nuevo_umbral != st.session_state["umbral_monto"]:
        st.session_state["umbral_monto"] = nuevo_umbral
        res_reload = orquestador.generar_propuestas_reposicion(umbral_alto_valor_cop=nuevo_umbral)
        st.session_state["propuestas_activas"] = res_reload["propuestas"]
        st.session_state["conteo_paradas"] = res_reload["conteo_paradas"]
        st.session_state["inversion_total_formato"] = res_reload["inversion_total_formato"]
        st.rerun()

    st.markdown("---")
    if st.button("↻ Sincronizar Supabase", use_container_width=True):
        st.cache_data.clear()
        res_sync = orquestador.generar_propuestas_reposicion(umbral_alto_valor_cop=st.session_state["umbral_monto"])
        st.session_state["propuestas_activas"] = res_sync["propuestas"]
        st.session_state["conteo_paradas"] = res_sync["conteo_paradas"]
        st.session_state["inversion_total_formato"] = res_sync["inversion_total_formato"]
        st.rerun()

    st.markdown("""
    <div style="margin-top: 1.5rem; font-size: 0.76rem; color: #DBEAFE; line-height: 1.6;">
        <div>• <strong>Protocolo B4_02:</strong> Ingesta 5 pasos</div>
        <div>• <strong>Integridad:</strong> 3FN normalizada</div>
        <div>• <strong>Anti-Alucinación:</strong> Núcleo determinístico</div>
        <div>• <strong>Modelo:</strong> EOQ / ROP / ERI / SLA / MRP</div>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ENCABEZADO PRINCIPAL (SAAS HEADER)
# ------------------------------------------------------------------------------
propuestas_pendientes = st.session_state.get("propuestas_activas", [])
n_alertas = len(propuestas_pendientes)

st.markdown(f"""
<div class="brand-header">
    <div>
        <div class="brand-title">
            <span style="font-size: 1.4rem;">⚡</span> <span class="accent">E2 SAS</span> &nbsp;·&nbsp; Control de Abastecimiento &amp; Operaciones
        </div>
        <div class="brand-subtitle">
            Motor determinístico EOQ/ROP/ERI/SLA/MRP · Supervisión humana obligatoria · Salvaguardas anti-alucinación
        </div>
    </div>
    <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
        <span class="brand-badge-green">● Operativo</span>
        <span class="brand-badge">Protocolo B4_02</span>
        {f'<span class="brand-badge" style="background:#FEF2F2; color:#B91C1C; border-color:#FECACA;">⚠ {n_alertas} pendientes</span>' if n_alertas > 0 else ''}
    </div>
</div>
""", unsafe_allow_html=True)

# ── 4 KPI CARDS ──────────────────────────────────────────────────────────────
st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4, gap="small")

with m1:
    eri_exactos = eri_tg.get('skus_exactos', 0)
    eri_total   = eri_tg.get('total_skus', 0)
    eri_pct     = eri_tg.get('eri_porcentaje_exactitud', '—')
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-top">
        <div class="kpi-icon-box" style="background:#EFF6FF; color:#2563EB;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
          </svg>
        </div>
        <span class="kpi-badge" style="background:#DCFCE7; color:#15803D;">{eri_pct}</span>
      </div>
      <div class="kpi-val">{eri_exactos}<span style="font-size:1rem; color:#94A3B8; font-weight:600;"> / {eri_total}</span></div>
      <div class="kpi-lbl">Exactitud de Inventario (ERI)</div>
      <div class="kpi-sub">SKUs sin descuadre patrimonial</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    inv_fmt = st.session_state.get('inversion_total_formato', '$ 0')
    bajo_rop = len(propuestas_pendientes)
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-top">
        <div class="kpi-icon-box" style="background:#FEF2F2; color:#DC2626;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/>
          </svg>
        </div>
        <span class="kpi-badge" style="background:#FEE2E2; color:#B91C1C;">{bajo_rop} Bajo ROP</span>
      </div>
      <div class="kpi-val" style="font-size:1.4rem;">{inv_fmt}</div>
      <div class="kpi-lbl">Inversión Reorden Sugerida</div>
      <div class="kpi-sub">Reposición óptima EOQ/ROP</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    sla_fmt  = kpi_sla.get('sla_global_formato', '—')
    mora_d   = kpi_sla.get('mora_promedio_cuando_tarde_dias', 0)
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-top">
        <div class="kpi-icon-box" style="background:#FFFBEB; color:#D97706;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
        <span class="kpi-badge" style="background:#FEF3C7; color:#B45309;">+{mora_d}d mora</span>
      </div>
      <div class="kpi-val">{sla_fmt}</div>
      <div class="kpi-lbl">Cumplimiento SLA Proveedores</div>
      <div class="kpi-sub">Entregas a tiempo OTD históricas</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    a_pct  = kpi_abc['clases']['A']['pct_valor']
    a_skus = kpi_abc['clases']['A']['total_skus']
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-top">
        <div class="kpi-icon-box" style="background:#FAF5FF; color:#7C3AED;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M21.21 15.89A10 10 0 118 2.83"/><path d="M22 12A10 10 0 0012 2v10z"/>
          </svg>
        </div>
        <span class="kpi-badge" style="background:#EDE9FE; color:#6D28D9;">Pareto 80/20</span>
      </div>
      <div class="kpi-val">{a_pct}%</div>
      <div class="kpi-lbl">Concentración Clase A</div>
      <div class="kpi-sub">{a_skus} SKUs concentran el valor</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

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
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #DEE5EE; border-radius:10px; padding:6px 12px; margin-top:24px; text-align:center;">
                <span style="font-size:0.68rem; color:#64748B; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">Próxima OC:</span>
                <span style="font-size:0.95rem; font-weight:800; color:#1E3A8A; margin-left:6px;">{siguiente_oc}</span>
            </div>
            """, unsafe_allow_html=True)
        with fc4:
            st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
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
                st.markdown(f"""
                <div class="memo-card">
                    <div class="memo-title">📋 {memo['dictamen']}</div>
                    <div class="memo-body">{memo['memo_ejecutivo']}</div>
                    <div class="memo-action">
                        ➜ <strong>Directriz:</strong> {memo['accion_recomendada']}
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
            <div style="background:#FFFFFF; border:1px solid #DEE5EE; border-radius:12px; padding:0.9rem 1rem; margin-bottom:0.8rem; box-shadow:0 1px 4px rgba(15,23,42,0.03);">
                <div style="font-size:0.7rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em;">Lote Estándar (Sin Paradas)</div>
                <div style="font-size:1.35rem; font-weight:800; color:#0F172A; margin:2px 0;">{estandar_count} <span style="font-size:0.75rem; font-weight:600; color:#10B981;">Listas para OC</span></div>
                <div style="font-size:0.75rem; color:#64748B;">Cumplen SLA, saldo verificado y bajo umbral.</div>
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
                # Lectura robusta con soporte UTF-8 y fallback a latin-1 para tildes
                try:
                    df_up = pd.read_csv(archivo_subido)
                except UnicodeDecodeError:
                    archivo_subido.seek(0)
                    df_up = pd.read_csv(archivo_subido, encoding="latin-1")

                res_ing = cambios.ejecutar_ingesta_5_pasos(
                    tabla_destino=tabla_seleccionada,
                    df_entrante=df_up,
                    nombre_archivo=archivo_subido.name,
                    usuario=st.session_state["usuario_activo"],
                    modo_idempotente=True,
                    persistir_en_bd=persistir_db
                )
                st.session_state["ultimo_reporte_ingesta"] = res_ing
                if res_ing.get("exito") and persistir_db and res_ing.get("filas_cargadas", 0) > 0:
                    st.cache_data.clear()
                    res_reload = orquestador.generar_propuestas_reposicion(umbral_alto_valor_cop=st.session_state["umbral_monto"])
                    st.session_state["propuestas_activas"] = res_reload["propuestas"]
                    st.session_state["conteo_paradas"] = res_reload["conteo_paradas"]
                    st.session_state["inversion_total_formato"] = res_reload["inversion_total_formato"]
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
                paso_f = res_ing.get("paso_fallido", "VALIDACIÓN")
                st.error(f"🛑 CARGA RECHAZADA EN PASO '{paso_f}'")
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
            <div style="background:#FFFFFF; border:1px solid #DEE5EE; border-radius:14px; padding:1.2rem; box-shadow:0 1px 4px rgba(15,23,42,0.03);">
                <div style="font-size:0.72rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em;">Resumen de Veracidad Patrimonial</div>
                <div style="font-size:1.85rem; font-weight:800; color:#0F172A; letter-spacing:-0.03em; margin:0.3rem 0;">{eri_tg.get('eri_porcentaje_exactitud', '74.3%')} <span style="font-size:0.85rem; font-weight:600; color:#10B981;">ERI</span></div>
                <div style="display:flex; flex-direction:column; gap:6px; margin-top:0.6rem;">
                    <div style="display:flex; justify-content:space-between; font-size:0.82rem; padding:6px 10px; background:#F0FDF4; border-radius:8px; border:1px solid #DCFCE7;">
                        <span style="color:#166534; font-weight:600;">Cuadrados:</span>
                        <strong style="color:#15803D;">{eri_tg.get('skus_exactos', 0)} SKUs</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.82rem; padding:6px 10px; background:#FEF2F2; border-radius:8px; border:1px solid #FEE2E2;">
                        <span style="color:#991B1B; font-weight:600;">Descuadrados:</span>
                        <strong style="color:#DC2626;">{eri_tg.get('skus_descuadrados', 0)} SKUs</strong>
                    </div>
                </div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:0.8rem; padding-top:0.6rem; border-top:1px solid #F1F5F9;">
                    Desalineación Total:<br>
                    <strong style="font-size:1rem; color:#0F172A;">{eri_tg.get('desalineacion_contable_bruta', '$ 0 COP')}</strong>
                </div>
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
        col_c1, col_c2 = st.columns([1.2, 1.8])
        with col_c1:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:1.1rem; box-shadow:0 2px 8px rgba(15,23,42,0.03);">
                <div style="font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.6rem;">Matriz Pareto Anualizada</div>
                <div style="display:flex; flex-direction:column; gap:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:#EFF6FF; border-radius:8px; border:1px solid #BFDBFE;">
                        <div>
                            <span style="font-weight:700; color:#1D4ED8; font-size:0.85rem;">Clase A (80% Valor)</span>
                            <div style="font-size:0.75rem; color:#64748B;">{kpi_abc['clases']['A']['total_skus']} SKUs clave</div>
                        </div>
                        <span style="font-weight:800; color:#1E3A8A; font-size:1.05rem;">{kpi_abc['clases']['A']['pct_valor']}%</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:#FFF7ED; border-radius:8px; border:1px solid #FED7AA;">
                        <div>
                            <span style="font-weight:700; color:#C2410C; font-size:0.85rem;">Clase B (15% Valor)</span>
                            <div style="font-size:0.75rem; color:#64748B;">{kpi_abc['clases']['B']['total_skus']} SKUs control</div>
                        </div>
                        <span style="font-weight:800; color:#9A3412; font-size:1.05rem;">{kpi_abc['clases']['B']['pct_valor']}%</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:#FEFCE8; border-radius:8px; border:1px solid #FEF08A;">
                        <div>
                            <span style="font-weight:700; color:#A16207; font-size:0.85rem;">Clase C (5% Valor)</span>
                            <div style="font-size:0.75rem; color:#64748B;">{kpi_abc['clases']['C']['total_skus']} SKUs baja rotación</div>
                        </div>
                        <span style="font-weight:800; color:#854D0E; font-size:1.05rem;">{kpi_abc['clases']['C']['pct_valor']}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_c2:
            df_donut = pd.DataFrame([
                {"Clase": "Clase A (80% Valor)", "Porcentaje": float(kpi_abc['clases']['A']['pct_valor'])},
                {"Clase": "Clase B (15% Valor)", "Porcentaje": float(kpi_abc['clases']['B']['pct_valor'])},
                {"Clase": "Clase C (5% Valor)", "Porcentaje": float(kpi_abc['clases']['C']['pct_valor'])}
            ])
            chart_donut = alt.Chart(df_donut).mark_arc(innerRadius=60, stroke="#FFFFFF", strokeWidth=2).encode(
                theta=alt.Theta("Porcentaje:Q"),
                color=alt.Color(
                    "Clase:N",
                    scale=alt.Scale(
                        domain=["Clase A (80% Valor)", "Clase B (15% Valor)", "Clase C (5% Valor)"],
                        range=["#2563EB", "#F97316", "#FBBF24"]
                    ),
                    legend=alt.Legend(title="Distribución Pareto", orient="right")
                ),
                tooltip=["Clase", "Porcentaje"]
            ).properties(height=210, title="Distribución Visual del Consumo Total")
            st.altair_chart(chart_donut, use_container_width=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.88rem; font-weight:700; color:#B91C1C;'>SKUs Inmovilizados de Plata Muerta (Cero Salidas en Historial)</div>", unsafe_allow_html=True)
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

        chart_sla = alt.Chart(df_sla).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6, size=20).encode(
            x=alt.X("sla_cumplimiento_pct:Q", title="SLA Cumplimiento a Tiempo (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("categoria:N", sort="-x", title=None),
            color=alt.condition(
                alt.datum.sla_cumplimiento_pct >= 95,
                alt.value("#10B981"),
                alt.value("#2563EB")
            ),
            tooltip=["categoria", "total_oc_cerradas", "a_tiempo", "retrasadas", "sla_cumplimiento_formato", "mora_promedio_dias"]
        ).properties(height=160, title="Nivel de Servicio OTD por Familia de Proveedores (Verde = Meta 95%)")
        st.altair_chart(chart_sla, use_container_width=True)

        st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#0F172A; margin: 0.6rem 0 0.3rem 0;'>Auditoría Detallada de Desfase de Lead Time por Proveedor</div>", unsafe_allow_html=True)
        st.dataframe(
            df_sla[[
                "categoria", "total_oc_cerradas", "a_tiempo", "retrasadas",
                "sla_cumplimiento_formato", "mora_promedio_dias", "lead_time_erp_dias",
                "lead_time_real_dias", "desfase_dias"
            ]],
            use_container_width=True,
            height=260
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
