import threading
import customtkinter as ctk
from tkinter import filedialog

from functions.db import cargar_productos_excel

# ---------- Colores ----------
COLOR_FONDO = "#1a1a1a"
COLOR_TEXTO = "#ffffff"
COLOR_TEXTO_SECUNDARIO = "#9a9a9a"
COLOR_INPUT = "#242424"
COLOR_BORDE = "#3a3a3a"
COLOR_BOTON_ACTIVO = "#3b8ed0"
COLOR_HOVER = "#5aa5dd"
COLOR_GRIS = "#3a3a3a"
COLOR_GRIS_HOVER = "#4a4a4a"
COLOR_VERDE = "#2fa572"
COLOR_ROJO = "#e74c3c"


class VentanaSubirMasivo(ctk.CTkToplevel):
    """
    Ventana para elegir un archivo Excel y cargarlo masivamente al stock.
    """

    def __init__(self, master, on_completado=None):
        super().__init__(master)
        self.on_completado = on_completado
        self.ruta_archivo = None

        self.title("Subir productos masivamente")
        self.geometry("480x600")
        self.configure(fg_color=COLOR_FONDO)
        self.resizable(False, False)

        self.transient(master)
        self.grab_set()

        self._crear_widgets()

    def _crear_widgets(self):
        ctk.CTkLabel(
            self, text="Subir productos masivamente",
            font=("Arial", 18, "bold"), text_color=COLOR_TEXTO
        ).pack(pady=(20, 10))

        # ---------- Instrucciones ----------
        texto_ayuda = (
            "El archivo debe tener estas columnas en la primera fila:\n"
            "codigo, descripcion, cantidad_por_caja, cantidad_en_stock, precio\n\n"
            "Si hay algún error en los datos, no se subirá ningún producto."
        )
        ctk.CTkLabel(
            self, text=texto_ayuda,
            font=("Arial", 12), text_color=COLOR_TEXTO_SECUNDARIO,
            justify="left"
        ).pack(padx=25, pady=(0, 20), anchor="w")

        # ---------- Botón para elegir archivo ----------
        self.boton_archivo = ctk.CTkButton(
            self, text="Seleccionar archivo Excel",
            fg_color=COLOR_GRIS, hover_color=COLOR_GRIS_HOVER,
            text_color=COLOR_TEXTO, corner_radius=8,
            command=self._seleccionar_archivo
        )
        self.boton_archivo.pack(padx=25, pady=(0, 20), fill="x")

        # ---------- Barra de progreso ----------
        self.barra_progreso = ctk.CTkProgressBar(
            self, progress_color=COLOR_BOTON_ACTIVO
        )
        self.barra_progreso.pack(padx=25, pady=(0, 8), fill="x")
        self.barra_progreso.set(0)

        self.label_estado = ctk.CTkLabel(
            self, text="Esperando archivo...",
            font=("Arial", 12), text_color=COLOR_TEXTO_SECUNDARIO
        )
        self.label_estado.pack(pady=(0, 15))

        # ---------- Área con scroll para mostrar errores/resultado ----------
        self.contenedor_resultado = ctk.CTkScrollableFrame(
            self, fg_color=COLOR_INPUT, corner_radius=8
        )
        self.contenedor_resultado.pack(padx=25, pady=(0, 15), fill="both", expand=True)

        # ---------- Botones ----------
        fila_botones = ctk.CTkFrame(self, fg_color="transparent")
        fila_botones.pack(fill="x", padx=25, pady=(0, 20))

        self.boton_subir = ctk.CTkButton(
            fila_botones, text="Subir",
            fg_color=COLOR_BOTON_ACTIVO, hover_color=COLOR_HOVER,
            text_color=COLOR_TEXTO, corner_radius=8,
            font=("Arial", 13, "bold"),
            command=self._iniciar_carga
        )
        self.boton_subir.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            fila_botones, text="Cancelar",
            fg_color=COLOR_GRIS, hover_color=COLOR_GRIS_HOVER,
            text_color=COLOR_TEXTO, corner_radius=8,
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

    # ------------------------------------------------------------------

    def _seleccionar_archivo(self):
        """Abre el explorador de archivos para elegir el Excel."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta:
            self.ruta_archivo = ruta
            nombre_archivo = ruta.split("/")[-1]
            self.boton_archivo.configure(text=nombre_archivo)
            self.label_estado.configure(text="Archivo listo. Tocá 'Subir' para continuar.")

    def _iniciar_carga(self):
        """
        Lanza el procesamiento del Excel en un hilo aparte, para no
        congelar la ventana mientras se leen y validan las filas.
        """
        if not self.ruta_archivo:
            self.label_estado.configure(text="Primero seleccioná un archivo.", text_color=COLOR_ROJO)
            return

        # Limpiamos resultados de un intento anterior, si hubo
        for widget in self.contenedor_resultado.winfo_children():
            widget.destroy()

        self.boton_subir.configure(state="disabled")
        self.boton_archivo.configure(state="disabled")
        self.barra_progreso.configure(progress_color=COLOR_BOTON_ACTIVO)
        self.barra_progreso.set(0)
        self.barra_progreso.start()  # animación indeterminada mientras procesa
        self.label_estado.configure(text="Procesando archivo...", text_color=COLOR_TEXTO_SECUNDARIO)

        hilo = threading.Thread(target=self._procesar_en_segundo_plano, daemon=True)
        hilo.start()

    def _procesar_en_segundo_plano(self):
        """
        Corre en un hilo aparte: llama a la función de carga masiva
        (que puede tardar un momento) y después programa que el resultado
        se muestre en el hilo principal de la interfaz (con 'after').
        """
        resultado = cargar_productos_excel(self.ruta_archivo)
        self.after(0, lambda: self._mostrar_resultado(resultado))

    def _mostrar_resultado(self, resultado):
        """
        Se ejecuta en el hilo principal. Detiene la animación de la barra
        y la deja verde (éxito) o roja (error), mostrando el detalle.
        """
        self.barra_progreso.stop()
        self.boton_archivo.configure(state="normal")

        if resultado["exito"]:
            self.barra_progreso.configure(progress_color=COLOR_VERDE)
            self.barra_progreso.set(1)
            self.label_estado.configure(
                text=f"¡Listo! Se insertaron {resultado['insertados']} productos.",
                text_color=COLOR_VERDE
            )

            if resultado["duplicados"]:
                ctk.CTkLabel(
                    self.contenedor_resultado,
                    text=f"{len(resultado['duplicados'])} duplicado(s) descartado(s):",
                    font=("Arial", 12, "bold"), text_color=COLOR_TEXTO_SECUNDARIO,
                    anchor="w"
                ).pack(anchor="w", padx=10, pady=(10, 5))

                for texto in resultado["duplicados"]:
                    ctk.CTkLabel(
                        self.contenedor_resultado, text=f"• {texto}",
                        font=("Arial", 11), text_color=COLOR_TEXTO_SECUNDARIO,
                        anchor="w", justify="left", wraplength=400
                    ).pack(anchor="w", padx=10, pady=2)

            self.boton_subir.configure(text="Listo", state="disabled")

            if self.on_completado:
                self.on_completado()

        else:
            self.barra_progreso.configure(progress_color=COLOR_ROJO)
            self.barra_progreso.set(1)
            self.label_estado.configure(
                text=f"Se encontraron {len(resultado['errores'])} error(es). No se subió nada.",
                text_color=COLOR_ROJO
            )

            ctk.CTkLabel(
                self.contenedor_resultado,
                text="Errores encontrados:",
                font=("Arial", 12, "bold"), text_color=COLOR_ROJO,
                anchor="w"
            ).pack(anchor="w", padx=10, pady=(10, 5))

            for texto in resultado["errores"]:
                ctk.CTkLabel(
                    self.contenedor_resultado, text=f"• {texto}",
                    font=("Arial", 11), text_color=COLOR_TEXTO_SECUNDARIO,
                    anchor="w", justify="left", wraplength=400
                ).pack(anchor="w", padx=10, pady=2)

            # Permite corregir el archivo y volver a intentar
            self.boton_subir.configure(state="normal")