"""Todos los numeros del juego viven aqui.

Cambiar un valor aqui cambia el balance de la partida sin tocar el codigo.
Ojo con el nombre "hambre": subir SIEMPRE es bueno, asi que
hambre = 100 significa "bien alimentada" y hambre = 0 significa
"murio de hambre". Es la unica forma de que la regla de derrota
(estar a 0) tenga sentido.
"""

DEFAULT_CONFIG = {
    # --- Identidad ---
    "nombre_mascota": "Mochi",

    # --- Valores iniciales ---
    "hambre_inicial": 60,
    "energia_inicial": 70,
    "felicidad_inicial": 65,
    "maximo_estadistica": 100,

    # --- Accion: ALIMENTAR (sube hambre, da un poco de sueño) ---
    "alimentar_hambre": 25,
    "alimentar_energia": -3,
    "alimentar_felicidad": 5,

    # --- Accion: JUGAR (sube felicidad, cansa y da hambre) ---
    "jugar_hambre": -10,
    "jugar_energia": -12,
    "jugar_felicidad": 25,

    # --- Accion: DORMIR (recupera energia, da hambre y aburre) ---
    "dormir_hambre": -10,
    "dormir_energia": 30,
    "dormir_felicidad": -3,

    # --- Decaimiento por turno: el "paso del tiempo" ---
    "perdida_turno_hambre": 6,
    "perdida_turno_energia": 3,
    "perdida_turno_felicidad": 5,

    # --- Eventos: probabilidad de que salte uno en cada turno ---
    "probabilidad_evento": 0.35,

    # --- Umbrales que definen como se siente la mascota ---
    "umbral_alto": 70,
    "umbral_bajo": 30,

    # --- Interfaz ---
    "turnos_historial": 6,
}
