import customtkinter as ctk
from PIL import Image
import os

# Colores usados en la topbar
COLOR_TOPBAR = "#242424"
COLOR_BOTON_ACTIVO = "#3b8ed0"
COLOR_HOVER = "#3a3a3a"
COLOR_TRANSPARENTE = "transparent"
COLOR_TEXTO = "#ffffff"

from functions.paths import obtener_ruta_assets
RUTA_ICONS = os.path.join(obtener_ruta_assets(), "icons")


class TopBar(ctk.CTkFrame):
    def __init__(self, master, on_navegar, pagina_inicial="stock"):
        """
        master: widget padre
        on_navegar: función callback que se llama al hacer click en un botón,
                    recibe el nombre de la página como argumento (ej: "stock")
        pagina_inicial: qué botón queda activo al iniciar
        """
        super().__init__(master, fg_color=COLOR_TOPBAR, corner_radius=0, height=60)
        self.on_navegar = on_navegar
        self.botones = {}
        self.pagina_activa = pagina_inicial

        # Definimos las páginas: (clave interna, texto visible, nombre del ícono)
        self.paginas = [
            ("stock", "Stock", "stock.png"),
            ("pedido", "Pedido", "pedido.png"),
            ("configuracion", "Configuración", "configuracion.png"),
            ("informacion", "Información", "informacion.png"),
        ]

        self._crear_botones()

    def _cargar_icono(self, nombre_archivo):
        """Carga un ícono desde assets/icons, devuelve None si no existe."""
        ruta = os.path.join(RUTA_ICONS, nombre_archivo)
        if os.path.exists(ruta):
            imagen = Image.open(ruta)
            return ctk.CTkImage(light_image=imagen, dark_image=imagen, size=(20, 20))
        return None

    def _crear_botones(self):
        contenedor = ctk.CTkFrame(self, fg_color=COLOR_TRANSPARENTE)
        contenedor.pack(side="left", padx=15, pady=10)

        for clave, texto, icono_nombre in self.paginas:
            icono = self._cargar_icono(icono_nombre)

            boton = ctk.CTkButton(
                contenedor,
                text=texto,
                image=icono,
                compound="left",
                fg_color=COLOR_BOTON_ACTIVO if clave == self.pagina_activa else COLOR_TRANSPARENTE,
                hover_color=COLOR_HOVER,
                text_color=COLOR_TEXTO,
                corner_radius=8,
                anchor="w",
                command=lambda c=clave: self._click_boton(c)
            )
            boton.pack(side="left", padx=5)
            self.botones[clave] = boton

    def _click_boton(self, clave):
        self.pagina_activa = clave
        self._actualizar_colores()
        self.on_navegar(clave)

    def _actualizar_colores(self):
        """Pinta de celeste el botón activo, y transparente el resto."""
        for clave, boton in self.botones.items():
            if clave == self.pagina_activa:
                boton.configure(fg_color=COLOR_BOTON_ACTIVO)
            else:
                boton.configure(fg_color=COLOR_TRANSPARENTE)