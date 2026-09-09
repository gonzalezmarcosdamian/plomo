# Bitácora

Qué pasó, por fecha. **Lo nuevo va arriba.** No se edita lo viejo: si algo
resultó estar mal, se corrige en una entrada nueva que lo diga.

Las lecciones no van acá sino en [APRENDIZAJES.md](APRENDIZAJES.md). La
diferencia: si dentro de seis meses, en otro proyecto, la seguirías aplicando,
es aprendizaje. Si solo explica una fecha, es bitácora.

---

## 2026-09-09 — version 1 del tema, de 112 a 240 compases

**Que se hizo**

Se paso de un loop largo a un tema con forma. El disparador fueron dos frases
del DJ: *"hace que explote, que sumen cosas, no restes"* y despues *"dale
continuidad al tema con estructura que corresponda para un tema terminado"*.

Medido compas por compas, el arreglo de 112 compases tenia tres problemas y los
tres eran el mismo: del 17 al 60 habia SIEMPRE cuatro capas y el mismo peso —un
tercio del tema sin que entrara ni saliera nada—; en el 61-62 habia un pozo de
218 puesto a proposito "para que el drop pegue"; y en el climax el gancho se
callaba para dejarle lugar al arpegio, que no es sumar una capa sino cambiarla.
El drop era 1.7 veces la intro.

Se sumaron seis capas que no existian: `Sub` (fundamental sostenida), `Anchos`
(golpes de acorde dos octavas arriba, en las corcheas que los acordes dejan
libres), `Repiques` (segunda mano de percusion), `Splash` (cimbal 808 en pista
propia — el crash del 909 es una muestra de bronce y en un tema sintetico se
escucha como que entro un baterista), `Reversa` (el barrido que desemboca en el
golpe) y `Lead` (la figura dulce arriba de todo, solo en el segundo drop).

El pozo del 61-64 paso a ser un redoble que ACUMULA: sigue sonando todo y encima
entran golpes cada vez mas juntos, con el shaker cerrandose a semicorcheas.

**La forma, y de donde salieron los numeros**

Se escribio `scripts/estructura.py`, que faltaba: el proyecto sabia medir groove
sobre ocho compases y no sabia medir la FORMA de un tema entero. Clasifica cada
compas en BAJADA / GROOVE / TEMA / DROP con tres bandas y umbrales sacados del
propio tema, no absolutos.

Medidos Minicube, Go (HANA + Eze Arias) y Cryo: 7.2, 7.5 y 8.1 minutos; intro de
DJ de 16 a 32 compases; una bajada grande de 28 a 56 pasada la mitad; salida de
DJ de 24 a 32. De ahi salieron los 240 compases (7:48) y las nueve partes de
`FORMA` en `idea.py`.

`scripts/montar.py` pone las nueve carpetas en el arreglo. Lo primero que hace
es borrar el arreglo de cada pista con un clip vacio del largo del tema, porque
`duplicate_clip_to_arrangement` reemplaza lo que pisa pero no lo que no pisa: un
clip de la version anterior en un compas que la nueva no usa sobrevive y suena.

**Como quedo**

    compases    parte        impacto  capas
       1-32     intro            378    3
      33-64     tema             899    6
      65-80     subida1         1084  6-7
      81-112    drop1           1816  9-10
     113-144    bajada           246    6
     145-160    subida2         1233  6-7
     161-192    drop2           2147  10-11
     193-208    salida          2126  10-11
     209-240    salida_dj        577    4

El pico cae en el compas 168, adentro del segundo drop. El segundo drop mide
1.18 veces el primero: antes median 2097 y 2099, identicos al 0.1%, y dos drops
iguales no son dos drops.

**La auditoria, y los tres arreglos que salio**

`escuchar.py` sobre las nueve partes encontro un ALTO y dos MEDIO reales:

*El filtro de peine en las dos subidas.* Trece racimos de clap y shaker a menos
de 10 ms por seccion — el defecto que ya habia causado la queja "arenoso y a
destiempo". La causa: el redoble escribia un SEGUNDO shaker de dieciseis
semicorcheas encima del que el patron base ya tocaba, con otro perfil de
humanizacion. Dos capas en la misma grilla con distinto perfil es una capa
peleandose consigo misma. Se borro el duplicado y el shaker que ya estaba
aprieta subiendo de velocidad; los golpes del redoble pasaron al perfil
"percusion" para caer exactamente encima del shaker en vez de a unos ms.

*Los golpes anchos cubrian el 22% del tiempo* contra el 71-84% de las
referencias. Se estiraron a 1.30 pulsos y en el climax pasaron a los cuatro
contratiempos en vez de dos, que es lo que significa que un acorde se abra.

*Y ahi el instrumento encontro un bug que la medicion sola no veia:* con cuatro
golpes por compas y 1.05 de duracion, cada acorde se solapaba con el siguiente
en la MISMA altura. En MIDI eso no sostiene, apaga — la nota real duraba 0.05
pulsos. Es la tercera vez que aparece este error en el proyecto, y la primera
que lo encuentra una herramienta en vez de un oido. Se bajo a 0.92, que es menos
que el hueco de 1.0 entre ataque y ataque.

Tambien se corrigio el instrumento: avisaba "puede sonar cortado" del platillo y
del barrido, que suenan una vez cada ocho compases POR DISENIO. Un instrumento
que avisa de lo que esta bien entrena a ignorarlo. Ahora exime a las capas de
menos de un golpe cada dos compases, por forma y no por una lista de nombres.

Quedan seis partes limpias de nueve. Las tres restantes —los dos drops y la
salida— avisan "en el limite de lo denso": 25.9 notas por compas contra 17.7
medido. Se deja como esta y anotado: la bateria da 18.8 por compas contra ~14 de
la referencia y el bajo 8.1 contra ~4, pero es material medido de Vuarambon y
del propio arreglo, y bajarlo es una decision del DJ y no del que mide.

**Lo que quedo pendiente**

No se exporto audio. El tema vive en el set de Live y en
`postproduction/bocetos/v1/`; para tener un archivo hay que renderizar a mano,
porque no hay handler de export en AbletonOSC.

La mezcla no se toco: los volumenes de las diecisiete pistas son los que
quedaron de cargarlas una por una, no una mezcla hecha.

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
