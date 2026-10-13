---
name: texto-con-tema
description: Use ONLY when the user asks to reescribir el texto de un proyecto (comentarios, docstrings, prints, logs, mensajes de error, textos de la UI) segun un tema, manteniendo intacto el codigo - Spanish "tematizar", "reescribir los textos con tema", "poner los comentarios en plan pirata/medieval/espacial", English "theme the comments/text", "rewrite all non-code text with a theme", "pirate/medieval/space themed comments". Applies a chosen theme (default cientifico-lunar) to everything that is not code, verifies with an AST checker and the test suites that code did not change, and auto-reverts + self-improves on any failure. Do not use to translate comments to English (use comentarios-a-ingles) or to change logic.
---

# Texto con tema

Reescribe **todo el texto que no es codigo** (comentarios, docstrings, `print`,
`logger`, mensajes de error, textos de la interfaz) aplicando un tema. El codigo
—logica, identificadores, numeros, operadores, control de flujo— debe quedar
**byte a byte igual**. La skill se prueba a si misma y, si toca codigo, revierte
y se corrige sola.

## Tema

- Tema por defecto: **cientifico-lunar** (naves, orbita, gravedad cero, alienigenas).
- Si el usuario pide otro tema (pirata, medieval, ...), usa ese.
- El tema se aplica solo al **texto humano**. No inventes nombres de simbolos.

## Alcance

Todos los `**/*.py` del proyecto o carpeta indicada, **incluidos** los
`test_*.py`, `tests/` y modulos sueltos de la raiz. Excluye siempre
`.git`, `.venv`, `venv`, `__pycache__`, `.mypy_cache`, `.pytest_cache`,
`.ruff_cache`.

## Se tematiza

- Comentarios `#` (de linea y inline) y bloques de comentarios.
- Docstrings de modulo, clase, funcion y metodo (incluidas las secciones
  `Args:`, `Returns:`, `Raises:` y el bloque de ejemplo).
- Textos humanos: `st.title/caption/markdown/button/error/success/...`,
  mensajes de `game/`, `logger.*`, `print(...)` (incluidos los `print("OK ...")`
  de los tests).

## NUNCA se toca (es codigo)

- Identificadores, imports, numeros, operadores, decoradores, firmas,
  `from __future__ import annotations`.
- Placeholders de formato (`%s`, `%d`, `{...}`, `{:>10}`) y las expresiones
  dentro de f-strings: en `f"Hola {nombre:.2f}"` solo cambia `Hola `.
- Secuencias de escape (`\n`, `\t`, `%`, `{}`) y el numero de argumentos de un
  `logger`/`format`.
- Strings funcionales (no son texto para el usuario):
  claves de `dict`, de `config`, de `st.session_state`, de widgets (`key=`),
  valores de `Enum` que se comparan, `COLOR_CSS` (`"verde"`, `"amarillo"`,
  `"gris"`, `"vacia"`), clases CSS (`casilla`, `tecla`, `map-panel`,
  `story-panel`), `game.status == "won"`, `encoding=`, rutas y nombres de
  fichero.
- Emojis que usa la logica: `mascota` los assertiona
  (`test_juego.py` comprueba `emoji() == "??"` y que el emoji cambie). No los
  sustituyas por iconos del tema.
- Bloques de doctest (`>>> ...` y su salida esperada): son codigo ejecutable.

## Excepciones conscientes de este workspace

1. **`ejemplo_prueba.py` se queda ASCII** (sin tildes ni enye). Hay un test de
   guarda (`test_...esta escrito sin tildes ni enyes`) que lo exige. El tema
   ahi se escribe sin acentos.
2. **Tests acoplados**: cuando un `test_*.py` comprueba el **contenido** de un
   mensaje (por ejemplo `tests/test_ejemplo_prueba.py` comprueba `"vacia"`,
   `"etiqueta"`, `"peso"`, `"informe"`, `"victoria"`, `"turno N"` y el formato
   `"pulso: 70.0 (peso 1.0)"`), se tematiza **el modulo y el test a la vez**,
   reescribiendo la asercion para que siga comprobando la misma propiedad con
   el texto nuevo. No se desactiva ni se borra ninguna prueba.
3. **Emojis**: ver arriba, son carga funcional.

## Flujo (sigue el orden, no adelantes pasos)

1. **Confirmar** tema y alcance. Si el arbol git no esta limpio, avisar antes
   de tocar nada (para poder distinguir tus cambios de los previos).
2. **Baseline**: corre las suites y guarda la salida. Si la baseline ya esta en
   rojo, **detente** y dilo.
   - `mascota/`: `python test_juego.py`
   - `wordle/`: `python test_wordle.py`
   - `tests/`: `python tests/test_ejemplo_prueba.py` (desde la raiz)
   - `proyecto/`: sin suite; anotalo.
3. **Respaldar**: copia cada archivo que vayas a tocar antes de editarlo:
   `Copy-Item -LiteralPath <archivo> -Destination "$env:TEMP\opencode\tema-backup\<ruta-relativa>" -Force`
4. **Clasificar**: por archivo, separa strings de texto humano de strings
   funcionales (lista de arriba). Ante la duda, tratalo como funcional.
5. **Editar** con `Edit`, respetando: significado y **por que** del comentario,
   estructura del docstring, emojis, placeholders y la regla ASCII de
   `ejemplo_prueba.py`. Tematiza tests acoplados en el mismo paso que su modulo.
6. **Capa 1 (AST)**: por cada archivo modificado, ejecuta:
   `python .opencode/skills/texto-con-tema/scripts/verificar_solo_texto.py "<respaldo>" "<archivo>"`.
   Debe imprimir `OK`. Si imprime `FAIL`, el codigo cambio: ve al paso 9.
7. **Capa 2 (compila)**: `python -m py_compile <archivo>` por cada archivo.
8. **Capa 3 (suites)**: repite las suites del paso 2. Todas verdes -> paso 10.
9. **Undo + auto-mejora** (si fallo la capa 1, 2 o 3):
   - Restaura el archivo desde su respaldo:
     `Copy-Item -LiteralPath "$env:TEMP\opencode\tema-backup\<ruta>" -Destination "<archivo>" -Force`
   - Anota la causa real (que string era funcional, que placeholder se rompio).
   - **Mejora esta skill**: anade al `SKILL.md` la regla que faltaba para que el
     error no se repita.
   - Reintenta desde el paso 4. No uses `git reset`, `git clean` ni nada
     destructivo.
10. **Reportar**: lista de archivos con el numero de bloques tematizados,
    salida **literal** de las suites corridas, y cualquier texto dejado igual a
    proposito y por que. Borra los respaldos.

## Reglas duras

- La capa 1 (AST) prueba que no cambio el codigo; las capas 2 y 3 cubren los
  strings funcionales que el AST no distingue.
- Nunca temas los textos de los pasos 1-3 del flujo (mensajes de salida de
  tests, rutas, claves).
- No ejecutes `git` (commit, push) sin peticion explicita.
- No borres archivos ni desactives pruebas para que la suite pase.

## Registro de mejoras

(aqui la skill anota, cada vez que se corrige, la regla que se anadio)

- (vacio)
