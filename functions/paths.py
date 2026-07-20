import os
import sys
import shutil
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
    Crea una copia de seguridad del archivo de base de datos,
    con la fecha en el nombre, dentro de mf-app/backups.
    Si el archivo de la base de datos aún no existe, no hace nada.
    También elimina backups con más de 30 días de antigüedad.
    """
    ruta_db = obtener_ruta_db()

    if not ruta_db.exists():
        return

    carpeta_app = obtener_carpeta_app().parent
    carpeta_backups = carpeta_app / "backups"
    carpeta_backups.mkdir(parents=True, exist_ok=True)

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ruta_backup = carpeta_backups / f"mf-app_{fecha_hoy}.db"

    if not ruta_backup.exists():
        shutil.copy2(ruta_db, ruta_backup)

    limpiar_backups_viejos()

def limpiar_backups_viejos(dias=30):
    """
    Elimina los archivos de backup que tengan más de 'dias' días de antigüedad,
    para que la carpeta de backups no crezca indefinidamente.
    """
    carpeta_app = obtener_carpeta_app().parent
    carpeta_backups = carpeta_app / "backups"

    if not carpeta_backups.exists():
        return  # no hay carpeta de backups todavía, no hay nada que limpiar

    ahora = datetime.now()

    for archivo in carpeta_backups.glob("mf-app_*.db"):
        # Fecha de última modificación del archivo
        fecha_modificacion = datetime.fromtimestamp(archivo.stat().st_mtime)
        antiguedad = (ahora - fecha_modificacion).days

        if antiguedad > dias:
            archivo.unlink()  # elimina el archivo