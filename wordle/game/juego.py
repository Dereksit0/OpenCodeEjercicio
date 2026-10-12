"""Reglas de la partida: turnos, validacion, victoria y derrota.

No importa Streamlit. La partida se puede jugar entera desde la terminal
(mira test_wordle.py) sin levantar la interfaz.
"""

from __future__ import annotations

import string

from game.banco import BancoPalabras
from game.evaluador import EvaluadorPalabras
from game.modelos import Intento, Resultado

ABCEDARIO = set(string.ascii_lowercase)


class JuegoWordle:
    """Orquestador de una partida. Es el unico que sabe cuando se acaba."""

    ESTADO_JUGANDO = "jugando"
    ESTADO_GANADO = "ganado"
    ESTADO_PERDIDO = "perdido"

    def __init__(self, banco: BancoPalabras, config: dict) -> None:
        self.banco = banco
        self.config = dict(config)
        self.longitud = config["longitud_palabra"]
        self.intentos_maximos = config["intentos_maximos"]
        self.secreta: str = ""
        self.intentos: list[Intento] = []
        self.intentos_usados: int = 0
        self.estado: str = self.ESTADO_JUGANDO
        self.reiniciar()

    @classmethod
    def iniciar(cls, banco: BancoPalabras, config: dict) -> JuegoWordle:
        return cls(banco, config)

    # -- Estado -------------------------------------------------------------
    def reiniciar(self) -> None:
        """Baraja una palabra nueva y deja el contador a cero."""
        self.secreta = self.banco.elegir_secreta() or ""
        self.intentos = []
        self.intentos_usados = 0
        self.estado = self.ESTADO_JUGANDO

    def esta_jugando(self) -> bool:
        return self.estado == self.ESTADO_JUGANDO

    def quedan_intentos(self) -> int:
        return max(0, self.intentos_maximos - self.intentos_usados)

    # -- Turno --------------------------------------------------------------
    def intentar(self, palabra: str) -> Resultado:
        """Unico punto de entrada del jugador.

        Devuelve un Resultado con valido=False si la palabra no sirve, y en
        ese caso NO se cuenta intento. Devuelve valido=True con el Intento ya
        evaluado si la palabra entra al tablero.
        """
        if not self.esta_jugando():
            return Resultado(False, "La partida ya ha terminado.")

        palabra = self._normalizar(palabra)

        if len(palabra) != self.longitud:
            return Resultado(
                False, f"La palabra debe tener {self.longitud} letras."
            )

        if not self._solo_letras(palabra):
            return Resultado(
                False, "Solo se admiten las 26 letras del abecedario, sin ñ ni tildes."
            )

        if not self.banco.es_valida(palabra):
            return Resultado(
                False, f"«{palabra.upper()}» no está en el diccionario."
            )

        intento = self.registrar(palabra)
        self.comprobar_victoria()
        self.comprobar_derrota()
        return Resultado(True, "", intento)

    def registrar(self, palabra: str) -> Intento:
        """Mete el intento en el historial con sus colores ya resueltos."""
        estados = EvaluadorPalabras.evaluar(palabra, self.secreta)
        intento = Intento(
            numero=len(self.intentos) + 1,
            palabra=palabra,
            estados=estados,
        )
        self.intentos.append(intento)
        self.intentos_usados = len(self.intentos)
        return intento

    # -- Condiciones de fin -------------------------------------------------
    def comprobar_victoria(self) -> bool:
        """Gana quien acierte la palabra, en cualquiera de los 6 intentos."""
        if self.intentos and self.intentos[-1].es_correcto():
            self.estado = self.ESTADO_GANADO
            return True
        return False

    def comprobar_derrota(self) -> bool:
        """Se pierde al agotar los intentos.

        La comprobacion de que el estado sea "jugando" impide que la
        derrota salte en el mismo intento en el que se ha ganado.
        """
        if (
            self.estado == self.ESTADO_JUGANDO
            and self.intentos_usados >= self.intentos_maximos
        ):
            self.estado = self.ESTADO_PERDIDO
            return True
        return False

    # -- Utilidades internas ------------------------------------------------
    def _normalizar(self, palabra: str) -> str:
        """Quita espacios y pasa a minusculas segun la configuracion."""
        if self.config.get("permitir_espacios", True):
            palabra = palabra.strip()
        if self.config.get("normalizar_mayusculas", True):
            palabra = palabra.lower()
        return palabra

    def _solo_letras(self, palabra: str) -> bool:
        """Comprueba letra a letra.

        No se usa str.isalpha() porque en Python True tambien para la ñ
        y las tildes, que este juego no acepta.
        """
        if self.config.get("aceptar_tildes", False):
            return palabra.isalpha()
        return all(caracter in ABCEDARIO for caracter in palabra)
