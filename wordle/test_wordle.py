"""Tests del Wordle, sin Streamlit y sin pytest: solo `assert`.

    python test_wordle.py

Lo importante de este archivo es el bloque de letras repetidas: es el
error clasico al Implementar el coloreado, asi que cada caso esta
acompanado del comentario que explica por que sale ese color.
"""

import random
import sys

from config import DEFAULT_CONFIG
from datos.palabras import PALABRAS
from game import BancoPalabras, EstadoLetra, EvaluadorPalabras, JuegoWordle

# La consola de Windows usa cp1252 y revienta con los simbolos del juego.
sys.stdout.reconfigure(encoding="utf-8")


def codigos(intento: str, secreta: str) -> list[str]:
    """Atajo para los tests: evalua y devuelve los estados en texto."""
    return [estado.valor() for estado in EvaluadorPalabras.evaluar(intento, secreta)]


def test_el_banco_cumple_sus_propias_reglas() -> None:
    # El dato se escribe en mayusculas...
    for palabra in PALABRAS:
        assert len(palabra) == 5, palabra
        assert palabra.isupper() and palabra.isalpha(), palabra

    # ...pero el banco trabaja en minusculas, que es lo que produce
    # normalizar() al validar un intento.
    banco = BancoPalabras.construir(5)
    assert banco.total() >= 200, f"el banco es demasiado pequeño: {banco.total()}"
    assert len(banco.validas) == banco.total(), "hay palabras repetidas en el banco"
    for palabra in banco.palabras:
        assert palabra == palabra.lower(), palabra

    # Y una palabra en minusculas tiene que valer en el banco.
    assert banco.es_valida(banco.palabras[0])
    print(f"OK  el banco tiene {banco.total()} palabras de 5 letras, sin repetir")


def test_los_tres_colores_basicos() -> None:
    """Un solo intento que produce los tres colores a la vez.
    Secreta ALGAS, intento PESCA:
      P gris · E gris · S amarillo · C gris · A amarillo
    """
    assert codigos("PESCA", "ALGAS") == [
        "gris",  # la P no esta en ALGAS
        "gris",  # la E no esta en ALGAS
        "amarillo",  # la S esta en ALGAS (posicion 3)
        "gris",  # la C no esta en ALGAS
        "amarillo",  # la A esta en ALGAS (posiciones 0 y 3)
    ]
    # y el acierto completo sale todo verde
    assert codigos("ALGAS", "ALGAS") == ["verde"] * 5
    print("OK  los tres colores se calculan bien en un mismo intento")


def test_letras_repetidas_el_caso_clasico() -> None:
    """El caso que rompe la implementacion de una sola pasada.

    Secreta  ALGAS  (una A de sobra y un S)
    Intento  SALSA  (dos S y dos A)
    Naive daria 5 amarillos. El correcto es 4, porque el segundo S ya
    no tiene letra S disponible en la palabra secreta.
    """
    assert codigos("SALSA", "ALGAS") == [
        "amarillo",  # S esta en ALGAS (posicion 3)
        "amarillo",  # A esta en ALGAS (posicion 0)
        "amarillo",  # L esta en ALGAS (posicion 2)
        "gris",  # la segunda S: ya se consumio la unica S
        "amarillo",  # A esta en ALGAS (posicion 0)
    ]


def test_letras_repetidas_con_verde_que_gasta_la_letra() -> None:
    """La secreta LLAMA tiene dos L ya colocadas; el intento no puede
    marcarlas amarillas dos veces por el mismo L de la secreta."""
    # Intento LLAVA contra LLAMA:
    #   pos 0 y 1 verdes (LL), pos 2 verde (A), pos 3 V gris, pos 4 verde (A)
    assert codigos("LLAVA", "LLAMA") == ["verde", "verde", "verde", "gris", "verde"]


def test_letras_repetidas_mas_complicado() -> None:
    """Secreta PERRO (dos R) e intento RERRO (tres R).

    Tres R en el intento, pero la secreta solo tiene dos, y ademas dos de
    ellas ya estan verdes: la R de la posicion 0 se queda gris porque las
    otras dos R ya se gastaron en las posiciones 2 y 3.
    """
    # PERRO = P E R R O
    # RERRO = R E R R O
    #  pos 0: R vs P -> no verde
    #  pos 1: E vs E -> VERDE
    #  pos 2: R vs R -> VERDE
    #  pos 3: R vs R -> VERDE
    #  pos 4: O vs O -> VERDE
    # Queda solo la P disponible, asi que la R de la posicion 0 es gris.
    assert codigos("RERRO", "PERRO") == ["gris", "verde", "verde", "verde", "verde"]


def test_ningun_verde_puede_saltar_despues_de_un_amarillo() -> None:
    """Invariante general sobre muchos pares: el numero de casillas
    verdes + amarillas de una letra nunca puede pasar de las copias de
    esa letra que hay en la palabra secreta."""
    for secreta in ("PERRO", "ALGAS", "LLAMA", "SALSA", "GANSO", "TINTA", "POLLO"):
        for intento in ("SALSA", "ALGAS", "RERRO", "LLAMA", "GANSO", "ANANA", "OLLLO"):
            estados = codigos(intento, secreta)
            for letra in set(intento):
                disponibles = secreta.count(letra)
                marcadas = sum(
                    1
                    for i, estado in enumerate(estados)
                    if estado in ("verde", "amarillo") and intento[i] == letra
                )
                assert marcadas <= disponibles, (
                    f"{intento} vs {secreta}: '{letra}' tiene {disponibles} copias "
                    f"pero se marcan {marcadas}"
                )
    print("OK  nunca se marcan mas letras de las que hay disponibles")


def test_intento_valido_ocupa_una_fila() -> None:
    juego = JuegoWordle.iniciar(BancoPalabras.construir(5), dict(DEFAULT_CONFIG))
    juego.secreta = "perro"  # fijamos la secreta para que el test sea fijo

    resultado = juego.intentar("SALSA")

    assert resultado.valido
    assert resultado.exito()
    assert len(resultado.intento.estados) == 5
    assert resultado.intento.numero == 1
    assert juego.intentos_usados == 1
    print("OK  un intento valido ocupa una fila del tablero")


def test_palabras_invalidas_no_cuentan_intento() -> None:
    juego = JuegoWordle.iniciar(BancoPalabras.construir(5), dict(DEFAULT_CONFIG))
    juego.secreta = "perro"

    casos = [
        ("CASA", "pocos caracteres"),      # 4 letras
        ("CASINO", "muchos caracteres"),    # 6 letras
        ("BRONX", "no esta en el diccionario"),
        ("NNNN", "no esta en el diccionario"),
        ("12345", "no son letras"),
    ]
    for palabra, motivo in casos:
        resultado = juego.intentar(palabra)
        assert not resultado.valido, f"{palabra} deberia ser invalido ({motivo})"
        assert resultado.error, f"falta el mensaje de error para {palabra}"
        assert juego.intentos_usados == 0, f"{palabra} no deberia contar intento"
    print(f"OK  las {len(casos)} palabras invalidas se rechazan sin gastar intento")


def test_las_mayusculas_y_los_espacios_se_normalizan() -> None:
    juego = JuegoWordle.iniciar(BancoPalabras.construir(5), dict(DEFAULT_CONFIG))
    juego.secreta = "perro"

    resultado = juego.intentar("  salsa  ")

    assert resultado.valido
    assert resultado.intento.palabra == "salsa", "deberia quedar en minusculas"
    print("OK  '  SALSA  ' se acepta y se guarda como 'salsa'")


def test_victoria_en_el_ultimo_intento() -> None:
    config = dict(DEFAULT_CONFIG)
    juego = JuegoWordle.iniciar(BancoPalabras.construir(5), config)
    juego.secreta = "perro"

    # 5 intentos fallidos y el sexto acertado.
    fallidos = [p for p in BancoPalabras.construir(5).palabras if p != "perro"][:5]
    for palabra in fallidos:
        juego.intentar(palabra.lower())
        assert juego.esta_jugando(), "no deberia terminar antes de tiempo"

    resultado = juego.intentar("perro")

    assert resultado.valido
    assert juego.estado == JuegoWordle.ESTADO_GANADO
    assert not juego.esta_jugando()
    print("OK  se puede ganar en el sexto intento")


def test_derrota_al_agotar_los_intentos() -> None:
    config = dict(DEFAULT_CONFIG)
    juego = JuegoWordle.iniciar(BancoPalabras.construir(5), config)
    juego.secreta = "perro"

    fallidos = [p for p in BancoPalabras.construir(5).palabras if p != "perro"][:6]
    for palabra in fallidos:
        juego.intentar(palabra.lower())

    assert juego.intentos_usados == config["intentos_maximos"]
    assert juego.estado == JuegoWordle.ESTADO_PERDIDO
    assert not juego.esta_jugando()
    assert juego.quedan_intentos() == 0
    print("OK  al sexto fallo se pierde la partida")


def test_tras_la_derrota_no_se_puede_seguir_jugando() -> None:
    juego = JuegoWordle.iniciar(BancoPalabras.construir(5), dict(DEFAULT_CONFIG))
    juego.secreta = "perro"
    fallidos = [p for p in BancoPalabras.construir(5).palabras if p != "perro"][:6]
    for palabra in fallidos:
        juego.intentar(palabra.lower())

    resultado = juego.intentar("CASINO")  # ni siquiera es valida

    assert not resultado.valido
    assert juego.intentos_usados == 6, "no debe contar un intento nuevo"
    print("OK  despues de perder, cualquier palabra se rechaza")


def test_la_derrota_no_salta_en_el_turno_ganador() -> None:
    """Si el ultimo intento acierta, es victoria aunque se agoten los
    seis: no puede ser las dos cosas a la vez."""
    config = dict(DEFAULT_CONFIG)
    config["intentos_maximos"] = 2
    juego = JuegoWordle.iniciar(BancoPalabras.construir(5), config)
    juego.secreta = "perro"

    juego.intentar("CASINO".lower())  # 6 letras: no es valida, no cuenta
    juego.intentar("gatos")          # falla y cuenta como intento 1 de 2
    assert juego.intentos_usados == 1
    juego.intentar("perro")           # acierta en el ultimo intento

    assert juego.intentos_usados == 2
    assert juego.estado == JuegoWordle.ESTADO_GANADO
    print("OK  acertar en el ultimo intento es victoria, no derrota")


def test_reiniciar_baraja_otra_palabra() -> None:
    juego = JuegoWordle.iniciar(BancoPalabras.construir(5), dict(DEFAULT_CONFIG))
    juego.intentar("CASINO")  # intento invalido, no cuenta
    juego.reiniciar()

    assert juego.intentos == []
    assert juego.intentos_usados == 0
    assert juego.estado == JuegoWordle.ESTADO_JUGANDO
    assert juego.secreta in BancoPalabras.construir(5).palabras
    # puede tocar la misma palabra por azar, asi que no se comprueba el
    # cambio: lo que importa es que la partida vuelve a admitir jugadas
    assert juego.intentar("salsa").valido is True
    print("OK  reiniciar deja la partida a cero con una palabra del banco")


def test_el_estado_de_las_letras_mapea_a_clases_css() -> None:
    assert EstadoLetra.VERDE.color_css() == "verde"
    assert EstadoLetra.AMARILLO.color_css() == "amarillo"
    assert EstadoLetra.GRIS.color_css() == "gris"
    assert EstadoLetra.VACIA.color_css() == "vacia"
    print("OK  cada estado de letra tiene su clase CSS")


def test_la_secreta_siempre_tiene_la_longitud_correcta() -> None:
    for _ in range(50):
        juego = JuegoWordle.iniciar(BancoPalabras.construir(5), dict(DEFAULT_CONFIG))
        assert len(juego.secreta) == 5, juego.secreta
        assert juego.secreta.islower(), juego.secreta
    print("OK  la palabra secreta siempre tiene 5 letras en minusculas")


def test_la_secreta_tiene_letras_repetidas_a_veces() -> None:
    """Comprobacion de que el banco incluye palabras con repetidas, que
    son las que hacen util el algoritmo de dos pasadas."""
    banco = BancoPalabras.construir(5)
    con_repetidas = [p for p in banco.palabras if len(set(p)) < 5]

    assert len(con_repetidas) > 20, f"solo hay {len(con_repetidas)} con repetidas"
    print(f"OK  el banco tiene {len(con_repetidas)} palabras con letras repetidas")


def main() -> None:
    # Semilla fija para que los tests que barajan sean repetibles.
    random.seed(11)

    tests = [v for nombre, v in sorted(globals().items()) if nombre.startswith("test_")]
    for test in tests:
        test()

    print(f"\n{len(tests)} tests correctos.")


if __name__ == "__main__":
    main()
