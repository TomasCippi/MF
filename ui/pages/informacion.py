import customtkinter as ctk


class PaginaInformacion(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#1a1a1a")
        ctk.CTkLabel(self, text="Página de Informacion", font=("Arial", 20)).pack(pady=30)