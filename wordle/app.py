"""InterfazStreamlit: el tablero, la entrada y los botones.

La regla de oro de Streamlit es que el script se reejecuta entero en cada
clic, y que una clave de widget NO se puede modificar despues de haber
instanciado ese widget en la misma pasada. Por eso los dos botones que
necesitan vaciar el campo de texto usan callbacks (on_click): los callbacks
se ejecutan ANTES de repintar el script, y ahi si se puede tocar la clave.
"""

import streamlit as st

from config import DEFAULT_CONFIG
from game import COLORES_WORDLE, BancoPalabras, EstadoLetra, JuegoWordle

st.set_page_config(page_title="Wordle", page_icon="🟩", layout="centered")

TECLADO = ("QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM")

# Numeros editables en la barra lateral: (clave, etiqueta, minimo, maximo, paso)
PARAMETROS_SIDEBAR = [
    ("intentos_maximos", "Intentos máximos", 3, 10, 1),
    ("tamano_casilla_px", "Tamaño de casilla (px)", 30, 90, 4),
    ("hueco_casilla_px", "Separación (px)", 0, 20, 1),
    ("mostrar_teclado", "Mostrar teclado de letras", None, None, None),
    ("animacion_volteo", "Animación de volteo", None, None, None),
    ("normalizar_mayusculas", "Aceptar mayúsculas", None, None, None),
    ("permitir_espacios", "Ignorar espacios", None, None, None),
    ("aceptar_tildes", "Aceptar tildes y ñ", None, None, None),
]


# ---------------------------------------------------------------------------
# Estado de la sesion
# ---------------------------------------------------------------------------
def iniciar_sesion() -> None:
    """Crea config, juego y cuentas la primera vez; luego los reutiliza.

    Sin el "if not in", cada clic recrearia la partida y la palabra secreta
    cambiaria sola.
    """
    if "config" not in st.session_state:
        st.session_state.config = dict(DEFAULT_CONFIG)
    if "juego" not in st.session_state:
        st.session_state.juego = JuegoWordle.iniciar(
            BancoPalabras.construir(st.session_state.config["longitud_palabra"]),
            st.session_state.config,
        )
    if "cuentas" not in st.session_state:
        st.session_state.cuentas = {
            "ganadas": 0,
            "perdidas": 0,
            "racha": 0,
            "mejor_racha": 0,
        }
    if "error" not in st.session_state:
        st.session_state.error = ""


# ---------------------------------------------------------------------------
# Callbacks: se ejecutan antes de repintar el script
# ---------------------------------------------------------------------------
def al_intentar() -> None:
    """Toma la palabra construida letra a letra y la manda al juego.

    El jugador escribe una sola letra por casilla, y el callback junta esas
    letras en la palabra completa para reutilizar la validacion del juego.
    """
    juego: JuegoWordle = st.session_state.juego
    letras = st.session_state.get("entrada_letras", [""] * st.session_state.config["longitud_palabra"])
    palabra = "".join(letras).strip()
    st.session_state.entrada = palabra

    if len(palabra) != st.session_state.config["longitud_palabra"]:
        st.session_state.error = (
            f"Debes completar las {st.session_state.config['longitud_palabra']} letras."
        )
        return

    resultado = juego.intentar(palabra)

    if resultado.valido:
        st.session_state.error = ""
        if not juego.esta_jugando():
            sumar_partida(ganada=juego.estado == JuegoWordle.ESTADO_GANADO)
    else:
        st.session_state.error = resultado.error

    st.session_state.entrada_letras = [""] * st.session_state.config["longitud_palabra"]
    st.session_state.entrada = ""


def al_nueva_palabra() -> None:
    """Baraja otra palabra y pone los contadores a cero."""
    juego: JuegoWordle = st.session_state.juego
    juego.reiniciar()
    st.session_state.entrada = ""
    st.session_state.entrada_letras = [""] * st.session_state.config["longitud_palabra"]
    st.session_state.error = ""


def sumar_partida(ganada: bool) -> None:
    """Actualiza las cuentas de la sesion."""
    cuentas = st.session_state.cuentas
    if ganada:
        cuentas["ganadas"] += 1
        cuentas["racha"] += 1
        cuentas["mejor_racha"] = max(cuentas["mejor_racha"], cuentas["racha"])
    else:
        cuentas["perdidas"] += 1
        cuentas["racha"] = 0


# ---------------------------------------------------------------------------
# Dibujado del tablero
# ---------------------------------------------------------------------------
def casilla_html(letra: str, estado: EstadoLetra, indice: int, animar: bool) -> str:
    """Una casilla suelta. El indice alimenta el retardo de la animacion
    para que las letras salgan de izquierda a derecha."""
    estilo_animacion = f" style='animation-delay:{indice * 0.08:.2f}s'" if animar else ""
    return (
        f"<div class='casilla {estado.color_css()}'{estilo_animacion}>{letra}</div>"
    )


def dibujar_tablero() -> None:
    """Pinta la rejilla de 6 filas x 5 casillas de una sola vez.

    Las filas que aun no se han jugado salen vacias con borde, que es
    justo como se ve el tablero real de Wordle.
    """
    juego: JuegoWordle = st.session_state.juego
    config = st.session_state.config
    animar = config["animacion_volteo"] and bool(juego.intentos)

    filas = []
    for indice_fila in range(config["intentos_maximos"]):
        intento = (
            juego.intentos[indice_fila]
            if indice_fila < len(juego.intentos)
            else None
        )
        casillas = []
        for indice in range(config["longitud_palabra"]):
            if intento is None:
                estado = EstadoLetra.VACIA
                letra = ""
            else:
                letra = intento.palabra[indice].upper()
                estado = intento.estados[indice]
            casillas.append(casilla_html(letra, estado, indice, animar))
        filas.append(f"<div class='fila'>{''.join(casillas)}</div>")

    st.markdown(
        f"<div class='tablero'>{''.join(filas)}</div>",
        unsafe_allow_html=True,
    )


def dibujar_teclado() -> None:
    """Extra opcional: cada letra con el mejor color que ha tenido.

    Verde gana siempre, luego amarillo, luego gris: la misma prioridad que
    usa el algoritmo de dos pasadas. Por eso se comparan los colores con
    una tabla y no se sobrescribe sin más: si no, un gris de un intento
    temprano taparía al verde de uno posterior.
    """
    juego: JuegoWordle = st.session_state.juego
    prioridad = {
        EstadoLetra.VACIA: 0,
        EstadoLetra.GRIS: 1,
        EstadoLetra.AMARILLO: 2,
        EstadoLetra.VERDE: 3,
    }
    colores: dict[str, EstadoLetra] = {}

    for intento in juego.intentos:
        for letra, estado in zip(intento.palabra, intento.estados):
            if prioridad[estado] > prioridad[colores.get(letra, EstadoLetra.VACIA)]:
                colores[letra] = estado

    filas = []
    for fila in TECLADO:
        teclas = "".join(
            f"<div class='tecla {colores.get(letra.lower(), EstadoLetra.VACIA).color_css()}'>"
            f"{letra}</div>"
            for letra in fila
        )
        filas.append(f"<div class='tecla-fila'>{teclas}</div>")

    st.markdown(f"<div class='teclado'>{''.join(filas)}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Dibujado del resto
# ---------------------------------------------------------------------------
def dibujar_entrada() -> None:
    """Cada letra se introduce en su propia casilla, una por una.

    Esto permite jugar escribiendo solo una letra en vez de la palabra entera,
    pero la palabra final sigue pasando por la misma validacion del juego.
    """
    juego: JuegoWordle = st.session_state.juego
    config = st.session_state.config
    terminado = not juego.esta_jugando()
    longitud = config["longitud_palabra"]

    if "entrada_letras" not in st.session_state:
        st.session_state.entrada_letras = [""] * longitud

    columnas = st.columns(longitud)
    for indice, columna in enumerate(columnas):
        with columna:
            valor = st.text_input(
                f"Letra {indice + 1}",
                max_chars=1,
                key=f"entrada_letra_{indice}",
                label_visibility="collapsed",
                value=st.session_state.entrada_letras[indice],
                disabled=terminado,
            )
            st.session_state.entrada_letras[indice] = valor.upper() if valor else ""

    st.button(
        "Intentar",
        on_click=al_intentar,
        disabled=terminado,
        width="stretch",
    )

    if st.session_state.error:
        st.error(st.session_state.error)


def dibujar_estado() -> None:
    """Muestra intentos restantes, y el final si la partida ha acabado."""
    juego: JuegoWordle = st.session_state.juego

    if juego.estado == JuegoWordle.ESTADO_GANADO:
        st.success(f"🎉 ¡Acertaste **{juego.secreta.upper()}** en {juego.intentos_usados}!")
    elif juego.estado == JuegoWordle.ESTADO_PERDIDO:
        st.error(f"💀 Se acabaron los intentos. La palabra era **{juego.secreta.upper()}**.")
    else:
        st.caption(f"Te quedan **{juego.quedan_intentos()}** intentos.")

    if not juego.esta_jugando():
        st.button(
            "🔄 Otra palabra",
            on_click=al_nueva_palabra,
            width="stretch",
        )


def dibujar_cuentas() -> None:
    """Las estadisticas de la sesion actual."""
    cuentas = st.session_state.cuentas
    columnas = st.columns(4)
    with columnas[0]:
        st.metric("Ganadas", cuentas["ganadas"])
    with columnas[1]:
        st.metric("Perdidas", cuentas["perdidas"])
    with columnas[2]:
        st.metric("Racha", cuentas["racha"])
    with columnas[3]:
        st.metric("Mejor racha", cuentas["mejor_racha"])


def dibujar_sidebar() -> None:
    """Edita el config en caliente.

    La longitud de palabra no se edita aqui a proposito: cambiaria el
    tamano del tablero y dejaria el banco sin palabras, asi que se deja
    fija en 5 como el resto de proyectos.

    Ojo con el orden: esta funcion se ejecuta ANTES de dibujar_entrada(),
    y por eso puede limpiar la clave "entrada". Si se llamara despues,
    Streamlit se quejaria porque el widget ya estaria creado.
    """
    with st.sidebar:
        st.markdown("### ⚙️ Ajustes")
        st.caption("Cambiar un valor empieza una partida nueva.")

        for clave, etiqueta, minimo, maximo, paso in PARAMETROS_SIDEBAR:
            actual = st.session_state.config[clave]
            if minimo is None:  # es un interruptor on/off
                nuevo = st.toggle(etiqueta, value=bool(actual), key=f"cfg_{clave}")
            else:
                nuevo = st.number_input(
                    etiqueta,
                    min_value=minimo,
                    max_value=maximo,
                    step=paso,
                    value=int(actual),
                    key=f"cfg_{clave}",
                )
            if nuevo != actual:
                st.session_state.config[clave] = nuevo
                # El tablero cambia de tamano o el banco cambia de reglas,
                # asi que se reconstruye el juego entero.
                st.session_state.juego = JuegoWordle.iniciar(
                    BancoPalabras.construir(st.session_state.config["longitud_palabra"]),
                    st.session_state.config,
                )
                st.session_state.entrada = ""
                st.session_state.error = ""


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
def inyectar_estilos() -> None:
    """CSS del tablero. Los colores salen del modelo, no estan escritos aqui."""
    config = st.session_state.get("config", DEFAULT_CONFIG)
    st.markdown(
        f"""
        <style>
        .tablero {{
            display: flex; flex-direction: column; gap: {config["hueco_casilla_px"]}px;
            align-items: center; margin: 0 auto 1.2rem auto; width: fit-content;
        }}
        .fila {{ display: flex; gap: {config["hueco_casilla_px"]}px; }}
        .casilla {{
            width: {config["tamano_casilla_px"]}px;
            height: {config["tamano_casilla_px"]}px;
            display: flex; align-items: center; justify-content: center;
            font-size: {config["tamano_casilla_px"] * 0.46:.0f}px; font-weight: 800;
            text-transform: uppercase; color: #fff; border-radius: 4px;
            box-sizing: border-box;
        }}
        .casilla.verde {{ background: {COLORES_WORDLE[EstadoLetra.VERDE]}; border: 2px solid {COLORES_WORDLE[EstadoLetra.VERDE]}; }}
        .casilla.amarillo {{ background: {COLORES_WORDLE[EstadoLetra.AMARILLO]}; border: 2px solid {COLORES_WORDLE[EstadoLetra.AMARILLO]}; }}
        .casilla.gris {{ background: {COLORES_WORDLE[EstadoLetra.GRIS]}; border: 2px solid {COLORES_WORDLE[EstadoLetra.GRIS]}; }}
        .casilla.vacia {{ background: transparent; border: 2px solid {COLORES_WORDLE[EstadoLetra.GRIS]}; }}

        @keyframes voltear {{
            0% {{ transform: rotateX(0deg); }}
            45% {{ transform: rotateX(90deg); }}
            60% {{ transform: rotateX(90deg); }}
            100% {{ transform: rotateX(0deg); }}
        }}
        .casilla.verde, .casilla.amarillo, .casilla.gris {{ animation: voltear 0.35s ease; }}

        .teclado {{ display: flex; flex-direction: column; gap: 5px; align-items: center; margin-top: 1rem; }}
        .tecla-fila {{ display: flex; gap: 4px; }}
        .tecla {{
            width: 34px; height: 42px; display: flex; align-items: center;
            justify-content: center; font-weight: 700; font-size: 0.85rem;
            color: #fff; border-radius: 4px; background: #818384;
        }}
        .tecla.vacia {{ background: #565758; }}
        div.stButton > button {{ border-radius: 10px; font-weight: 700; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Pantalla
# ---------------------------------------------------------------------------
# El orden importa. La sidebar primero, porque al mover un parametro cambia
# la config de la sesion; y despues los estilos, para que el CSS salga ya con
# el tamano de casilla nuevo. Al reves, habria que esperar un clic mas para
# que el tablero se repintara al tamano correcto.
iniciar_sesion()
dibujar_sidebar()
inyectar_estilos()

st.title("🟩 Wordle")
st.caption(
    "Adivina la palabra de 5 letras en 6 intentos. "
    "🟩 correcta y en su sitio · 🟨 existe pero en otro sitio · ⬜ no existe."
)

dibujar_tablero()
dibujar_entrada()
dibujar_estado()

if st.session_state.config["mostrar_teclado"]:
    dibujar_teclado()

with st.expander("📊 Estadísticas de esta sesión"):
    dibujar_cuentas()
