# Reglas de {{NOMBRE}} — para Claude

<!-- Este archivo se lee entero en cada sesión. Mantenelo corto: si crece a más
     de una pantalla, lo que sobra va a docs/ y acá queda el puntero. Una regla
     que nadie lee no es una regla. -->

## Qué es esto

{{DESCRIPCION}}

## Lo que no se hace

<!-- Las prohibiciones van primero y con su motivo. Una prohibición sin motivo
     se saltea la primera vez que estorba. -->

- 

## Cómo se decide

Los criterios viven en `rules/criterio.json`, no en el código. Cada uno lleva su
**valor**, su **porqué** y su **evidencia**. Para cambiar uno hace falta una
medición, no una impresión.

Una regla marcada `PENDIENTE` en evidencia está sin medir: se puede usar, pero
no se puede defender.

## Cómo se mide

Tres corpus, y confundirlos invalida todo:

- **PROPIO** — lo que produjo el sistema. Si el sistema impone la regla, medirla
  contra su propia salida siempre la confirma. **No prueba nada.**
- **USADO** — lo que efectivamente se eligió usar. Sirve.
- **CONTROL** — lo comparable que **no** se eligió. Es el único que convierte una
  descripción del dominio en una preferencia.

Toda herramienta que produzca algo para que una persona lo evalúe **verifica su
propia salida y reporta el chequeo**, también cuando sale bien.

## Estructura

- `src/{{PAQUETE}}/` — módulos que se importan y se testean
- `scripts/` — lo que se corre desde la línea de comandos
- `scripts/archive/` — one-offs ya ejecutados; **no se borran**, son memoria
- `rules/` — los criterios como dato versionado
- `data/` — datos generados y medidos
- `docs/` — `ARCHITECTURE.md`, `BITACORA.md`, `APRENDIZAJES.md`
- `.claude/agents/` — un agente por dominio, no uno por tarea
- `.claude/skills/` — los flujos invocables con `/`
- Raíz — solo archivos de configuración

Archivos de 200-400 líneas, 800 como máximo.

## Bitácora y aprendizajes

Al cerrar una sesión con algo sustantivo: entrada en `docs/BITACORA.md` (arriba,
con fecha). Si además apareció algo que seguirías aplicando en otro proyecto
dentro de seis meses, va también a `docs/APRENDIZAJES.md`.

Son dos archivos distintos a propósito. La bitácora explica una fecha; el
aprendizaje sobrevive al proyecto.
