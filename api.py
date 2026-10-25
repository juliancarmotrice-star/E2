"""
API Backend RESTful para Sistema de Producción 4.0 - E2 SAS
Archivo: api.py
Tecnología: FastAPI + Uvicorn + Supabase + Núcleo Determinístico

Conecta las interfaces generadas por Google Stitch (o cualquier cliente React/Web/Mobile)
con los motores de cálculo en Python y la base de datos Supabase.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import orquestador
import nucleo.exactitud_eri as eri
import nucleo.clasificacion_abc as abc
import nucleo.sla_proveedores as sla
import nucleo.explosion_mrp as mrp
import nucleo.reposicion_eoq_rop as reposicion
import nucleo.explicador_ia as explicador

app = FastAPI(
    title="E2 SAS · Producción 4.0 API",
    description="API REST de conexión para el frontend de Google Stitch con el motor industrial de inventarios.",
    version="1.0.0"
)

# Permitir CORS para desarrollo local y despliegues frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# MODELOS DE ENTRADA (PYDANTIC)
# ==========================================
class AprobacionRequest(BaseModel):
    propuesta: Dict[str, Any]
    decidido_por: Optional[str] = "Planeador de Compras"
    comentarios: Optional[str] = None

class RechazoRequest(BaseModel):
    propuesta: Dict[str, Any]
    motivo_rechazo: str
    decidido_por: Optional[str] = "Planeador de Compras"

class JustificacionRequest(BaseModel):
    propuesta: Dict[str, Any]


# ==========================================
# RUTAS DE CONSULTA Y ANALÍTICA (READ)
# ==========================================

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "E2 SAS Producción 4.0 API"}

@app.get("/api/kpis")
def get_kpis():
    """Obtiene indicadores globales para el dashboard ejecutivo."""
    diag_eri = eri.obtener_diagnostico_eri()
    items_eri = len(diag_eri)
    exactos = sum(1 for d in diag_eri if d.get("discrepancia_unidades") == 0)
    eri_pct = round((exactos / items_eri) * 100, 2) if items_eri > 0 else 0.0

    plan_eoq = reposicion.obtener_plan_compras_sugeridas()
    propuestas = orquestador.generar_propuestas_reposicion()

    items_abc = abc.obtener_clasificacion_abc()
    clase_a = sum(1 for i in items_abc if i.get("clasificacion_abc") == "A")

    return {
        "eri_exactitud_pct": eri_pct,
        "total_skus": items_eri,
        "skus_clase_a": clase_a,
        "items_en_quiebre": plan_eoq.get("total_items_a_pedir", 0),
        "inversion_sugerida_cop": propuestas.get("inversion_total_cop", 0),
        "inversion_sugerida_formato": propuestas.get("inversion_total_formato", "$ 0 COP"),
        "conteo_paradas": propuestas.get("conteo_paradas", {})
    }

@app.get("/api/eri")
def get_eri():
    """Diagnóstico de Exactitud de Registro de Inventario (Kardex vs Conteo vs Cuaderno)."""
    return eri.obtener_diagnostico_eri()

@app.get("/api/abc")
def get_abc():
    """Clasificación Pareto 80/15/5 y valor de consumo anualizado."""
    return abc.obtener_clasificacion_abc()

@app.get("/api/sla")
def get_sla():
    """Métricas de cumplimiento de entrega por categoría de proveedor."""
    return sla.obtener_metricas_sla_por_categoria()

@app.get("/api/mrp")
def get_mrp():
    """Explosión de necesidades netas MRP con árbol de producto BOM."""
    return mrp.obtener_plan_requerimientos_mrp()

@app.get("/api/reposicion")
def get_reposicion():
    """Plan determinístico EOQ, ROP y Stock de Seguridad."""
    return reposicion.obtener_plan_compras_sugeridas()

@app.get("/api/propuestas")
def get_propuestas():
    """Propuestas de compra calculadas en memoria con evaluación de criterios de parada."""
    return orquestador.generar_propuestas_reposicion()


# ==========================================
# RUTAS TRANSACCIONALES (WRITE / ORCHESTRATOR)
# ==========================================

@app.post("/api/propuestas/aprobar")
def post_aprobar(body: AprobacionRequest):
    """Aprueba una propuesta y emite la OC en Supabase."""
    try:
        resultado = orquestador.aprobar_propuesta(
            propuesta=body.propuesta,
            decidido_por=body.decidido_por,
            comentarios=body.comentarios
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/propuestas/rechazar")
def post_rechazar(body: RechazoRequest):
    """Rechaza una propuesta y audita la causa en Supabase."""
    try:
        resultado = orquestador.rechazar_propuesta(
            propuesta=body.propuesta,
            motivo_rechazo=body.motivo_rechazo,
            decidido_por=body.decidido_por
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/explicador/justificar")
def post_justificar(body: JustificacionRequest):
    """Genera un dictamen ejecutivo de riesgo y justificación de compra con IA."""
    try:
        texto = explicador.explicar_decision_compra(body.propuesta)
        return {"justificacion": texto}
    except Exception as e:
        return {"justificacion": f"No se pudo generar dictamen de IA: {str(e)}"}


# ==========================================
# SERVIDORES DE INTERFAZ STITCH (FRONTEND)
# ==========================================
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "stitch_industrial_supply_chain_dashboard")
if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="stitch_app")

    @app.get("/")
    def index():
        return RedirectResponse(url="/app/e2_sas_control_dashboard/code.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

