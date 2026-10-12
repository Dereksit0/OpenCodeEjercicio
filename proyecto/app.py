import streamlit as st
import time

from config import DEFAULT_CONFIG
from game.models import Game

st.set_page_config(page_title="Castillo Aventura", page_icon="🏰", layout="wide")

st.markdown(
    """
    <style>
        :root {
            --bg: #050b13;
            --bg-2: #0b121d;
            --panel: rgba(16, 24, 34, 0.96);
            --panel-soft: rgba(26, 34, 46, 0.9);
            --panel-alt: rgba(12, 17, 25, 0.98);
            --line: rgba(255,255,255,0.08);
            --text: #edf5ff;
            --muted: #9aa8bb;
            --blue: #59a9ff;
            --gold: #ffbf4a;
            --red: #ff6363;
            --green: #64dd9a;
            --purple: #a78bfa;
        }

        html, body, [data-testid="stAppViewContainer"], .main {
            background: radial-gradient(circle at top, #0d1420 0%, var(--bg) 38%, #04080d 100%);
            color: var(--text);
        }

        [data-testid="stSidebar"] {
            background: rgba(17, 24, 34, 0.98);
            border-right: 1px solid var(--line);
            padding: 1rem 0.8rem;
        }

        .sidebar-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f4f7ff;
            margin-bottom: 1rem;
        }

        .sidebar-block {
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 0.9rem 0.8rem;
            margin-bottom: 0.9rem;
        }

        .sidebar-label {
            font-size: 0.92rem;
            color: var(--muted);
            margin-bottom: 0.5rem;
        }

        .stepper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
        }

        .stepper button {
            width: 2.1rem !important;
            height: 2.1rem !important;
            min-width: 2.1rem !important;
            border-radius: 10px !important;
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid var(--line) !important;
            color: var(--text) !important;
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            padding: 0 !important;
        }

        .stepper-value {
            flex: 1;
            text-align: center;
            font-weight: 700;
            color: var(--text);
            padding: 0.35rem 0.4rem;
            border-radius: 10px;
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--line);
        }

        .app-shell {
            max-width: 1360px;
            margin: 0 auto;
            padding: 1.2rem 1rem 2rem;
        }

        .metrics-row {
            display: grid;
            grid-template-columns: repeat(4, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 0.8rem;
        }

        .metric-card {
            min-height: 92px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 0.7rem 0.9rem;
            border-radius: 16px;
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--line);
        }

        .metric-label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--muted);
            font-size: 0.96rem;
            margin-bottom: 0.3rem;
        }

        .metric-value {
            font-size: clamp(2rem, 2.3vw, 2.7rem);
            font-weight: 700;
            letter-spacing: -0.04em;
            color: var(--text);
        }

        .metric-value.gold {
            color: var(--gold);
        }

        .health-track {
            max-width: 760px;
            margin: 0 auto 1.2rem auto;
            height: 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            overflow: hidden;
            border: 1px solid var(--line);
        }

        .health-bar {
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #47a4ff 0%, #76c6ff 100%);
            box-shadow: 0 0 18px rgba(82,169,255,0.5);
        }

        .map-panel {
            border-top: 1px solid var(--line);
            padding-top: 1.2rem;
        }

        .map-header {
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.7rem;
            font-weight: 700;
            font-size: clamp(1.8rem, 2vw, 2.5rem);
            margin-bottom: 0.9rem;
            color: #edf4ff;
        }

        .map-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(70px, 1fr));
            gap: 0.7rem;
            margin-top: 0.7rem;
        }

        .tile {
            min-height: 100px;
            border-radius: 14px;
            background: rgba(255,255,255,0.02);
            border: 1px dashed rgba(255,255,255,0.12);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--muted);
            text-transform: lowercase;
            font-size: 0.72rem;
            padding: 0.25rem;
        }

        .tile strong {
            font-size: 1.3rem;
            margin-bottom: 0.3rem;
            display: block;
        }

        .tile.enemy {
            border-color: rgba(255,191,74,0.72);
            box-shadow: inset 0 0 0 1px rgba(255,191,74,0.25);
            background: rgba(255,191,74,0.04);
        }

        .tile.treasure {
            border-color: rgba(100, 221, 154, 0.6);
            background: rgba(100, 221, 154, 0.04);
        }

        .tile.wall {
            border-color: rgba(255,99,99,0.65);
            background: rgba(255,99,99,0.07);
        }

        .tile.fog {
            color: #748196;
            background: rgba(0,0,0,0.2);
            border-style: solid;
        }

        .tile.current {
            border-color: rgba(89,169,255,0.9);
            box-shadow: 0 0 0 1px rgba(89,169,255,0.38), 0 0 15px rgba(89,169,255,0.18);
            background: rgba(89,169,255,0.06);
        }

        .story-panel {
            margin-top: 1.5rem;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: rgba(255,255,255,0.02);
            padding: 1.1rem 1.1rem 1rem;
        }

        .story-title {
            margin: 0 0 0.55rem;
            color: var(--text);
            font-size: clamp(2rem, 2vw, 2.5rem);
        }

        .story-desc {
            margin: 0 0 1rem;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.6;
        }

        .answer-box {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }

        .answer-box input {
            background: rgba(255,255,255,0.02);
            color: var(--text);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 0.6rem 0.9rem;
            min-width: 180px;
        }

        div.stButton > button {
            width: 100%;
            border-radius: 12px !important;
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid var(--line) !important;
            color: var(--text) !important;
            font-weight: 600 !important;
            padding: 0.72rem 1rem !important;
            box-shadow: none !important;
        }

        div.stButton > button:hover {
            border-color: rgba(89,169,255,0.5) !important;
            background: rgba(89,169,255,0.08) !important;
        }

        .status-pill {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            font-weight: 700;
            border: 1px solid transparent;
        }

        .status-pill.win {
            background: rgba(100,221,154,0.12);
            border-color: rgba(100,221,154,0.35);
            color: #c8f9db;
        }

        .status-pill.lose {
            background: rgba(255,99,99,0.12);
            border-color: rgba(255,99,99,0.35);
            color: #ffc0c0;
        }

        @media (max-width: 900px) {
            .metrics-row { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
            .map-grid { grid-template-columns: repeat(3, minmax(80px, 1fr)); }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_game():
    if "config" not in st.session_state:
        st.session_state.config = DEFAULT_CONFIG.copy()
    if "game" not in st.session_state:
        st.session_state.game = Game.create(st.session_state.config)


def reset_game():
    st.session_state.game = Game.create(st.session_state.config)
    st.session_state.answer_input = ""


init_game()


def update_config(key, delta):
    current = st.session_state.config[key]
    st.session_state.config[key] = max(1, current + delta)
    reset_game()


def render_sidebar():
    st.sidebar.markdown('<div class="sidebar-title">⚔️ Reglas de la partida</div>', unsafe_allow_html=True)

    params = [
        ("vida_inicial", "Vida inicial"),
        ("penalizacion_error", "Penalización por error"),
        ("danio_enemigo", "Daño por enemigo"),
        ("oro_objetivo", "Oro objetivo"),
        ("tiempo_limite", "Segundos por respuesta"),
        ("etapas", "Etapas del castillo"),
    ]

    for key, label in params:
        st.sidebar.markdown(f'<div class="sidebar-label">{label}</div>', unsafe_allow_html=True)
        left, mid, right = st.sidebar.columns([1, 2, 1])
        with left:
            if st.button("−", key=f"minus_{key}", use_container_width=True):
                update_config(key, -1)
        with mid:
            st.write(f"{st.session_state.config[key]}")
        with right:
            if st.button("+", key=f"plus_{key}", use_container_width=True):
                update_config(key, 1)


def render_metrics(game):
    metrics = [
        ("❤️", "Vida", f"{game.player.health} / {st.session_state.config['vida_inicial']}"),
        ("🟡", "Oro", f"{game.player.gold} / {st.session_state.config['oro_objetivo']}"),
        ("⚔️", "Enemigos", str(game.player.enemies_defeated)),
        ("🧭", "Salas", str(game.player.rooms_cleared)),
    ]

    cols = st.columns(4)
    for col, (icon, label, value) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label"><span>{icon}</span><span>{label}</span></div>
                    <div class="metric-value {'gold' if label == 'Oro' else ''}">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    health_pct = max(0.0, (game.player.health / st.session_state.config['vida_inicial']) * 100)
    st.markdown(
        f"""
        <div class="health-track">
            <div class="health-bar" style="width: {health_pct}%;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_map(game):
    st.markdown('<div class="map-panel">', unsafe_allow_html=True)
    st.markdown('<div class="map-header"><span>🗺️</span><span>Mapa del castillo</span></div>', unsafe_allow_html=True)

    rooms = game.map.rooms
    cells = []
    for idx, room in enumerate(rooms):
        css = "tile"

        if not room.explored and idx != game.player.current_room:
            icon = "?"
            label = "sin explorar"
            css += " fog"
        elif room.kind == "enemy":
            icon = "⚔️"
            label = "enemigo"
            css += " enemy"
        elif room.kind == "treasure":
            icon = "🏆"
            label = "tesoro"
            css += " treasure"
        elif room.kind == "wall":
            icon = "🧱"
            label = "muro"
            css += " wall"
        else:
            icon = "·"
            label = "vacía"

        if idx == game.player.current_room:
            css += " current"

        cells.append(f'<div class="{css}"><strong>{icon}</strong><span>{label}</span></div>')

    st.markdown(f'<div class="map-grid">{"".join(cells)}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_room(game):
    room = game.current_room()

    last_event = getattr(game, "last_event", "")
    if last_event:
        st.warning(last_event)

    if game.status == "won":
        st.markdown('<div class="story-panel"><h3 class="story-title">🎉 ¡Victoria!</h3>', unsafe_allow_html=True)
        st.markdown(f"<p class='story-desc'>Has reunido {game.player.gold} oro y escapaste del castillo con vida.</p>", unsafe_allow_html=True)
        if st.button("Jugar otra vez"):
            reset_game()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if game.status == "lost":
        st.markdown('<div class="story-panel"><h3 class="story-title">💥 Derrota</h3>', unsafe_allow_html=True)
        st.markdown(f"<p class='story-desc'>Te quedaste sin vida. Oro conseguido: {game.player.gold}</p>", unsafe_allow_html=True)
        if st.button("Reiniciar"):
            reset_game()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if room.kind == "enemy":
        if game.current_operation is None:
            game.generate_enemy_operation()

        remaining = game.time_left()
        st.markdown(f'<div class="story-panel"><h3 class="story-title">⚔️ Encuentro con {room.enemy.name}</h3>', unsafe_allow_html=True)
        st.markdown(f"<p class='story-desc'>{room.description}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='story-desc'><strong>Tiempo restante:</strong> {remaining:.1f}s</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='story-desc'><strong>Operación:</strong> {game.current_operation.text()}</p>", unsafe_allow_html=True)

        answer = st.text_input("Respuesta", key=f"enemy_answer_{game.player.current_room}", value=st.session_state.get(f"enemy_answer_{game.player.current_room}", ""))
        if st.button("Resolver"):
            game.handle_enemy_answer(answer)
            st.rerun()

        if remaining <= 0:
            game.apply_time_expired()
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        return

    if room.kind == "treasure":
        st.markdown('<div class="story-panel"><h3 class="story-title">🏆 Tesoro encontrado</h3>', unsafe_allow_html=True)
        st.markdown(f"<p class='story-desc'>{room.description} Obtienes {room.gold} de oro.</p>", unsafe_allow_html=True)
        if st.button("Recoger oro y continuar"):
            game.player.gain_gold(room.gold)
            room.kind = "empty"
            room.gold = 0
            room.explored = True
            game.check_end_state()
            if game.status == "playing":
                game.move_next_room()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown('<div class="story-panel"><h3 class="story-title">🕯️ Habitación vacía</h3>', unsafe_allow_html=True)
    st.markdown(f"<p class='story-desc'>{room.description}</p>", unsafe_allow_html=True)
    if st.button("Siguiente habitación"):
        game.move_next_room()
        game.check_end_state()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


render_sidebar()

game = st.session_state.game
render_metrics(game)
render_map(game)
render_room(game)

if game.status != "playing":
    st.markdown('<div class="status-pill win">Victoria</div>' if game.status == "won" else '<div class="status-pill lose">Derrota</div>', unsafe_allow_html=True)
