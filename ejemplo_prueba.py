"""Modulo de ejemplo: promedios, notas, informes y turnos.

Sirve para demostrar las reglas del AGENTS.md del workspace. No forma parte
de `mascota/`, `wordle/` ni `proyecto/`, asi que no usa su `game/` ni su
`config.py`. Aqui los numeros ajustables viven en `Config`, que hace el
mismo papel que `config.py` en los otros proyectos.

Que demuestra cada parte:

- `calcular_promedio`: tipos en la firma, `Sequence` en vez de `list`,
  generador en vez de bucle que acumula, salida temprana, f-strings,
  comparaciones con `is`, excepciones concretas con mensaje util.
- `Config` y `DEFAULT_CONFIG`: la unica sede de los numeros ajustables, en
  `SCREAMING_SNAKE_CASE` y en un dataclass sin una sola regla de juego.
- `Nota` y `crear_nota`: `T | None`, `field(default_factory=...)` en vez de
  una coleccion por defecto, y una funcion de fabrica con la validacion en
  lugar de un `__init__` con logica.
- `Informe`: composicion en vez de herencia, un unico sitio que decide el
  peso de una nota, y `logger.debug` en vez de imprimir.
- `escribir_resumen`: `with` para todo recurso.
- `Partida` y `crear_partida`: maquina de turnos con victoria, derrota y la
  prohibicion de jugar despues de terminar, con el resultado decidido en un
  solo sitio.
- `promedio_ponderado` no esta optimizado a proposito: la calidad 17 pide
  medir antes de optimizar y aqui no hay nada que medir.

Lo que este modulo no demuestra, y por que:

- Secretos (calidad 15): el ejemplo no maneja credenciales, asi que no hay
  variable de entorno que leer ni clave que registrar. Lo comprobable, que
  aqui no se imprime ni se registra nada fuera del `logger`, lo vigilan los
  tests de guarda.
- Las reglas de comunicacion, de dependencias y de seguridad del entorno
  (no instalar sin preguntar, no tocar la red, no hacer commits) rigen mi
  forma de trabajar, no el codigo: se demuestran en la conversacion.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class PartidaTerminada(RuntimeError):
    """Se lanza al intentar gastar un turno en una partida ya terminada.

    Existe para que el llamante distinga "no puedes seguir" de un fallo
    cualquiera: es un error de estado, no un dato malo.
    """


class Resultado(Enum):
    """Como esta una partida: todavia en juego, ganada o perdida."""

    EN_CURSO = "en curso"
    VICTORIA = "victoria"
    DERROTA = "derrota"


@dataclass(frozen=True)
class Config:
    """Numeros ajustables del ejemplo, sin una sola regla de juego.

    Todos los numeros que se pueden cambiar sin tocar la logica viven aqui.
    Es el mismo papel que `config.py` cumple en `mascota/`, `wordle/` y
    `proyecto/`.

    Args:
        turnos_maximos: Intentos disponibles antes de que la partida cuente
            como derrota.
        peso_por_defecto: Peso que recibe una nota que no indica el suyo.
    """

    turnos_maximos: int = 6
    peso_por_defecto: float = 1.0


DEFAULT_CONFIG = Config()


def _es_numero(valor: object) -> bool:
    """Indica si `valor` sirve para entrar en una media.

    `bool` queda fuera a proposito: en Python `True` es subclase de `int`,
    asi que sin este filtro `calcular_promedio([True])` devolveria 1.0 en
    lugar de avisar de que le han pasado un booleano.

    Args:
        valor: Cualquier objeto. La funcion no lanza excepciones.

    Returns:
        `True` si `valor` es un `int` o un `float` que no sea `bool`.
    """
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def calcular_promedio(numeros: Sequence[float]) -> float:
    """Devuelve la media aritmetica de los numeros recibidos.

    Se anota `Sequence[float]` y no `list[float]` porque la funcion solo
    necesita recorrer los valores una vez: admite listas, tuplas y
    cualquier otra secuencia con el mismo resultado.

    Args:
        numeros: Valores numericos cuya media se quiere calcular.

    Returns:
        La suma de los valores dividida entre la cantidad de valores.

    Raises:
        ValueError: Si `numeros` esta vacia, porque no hay nada que promediar.
        TypeError: Si algun valor no es numerico. El mensaje dice el indice
            del elemento que fallo, que es lo que hace util el error.

    Ejemplo:
        >>> calcular_promedio([2.0, 4.0])
        3.0
        >>> calcular_promedio(["dos"])
        Traceback (most recent call last):
            ...
        TypeError: el elemento del indice 0 no es un numero: 'dos'
    """
    if not numeros:
        raise ValueError("no se puede calcular el promedio de una lista vacia")

    indice_invalido = next(
        (indice for indice, valor in enumerate(numeros) if not _es_numero(valor)),
        None,
    )
    if indice_invalido is not None:
        raise TypeError(
            f"el elemento del indice {indice_invalido} no es un numero: "
            f"{numeros[indice_invalido]!r}"
        )

    # `sum` recorre en C y aqui no hay nada que medir: son cinco elementos,
    # no una partida entera. La calidad 17 pide optimizar cuando el perfil
    # lo justifique, y este perfil no lo justifica.
    return sum(numeros) / len(numeros)


@dataclass(frozen=True)
class Nota:
    """Una medicion con su etiqueta, su valor y un peso opcional.

    Es `frozen` a proposito: una nota ya medida no se reescribe, y si el
    valor cambia se crea otra. Asi ningun informe puede quedar mostrando
    numeros que ya no son los que se midieron.

    Args:
        etiqueta: Nombre corto de lo medido.
        valor: La magnitud medida.
        peso: Cuanto cuenta esta nota frente a las demas. `None` significa
            "que lo decida el informe", que no es lo mismo que un peso de 1.0.
        muestras: Valores originales, si los hay. Usa `default_factory`
            porque una lista vacia escrita como valor por defecto la
            compartirian todas las notas, y el efecto aparece dos turnos
            despues del error que lo provoco.
    """

    etiqueta: str
    valor: float
    peso: float | None = None
    muestras: list[float] = field(default_factory=list)


def crear_nota(
    etiqueta: str,
    valor: float,
    peso: float | None = None,
    muestras: Sequence[float] | None = None,
) -> Nota:
    """Crea una nota validando los datos y decidiendo los valores ausentes.

    La validacion vive aqui y no en `Nota.__init__` a proposito: el dataclass
    solo guarda, y la fabrica es la que devuelve un error con un mensaje
    util. `muestras=None` se convierte en lista ya aqui, para que `Nota` no
    tenga que interpretar lo que significa "sin muestras".

    Args:
        etiqueta: Nombre corto de lo medido. No puede quedar vacio.
        valor: La magnitud medida. Tiene que ser un numero.
        peso: Peso explicito. `None` deja que lo resuelva el informe.
        muestras: Valores originales. `None` equivale a lista vacia.

    Returns:
        Una `Nota` lista para entrar en un `Informe`.

    Raises:
        ValueError: Si `etiqueta` queda vacia, si `valor` no es un numero o
            si `peso` no es un numero mayor que cero.

    Ejemplo:
        >>> crear_nota("pulso", 70.0, peso=2.0).peso
        2.0
    """
    if not isinstance(etiqueta, str) or not etiqueta.strip():
        raise ValueError("la etiqueta de una nota no puede estar vacia")
    if not _es_numero(valor):
        raise ValueError(f"el valor de '{etiqueta}' no es un numero: {valor!r}")
    if peso is not None and (not _es_numero(peso) or peso <= 0):
        raise ValueError(
            f"el peso de '{etiqueta}' debe ser un numero mayor que cero: {peso!r}"
        )

    return Nota(
        etiqueta=etiqueta,
        valor=float(valor),
        peso=float(peso) if peso is not None else None,
        muestras=list(muestras) if muestras is not None else [],
    )


@dataclass(frozen=True)
class Informe:
    """Conjunto de notas del que salen los promedios y el resumen.

    Compone las notas en una tupla en vez de heredar de ellas: un informe
    *tiene* notas, no *es* una nota. Con la herencia, `promedio_ponderado`
    tendria que funcionar con un solo `valor`, que no es lo que hace.

    Args:
        notas: Mediciones del informe. Van en tupla para que despues de
            construido no se puedan anadir ni quitar.
        config: Configuracion de la que sale el peso de las notas que no
            indican el suyo.
    """

    notas: tuple[Nota, ...]
    config: Config = DEFAULT_CONFIG

    @property
    def cantidad(self) -> int:
        """Devuelve cuantas notas tiene el informe.

        Returns:
            El numero de notas de la tupla.
        """
        return len(self.notas)

    def peso_de(self, nota: Nota) -> float:
        """Resuelve el peso con el que una nota cuenta dentro del informe.

        Es el unico sitio que decide ese peso: si el promedio y el resumen
        escrito lo resolvieran por su cuenta, podrian dar numeros distintos
        con las mismas notas.

        Args:
            nota: Nota del informe cuyo peso se quiere resolver.

        Returns:
            El peso explicito de la nota o `config.peso_por_defecto` cuando la
            nota no indica ninguno.
        """
        return self.config.peso_por_defecto if nota.peso is None else nota.peso

    def promedio_ponderado(self) -> float:
        """Calcula la media de los valores pesando cada uno por su peso.

        Returns:
            La media ponderada de los valores, con los pesos que resuelve
            `peso_de`.

        Raises:
            ValueError: Si el informe no tiene notas, porque entonces no hay
                nada que promediar.

        Ejemplo:
            >>> Informe((crear_nota("a", 10.0),)).promedio_ponderado()
            10.0
        """
        if not self.notas:
            raise ValueError("no se puede calcular el promedio de un informe vacio")

        pesos = [self.peso_de(nota) for nota in self.notas]
        sin_peso = sum(1 for nota in self.notas if nota.peso is None)
        # Aqui se informa y no se imprime: la logica no tiene pantalla, y el
        # detalle de cuantas notas entraron con el peso por defecto sirve para
        # entender el numero de salida (calidad 13 y excepcion 2).
        logger.debug(
            "promedio de %d notas, %d con el peso por defecto %s",
            self.cantidad,
            sin_peso,
            self.config.peso_por_defecto,
        )
        total = sum(
            nota.valor * peso
            for nota, peso in zip(self.notas, pesos, strict=True)
        )
        return total / sum(pesos)


def escribir_resumen(informe: Informe, ruta: Path) -> None:
    """Escribe el resumen del informe en `ruta`, una linea por nota.

    El `with` no es decoracion: sin el, una escritura que falle a mitad
    deja el fichero abierto y el resumen a medias.

    Args:
        informe: Informe cuyo resumen se quiere guardar.
        ruta: Fichero de destino. Se sobrescribe si ya existia.
    """
    lineas = [
        f"{nota.etiqueta}: {nota.valor} (peso {informe.peso_de(nota)})"
        for nota in informe.notas
    ]
    with ruta.open("w", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas) + "\n")


@dataclass
class Partida:
    """Turnos que quedan y como ha terminado la partida.

    Es mutable a proposito: cada jugada mueve el contador. El resultado se
    decide solo en `jugar`, para que exista un unico sitio que dice si la
    partida sigue, que es la forma que tiene este workspace de no repetir
    una regla en dos archivos.

    Args:
        turnos_maximos: Intentos disponibles. Sale de `Config`, no de un
            numero escrito aqui.
        turno: Turno en el que esta la partida, empezando en 1.
        resultado: Como termino la partida. `None` mientras sigue en curso.
    """

    turnos_maximos: int
    turno: int = 1
    resultado: Resultado | None = None

    @property
    def en_curso(self) -> bool:
        """Indica si la partida todavia admite jugadas.

        Returns:
            `True` si la partida todavia no ha terminado.
        """
        return self.resultado is None

    def jugar(self, acierto: bool) -> Resultado:
        """Gasta un turno y devuelve como queda la partida.

        Args:
            acierto: Si el intento de este turno cumple el objetivo.

        Returns:
            `Resultado.EN_CURSO` si quedan turnos, `Resultado.VICTORIA` al
            acertar y `Resultado.DERROTA` al agotarlos sin acertar.

        Raises:
            PartidaTerminada: Si la partida ya termino. Comprobarlo aqui, y
                no en el llamante, deja imposible jugar despues del final.

        Ejemplo:
            >>> crear_partida(Config(turnos_maximos=1)).jugar(True) is Resultado.VICTORIA
            True
        """
        terminado = self.resultado
        if terminado is not None:
            raise PartidaTerminada(
                f"la partida ya termino como {terminado.value}, en el turno {self.turno}"
            )

        self.turno += 1

        # El resultado se decide aqui y en ningun otro sitio, y en este orden:
        # la victoria manda sobre la derrota, porque acertar en el ultimo
        # turno es ganar y no empatar.
        if acierto:
            self.resultado = Resultado.VICTORIA
        elif self.turno > self.turnos_maximos:
            self.resultado = Resultado.DERROTA

        if self.resultado is not None:
            logger.debug(
                "partida terminada en el turno %d: %s",
                self.turno,
                self.resultado.value,
            )

        if self.resultado is None:
            return Resultado.EN_CURSO
        return self.resultado


def crear_partida(config: Config = DEFAULT_CONFIG) -> Partida:
    """Crea una partida con los turnos que fija la configuracion.

    Fabrica y no `Partida(...)` en el llamante, para que el numero de
    turnos tenga una sola fuente y nadie lo escriba a mano.

    Args:
        config: Configuracion de la que sale `turnos_maximos`.

    Returns:
        Una `Partida` en curso con los turnos de `config`.
    """
    return Partida(turnos_maximos=config.turnos_maximos)