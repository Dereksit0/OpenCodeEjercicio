"""Pruebas del modulo de ejemplo, con `assert` planos y sin pytest.

    python tests/test_ejemplo_prueba.py     # runner propio, sin dependencias
    pytest tests                            # el mismo archivo, con pytest

Se mantiene el formato del workspace (funciones `test_*` y un `main()` que
las recoge) aunque pytest ya este instalado: migrar las tres suites
existentes es un trabajo consciente, no automatico (excepcion 3 de
[AGREGADO] Convenciones de calidad). El archivo vive en `tests/` porque
pytest ya lo permite (regla 2 de [AGREGADO] Pruebas).

Los tests son deterministas: aqui no se baraja nada, asi que no hace falta
`random.seed`. Si algun dia hiciera falta, la semilla va al principio de
`main()` (regla 7 de [AGREGADO] Pruebas).

Ademas del comportamiento, hay tests de guarda que miran la forma del
codigo del modulo (imports salvajes, `print`, `== None`, docstrings,
parametros por defecto) y la forma de los `game/` de los otros proyectos.
Esos si que hacen falta: son reglas que un test de comportamiento no
puede violar sin que se note.
"""

from __future__ import annotations

import contextlib
import inspect
import io
import logging
import re
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import cast

# El test vive en tests/, y el modulo que prueba en la raiz del workspace.
# Sin esto, `import ejemplo_prueba` falla porque el interprete solo anade
# la carpeta del propio archivo al path, no la carpeta del modulo.
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import ejemplo_prueba
from ejemplo_prueba import (
    DEFAULT_CONFIG,
    Config,
    Informe,
    Nota,
    Partida,
    PartidaTerminada,
    Resultado,
    calcular_promedio,
    crear_nota,
    crear_partida,
    escribir_resumen,
)

# La consola de Windows usa cp1252 y revienta con los simbolos del test.
# Se accede a reconfigure con getattr porque solo existe en TextIOWrapper: en
# un stdout redirection (por ejemplo, cuando pytest captura la salida) no esta,
# y el AttributeError seria mas dificil de leer que este comentario.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

NOMBRE_MODULO = ejemplo_prueba.__name__
CARPETAS_CON_JUEGO = ("mascota", "wordle", "proyecto")
COLECCIONES_MUTABLES = (list, dict, set, bytearray)


class _ColectorDeLogs(logging.Handler):
    """Guarda los registros que emite el modulo para poder revisarlos."""

    def __init__(self) -> None:
        """Crea el colector con la lista de registros vacia.

        Returns:
            Nada: un handler no devuelve nada.
        """
        super().__init__()
        self.registros: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Anota un registro para que el test pueda revisarlo.

        Args:
            record: Registro emitido por el modulo bajo prueba.
        """
        self.registros.append(record)


def _fuente_del_ejemplo() -> str:
    """Devuelve el codigo fuente del modulo de ejemplo.

    Returns:
        El texto de `ejemplo_prueba.py`, que es lo que miran los tests de
        guarda: aqui importa la forma del codigo, no lo que hace.
    """
    return Path(cast(str, ejemplo_prueba.__file__)).read_text(encoding="utf-8")


def _miembros_del_ejemplo(contenedor: object) -> Iterator[tuple[str, object]]:
    """Itera por lo que el propio modulo de ejemplo define, en orden.

    Se filtran tres cosas: lo que empieza por `_` (privado), lo importado de
    otro modulo (comparando `__module__`) y los miembros heredados. Las
    `property` se desenrollan a su `fget` para poder exigirle docstring al
    metodo que las calcula.

    Args:
        contenedor: Modulo o clase del ejemplo que se quiere inspeccionar.

    Yields:
        Pares `(nombre, objeto)` de funciones, clases y metodos publicos
        definidos por el modulo de ejemplo.
    """
    for nombre, miembro in inspect.getmembers(contenedor):
        if nombre.startswith("_"):
            continue
        candidato = miembro.fget if isinstance(miembro, property) else miembro
        if getattr(candidato, "__module__", None) != NOMBRE_MODULO:
            continue
        if inspect.isfunction(candidato) or inspect.isclass(candidato):
            yield nombre, candidato


def _modulos_de_juego() -> list[Path]:
    """Devuelve los archivos de `game/` de los tres proyectos del workspace.

    Returns:
        Rutas ordenadas, para que un fallo apunte siempre al mismo archivo y
        la suite sea determinista tambien al leer.
    """
    return sorted(
        modulo
        for carpeta in CARPETAS_CON_JUEGO
        for modulo in (RAIZ / carpeta / "game").glob("*.py")
    )


# --- Promedios: tipos, generador, salida temprana y errores utiles ---------


def test_el_promedio_de_una_lista_normal() -> None:
    # El caso base: dos elementos, division exacta.
    assert calcular_promedio([2.0, 4.0]) == 3.0
    print("OK  el promedio de una lista normal es correcto")


def test_el_promedio_de_un_solo_elemento() -> None:
    # Un solo elemento: el promedio es ese mismo elemento. Es el limite
    # inferior del tamaño de la lista.
    assert calcular_promedio([7.5]) == 7.5
    print("OK  el promedio de un solo elemento es ese elemento")


def test_el_promedio_de_los_limites() -> None:
    # Los tres limites de rango que pide la regla 5 de [AGREGADO] Pruebas,
    # translate al dominio de esta funcion: negativo, cero y un numero muy
    # grande. Un promedio puede ser negativo; la funcion no debe recortarlo.
    assert calcular_promedio([-2.0, -4.0]) == -3.0
    assert calcular_promedio([0.0, 0.0]) == 0.0
    assert calcular_promedio([1e6, 3e6]) == 2e6
    print("OK  el promedio respeta negativos, cero y magnitudes grandes")


def test_el_promedio_admite_una_tupla() -> None:
    # Se anota Sequence, no list, porque el calculo solo necesita iterar.
    # Si la anotacion dijera list, esto seria un fallo de tipos.
    assert calcular_promedio((1, 2, 3)) == 2.0
    print("OK  el promedio funciona con cualquier secuencia de numeros")


def test_una_lista_vacia_es_error_explicito() -> None:
    # Una lista vacia no tiene promedio. Dividir por cero daria ZeroDivisionError
    # sin contexto, asi que la regla 6 de [AGREGADO] Convenciones de calidad
    # exige una excepcion concreta y un mensaje util.
    try:
        calcular_promedio([])
    except ValueError as error:
        assert "vacia" in str(error).lower() or "vacía" in str(error).lower()
        print("OK  una lista vacia lanza ValueError con mensaje legible")
    else:
        raise AssertionError("una lista vacia deberia lanzar ValueError")


def test_una_lista_con_valores_no_numericos_dice_el_indice() -> None:
    # La anotacion dice float, pero en Python nada impide pasar un str en
    # tiempo de ejecucion. Un TypeError claro es mejor que un AttributeError
    # raro salir de dentro de sum(), y el indice es lo que hace el mensaje
    # util cuando la lista tiene veinte elementos.
    try:
        calcular_promedio([1.0, "dos"])  # type: ignore[list-item]
    except TypeError as error:
        assert "1" in str(error), f"el mensaje deberia señalar el indice: {error}"
        print("OK  un valor no numerico lanza TypeError diciendo el indice")
    else:
        raise AssertionError("un valor no numerico deberia lanzar TypeError")


def test_un_booleano_no_cuenta_como_numero() -> None:
    # Regresion (regla 6 de [AGREGADO] Pruebas): en Python `True` es
    # subclase de `int`, asi que sin el filtro de `_es_numero` este
    # promedio devolveria 0.5 en vez de avisar de que le han pasado un
    # booleano. El fallo era silencioso y volvia a aparecer.
    try:
        calcular_promedio([True, False])
    except TypeError:
        print("OK  un booleano no se cuela como numero en el promedio")
    else:
        raise AssertionError("un booleano deberia lanzar TypeError")


# --- Notas e informes: fabrica, nulo moderno, composicion, logger ---------


def test_una_nota_sin_peso_conserva_el_nulo_y_el_informe_lo_resuelve() -> None:
    # `peso: float | None` no es un adorno: `None` significa "el informe
    # decide", que es distinto de un peso de 1.0. Si el modulo sustituyera
    # el `None` por 1.0 al crear la nota, este test veria 1.0 en vez de `None`.
    nota = crear_nota("pulso", 70.0)

    assert nota.peso is None
    assert Informe(notas=(nota,)).peso_de(nota) == DEFAULT_CONFIG.peso_por_defecto
    print("OK  la nota sin peso guarda None y el informe aplica el de la config")


def test_las_muestras_de_dos_notas_no_se_comparten() -> None:
    # Regresion de la regla 12 de [AGREGADO] Estilo: con `muestras: list = []`
    # como valor por defecto, todas las notas comparten la misma lista y
    # `muestras.append(...)` en una nota aparece en las demas. El fallo sale
    # dos turnos despues del que lo provoco, asi que la red de seguridad es
    # este test, no una mirada al codigo.
    primera = crear_nota("a", 1.0)
    segunda = crear_nota("b", 2.0)
    primera.muestras.append(9.0)

    assert primera.muestras == [9.0]
    assert segunda.muestras == []
    print("OK  las muestras de cada nota son suyas (default_factory)")


def test_crear_nota_rechaza_una_etiqueta_vacia() -> None:
    # Una etiqueta vacia deja el resumen escrito con una linea sin nombre, y
    # el error aparece en la lectura del fichero, no aqui (regla 6: el dato
    # invalido se rechaza con un motivo legible).
    try:
        crear_nota("   ", 1.0)
    except ValueError as error:
        assert "etiqueta" in str(error)
        print("OK  una etiqueta vacia se rechaza en la fabrica")
    else:
        raise AssertionError("una etiqueta vacia deberia lanzar ValueError")


def test_crear_nota_rechaza_un_peso_que_no_se_pueda_ponderar() -> None:
    # Peso cero daria una division por cero al promediar, y peso negativo
    # daria una media al reves. Los dos se paran en la fabrica.
    for peso, motivo in ((0.0, "cero"), (-1.0, "negativo")):
        try:
            crear_nota("a", 1.0, peso=peso)
        except ValueError as error:
            assert "peso" in str(error), f"el mensaje deberia hablar del peso: {error}"
        else:
            raise AssertionError(f"un peso {motivo} deberia lanzar ValueError")
    print("OK  la fabrica rechaza pesos cero y negativos")


def test_el_informe_compone_sus_notas_y_no_hereda_de_ellas() -> None:
    # Composicion antes que herencia (regla 11 de Convenciones). Si el
    # informe heredara de la nota, `promedio_ponderado` tendria que
    # funcionar con un solo `valor`, que no es lo que hace.
    assert is_dataclass(Informe)
    assert issubclass(Informe, Nota) is False
    assert [campo.name for campo in fields(Informe)] == ["notas", "config"]
    print("OK  el informe compone una tupla de notas y no hereda de ellas")


def test_el_promedio_ponderado_resuelve_cada_peso_una_sola_vez() -> None:
    # Una nota con peso explicito pesa 3, la otra usa el de la configuracion.
    # El promedio ponderado es (10*3 + 20*1) / 4 = 12.5. Si el peso por
    # defecto se aplicara dos veces o se ignorara alguno, el numero cambia.
    informe = Informe(
        notas=(crear_nota("a", 10.0, peso=3.0), crear_nota("b", 20.0)),
        config=Config(peso_por_defecto=1.0),
    )

    assert informe.cantidad == 2
    assert informe.promedio_ponderado() == 12.5
    print("OK  el promedio ponderado usa el peso de cada nota una sola vez")


def test_el_promedio_ponderado_registra_en_el_log_y_no_imprime() -> None:
    # Calidad 13 y excepcion 2: la logica no tiene pantalla, asi que informa
    # con `logger` y no con un `print`. El test ata las dos puntas: el
    # `print` se captura vacio y el `logger` recibe un registro.
    informe = Informe(notas=(crear_nota("a", 10.0), crear_nota("b", 20.0, peso=3.0)))
    colector = _ColectorDeLogs()
    nivel_previo = ejemplo_prueba.logger.level
    salida = io.StringIO()

    ejemplo_prueba.logger.addHandler(colector)
    ejemplo_prueba.logger.setLevel(logging.DEBUG)
    try:
        with contextlib.redirect_stdout(salida):
            promedio = informe.promedio_ponderado()
    finally:
        ejemplo_prueba.logger.removeHandler(colector)
        ejemplo_prueba.logger.setLevel(nivel_previo)

    assert promedio == 17.5
    assert salida.getvalue() == "", "la logica no debe escribir en la consola"
    assert any(registro.levelno == logging.DEBUG for registro in colector.registros)
    print("OK  el promedio ponderado informa por log y no imprime nada")


def test_el_promedio_ponderado_de_un_informe_vacio_es_error() -> None:
    # Sin notas no hay promedio. Es el mismo error que en `calcular_promedio`
    # pero con su propio mensaje: el llamante tiene que saber si fallo la
    # lista de numeros o el informe entero.
    try:
        Informe(notas=()).promedio_ponderado()
    except ValueError as error:
        assert "informe" in str(error)
        print("OK  un informe sin notas lanza ValueError con su mensaje")
    else:
        raise AssertionError("un informe vacio deberia lanzar ValueError")


# --- Partida: victoria, derrota y no seguir jugando ----------------------


def test_una_partida_nace_en_curso_sin_resultado() -> None:
    # El resultado empieza en `None` porque todavia no hay ninguno; el enum
    # `EN_CURSO` es lo que devuelve cada jugada mientras queden turnos.
    partida = crear_partida()

    assert partida.en_curso is True
    assert partida.resultado is None
    assert partida.turnos_maximos == DEFAULT_CONFIG.turnos_maximos
    print("OK  una partida nueva esta en curso y sin resultado")


def test_los_turnos_maximos_salen_de_la_config_y_no_de_un_numero_suelto() -> None:
    # `config.py` es la unica sede de numeros ajustables: el mismo concepto
    # vive aqui en `Config`. Si `crear_partida` escribiera el 6 dentro, este
    # test seguiria verde con otra configuracion, que es justo el fallo.
    partida = crear_partida(Config(turnos_maximos=2))

    assert partida.turnos_maximos == 2
    print("OK  los turnos maximos vienen de la configuracion, no del codigo")


def test_la_victoria_llega_en_el_ultimo_turno() -> None:
    # Victoria en el ultimo turno: es el caso que un `>` mal puesto
    # robaría, porque regalaria un turno extra. Con 2 turnos, acertar en la
    # segunda jugada gana y la partida se cierra.
    partida = crear_partida(Config(turnos_maximos=2))

    assert partida.jugar(False) is Resultado.EN_CURSO
    assert partida.jugar(True) is Resultado.VICTORIA
    print("OK  acertar en el ultimo turno da la victoria")


def test_la_derrota_ocurre_en_el_turno_en_que_se_agotan_los_turnos() -> None:
    # Derrota en el turno en el que ocurre: con 3 turnos, la cuarta jugada no
    # existe. El turno se queda en 4 para que se vea que la jugada que fallo
    # si se conto.
    partida = crear_partida(Config(turnos_maximos=3))

    for jugada in range(3):
        resultado = partida.jugar(False)
        esperado = Resultado.EN_CURSO if jugada < 2 else Resultado.DERROTA
        assert resultado is esperado

    assert partida.resultado is Resultado.DERROTA
    assert partida.turno == 4
    print("OK  la derrota llega en el turno que agota los intentos")


def test_cada_jugada_gasta_exactamente_un_turno() -> None:
    # El turno avanza de uno en uno. Un `+= 2` pasaria desapercibido hasta
    # que la partida terminara antes de tiempo.
    partida = crear_partida(Config(turnos_maximos=4))

    partida.jugar(False)
    assert partida.turno == 2
    partida.jugar(False)
    assert partida.turno == 3
    print("OK  cada jugada consume un solo turno")


def test_no_se_puede_jugar_despues_de_ganar() -> None:
    # Regla 5 de [AGREGADO] Pruebas: despues de terminar no se puede seguir
    # jugando. Se comprueba con el final feliz y no solo con la derrota.
    partida = crear_partida(Config(turnos_maximos=2))
    partida.jugar(True)

    try:
        partida.jugar(True)
    except PartidaTerminada as error:
        assert "victoria" in str(error)
        print("OK  no se puede jugar despues de ganar")
    else:
        raise AssertionError("una partida ganada deberia rechazar otra jugada")


def test_no_se_puede_jugar_despues_de_perder() -> None:
    # El otro final. Ademas el mensaje lleva el turno en el que termino, que
    # es lo que hace falta para entender un fallo de una partida guardada.
    partida = crear_partida(Config(turnos_maximos=1))
    partida.jugar(False)

    try:
        partida.jugar(False)
    except PartidaTerminada as error:
        assert "derrota" in str(error) and "turno 2" in str(error)
        print("OK  no se puede jugar despues de perder")
    else:
        raise AssertionError("una partida perdida deberia rechazar otra jugada")


# --- Ficheros: `with` para todo recurso -----------------------------------


def test_el_resumen_se_escribe_y_se_vuelve_a_leer() -> None:
    # `with` para todo recurso (calidad 5): el `TemporaryDirectory` de este
    # test y el fichero que escribe el modulo se cierran solos. El peso que
    # sale escrito es el mismo que usa el promedio, porque lo decide
    # `Informe.peso_de` y no cada consumidor por su cuenta.
    informe = Informe(notas=(crear_nota("pulso", 70.0), crear_nota("sangre", 12.0, peso=2.0)))

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "resumen.txt"
        escribir_resumen(informe, ruta)
        with ruta.open(encoding="utf-8") as archivo:
            lineas = archivo.read().splitlines()

    assert lineas == ["pulso: 70.0 (peso 1.0)", "sangre: 12.0 (peso 2.0)"]
    print("OK  el resumen se escribe con `with` y se lee integro")


# --- Guardas de forma del propio modulo -----------------------------------


def test_el_modulo_no_imprime_ni_para_en_el_primer_error() -> None:
    # Reglas 7 y 13: la logica devuelve informacion y no escribe en la
    # consola, y para depurar se usa `logger`. Una linea suelta de
    # `print` se cuela en un parche y nadie la ve hasta que rompe un test.
    fuente = _fuente_del_ejemplo()

    assert "print(" not in fuente
    assert "breakpoint(" not in fuente
    assert "pdb" not in fuente
    print("OK  el modulo no imprime ni depura con print o breakpoint")


def test_el_modulo_no_trae_imports_salvajes_ni_excepciones_a_pelo() -> None:
    # Regla 4 (nada de `from modulo import *`) y regla 6 de Estilo
    # (capturar excepciones concretas, nunca a pelo). Un `except:` se come
    # tambien los Ctrl+C y los errores de programacion.
    fuente = _fuente_del_ejemplo()

    assert "import *" not in fuente
    assert "__import__(" not in fuente
    assert not re.search(r"except\s*:", fuente)
    print("OK  el modulo no usa imports salvajes ni except a pelo")


def test_el_modulo_compara_con_is_y_no_con_igual() -> None:
    # Regla 6 de Convenciones: `is` para `None`, `True` y `False`. Con `==`
    # un objeto con `__eq__` raro (un `numpy.nan` de la partida, un `Decimal`)
    # devuelve False y el codigo sigue por un camino imposible.
    fuente = _fuente_del_ejemplo()
    prohibidos = re.findall(r"==\s*(?:None|True|False)|!=\s*(?:None|True|False)", fuente)

    assert not prohibidos, f"comparaciones con = en lugar de is: {prohibidos}"
    print("OK  el modulo compara None, True y False con `is`")


def test_el_modulo_no_deja_colecciones_mutables_por_defecto() -> None:
    # Regla 12 de Estilo. En una funcion, un `= []` se comparte entre todas
    # las llamadas; en un dataclass, `field(default_factory=list)` es lo que
    # evita que dos notas compartan la misma lista.
    for nombre, miembro in _miembros_del_ejemplo(ejemplo_prueba):
        if inspect.isclass(miembro) or not callable(miembro):
            continue
        for nombre_parametro, parametro in inspect.signature(miembro).parameters.items():
            assert not isinstance(parametro.default, COLECCIONES_MUTABLES), (
                f"{nombre}.{nombre_parametro} tiene una coleccion mutable por defecto"
            )
    print("OK  ninguna funcion del modulo deja colecciones mutables por defecto")


def test_ninguna_funcion_publica_supera_los_cinco_parametros() -> None:
    # Regla 9 de Convenciones: 5 parametros o menos; si hacen falta mas, un
    # dataclass que los agrupe. `crear_nota` esta justo en el limite, que es
    # donde conviene estar para notarlo.
    for nombre, miembro in _miembros_del_ejemplo(ejemplo_prueba):
        if inspect.isclass(miembro) or not callable(miembro):
            continue
        total = len(inspect.signature(miembro).parameters)
        assert total <= 5, f"{nombre} declara {total} parametros y el tope son 5"
    print("OK  ninguna funcion publica del modulo pasa de cinco parametros")


def test_toda_funcion_clase_y_metodo_publico_tiene_docstring_google() -> None:
    # Regla 2 de Convenciones: docstring en formato Google con `Args:`,
    # `Returns:` y `Raises:` segun corresponda. El test comprueba lo que se
    # puede comprobar de forma objetiva: si algo recibe argumentos, los
    # documenta; si algo lanza, documenta las excepciones.
    for nombre, miembro in _miembros_del_ejemplo(ejemplo_prueba):
        doc = (getattr(miembro, "__doc__", None) or "").strip()
        assert doc, f"{nombre} no tiene docstring"
        if inspect.isclass(miembro) or not callable(miembro):
            continue
        firma = inspect.signature(miembro)
        if firma.parameters:
            assert "Args:" in doc, f"{nombre} no documenta sus argumentos"
        retorno = firma.return_annotation
        if retorno is not inspect.Signature.empty and str(retorno) != "None":
            assert "Returns:" in doc, f"{nombre} no documenta su retorno"
        if "raise " in inspect.getsource(miembro):
            assert "Raises:" in doc, f"{nombre} lanza excepciones sin documentarlas"
    print("OK  todo lo publico del modulo tiene docstring en formato Google")


def test_el_codigo_del_modulo_va_sin_tildes_ni_enyes() -> None:
    # Reglas 3 y 4 de Estilo: docstrings sin tildes ni enye, y simbolos sin
    # tildes. Las tildes quedan para el texto que ve el usuario en pantalla,
    # no para lo que teclea Python.
    fuente = _fuente_del_ejemplo()
    prohibidos = sorted({caracter for caracter in fuente if caracter in "áéíóúüñÁÉÍÓÚÑ¿¡"})

    assert not prohibidos, f"el modulo usa caracteres acentuados: {prohibidos}"
    print("OK  el modulo esta escrito sin tildes ni enyes")


# --- Guardas de estructura del workspace ----------------------------------


def test_los_modulos_de_game_no_importan_streamlit_ni_app() -> None:
    # Regla estructural: `game/` nunca importa streamlit y `app.py` solo
    # pinta. Es la regla que permite testear la partida sin levantar la
    # interfaz. Se buscan imports de verdad y no la palabra "streamlit",
    # porque esos modulos la mencionan en sus docstrings para explicar
    # justo que no dependen de ella.
    patron_streamlit = re.compile(r"^\s*(?:from\s+streamlit|import\s+streamlit)", re.M)
    patron_app = re.compile(r"^\s*(?:from\s+app\b|import\s+app\b)", re.M)

    modulos = _modulos_de_juego()
    assert modulos, "no se encontro ningun modulo en game/"

    for ruta in modulos:
        fuente = ruta.read_text(encoding="utf-8")
        assert not patron_streamlit.search(fuente), f"{ruta} importa streamlit"
        assert not patron_app.search(fuente), f"{ruta} importa app.py"
    print("OK  ningun modulo de game/ importa streamlit ni app.py")


def test_los_modulos_de_game_tienen_future_annotations_y_sin_print() -> None:
    # Regla 10 de Estilo (`from __future__ import annotations` en cada modulo
    # nuevo de `game/`) y regla 7 (esa capa no imprime). Se excluyen los
    # `__init__.py`: solo reexportan nombres, no declaran logica.
    modulos = [ruta for ruta in _modulos_de_juego() if ruta.name != "__init__.py"]
    assert modulos, "no se encontro ningun modulo de logica en game/"

    for ruta in modulos:
        fuente = ruta.read_text(encoding="utf-8")
        assert "from __future__ import annotations" in fuente, (
            f"{ruta} no trae `from __future__ import annotations`"
        )
        assert "print(" not in fuente, f"{ruta} imprime desde game/"
    print("OK  los modulos de logica traen future annotations y no imprimen")


def test_esta_suite_no_se_salta_ni_se_desactiva() -> None:
    # Regla 8 de [AGREGADO] Pruebas: prohibido saltar, desactivar o borrar
    # pruebas para que la suite pase. Los patrones se arman con
    # concatenacion para que este test no se detecte a si mismo al leer su
    # propio codigo.
    fuente = Path(__file__).read_text(encoding="utf-8")
    patrones_prohibidos = ("pytest." + "skip", "pytest." + "xfail", "unittest." + "skip")

    for patron in patrones_prohibidos:
        assert patron not in fuente, f"la suite usa {patron}"
    print("OK  la suite no salta ni desactiva ninguna prueba")


def main() -> None:
    """Corre todas las pruebas del archivo y dice cuantas han pasado.

    Returns:
        Nada: si una prueba falla, la excepcion sube y el proceso sale con
        codigo distinto de cero, que es lo que CI necesita para enterarse.
    """
    tests = [
        valor
        for nombre, valor in sorted(globals().items())
        if nombre.startswith("test_")
    ]
    for test in tests:
        test()

    print(f"\n{len(tests)} tests correctos.")


if __name__ == "__main__":
    main()