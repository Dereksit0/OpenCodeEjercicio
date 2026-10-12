"""Modelos de datos: estructuras puras, sin Streamlit y sin reglas de partida.

Aqui vive el "que" (los datos) y no el "cuando" (el paso de los turnos),
que es cosa de game/juego.py. Asi se puede probar cada pieza por separado.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from config import DEFAULT_CONFIG

# Las tres estadisticas del juego, siempre en este orden.
CLAVES = ("hambre", "energia", "felicidad")

ICONOS_ESTADISTICA = {"hambre": "🍖", "energia": "⚡", "felicidad": "💖"}


# ---------------------------------------------------------------------------
# Estadisticas
# ---------------------------------------------------------------------------
@dataclass
class Estadisticas:
    """Las tres barras de la mascota. Es la unica puerta de entrada a los valores.

    Nadie debe escribir "estadisticas.hambre = 50" directamente: siempre se
    pasa por aumentar() o disminuir(), que recortan a [0, maximo]. Asi es
    imposible que una estadistica se salga de rango.
    """

    hambre: int = 60
    energia: int = 70
    felicidad: int = 65
    maximo: int = 100

    def valor(self, estadistica: str) -> int:
        return getattr(self, estadistica)

    def _aplicar(self, estadistica: str, cantidad: int) -> None:
        nuevo = max(0, min(self.maximo, self.valor(estadistica) + cantidad))
        setattr(self, estadistica, nuevo)

    def aumentar(self, estadistica: str, cantidad: int) -> None:
        """Sube una estadistica. Un valor negativo actua como bajada."""
        self._aplicar(estadistica, cantidad)

    def disminuir(self, estadistica: str, cantidad: int) -> None:
        """Baja una estadistica sin poder bajar de 0."""
        self._aplicar(estadistica, -cantidad)

    def contar_bajas(self, umbral_bajo: int = 30) -> int:
        """Cuantas estadisticas estan en zona critica."""
        return sum(1 for clave in CLAVES if self.valor(clave) <= umbral_bajo)

    def esta_critica(self, umbral_bajo: int = 30) -> bool:
        return self.contar_bajas(umbral_bajo) > 0

    def mas_bajas(self) -> str:
        """Devuelve el nombre de la estadistica mas baja. Se usa para decidir
        por que se escapa la mascota cuando llega a 0."""
        return min(CLAVES, key=lambda clave: self.valor(clave))

    def esta_a_cero(self) -> bool:
        return any(self.valor(clave) <= 0 for clave in CLAVES)

    def esta_alta(self, umbral_alto: int = 70) -> bool:
        return all(self.valor(clave) >= umbral_alto for clave in CLAVES)

    def estado_general(self, umbral_bajo: int = 30, umbral_alto: int = 70) -> str:
        """Traduce los numeros a un estado emocional legible."""
        if self.contar_bajas(umbral_bajo) >= 2:
            return "enferma"
        if self.hambre <= umbral_bajo:
            return "hambrienta"
        if self.energia <= umbral_bajo:
            return "cansada"
        if self.felicidad <= umbral_bajo:
            return "triste"
        if self.esta_alta(umbral_alto):
            return "feliz"
        return "normal"

    def copiar(self) -> Estadisticas:
        return Estadisticas(
            hambre=self.hambre,
            energia=self.energia,
            felicidad=self.felicidad,
            maximo=self.maximo,
        )


# ---------------------------------------------------------------------------
# Accion
# ---------------------------------------------------------------------------
class Accion(Enum):
    """Las tres acciones del jugador. Solo describen COMO se mueven los
    numeros (deltas); de cuando se aplican decide el Juego."""

    ALIMENTAR = "alimentar"
    JUGAR = "jugar"
    DORMIR = "dormir"

    def nombre(self) -> str:
        return self.value.capitalize()

    def icono(self) -> str:
        return {"alimentar": "🍎", "jugar": "🎾", "dormir": "😴"}[self.value]

    def etiqueta(self) -> str:
        """Texto del boton."""
        return f"{self.icono()} {self.nombre()}"

    def deltas(self, config: dict | None = None) -> dict:
        """Cuanto cambia cada estadistica con esta accion.

        Sin argumentos usa los valores por defecto de config.py; pasando
        el config de la partida se respetan los valores que el jugador
        haya cambiado en la barra lateral.
        """
        activo = config or DEFAULT_CONFIG
        return {
            clave: activo[f"{self.value}_{clave}"] for clave in CLAVES
        }

    def mensaje_exito(self) -> str:
        return random.choice(MENSAJES_ACCION[self.value])


# ---------------------------------------------------------------------------
# Evento
# ---------------------------------------------------------------------------
@dataclass
class Evento:
    """Suceso aleatorio que el tiempo impone a la mascota.

    "probabilidad" es un PESO RELATIVO dentro del catalogo: entre todos los
    eventos, el mas alto sale mas veces. Si solo hay un evento, sale siempre.
    Que salte o no en un turno lo decide config["probabilidad_evento"].
    """

    nombre: str
    icono: str
    descripcion: str
    deltas: dict
    probabilidad: float = 1.0

    @classmethod
    def generar_aleatorio(cls) -> Evento:
        return random.choices(
            CATALOGO_EVENTOS,
            weights=[evento.probabilidad for evento in CATALOGO_EVENTOS],
            k=1,
        )[0]

    def aplicar(self, estadisticas: Estadisticas) -> None:
        for clave, cantidad in self.deltas.items():
            if cantidad >= 0:
                estadisticas.aumentar(clave, cantidad)
            else:
                estadisticas.disminuir(clave, -cantidad)

    def texto(self) -> str:
        return f"{self.icono} {self.nombre}: {self.descripcion}"


CATALOGO_EVENTOS: list[Evento] = [
    Evento("Lluvia sorpresa", "🌧️", "Me ha mojado el pelito y me he puesto de morado.", {"hambre": -5, "felicidad": -5}, 2.0),
    Evento("Golpe de calor", "🥵", "¡Mucho calor! Necesito sombra urgentemente.", {"energia": -10, "felicidad": -3}, 2.0),
    Evento("Bicho en el pelo", "🐛", "¡Socorro! Un bicho me ha caminado por la cabeza.", {"hambre": -2, "felicidad": -6}, 1.5),
    Evento("Mimos de su humano", "💖", "¡Me ha rascado detrás de la oreja! Purrrr.", {"felicidad": 8}, 2.0),
    Evento("Comida extra encontrada", "🎁", "¡Alguien me ha dejado un snack en el suelo!", {"hambre": 10, "felicidad": 3}, 1.5),
    Evento("Pesadilla", "😈", "He soñádo con una nevera vacía. Que miedo.", {"energia": -8, "felicidad": -10}, 1.5),
    Evento("Siesta improvisada", "☕", "Me he dormido 20 minutos. Estoy nuevo.", {"energia": 5, "felicidad": -2}, 2.0),
]


# ---------------------------------------------------------------------------
# Mensaje
# ---------------------------------------------------------------------------
@dataclass
class Mensaje:
    """Una linea del chatter de la mascota, que la interfaz pinta en pantalla."""

    texto: str
    icono: str
    tipo: str  # "sistema" | "accion" | "evento" | "estado" | "derrota"
    turno: int = 0

    @classmethod
    def crear(cls, texto: str, icono: str, tipo: str, turno: int = 0) -> Mensaje:
        return cls(texto=texto, icono=icono, tipo=tipo, turno=turno)


# ---------------------------------------------------------------------------
# Mascota
# ---------------------------------------------------------------------------
@dataclass
class Mascota:
    """La criatura en si: un nombre, un emoji y tres barras de estadisticas.

    Aqui NO hay reglas de partida (no sabe cuando se escapa ni cuando acaba
    un turno); solo sabe como se siente y que dice al respecto.
    """

    nombre: str = "Mochi"
    turno: int = 0
    viva: bool = True
    estadisticas: Estadisticas = field(default_factory=Estadisticas)

    def reaccionar_accion(self, accion: Accion) -> str:
        """Frase corta que dice justo despues de que le hagan la accion."""
        return random.choice(MENSAJES_ACCION[accion.value])

    def emoji(self, umbral_bajo: int = 30, umbral_alto: int = 70) -> str:
        """El emoji se decide por prioridad: primero si esta muerta, luego
        por como estan las barras, y al final el estado normal."""
        if not self.viva:
            return "💀"
        estado = self.estadisticas.estado_general(umbral_bajo, umbral_alto)
        return EMOJI_ESTADO[estado]

    def saludo(self, umbral_bajo: int = 30, umbral_alto: int = 70) -> str:
        """Lo que dice espontaneamente al terminar cada turno."""
        estado = self.estadisticas.estado_general(umbral_bajo, umbral_alto)
        return random.choice(SALUDOS[estado])


# ---------------------------------------------------------------------------
# Textos del juego (separados para no ensuciar las clases)
# ---------------------------------------------------------------------------
MENSAJES_ACCION = {
    "alimentar": [
        "🍎 ¡Ñam! Eso estaba riquísimo.",
        "🍎 Me he comido hasta la salsa. ¡Buenísimo!",
        "🍎 Gracias por la comida, estaba enloqueciendo.",
    ],
    "jugar": [
        "🎾 ¡Vamos, otra vez, otra vez!",
        "🎾 Me encanta perseguir la pelota por el salón.",
        "🎾 Me he cansado pero me ha sido divertido.",
    ],
    "dormir": [
        "😴 Una siestita y como nuevo.",
        "💤 Zzz... Zzz... no me despiertes.",
        "😴 Me he echado la siesta en el sofá, estaba calentito.",
    ],
}

SALUDOS = {
    "feliz": [
        "🥳 ¡Estoy de diez! ¡Vamos a celebrar!",
        "🥳 Me encanta la vida contigo.",
        "🥳 Todo va perfecto, sigamos así.",
    ],
    "normal": [
        "🙂 Aquí ando, sin más.",
        "😺 Esto de vivir es bien chulo.",
        "😺 Me va bien, ¿y a ti?",
    ],
    "hambrienta": [
        "😋 ¡Tengo un hambre que no es normal!",
        "🍽 ¿Se cocina algo o qué?",
        "🐟 ¿Tienes algo de comer a mano?",
    ],
    "cansada": [
        "😴 Estoy cansadísimo... necesito dormir ya.",
        "💤 Me pesan los ojitos.",
        "😪 Un café y algo más, por favor.",
    ],
    "triste": [
        "😢 Me siento solito/a aquí en mi esquinito.",
        "🥺 No me hasaties mucho hoy, ¿verdad?",
        "💔 Algo me pesa en el corazoncito.",
    ],
    "enferma": [
        "🤢 Me siento fatal, creo que me estoy poniendo mala.",
        "😵 No me siento bien de nada, todo duele.",
        "🚑 Esto no es normal, necesito un mimo.",
    ],
}

EMOJI_ESTADO = {
    "feliz": "🥳",
    "normal": "😺",
    "hambrienta": "😋",
    "cansada": "😴",
    "triste": "😢",
    "enferma": "🤢",
}

MENSAJES_DERROTA = {
    "hambre": "Se ha escapado a buscar comida por la casa... y no ha vuelto. 🍽",
    "energia": "Se ha escapado a dormir la sieta al sofá y se ha instalado. 💤",
    "felicidad": "Se ha aburrido tanto que se ha ido a buscar Diversión contigo. 💔",
}
