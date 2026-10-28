"""
Módulo de Acceso a Datos - E2 SAS (Producción 4.0)
Responsabilidad: Conectar a Supabase mediante la API REST PostgREST y suministrar
los datos a los módulos analíticos.

Contrato:
- Entrada: nombre de tabla o vista, filtros opcionales (dict), select, limit, order
- Salida: list[dict] con los registros serializados
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Dict, List, Optional


def obtener_configuracion() -> Dict[str, str]:
    """
    Carga variables de entorno buscando el archivo .env en la raíz del proyecto.
    """
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    raiz_proyecto = os.path.dirname(directorio_actual)
    ruta_env = os.path.join(raiz_proyecto, ".env")

    config = {
        "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
        "SUPABASE_KEY": (
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
            or os.environ.get("SUPABASE_KEY")
            or os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
        )
    }

    if os.path.exists(ruta_env):
        with open(ruta_env, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#") and "=" in linea:
                    k, v = linea.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == "SUPABASE_URL" and not config["SUPABASE_URL"]:
                        config["SUPABASE_URL"] = v
                    elif k in ("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "SUPABASE_KEY", "SUPABASE_PUBLISHABLE_KEY") and not config["SUPABASE_KEY"]:
                        config["SUPABASE_KEY"] = v

    if not config["SUPABASE_URL"] or not config["SUPABASE_KEY"]:
        raise ValueError(
            "Configuración incompleta: SUPABASE_URL o API Key no encontrados en variables ni en .env"
        )

    return config


def consultar(
    objeto: str,
    filtros: Optional[Dict[str, Any]] = None,
    columnas: str = "*",
    limite: Optional[int] = None,
    orden: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Ejecuta una consulta GET sobre una tabla o vista analítica en Supabase.
    Maneja paginación transparente si limite es None.
    
    Args:
        objeto: Nombre de la tabla o vista (e.g. 'vista_clasificacion_abc')
        filtros: Diccionario de filtros con sintaxis PostgREST (e.g. {'categoria': 'eq.Vidrio'})
        columnas: Lista de columnas separadas por coma (default '*')
        limite: Cantidad máxima de registros
        orden: Criterio de ordenamiento (e.g. 'sku.asc', 'valor_consumo_anual_cop.desc')

    Returns:
        Lista de diccionarios con los registros retornados
    """
    cfg = obtener_configuracion()
    url_base = cfg["SUPABASE_URL"].rstrip("/")
    api_key = cfg["SUPABASE_KEY"]

    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Si se pide un límite específico, hacemos una única solicitud
    if limite is not None:
        params: Dict[str, str] = {"select": columnas, "limit": str(limite)}
        if orden:
            params["order"] = orden
        if filtros:
            for k, v in filtros.items():
                params[k] = str(v)

        query_str = urllib.parse.urlencode(params)
        endpoint = f"{url_base}/rest/v1/{objeto}?{query_str}"
        req = urllib.request.Request(endpoint, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            cuerpo = e.read().decode("utf-8")
            raise RuntimeError(f"Error HTTP {e.code} consultando '{objeto}': {cuerpo}") from e

    # Si no se especifica límite, paginamos en bloques de 1000 hasta traer todos
    tamano_pagina = 1000
    offset = 0
    todos_los_registros: List[Dict[str, Any]] = []

    while True:
        params = {
            "select": columnas,
            "limit": str(tamano_pagina),
            "offset": str(offset)
        }
        if orden:
            params["order"] = orden
        if filtros:
            for k, v in filtros.items():
                params[k] = str(v)

        query_str = urllib.parse.urlencode(params)
        endpoint = f"{url_base}/rest/v1/{objeto}?{query_str}"
        req = urllib.request.Request(endpoint, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req) as resp:
                lote = json.loads(resp.read().decode("utf-8"))
                todos_los_registros.extend(lote)
                if len(lote) < tamano_pagina:
                    break
                offset += tamano_pagina
        except urllib.error.HTTPError as e:
            cuerpo = e.read().decode("utf-8")
            raise RuntimeError(f"Error HTTP {e.code} consultando '{objeto}': {cuerpo}") from e
        except Exception as e:
            raise RuntimeError(f"Error de conexión consultando '{objeto}': {str(e)}") from e

    return todos_los_registros


import math


def _sanitizar_valor(val: Any) -> Any:
    """Convierte NaN, Inf y NaT en None para serialización JSON estándar válida."""
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    str_val = str(val).strip()
    if str_val in ("<NA>", "NaT", "nan", "NaN", "None", "NULL"):
        return None
    return val


def _sanitizar_registros(registros: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Limpia recursivamente una lista de diccionarios de registro."""
    return [
        {k: _sanitizar_valor(v) for k, v in r.items()}
        for r in registros
    ]


def insertar(
    tabla: str,
    registros: List[Dict[str, Any]],
    ignorar_duplicados: bool = False,
    on_conflict: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Inserta uno o varios registros en una tabla de Supabase.
    Soporta resolución idempotente ignore-duplicates (ON CONFLICT DO NOTHING).

    Args:
        tabla: Nombre de la tabla destino
        registros: Lista de diccionarios a insertar
        ignorar_duplicados: Si True, no falla ante conflicto de clave primaria
        on_conflict: Columnas de clave primaria para la resolución (e.g. 'sku', 'periodo,producto')
    """
    if not registros:
        return []

    cfg = obtener_configuracion()
    url_base = cfg["SUPABASE_URL"].rstrip("/")
    api_key = cfg["SUPABASE_KEY"]

    params_url = ""
    if on_conflict:
        params_url = f"?on_conflict={urllib.parse.quote(on_conflict)}"

    endpoint = f"{url_base}/rest/v1/{tabla}{params_url}"
    prefer_header = "resolution=ignore-duplicates,return=representation" if ignorar_duplicados else "return=representation"

    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": prefer_header
    }

    registros_limpios = _sanitizar_registros(registros)
    datos_bytes = json.dumps(registros_limpios).encode("utf-8")
    req = urllib.request.Request(endpoint, data=datos_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data) if data else []
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8")
        raise RuntimeError(f"Error HTTP {e.code} insertando en '{tabla}': {cuerpo}") from e
    except Exception as e:
        raise RuntimeError(f"Error de conexión insertando en '{tabla}': {str(e)}") from e


def actualizar(
    tabla: str,
    filtros: Dict[str, Any],
    valores: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Actualiza registros en una tabla de Supabase basados en filtros PostgREST.
    """
    if not filtros or not valores:
        return []

    cfg = obtener_configuracion()
    url_base = cfg["SUPABASE_URL"].rstrip("/")
    api_key = cfg["SUPABASE_KEY"]

    params: Dict[str, str] = {}
    for k, v in filtros.items():
        params[k] = str(v)

    query_str = urllib.parse.urlencode(params)
    endpoint = f"{url_base}/rest/v1/{tabla}?{query_str}"
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation"
    }

    datos_bytes = json.dumps(valores).encode("utf-8")
    req = urllib.request.Request(endpoint, data=datos_bytes, headers=headers, method="PATCH")

    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data) if data else []
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8")
        raise RuntimeError(f"Error HTTP {e.code} actualizando en '{tabla}': {cuerpo}") from e
    except Exception as e:
        raise RuntimeError(f"Error de conexión actualizando en '{tabla}': {str(e)}") from e


if __name__ == "__main__":
    print("Probando módulo nucleo.datos...")
    try:
        registros = consultar("vista_clasificacion_abc", limite=3)
        print(f"Éxito: Se obtuvieron {len(registros)} registros de vista_clasificacion_abc:")
        for r in registros:
            print(f" - {r.get('sku')}: {r.get('descripcion')} | {r.get('clasificacion_abc')} | {r.get('valor_consumo_anual_formato')}")
    except Exception as err:
        print(f"Fallo en prueba: {err}")
