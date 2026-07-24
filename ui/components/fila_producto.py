import os
import customtkinter as ctk
from PIL import Image

from functions.paths import obtener_carpeta_imgs

COLOR_FILA = "#242424"
COLOR_TEXTO = "#ffffff"
COLOR_TEXTO_SECUNDARIO = "#9a9a9a"
COLOR_BURBUJA = "#3a3a3a"
COLOR_PRECIO = "#3b8ed0"
COLOR_BOTON_ACTIVO = "#3b8ed0"
COLOR_HOVER = "#5aa5dd"
COLOR_ROJO = "#e74c3c"
COLOR_ROJO_HOVER = "#c0392b"
COLOR_GRIS = "#3a3a3a"
COLOR_GRIS_HOVER = "#4a4a4a"

RUTA_ICONS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons"
)

TAMANO_IMAGEN = 44
TAMANO_BOTON = 30

_CACHE_IMAGENES = {}
_CACHE_ICONOS = {}


def _cargar_icono(nombre_archivo):
    if nombre_archivo in _CACHE_ICONOS:
        return _CACHE_ICONOS[nombre_archivo]

    ruta = os.path.join(RUTA_ICONS, nombre_archivo)
    icono = None
    if os.path.exists(ruta):
        imagen = Image.open(ruta)
        icono = ctk.CTkImage(light_image=imagen, dark_image=imagen, size=(16, 16))

    _CACHE_ICONOS[nombre_archivo] = icono
    return icono


def _cargar_imagen_producto(nombre_imagen):
    nombre_imagen = nombre_imagen or "default.png"

    if nombre_imagen in _CACHE_IMAGENES:
        return _CACHE_IMAGENES[nombre_imagen]

    carpeta_imgs = obtener_carpeta_imgs()
    ruta_imagen = carpeta_imgs / nombre_imagen

    if ruta_imagen.exists():
        imagen = Image.open(ruta_imagen)
    else:
        imagen = Image.new("RGB", (TAMANO_IMAGEN, TAMANO_IMAGEN), COLOR_BURBUJA)

    imagen_ctk = ctk.CTkImage(
        light_image=imagen, dark_image=imagen, size=(TAMANO_IMAGEN, TAMANO_IMAGEN)
    )
    _CACHE_IMAGENES[nombre_imagen] = imagen_ctk
    return imagen_ctk


class FilaProducto(ctk.CTkFrame):
    """
    Fila de producto RECICLABLE: se crea una sola vez y se reutiliza
    llamando a actualizar(producto) en vez de destruirla y crear una nueva.
    corner_radius=0 en toda la fila para renderizar más rápido.
    """

    def __init__(self, master, on_eliminar=None, on_editar=None, on_agregar_factura=None):
        super().__init__(master, fg_color=COLOR_FILA, corner_radius=0, height=64)
        self.pack_propagate(False)

        self.producto = None
        self.on_eliminar = on_eliminar
        self.on_editar = on_editar
        self.on_agregar_factura = on_agregar_factura

        self._crear_widgets()

    def _crear_widgets(self):
        self.label_imagen = ctk.CTkLabel(self, text="")
        self.label_imagen.pack(side="left", padx=(10, 10), pady=8)

        columna_info = ctk.CTkFrame(self, fg_color="transparent")
        columna_info.pack(side="left", fill="both", expand=True, pady=8)

        self.label_nombre = ctk.CTkLabel(
            columna_info, text="",
            font=("Arial", 14, "bold"), text_color=COLOR_TEXTO, anchor="w"
        )
        self.label_nombre.pack(anchor="w", fill="x")

        self.label_codigo = ctk.CTkLabel(
            columna_info, text="",
            font=("Arial", 11), text_color=COLOR_TEXTO_SECUNDARIO, anchor="w"
        )
        self.label_codigo.pack(anchor="w", fill="x")

        columna_burbujas = ctk.CTkFrame(self, fg_color="transparent")
        columna_burbujas.pack(side="left", padx=10, pady=8)

        self.label_caja = ctk.CTkLabel(
            columna_burbujas, text="",
            font=("Arial", 11, "bold"), text_color=COLOR_TEXTO,
            fg_color=COLOR_BURBUJA, corner_radius=0, padx=8, pady=3
        )
        self.label_caja.pack(side="left", padx=(0, 6))

        self.label_stock = ctk.CTkLabel(
            columna_burbujas, text="",
            font=("Arial", 11, "bold"), text_color=COLOR_TEXTO,
            fg_color=COLOR_BURBUJA, corner_radius=0, padx=8, pady=3
        )
        self.label_stock.pack(side="left")

        self.label_precio = ctk.CTkLabel(
            self, text="",
            font=("Arial", 14, "bold"), text_color=COLOR_PRECIO, width=80
        )
        self.label_precio.pack(side="left", padx=10)

        columna_botones = ctk.CTkFrame(self, fg_color="transparent")
        columna_botones.pack(side="right", padx=10, pady=8)

        icono_eliminar = _cargar_icono("eliminar.png")
        ctk.CTkButton(
            columna_botones, text="" if icono_eliminar else "X", image=icono_eliminar,
            width=TAMANO_BOTON, height=TAMANO_BOTON,
            fg_color=COLOR_ROJO, hover_color=COLOR_ROJO_HOVER, corner_radius=0,
            command=lambda: self.on_eliminar(self.producto) if self.on_eliminar and self.producto else None
        ).pack(side="left", padx=(0, 6))

        icono_editar = _cargar_icono("editar.png")
        ctk.CTkButton(
            columna_botones, text="" if icono_editar else "E", image=icono_editar,
            width=TAMANO_BOTON, height=TAMANO_BOTON,
            fg_color=COLOR_GRIS, hover_color=COLOR_GRIS_HOVER, corner_radius=0,
            command=lambda: self.on_editar(self.producto) if self.on_editar and self.producto else None
        ).pack(side="left", padx=(0, 6))

        icono_factura = _cargar_icono("factura.png")
        ctk.CTkButton(
            columna_botones, text="" if icono_factura else "+", image=icono_factura,
            width=TAMANO_BOTON, height=TAMANO_BOTON,
            fg_color=COLOR_BOTON_ACTIVO, hover_color=COLOR_HOVER, corner_radius=0,
            command=lambda: self.on_agregar_factura(self.producto) if self.on_agregar_factura and self.producto else None
        ).pack(side="left")

    def actualizar(self, producto):
        """
        Actualiza el contenido de esta fila ya existente con los datos
        de un nuevo producto, sin destruir ni recrear ningún widget.
        Mucho más rápido que crear una FilaProducto nueva.
        """
        self.producto = producto

        self.label_imagen.configure(image=_cargar_imagen_producto(producto.get("imagen")))
        self.label_nombre.configure(text=producto.get("descripcion", ""))
        self.label_codigo.configure(text=producto.get("codigo", ""))
        self.label_caja.configure(text=f"Caja: {producto.get('cantidad_caja', 0)}")
        self.label_stock.configure(text=f"Stock: {producto.get('cantidad_stock', 0)}")
        self.label_precio.configure(text=f"${producto.get('precio', 0):,.2f}")