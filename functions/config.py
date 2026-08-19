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

def establecer_proximo_remito(numero_usado):
    """
    Guarda como próximo remito el número siguiente al que el usuario
    efectivamente usó en la factura (numero_usado + 1), sin importar
    cuál era el valor guardado antes.
    """
    config = _leer_config()
    config["proximo_remito"] = numero_usado + 1
    _guardar_config(config)

def _guardar_config(config):
    """Sobreescribe el archivo config.json con el diccionario dado."""
    ruta = _obtener_ruta_config()
    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(config, archivo, indent=2)
    except Exception as e:
        logger.error(f"No se pudo guardar config.json: {e}")
        raise


def obtener_proximo_remito():
    """
    Devuelve el próximo número de remito a usar (empieza en 1 si nunca
    se guardó nada todavía). No modifica nada, solo lee.
    """
    config = _leer_config()
    return config.get("proximo_remito", 1)

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

def obtener_email_vendedor():
    """Devuelve el email configurado para mostrar en las exportaciones."""
    config = _leer_config()
    return config.get("email_vendedor", "distribuidoramf@gmail.com")


def guardar_email_vendedor(email):
    config = _leer_config()
    config["email_vendedor"] = email
    _guardar_config(config)

def obtener_direccion_empresa():
    """Dirección que aparece en las facturas (arriba, junto al cliente)."""
    config = _leer_config()
    return config.get("direccion_empresa", "Llavallol 5470, C.A.B.A.")


def guardar_direccion_empresa(direccion):
    config = _leer_config()
    config["direccion_empresa"] = direccion
    _guardar_config(config)

def obtener_productos_por_pagina():
    """Cantidad de productos a mostrar por página en Stock."""
    config = _leer_config()
    return config.get("productos_por_pagina", 20)


def guardar_productos_por_pagina(cantidad):
    config = _leer_config()
    config["productos_por_pagina"] = cantidad
    _guardar_config(config)
