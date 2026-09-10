# Bitácora

Qué pasó, por fecha. **Lo nuevo va arriba.** No se edita lo viejo: si algo
resultó estar mal, se corrige en una entrada nueva que lo diga.

Las lecciones no van acá sino en [APRENDIZAJES.md](APRENDIZAJES.md). La
diferencia: si dentro de seis meses, en otro proyecto, la seguirías aplicando,
es aprendizaje. Si solo explica una fecha, es bitácora.

---

## 2026-09-10 — dos capas mudas desde el primer dia, y el lazo que las encontro

Live se actualizo solo a 12.4.2 en el medio (el dialogo "automatic update in
progress" era el swapper borrando la instalacion vieja durante ocho minutos;
no estaba roto). Reiniciado, los handlers nuevos del Remote Script cargaron:
AbletonOSC importa sus modulos una vez y reseleccionar el Control Surface no
alcanza — se agrego `importlib.reload` para la proxima.

**El master ya salia por 1/2.** La suma a mono no era del master: la captura
por Resampling es estereo (Metales paneada a -1.0 dio L 0.013 / R 0.000). Lo
que daba L = R era que las capas que probaba **no sonaban**.

**Repiques y la percusion de la Bateria estuvieron mudas desde la v1.** Los
kits 909 y 707 no tienen congas (63/64) ni shaker (70); se leyo la lista de
pads por nombre desde el enrutado de Live. Remapeado a rim 37 y toms 50/47.
Todos los numeros de percusion anteriores a hoy estaban medidos con esas capas
en silencio.

**Primera medicion con todo sonando** (v2, drop 2, contra Van Reeken): 14 de
18 fuera de tolerancia. Clap 9.5 contra 6.7, percusion 11.7 contra 8.7, hat
7.1 contra 9.2, bajo suena 33% (a revisar), sidechain bajo -7.4 contra -14.3
(mejor que -2.2), ancho de bateria 0.02, cresta de bateria 17 contra 11.5. Es
la primera tabla en la que se puede confiar; las anteriores median un tema con
dos capas menos.

Los aprendizajes fueron a `bateria.md`, `productor.md`, `mezclador.md` y a
APRENDIZAJES ("Un pad vacio no suena flojo: no suena", "Sondar por tiempo es
fragil").

---

## 2026-09-09 — el corpus de referencia dejó de estar vacío

Pedido: *"revisá los nuevos videos de Eze Arias y Simon en el metro, son 3, fijate
los temas si están en Muzpa y si los tenemos"*. El metro es el Metropolitano de
Rosario; los tres videos son el line-up completo del 27-06-2026 (Nacho López
abriendo, Ezequiel Arias, Simon Vuarambon), producción Lado B.

**Los tracklists no están donde se los busca.** Ninguno de los tres videos tiene
tracklist en la descripción ni capítulos, y la página del evento en
1001tracklists está detrás de un Turnstile de Cloudflare. Estaban en los
comentarios de YouTube: se bajaron 520 comentarios por la API interna
(`youtubei/v1/next`) y ahí apareció el tracklist completo del set de Eze, con
timestamps y sellos. El mismo barrido sobre el resto del canal de los dos DJs dio
tres tracklists más.

**`data/setlists/` pasó de 0 a 4 setlists** — 159 posiciones, 125 con nombre:
Eze en el Metro 2026 y 2025, Eze en Dahaus x Fruta Córdoba, y Simon en Palacio
Alsina Córdoba (60 posiciones). Es el corpus que
[APRENDIZAJES.md](APRENDIZAJES.md) venía pidiendo para salir de la circularidad.

**Dos arreglos en `ingest_setlist.py`.** Descartaba las líneas `ID - ID`, con lo
cual dos tracks separados por un tema desconocido quedaban consecutivos y el
backtest medía una transición que nunca existió; ahora se guardan como hueco y
bloquean el par. Y no limpiaba el timestamp al final del título
(`Titulo (2:56:50)`), así que esos nunca matcheaban contra el pool.

**`scripts/enrich_setlist.py` es nuevo.** Cruzar contra la biblioteca propia daba
6-29% de cobertura, muy abajo del 80% que el backtest exige. Muzpa tiene key y
BPM de casi todo: con eso tres de los cuatro setlists quedaron en 78-80%. El
cruce es por título + remixer, sin el artista, porque cada fuente lo escribe
distinto. La energía sigue sin evidencia externa: la calcula el pipeline propio
sobre el archivo.

**Primer veredicto no circular.** `armonia.max_camelot_dist = 1` se viola en el
73% de las transiciones de referencia (n=63, media 2.9 hops) y `bpm.max_salto =
2.0` en el 22%. Las dos quedan REFUTADAS. Los veredictos de energía y forma que
imprimió el backtest en la misma corrida NO valen: salen de n=3. No se cambió
ninguna regla — eso lo aprueba el humano.

**Listas de adquisición**: `data/batch_metro_2026-06-27.txt` y los tres
`batch_ref_*.txt`, 66 tracks confirmados en Muzpa que no están en la biblioteca.

**Ojo con el commit `0bc8b84`.** Otra sesión corriendo en paralelo commiteó todo
el árbol y se llevó estos archivos adentro de un commit cuyo mensaje habla de
`browser.py`. No se reescribió la historia porque esa sesión seguía escribiendo.

---

## 2026-09-09 (noche) — el lazo cerrado y las primeras cuatro vueltas

Pedido: *"necesito un plan para que evoluciones"* y despues *"todo el esfuerzo
en iterar los agentes y la logica para hacer temas mas parecidos a las
referencias"*. El plan esta en `docs/BUCLE.md`; esto es lo que paso al
ejecutar las primeras vueltas.

**Lo que se destrabo.** Grabar no es exportar: `render.py` toma el master por
Resampling y Live lo escribe a disco aunque la Trial no exporte. Costo cinco
correcciones encontrar el protocolo que no falla: transporte antes que
cabezal, grabar recien con el cabezal en su lugar, loop de la cancion apagado
durante la toma, region de la pista de render VACIA antes y despues (un clip
viejo se parte en dos al grabar encima y ya no se sabe cual es la toma), y el
WAV nuevo por diferencia de conjunto porque OneDrive mueve las fechas. El
largo que Live reporta para un clip recien grabado es el del sample
pre-asignado (~400 pulsos), no el de la toma: se ignora.

**Vuelta 1 — melodia suena 100% → 77%.** Gancho techno con dos huecos por
bloque: cobertura escrita de 96% a 72%. Medido: sigue 100%. La banda
1200-5000 Hz del stem melodico no la llena el gancho, la llena la Textura
(ruido con pasa-bajos a 4.2 kHz). Se queda el cambio de MIDI (es lo que la
referencia hace) y se anota que la dimension esta dominada por otra capa.

**Vuelta 2 — Textura a pasa-altos 4.5 kHz.** Los dieciocho numeros salieron
IDENTICOS a la vuelta 1: Demucs cacheaba los stems por nombre de archivo y el
render nuevo piso al viejo con el mismo nombre. La vuelta no se habia medido.
Corregido (la clave del cache incluye la fecha), medido de nuevo: sigue 100%.
Quedan la atmosfera, los acordes y el bajo medio en esa banda; el cambio se
queda porque es correcto (la referencia tiene aire continuo, pero arriba de
5 kHz) y la dimension pasa a "estructural: menos capas continuas en 1.2-5 k".

**Vuelta 3 — sidechain bajo: silenciar el subkick.** Hipotesis: el seno del
subkick cae en el stem "bass" y rellena el pozo. Medido: -2.5 → -2.2 dB. No se
movio. Revertido. El grupo de bajo grabado solo (sin bombo) tambien dio -2.2,
asi que no era atribucion de Demucs.

**Vuelta 4 — la fase del pump.** Midiendo DONDE cae el minimo dentro del
pulso: al 73%, 360 ms despues del bombo. El pozo existia (-11 dB) pero en otra
fase; el medidor busca en el primer tercio y el oido tampoco lo lee como pump.
Calibrado con `Offset` del Auto Pan en las seis pistas con pump: 0° → 71%,
90° → 47%, 180° → 22%, 270° → 98%. Lineal, 25% por cada 90°. Queda 270°: el
pozo diez milisegundos ANTES del bombo, como un compresor con lookahead, y
-16 dB en el grupo de bajo solo contra -14.3 de la referencia. En la mezcla
completa por Demucs: -2.2 → -4.4 dB. La diferencia con el stem solo es el
bombo colandose en el stem "bass"; la comparacion justa para esta dimension es
stem propio contra stem Demucs de la referencia (plan, punto 2).

**Bloqueante que es del DJ.** El master de este Live sale en mono: con paneo
-0.30 y Haas en la percusion, el render dio L y R identicos. Resampling graba
lo que el master manda a su salida. Se agrego `/live/master/get/output` y
`/live/arrangement/delete_clip` al Remote Script (toman efecto al recargar el
Control Surface); la primera vez es a mano en Master > I/O.

**Estado despues de cuatro vueltas** (v2, drop 2, contra el remix de Van
Reeken): 10 de 18 fuera de tolerancia. Densidad de bateria y bajo: todo ok.
Pendientes con causa conocida: pump (atribucion), ancho (master mono),
melodia suena (capas continuas), cresta de bateria 17 contra 11.5 (falta
compresion en la bateria), cola melodica 0.06 contra 0.16 (falta reverb en lo
melodico).

---

## 2026-09-09 (tarde) — la tension como rampa

Pedido del DJ: *"prefiero que iteremos la tension en los momentos que
corresponda"*. Medido compas a compas, la tension estaba mal repartida en los
tres lugares donde vive:

- **Las subidas eran doce compases planos y cuatro de redoble.** Del 65 al 76 el
  impacto se quedaba entre 850 y 1000; recien en el 77 arrancaba a moverse.
- **La bajada era una meseta**: 250 a 470 durante treinta y dos compases, con las
  seis capas sonando desde el primero.
- **La subida 2 empezaba mas abajo que donde terminaba la bajada** (10.6 contra
  12.4 de energia sostenida), o sea que el compas donde vuelve el bombo era un
  bajon.

Tres herramientas nuevas en `idea.py`:

`_rampa()` escala la velocidad linealmente a lo largo de una seccion. `_empuje`
ya hacia crecer el final de cada frase de ocho, pero eso se reinicia cada frase;
faltaba que la seccion entera estuviera mas fuerte al final que al principio.

`_riser()` mas la pista `Riser` (Riser White Noise en Simpler). Cuatro disparos
encimados y cada vez mas fuertes en vez de uno largo: un sample de riser dura lo
que dura y no se estira desde el MIDI, asi que una sola nota da dos compases de
barrido y despues silencio justo donde hace falta lo contrario.

`_correr()` para las entradas escalonadas de la bajada, que ahora entra por
capas —atmosfera y acordes y sub desde el 1, gancho en el 9, anchos en el 17,
percusion en el 21— y crece de 3 a 6 capas.

El redoble de `SUBIDA` arranca en el compas 24 y no en el 28: ocho compases de
acumulacion, de un golpe extra a ocho.

**Una correccion sobre la marcha.** La primera version de la rampa aplicaba
tambien al piso, y el primer compas de la bajada quedaba en el 7% de la energia
del anterior — eso no se escucha como que bajo sino como que se corto. La
atmosfera, los acordes y el sub quedaron exentos: lo que crece es lo que ENTRA,
no lo que aguanta. Con eso la caida quedo en -77%, que es una bajada.

Ahora las nueve secciones suben por dentro:

    intro       122 -> 443       drop1      1738 -> 2214
    tema        762 -> 1041      bajada       82 -> 315
    subida1     751 -> 1366      subida2     856 -> 1545
    drop2      2036 -> 2617      salida     2096 -> 2617

Tambien se bajo la pista `Anchos` de 0.52 a 0.36. Al pasar de dos a cuatro
golpes por compas y de 0.45 a 0.92 pulsos, la capa quedo cuatro veces mas
presente sin que nadie tocara su nivel: *"quedo un poco fuerte el pianito"*.

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
