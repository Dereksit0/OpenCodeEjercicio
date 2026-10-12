"""InterfazStreamlit: dibuja la partida y conecta los botones.

Regla de oro de Streamlit: el script se reejecuta entero en cada clic.
Por eso el objeto Juego NO se crea aqui en cada pasada, sino una sola vez
guardado en st.session_state. Si se creara aqui, cada clic borraria la partida.
"""

import streamlit as st

from config import DEFAULT_CONFIG
from game import CLAVES, ICONOS_ESTADISTICA, Accion, Juego

st.set_page_config(page_title="Mascota Virtual", page_icon="🐾", layout="centered")

# Los numeros editables de la barra lateral, agrupados para no saturarla.
# (clave del config, etiqueta visible, minimo, maximo, incremento)
GRUPOS_SIDEBAR = {
    "🐾 Valores iniciales": [
        ("hambre_inicial", "Hambre inicial", 0, 100, 5),
        ("energia_inicial", "Energía inicial", 0, 100, 5),
        ("felicidad_inicial", "Felicidad inicial", 0, 100, 5),
        ("maximo_estadistica", "Máximo por estadística", 10, 200, 10),
    ],
    "🍎 Alimentar": [
        ("alimentar_hambre", "Hambre", -50, 50, 5),
        ("alimentar_energia", "Energía", -50, 50, 5),
        ("alimentar_felicidad", "Felicidad", -50, 50, 5),
    ],
    "🎾 Jugar": [
        ("jugar_hambre", "Hambre", -50, 50, 5),
        ("jugar_energia", "Energía", -50, 50, 5),
        ("jugar_felicidad", "Felicidad", -50, 50, 5),
    ],
    "😴 Dormir": [
        ("dormir_hambre", "Hambre", -50, 50, 5),
        ("dormir_energia", "Energía", -50, 50, 5),
        ("dormir_felicidad", "Felicidad", -50, 50, 5),
    ],
    "⏳ Paso del tiempo": [
        ("perdida_turno_hambre", "Hambre por turno", 0, 30, 1),
        ("perdida_turno_energia", "Energía por turno", 0, 30, 1),
        ("perdida_turno_felicidad", "Felicidad por turno", 0, 30, 1),
    ],
    "⚙️ Eventos y estados": [
        ("probabilidad_evento", "Probabilidad de evento", 0.0, 1.0, 0.05),
        ("umbral_bajo", "Umbral de «me siento mal»", 0, 100, 5),
        ("umbral_alto", "Umbral de «estoy genial»", 0, 100, 5),
        ("turnos_historial", "Mensajes en pantalla", 3, 20, 1),
    ],
}


# ---------------------------------------------------------------------------
# Estado de la sesion
# ---------------------------------------------------------------------------
def iniciar_sesion() -> None:
    """Crea el juego y el config la primera vez; despues los reutiliza.

    El "if not in" es imprescindible: sin el, cada repintado del script
    sustituiria la mascota por una recien iniciada.
    """
    if "config" not in st.session_state:
        st.session_state.config = dict(DEFAULT_CONFIG)
    if "juego" not in st.session_state:
        st.session_state.juego = Juego.iniciar(st.session_state.config)


def reiniciar_juego() -> None:
    """Empieza una partida nueva manteniendo los parametros actuales."""
    st.session_state.juego.reiniciar()


def manejar_accion(accion: Accion) -> None:
    """Aplica la accion y fuerza el repintado de la pantalla.

    Sin st.rerun() la pantalla se quedaria congelada hasta el proximo clic.
    """
    st.session_state.juego.realizar_accion(accion)
    st.rerun()


# ---------------------------------------------------------------------------
# Dibujado
# ---------------------------------------------------------------------------
def dibujar_mascota() -> None:
    """La carta grande con el emoji, el nombre y el turno."""
    juego = st.session_state.juego
    umbral_bajo = juego.config["umbral_bajo"]
    umbral_alto = juego.config["umbral_alto"]

    st.markdown(
        f"""
        <div class="pet-card">
            <div class="pet-emoji">{juego.mascota.emoji(umbral_bajo, umbral_alto)}</div>
            <div class="pet-name">{juego.mascota.nombre}</div>
            <div class="pet-turn">Turno {juego.turno}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dibujar_barras() -> None:
    """Las tres barras. st.progress ya recorta el valor, solo hay que
    pasarle el porcentaje y la etiqueta."""
    estadisticas = st.session_state.juego.mascota.estadisticas
    for clave in CLAVES:
        valor = estadisticas.valor(clave)
        st.progress(
            valor / estadisticas.maximo,
            text=f"{ICONOS_ESTADISTICA[clave]} {clave.capitalize()} · {valor}/{estadisticas.maximo}",
        )


def dibujar_botones() -> None:
    """Los tres botones de accion, deshabilitados cuando la partida acaba."""
    juego = st.session_state.juego
    terminado = not juego.esta_jugando()

    columnas = st.columns(3)
    for columna, accion in zip(columnas, list(Accion)):
        with columna:
            if st.button(
                accion.etiqueta(),
                width="stretch",
                disabled=terminado,
                key=f"btn_{accion.value}",
            ):
                manejar_accion(accion)


def dibujar_historial() -> None:
    """El chatter: lo mas reciente arriba, que es lo que importa."""
    juego = st.session_state.juego
    st.markdown("##### 💬 Lo que dice")
    with st.container(border=True):
        for mensaje in reversed(juego.historial):
            st.markdown(f"{mensaje.icono} {mensaje.texto}")


def dibujar_derrota() -> None:
    """Panel final. Se pinta siempre, pero solo hace algo si se ha perdido,
    asi el orden del render no cambia al perder."""
    juego = st.session_state.juego
    if juego.esta_jugando():
        return

    st.error(
        f"### 💀 {juego.mascota.nombre} se ha escapado\n\n"
        f"**Motivo:** {juego.motivo_derrota.capitalize()}. "
        f"Aguantó {juego.turno} turnos."
    )
    if st.button("🐾 Nueva mascota", width="stretch"):
        reiniciar_juego()
        st.rerun()


def dibujar_sidebar() -> None:
    """Edita el config en caliente.

    Cada control usa su propia clave (prefijo cfg_) para que Streamlit no
    se queje de modificar un widget ya creado. Al detectar un cambio se
    reinicia la partida, porque cambiar el balance a mitad de juego daria
    estadísticas absurdas.
    """
    with st.sidebar:
        st.markdown("### ⚙️ Parámetros del juego")
        st.caption("Cambiar un valor reinicia la partida.")

        nombre = st.text_input(
            "Nombre de la mascota",
            value=st.session_state.config["nombre_mascota"],
            key="cfg_nombre_mascota",
        )
        if nombre != st.session_state.config["nombre_mascota"]:
            st.session_state.config["nombre_mascota"] = nombre or DEFAULT_CONFIG["nombre_mascota"]
            reiniciar_juego()

        for titulo, controles in GRUPOS_SIDEBAR.items():
            with st.expander(titulo):
                for clave, etiqueta, minimo, maximo, paso in controles:
                    valor = st.number_input(
                        etiqueta,
                        min_value=minimo,
                        max_value=maximo,
                        step=paso,
                        value=float(st.session_state.config[clave])
                        if isinstance(st.session_state.config[clave], float)
                        else st.session_state.config[clave],
                        key=f"cfg_{clave}",
                    )
                    if valor != st.session_state.config[clave]:
                        st.session_state.config[clave] = valor
                        reiniciar_juego()


# ---------------------------------------------------------------------------
# Pantalla
# ---------------------------------------------------------------------------
def inyectar_estilos() -> None:
    """Un poco de CSS solo para la carta de la mascota y los botones."""
    st.markdown(
        """
        <style>
        .pet-card {
            text-align: center;
            padding: 1.4rem 1rem 1.1rem 1rem;
            border-radius: 22px;
            border: 1px solid rgba(255,255,255,0.12);
            background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
            margin-bottom: 1rem;
        }
        .pet-emoji { font-size: 6rem; line-height: 1.1; }
        .pet-name { font-size: 1.6rem; font-weight: 700; margin-top: 0.3rem; }
        .pet-turn { opacity: 0.65; font-size: 0.9rem; }
        div.stButton > button { border-radius: 14px; font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )


inyectar_estilos()
iniciar_sesion()
dibujar_sidebar()

juego = st.session_state.juego

st.title("🐾 Mascota Virtual")
st.caption(
    "Hambre, energía y felicidad: **cuanto más alto, mejor**. "
    "Si cualquiera de las tres llega a 0, tu mascota se escapa."
)

dibujar_mascota()
dibujar_barras()
dibujar_botones()
dibujar_derrota()
dibujar_historial()
