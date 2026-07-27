"""
functions/carrito.py

Carrito de pedido en memoria, compartido entre Stock (donde se agregan
productos) y Pedido (donde se ve el listado y se calculan totales).
Al ser un módulo, el estado persiste mientras la app esté abierta,
sin importar cuántas veces se recreen las páginas al navegar.
"""

_carrito = {}  # clave: codigo del producto, valor: dict con sus datos + cantidad


def agregar_producto(producto):
    """Agrega el producto con cantidad 1, o le suma 1 si ya estaba."""
    codigo = producto.get("codigo")
    if codigo in _carrito:
        _carrito[codigo]["cantidad"] += 1
    else:
        _carrito[codigo] = {
            "codigo": codigo,
            "descripcion": producto.get("descripcion", ""),
            "precio": producto.get("precio", 0),
            "imagen": producto.get("imagen"),
            "cantidad": 1,
        }
    return _carrito[codigo]["cantidad"]


def cambiar_cantidad(codigo, delta):
    """
    Suma 'delta' (positivo o negativo) a la cantidad. Si llega a 0,
    el producto se elimina del carrito. Devuelve la cantidad final.
    """
    if codigo not in _carrito:
        return 0

    _carrito[codigo]["cantidad"] += delta

    if _carrito[codigo]["cantidad"] <= 0:
        del _carrito[codigo]
        return 0

    return _carrito[codigo]["cantidad"]


def eliminar_producto(codigo):
    _carrito.pop(codigo, None)


def obtener_cantidad(codigo):
    return _carrito.get(codigo, {}).get("cantidad", 0)


def obtener_carrito():
    return list(_carrito.values())


def limpiar_carrito():
    _carrito.clear()


def calcular_subtotal():
    return sum(item["precio"] * item["cantidad"] for item in _carrito.values())