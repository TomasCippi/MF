import logging
from datetime import datetime
from functions.paths import obtener_carpeta_app  # Solo depende de paths.py, sin ciclos

# Máxima cantidad de archivos de log (uno por día) que se conservan.
# Igual que con los backups, evita que la carpeta 'logs' crezca para
# siempre en una app que puede quedar años instalada en una PC.
MAXIMO_ARCHIVOS_LOG = 60


def obtener_carpeta_logs():
    """
    Devuelve la carpeta de logs dentro de mf-app, creándola si no existe.
    Ejemplo: mf-app/logs/
    """
    # obtener_carpeta_app() devuelve la carpeta 'db', subimos un nivel
    # para llegar a la carpeta raíz de la app (mf-app) y ahí crear 'logs'
    carpeta_app = obtener_carpeta_app().parent
    carpeta_logs = carpeta_app / "logs"
    carpeta_logs.mkdir(parents=True, exist_ok=True)
    return carpeta_logs


def _limpiar_logs_viejos(carpeta_logs, cantidad_maxima=MAXIMO_ARCHIVOS_LOG):
    """Mantiene como máximo 'cantidad_maxima' archivos .log, borrando los más viejos."""
    try:
        archivos = sorted(
            carpeta_logs.glob("*.log"),
            key=lambda archivo: archivo.stat().st_mtime,
            reverse=True
        )
        for archivo in archivos[cantidad_maxima:]:
            archivo.unlink()
    except Exception:
        # La limpieza de logs nunca debe romper el arranque de la app.
        pass


def obtener_logger(nombre="mf-app"):
    """
    Crea y devuelve un logger configurado para escribir en un archivo
    con el nombre de la fecha actual (ej: 2026-07-20.log), dentro de mf-app/logs.

    Registra desde nivel INFO (operaciones normales: alta, edición y baja
    de productos, cargas masivas, backups) hasta CRITICAL. Esto sirve para
    poder reconstruir qué pasó si el usuario reporta un problema, sin
    depender de la consola (que en el .exe final no se ve).
    """
    carpeta_logs = obtener_carpeta_logs()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_log = carpeta_logs / f"{fecha_hoy}.log"

    # getLogger con el mismo nombre siempre devuelve la misma instancia,
    # así evitamos crear loggers duplicados en distintas partes del programa.
    logger = logging.getLogger(nombre)
    logger.setLevel(logging.INFO)

    # Si el logger ya tiene handlers configurados (por ejemplo, porque esta
    # función ya se llamó antes), no los volvemos a agregar. Si no hacemos
    # esta verificación, cada llamada duplicaría las líneas en el log.
    if not logger.handlers:
        formato = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Handler que escribe los logs en el archivo del día
        handler_archivo = logging.FileHandler(archivo_log, encoding="utf-8")
        handler_archivo.setFormatter(formato)
        logger.addHandler(handler_archivo)

        # Handler que muestra los logs por consola (solo visible si hay terminal,
        # por ejemplo mientras desarrollamos; en el .exe final no se va a ver)
        handler_consola = logging.StreamHandler()
        handler_consola.setFormatter(formato)
        logger.addHandler(handler_consola)

        _limpiar_logs_viejos(carpeta_logs)

    return logger