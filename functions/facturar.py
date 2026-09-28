"""
functions/facturar.py

Genera la factura del pedido como Excel, siguiendo la planilla en papel:
PRESUPUESTO/cliente, DIRECCION, remito y fecha, tabla de artículos y
totales (con descuento y deuda si corresponde).

Cada hoja lleva DOS copias iguales, una arriba (vendedor) y otra abajo
(cliente), separadas por una línea gruesa. Si el pedido tiene pocos
productos las dos copias entran en una sola A4; si tiene muchos, cada
copia pasa a su propia hoja.
"""

from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.pagebreak import Break

from functions.logger import obtener_logger
from functions.config import obtener_direccion_empresa

logger = obtener_logger()

# Colores
COLOR_NEGRO = "000000"
COLOR_BLANCO = "FFFFFF"
COLOR_GRIS_CLARO = "D9D9D9"

# Bordes
BORDE_GRUESO = Side(style="thick", color=COLOR_NEGRO)
BORDE_FINO = Side(style="thin", color=COLOR_NEGRO)
BORDE_CELDA = Border(left=BORDE_FINO, right=BORDE_FINO, top=BORDE_FINO, bottom=BORDE_FINO)

# Formatos de número
FORMATO_PESOS = '"$"#,##0.00'
FORMATO_DESCUENTO = '-"$"#,##0.00'  # muestra el monto con signo menos adelante

# Columnas: A=Artículo (código), B=Descripción, C=Cantidad, D=Precio, E=Total
ANCHO_COLUMNAS = {"A": 14, "B": 42, "C": 12, "D": 14, "E": 16}

# Filas mínimas de la tabla de productos. Si hay menos productos las filas
# sobrantes quedan vacías; si hay más, la tabla crece sola.
# Es también el máximo con el que entran las dos copias en una A4.
# Si con los totales extra no entran, bajarlo a 14.
FILAS_PRODUCTOS_MIN = 16


def generar_factura_excel(ruta_destino, cliente, remito, items, porcentaje_descuento=0, deuda=0):
    """
    Genera el Excel de la factura en 'ruta_destino' con las dos copias.

    items: lista de dicts con codigo, descripcion, precio y cantidad.
    Devuelve True si se generó bien, False si hubo algún error.
    """
    try:
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Factura"

        for col, ancho in ANCHO_COLUMNAS.items():
            hoja.column_dimensions[col].width = ancho

        # Cálculos: se hacen una sola vez y se usan en las dos copias
        subtotal = sum(i["precio"] * i["cantidad"] for i in items)
        monto_descuento = subtotal * (porcentaje_descuento / 100)
        total_final = subtotal - monto_descuento + (deuda or 0)

        fecha = datetime.now().strftime("%d-%m-%y")
        direccion = obtener_direccion_empresa()

        # ¿Hay más productos de los que entran con las dos copias en una hoja?
        pedido_largo = len(items) > FILAS_PRODUCTOS_MIN

        # Copia 1 (arriba)
        ultima_fila_copia_1 = _dibujar_copia(
            hoja, 1, cliente, remito, fecha, direccion, items,
            subtotal, monto_descuento, porcentaje_descuento, deuda, total_final
        )

        # Separador: una fila en blanco, la línea gruesa y otra fila en blanco
        fila_separador = ultima_fila_copia_1 + 2
        for col_idx in range(1, 6):
            hoja.cell(row=fila_separador, column=col_idx).border = Border(top=BORDE_GRUESO)
        hoja.row_dimensions[ultima_fila_copia_1 + 1].height = 18
        hoja.row_dimensions[fila_separador].height = 10
        hoja.row_dimensions[fila_separador + 1].height = 18

        # Copia 2 (abajo)
        ultima_fila_copia_2 = _dibujar_copia(
            hoja, fila_separador + 2, cliente, remito, fecha, direccion, items,
            subtotal, monto_descuento, porcentaje_descuento, deuda, total_final
        )

        # Impresión: A4 vertical, todo el ancho en una sola página
        hoja.page_setup.orientation = "portrait"
        hoja.page_setup.paperSize = hoja.PAPERSIZE_A4
        hoja.page_setup.fitToWidth = 1
        hoja.sheet_properties.pageSetUpPr.fitToPage = True
        hoja.print_area = f"A1:E{ultima_fila_copia_2}"
        hoja.page_margins = PageMargins(left=0.3, right=0.3, top=0.3, bottom=0.3)

        if pedido_largo:
            # No entran las dos copias juntas: la segunda arranca en otra hoja
            hoja.page_setup.fitToHeight = 0
            hoja.row_breaks.append(Break(id=fila_separador + 1))
        else:
            # Las dos copias entran juntas en una sola A4
            hoja.page_setup.fitToHeight = 1

        libro.save(ruta_destino)
        logger.info(f"Factura generada en '{ruta_destino}' (remito {remito}, cliente '{cliente}').")
        return True

    except Exception as e:
        logger.error(f"Error al generar la factura: {e}")
        return False


def _celda(hoja, fila, col, valor=None, negrita=False, tamano=11, color=COLOR_NEGRO,
           fondo=None, horizontal="center", indent=0, formato=None):
    """Escribe una celda con su estilo y borde. Evita repetir todo el formateo."""
    celda = hoja.cell(row=fila, column=col, value=valor)
    celda.font = Font(bold=negrita, size=tamano, color=color)
    celda.alignment = Alignment(horizontal=horizontal, vertical="center", indent=indent)
    celda.border = BORDE_CELDA
    if fondo:
        celda.fill = PatternFill("solid", fgColor=fondo)
    if formato:
        celda.number_format = formato
    return celda


def _dibujar_copia(hoja, fila_inicio, cliente, remito, fecha, direccion, items,
                   subtotal, monto_descuento, porcentaje_descuento, deuda, total_final):
    """
    Dibuja una copia completa (encabezado, tabla y totales) desde 'fila_inicio'.
    Devuelve el número de la última fila que usó.
    """
    fila = fila_inicio

    # --- Fila 1: PRESUPUESTO | cliente (B:C) | remito | fecha ---
    _celda(hoja, fila, 1, "PRESUPUESTO", negrita=True, fondo=COLOR_BLANCO)
    hoja.merge_cells(start_row=fila, start_column=2, end_row=fila, end_column=3)
    _celda(hoja, fila, 2, cliente or "-", negrita=True, tamano=13, fondo=COLOR_GRIS_CLARO)
    _celda(hoja, fila, 3, fondo=COLOR_GRIS_CLARO)  # celda absorbida por el merge, solo estilo
    _celda(hoja, fila, 4, f"R - {remito}", negrita=True, tamano=12, fondo=COLOR_BLANCO)
    _celda(hoja, fila, 5, fecha, negrita=True, fondo=COLOR_BLANCO)
    hoja.row_dimensions[fila].height = 24
    fila += 1

    # --- Fila 2: DIRECCION | dirección (B:C) | resto en gris ---
    _celda(hoja, fila, 1, "DIRECCION", negrita=True, fondo=COLOR_GRIS_CLARO)
    hoja.merge_cells(start_row=fila, start_column=2, end_row=fila, end_column=3)
    _celda(hoja, fila, 2, direccion or "-", fondo=COLOR_GRIS_CLARO, horizontal="left", indent=1)
    _celda(hoja, fila, 3, fondo=COLOR_GRIS_CLARO)
    _celda(hoja, fila, 4, fondo=COLOR_GRIS_CLARO)
    _celda(hoja, fila, 5, fondo=COLOR_GRIS_CLARO)
    hoja.row_dimensions[fila].height = 22
    fila += 1

    # --- Encabezados de la tabla (fondo negro, letra blanca) ---
    for col_idx, texto in enumerate(["Artículo", "Descripción", "Cantidad", "Precio", "Total"], start=1):
        _celda(hoja, fila, col_idx, texto, negrita=True, color=COLOR_BLANCO, fondo=COLOR_NEGRO)
    hoja.row_dimensions[fila].height = 20
    fila += 1

    # --- Filas de productos ---
    # Se dibujan como mínimo FILAS_PRODUCTOS_MIN filas; si hay más productos,
    # se dibuja una fila por cada uno. La columna del código va en gris
    # aunque la fila esté vacía, como en la planilla en papel.
    cantidad_filas = max(FILAS_PRODUCTOS_MIN, len(items))

    for i in range(cantidad_filas):
        item = items[i] if i < len(items) else None

        _celda(hoja, fila, 1, item["codigo"] if item else None,
               negrita=True, tamano=10, fondo=COLOR_GRIS_CLARO)
        _celda(hoja, fila, 2, item["descripcion"] if item else None, horizontal="left")
        _celda(hoja, fila, 3, item["cantidad"] if item else None, negrita=True)
        _celda(hoja, fila, 4, item["precio"] if item else None, formato=FORMATO_PESOS)
        _celda(hoja, fila, 5, item["precio"] * item["cantidad"] if item else None,
               formato=FORMATO_PESOS)
        fila += 1

    # --- Totales ---
    def _fila_total(texto, valor, tamano=11):
        """Fila de totales: etiqueta a la derecha (A:D) y el valor en E."""
        nonlocal fila
        hoja.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=4)
        _celda(hoja, fila, 1, texto, negrita=True, tamano=tamano,
               fondo=COLOR_GRIS_CLARO, horizontal="right")
        for col_idx in range(2, 5):
            _celda(hoja, fila, col_idx, fondo=COLOR_GRIS_CLARO)
        _celda(hoja, fila, 5, valor, negrita=True, tamano=tamano,
               fondo=COLOR_GRIS_CLARO, formato=FORMATO_PESOS)
        hoja.row_dimensions[fila].height = 20
        fila += 1

    hay_descuento = monto_descuento > 0
    hay_deuda = bool(deuda and deuda > 0)
    total_compra = subtotal - monto_descuento  # la compra ya con el descuento aplicado

    # Caso simple: sin descuento ni deuda, alcanza con un TOTAL
    if not hay_descuento and not hay_deuda:
        _fila_total("TOTAL", subtotal, tamano=13)
        return fila - 1

    # Parte de la compra
    if hay_descuento:
        _fila_total("SUBTOTAL", subtotal)

        # Fila del descuento: A y B vacías, C = etiqueta, D = porcentaje, E = monto
        _celda(hoja, fila, 1, fondo=COLOR_GRIS_CLARO)
        _celda(hoja, fila, 2, fondo=COLOR_GRIS_CLARO)
        _celda(hoja, fila, 3, "Descuento", negrita=True, fondo=COLOR_GRIS_CLARO, horizontal="right")
        _celda(hoja, fila, 4, f"{porcentaje_descuento:g}%", negrita=True, fondo=COLOR_GRIS_CLARO)
        _celda(hoja, fila, 5, monto_descuento, negrita=True, fondo=COLOR_GRIS_CLARO,
               formato=FORMATO_DESCUENTO)
        hoja.row_dimensions[fila].height = 20
        fila += 1

        _fila_total("", total_compra, tamano=12 if hay_deuda else 13)
    else:
        _fila_total("TOTAL", subtotal, tamano=12)

    # Parte de la deuda
    if hay_deuda:
        _fila_total("SALDO ANTERIOR", deuda)
        _fila_total("SUBTOTAL", total_final, tamano=13)

    return fila - 1
