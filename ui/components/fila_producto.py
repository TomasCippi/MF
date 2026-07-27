import os
import customtkinter as ctk
from PIL import Image

from functions.paths import obtener_carpeta_imgs
from functions import carrito

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
    Fila de producto reciclable (pool). El botón de agregar al pedido
    arranca como un simple "+"; al tocarlo, se transforma en un stepper
    (− número +) para poder ajustar la cantidad sin volver a tocar "+".
    """

    def __init__(self, master, on_eliminar=None, on_editar=None):
        super().__init__(master, fg_color=COLOR_FILA, corner_radius=0, height=64)
        self.pack_propagate(False)

        self.producto = None
        self.on_eliminar = on_eliminar
        self.on_editar = on_editar

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

        # ---------- Zona del carrito: arranca como un solo botón "+" ----------
        self.contenedor_carrito = ctk.CTkFrame(columna_botones, fg_color="transparent")
        self.contenedor_carrito.pack(side="left")

        self.boton_mas_inicial = ctk.CTkButton(
            self.contenedor_carrito, text="+",
            width=TAMANO_BOTON, height=TAMANO_BOTON,
            fg_color=COLOR_BOTON_ACTIVO, hover_color=COLOR_HOVER, corner_radius=0,
            font=("Arial", 14, "bold"),
            command=self._agregar_al_pedido
        )

        self.boton_restar = ctk.CTkButton(
            self.contenedor_carrito, text="−",
            width=TAMANO_BOTON, height=TAMANO_BOTON,
            fg_color=COLOR_GRIS, hover_color=COLOR_GRIS_HOVER, corner_radius=0,
            font=("Arial", 14, "bold"),
            command=lambda: self._cambiar_cantidad(-1)
        )

        self.label_cantidad = ctk.CTkLabel(
            self.contenedor_carrito, text="0", width=28,
            font=("Arial", 13, "bold"), text_color=COLOR_TEXTO
        )

        self.boton_sumar = ctk.CTkButton(
            self.contenedor_carrito, text="+",
            width=TAMANO_BOTON, height=TAMANO_BOTON,
            fg_color=COLOR_BOTON_ACTIVO, hover_color=COLOR_HOVER, corner_radius=0,
            font=("Arial", 14, "bold"),
            command=lambda: self._cambiar_cantidad(1)
        )

    def _mostrar_stepper(self):
        """Oculta el botón '+' inicial y muestra − número +."""
        self.boton_mas_inicial.pack_forget()
        self.boton_restar.pack(side="left")
        self.label_cantidad.pack(side="left")
        self.boton_sumar.pack(side="left")

    def _mostrar_boton_inicial(self):
        """Oculta el stepper y vuelve a mostrar solo el botón '+'."""
        self.boton_restar.pack_forget()
        self.label_cantidad.pack_forget()
        self.boton_sumar.pack_forget()
        self.boton_mas_inicial.pack(side="left")

    def _agregar_al_pedido(self):
        """Primer toque en '+': agrega 1 al carrito y pasa a mostrar el stepper."""
        if not self.producto:
            return

        cantidad = carrito.agregar_producto(self.producto)
        self.label_cantidad.configure(text=str(cantidad))
        self._mostrar_stepper()

    def _cambiar_cantidad(self, delta):
        """Suma o resta desde el stepper. Si llega a 0, vuelve a mostrar solo '+'."""
        if not self.producto:
            return

        codigo = self.producto.get("codigo")
        cantidad = carrito.cambiar_cantidad(codigo, delta)
        self.label_cantidad.configure(text=str(cantidad))

        if cantidad == 0:
            self._mostrar_boton_inicial()

    def actualizar(self, producto):
        """
        Actualiza el contenido de esta fila reciclada con los datos de
        un nuevo producto, y sincroniza el estado del carrito (muestra
        el stepper si ya tiene cantidad > 0, o el botón '+' si no).
        """
        self.producto = producto

        self.label_imagen.configure(image=_cargar_imagen_producto(producto.get("imagen")))
        self.label_nombre.configure(text=producto.get("descripcion", ""))
        self.label_codigo.configure(text=producto.get("codigo", ""))
        self.label_caja.configure(text=f"Caja: {producto.get('cantidad_caja', 0)}")
        self.label_stock.configure(text=f"Stock: {producto.get('cantidad_stock', 0)}")
        self.label_precio.configure(text=f"${producto.get('precio', 0):,.2f}")

        cantidad_actual = carrito.obtener_cantidad(producto.get("codigo"))
        self.label_cantidad.configure(text=str(cantidad_actual))

        if cantidad_actual > 0:
            self._mostrar_stepper()
        else:
            self._mostrar_boton_inicial()