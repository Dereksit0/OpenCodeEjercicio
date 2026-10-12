# 🐾 Mascota Virtual

Un Tamagotchi en Streamlit. Tienes tres barras (**hambre**, **energía** y
**felicidad**) y tres acciones (**Alimentar**, **Jugar**, **Dormir**).
Cada acción es un turno, y en cada turno el tiempo cobra su parte y a
veces salta un evento. Si alguna barra llega a **0**, tu mascota se escapa.

> **Ojo con el nombre "hambre":** subir siempre es bueno. `hambre = 100`
> significa *bien alimentada* y `hambre = 0` significa *murió de hambre*.
> Por eso la regla de derrota tiene sentido.

## Ejecutar

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Y para comprobar las reglas sin abrir el navegador:

```powershell
python test_juego.py
```

## Cómo está repartido el código

| Archivo | Qué contiene |
|---|---|
| `config.py` | Todos los números del juego. Cambiar aquí = cambiar el balance. |
| `game/modelos.py` | `Estadisticas`, `Accion`, `Evento`, `Mensaje`, `Mascota`. Datos puros. |
| `game/juego.py` | `Juego`: qué pasa en cada turno, cuándo se pierde, qué dice la mascota. Sin Streamlit. |
| `app.py` | La pantalla: `st.session_state`, botones, barras y sidebar. |

`game/` no importa `streamlit` nunca, y por eso se puede testear desde la
terminal.

## Cómo fluye un turno

```
Clic en un botón
   └─> Juego.realizar_accion(accion)
        1. la mascota reacciona y cambian las barras
        2. avanzar_turno(): el tiempo cobra las pérdidas del turno
        3. ¿salta un evento? (probabilidad configurable)
        4. la mascota dice cómo se encuentra
        5. comprobar_derrota(): ¿alguna barra en 0? → se escapa
   └─> st.rerun(): se repinta la pantalla
```

## Decisiones que conviene conocer

- **El tiempo solo avanza al pulsar.** Es un juego por turnos, no hay reloj
  ni temporizador. Si no haces nada, no pasa nada.
- **`st.session_state` es obligatorio.** Streamlit reejecuta el script entero
  en cada clic, así que el objeto `Juego` se crea una sola vez y se guarda
  ahí. Si se creara en cada pasada, cada clic borraría la partida.
- **Nadie escribe las barras directamente.** Todo pasa por
  `Estadisticas.aumentar()` / `.disminuir()`, que recortan a `[0, 100]`.
- **La derrota se comprueba en un único sitio**, al final del turno, así que
  es imposible "ganar" el turno en el que mueres.

## Balance actual

Medido con los valores por defecto (200 partidas por estrategia):

| Estrategia | Turnos de media | Se escapó por |
|---|---|---|
| Solo **Alimentar** | 11 | energía |
| Solo **Jugar** | 4 | hambre |
| Solo **Dormir** | 4 | hambre |
| Rotar **A-J-D** (la mejor) | 16 | hambre |
| Alternar **A-D** | 15 | felicidad |

No hay ninguna estrategia ganadora: siempre hay que mezclar las tres. Para
una partida más corta o más larga, baja los valores de `perdida_turno_*` en
la barra lateral, sin tocar código.
