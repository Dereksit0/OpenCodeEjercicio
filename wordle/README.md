# 🟩 Wordle

Un Wordle en Streamlit, en español. Adivina la palabra secreta de 5 letras
en 6 intentos. Cada intento devuelve el color de cada letra:

| | Significado |
|---|---|
| 🟩 **verde** | la letra es correcta y está en su posición |
| 🟨 **amarillo** | la letra está en la palabra, pero en otro sitio |
| ⬜ **gris** | la letra no está en la palabra |

Un intento que no esté en el diccionario **no cuenta** y avisa con un error.

## Ejecutar

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Y para comprobar las reglas sin abrir el navegador:

```powershell
python test_wordle.py
```

## Cómo está repartido el código

| Archivo | Qué contiene |
|---|---|
| `config.py` | Los parámetros (intentos, tamaño de casilla, normalización). |
| `datos/palabras.py` | Las 266 palabras del banco. Dato puro, cero lógica. |
| `game/modelos.py` | `EstadoLetra`, `Intento`, `Resultado`. |
| `game/banco.py` | `BancoPalabras`: carga, filtra, valida y sortea. |
| `game/evaluador.py` | `EvaluadorPalabras`: el algoritmo de dos pasadas. |
| `game/juego.py` | `JuegoWordle`: turnos, victoria, derrota. Sin Streamlit. |
| `app.py` | La pantalla: `st.session_state`, callbacks, HTML y CSS. |

`game/` no importa `streamlit` nunca, y por eso se puede testear desde la
terminal.

## El algoritmo de las letras repetidas

Es la única parte difícil de verdad. La regla mental es una:

> cada letra de la palabra secreta se puede acertar **una sola vez**.

Por eso hacen falta dos pasadas:

1. **Verdes primero**, que tienen prioridad absoluta.
2. **Amarillos después**, con un contador de las letras que *quedan* en la
   secreta. Las posiciones ya verdes se ponen a cero en ese contador: su
   letra ya se gastó y no puede volver a aparecer amarilla en otro sitio.

```
secreta ALGAS   intento SALSA
                  S -> hay 1 S        -> 🟨
                  A -> hay 2 A        -> 🟨
                  L -> hay 1 L        -> 🟨
                  S -> ya no queda S  -> ⬜   <-- aquí falla la versión naïve
                  A -> todavía queda 1 A -> 🟨
```

Con una sola pasada saldrían cinco amarillos, cuando solo hay dos `A` y un
`S` disponibles. `test_wordle.py` tiene este caso y dos más como regresión.

## Decisiones que conviene conocer

- **`st.session_state` es obligatorio.** Streamlit reejecuta el script entero
  en cada clic, así que el objeto `JuegoWordle` se crea una sola vez y se
  guarda ahí. Si se creara en cada pasada, la palabra secreta cambiaría sola.
- **Los botones usan callbacks (`on_click`)**, no el cuerpo del script. Es lo
  único que permite vaciar el campo de texto: si se hiciera en el cuerpo,
  Streamlit lanza `StreamlitAPIException` al tocar la clave de un widget ya
  creado. Con callbacks además no hace falta `st.rerun()`.
- **El campo no lleva `max_chars`.** Si lo llevara, Streamlit cortaría en
  silencio lo que sobra y quien escribiera `CASINO` vería «no está en el
  diccionario» en vez de «debe tener 5 letras», sin entender el motivo. Sin
  recorte, el aviso del juego es el correcto.
- **No se usa `str.isalpha()`** para validar letras, porque en Python también
  devuelve `True` para `ñ` y las tildes. Se comprueba letra a letra contra
  `"a".."z"`.
- **El CSS se pinta desde el modelo.** `EstadoLetra.color_css()` decide la
  clase de cada casilla, así que el HTML no puede desincronizarse del juego.
- **`dibujar_sidebar()` se ejecuta antes de `dibujar_entrada()`** a propósito:
  así puede limpiar la clave `entrada` sin que el widget exista todavía.

## Ampliar el banco

Añade la palabra en el grupo que toque de `datos/palabras.py`. Debe tener
**5 letras, en mayúsculas y sin tildes ni ñ**. `test_wordle.py` comprueba
estas reglas al arrancar.
