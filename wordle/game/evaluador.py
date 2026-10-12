"""Traduce un intento en los 5 colores que se pintan.

Aqui vive la unica parte dificil de verdad del Wordle: las letras
repetidas. La regla mental es una sola:

    cada letra de la palabra secreta se puede acertar UNA sola vez.

Por eso hacen falta dos pasadas. En la primera se colocan los verdes, que
tienen prioridad absoluta. En la segunda se recorren los huecos buscando
amarillos, pero descontando del contador las letras que ya se gastaron en
los verdes. Si se hiciera en una sola pasada, "ALGAS" contra "SALSA"
daria cinco amarillos cuando solo hay dos 'A' y un 'S' disponibles.
"""

from __future__ import annotations

from game.modelos import EstadoLetra


class EvaluadorPalabras:
    """Solo metodos estaticos: no guarda estado, se puede usar suelto."""

    @staticmethod
    def evaluar(intento: str, secreta: str) -> list[EstadoLetra]:
        """Devuelve un estado por letra del intento, en orden.

        Se da por hecho que intento y secreta tienen la misma longitud: de
        eso se encarga JuegoWordle.intentar(), que valida antes de llegar
        aqui. Si se llamara directamente con cadenas distintas, daria error.
        """
        estados = [EstadoLetra.GRIS] * len(secreta)

        EvaluadorPalabras._marcar_verdes(intento, secreta, estados)
        restantes = EvaluadorPalabras._contar_restantes(secreta, estados)
        EvaluadorPalabras._marcar_amarillos(intento, estados, restantes)

        return estados

    @staticmethod
    def _marcar_verdes(intento: str, secreta: str, estados: list[EstadoLetra]) -> None:
        """Pasada 1: letra correcta en su sitio. Solo eso se toca todavia."""
        for posicion in range(len(secreta)):
            if intento[posicion] == secreta[posicion]:
                estados[posicion] = EstadoLetra.VERDE

    @staticmethod
    def _contar_restantes(secreta: str, estados: list[EstadoLetra]) -> dict[str, int]:
        """Cuantas copias de cada letra quedan por colocar.

        Las posiciones ya verdes se ponen a cero: su letra ya se ha
        acertado y no puede volver a amarilla en otro sitio.
        """
        restantes: dict[str, int] = {}
        for posicion, letra in enumerate(secreta):
            if estados[posicion] is EstadoLetra.VERDE:
                continue
            restantes[letra] = restantes.get(letra, 0) + 1
        return restantes

    @staticmethod
    def _marcar_amarillos(
        intento: str,
        estados: list[EstadoLetra],
        restantes: dict[str, int],
    ) -> None:
        """Pasada 2: si la letra existe pero en otro sitio, se marca
        amarilla y se gasta una unidad del contador."""
        for posicion, letra in enumerate(intento):
            if estados[posicion] is EstadoLetra.VERDE:
                continue  # ya resuelta en la pasada 1
            if restantes.get(letra, 0) > 0:
                estados[posicion] = EstadoLetra.AMARILLO
                restantes[letra] -= 1
