"""
functions/config.py

Guarda configuración simple y persistente de la app (por ahora, solo
el próximo número de remito) en un archivo config.json dentro de la
carpeta de datos de la app.
"""

import json

from functions.paths import obtener_carpeta_app
from functions.logger import obtener_logger

logger = obtener_logger()


def _obtener_ruta_config():
    """Devuelve la ruta al archivo config.json (mismo nivel que la carpeta db)."""
    carpeta_app = obtener_carpeta_app().parent
    return carpeta_app / "config.json"


def _leer_config():
    """Lee el archivo config.json. Si no existe, devuelve un diccionario vacío."""
    ruta = _obtener_ruta_config()
    if not ruta.exists():
        return {}

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except Exception as e:
        logger.warning(f"No se pudo leer config.json, se usará configuración vacía: {e}")
        return {}


def _guardar_config(config):
    """Sobreescribe el archivo config.json con el diccionario dado."""
    ruta = _obtener_ruta_config()
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(config, archivo, indent=2)


def obtener_proximo_remito():
    """
    Devuelve el próximo número de remito a usar (empieza en 1 si nunca
    se guardó nada todavía). No modifica nada, solo lee.
    """
    config = _leer_config()
    return config.get("proximo_remito", 1)


def incrementar_remito():
    """
    Suma 1 al número de remito guardado y lo persiste. Se llama cuando
    se confirma/exporta un pedido, para que el próximo ya venga
    autocompletado con el siguiente número.
    """
    config = _leer_config()
    actual = config.get("proximo_remito", 1)
    config["proximo_remito"] = actual + 1
    _guardar_config(config)

def obtener_ruta_facturas():
    """
    Devuelve la carpeta donde se guardan las facturas. Si el usuario
    nunca la configuró, usa mf-app/facturas por defecto.
    """
    config = _leer_config()
    ruta_guardada = config.get("ruta_facturas")

    if ruta_guardada:
        return ruta_guardada

    carpeta_app = obtener_carpeta_app().parent
    carpeta_default = carpeta_app / "facturas"
    carpeta_default.mkdir(parents=True, exist_ok=True)
    return str(carpeta_default)


def guardar_ruta_facturas(ruta):
    """Guarda la carpeta elegida por el usuario para futuras facturas."""
    config = _leer_config()
    config["ruta_facturas"] = ruta
    _guardar_config(config)