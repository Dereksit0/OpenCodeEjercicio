"""Tests del juego, sin Streamlit y sin pytest: solo `assert`.

    python test_juego.py

Sirven para comprobar que las reglas (deltas, decaimiento, derrota) hacen
lo que dicen y que el balance no esta roto.
"""

import random
import sys

from config import DEFAULT_CONFIG
from game import Accion, Estadisticas, Evento, Juego

# La consola de Windows usa cp1252 y revienta con los emojis del juego.
sys.stdout.reconfigure(encoding="utf-8")


def config_de_prueba(**cambios) -> dict:
    """Copia del config con los eventos desactivados, para tests deterministas."""
    config = dict(DEFAULT_CONFIG)
    config["probabilidad_evento"] = 0.0
    config.update(cambios)
    return config


def test_las_tres_estadisticas_empiezan_por_el_config() -> None:
    config = config_de_prueba()
    juego = Juego.iniciar(config)
    stats = juego.mascota.estadisticas

    assert stats.hambre == config["hambre_inicial"]
    assert stats.energia == config["energia_inicial"]
    assert stats.felicidad == config["felicidad_inicial"]
    assert juego.turno == 0
    assert juego.esta_jugando()
    print("OK  valores iniciales correctos")


def test_alimentar_sube_hambre_y_pero_no_toca_el_resto() -> None:
    stats = Estadisticas(hambre=50, energia=50, felicidad=50)
    deltas = Accion.ALIMENTAR.deltas(DEFAULT_CONFIG)

    stats.aumentar("hambre", deltas["hambre"])
    stats.disminuir("energia", -deltas["energia"])

    assert stats.hambre == 75
    assert stats.energia == 47
    assert stats.felicidad == 50
    print("OK  alimentar sube hambre y baja energia")


def test_las_estadisticas_nunca_se_salen_de_rango() -> None:
    stats = Estadisticas(hambre=50, energia=50, felicidad=50)

    stats.aumentar("hambre", 999)   # topa contra el maximo
    stats.disminuir("energia", 999) # topa contra el cero

    assert stats.hambre == stats.maximo
    assert stats.energia == 0
    print("OK  valores recortados a [0, maximo]")


def test_el_turno_cobra_siempre_las_perdidas_de_tiempo() -> None:
    config = config_de_prueba(hambre_inicial=80, energia_inicial=80, felicidad_inicial=80)
    juego = Juego.iniciar(config)

    juego.realizar_accion(Accion.DORMIR)
    stats = juego.mascota.estadisticas

    # Orden importante: primero la accion y luego el tiempo.
    # Energia: 80 + 30 = 110 -> se recorta a 100 -> despues -3 = 97.
    assert stats.energia == 97
    # Hambre: 80 - 10 (dormir) - 6 (tiempo) = 64.
    assert stats.hambre == 64
    assert juego.turno == 1
    print("OK  el paso del tiempo se aplica en cada turno")


def test_llegar_a_cero_es_derrota_y_dice_el_motivo() -> None:
    config = config_de_prueba(hambre_inicial=2, energia_inicial=100, felicidad_inicial=100)
    juego = Juego.iniciar(config)

    juego.realizar_accion(Accion.JUGAR)

    assert juego.mascota.estadisticas.hambre == 0
    assert not juego.esta_jugando()
    assert juego.motivo_derrota == "hambre"
    assert juego.mascota.emoji() == "💀"
    print("OK  al llegar a 0 la mascota se escapa por hambre")


def test_tras_derrota_las_acciones_se_ignoran() -> None:
    config = config_de_prueba(energia_inicial=100, felicidad_inicial=100)
    juego = Juego.iniciar(config)
    juego.mascota.estadisticas.hambre = 0
    juego.comprobar_derrota()

    turno_final = juego.turno
    juego.realizar_accion(Accion.ALIMENTAR)

    assert juego.turno == turno_final
    assert juego.estado == Juego.ESTADO_PERDIDO
    print("OK  no se puede jugar despues de perder")


def test_reiniciar_devuelve_las_estadisticas_al_config() -> None:
    config = config_de_prueba()
    juego = Juego.iniciar(config)

    for _ in range(4):
        juego.realizar_accion(Accion.JUGAR)
    juego.reiniciar()

    assert juego.turno == 0
    assert juego.estado == Juego.ESTADO_JUGANDO
    assert juego.motivo_derrota == ""
    assert juego.mascota.estadisticas.hambre == config["hambre_inicial"]
    print("OK  reiniciar deja la partida como al principio")


def test_los_eventos_se_generan_dentro_del_rango() -> None:
    for _ in range(200):
        evento = Evento.generar_aleatorio()
        stats = Estadisticas(hambre=50, energia=50, felicidad=50)
        evento.aplicar(stats)

        for clave in ("hambre", "energia", "felicidad"):
            assert 0 <= stats.valor(clave) <= stats.maximo
    print("OK  los eventos siempre respetan el rango [0, maximo]")


def test_la_probabilidad_cero_desactiva_los_eventos() -> None:
    juego = Juego.iniciar(config_de_prueba())
    for _ in range(50):
        assert juego.aplicar_evento() is None
    print("OK  probabilidad_evento = 0 no dispara eventos")


def test_el_emoji_y_el_mensaje_cambian_segun_el_estado() -> None:
    config = config_de_prueba()
    juego = Juego.iniciar(config)
    emojis_vistos = set()

    for accion in Accion:
        stats = juego.mascota.estadisticas
        stats.hambre, stats.energia, stats.felicidad = 80, 80, 80
        emojis_vistos.add(juego.mascota.emoji())
        juego.realizar_accion(accion)

    stats = juego.mascota.estadisticas
    stats.hambre, stats.energia, stats.felicidad = 10, 10, 10
    emojis_vistos.add(juego.mascota.emoji())

    assert len(emojis_vistos) >= 2, "el emoji deberia cambiar con el estado"
    assert "🤢" in emojis_vistos, "con dos estadisticas bajas debe estar enferma"
    print(f"OK  el estado cambia el emoji (vistos: {sorted(emojis_vistos)})")


def test_el_balance_aganta_entre_5_y_20_turnos() -> None:
    """Una partida no debe ser ni instantanea ni eterna."""
    turnos = []
    for _ in range(50):
        juego = Juego.iniciar(dict(DEFAULT_CONFIG))
        while juego.esta_jugando() and juego.turno < 200:
            # Rotar las tres acciones es lo que hace un jugador normal.
            juego.realizar_accion(list(Accion)[juego.turno % 3])
        turnos.append(juego.turno)

    promedio = sum(turnos) / len(turnos)
    assert 5 <= promedio <= 20, f"partida demasiado corta o larga: {promedio:.1f} turnos"
    assert all(juego <= 200 for juego in turnos)
    print(f"OK  duracion media de la partida: {promedio:.1f} turnos (min {min(turnos)}, max {max(turnos)})")


def test_no_basta_con_alternar_comer_y_dormir() -> None:
    """Comer y dormir en bucle parece seguro, pero no mantiene la
    felicidad: hay que jugar tambien. Este test vigila que ese truco no
    vuelva a ser una partida infinita."""
    turnos = []
    for _ in range(30):
        juego = Juego.iniciar(dict(DEFAULT_CONFIG))
        while juego.esta_jugando() and juego.turno < 300:
            juego.realizar_accion(
                Accion.ALIMENTAR if juego.turno % 2 == 0 else Accion.DORMIR
            )
        turnos.append(juego.turno)

    assert max(turnos) < 40, f"el truco de comer y dormir dura demasiado: {max(turnos)}"
    print(f"OK  comer y dormir en bucle no es infinito (max {max(turnos)} turnos)")


def main() -> None:
    # Semilla fija para que el test de eventos y el de balance sean repetibles.
    random.seed(7)

    tests = [valor for nombre, valor in sorted(globals().items()) if nombre.startswith("test_")]
    for test in tests:
        test()

    print(f"\n{len(tests)} tests correctos.")


if __name__ == "__main__":
    main()
