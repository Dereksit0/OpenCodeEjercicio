---
name: comentarios-a-ingles
description: Use ONLY when the user asks to analyze the whole codebase and translate its code comments or docstrings into English (Spanish - "traducir comentarios al ingles", "pasar los comentarios a ingles", "cambiar docstrings a ingles"; English - "translate comments to English", "convert comments/docstrings to English", "English comments"). It walks every source file, translates inline comments and docstrings without changing behavior, and verifies the project tests still pass. Do not use for translating user-facing UI strings, error messages, identifiers, or converting code to another language.
---

# Comentarios a ingles

Traduce al ingles los **comentarios y docstrings** de un proyecto Python, sin
cambiar una sola linea de comportamiento. Pensada para ejecutarse sobre un
directorio entero y dejar el codigo listo para revisar.

## Advertencia de conflicto

Este workspace (`AGENTS.md`) exige docstrings y comentarios **en espanol**.
Esta skill hace lo contrario a proposito, solo cuando el usuario la invoca de
forma explicita. No edites `AGENTS.md` como parte de esta tarea salvo que el
usuario lo pida.

## Alcance: que SI y que NO

**SI se traduce:**

- Comentarios de linea (`# ...`), incluidos los inline al final de una linea.
- Bloques de comentarios consecutivos.
- Docstrings de modulo, clase, funcion y metodo, incluida la estructura Google
  (`Args:`, `Returns:`, `Raises:`, y el bloque `Ejemplo:` / `Example:`).
- Comentarios dentro de `test_*.py`.

**NO se toca:**

- Identificadores (nombres de variable, funcion, clase, modulo, argumentos).
- Strings de la interfaz de usuario (textos de Streamlit, mensajes de error
  visibles, valores de `Enum` que el usuario lee, `page_icon`, emojis).
- Codigo, numeros, imports, decoradores, firmas y anotaciones de tipo.
- `from __future__ import annotations` y cualquier linea ejecutable.

En caso de duda sobre si un string es "comentario" o "interfaz", **pregunta**;
no inventes.

## Paso a paso

1. **Descubrir archivos.** Recorre los `**/*.py` del proyecto o directorio que
   pida el usuario. Excluye siempre:
   `.git`, `.venv`, `venv`, `__pycache__`, `.mypy_cache`, `.pytest_cache`,
   `.ruff_cache`, y cualquier carpeta de dependencias.
   Si el usuario no acoto la ruta, lista primero los archivos encontrados y
   confirma el alcance antes de editar.

2. **Inventariar.** Por archivo, localiza cada comentario y docstring y
   clasificalo (modulo, clase, funcion, metodo, inline). Un archivo sin
   comentarios en espanol se salta sin editar.

3. **Traducir.** Aplica `Edit` bloque a bloque. Reglas:
   - Traduce el **significado**, no palabra por palabra; el comentario debe
     seguir explicando el **por que** (invariante, caso limite, decision no
     obvia), no repetir lo que la linea ya dice.
   - Manten la estructura del docstring: mismas secciones, mismo orden y misma
     sangria que la version original.
   - Conserva emojis, simbolos y bloques de codigo embebidos.
   - No pases de **88 caracteres** por linea (limite de `ruff format`).
   - Usa ingles tecnico natural; nada de traducciones rigidas.
   - No reescribas el archivo completo si basta con editar los comentarios.

4. **Verificar.** Ejecuta la suite del proyecto afectado y **pega el resultado
   literal**; no digas "funciona" sin haberlo corrido:
   - `mascota/`: `python test_juego.py`
   - `wordle/`: `python test_wordle.py`
   - `proyecto/`: sin suite. Si tocas logica acompana un test; si solo
     tradujiste, dilo.
   - `ruff` / `mypy` no estan instalados: revision manual, no los asumas.

5. **Reportar.** Cierra con:
   - Lista de archivos modificados y cuantos bloques en cada uno.
   - Resultado literal de los tests corridos.
   - Cualquier texto que hayas dejado en espanol a proposito y por que.

## Reglas duras

- **Cero cambios de comportamiento.** Si un test falla despues del cambio, algo
  se tradujo demas: revierte ese bloque, no "arregles" el test.
- **No ejecutes `git`** (commit, push, reset) sin peticion explicita.
- **No borres archivos ni sobrescribas** trabajo existente fuera de los
  comentarios y docstrings.
- Si el usuario pide tambien traducir la interfaz o los mensajes de error, eso
  queda **fuera** de esta skill: avisa y confirma antes de hacerlo.

## Ejemplo

Antes:

```python
def aumentar(self, cantidad: int) -> None:
    """Sube la estadistica sin pasarse del maximo.

    Args:
        cantidad: Cuanto sumar. Nunca negativo.
    """
    # Se recorta aqui para que el valor no salga del rango [0, maximo].
    self.valor = min(self.valor + cantidad, self.maximo)
```

Despues:

```python
def aumentar(self, cantidad: int) -> None:
    """Raise the stat without exceeding the maximum.

    Args:
        cantidad: How much to add. Never negative.
    """
    # Clamped here so the value never leaves the [0, maximo] range.
    self.valor = min(self.valor + cantidad, self.maximo)
```

Nota: los identificadores (`aumentar`, `cantidad`, `maximo`) y los valores de
rango **no** se traducen.
