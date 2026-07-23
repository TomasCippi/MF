import customtkinter as ctk
from PIL import Image
import os
import unicodedata

from functions.db import obtener_productos
from ui.pages.agregar_producto import VentanaAgregarProducto
from ui.components.fila_producto import FilaProducto
from ui.pages.confirmar_eliminar import VentanaConfirmarEliminar

COLOR_FONDO = "#1a1a1a"
COLOR_BURBUJA = "#3a3a3a"
COLOR_TEXTO = "#ffffff"
COLOR_TEXTO_SECUNDARIO = "#9a9a9a"
COLOR_INPUT = "#242424"
COLOR_BORDE = "#3a3a3a"
COLOR_BOTON_ACTIVO = "#3b8ed0"
COLOR_HOVER = "#5aa5dd"

RUTA_ICONS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons")


class PaginaStock(ctk.CTkFrame):
    """
    Página de Stock. Muestra el título, la cantidad de productos,
    un buscador y el botón para añadir productos.
    """

    def __init__(self, master):
        super().__init__(master, fg_color=COLOR_FONDO)

        self.todos_los_productos = []  # cache en memoria para filtrar sin golpear la db en cada tecla

        # ---------- Encabezado: título + burbuja ----------
        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.pack(anchor="w", padx=30, pady=(30, 15), fill="x")

        titulo = ctk.CTkLabel(
            encabezado,
            text="Stock",
            font=("Arial", 24, "bold"),
            text_color=COLOR_TEXTO
        )
        titulo.pack(side="left")

        self.burbuja = ctk.CTkLabel(
            encabezado,
            text="0",
            font=("Arial", 14, "bold"),
            text_color=COLOR_TEXTO,
            fg_color=COLOR_BURBUJA,
            corner_radius=12,
            width=32,
            height=24
        )
        self.burbuja.pack(side="left", padx=(12, 0))

        # ---------- Fila: buscador + botón añadir ----------
        fila_busqueda = ctk.CTkFrame(self, fg_color="transparent")
        fila_busqueda.pack(fill="x", padx=30, pady=(0, 20))

        # El input se expande, el botón queda con tamaño fijo al costado
        contenedor_input = ctk.CTkFrame(
            fila_busqueda,
            fg_color=COLOR_INPUT,
            corner_radius=8,
            border_width=1,
            border_color=COLOR_BORDE
        )
        contenedor_input.pack(side="left", fill="x", expand=True, padx=(0, 15))

        icono_lupa = self._cargar_icono("buscar.png")
        if icono_lupa:
            label_lupa = ctk.CTkLabel(contenedor_input, image=icono_lupa, text="")
            label_lupa.pack(side="left", padx=(12, 5), pady=8)

        self.entry_busqueda = ctk.CTkEntry(
            contenedor_input,
            placeholder_text="Buscar por código o descripción...",
            fg_color="transparent",
            border_width=0,
            text_color=COLOR_TEXTO,
            font=("Arial", 13)
        )
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=8)
        self.entry_busqueda.bind("<KeyRelease>", self._on_buscar)

        boton_agregar = ctk.CTkButton(
            fila_busqueda,
            text="+  Añadir producto",
            fg_color=COLOR_BOTON_ACTIVO,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXTO,
            corner_radius=8,
            font=("Arial", 13, "bold"),
            width=170,
            height=36,
            command=self._abrir_agregar_producto
        )
        boton_agregar.pack(side="left")
        
        # ---------- Línea divisoria ----------
        divisor = ctk.CTkFrame(self, fg_color=COLOR_BORDE, height=1)
        divisor.pack(fill="x", padx=30, pady=(0, 15))

        # ---------- Contenedor con scroll para la lista de productos ----------
        # Por ahora queda vacío, acá se van a mostrar los productos más adelante.
        self.contenedor_productos = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_FONDO,
            corner_radius=0
        )
        self.contenedor_productos.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        # ---------- Fila inferior: botones de carga masiva / exportar ----------
        fila_botones_inferior = ctk.CTkFrame(self, fg_color="transparent")
        fila_botones_inferior.pack(fill="x", padx=30, pady=(0, 20))

        boton_subir_masivo = ctk.CTkButton(
            fila_botones_inferior,
            text="Subir masivamente",
            fg_color=COLOR_BURBUJA,
            hover_color="#4a4a4a",
            text_color=COLOR_TEXTO,
            corner_radius=8,
            font=("Arial", 13),
            width=170,
            height=36,
            command=lambda: print("Subir masivamente (pendiente de implementar).")
        )
        boton_subir_masivo.pack(side="left", padx=(0, 10))

        boton_exportar = ctk.CTkButton(
            fila_botones_inferior,
            text="Exportar lista",
            fg_color=COLOR_BURBUJA,
            hover_color="#4a4a4a",
            text_color=COLOR_TEXTO,
            corner_radius=8,
            font=("Arial", 13),
            width=140,
            height=36,
            command=lambda: print("Exportar lista (pendiente de implementar).")
        )
        boton_exportar.pack(side="left")
        # ---------- Carga inicial ----------
        self._cargar_productos()

    def _cargar_icono(self, nombre_archivo):
        """Carga un ícono desde assets/icons, devuelve None si no existe."""
        ruta = os.path.join(RUTA_ICONS, nombre_archivo)
        if os.path.exists(ruta):
            imagen = Image.open(ruta)
            return ctk.CTkImage(light_image=imagen, dark_image=imagen, size=(18, 18))
        return None

    def _cargar_productos(self):
        """
        Trae todos los productos de la base de datos, los guarda en cache,
        actualiza la burbuja con la cantidad total, y renderiza la lista.
        """
        try:
            self.todos_los_productos = obtener_productos()
        except Exception:
            self.todos_los_productos = []

        self.burbuja.configure(text=str(len(self.todos_los_productos)))
        self._renderizar_productos(self.todos_los_productos)

    def _renderizar_productos(self, productos):
        """
        Limpia el contenedor con scroll y dibuja una FilaProducto
        por cada producto de la lista recibida.
        """
        # Borra todo lo que había dibujado antes
        for widget in self.contenedor_productos.winfo_children():
            widget.destroy()

        if not productos:
            ctk.CTkLabel(
                self.contenedor_productos,
                text="No se encontraron productos.",
                font=("Arial", 13),
                text_color=COLOR_TEXTO_SECUNDARIO
            ).pack(pady=20)
            return

        for producto in productos:
            fila = FilaProducto(
                self.contenedor_productos,
                producto=producto,
                on_eliminar=self._on_eliminar_producto,
                on_editar=self._on_editar_producto,
                on_agregar_factura=self._on_agregar_factura
            )
            fila.pack(fill="x", pady=4)

    def _normalizar(self, texto):
        texto = texto.lower()
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
        return texto

    def _on_buscar(self, event=None):
        texto = self._normalizar(self.entry_busqueda.get().strip())

        if texto == "":
            resultados = self.todos_los_productos
        else:
            resultados = [
                p for p in self.todos_los_productos
                if texto in self._normalizar(str(p.get("codigo", "")))
                or texto in self._normalizar(str(p.get("descripcion", "")))
            ]

        self.burbuja.configure(text=str(len(resultados)))
        self._renderizar_productos(resultados)

    # ---------- Callbacks de los botones de cada fila (por ahora, placeholders) ----------

    def _on_eliminar_producto(self, producto):
        VentanaConfirmarEliminar(self, producto=producto, on_eliminado=self._cargar_productos)

    def _on_editar_producto(self, producto):
        print(f"Editar producto: {producto.get('codigo')} (pendiente de implementar).")

    def _on_agregar_factura(self, producto):
        print(f"Añadir a factura: {producto.get('codigo')} (pendiente de implementar).")

    def _abrir_agregar_producto(self):
        """
        Abre la ventana emergente para añadir un producto nuevo.
        Al confirmar, refresca la cantidad de productos en la burbuja.
        """
        VentanaAgregarProducto(self, on_producto_agregado=self._cargar_productos)