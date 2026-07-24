"""
ui/components/toast.py

Componente de notificaciones flotantes ("toast"). Es un frame que se
superpone DENTRO de la ventana principal usando .place(), así funciona
igual en Windows, X11 y Wayland (a diferencia de una ventana emergente
del sistema operativo, que en Wayland no se puede posicionar).

Uso desde cualquier página:

    from ui.components.toast import mostrar_toast

    mostrar_toast(self, "Producto guardado correctamente.", tipo="exito")
    mostrar_toast(self, "No se pudo eliminar el producto.", tipo="error")
    mostrar_toast(self, "Revisá los campos marcados.", tipo="advertencia")
"""

import os
import customtkinter as ctk
from PIL import Image

# Tiempo que se muestra el toast antes de desaparecer solo (en milisegundos).
DURACION_TOAST_MS = 5000

MARGEN_PX = 20
ESPACIO_ENTRE_TOASTS_PX = 10

COLOR_TEXTO = "#ffffff"

RUTA_ICONS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons"
)

_ESTILOS_TOAST = {
    "error": {"color": "#e74c3c", "icono": "stock.png"},
    "exito": {"color": "#2fa572", "icono": "stock.png"},
    "advertencia": {"color": "#e6a23c", "icono": "stock.png"},
}

# Cache de íconos ya cargados, para no releer el disco en cada toast.
_CACHE_ICONOS = {}

# Registro de toasts activos por ventana principal, para apilarlos
# uno arriba del otro si aparece más de uno al mismo tiempo.
_toasts_activos = {}


def mostrar_toast(widget_referencia, texto, tipo="exito", duracion_ms=None):
    """
    Muestra una notificación flotante abajo a la derecha de la ventana
    principal. Se cierra sola pasado 'duracion_ms' (o DURACION_TOAST_MS
    si no se especifica), o antes si el usuario la toca.
    """
    ventana_principal = widget_referencia.winfo_toplevel()
    estilo = _ESTILOS_TOAST.get(tipo, _ESTILOS_TOAST["exito"])
    duracion = duracion_ms if duracion_ms is not None else DURACION_TOAST_MS

    toast = _Toast(ventana_principal, texto, estilo, duracion)

    _toasts_activos.setdefault(ventana_principal, [])
    _toasts_activos[ventana_principal].append(toast)
    _reacomodar_toasts(ventana_principal)


def _cargar_icono_toast(nombre_archivo, tamano=28):
    """Carga (y cachea) el ícono del toast, ya escalado al tamaño deseado."""
    clave = (nombre_archivo, tamano)
    if clave in _CACHE_ICONOS:
        return _CACHE_ICONOS[clave]

    ruta = os.path.join(RUTA_ICONS, nombre_archivo)
    icono = None
    if os.path.exists(ruta):
        imagen = Image.open(ruta)
        icono = ctk.CTkImage(light_image=imagen, dark_image=imagen, size=(tamano, tamano))

    _CACHE_ICONOS[clave] = icono
    return icono


def _reacomodar_toasts(ventana_principal):
    """Reubica todos los toasts activos de esta ventana, apilados de abajo hacia arriba."""
    lista = _toasts_activos.get(ventana_principal, [])
    lista = [t for t in lista if t.winfo_exists()]
    _toasts_activos[ventana_principal] = lista

    y_acumulado = MARGEN_PX
    for toast in reversed(lista):  # el más nuevo queda abajo de todo
        toast.place(relx=1.0, rely=1.0, x=-MARGEN_PX, y=-y_acumulado, anchor="se")
        toast.update_idletasks()
        y_acumulado += toast.winfo_height() + ESPACIO_ENTRE_TOASTS_PX


class _Toast(ctk.CTkFrame):
    """
    Frame flotante: ícono grande a la izquierda (ocupa todo el alto),
    texto en blanco al lado. Posicionado con .place() sobre la ventana
    principal. Uso interno: se crea a través de mostrar_toast().
    """

    def __init__(self, ventana_principal, texto, estilo, duracion_ms):
        super().__init__(ventana_principal, fg_color=estilo["color"], corner_radius=10)

        self._ventana_principal = ventana_principal

        icono = _cargar_icono_toast(estilo["icono"], tamano=28)

        if icono:
            label_icono = ctk.CTkLabel(self, image=icono, text="")
            label_icono.pack(side="left", padx=(16, 10), pady=14)
            label_icono.bind("<Button-1>", lambda e: self._cerrar())

        label_texto = ctk.CTkLabel(
            self, text=texto,
            font=("Arial", 13, "bold"), text_color=COLOR_TEXTO,
            wraplength=260, justify="left", anchor="w"
        )
        label_texto.pack(side="left", padx=(0, 16), pady=14, fill="y")
        label_texto.bind("<Button-1>", lambda e: self._cerrar())

        self.bind("<Button-1>", lambda e: self._cerrar())
        self.lift()

        self.after(duracion_ms, self._cerrar)

    def _cerrar(self):
        try:
            self.destroy()
        except Exception:
            pass
        _reacomodar_toasts(self._ventana_principal)