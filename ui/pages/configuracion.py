import customtkinter as ctk

from functions.config import (
    obtener_email_vendedor, guardar_email_vendedor,
    obtener_productos_por_pagina, guardar_productos_por_pagina
)
from ui.components.toast import mostrar_toast

COLOR_FONDO = "#1a1a1a"
COLOR_TEXTO = "#ffffff"
COLOR_TEXTO_SECUNDARIO = "#9a9a9a"
COLOR_INPUT = "#242424"
COLOR_BORDE = "#3a3a3a"
COLOR_BOTON_ACTIVO = "#3b8ed0"
COLOR_HOVER = "#5aa5dd"


class PaginaConfiguracion(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLOR_FONDO)

        ctk.CTkLabel(
            self, text="Configuración",
            font=("Arial", 24, "bold"), text_color=COLOR_TEXTO
        ).pack(anchor="w", padx=30, pady=(30, 20))

        # ---------- Email del vendedor ----------
        ctk.CTkLabel(
            self, text="Email de contacto (aparece en la lista exportada)",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=30)

        self.entry_email = ctk.CTkEntry(
            self, fg_color=COLOR_INPUT, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO, height=38, corner_radius=0
        )
        self.entry_email.pack(fill="x", padx=30, pady=(5, 20))
        self.entry_email.insert(0, obtener_email_vendedor())

        # ---------- Cantidad de productos por página ----------
        ctk.CTkLabel(
            self, text="Productos por página en Stock",
            font=("Arial", 13), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=30)

        validar_entero = self.register(self._validar_numero_entero)
        self.entry_por_pagina = ctk.CTkEntry(
            self, fg_color=COLOR_INPUT, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO, height=38, corner_radius=0,
            validate="key", validatecommand=(validar_entero, "%P")
        )
        self.entry_por_pagina.pack(fill="x", padx=30, pady=(5, 5))
        self.entry_por_pagina.insert(0, str(obtener_productos_por_pagina()))

        ctk.CTkLabel(
            self, text="El cambio se aplica la próxima vez que abras la app.",
            font=("Arial", 11), text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=30, pady=(0, 20))

        # ---------- Botón guardar ----------
        ctk.CTkButton(
            self, text="Guardar cambios",
            fg_color=COLOR_BOTON_ACTIVO, hover_color=COLOR_HOVER,
            text_color=COLOR_TEXTO, corner_radius=0,
            font=("Arial", 14, "bold"), height=42,
            command=self._guardar
        ).pack(fill="x", padx=30, pady=(0, 20))

    def _validar_numero_entero(self, texto):
        return texto == "" or texto.isdigit()

    def _guardar(self):
        email = self.entry_email.get().strip()
        cantidad_texto = self.entry_por_pagina.get().strip()

        if not email:
            mostrar_toast(self, "El email no puede estar vacío.", tipo="advertencia")
            return

        cantidad = int(cantidad_texto) if cantidad_texto else 20
        if cantidad < 1:
            cantidad = 1

        guardar_email_vendedor(email)
        guardar_productos_por_pagina(cantidad)

        mostrar_toast(self, "Configuración guardada correctamente.", tipo="exito")