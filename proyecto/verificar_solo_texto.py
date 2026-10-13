# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2026-10-12 15:48:32
# @Last Modified by:   Your name
# @Last Modified time: 2026-10-12 16:49:16
"""Comprueba que entre dos versiones de un archivo solo cambio el texto.

La usa la skill `texto-con-tema`: recibe la copia de respaldo (original) y el
archivo ya tematizado, y aborta el despegue si el codigo cambio. Para
decidirlo acopla ambas tomas con `ast`, enmascara la carga de todo
`ast.Constant` de tipo `str` o `bytes` (docstrings incluidas) y compara la
estructura resultante. Los numeros, identificadores, operadores y el control
de flujo quedan a la vista, de modo que cualquier variacion real en el codigo
hace que la comparacion pierda la orbita. Los comentarios no viajan en el
AST, asi que tematizarlos nunca enciende la alarma.

Uso:
    python verificar_solo_texto.py <original.py> <modificado.py>
    python verificar_solo_texto.py  # despliega los selectores de orbita

Codigo de salida:
    0: solo cambio el texto (o el contenido de los strings), codigo intacto.
    1: el codigo cambio, o alguno de los archivos no compila.
    2: uso incorrecto o se aborto la seleccion de archivos.
"""

from __future__ import annotations

import ast
import difflib
import sys
from pathlib import Path


def _enmascarar_strings(arbol: ast.AST) -> ast.AST:
    """Purga la carga de cada string, conservando si era `str` o `bytes`.

    Args:
        arbol: Arbol sintactico que se va a poner a cero.

    Returns:
        El mismo arbol, con las cargas `str` y `bytes` al vacio. Los demas
        tipos de `Constant` (numeros, `None`, `True`, `False`) no se tocan.
    """
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Constant):
            continue
        if isinstance(nodo.value, str):
            nodo.value = ""
        elif isinstance(nodo.value, bytes):
            nodo.value = b""
    return arbol


def _leer(ruta: Path) -> str:
    """Recupera un fichero Python como UTF-8, tolerando un BOM inicial.

    Args:
        ruta: Archivo que se quiere recuperar de la memoria de a bordo.

    Returns:
        El contenido del archivo como texto.
    """
    return ruta.read_text(encoding="utf-8-sig")


def _seleccionar_archivos() -> tuple[Path, Path] | None:
    """Despliega los selectores de orbita cuando el script arranca sin argumentos.

    Returns:
        Las rutas del original y del modificado, o `None` si se aborto.

    Raises:
        ImportError: Si Tkinter no esta a bordo en esta instalacion de Python.
        tk.TclError: Si no se puede encender la consola grafica de mando.
    """
    import tkinter as tk
    from tkinter import filedialog

    ventana = tk.Tk()
    try:
        ventana.withdraw()
        original = filedialog.askopenfilename(
            title="Captura el archivo original",
            filetypes=[("Archivos Python", "*.py"), ("Todos los archivos", "*.*")],
        )
        if not original:
            return None

        modificado = filedialog.askopenfilename(
            title="Captura el archivo modificado",
            filetypes=[("Archivos Python", "*.py"), ("Todos los archivos", "*.*")],
        )
        if not modificado:
            return None

        return Path(original), Path(modificado)
    finally:
        ventana.destroy()


def _dump(fuente: str) -> str:
    """Escanea la fuente y devuelve su AST con los strings enmascarados.

    Se usa `indent=2` para que el `dump` salga en varias lineas de telemetria
    y el diff posterior se lea sin hipoxia.

    Args:
        fuente: Codigo fuente Python.

    Returns:
        El `ast.dump` del arbol normalizado, listo para comparar y difear.

    Raises:
        SyntaxError: Si la fuente no acopla.
    """
    arbol = ast.parse(fuente)
    return ast.dump(_enmascarar_strings(arbol), indent=2, include_attributes=False)


def main(argv: list[str]) -> int:
    """Acopla dos versiones de un archivo y decide si el codigo quedo igual.

    Args:
        argv: Argumentos del proceso; se esperan original, modificado y nada
            mas.

    Returns:
        El codigo de salida descrito en el docstring del modulo.
    """
    if len(argv) == 1:
        rutas = _seleccionar_archivos()
        if rutas is None:
            print("FAIL: se aborto la seleccion de archivos.")
            return 2
        original, modificado = rutas
    elif len(argv) == 3:
        original = Path(argv[1])
        modificado = Path(argv[2])
    else:
        print("uso: verificar_solo_texto.py <original.py> <modificado.py>")
        return 2

    try:
        antes = _dump(_leer(original))
    except (OSError, SyntaxError) as error:
        print(f"FAIL: no se pudo recuperar ni acoplar el original: {error}")
        return 1
    try:
        despues = _dump(_leer(modificado))
    except (OSError, SyntaxError) as error:
        print(f"FAIL: no se pudo recuperar ni acoplar el modificado: {error}")
        return 1

    if antes == despues:
        print(
            f"OK: solo cambio el texto, el codigo sigue a bordo ({modificado.name})"
        )
        return 0

    print(f"FAIL: el codigo se desvio en {modificado.name}")
    for linea in difflib.unified_diff(
        antes.splitlines(),
        despues.splitlines(),
        fromfile=f"original/{original.name}",
        tofile=f"modificado/{modificado.name}",
        lineterm="",
    ):
        print(linea)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
