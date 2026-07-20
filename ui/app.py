import sys
import os

import customtkinter as ctk
from PIL import Image
from tkinter import PhotoImage

from ui.components.topbar import TopBar
from ui.pages.stock import PaginaStock
from ui.pages.pedido import PaginaPedido
from ui.pages.configuracion import PaginaConfiguracion
from ui.pages.informacion import PaginaInformacion

COLOR_FONDO = "#1a1a1a"

# Carpeta assets, un nivel arriba de ui/
RUTA_ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


class App(ctk.CTk):
    """
    Ventana principal de la aplicación.
    Contiene la barra superior (TopBar) y un contenedor donde se
    muestra la página activa (Stock, Pedido, Configuración, Información).
    """

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")

        self.title("MF App")
        self.configure(fg_color=COLOR_FONDO)

        self._configurar_icono()
        self._maximizar_ventana()

        # ---------- Barra superior ----------
        self.topbar = TopBar(self, on_navegar=self.mostrar_pagina, pagina_inicial="stock")
        self.topbar.pack(side="top", fill="x")

        # ---------- Contenedor de páginas ----------
        self.contenedor = ctk.CTkFrame(self, fg_color=COLOR_FONDO, corner_radius=0)
        self.contenedor.pack(side="top", fill="both", expand=True)

        # Diccionario clave -> clase de la página (todavía no instanciadas)
        self.clases_paginas = {
            "stock": PaginaStock,
            "pedido": PaginaPedido,
            "configuracion": PaginaConfiguracion,
            "informacion": PaginaInformacion,
        }

        self.pagina_actual = None
        self.mostrar_pagina("stock")  # página inicial

    def _configurar_icono(self):
        """
        Configura el ícono de la ventana según el sistema operativo.
        Windows necesita .ico, Linux usa .png.
        """
        if sys.platform.startswith("win"):
            ruta_icono = os.path.join(RUTA_ASSETS, "icon.ico")
            if os.path.exists(ruta_icono):
                self.iconbitmap(ruta_icono)
        else:
            ruta_icono = os.path.join(RUTA_ASSETS, "icon.png")
            if os.path.exists(ruta_icono):
                icono_tk = PhotoImage(file=ruta_icono)
                self.iconphoto(True, icono_tk)

    def _maximizar_ventana(self):
        """
        Maximiza la ventana al iniciar, según el sistema operativo.
        """
        if sys.platform.startswith("win"):
            self.state("zoomed")
        else:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                # Respaldo por si el gestor de ventanas de Linux no soporta -zoomed
                self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")

    def mostrar_pagina(self, clave):
        """
        Destruye la página actual (si hay una) y muestra la nueva,
        según la clave recibida desde el TopBar.
        """
        if self.pagina_actual is not None:
            self.pagina_actual.destroy()

        clase_pagina = self.clases_paginas[clave]
        self.pagina_actual = clase_pagina(self.contenedor)
        self.pagina_actual.pack(fill="both", expand=True)