from functions.db import inicializar_db


def main():
    """
    Punto de entrada de la aplicación.
    Al iniciar, se asegura de que la base de datos (y sus carpetas)
    existan antes de continuar con el resto del programa.
    """
    inicializar_db()

    # Acá más adelante vamos a llamar a la interfaz (UI)
    print("La app inició correctamente.")


if __name__ == "__main__":
    main()