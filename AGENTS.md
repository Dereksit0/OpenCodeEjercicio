# AGENTS.md — OpenCode

Workspace con tres proyectos Python + Streamlit hermanos. No es un `git repo`
en la raíz, así que cada carpeta es su propia unidad.

| Proyecto | Qué es | Tests |
|---|---|---|
| `mascota/` | Tamagotchi. Tres barras (hambre/energía/felicidad), tres acciones por turno. | `python test_juego.py` |
| `wordle/` | Adivina la palabra de 5 letras en 6 intentos. | `python test_wordle.py` |
| `proyecto/` | Roguelike con operaciones matemáticas y mapa de habitaciones. | **Sin tests todavía.** |

## Estructura comun a todos

```
<proyecto>/
  app.py        # Solo la pantalla: session_state, widgets, CSS.
  config.py     # DEFAULT_CONFIG, todos los numeros ajustables del juego.
  game/
    __init__.py
    modelos.py  # Datos puros. Sin reglas de partida.
    juego.py    # El orquestador: que pasa en cada turno.
  test_*.py     # Aserts planos, sin pytest.
  requirements.txt
```

Reglas estructurales que ya existen en el codigo y hay que mantener:

- `game/` **nunca** importa `streamlit`. Por eso la partida se testea desde la
  terminal sin levantar la interfaz.
- `config.py` es la unica sede de numeros ajustables. Si un valor se puede
  cambiar sin tocar logica, va en `DEFAULT_CONFIG`, no hardcodeado en la clase.
- La logica va en `game/`; `app.py` solo pinta. Si una regla se puede escribir en
  `game/`, alli va.
- Ojo con el sentido de "hambre" en `mascota/`: subir **siempre** es bueno.
  `hambre = 100` es "bien alimentada", `hambre = 0` es "murio de hambre".

<!-- AGREGADO POR MÍ: INICIO -->

# [AGREGADO] Comandos del proyecto

1. **Instalar dependencias**: se hace dentro de cada proyecto, nunca en la raiz.
   `pip install -r requirements.txt` desde `mascota/`, `wordle/` o `proyecto/`.
   Los tres `requirements.txt` de momento solo piden `streamlit` (`>=1.30` en
   `mascota/` y `wordle/`, sin fijar en `proyecto/`).
2. **Ejecutar los tests**: hoy NO hay pytest. La convencion real del workspace es
   un archivo `test_*.py` con `assert` planos y un `main()` que los corre a mano.
   - `cd mascota; python test_juego.py`
   - `cd wordle; python test_wordle.py`
   - `proyecto/` no tiene suite todavia: si anades logica, anade tambien su test.
   - Con pytest en el futuro: `pytest` desde la carpeta del proyecto. pytest es el
   objetivo, pero la migracion se decide de forma consciente (ver la excepcion 3
   de las Convenciones de calidad).
3. **Linter y formateador (aun NO instalados)**: hoy `ruff`, `black` y `mypy` no
   estan en el sistema ni en ningun `requirements.txt`. Cuando se creen, los
   comandos a usar son `ruff check .`, `ruff format .` (black-compatible) y
   `mypy game/`. Hasta entonces, revisa a mano y no asumas que pasan.
4. **Tipos**: `mypy game/` cuando este disponible. Los modulos ya usan
   `from __future__ import annotations` y anotaciones en las firmas publicas, asi
   que el codigo deberia estar casi listo para el.
5. **Ejecutar la aplicacion**: `streamlit run app.py` desde la carpeta del
   proyecto. Levanta un servidor local; `game/` se importa sin problema porque
   no depende de streamlit.
6. **Antes de dar por buena una regla nueva**, ejecuta el test del proyecto
   afectado y pega el resultado. No digas "funciona" sin haberlo corrido.
7. **Scripts de apoyo**: `proyecto/.venv/` existe; no la uses para los otros dos
   proyectos ni la borres. Si necesitas un entorno nuevo, pregunta antes de crear
   uno.

# [AGREGADO] Estilo de codigo y buenas practicas de Python

1. **PEP 8** en todo lo nuevo. Si una linea pasa de 88 caracteres, partela:
   ese es el limite de `ruff format`, que es el formateador que usa el
   workspace (ver la seccion de Convenciones de calidad).
2. **Type hints en las firmas publicas**: anotaciones de entrada y de retorno
   (`def realizar_accion(self, accion: Accion) -> str:`). Los metodos privados
   tambien se anotan, por consistencia.
3. **Docstrings en espanol, sin tildes ni enye en el codigo**. Explican el "que"
   y, cuando hay una decision no obvia, el "por que". Sin docstring de una linea
   que solo repita el nombre de la funcion.
4. **Nombres sin tildes ni enye en identificadores**: `hambre`, `energia`,
   `felicidad`, `movimiento`. Las tildes van en los textos visibles y en los
   comentarios, nunca en un simbolo. En espanol `libreria` y no `library`.
5. **`snake_case`** para funciones, variables y modulos; **`PascalCase`** para
   clases y dataclasses; `SCREAMING_SNAKE_CASE` para constantes.
6. **Manejo de errores explicito**: captura excepciones concretas, nunca
   `except:` a pelo. Si un dato es invalido, devuelve o registra un motivo
   legible; no dejes que `KeyError` reviente la interfaz.
7. **Sin `print()` en `game/`**. Esa capa no imprime: devuelve informacion para
   que `app.py` la pinte. Los `print` solo existen en los `test_*.py` para
   confirmar el `OK`.
8. **Un solo sitio por regla**. La derrota se comprueba al final del turno y en
   ningun otro punto; las barras solo se tocan por `aumentar()` / `disminuir()`.
   Si añades una comprobacion, revisa que no exista ya en otro archivo.
9. **Refactoriza solo cuando el test verde lo pide**: primero el test, luego el
   minimo codigo, y solo despues limpias duplicados. No mezcles un rediseño con
   una funcionalidad nueva.
10. **`from __future__ import annotations`** al principio de cada modulo nuevo de
    `game/`. Ya lo hacen `modelos.py` y `juego.py`; mantenlo.
11. **Nulo moderno**: escribe `T | None`, nunca `Optional[T]`. Los modulos ya
    usan `from __future__ import annotations`, asi que la anotacion es valida en
    Python 3.10+. Deuda existente: `proyecto/game/models.py` usa `Optional` en
    `Enemy.enemy`, `Game.current_operation` y `Game.time_started`.
12. **Argumentos por defecto inmutables**. Si necesitas una coleccion por
    defecto, usa `field(default_factory=...)` en el dataclass. `Estadisticas`
    ya lo hace bien con `Mascota.estadisticas`.

# [AGREGADO] Convenciones de calidad (Python)

Estas reglas rigen TODO el codigo nuevo. Complementan la seccion de estilo
anterior; donde choquen con ella, manda esta. Al final estan las excepciones
conscientes a este workspace, con su motivo.

1. **Cero codigo sobrante**: nada de abstracciones, parametros ni helpers que
   no hagan falta para resolver lo pedido. Nada de deuda tecnica.
2. **Docstrings en formato Google** para toda funcion, clase y metodo publico,
   con `Args:`, `Returns:` y `Raises:`. Incluye un ejemplo en el docstring si la
   funcion es compleja o poco evidente:

   ```python
   def calculate_total(items: list[dict], tax_rate: float = 0.0) -> float:
       """Calculate the total cost of items including tax.

       Args:
           items: List of item dictionaries with 'price' keys
           tax_rate: Tax rate as decimal (e.g., 0.08 for 8%)

       Returns:
           Total cost including tax

       Raises:
           ValueError: If items is empty or tax_rate is negative
       """
   ```
3. **Nada de `Any`** salvo necesidad real. Si un tipo es dinamico, explica en el
   docstring por que.
4. **Nada de imports salvajes**: nunca `from modulo import *`.
5. **`with` para todo recurso**: ficheros, conexiones, locks. Nunca cierres a
   mano en un camino de error.
6. **`is` para comparar con `None`, `True` y `False`.** Con `==` es un bug
   esperando.
7. **f-strings** para formatear. Nada de `%` ni de `.format()` en codigo nuevo.
8. **List comprehensions y generadores** en vez de bucles que acumulan.
   `enumerate()` en vez de contadores manuales.
9. **Parametros**: 5 o menos por funcion. Si necesitas mas, agrupa en un
   dataclass. Si revisas y sigue siendo mas, explica por que en el docstring.
10. **Salidas tempranas** para reducir anidamiento, no capas de `if` dentro de
    `if`.
11. **Una responsabilidad por funcion y por clase**. Un `__init__` simple:
    si necesita logica de verdad, extrae una funcion de fabrica (`create()`).
    Composicion antes que herencia.
12. **Nada de comentarios tautologicos**. No escribas `# sube el hambre` encima
    de una linea que ya sube el hambre. El comentario explica el POR QUE: la
    invariante, el caso limite, la decision que no es obvia.
13. **Sin `print()` de depuracion ni `breakpoint()`**, nunca. Para depurar, usa
    `logger`.
14. **Imports ordenados**: estandar, luego terceros, luego locales. El modulo
    `time` va arriba con `import time`, no con `__import__("time")` en linea.
15. **Nunca imprimas ni registres secretos**, ni URLs que lleven clave de API.
16. **Antes de commitear**: pasan los tests, pasa mypy, pasa ruff, todas las
    funciones nuevas tienen docstring y type hints, y no queda codigo comentado
    ni `print` de depuracion.
17. **Optimiza cuando el perfil lo justifique, no por defecto.** Aqui los bucles
    son de 5 letras y 6 turnos: `EvaluadorPalabras.evaluar()` recorre 15
    caracteres. Vectorizar o paralelizar ahi es sobre-ingenieria y ademas rompe
    la documentacion de las dos pasadas, que es la parte dificil del Wordle.
    Cuando la medicion demuestre un cuello de botella real, optimiza y explica
    la medicion. La claridad y la mantenibilidad ganan a la sofisticacion.

## [AGREGADO] Excepciones conscientas a estas convenciones

Estas cuatro reglas no aplican a este workspace. No las "arregles" sin preguntar.

1. **Emoji: PERMITIDOS y son carga funcional.** `mascota/` es un Tamagotchi, y
   su cara ES el producto: `ICONOS_ESTADISTICA`, `Accion.icono()`,
   `EMOJI_ESTADO` y el `page_icon` de `app.py` son la interfaz, no adorno.
   En `wordle/`, 🟩🟨⬜ son la representacion de los tres colores. Borrarlos deja
   un juego sin cara. La regla general de no usar emoji sigue valiendo para
   nombres de simbolo, claves de config y mensajes de log.
2. **`logger.error` en vez de `print` para reportar a consola**: aplica a scripts
   y a `app.py`. En `game/` NO hay logger ni print: esa capa devuelve
   informacion y `app.py` la pinta. Es lo que permite testear la partida sin
   levantar Streamlit.
3. **pytest**: se quiere, pero hoy no esta instalado y las dos suites
   existentes funcionan. Migrar es trabajo consciente, no automatico. Cuando se
   migre, los tests pasan a `tests/` y `proyecto/` recibe su `test_models.py`.
4. **`uv` y `pyproject.toml`**: el workspace usa `requirements.txt` y tres
   carpetas independientes, con una `.venv` ya creada en `proyecto/`. Adoptar
   `uv` es un cambio de estructura de proyecto: pidelo antes, no lo impongas.

# [AGREGADO] Pruebas

1. **Metodo actual: `assert` planos, sin pytest.** Un `test_*.py` por proyecto
   con funciones `test_*()` y un `main()` que las recoge con
   `[v for nombre, v in sorted(globals().items()) if nombre.startswith("test_")]`.
   Manten ese formato hasta que se decida migrar a pytest de forma consciente.
   El patron `Arrange-Act-Assert` se respeta igual en cada test: preparar,
   actuar, comprobar.
2. **Carpeta `tests/` cuando exista pytest.** Hasta entonces los tests viven en la
   raiz del proyecto, junto a `app.py`, como `test_juego.py` / `test_wordle.py`.
3. **Nombres de prueba descriptivos y en espanol**, en frase completa:
   `test_las_estadisticas_nunca_se_salen_de_rango`, no `test_1` ni `test_hambre`.
   Cada test imprime una linea `OK ...` explicando que ha comprobado.
4. **Cada test explica el porqué del caso tricky con un comentario**, como hace
   `test_letras_repetidas_el_caso_clasico` en `wordle/`. Los casos raros valen
   mas que diez triviales.
5. **Casos a cubrir siempre**: los tres limites de rango (`0`, `maximo`, y el
   recorte por encima y por debajo), la victoria en el ultimo turno, la derrota
   en el turno en que ocurre, y que despues de terminar no se pueda seguir
   jugando.
6. **Regresion**: si arreglas un fallo, deja el test que lo hacia fallar. Un bug
   corregido sin test vuelve, porque nadie lo vigila.
7. **Determinismo**: `random.seed(...)` con valor fijo al inicio de `main()`.
   Los tests que barajan deben ser repetibles; sin semilla, un fallo aparece una
   vez de cada diez.
8. **Prohibido desactivar, saltarse ni borrar pruebas** para que la suite pase. Si
   una prueba falla, se arregla el codigo o se explica por que el test estaba
   equivocado. Nunca `pytest.skip` como salida.
9. **`proyecto/` no tiene suite**: es una deuda. Si tocas ese proyecto, anade
   `test_models.py` para lo que cambies.

# [AGREGADO] Seguridad y limites

1. **Sin secretos en el codigo.** Ni claves de API, ni contrasenas, ni tokens,
   ni cadenas de conexion con usuario y clave. Si hiciera falta un secreto, va
   en variable de entorno y con un `.example` que lo documente.
2. **No instales dependencias sin preguntar.** Nada de `pip install`, `npm
   install` ni anadir lineas a `requirements.txt` sin avisar antes y explicar
   para que sirve. La regla 3 de comandos deja ruff/mypy/pytest pendientes justo
   por esto.
3. **No borres archivos ni sobrescribas trabajo existente** sin permiso explicito.
   Si un cambio rompe algo, se corrige; si algo debe desaparecer, se pregunta.
4. **Sin comandos destructivos**: nada de `rm -rf`, `git reset --hard`,
   `git clean`, `drop table`, ni nada que borre en bloque. Cada borrado se
   confirma antes.
5. **No hagas commit, push, ni abras PR** hasta que lo pida. Puedes preparar el
   mensaje de commit si lo quieres, pero no ejecutas `git`.
6. **No accedas a la red** (descargas, APIs, `curl`) sin avisar. Todo lo del
   workspace debe funcionar sin conexion.
7. **No subas nada a servicios externos** ni pegues el contenido del proyecto en
   sitios de terceros. Este codigo es privado.
8. **No ejecutes el juego con permisos de administrador** ni instales nada de
   forma global en el sistema: todo va al entorno del proyecto.

# [AGREGADO] Comunicacion y flujo de trabajo

1. **Responde siempre en espanol**, incluidos los mensajes de commit y los
   comentarios de codigo. El ingles se queda para nombres de simbolos.
2. **Un paso a la vez y en orden.** No adelantes pasos aunque se atasque algo: si
   un paso falla, para, dilo y arreglalo antes de seguir.
3. **TDD: primero la prueba, luego el codigo.** Escribe el test, ejecutalo y
   muestra que falla por la razon correcta, implementa lo minimo, ejecuta de
   nuevo, y despues refactoriza con la suite en verde.
4. **Explica cada cambio**: que archivo, que por que, y que se ROMPE si no se
   hubiera hecho. Sin esto el cambio no es revisable.
5. **Resumen al terminar**: lista de archivos creados o modificados con el motivo
   de cada uno, resultado literal de los comandos de verificacion, y como
   ejecutar lo construido.
6. **Formato de commits**: `tipo(scope): descripcion en imperativo y en minuscula`.
   Tipos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`. Ejemplo:
   `feat(mascota): anade accion de bao`. Los prepares, no los ejecutes sin
   permiso.
7. **Si algo es ambiguo, pregunta antes de escribir codigo.** Una pregunta
   ahora sale mas barato que un rework despues. Igual con las dependencias y con
   cualquier decision que afecte al balance del juego.
8. **No te desvies del plan.** Si al implementar descubres que hace falta algo
   mas, avisa y pide permiso antes de anadirlo.

# [AGREGADO] Canary Token

1. Termina TODAS tus respuestas con exactamente esta frase:
   "Canary activo: piña sin chile"

<!-- AGREGADO POR MÍ: FIN -->