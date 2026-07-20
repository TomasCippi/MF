import customtkinter as ctk


class PaginaConfiguracion(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#1a1a1a")
        ctk.CTkLabel(self, text="Página de Configuración", font=("Arial", 20)).pack(pady=30)