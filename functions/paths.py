import gzip
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

# Cuántos backups recientes se guardan siempre, y por cuántos días se
# conserva además el último backup de cada día.
BACKUPS_RECIENTES = 30
DIAS_BACKUP_DIARIO = 60


def _log():
    # Se importa acá adentro para evitar imports circulares con el logger
    from functions.logger import obtener_logger
    return obtener_logger()


def obtener_ruta_assets():
    """
    Devuelve la ruta a la carpeta 'assets', tanto si la app corre como
    script normal (desarrollo) como si corre empaquetada con PyInstaller
    en modo --onefile (donde los archivos se extraen a una carpeta
    temporal indicada en sys._MEIPASS).
    """
    if getattr(sys, "frozen", False):
        # Corriendo como .exe empaquetado
        base = sys._MEIPASS
    else:
        # Corriendo como script normal: la raíz del proyecto es un
        # nivel arriba de la carpeta 'functions'
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base, "assets")


def obtener_carpeta_app():
    """
    Determina la carpeta donde se guardarán los datos de la app
    según el sistema operativo, y la crea si no existe.

    - En Windows: Documentos\\mf-app\\db
    - En Linux:   ~/.local/share/mf-app/db

    Devuelve un objeto Path apuntando a la carpeta 'db'.
    """
    sistema = sys.platform

    if sistema.startswith("win"):
        # En Windows, usamos la carpeta de Documentos del usuario,
        # que es visible y accesible sin restricciones raras
        carpeta_app = Path.home() / "Documents" / "mf-app"
    else:
        carpeta_app = Path.home() / ".local" / "share" / "mf-app"

    carpeta_db = carpeta_app / "db"
    carpeta_db.mkdir(parents=True, exist_ok=True)

    return carpeta_db


def obtener_ruta_db():
    """
    Devuelve la ruta completa (carpeta + nombre de archivo)
    al archivo de base de datos SQLite.
    """
    carpeta_db = obtener_carpeta_app()
    return carpeta_db / "mf-app.db"


def obtener_carpeta_imgs():
    """
    Devuelve la carpeta donde se guardan las imágenes de los productos,
    dentro de la carpeta 'db' (mf-app/db/imgs), creándola si no existe.
    """
    carpeta_db = obtener_carpeta_app()
    carpeta_imgs = carpeta_db / "imgs"
    carpeta_imgs.mkdir(parents=True, exist_ok=True)
    return carpeta_imgs


# ---------- Backups ----------

def _obtener_carpeta_backups():
    """Devuelve mf-app/backups, creándola si no existe."""
    carpeta_backups = obtener_carpeta_app().parent / "backups"
    carpeta_backups.mkdir(parents=True, exist_ok=True)
    return carpeta_backups


def _contar_productos(ruta_db):
    """Cantidad de filas en la tabla stock (0 si la tabla no existe o falla)."""
    try:
        conexion = sqlite3.connect(str(ruta_db), timeout=10)
        try:
            return conexion.execute("SELECT COUNT(*) FROM stock").fetchone()[0]
        finally:
            conexion.close()
    except sqlite3.Error:
        return 0


def hacer_backup_db():
    """
    Crea un backup NUEVO y comprimido (.db.gz) de la base, con fecha y hora
    en el nombre, y después limpia los viejos.

    - Si la base no tiene productos NO se hace backup: así una base vacía
      nunca va pisando a los backups buenos.
    - La copia se hace con la API de backup de SQLite, que da una copia
      consistente aunque haya cambios recientes en el archivo -wal.
    - Si el backup falla, se registra en el log pero no se corta la
      operación que lo pidió (crear, editar o eliminar un producto).
    """
    ruta_db = obtener_ruta_db()

    if not ruta_db.exists():
        return  # no hay nada que respaldar todavía

    try:
        if _contar_productos(ruta_db) == 0:
            _log().warning("No se hizo backup: la base no tiene productos.")
            return

        carpeta_backups = _obtener_carpeta_backups()
        momento = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ruta_backup = carpeta_backups / f"mf-app_{momento}.db.gz"
        copia_temporal = carpeta_backups / f"_temporal_{momento}.db"
        ruta_parcial = carpeta_backups / f"mf-app_{momento}.db.gz.partial"

        try:
            # 1) copia consistente de la base a un archivo temporal
            origen = sqlite3.connect(str(ruta_db), timeout=10)
            try:
                destino = sqlite3.connect(str(copia_temporal))
                try:
                    origen.backup(destino)
                finally:
                    destino.close()
            finally:
                origen.close()

            # 2) se comprime a un .partial y recién al final se renombra,
            # así nunca queda un backup a medio escribir con nombre válido
            with open(copia_temporal, "rb") as archivo_original:
                with gzip.open(ruta_parcial, "wb") as archivo_comprimido:
                    shutil.copyfileobj(archivo_original, archivo_comprimido)
            os.replace(ruta_parcial, ruta_backup)
        finally:
            copia_temporal.unlink(missing_ok=True)
            ruta_parcial.unlink(missing_ok=True)

        limpiar_backups_viejos()

    except Exception as e:
        _log().error(f"No se pudo hacer el backup de la base: {e}")


def limpiar_backups_viejos(cantidad_recientes=BACKUPS_RECIENTES, dias_diarios=DIAS_BACKUP_DIARIO):
    """
    Borra backups viejos, pero conserva:
    - los 'cantidad_recientes' más nuevos, y
    - el último backup de cada día de los últimos 'dias_diarios' días.
    Así, aunque un día se hagan muchísimos backups, los de días anteriores
    no se pierden.
    """
    carpeta_backups = _obtener_carpeta_backups()

    backups = sorted(
        carpeta_backups.glob("mf-app_*.db.gz"),
        key=lambda archivo: archivo.stat().st_mtime,
        reverse=True  # del más nuevo al más viejo
    )

    conservar = set(backups[:cantidad_recientes])

    limite = time.time() - dias_diarios * 86400
    dias_vistos = set()
    for archivo in backups:
        modificado = archivo.stat().st_mtime
        if modificado < limite:
            continue
        dia = datetime.fromtimestamp(modificado).date()
        if dia not in dias_vistos:
            dias_vistos.add(dia)
            conservar.add(archivo)

    for archivo in backups:
        if archivo not in conservar:
            try:
                archivo.unlink()
            except OSError as e:
                _log().warning(f"No se pudo borrar el backup viejo '{archivo.name}': {e}")


def restaurar_backup(ruta_backup):
    """
    Restaura la base desde un backup .db.gz. Usar con la app CERRADA.

    Antes de pisar nada, guarda una copia de la base actual junto a ella
    (mf-app_antes_de_restaurar_<fecha>.db). Los archivos -wal y -shm se
    borran para que SQLite no mezcle datos viejos con la base restaurada.
    """
    ruta_backup = Path(ruta_backup)
    ruta_db = obtener_ruta_db()

    if ruta_db.exists():
        momento = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        shutil.copy2(ruta_db, ruta_db.with_name(f"mf-app_antes_de_restaurar_{momento}.db"))

    for sufijo in ("-wal", "-shm"):
        auxiliar = Path(str(ruta_db) + sufijo)
        if auxiliar.exists():
            auxiliar.unlink()

    with gzip.open(ruta_backup, "rb") as archivo_comprimido:
        with open(ruta_db, "wb") as destino:
            shutil.copyfileobj(archivo_comprimido, destino)

    _log().info(f"Base restaurada desde '{ruta_backup.name}'.")
