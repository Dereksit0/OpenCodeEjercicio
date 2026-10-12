"""Parametros del juego.

Cambiar un valor aqui cambia las reglas de la partida sin tocar el codigo.
La longitud de palabra se puede tocar, pero solo funciona con 5: es la
unica longitud para la que el banco de datos/palabras.py tiene palabras.
"""

DEFAULT_CONFIG = {
    # --- Reglas ---
    "longitud_palabra": 5,
    "intentos_maximos": 6,

    # --- Apariencia del tablero ---
    "tamano_casilla_px": 58,
    "hueco_casilla_px": 5,
    "animacion_volteo": True,
    "mostrar_teclado": False,  # extra opcional: teclado QWERTY con los colores

    # --- Validacion de lo que escribe el jugador ---
    "normalizar_mayusculas": True,  # .lower() automatico
    "permitir_espacios": True,      # .strip() automatico
    "aceptar_tildes": False,        # si es True, tambien valen palabras con ñ o tilde
}
