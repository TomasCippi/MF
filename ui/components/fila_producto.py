"""
ui/components/fila_producto.py

Widget que representa una fila individual de producto dentro de la
lista de Stock. Muestra imagen, nombre, código, cantidades, precio
y los botones de acción (eliminar, editar, añadir a factura).

Pensado para adaptarse a pantallas chicas (laptop): usa tamaños
compactos y permite que el nombre/código se corten con "..." si no
entran, en vez de romper el layout.
"""

import os
import customtkinter as ctk
from PIL import Image

from functions.paths import obtener_carpeta_imgs

# ---------- Colores ----------
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

TAMANO_IMAGEN = 44   # antes 60, ahora más compacta
TAMANO_BOTON = 30    # antes 36


class FilaProducto(ctk.CTkFrame):
    """
    Representa una fila con la información de un producto.

    producto: diccionario con las claves codigo, descripcion, precio,
              cantidad_caja, cantidad_stock, imagen (viene de obtener_productos()).
    on_eliminar / on_editar / on_agregar_factura: callbacks que reciben
              el diccionario 'producto' completo.
    """

    def __init__(self, master, producto, on_eliminar=None, on_editar=None, on_agregar_factura=None):
        super().__init__(master, fg_color=COLOR_FILA, corner_radius=10, height=64)
        self.pack_propagate(False)  # mantiene la altura fija aunque el contenido varíe

        self.producto = producto
        self.on_eliminar = on_eliminar
        self.on_editar = on_editar
        self.on_agregar_factura = on_agregar_factura

        self._crear_widgets()

    def _crear_widgets(self):
        # ---------- Imagen del producto ----------
        imagen_ctk = self._cargar_imagen_producto()
        label_imagen = ctk.CTkLabel(self, image=imagen_ctk, text="")
        label_imagen.pack(side="left", padx=(10, 10), pady=8)

        # ---------- Nombre + código (se expande y se corta si no entra) ----------
        columna_info = ctk.CTkFrame(self, fg_color="transparent")
        columna_info.pack(side="left", fill="both", expand=True, pady=8)

        nombre = self.producto.get("descripcion", "")
        ctk.CTkLabel(
            columna_info,
            text=nombre,
            font=("Arial", 14, "bold"),
            text_color=COLOR_TEXTO,
            anchor="w"
        ).pack(anchor="w", fill="x")

        ctk.CTkLabel(
            columna_info,
            text=self.producto.get("codigo", ""),
            font=("Arial", 11),
            text_color=COLOR_TEXTO_SECUNDARIO,
            anchor="w"
        ).pack(anchor="w", fill="x")

        # ---------- Burbujas: cantidad por caja / cantidad en stock ----------
        columna_burbujas = ctk.CTkFrame(self, fg_color="transparent")
        columna_burbujas.pack(side="left", padx=10, pady=8)

        ctk.CTkLabel(
            columna_burbujas,
            text=f"Caja: {self.producto.get('cantidad_caja', 0)}",
            font=("Arial", 11, "bold"),
            text_color=COLOR_TEXTO,
            fg_color=COLOR_BURBUJA,
            corner_radius=8,
            padx=8, pady=3
        ).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            columna_burbujas,
            text=f"Stock: {self.producto.get('cantidad_stock', 0)}",
            font=("Arial", 11, "bold"),
            text_color=COLOR_TEXTO,
            fg_color=COLOR_BURBUJA,
            corner_radius=8,
            padx=8, pady=3
        ).pack(side="left")

        # ---------- Precio ----------
        precio = self.producto.get("precio", 0)
        ctk.CTkLabel(
            self,
            text=f"${precio:,.2f}",
            font=("Arial", 14, "bold"),
            text_color=COLOR_PRECIO,
            width=80
        ).pack(side="left", padx=10)

        # ---------- Botones de acción (a la derecha) ----------
        columna_botones = ctk.CTkFrame(self, fg_color="transparent")
        columna_botones.pack(side="right", padx=10, pady=8)

        # Botón eliminar (ícono rojo)
        icono_eliminar = self._cargar_icono("eliminar.png")
        ctk.CTkButton(
            columna_botones,
            text="" if icono_eliminar else "X",
            image=icono_eliminar,
            width=TAMANO_BOTON, height=TAMANO_BOTON,
            fg_color=COLOR_ROJO,
            hover_color=COLOR_ROJO_HOVER,
            corner_radius=8,
            command=lambda: self.on_eliminar(self.producto) if self.on_eliminar else None
        ).pack(side="left", padx=(0, 6))

        # Botón editar (ícono gris)
        icono_editar = self._cargar_icono("editar.png")
        ctk.CTkButton(
            columna_botones,
            text="" if icono_editar else "E",
            image=icono_editar,
            width=TAMANO_BOTON, height=TAMANO_BOTON,
            fg_color=COLOR_GRIS,
            hover_color=COLOR_GRIS_HOVER,
            corner_radius=8,
            command=lambda: self.on_editar(self.producto) if self.on_editar else None
        ).pack(side="left", padx=(0, 6))

        # Botón añadir a factura (celeste)
        icono_factura = self._cargar_icono("factura.png")
        ctk.CTkButton(
            columna_botones,
            text="" if icono_factura else "+",
            image=icono_factura,
            width=TAMANO_BOTON, height=TAMANO_BOTON,
            fg_color=COLOR_BOTON_ACTIVO,
            hover_color=COLOR_HOVER,
            corner_radius=8,
            command=lambda: self.on_agregar_factura(self.producto) if self.on_agregar_factura else None
        ).pack(side="left")

    def _cargar_icono(self, nombre_archivo):
        """Carga un ícono chico (16x16) desde assets/icons. Devuelve None si no existe."""
        ruta = os.path.join(RUTA_ICONS, nombre_archivo)
        if os.path.exists(ruta):
            imagen = Image.open(ruta)
            return ctk.CTkImage(light_image=imagen, dark_image=imagen, size=(16, 16))
        return None

    def _cargar_imagen_producto(self):
        """
        Carga la imagen del producto desde la carpeta de almacenamiento
        de la app (mf-app/db/imgs). Si no existe el archivo, muestra un
        cuadro gris vacío en su lugar (no rompe la fila).
        """
        nombre_imagen = self.producto.get("imagen") or "default.png"
        carpeta_imgs = obtener_carpeta_imgs()
        ruta_imagen = carpeta_imgs / nombre_imagen

        if ruta_imagen.exists():
            imagen = Image.open(ruta_imagen)
        else:
            imagen = Image.new("RGB", (TAMANO_IMAGEN, TAMANO_IMAGEN), COLOR_BURBUJA)

        return ctk.CTkImage(
            light_image=imagen, dark_image=imagen,
            size=(TAMANO_IMAGEN, TAMANO_IMAGEN)
        )