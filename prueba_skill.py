"""Sonda de verificacion para la skill de traduccion de comentarios.

Este modulo es desechable: permite comprobar que la skill
`comentarios-a-ingles` traduce comentarios y docstrings sin alterar el
comportamiento. No forma parte de mascota, wordle ni proyecto.
"""

from __future__ import annotations


def sumar_pares(numeros: list[int]) -> int:
    """Suma los valores pares de una muestra numerica.

    Args:
        numeros: Muestra de enteros; puede estar vacia.

    Returns:
        Suma de los valores pares; devuelve 0 si no hay ninguno.

    Example:
        >>> sumar_pares([1, 2, 3, 4])
        6
    """
    # La expresion generadora analiza la muestra sin crear una lista intermedia.
    return sum(valor for valor in numeros if valor % 2 == 0)


def main() -> None:
    """Ejecuta las comprobaciones de control y comunica el resultado."""
    # Muestra de control: 2 + 4 = 6, con comparacion de igualdad estricta.
    resultado = sumar_pares([1, 2, 3, 4])
    assert resultado == 6, f"la telemetria esperaba 6 y obtuvo {resultado}"

    # Una muestra vacia debe producir cero sin interrumpir el experimento.
    assert sumar_pares([]) == 0, "una muestra vacia debe producir cero"

    print("OK: calculo cientifico-lunar validado")


if __name__ == "__main__":
    main()
