from tkinter import messagebox

from functions.db import inicializar_db
from ui.app import App


def main():
    """
    Punto de entrada de la aplicación.
    Inicializa la base de datos y luego lanza la interfaz gráfica.
    """
    try:
        inicializar_db()
    except Exception as e:
        # Si esto falla, la app no puede seguir. Como en Windows el .exe
        # corre sin consola visible, mostramos un mensaje nativo para que
        # el usuario (y no solo el log) se entere de que algo salió mal.
        messagebox.showerror(
            "MF App - Error al iniciar",
            "No se pudo inicializar la base de datos.\n\n"
            f"Detalle: {e}\n\n"
            "Revisá el archivo de log en la carpeta de la app."
        )
        return

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()