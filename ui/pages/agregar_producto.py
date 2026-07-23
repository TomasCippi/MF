import os
import shutil
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image

from functions.db import insertar_producto
from functions.paths import obtener_carpeta_imgs


# ---------- Colores usados en esta ventana ----------
COLOR_FONDO = "#1a1a1a"
COLOR_TEXTO = "#ffffff"
COLOR_TEXTO_SECUNDARIO = "#9a9a9a"
COLOR_INPUT = "#242424"
COLOR_BORDE = "#3a3a3a"          # borde normal de los inputs
COLOR_ERROR = "#e74c3c"          # borde rojo cuando falta un campo obligatorio
COLOR_BOTON_ACTIVO = "#3b8ed0"   # celeste, botón principal "Añadir producto"
COLOR_HOVER = "#5aa5dd"
COLOR_GRIS = "#3a3a3a"           # gris del botón "Cancelar" y "Seleccionar imagen"
COLOR_GRIS_HOVER = "#4a4a4a"
COLOR_VERDE = "#2fa572"          # color del botón de imagen una vez seleccionada
COLOR_VERDE_HOVER = "#268a5e"


class VentanaAgregarProducto(ctk.CTkToplevel):
    """
    Ventana emergente para añadir un producto nuevo.
    Hereda de CTkToplevel, que es la clase de CustomTkinter para
    crear ventanas secundarias (independientes de la ventana principal).
    """

    def __init__(self, master, on_producto_agregado=None):
        super().__init__(master)

        self.on_producto_agregado = on_producto_agregado

        # Ruta original del archivo de imagen elegido por el usuario.
        # Se guarda en memoria nada más; la copia real a la carpeta de
        # la app se hace recién al confirmar el producto.
        self.ruta_imagen_seleccionada = None

        # ---------- Configuración básica de la ventana ----------
        self.title("Añadir producto")
        self.geometry("450x650")
        self.configure(fg_color=COLOR_FONDO)
        self.resizable(False, False)

        # 'transient' asocia esta ventana a la principal (se minimiza con ella, etc).
        # 'grab_set' bloquea la interacción con la ventana principal mientras
        # este popup esté abierto, para evitar que el usuario haga doble click
        # en "Añadir producto" o interactúe con el fondo por error.
        self.transient(master)
        self.grab_set()

        self._crear_widgets()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _crear_widgets(self):
        """Crea y ubica todos los elementos visuales de la ventana."""

        # ---------- Título ----------
        ctk.CTkLabel(
            self, text="Añadir producto",
            font=("Arial", 20, "bold"), text_color=COLOR_TEXTO
        ).pack(pady=(20, 15))

        # ---------- Botón para seleccionar imagen ----------
        # Arranca gris con el texto "Seleccionar imagen". Al elegir un
        # archivo, se pone verde y muestra el nombre del archivo elegido.
        self.boton_imagen = ctk.CTkButton(
            self, text="Seleccionar imagen",
            fg_color=COLOR_GRIS, hover_color=COLOR_GRIS_HOVER,
            text_color=COLOR_TEXTO, corner_radius=8,
            command=self._seleccionar_imagen
        )
        self.boton_imagen.pack(pady=(0, 20), padx=25, fill="x")

        # ---------- Nombre del producto (obligatorio) ----------
        ctk.CTkLabel(
            self, text="Nombre del producto",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=25)

        self.entry_nombre = ctk.CTkEntry(
            self, fg_color=COLOR_INPUT, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO
        )
        self.entry_nombre.pack(pady=(5, 15), padx=25, fill="x")

        # ---------- Código (obligatorio) ----------
        ctk.CTkLabel(
            self, text="Código",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=25)

        self.entry_codigo = ctk.CTkEntry(
            self, fg_color=COLOR_INPUT, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO
        )
        self.entry_codigo.pack(pady=(5, 15), padx=25, fill="x")

        # ---------- Precio (obligatorio, con símbolo $ al inicio) ----------
        ctk.CTkLabel(
            self, text="Precio",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=25)

        # Este frame actúa como "input compuesto": el símbolo $ fijo
        # a la izquierda, y adentro el Entry real sin bordes propios.
        # Se guarda como atributo (self.contenedor_precio) porque es
        # a este frame al que le pintamos el borde rojo si falta el precio.
        self.contenedor_precio = ctk.CTkFrame(
            self, fg_color=COLOR_INPUT, corner_radius=8,
            border_width=1, border_color=COLOR_BORDE
        )
        self.contenedor_precio.pack(pady=(5, 15), padx=25, fill="x")

        ctk.CTkLabel(
            self.contenedor_precio, text="$", text_color=COLOR_TEXTO_SECUNDARIO,
            font=("Arial", 13, "bold")
        ).pack(side="left", padx=(12, 5), pady=8)

        # 'register' envuelve nuestra función de validación para que
        # Tkinter pueda llamarla en cada tecla presionada (validate="key").
        validar_decimal = self.register(self._validar_numero_decimal)
        self.entry_precio = ctk.CTkEntry(
            self.contenedor_precio, fg_color="transparent", border_width=0,
            text_color=COLOR_TEXTO,
            validate="key", validatecommand=(validar_decimal, "%P")
        )
        self.entry_precio.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=8)

        # ---------- Cantidad en stock / Cantidad por caja (opcionales) ----------
        fila_cantidades = ctk.CTkFrame(self, fg_color="transparent")
        fila_cantidades.pack(pady=(0, 20), padx=25, fill="x")

        validar_entero = self.register(self._validar_numero_entero)

        # Columna izquierda: cantidad en stock
        columna_stock = ctk.CTkFrame(fila_cantidades, fg_color="transparent")
        columna_stock.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkLabel(
            columna_stock, text="Cantidad en stock",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w")

        self.entry_stock = ctk.CTkEntry(
            columna_stock, fg_color=COLOR_INPUT, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO,
            validate="key", validatecommand=(validar_entero, "%P")
        )
        self.entry_stock.pack(pady=(5, 0), fill="x")

        # Columna derecha: cantidad por caja
        columna_caja = ctk.CTkFrame(fila_cantidades, fg_color="transparent")
        columna_caja.pack(side="left", fill="x", expand=True, padx=(8, 0))

        ctk.CTkLabel(
            columna_caja, text="Cantidad por caja",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w")

        self.entry_caja = ctk.CTkEntry(
            columna_caja, fg_color=COLOR_INPUT, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO,
            validate="key", validatecommand=(validar_entero, "%P")
        )
        self.entry_caja.pack(pady=(5, 0), fill="x")

        # ---------- Mensaje de error (debajo de los campos) ----------
        self.label_error = ctk.CTkLabel(
            self, text="", text_color=COLOR_ERROR, font=("Arial", 12)
        )
        self.label_error.pack(pady=(0, 5))

        # ---------- Botón principal: Añadir producto ----------
        ctk.CTkButton(
            self, text="Añadir producto",
            fg_color=COLOR_BOTON_ACTIVO, hover_color=COLOR_HOVER,
            text_color=COLOR_TEXTO, corner_radius=8,
            font=("Arial", 13, "bold"),
            command=self._confirmar_agregar
        ).pack(pady=(5, 8), padx=25, fill="x")

        # ---------- Botón secundario: Cancelar ----------
        ctk.CTkButton(
            self, text="Cancelar",
            fg_color=COLOR_GRIS, hover_color=COLOR_GRIS_HOVER,
            text_color=COLOR_TEXTO, corner_radius=8,
            command=self.destroy
        ).pack(pady=(0, 20), padx=25, fill="x")

        # ---------- Binds para "limpiar" el borde rojo al corregir ----------
        # Apenas el usuario empieza a escribir en un campo que había quedado
        # marcado en rojo, el borde vuelve a la normalidad automáticamente.
        self.entry_nombre.bind(
            "<KeyRelease>",
            lambda e: self.entry_nombre.configure(border_color=COLOR_BORDE)
        )
        self.entry_codigo.bind(
            "<KeyRelease>",
            lambda e: self.entry_codigo.configure(border_color=COLOR_BORDE)
        )
        self.entry_precio.bind(
            "<KeyRelease>",
            lambda e: self.contenedor_precio.configure(border_color=COLOR_BORDE)
        )

    # ------------------------------------------------------------------
    # Validaciones de entrada numérica (se ejecutan en cada tecla)
    # ------------------------------------------------------------------

    def _validar_numero_entero(self, texto):
        """
        Permite solo dígitos (0-9), o el campo vacío (para poder borrar
        todo el contenido sin que Tkinter lo rechace).
        """
        return texto == "" or texto.isdigit()

    def _validar_numero_decimal(self, texto):
        """
        Permite números con un único punto decimal (ej: '1250.50'),
        o el campo vacío. 'replace(".", "", 1)' quita como máximo un
        punto antes de chequear que el resto sean todos dígitos.
        """
        if texto == "":
            return True
        return texto.replace(".", "", 1).isdigit()

    # ------------------------------------------------------------------
    # Selección de imagen
    # ------------------------------------------------------------------

    def _seleccionar_imagen(self):
        """
        Abre el explorador de archivos del sistema operativo para elegir
        una imagen. Importante: acá NO se copia el archivo a ningún lado,
        solo se guarda la ruta en memoria (self.ruta_imagen_seleccionada).
        La copia real se hace en _confirmar_agregar(), y solo si el
        producto se pudo insertar correctamente en la base de datos.
        """
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen del producto",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )

        if ruta:
            self.ruta_imagen_seleccionada = ruta
            nombre_archivo = os.path.basename(ruta)

            # Cambiamos el botón a verde y mostramos el nombre del archivo,
            # como confirmación visual de que la imagen fue elegida.
            self.boton_imagen.configure(
                text=nombre_archivo,
                fg_color=COLOR_VERDE,
                hover_color=COLOR_VERDE_HOVER
            )

    def _procesar_y_guardar_imagen(self, ruta_origen, ruta_destino, tamano_maximo=500, calidad=85):
        imagen = Image.open(ruta_origen)

        # Si tiene canal de transparencia, la aplanamos sobre fondo blanco
        if imagen.mode in ("RGBA", "LA") or (imagen.mode == "P" and "transparency" in imagen.info):
            imagen = imagen.convert("RGBA")
            fondo = Image.new("RGB", imagen.size, (255, 255, 255))
            fondo.paste(imagen, mask=imagen.split()[-1])  # usa el canal alfa como máscara
            imagen = fondo
        else:
            imagen = imagen.convert("RGB")

        # Escala manteniendo proporción, sin recortar, para que entre
        # dentro de un cuadro de tamano_maximo x tamano_maximo.
        # Image.LANCZOS da buena calidad al reducir tamaño.
        imagen.thumbnail((tamano_maximo, tamano_maximo), Image.LANCZOS)

        imagen.save(ruta_destino, "JPEG", quality=calidad, optimize=True)

    # ------------------------------------------------------------------
    # Confirmar y guardar el producto
    # ------------------------------------------------------------------

    def _confirmar_agregar(self):
        """
        Válida los campos obligatorios (marcando en rojo los que falten),
        inserta el producto en la base de datos y, si todo salió bien,
        copia la imagen seleccionada a la carpeta de almacenamiento de
        la app, renombrada con el código del producto.
        """
        # Primero limpiamos cualquier borde rojo que haya quedado de un
        # intento anterior, así no se acumulan errores viejos.
        self._resetear_bordes()

        # Leemos y limpiamos los valores de los campos
        nombre = self.entry_nombre.get().strip()
        codigo = self.entry_codigo.get().strip()
        precio_texto = self.entry_precio.get().strip()
        stock_texto = self.entry_stock.get().strip()
        caja_texto = self.entry_caja.get().strip()

        # ---------- Validación de campos obligatorios ----------
        hay_error = False

        if not nombre:
            self.entry_nombre.configure(border_color=COLOR_ERROR)
            hay_error = True

        if not codigo:
            self.entry_codigo.configure(border_color=COLOR_ERROR)
            hay_error = True

        if not precio_texto:
            self.contenedor_precio.configure(border_color=COLOR_ERROR)
            hay_error = True

        if hay_error:
            self.label_error.configure(text="Completá los campos obligatorios marcados en rojo.")
            return

        # ---------- Conversión y validación del precio ----------
        try:
            precio = float(precio_texto)
        except ValueError:
            self.contenedor_precio.configure(border_color=COLOR_ERROR)
            self.label_error.configure(text="El precio debe ser un número válido.")
            return

        # Cantidades opcionales: si el usuario no completó nada, usamos 1
        # (mismo criterio que ya definimos en functions/db.py)
        cantidad_stock = int(stock_texto) if stock_texto else 1
        cantidad_caja = int(caja_texto) if caja_texto else 1

        # ---------- Nombre final de la imagen (todavía no se copia) ----------
        nombre_imagen_final = None
        if self.ruta_imagen_seleccionada:
            nombre_imagen_final = f"{codigo}.jpg"

        # ---------- Insertar el producto en la base de datos ----------
        nuevo_id = insertar_producto(
            codigo=codigo,
            descripcion=nombre,
            precio=precio,
            cantidad_caja=cantidad_caja,
            cantidad_stock=cantidad_stock,
            imagen=nombre_imagen_final
        )

        # insertar_producto() devuelve None si el código ya existía
        if nuevo_id is None:
            self.entry_codigo.configure(border_color=COLOR_ERROR)
            self.label_error.configure(text=f"El código '{codigo}' ya existe.")
            return

        # ---------- Recién ahora procesamos y guardamos la imagen ----------
        # Solo llegamos acá si el producto se insertó con éxito.
        if self.ruta_imagen_seleccionada:
            try:
                carpeta_imgs = obtener_carpeta_imgs()
                # Siempre guardamos como .jpg, sin importar la extensión original
                destino = carpeta_imgs / f"{codigo}.jpg"
                self._procesar_y_guardar_imagen(self.ruta_imagen_seleccionada, destino)
            except Exception as e:
                # El producto ya quedó guardado en la base; si falla la
                # imagen, avisamos pero no revertimos el producto creado.
                self.label_error.configure(text=f"Producto guardado, pero falló la imagen: {e}")

        # ---------- Avisar a quien abrió esta ventana (ej: página Stock) ----------
        if self.on_producto_agregado:
            self.on_producto_agregado()

        # Cierra la ventana emergente
        self.destroy()

    def _resetear_bordes(self):
        """
        Vuelve todos los bordes de los campos obligatorios a su color
        normal, y limpia el mensaje de error. Se llama al inicio de cada
        intento de confirmar, para no arrastrar errores de intentos previos.
        """
        self.entry_nombre.configure(border_color=COLOR_BORDE)
        self.entry_codigo.configure(border_color=COLOR_BORDE)
        self.contenedor_precio.configure(border_color=COLOR_BORDE)
        self.label_error.configure(text="")