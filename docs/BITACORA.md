# Bitácora

Qué pasó, por fecha. **Lo nuevo va arriba.** No se edita lo viejo: si algo
resultó estar mal, se corrige en una entrada nueva que lo diga.

Las lecciones no van acá sino en [APRENDIZAJES.md](APRENDIZAJES.md). La
diferencia: si dentro de seis meses, en otro proyecto, la seguirías aplicando,
es aprendizaje. Si solo explica una fecha, es bitácora.

---

## 2026-09-08 (tarde) — de medir a componer

**Qué se hizo**

Se armó el tema de 240 compases con la plantilla medida, se lo auditó con el
`curador`, se aplicaron sus siete correcciones — y despues se lo tiró. El DJ
dijo *"no le encuentro sentido al tema, no es warm no es peak, es raro"* y
despues *"la música no me dice nada"*.

El diagnóstico: estaba compuesto desde la mediana de todo el repertorio, y la
mediana de todo no es ningún momento de la noche. Se cambió la estrategia a
`scripts/idea.py`: 32 compases, una sola idea, dicha de entrada. La semilla no es
una estadística sino la célula rítmica del bajo de `Moonflare` y, en la iteración
siguiente, la frase de cuatro compases de `Sunset Love` con su acorde iv.

Se agregó `src/plomo/humano.py` — humanización por rol, con dirección — y el
agente `musico`, que existe justamente porque el proyecto sabía medir y no sabía
componer.

**Qué se decidió, y por qué**

Un artefacto se hace para un momento concreto, no para la mediana. La mediana
sirve para descartar familias enteras, no para escribir.

Los bocetos pasan a durar un minuto. Uno de ocho minutos no se puede iterar:
para cuando termina ya no te acordás del principio.

**Qué se rompió y cómo se arregló**

- El gancho decía entrar en el compás 5 y entraba en el 2: se sumaban 4 a una
  variable en PULSOS creyendo que estaba en compases. Lo encontró el auditor, no
  una medición.
- 67% de los compases eran idénticos al de 8 antes. El primer intento de
  variación alternaba por compás par y no cambió nada — 8 es par. Con período 16
  quedó en 0%.
- 6 de 11 secciones caían fuera de la grilla de 16 por una sola fila de 8
  compases que corría todo lo posterior medio período de fraseo.
- El riser fuerte iba al primer drop y no al segundo, porque la comparación era
  con `"Drop"` y nunca matcheaba `"Drop 2"`.
- La capa que sostiene tenía 7 huecos de 146 ms, uno en cada frontera de sección,
  y reatacaba al descubierto. Lo encontró el `musico`.
- Los hats estaban en la semicorchea justo ANTES de cada pulso: no se escuchaban
  como hat sino como un adelanto del golpe.
- La medición de estructura de los temas de peak falló —devolvió "1 compás" para
  los siete— porque se leyó mal el esquema del JSON. Lo que se dijo sobre
  estructura de peak es criterio, no medición.

**Qué quedó pendiente**

- El loop de 32 compases todavía no se llevó de vuelta a un tema largo. El orden
  correcto es ese: primero que la idea funcione, después el arreglo alrededor.
- Los tresillos de conga contra las semicorcheas del hat: poliritmia deliberada,
  y lo único que el `musico` marcó como posible aspereza restante.
- El agente `musico` no aparece en el registro hasta reiniciar la sesión.

## 2026-09-08 — producción: de la síntesis propia a Live, y de la opinión a la medición

**Qué se hizo**

Se abandonó la síntesis propia de `render_sketch.py` como forma de escuchar un
boceto y se construyó la capa para operar Ableton Live por código:
`src/plomo/live.py` sobre AbletonOSC, más la extensión propia `browser.py` del
Remote Script —que AbletonOSC no traía— para cargar instrumentos y samples.

Se instaló Demucs en `.venv-demucs`, un entorno aparte con CUDA, y con eso se
volvió posible transcribir temas reales a MIDI (`separar.py`, `copiar_tema.py`).

Con los stems se midió el repertorio propio: densidad de arreglo
(`medir_arreglos.py`), color del timbre melódico (`color_melodico.py`),
percusión de adorno (`repiques.py`). Los resultados reescribieron
`make_sketch.py` entero.

Se armó el primer tema completo: `extender.py` expande un loop de 8 compases a
240 con secciones, riser, redoble y doblajes por octava.

Dos agentes corrieron en paralelo: `research` produjo el informe de Live que
reescribió `.claude/agents/productor.md`, y `productor` produjo
[MI_SONIDO_PRODUCCION.md](MI_SONIDO_PRODUCCION.md) con un grupo de control de 20
temas nunca tocados.

Se creó `arquetipo/`, para que el método sea reusable en otros proyectos.

**Qué se decidió, y por qué**

El boceto se escribe con la densidad medida, no con criterio. La versión vieja
ponía 44 notas por compás contra las 17.7 de los temas que se tocan.

La estructura del tema sale de la plantilla medida: 240 compases, breakdown de
32 arrancando en el 120. No es un promedio — 16 de 41 temas caen exactamente ahí.

El swing quedó en 0 por defecto: nunca fue el problema y no hay nada medido que
lo justifique.

**Qué se rompió y cómo se arregló**

- Los cinco clips se cargaban con cinco largos distintos (8.15, 7.99, 7.93, 7.98,
  7.78 compases), así que arrancaban juntos y se separaban en cada vuelta. Se
  escuchaba como destiempo y era aritmética. Ahora un solo largo, en compases
  enteros.
- `create_clip` sobre un slot ocupado no reemplaza: tira error y sigue, y las
  notas van al clip viejo. Ahora `cargar_midi` borra primero.
- `nombre_pista` leía `[0]` de la respuesta, que es el índice de pista y no el
  nombre. Los getters de pista contestan `(indice, valor)`; los de song, solo el
  valor.
- El fallback de batería era `"Drums Warm & Wide"`, que es un Audio Effect Rack
  de bus y no un kit: habría cargado una cadena de efectos en una pista MIDI.
- `_buscar()` de `medir_arreglos.py` cruzaba por subcadena y devolvía la versión
  equivocada — "Cardamom (Original Mix)" traía el FAERO Remix. Ahora usa
  `plomo.matching.clave`, que conserva el remixer.
- `data/mi_sonido.json` decía 1004 reproducciones y son 510. El fix del doble
  conteo estaba en el código pero el JSON nunca se había regenerado, porque el
  script solo escribe con `--json`.

**Qué quedó pendiente**

- Probar `clip.create_automation_envelope()` desde el Remote Script. Max for Live
  lo bloquea con una lista blanca, pero un Remote Script no pasa por `MxDCore`.
  Si funciona, se puede escribir automatización — el filtro que se abre en el
  breakdown, que hoy es imposible.
- Handler de return y master tracks: todo `track.py` itera `song.tracks`, así que
  un return creado queda inalcanzable.
- `duplicate_clip_to_arrangement`, para que `extender.py` escriba en la línea de
  tiempo y no en clips de Session.
- La densidad de onsets de `reverse_engineer.py` **satura** (techo del detector
  en 16.1 por compás): no sirve para comparar tracks entre sí.
