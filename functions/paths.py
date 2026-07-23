import os
import sys
import shutil
import gzip
from datetime import datetime
from pathlib import Path

def obtener_carpeta_app():
    """
    Determina la carpeta donde se guardarán los datos de la app
    según el sistema operativo, y la crea si no existe.

    - En Windows: %APPDATA%\\mf-app\\db
    - En Linux:   ~/.local/share/mf-app/db

    Devuelve un objeto Path apuntando a la carpeta 'db'.
    """
    sistema = sys.platform  # Detecta el sistema operativo actual

    if sistema.startswith("win"):
        # En Windows, usamos la variable de entorno APPDATA
        base = os.getenv("APPDATA")
        if not base:
            # Si por algún motivo no existe APPDATA, usamos la carpeta home como respaldo
            base = str(Path.home())
        carpeta_app = Path(base) / "mf-app"
    else:
        # En Linux (y sistemas tipo Unix), usamos el estándar XDG
        carpeta_app = Path.home() / ".local" / "share" / "mf-app"

    carpeta_db = carpeta_app / "db"

    # Crea la carpeta (y todas las carpetas padre necesarias) si no existen.
    # exist_ok=True evita que tire error si ya existe.
    carpeta_db.mkdir(parents=True, exist_ok=True)

    return carpeta_db


def obtener_ruta_db():
    """
    Devuelve la ruta completa (carpeta + nombre de archivo) 
    al archivo de base de datos SQLite.
    """
    carpeta_db = obtener_carpeta_app()
    return carpeta_db / "mf-app.db"

def hacer_backup_db():
    """
    Crea un backup NUEVO y comprimido del archivo de base de datos, con
    fecha y hora exacta en el nombre. Cada acción (crear, editar, eliminar,
    carga masiva) genera su propio archivo, sin pisar los anteriores.

    El backup se guarda comprimido con gzip (extensión .db.gz), lo que
    reduce bastante su peso comparado con copiar el archivo tal cual.

    Después de crear el backup, llama a limpiar_backups_viejos() para
    mantener como máximo 30 backups guardados.
    """
    ruta_db = obtener_ruta_db()

    if not ruta_db.exists():
        return  # no hay nada que respaldar todavía

    carpeta_app = obtener_carpeta_app().parent
    carpeta_backups = carpeta_app / "backups"
    carpeta_backups.mkdir(parents=True, exist_ok=True)

    momento = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ruta_backup = carpeta_backups / f"mf-app_{momento}.db.gz"

    # Lee el archivo original y lo escribe comprimido con gzip
    with open(ruta_db, "rb") as archivo_original:
        with gzip.open(ruta_backup, "wb") as archivo_comprimido:
            shutil.copyfileobj(archivo_original, archivo_comprimido)

    limpiar_backups_viejos()


def limpiar_backups_viejos(cantidad_maxima=30):
    """
    Mantiene como máximo 'cantidad_maxima' backups guardados.
    Si hay más, elimina los más viejos (según fecha de modificación),
    dejando siempre los más recientes.
    """
    carpeta_app = obtener_carpeta_app().parent
    carpeta_backups = carpeta_app / "backups"

    if not carpeta_backups.exists():
        return

    backups = sorted(
        carpeta_backups.glob("mf-app_*.db.gz"),
        key=lambda archivo: archivo.stat().st_mtime,
        reverse=True
    )

    backups_a_eliminar = backups[cantidad_maxima:]

    for archivo in backups_a_eliminar:
        archivo.unlink()

def obtener_carpeta_imgs():
    """
    Devuelve la carpeta donde se guardan las imágenes de los productos,
    dentro de la carpeta 'db' (mf-app/db/imgs), creándola si no existe.
    """
    carpeta_db = obtener_carpeta_app()
    carpeta_imgs = carpeta_db / "imgs"
    carpeta_imgs.mkdir(parents=True, exist_ok=True)
    return carpeta_imgs