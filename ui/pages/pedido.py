import customtkinter as ctk
from PIL import Image
from tkinter import filedialog, messagebox
import os

from functions.facturar import generar_factura_excel
from functions.config import obtener_proximo_remito, establecer_proximo_remito
from functions.db import obtener_producto, editar_producto
from ui.components.toast import mostrar_toast
from functions.paths import obtener_carpeta_imgs, hacer_backup_db
from functions import carrito

COLOR_FONDO = "#1a1a1a"
COLOR_FILA = "#242424"
COLOR_TEXTO = "#ffffff"
COLOR_TEXTO_SECUNDARIO = "#9a9a9a"
COLOR_INPUT = "#242424"
COLOR_BORDE = "#3a3a3a"
COLOR_PRECIO = "#3b8ed0"
COLOR_BOTON_ACTIVO = "#3b8ed0"
COLOR_HOVER = "#5aa5dd"
COLOR_GRIS = "#3a3a3a"
COLOR_GRIS_HOVER = "#4a4a4a"
COLOR_ROJO = "#e74c3c"
COLOR_ROJO_HOVER = "#c0392b"

TAMANO_IMAGEN_ITEM = 40

_CACHE_IMAGENES = {}


def _cargar_imagen_item(nombre_imagen):
    """Carga (y cachea) la imagen de un producto, o un cuadrado gris si no tiene."""
    nombre_imagen = nombre_imagen or "default.png"

    if nombre_imagen in _CACHE_IMAGENES:
        return _CACHE_IMAGENES[nombre_imagen]

    carpeta_imgs = obtener_carpeta_imgs()
    ruta_imagen = carpeta_imgs / nombre_imagen

    if nombre_imagen != "default.png" and ruta_imagen.exists():
        imagen = Image.open(ruta_imagen)
    else:
        imagen = Image.new("RGB", (TAMANO_IMAGEN_ITEM, TAMANO_IMAGEN_ITEM), COLOR_GRIS)

    imagen_ctk = ctk.CTkImage(
        light_image=imagen, dark_image=imagen, size=(TAMANO_IMAGEN_ITEM, TAMANO_IMAGEN_ITEM)
    )
    _CACHE_IMAGENES[nombre_imagen] = imagen_ctk
    return imagen_ctk


class PaginaPedido(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLOR_FONDO)

        # Envuelve TODA la página en scroll, por si el contenido no entra
        # verticalmente en pantallas más chicas de alto.
        self.contenedor_scroll = ctk.CTkScrollableFrame(
            self, fg_color=COLOR_FONDO, corner_radius=0
        )
        self.contenedor_scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.contenedor_scroll, text="Pedido",
            font=("Arial", 24, "bold"), text_color=COLOR_TEXTO
        ).pack(anchor="w", padx=30, pady=(30, 20))

        # ---------- Fila principal: 50% formulario / 50% lista de productos ----------
        fila_principal = ctk.CTkFrame(self.contenedor_scroll, fg_color="transparent")
        fila_principal.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        # Grid con dos columnas de igual peso, así se reparten 50/50
        # sin importar el ancho real de la ventana.
        fila_principal.grid_columnconfigure(0, weight=1, uniform="mitad")
        fila_principal.grid_columnconfigure(1, weight=1, uniform="mitad")

        columna_formulario = ctk.CTkFrame(fila_principal, fg_color="transparent")
        columna_formulario.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        columna_lista = ctk.CTkFrame(fila_principal, fg_color="transparent")
        columna_lista.grid(row=0, column=1, sticky="nsew", padx=(15, 0))

        self._crear_formulario(columna_formulario)
        self._crear_lista_carrito(columna_lista)

        self._crear_totales()
        self._crear_boton_generar()

        self._actualizar_lista()

    def al_mostrar(self):
        """Se llama cada vez que esta página se vuelve visible."""
        self._actualizar_lista()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _crear_formulario(self, contenedor):
        validar_entero = self.register(self._validar_numero_entero)
        validar_decimal = self.register(self._validar_numero_decimal)

        # ---------- Cliente ----------
        ctk.CTkLabel(
            contenedor, text="Cliente",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w")

        self.entry_cliente = ctk.CTkEntry(
            contenedor, placeholder_text="Nombre del cliente",
            fg_color=COLOR_INPUT, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO, height=38, corner_radius=0
        )
        self.entry_cliente.pack(fill="x", pady=(5, 15))

        # ---------- Remito ----------
        ctk.CTkLabel(
            contenedor, text="Número de remito",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w")

        self.entry_remito = ctk.CTkEntry(
            contenedor, placeholder_text="Ej: 0001",
            fg_color=COLOR_INPUT, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO, height=38, corner_radius=0,
            validate="key", validatecommand=(validar_entero, "%P")
        )
        self.entry_remito.pack(fill="x", pady=(5, 15))
        self.entry_remito.insert(0, str(obtener_proximo_remito()))

        # ---------- Descuento ----------
        ctk.CTkLabel(
            contenedor, text="Descuento (%)",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w")

        self.entry_descuento = ctk.CTkEntry(
            contenedor, placeholder_text="0",
            fg_color=COLOR_INPUT, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO, height=38, corner_radius=0,
            validate="key", validatecommand=(validar_decimal, "%P")
        )
        self.entry_descuento.pack(fill="x", pady=(5, 15))
        self.entry_descuento.bind("<KeyRelease>", lambda e: self._actualizar_totales())

        # ---------- Deuda ----------
        ctk.CTkLabel(
            contenedor, text="Deuda",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w")

        self.entry_deuda = ctk.CTkEntry(
            contenedor, placeholder_text="0",
            fg_color=COLOR_INPUT, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO, height=38, corner_radius=0,
            validate="key", validatecommand=(validar_entero, "%P")
        )
        self.entry_deuda.pack(fill="x", pady=(5, 0))
        self.entry_deuda.bind("<KeyRelease>", lambda e: self._actualizar_totales())

    def _crear_lista_carrito(self, contenedor):
        ctk.CTkLabel(
            contenedor, text="Productos del pedido",
            font=("Arial", 15, "bold"), text_color=COLOR_TEXTO
        ).pack(anchor="w", pady=(0, 10))

        self.contenedor_lista = ctk.CTkScrollableFrame(
            contenedor, fg_color=COLOR_FONDO, corner_radius=0, height=320
        )
        self.contenedor_lista.pack(fill="both", expand=True)

    def _crear_totales(self):
        self.contenedor_totales = ctk.CTkFrame(
            self.contenedor_scroll, fg_color=COLOR_FILA, corner_radius=0
        )
        self.contenedor_totales.pack(fill="x", padx=30, pady=(0, 15))
        # El contenido de adentro se arma dinámicamente en _actualizar_totales(),
        # ya que qué filas se muestran depende de si hay descuento/deuda o no.

    def _crear_boton_generar(self):
        ctk.CTkButton(
            self.contenedor_scroll, text="Generar factura",
            fg_color=COLOR_BOTON_ACTIVO, hover_color=COLOR_HOVER,
            text_color=COLOR_TEXTO, corner_radius=0,
            font=("Arial", 16, "bold"), height=50,
            command=self._generar_factura
        ).pack(fill="x", padx=30, pady=(0, 30))

    # ------------------------------------------------------------------
    # Datos: renderizar carrito y recalcular totales
    # ------------------------------------------------------------------

    def _actualizar_lista(self):
        for widget in self.contenedor_lista.winfo_children():
            widget.destroy()

        items = carrito.obtener_carrito()

        if not items:
            ctk.CTkLabel(
                self.contenedor_lista, text="No hay productos en el pedido todavía.",
                font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
            ).pack(pady=20)
        else:
            for item in items:
                self._crear_fila_item(item)

        self._actualizar_totales()

    def _crear_fila_item(self, item):
        fila = ctk.CTkFrame(self.contenedor_lista, fg_color=COLOR_FILA, corner_radius=0, height=60)
        fila.pack(fill="x", pady=4)
        fila.pack_propagate(False)

        imagen_ctk = _cargar_imagen_item(item.get("imagen"))
        ctk.CTkLabel(fila, image=imagen_ctk, text="").pack(side="left", padx=(10, 8), pady=8)

        # Columna de texto: nombre arriba, precio unitario abajo, se
        # achica o crece según el espacio disponible sin empujar el resto.
        columna_info = ctk.CTkFrame(fila, fg_color="transparent")
        columna_info.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=8)

        ctk.CTkLabel(
            columna_info, text=item["descripcion"],
            font=("Arial", 13, "bold"), text_color=COLOR_TEXTO, anchor="w"
        ).pack(anchor="w", fill="x")

        ctk.CTkLabel(
            columna_info, text=f"${item['precio']:,.2f} c/u",
            font=("Arial", 11), text_color=COLOR_TEXTO_SECUNDARIO, anchor="w"
        ).pack(anchor="w", fill="x")

        stepper = ctk.CTkFrame(fila, fg_color="transparent")
        stepper.pack(side="left", padx=6)

        ctk.CTkButton(
            stepper, text="−", width=26, height=26,
            fg_color=COLOR_GRIS, hover_color=COLOR_GRIS_HOVER, corner_radius=0,
            command=lambda: self._cambiar_cantidad(item["codigo"], -1)
        ).pack(side="left")

        ctk.CTkLabel(
            stepper, text=str(item["cantidad"]), width=26,
            font=("Arial", 13, "bold"), text_color=COLOR_TEXTO
        ).pack(side="left")

        ctk.CTkButton(
            stepper, text="+", width=26, height=26,
            fg_color=COLOR_BOTON_ACTIVO, hover_color=COLOR_HOVER, corner_radius=0,
            command=lambda: self._cambiar_cantidad(item["codigo"], 1)
        ).pack(side="left")

        subtotal_item = item["precio"] * item["cantidad"]
        ctk.CTkLabel(
            fila, text=f"${subtotal_item:,.2f}",
            font=("Arial", 13, "bold"), text_color=COLOR_PRECIO, width=85
        ).pack(side="left", padx=6)

        # El botón eliminar va al final, con ancho fijo reservado y sin
        # 'expand' en ningún widget anterior que pueda robarle el espacio.
        ctk.CTkButton(
            fila, text="🗑", width=30, height=30,
            fg_color=COLOR_ROJO, hover_color=COLOR_ROJO_HOVER, corner_radius=0,
            command=lambda: self._eliminar_item(item["codigo"])
        ).pack(side="left", padx=(6, 10))

    def _cambiar_cantidad(self, codigo, delta):
        carrito.cambiar_cantidad(codigo, delta)
        self._actualizar_lista()

    def _eliminar_item(self, codigo):
        carrito.eliminar_producto(codigo)
        self._actualizar_lista()

    def _fila_total(self, texto, valor, destacado=False):
        """Crea y agrega una fila de total al contenedor_totales."""
        fila = ctk.CTkFrame(self.contenedor_totales, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=(10 if destacado else 4, 10 if destacado else 4))

        ctk.CTkLabel(
            fila, text=texto,
            font=("Arial", 15 if destacado else 13, "bold" if destacado else "normal"),
            text_color=COLOR_TEXTO if destacado else COLOR_TEXTO_SECUNDARIO
        ).pack(side="left")

        ctk.CTkLabel(
            fila, text=valor,
            font=("Arial", 17 if destacado else 13, "bold"),
            text_color=COLOR_PRECIO if destacado else COLOR_TEXTO
        ).pack(side="right")

    def _actualizar_totales(self):
        for widget in self.contenedor_totales.winfo_children():
            widget.destroy()

        subtotal = carrito.calcular_subtotal()

        try:
            porcentaje_descuento = float(self.entry_descuento.get()) if self.entry_descuento.get() else 0
        except ValueError:
            porcentaje_descuento = 0

        monto_descuento = subtotal * (porcentaje_descuento / 100)
        total_productos = subtotal - monto_descuento

        try:
            deuda = int(self.entry_deuda.get()) if self.entry_deuda.get() else 0
        except ValueError:
            deuda = 0

        total_final = total_productos + deuda

        self._fila_total("Subtotal", f"${subtotal:,.2f}")

        if monto_descuento > 0:
            self._fila_total("Descuento", f"-${monto_descuento:,.2f}")

        if monto_descuento > 0:
            self._fila_total("Total productos", f"${total_productos:,.2f}")

        if deuda > 0:
            self._fila_total("Deuda", f"${deuda:,.2f}")

        self._fila_total("Total a pagar", f"${total_final:,.2f}", destacado=True)

    # ------------------------------------------------------------------

    def _validar_numero_entero(self, texto):
        return texto == "" or texto.isdigit()

    def _validar_numero_decimal(self, texto):
        if texto == "":
            return True
        return texto.replace(".", "", 1).isdigit()

    def _generar_factura(self):
        items = carrito.obtener_carrito()

        if not items:
            mostrar_toast(self, "No hay productos en el pedido.", tipo="advertencia")
            return

        cliente = self.entry_cliente.get().strip()
        remito = self.entry_remito.get().strip() or "0"

        try:
            porcentaje_descuento = float(self.entry_descuento.get()) if self.entry_descuento.get() else 0
        except ValueError:
            porcentaje_descuento = 0

        try:
            deuda = int(self.entry_deuda.get()) if self.entry_deuda.get() else 0
        except ValueError:
            deuda = 0

        # Verifica que haya stock suficiente para cada producto del pedido
        productos_insuficientes = []
        for item in items:
            producto = obtener_producto(codigo=item["codigo"])
            if producto and item["cantidad"] > producto["cantidad_stock"]:
                productos_insuficientes.append(
                    f"{item['descripcion']} (pedís {item['cantidad']}, hay {producto['cantidad_stock']})"
                )

        if productos_insuficientes:
            mensaje = "Stock insuficiente:\n" + "\n".join(productos_insuficientes)
            confirmar = messagebox.askyesno(
                "Stock insuficiente",
                f"{mensaje}\n\n¿Querés continuar igual?"
            )
            if not confirmar:
                return

        nombre_sugerido = f"R-{remito}_{cliente or 'cliente'}.xlsx".replace(" ", "_")

        ruta = filedialog.asksaveasfilename(
            title="Guardar factura",
            defaultextension=".xlsx",
            filetypes=[("Archivo Excel", "*.xlsx")],
            initialfile=nombre_sugerido
        )

        if not ruta:
            return

        exito = generar_factura_excel(
            ruta, cliente, remito, items,
            porcentaje_descuento=porcentaje_descuento, deuda=deuda
        )

        if not exito:
            mostrar_toast(self, "No se pudo generar la factura.", tipo="error")
            return

        # Descuenta del stock lo vendido en esta factura
        for item in items:
            producto = obtener_producto(codigo=item["codigo"])
            if producto:
                nuevo_stock = max(0, producto["cantidad_stock"] - item["cantidad"])
                editar_producto(id=producto["id"], cantidad_stock=nuevo_stock)

        hacer_backup_db()

        # Limpia el carrito y sube el número de remito
        carrito.limpiar_carrito()
        establecer_proximo_remito(int(remito))

        self.entry_remito.delete(0, "end")
        self.entry_remito.insert(0, str(obtener_proximo_remito()))
        self.entry_cliente.delete(0, "end")
        self.entry_descuento.delete(0, "end")
        self.entry_deuda.delete(0, "end")

        self._actualizar_lista()

        mostrar_toast(self, "Factura generada y exportada correctamente.", tipo="exito")