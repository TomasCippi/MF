import customtkinter as ctk
from PIL import Image
import os
import unicodedata
from tkinter import filedialog
from datetime import datetime

from functions.exportar_lista import exportar_stock_excel
from functions.db import obtener_productos
from ui.pages.agregar_producto import VentanaAgregarProducto
from ui.components.fila_producto import FilaProducto
from ui.pages.confirmar_eliminar import VentanaConfirmarEliminar
from ui.pages.subir_masivo import VentanaSubirMasivo
from ui.components.toast import mostrar_toast

COLOR_FONDO = "#1a1a1a"
COLOR_BURBUJA = "#3a3a3a"
COLOR_TEXTO = "#ffffff"
COLOR_TEXTO_SECUNDARIO = "#9a9a9a"
COLOR_INPUT = "#242424"
COLOR_BORDE = "#3a3a3a"
COLOR_BOTON_ACTIVO = "#3b8ed0"
COLOR_HOVER = "#5aa5dd"

RUTA_ICONS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons")

PRODUCTOS_POR_PAGINA = 10
RETRASO_BUSQUEDA_MS = 0


class PaginaStock(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLOR_FONDO)

        self.todos_los_productos = []
        self.productos_filtrados = []
        self.pagina_actual = 1
        self._id_after_busqueda = None

        # Pool de filas reutilizables: se crean UNA sola vez (tamaño fijo
        # = PRODUCTOS_POR_PAGINA) y se van reciclando con .actualizar(...)
        self._pool_filas = []

        self._crear_encabezado()
        self._crear_buscador()
        self._crear_lista_productos()
        self._crear_paginacion()
        self._crear_botones_inferiores()
        self._crear_pool_filas()

        self.after(10, self._cargar_productos)

    def al_mostrar(self):
        self.after(10, self._cargar_productos)

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _crear_encabezado(self):
        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.pack(anchor="w", padx=30, pady=(30, 15), fill="x")

        ctk.CTkLabel(
            encabezado, text="Stock",
            font=("Arial", 24, "bold"), text_color=COLOR_TEXTO
        ).pack(side="left")

        self.burbuja = ctk.CTkLabel(
            encabezado, text="0",
            font=("Arial", 14, "bold"), text_color=COLOR_TEXTO,
            fg_color=COLOR_BURBUJA, corner_radius=12, width=70, height=24
        )
        self.burbuja.pack(side="left", padx=(12, 0))

    def _crear_buscador(self):
        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(fill="x", padx=30, pady=(0, 20))

        contenedor_input = ctk.CTkFrame(
            fila, fg_color=COLOR_INPUT, corner_radius=8,
            border_width=1, border_color=COLOR_BORDE
        )
        contenedor_input.pack(side="left", fill="x", expand=True, padx=(0, 15))

        icono_lupa = self._cargar_icono("buscar.png")
        if icono_lupa:
            ctk.CTkLabel(contenedor_input, image=icono_lupa, text="").pack(
                side="left", padx=(12, 5), pady=8
            )

        self.entry_busqueda = ctk.CTkEntry(
            contenedor_input,
            placeholder_text="Buscar por código o descripción...",
            fg_color="transparent", border_width=0,
            text_color=COLOR_TEXTO, font=("Arial", 13)
        )
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=8)
        self.entry_busqueda.bind("<KeyRelease>", self._on_tecla_busqueda)

        ctk.CTkButton(
            fila, text="+  Añadir producto",
            fg_color=COLOR_BOTON_ACTIVO, hover_color=COLOR_HOVER,
            text_color=COLOR_TEXTO, corner_radius=8,
            font=("Arial", 13, "bold"), width=170, height=36,
            command=self._abrir_agregar_producto
        ).pack(side="left")

    def _crear_lista_productos(self):
        ctk.CTkFrame(self, fg_color=COLOR_BORDE, height=1).pack(
            fill="x", padx=30, pady=(0, 15)
        )

        self.contenedor_productos = ctk.CTkScrollableFrame(
            self, fg_color=COLOR_FONDO, corner_radius=0
        )
        self.contenedor_productos.pack(fill="both", expand=True, padx=30, pady=(0, 15))

    def _crear_paginacion(self):
        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(fill="x", padx=30, pady=(0, 10))

        self.boton_anterior = ctk.CTkButton(
            fila, text="← Anterior",
            fg_color=COLOR_BURBUJA, hover_color="#4a4a4a",
            text_color=COLOR_TEXTO, corner_radius=8,
            width=110, height=32, command=self._pagina_anterior
        )
        self.boton_anterior.pack(side="left")

        self.label_pagina = ctk.CTkLabel(
            fila, text="Página 1 de 1",
            font=("Arial", 12), text_color=COLOR_TEXTO_SECUNDARIO
        )
        self.label_pagina.pack(side="left", expand=True)

        self.boton_siguiente = ctk.CTkButton(
            fila, text="Siguiente →",
            fg_color=COLOR_BURBUJA, hover_color="#4a4a4a",
            text_color=COLOR_TEXTO, corner_radius=8,
            width=110, height=32, command=self._pagina_siguiente
        )
        self.boton_siguiente.pack(side="right")

    def _crear_botones_inferiores(self):
        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(fill="x", padx=30, pady=(0, 20))

        ctk.CTkButton(
            fila, text="Subir masivamente",
            fg_color=COLOR_BURBUJA, hover_color="#4a4a4a",
            text_color=COLOR_TEXTO, corner_radius=8,
            font=("Arial", 13), width=170, height=36,
            command=self._abrir_subir_masivo
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            fila, text="Exportar lista",
            fg_color=COLOR_BURBUJA, hover_color="#4a4a4a",
            text_color=COLOR_TEXTO, corner_radius=8,
            font=("Arial", 13), width=140, height=36,
            command=self._exportar_lista
        ).pack(side="left")

    def _crear_pool_filas(self):
        for _ in range(PRODUCTOS_POR_PAGINA):
            fila = FilaProducto(
                self.contenedor_productos,
                on_eliminar=self._on_eliminar_producto,
                on_editar=self._on_editar_producto
            )
            self._pool_filas.append(fila)

        self.label_sin_resultados = ctk.CTkLabel(
            self.contenedor_productos, text="No se encontraron productos.",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        )

    def _cargar_icono(self, nombre_archivo):
        ruta = os.path.join(RUTA_ICONS, nombre_archivo)
        if os.path.exists(ruta):
            imagen = Image.open(ruta)
            return ctk.CTkImage(light_image=imagen, dark_image=imagen, size=(18, 18))
        return None

    # ------------------------------------------------------------------
    # Datos: carga, búsqueda (con debounce) y paginación
    # ------------------------------------------------------------------

    def _cargar_productos(self):
        try:
            self.todos_los_productos = obtener_productos()
        except Exception:
            self.todos_los_productos = []

        self.productos_filtrados = self.todos_los_productos
        self.pagina_actual = 1
        self._actualizar_vista()

    def _normalizar(self, texto):
        texto = texto.lower()
        texto = unicodedata.normalize("NFD", texto)
        return "".join(c for c in texto if unicodedata.category(c) != "Mn")

    def _on_tecla_busqueda(self, event=None):
        if self._id_after_busqueda is not None:
            self.after_cancel(self._id_after_busqueda)
        self._id_after_busqueda = self.after(RETRASO_BUSQUEDA_MS, self._ejecutar_busqueda)

    def _ejecutar_busqueda(self):
        texto = self._normalizar(self.entry_busqueda.get().strip())

        if texto == "":
            self.productos_filtrados = self.todos_los_productos
        else:
            self.productos_filtrados = [
                p for p in self.todos_los_productos
                if texto in self._normalizar(str(p.get("codigo", "")))
                or texto in self._normalizar(str(p.get("descripcion", "")))
            ]

        self.pagina_actual = 1
        self._actualizar_vista()

    def _actualizar_vista(self):
        total = len(self.productos_filtrados)

        inicio = (self.pagina_actual - 1) * PRODUCTOS_POR_PAGINA
        fin = inicio + PRODUCTOS_POR_PAGINA
        productos_pagina = self.productos_filtrados[inicio:fin]

        self.burbuja.configure(text=f"{len(productos_pagina)} de {total}")
        self._renderizar_productos(productos_pagina)
        self._actualizar_controles_paginacion(total)

    def _actualizar_controles_paginacion(self, total):
        total_paginas = max(1, (total + PRODUCTOS_POR_PAGINA - 1) // PRODUCTOS_POR_PAGINA)
        self.label_pagina.configure(text=f"Página {self.pagina_actual} de {total_paginas}")
        self.boton_anterior.configure(state="normal" if self.pagina_actual > 1 else "disabled")
        self.boton_siguiente.configure(state="normal" if self.pagina_actual < total_paginas else "disabled")

    def _pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self._actualizar_vista()

    def _pagina_siguiente(self):
        total_paginas = max(1, (len(self.productos_filtrados) + PRODUCTOS_POR_PAGINA - 1) // PRODUCTOS_POR_PAGINA)
        if self.pagina_actual < total_paginas:
            self.pagina_actual += 1
            self._actualizar_vista()

    def _renderizar_productos(self, productos):
        """
        En vez de destruir/crear widgets, reutiliza las filas del pool:
        - Las que corresponden a un producto, se actualizan y se muestran.
        - Las que sobran (última página incompleta), se ocultan con pack_forget.
        """
        if not productos:
            for fila in self._pool_filas:
                fila.pack_forget()
            self.label_sin_resultados.pack(pady=20)
            return

        self.label_sin_resultados.pack_forget()

        for i, fila in enumerate(self._pool_filas):
            if i < len(productos):
                fila.actualizar(productos[i])
                fila.pack(fill="x", pady=4)
            else:
                fila.pack_forget()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_eliminar_producto(self, producto):
        VentanaConfirmarEliminar(self, producto=producto, on_eliminado=self._cargar_productos)

    def _on_editar_producto(self, producto):
        VentanaAgregarProducto(self, producto=producto, on_guardado=self._cargar_productos)

    def _abrir_agregar_producto(self):
        VentanaAgregarProducto(self, producto=None, on_guardado=self._cargar_productos)

    def _abrir_subir_masivo(self):
        VentanaSubirMasivo(self, on_completado=self._cargar_productos)

    def _exportar_lista(self):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        nombre_sugerido = f"MF_precios_{fecha_hoy}.xlsx"

        ruta = filedialog.asksaveasfilename(
            title="Guardar listado de stock",
            defaultextension=".xlsx",
            filetypes=[("Archivo Excel", "*.xlsx")],
            initialfile=nombre_sugerido
        )

        if not ruta:
            return  # el usuario canceló el diálogo

        exito = exportar_stock_excel(ruta)

        if exito:
            mostrar_toast(self, "Lista exportada correctamente.", tipo="exito")
        else:
            mostrar_toast(self, "No se pudo exportar la lista.", tipo="error")