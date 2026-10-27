# Backlog

Lo pendiente que no es producción (para eso está [PLAN.md](PLAN.md)): sets, música,
reglas, medidas y arreglos del sistema. Cada ítem tiene de dónde salió y quién lo
resuelve. Se tacha cuando se hace, con el commit al lado; no se borra.

Prioridad: **A** cambia algo que el DJ va a tocar pronto, **B** mejora el criterio,
**C** es limpieza.

Fuentes de esta tanda (2026-10-22):
- La investigación del 158. El detalle y los links están en `data/research_b2b_2026-10.json`
  y en los 16 setlists nuevos de `data/setlists/`.
- Lo que se rompió armando el 158 entre el 20 y el 22 de octubre (ver
  [BITACORA.md](BITACORA.md)).

---

## 0. PRIMERO, la semana del 2026-11-02: eficiencia

"Corta el video aca, estas comiendo todos los tokens" (el DJ, 2026-10-26). Antes de seguir
con la Session 05 se baja el costo de trabajar con video. Lo medido ese día:

- el editor, en una vuelta de la hoja de recorrido: unos 380 mil tokens y 368 herramientas,
  con 66 clips bajados y mirados cuadro por cuadro;
- el revisor, sobre esa hoja: unos 230 mil tokens. Bloqueó por una estela de avión y por tres
  puestas de sol.

| # | Prio | Qué | Por qué | Quién |
|---|---|---|---|---|
| 0.1 | A | **Avisar el costo antes de lanzar un agente de video** y esperar el OK. | El DJ no lo veía venir. Ya está en la memoria (`feedback_tokens_video`). | yo |
| 0.2 | A | **Que las revisiones a 1:1 las haga un script, no el agente mirando.** Estelas y aviones (líneas rectas finas en el cielo), sol tocando el horizonte (el punto más brillante contra la línea), gente y construcciones. El agente mira solo lo que el script marca. | Casi todo el gasto es mirar cuadros. El revisor encontró a 1:1 una estela que el editor no vio. | tecnico + editor |
| 0.3 | A | **Encargos chicos y con tope**: elegir con hojas de miniaturas, bajar y mirar a 1:1 solo los 4 que van a la hoja, una vuelta por encargo. | 46 de los 66 clips bajados se descartaron. | yo |
| 0.4 | B | **Modelo por tarea**: buscar y bajar clips no necesita el modelo más caro (el editor corre en opus). El criterio sí. | Separar la tarea mecánica del juicio. | yo |
| 0.5 | B | **Imágenes más chicas para mirar**: las hojas de 3000 px se leen enteras; recortar por etapa o achicar. | Cada lectura de imagen grande pesa. | editor |
| 0.6 | A | **No retomar un agente largo con SendMessage para otra vuelta**: arrancar uno nuevo con un resumen corto. | La tercera vuelta del director sobre las almas (2026-10-27) se estimó en 75 mil tokens y el contador dio 243 mil: el agente retomado vuelve a cargar todo lo anterior. | yo |

## 0b. La Session 05 (el 159 en paisajes, "una tarde"): parada, se retoma después de 0

| # | Prio | Qué | Estado |
|---|---|---|---|
| 0b.1 | A | **Etapa 4, rearmarla**: planos 56-66 con el sol bajo que NO toca el horizonte (169565 sirve), una sola puesta en el plano 67 (178710, la única donde el sol entra de verdad), 68-69 sin sol a la vista (18503). Sacar 116206 (estela de avión). | lo dijo el revisor el 26/10, sin hacer |
| 0b.2 | A | **Etapa 5: faltan clips.** Hay 4 para 10 planos, y el final tira a oscuro. Buscar la última luz clara: cielos pastel, agua quieta que los refleja. | sin hacer |
| 0b.3 | B | Cambiar 221999 (se ve procesada) y revisar 230409 (la niebla puede leerse como mañana). | sin hacer |
| 0b.4 | A | **Disco para el render**: la 04 ocupó 13,2 GB terminada y casi el doble mientras se armaba. Hay 21,9 GB libres. Decide el DJ qué se libera: los .mov de las Sessions ya publicadas (31 GB en `postproduction/video`) o los clips estirados de la 04 (13 GB). | decide el DJ |
| 0b.5 | B | **Escuchar el 53:40 de la mezcla** (Earth → Renascence): el control de dos bajos dio 3,3 dB contra un límite de 3. | el DJ, antes de publicar |

Todo lo hecho está en la BITACORA del 2026-10-26. La hoja v1, bloqueada, está en
`C:\Users\gonza\Pictures\plomo_session_05_recorrido.jpg`.

---

## 1. El 158 (b2b Grey Area): decide el DJ

| # | Prio | Qué | Evidencia | Quién |
|---|---|---|---|---|
| 1.1 | A | **Meter Metro al lado de Grey Area.** Llenaría el hueco que dejó Un Mundo En Paz: el set quedó en 1h47 para una fecha de 2h. | Josh Wink, Simon Vuarambon – Metro (Simon Vuarambon Rework) es la otra cara del mismo lanzamiento (Bedrock, 9/10). Digweed (Transitions 1154) la puso pegada a Grey Area para cerrar su hora; Karotte también los encadenó. Ya está en la biblioteca (108314087). Quedó afuera del pool por la key: ver 3.1. | curador |
| 1.2 | B | **Probar las anclas en el lugar de los pros.** | Grey Area cae en el tramo final en 2 de 3 sets (89-90%). Prismatik va en el medio, rodando (30% en Khen, 9 de 12 en Eelke). En el 158 está al revés: Grey Area en el medio y Prismatik entregando. Son 3 y 2 sets: es una pista, no una regla. | curador |
| 1.3 | B | **Variante con Grey Area abriendo o cerrando.** | En los b2b, el tema que comparten los dos va en las puntas: Simon b2b Tantum, Cattaneo b2b Warren y Mellino b2b Eze abren con él, y Marsh b2b Sasha y Guy J b2b Mantzur cierran con temas propios. | curador |
| 1.4 | B | **Acordar cómo alternan.** | Nadie lleva una lista común: van de a uno, de a dos o de a tres o cuatro, y lo arreglan con una llamada antes (Mixmag, Khen y Mantzur). Si van de a uno, Grey Area (#9) y Prismatik (#15) le tocan al mismo DJ. | DJ |

**Confirmado: un b2b suena igual que un set solo.** Se compararon 12 b2b (86 transiciones)
con 44 sets solos: dan lo mismo en saltos de rueda, keys repetidas, BPM y modo mayor. La
lista única no necesita reglas especiales.

## 2. Música para bajar

Todo está en `data/research_b2b_2026-10.json`. No se bajó nada: se baja cuando el DJ lo pida.

| Prio | Tema | BPM | Key | Por qué |
|---|---|---|---|---|
| A | Khen, Yotam Avni – Retro | 124 | 5A | Va inmediatamente antes de Prismatik en el set de Khen (Balance Croatia); está en 7 sets |
| A | Khen – Doda | 122 | 7A | Va inmediatamente después de Prismatik en el set de Khen; está en 13 sets de 2026 |
| B | Floormagnet – Stargazed (Zoo Brazil Remix) | 124 | 6A | Va antes de Prismatik en el set de Eelke Kleijn (DLN 465) |
| B | Madraas – Leaving Places (Matthew Sona Remix) | 122 | 7A | Remix de Sona, a 1 de Prismatik en la rueda |
| B | Matthew Sona – Vesper (y remixes de Peter Makto y Soulmade AR) | 121 | 6A | Mismo productor y misma key que Prismatik |
| B | D-SHIFT – Find a Way | 124 | 6A | Balance, 25/09; lo tocaron Seaman y el propio D-Shift |
| B | Ellroy – Zanzibar | 123 | 6A | Mango Alley; está en 2 sets |
| B | Infusion – Legacy (Nick Warren & Jamie Stevens Remix) | 122 | 7A | Selador, 02/10; Warren firma el remix de Menq que cierra el 158 |
| C | Serious Dancers – Evelen (Nicolas Viana Remix) | 124 | 12A | Univack; está en 3 sets |
| C | Aler – Rising Kelly | 122 | 8A | Lo tocó Antrim en vivo |
| C | Trilucid, Tim Green – One Day At A Time (Tim Green Remix) | 124 | 11A | Está en 6 sets |
| C | Artic White – Aldilá (Matthew Sona Remix) | 122 | 10A | Para la biblioteca, no para el 158 |
| — | Tigerhook – What Music | — | 9B (Beatport) | Bedrock, sale el 23/10. Digweed lo puso 3º en la 1154. Esperar a que salga y medirle la key |

Ya están en la biblioteca y pegan con las anclas, pero no entraron al pool del 158:
Madre Noche (Mellino Remix), The Ways (Kamilo Ext) y Homeboy (Dilby Remix), por la zona de
key o la energía. Ver 4.2.

## 3. Reglas para desafiar con `/reglas`

| # | Prio | Regla | Qué dicen los datos nuevos |
|---|---|---|---|
| 3.1 | A | `armonia.max_camelot_dist` y la distancia entre **tonalidades paralelas** (misma tónica, otro modo) | Hoy esa distancia vale 4. Es el 17% de las violaciones (27 de 158), y el par Grey Area → Metro de Digweed es uno de esos casos. La regla de distancia 2 ya está refutada: la viola el 38% de los pasos, y sin contar las paralelas sigue en 31%. |
| 3.2 | B | `bpm.max_salto = 3.0` | En el corpus total la viola el 17% de los pasos. En lo nuevo baja a 11%, y en los b2b a 13%, debajo del umbral de 15%. La refutación se sostiene solo con el corpus viejo. |
| 3.3 | B | `armonia.modo_mayor_objetivo` y `sonido_propio.pct_zona_menor` | Dependen de quién lee la key. Sobre los mismos 391 temas, Rekordbox da 13% en mayor y Beatport 60%. En 171 de 174 desacuerdos, Rekordbox dice menor y Beatport mayor. |
| 3.4 | C | `densidad.tracks_por_hora = 8.8` (hoy ningún código la lee) | Los pros tocan entre 10 y 13 temas por hora (Digweed, Eelke, Vasami b2b Rada, Mellino b2b Eze), y el 158 va a 8.5. Puede ser porque las radios recortan los temas. |

## 4. Para medir

| # | Prio | Qué | Para qué |
|---|---|---|---|
| 4.1 | A | Pasar el detector de key por cromagrama (el que se usó con Grey Area) por Metro y por unos 24 de los 174 desacuerdos de modo | Decide si Metro entra al 158 (1.1) y qué fuente de key manda (3.1 y 3.3) |
| 4.2 | A | Medir la distancia de sonido y forma de Metro, Madre Noche, The Ways y Homeboy a Grey Area y a Prismatik | Saber si los vecinos de los pros también son vecinos para nuestra medida |
| 4.3 | B | Medir el ataque de la capa melódica con Demucs | Es la única medida que separó lo que el DJ llama "oscuro" (Emerge 3.6, Circle Of Lights 2.8). Usa la GPU, y la GPU es la que cuelga la PC: correrlo de a uno |
| 4.4 | B | Arreglar la energía de los temas que tienen el bajo desde el primer compás | El cue Bass IN en 0 ms se lee como "desconocido". Le pasa al 66% de la biblioteca (2092 de 3163). Con el bajo como conocido, Grey Area daría 7.1 y no 5.7, y Prismatik 6.6 y no 5.2 |
| 4.5 | C | Temas por hora de los pros contra el 8.8 | Va con 3.4 |

## 5. Arreglos del sistema (lo que se rompió estos días)

| # | Prio | Qué falló | Arreglo | Quién |
|---|---|---|---|---|
| 5.1 | A | **El sync no actualiza en el pen una lista que ya existe.** El 157 quedó con Fading Out después de tres syncs; Export Playlist agrega otra lista en la raíz en vez de reemplazar. Hoy el pen tiene el 157 dos veces y el 158 viejo | Procedimiento: borrar la lista del pen y sincronizar. El borrado lo hace el DJ, porque el clasificador de permisos me lo bloquea. Probar la pista del `Timestamp` en `masterPlaylists6.xml`, que necesita permiso. Llevar el lector de `export.pdb` a `scripts/verificar_pen.py` | tecnico |
| 5.2 | A | **Los tocados no ven otras versiones del mismo tema.** Un Mundo En Paz se había tocado hace dos días en otra versión y no se avisó: lo frenó el revisor | `plomo.tocados` tiene que cruzar por artista y título base, sin el nombre de la mezcla | tecnico |
| 5.3 | A | **El tema del pedido no era el que buscamos.** El DJ dijo "gray matter" y era Grey Area de Simon, que estaba en la biblioteca desde el 19. Se perdieron dos versiones del set | Antes de buscar afuera, mostrar los títulos parecidos de la biblioteca, sobre todo lo importado en la última semana, y preguntar el artista. Ver [APRENDIZAJES.md](APRENDIZAJES.md) | curador / master |
| 5.4 | B | **`spotify_sync` no encuentra temas con "feat." en el artista.** Pasó con Erdem Yetim feat. Erman Danisment, y se agregó a mano en `spotify_matches.json`. Además corta ante un 503 | Separar el artista por "feat." como ya se hace con la coma, y reintentar ante un 5xx | tecnico |
| 5.5 | B | **`spotify_validar` no mira Rekordbox.** El 150, el 151 y el 152 tenían en Rekordbox otro nombre que en Spotify | Comparar los tres lados: Rekordbox, receta y Spotify | tecnico |
| 5.6 | B | **El selector manda las anclas al principio.** El bonus del ancla se cobra al colocarla, así que poner el ancla "libre" no es un criterio. Además, el `n` del config no es el que usa | Medir el ancla con ventanas fijas, como se hizo en el 158, o cobrar el bonus al final del beam | analista |
| 5.7 | C | **La key de Grey Area es dudosa:** Rekordbox dice 3B y Muzpa Dbm | Va con 4.1 | analista |

## 6. Datos para corregir

| # | Qué |
|---|---|
| 6.1 | En `simon-vuarambon_dahaus-palacio-alsina-cordoba_2026-03-01.json` falta Grey Area entre las posiciones 56 y 57 (trackid lo pone a las 3:34:12). El backtest mide una transición que no existió. El archivo tiene campos agregados a mano: corregirlo con cuidado |
| 6.2 | El setlist de Sasha b2b Digweed está duplicado (1-17 se repite como 18-35) y en la posición 33 dice ":30" como artista |
| 6.3 | `backtest_rules.py` cuenta "ID" como artista. El "max artista = 24" que da son los huecos del Cattaneo b2b Warren |
| 6.4 | En DLN 465, Muzpa le dio 134 Fm a Mariano Favre – The Mad King; probablemente bajó otro tema |
| 6.5 | Documentar cómo se busca en trackid: el detalle trae los temas (`detectionProcesses[].detectionProcessMusicTracks`), la búsqueda inversa es `musictracks?keywords=` y después `audiostreams?musicTrackId=`, y set79 sirve como segunda fuente |
