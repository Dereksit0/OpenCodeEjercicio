"""Modelos de datos del Wordle: piezas puras, sin Streamlit y sin reglas.

Aqui solo se guarda informacion (una palabra, sus colores, un resultado).
Quien decide si la partida continua o termina es game/juego.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EstadoLetra(Enum):
    """El color de una casilla. VACIA es para los huecos del tablero que
    todavia no se han jugado, y se usa tambien como clase CSS."""

    VERDE = "verde"
    AMARILLO = "amarillo"
    GRIS = "gris"
    VACIA = "vacia"

    def valor(self) -> str:
        return self.value

    def color_css(self) -> str:
        """La clase CSS que se pondra en el <div> de la casilla.

        Vive aqui, y no en app.py, para que el HTML nunca se desincronice
        con el modelo: si mañana el verde se pinta de otro color, se toca
        este diccionario y nada mas.
        """
        return COLOR_CSS[self]


COLOR_CSS = {
    EstadoLetra.VERDE: "verde",
    EstadoLetra.AMARILLO: "amarillo",
    EstadoLetra.GRIS: "gris",
    EstadoLetra.VACIA: "vacia",
}

COLORES_WORDLE = {
    EstadoLetra.VERDE: "#538d4e",
    EstadoLetra.AMARILLO: "#b59f3b",
    EstadoLetra.GRIS: "#3a3a3c",
}


@dataclass
class Intento:
    """Una palabra ya jugada y el color que ha salido en cada letra."""

    numero: int
    palabra: str
    estados: list[EstadoLetra]

    def es_correcto(self) -> bool:
        """True si las 5 casillas son verdes: el jugador ha ganado."""
        return all(estado is EstadoLetra.VERDE for estado in self.estados)

    def letras_verde(self) -> str:
        """Solo las letras ya acertadas. Sirve para un futuro modo dificil,
        donde no se puede proposer una palabra que contradiga las pistas
        ya colocadas."""
        return "".join(
            letra
            for letra, estado in zip(self.palabra, self.estados)
            if estado is EstadoLetra.VERDE
        )


@dataclass
class Resultado:
    """Lo que devuelve JuegoWordle.intentar().

    Separar "ha sido valido" de "intento" evita que la interfaz tenga que
    adivinar por su cuenta si un turno se conto o no.
    """

    valido: bool
    error: str = ""
    intento: Intento | None = None

    def exito(self) -> bool:
        return self.valido and self.intento is not None
