import os
import shutil
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image

from functions.db import insertar_producto, editar_producto, codigo_es_valido
from functions.paths import obtener_carpeta_imgs
from functions.logger import obtener_logger
from ui.components.toast import mostrar_toast

logger = obtener_logger()

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
    def __init__(self, master, producto=None, on_guardado=None):
        super().__init__(master)

        self.producto = producto  # None = modo agregar, dict = modo editar
        self.on_guardado = on_guardado
        self.ruta_imagen_seleccionada = None

        self.title("Editar producto" if self.producto else "Añadir producto")
        self.geometry("450x650")
        self.configure(fg_color=COLOR_FONDO)
        self.resizable(False, False)

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
            self, text="Editar producto" if self.producto else "Añadir producto",
            font=("Arial", 20, "bold"), text_color=COLOR_TEXTO
        ).pack(pady=(20, 15))

        # ---------- Botón para seleccionar imagen ----------
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

        self.contenedor_precio = ctk.CTkFrame(
            self, fg_color=COLOR_INPUT, corner_radius=8,
            border_width=1, border_color=COLOR_BORDE
        )
        self.contenedor_precio.pack(pady=(5, 15), padx=25, fill="x")

        ctk.CTkLabel(
            self.contenedor_precio, text="$", text_color=COLOR_TEXTO_SECUNDARIO,
            font=("Arial", 13, "bold")
        ).pack(side="left", padx=(12, 5), pady=8)

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

        # ---------- Botón principal ----------
        ctk.CTkButton(
            self, text="Editar producto" if self.producto else "Añadir producto",
            fg_color=COLOR_BOTON_ACTIVO, hover_color=COLOR_HOVER,
            text_color=COLOR_TEXTO, corner_radius=8,
            font=("Arial", 13, "bold"),
            command=self._confirmar_guardar
        ).pack(pady=(5, 8), padx=25, fill="x")

        # ---------- Botón secundario: Cancelar ----------
        ctk.CTkButton(
            self, text="Cancelar",
            fg_color=COLOR_GRIS, hover_color=COLOR_GRIS_HOVER,
            text_color=COLOR_TEXTO, corner_radius=8,
            command=self.destroy
        ).pack(pady=(0, 20), padx=25, fill="x")

        # ---------- Si es modo edición, precargamos los campos ----------
        if self.producto:
            self.entry_nombre.insert(0, self.producto.get("descripcion", ""))
            self.entry_codigo.insert(0, self.producto.get("codigo", ""))
            self.entry_precio.insert(0, str(self.producto.get("precio", "")))
            self.entry_stock.insert(0, str(self.producto.get("cantidad_stock", "")))
            self.entry_caja.insert(0, str(self.producto.get("cantidad_caja", "")))

            imagen_actual = self.producto.get("imagen")
            if imagen_actual and imagen_actual != "default.png":
                self.boton_imagen.configure(
                    text=imagen_actual,
                    fg_color=COLOR_VERDE,
                    hover_color=COLOR_VERDE_HOVER
                )

        # ---------- Binds para "limpiar" el borde rojo al corregir ----------
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
        return texto == "" or texto.isdigit()

    def _validar_numero_decimal(self, texto):
        if texto == "":
            return True
        return texto.replace(".", "", 1).isdigit()

    # ------------------------------------------------------------------
    # Selección de imagen
    # ------------------------------------------------------------------

    def _seleccionar_imagen(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen del producto",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )

        if ruta:
            self.ruta_imagen_seleccionada = ruta
            nombre_archivo = os.path.basename(ruta)

            self.boton_imagen.configure(
                text=nombre_archivo,
                fg_color=COLOR_VERDE,
                hover_color=COLOR_VERDE_HOVER
            )

    def _procesar_y_guardar_imagen(self, ruta_origen, ruta_destino, tamano_maximo=500, calidad=85):
        imagen = Image.open(ruta_origen)

        if imagen.mode in ("RGBA", "LA") or (imagen.mode == "P" and "transparency" in imagen.info):
            imagen = imagen.convert("RGBA")
            fondo = Image.new("RGB", imagen.size, (255, 255, 255))
            fondo.paste(imagen, mask=imagen.split()[-1])
            imagen = fondo
        else:
            imagen = imagen.convert("RGB")

        imagen.thumbnail((tamano_maximo, tamano_maximo), Image.LANCZOS)
        imagen.save(ruta_destino, "JPEG", quality=calidad, optimize=True)

    # ------------------------------------------------------------------
    # Confirmar y guardar el producto
    # ------------------------------------------------------------------

    def _confirmar_guardar(self):
        self._resetear_bordes()

        nombre = self.entry_nombre.get().strip()
        codigo = self.entry_codigo.get().strip()
        precio_texto = self.entry_precio.get().strip()
        stock_texto = self.entry_stock.get().strip()
        caja_texto = self.entry_caja.get().strip()

        hay_error = False

        if not nombre:
            self.entry_nombre.configure(border_color=COLOR_ERROR)
            hay_error = True

        if not codigo:
            self.entry_codigo.configure(border_color=COLOR_ERROR)
            hay_error = True
        elif not codigo_es_valido(codigo):
            # El código se usa para armar el nombre del archivo de imagen
            # (ej: "ABC123.jpg"), así que no puede tener '/', '\', espacios
            # ni otros caracteres que rompan una ruta de archivo.
            self.entry_codigo.configure(border_color=COLOR_ERROR)
            self.label_error.configure(
                text="El código solo puede tener letras, números, '-' y '_'."
            )
            mostrar_toast(self, "El código solo puede tener letras, números, '-' y '_'.", tipo="advertencia")
            return

        if not precio_texto:
            self.contenedor_precio.configure(border_color=COLOR_ERROR)
            hay_error = True

        if hay_error:
            self.label_error.configure(text="Completá los campos obligatorios marcados en rojo.")
            mostrar_toast(self, "Completá los campos obligatorios.", tipo="advertencia")
            return

        try:
            precio = float(precio_texto)
        except ValueError:
            self.contenedor_precio.configure(border_color=COLOR_ERROR)
            self.label_error.configure(text="El precio debe ser un número válido.")
            mostrar_toast(self, "El precio debe ser un número válido.", tipo="error")
            return

        cantidad_stock = int(stock_texto) if stock_texto else 1
        cantidad_caja = int(caja_texto) if caja_texto else 1

        nombre_imagen_final = None
        if self.ruta_imagen_seleccionada:
            nombre_imagen_final = f"{codigo}.jpg"
        elif self.producto:
            imagen_anterior = self.producto.get("imagen")
            if imagen_anterior and imagen_anterior != "default.png":
                extension = os.path.splitext(imagen_anterior)[1]
                nombre_imagen_final = f"{codigo}{extension}"
            else:
                nombre_imagen_final = imagen_anterior

        if self.producto:
            # ---------- Modo edición ----------
            imagen_anterior = self.producto.get("imagen")

            try:
                exito = editar_producto(
                    id=self.producto["id"],
                    codigo=codigo,
                    descripcion=nombre,
                    precio=precio,
                    cantidad_caja=cantidad_caja,
                    cantidad_stock=cantidad_stock,
                    imagen=nombre_imagen_final
                )
            except Exception as e:
                logger.error(f"Error inesperado al editar producto: {e}")
                mostrar_toast(self, "Ocurrió un error inesperado al editar el producto.", tipo="error")
                return

            if not exito:
                self.entry_codigo.configure(border_color=COLOR_ERROR)
                self.label_error.configure(text=f"No se pudo editar (¿el código '{codigo}' ya existe en otro producto?).")
                mostrar_toast(self, f"El código '{codigo}' ya existe en otro producto.", tipo="error")
                return

            # ---------- Sincronizar el archivo de imagen con el cambio ----------
            carpeta_imgs = obtener_carpeta_imgs()

            if self.ruta_imagen_seleccionada:
                try:
                    destino = carpeta_imgs / nombre_imagen_final
                    self._procesar_y_guardar_imagen(self.ruta_imagen_seleccionada, destino)

                    if (imagen_anterior and imagen_anterior != "default.png"
                            and imagen_anterior != nombre_imagen_final):
                        ruta_anterior = carpeta_imgs / imagen_anterior
                        if ruta_anterior.exists():
                            ruta_anterior.unlink()
                except Exception as e:
                    self.label_error.configure(text=f"Producto editado, pero falló la imagen: {e}")
                    mostrar_toast(self, "Producto editado, pero falló guardar la imagen.", tipo="advertencia")

            elif (imagen_anterior and imagen_anterior != "default.png"
                    and imagen_anterior != nombre_imagen_final):
                try:
                    ruta_anterior = carpeta_imgs / imagen_anterior
                    ruta_nueva = carpeta_imgs / nombre_imagen_final
                    if ruta_anterior.exists():
                        ruta_anterior.rename(ruta_nueva)
                except Exception as e:
                    self.label_error.configure(text=f"Producto editado, pero falló renombrar la imagen: {e}")
                    mostrar_toast(self, "Producto editado, pero falló renombrar la imagen.", tipo="advertencia")

        else:
            # ---------- Modo agregar ----------
            try:
                nuevo_id = insertar_producto(
                    codigo=codigo,
                    descripcion=nombre,
                    precio=precio,
                    cantidad_caja=cantidad_caja,
                    cantidad_stock=cantidad_stock,
                    imagen=nombre_imagen_final
                )
            except Exception as e:
                logger.error(f"Error inesperado al insertar producto: {e}")
                mostrar_toast(self, "Ocurrió un error inesperado al guardar el producto.", tipo="error")
                return

            if nuevo_id is None:
                self.entry_codigo.configure(border_color=COLOR_ERROR)
                self.label_error.configure(text=f"El código '{codigo}' ya existe.")
                mostrar_toast(self, f"El código '{codigo}' ya existe.", tipo="error")
                return

            if self.ruta_imagen_seleccionada:
                try:
                    carpeta_imgs = obtener_carpeta_imgs()
                    destino = carpeta_imgs / nombre_imagen_final
                    self._procesar_y_guardar_imagen(self.ruta_imagen_seleccionada, destino)
                except Exception as e:
                    self.label_error.configure(text=f"Producto guardado, pero falló la imagen: {e}")
                    mostrar_toast(self, "Producto guardado, pero falló guardar la imagen.", tipo="advertencia")

        if self.on_guardado:
            self.on_guardado()

        # Se dispara con self.master porque esta ventana está por cerrarse
        mostrar_toast(
            self.master,
            "Producto editado correctamente." if self.producto else "Producto añadido correctamente.",
            tipo="exito"
        )

        self.destroy()

    def _resetear_bordes(self):
        self.entry_nombre.configure(border_color=COLOR_BORDE)
        self.entry_codigo.configure(border_color=COLOR_BORDE)
        self.contenedor_precio.configure(border_color=COLOR_BORDE)
        self.label_error.configure(text="")