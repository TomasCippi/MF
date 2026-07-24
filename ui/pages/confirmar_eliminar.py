"""
ui/pages/confirmar_eliminar.py

Ventana emergente (popup) de confirmación antes de eliminar un producto.
Muestra el nombre del producto en grande, y dos botones: Eliminar (rojo)
y Cancelar (gris). Solo si se confirma, se llama a eliminar_producto()
de functions/db.py.
"""

import customtkinter as ctk
from functions.db import eliminar_producto
from ui.components.toast import mostrar_toast

# ---------- Colores ----------
COLOR_FONDO = "#1a1a1a"
COLOR_TEXTO = "#ffffff"
COLOR_ROJO = "#e74c3c"
COLOR_ROJO_HOVER = "#c0392b"
COLOR_GRIS = "#3a3a3a"
COLOR_GRIS_HOVER = "#4a4a4a"


class VentanaConfirmarEliminar(ctk.CTkToplevel):
    """
    Ventana emergente que pide confirmación antes de eliminar un producto.

    producto: diccionario del producto a eliminar (necesita al menos 'codigo'
               y 'descripcion').
    on_eliminado: callback opcional, se llama después de eliminar con éxito
                  (por ejemplo, para refrescar la lista de Stock).
    """

    def __init__(self, master, producto, on_eliminado=None):
        super().__init__(master)
        self.producto = producto
        self.on_eliminado = on_eliminado

        self.title("Confirmar eliminación")
        self.geometry("380x220")
        self.configure(fg_color=COLOR_FONDO)
        self.resizable(False, False)

        self.transient(master)
        self.grab_set()

        self._crear_widgets()

    def _crear_widgets(self):
        ctk.CTkLabel(
            self,
            text="¿Eliminar este producto?",
            font=("Arial", 14),
            text_color="#9a9a9a"
        ).pack(pady=(30, 5))

        nombre = self.producto.get("descripcion", "")
        ctk.CTkLabel(
            self,
            text=nombre,
            font=("Arial", 22, "bold"),
            text_color=COLOR_TEXTO,
            wraplength=320,
            justify="center"
        ).pack(pady=(0, 30), padx=20)

        fila_botones = ctk.CTkFrame(self, fg_color="transparent")
        fila_botones.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(
            fila_botones,
            text="Eliminar",
            fg_color=COLOR_ROJO,
            hover_color=COLOR_ROJO_HOVER,
            text_color=COLOR_TEXTO,
            corner_radius=8,
            font=("Arial", 13, "bold"),
            command=self._confirmar_eliminacion
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            fila_botones,
            text="Cancelar",
            fg_color=COLOR_GRIS,
            hover_color=COLOR_GRIS_HOVER,
            text_color=COLOR_TEXTO,
            corner_radius=8,
            font=("Arial", 13),
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _confirmar_eliminacion(self):
        """
        Elimina el producto de la base de datos usando su código,
        avisa al callback (si existe) para refrescar la lista, muestra
        un toast de confirmación y cierra la ventana.
        """
        nombre = self.producto.get("descripcion", "El producto")
        eliminar_producto(codigo=self.producto.get("codigo"))

        if self.on_eliminado:
            self.on_eliminado()

        # Se dispara con self.master porque esta ventana está por cerrarse
        mostrar_toast(self.master, f"{nombre} eliminado correctamente.", tipo="exito")

        self.destroy()