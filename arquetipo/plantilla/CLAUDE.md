# Reglas de {{NOMBRE}} — para Claude

<!-- Este archivo se lee entero en cada sesión. Mantenelo corto: si crece a más
     de una pantalla, lo que sobra va a docs/ y acá queda el puntero. Una regla
     que nadie lee no es una regla. -->

## Qué es esto

{{DESCRIPCION}}

## Lo que no se hace

<!-- Las prohibiciones van primero y con su motivo. Una prohibición sin motivo
     se saltea la primera vez que estorba. -->

- **Decir "no se puede" sin agotar los descartes**: probar la versión nueva de la
  API o el flag, separar el síntoma de la explicación, probar la operación mínima
  aislada, buscar otro camino. Recién ahí, y diciendo con qué se probó y qué
  devolvió cada cosa. Una conclusión negativa escrita no se revisa sola.
- **`sys.path.insert(0, "src")` en un script**: es relativo a donde uno está
  parado y falla justo cuando se corre desde otro lado. El paquete se instala
  (`pip install -e .`).
- **Cambiar una regla a medias**: valor, evidencia, historial, versión y tag van
  en el mismo commit (`R.proponer` → aprobación → `R.aplicar`).
- 

## Cómo se decide

Los criterios viven en `rules/criterio.json` y se leen con
`from {{PAQUETE}}.criterio import R`. Cada uno lleva su **valor**, su **porqué** y
su **evidencia**. Para cambiar uno hace falta una medición, no una impresión.

Una regla marcada `PENDIENTE` en evidencia está sin medir: se puede usar, pero
no se puede defender. Una regla que ningún código lee (`R.sin_lector()`) o que se
lee con el número escrito a mano al lado es peor que no tenerla.

## Cómo se mide

Cuatro corpus, y confundirlos invalida todo:

- **PROPIO** — lo que produjo el sistema. Si el sistema impone la regla, medirla
  contra su propia salida siempre la confirma. **No prueba nada.**
- **USADO** — lo que efectivamente se eligió usar. Matiza; no refuta.
- **CONTROL** — lo comparable que **no** se eligió. Convierte una descripción del
  dominio en una preferencia.
- **REFERENCIA** — lo que hacen otros que saben. Es el único que **refuta**: si lo
  viola seguido y funciona, la regla es autoimpuesta, no una ley del dominio.
  Una regla marcada `decision_humana` no se refuta así: es un gusto, no una
  hipótesis.

Toda herramienta que produzca algo para que una persona lo evalúe **verifica su
propia salida y reporta el chequeo**, también cuando sale bien. El chequeo mira
lo que va a recibir la persona —el cuadro, el audio, la página—, compara contra
la fuente y no contra un paso propio, y dice lo que no pudo aplicar.

## Cómo se trabaja

- **Lo que dice la persona se anota literal.** Lo que no dijo no se supone: se
  deja vacío o se pregunta. Lo que sale a su nombre va en su voz, sin hechos
  que no dijo, y queda en privado hasta su OK.
- **La fuente se lee en el momento.** Cada número vive en un solo lugar. Lo que
  la persona también edita se lee antes de escribir —si no es lo último que
  escribiste, es suyo y no se pisa— y se relee después: aceptar un cambio no es
  haberlo aplicado.

## Estructura

Detalle en `docs/ARCHITECTURE.md`. `src/{{PAQUETE}}/` lo que se importa y se
testea · `scripts/` lo que se corre · `scripts/archive/` los one-offs ya
ejecutados (**no se borran**: son memoria) · `rules/` los criterios · `data/` lo
medido y chico (lo pesado y el scratch los ataja `.gitignore`) · `docs/`
bitácora, aprendizajes y `METODO.md` · `.claude/` un agente por dominio y los
flujos con `/`. Raíz: solo configuración (lo chequea `tests/test_estructura.py`).
Archivos de 200-400 líneas, 800 como máximo.

## Bitácora y aprendizajes

Al cerrar una sesión con algo sustantivo: entrada en `docs/BITACORA.md` (arriba,
con fecha). Si además apareció algo que seguirías aplicando en otro proyecto
dentro de seis meses, va también a `docs/APRENDIZAJES.md`.

Son dos archivos distintos a propósito. La bitácora explica una fecha; el
aprendizaje sobrevive al proyecto.
