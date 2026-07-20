from functions.db import inicializar_db
from ui.app import App


def main():
    """
    Punto de entrada de la aplicación.
    Inicializa la base de datos y luego lanza la interfaz gráfica.
    """
    inicializar_db()

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()  