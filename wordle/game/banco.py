"""El banco de palabras: guarda la lista, la valida y sortea la secreta.

Guarda tambien la longitud con la que se construyo. Asi es_valida() y
elegir_secreta() no necesitan parametros y siempre trabajan con palabras
de la medida correcta, aunque el jugador cambie la longitud en la barra
lateral.
"""

from __future__ import annotations

import random

from datos.palabras import PALABRAS


class BancoPalabras:
    def __init__(self, palabras: list[str], longitud: int = 5) -> None:
        self.longitud = longitud
        # El dato se escribe en MAYUSCULAS porque se lee mejor en el
        # archivo, pero el juego trabaja siempre en minusculas (es lo que
        # produce normalizar() al validar). Se pasa a minusculas aqui una
        # sola vez para que comparar nunca falle por mayusculas.
        #
        # Una lista para sortear en orden y un set para buscar rapido:
        # la validacion se ejecuta en cada intento, no en cada clic.
        self.palabras = [p.lower() for p in palabras if len(p) == longitud]
        self.validas = set(self.palabras)

    @classmethod
    def construir(cls, longitud: int = 5) -> BancoPalabras:
        """Carga datos/palabras.py una sola vez y lo deja filtrado."""
        return cls(PALABRAS, longitud)

    def total(self) -> int:
        return len(self.palabras)

    def es_valida(self, palabra: str) -> bool:
        return palabra in self.validas

    def elegir_secreta(self) -> str | None:
        return random.choice(self.palabras) if self.palabras else None
