# Set suelto — Atardecer, 2026-09-23

**Estado:** grabado. La animación tiene prototipos en `postproduction/video/`, falta el render final. No publicado: subir lo decide Gonzalo.
**No es de la serie "Sonido Argentino".** No lleva número, ni "Style", ni la plantilla de miniatura de la serie.
**Grabación:** en casa, al atardecer, una sola toma, salida directa de consola (`grabaciones/2026-09-23_set_consola_REC001.wav`).
**Master del video:** 25:49 (1549.5 s), −14 LUFS. Capítulos en `data/video/2026-09-23_capitulos.json`.
**Arco:** 4 temas, 118 → 120 BPM tocados, key 7A → 6A, energía 5.1 / 6.3 / 5.8 / 5.8.

Criterio aplicado de `docs/YOUTUBE_SERIE.md`: el término que se busca va adelante, tracklist completo con sellos, vidriera y no ingreso, se mide por minutos vistos, los shorts salen de los picos de la curva de energía. Lo que no aplica a un set suelto (el formato de 85 min, la plantilla de miniatura con número, la playlist de la serie) queda afuera.

---

## Título

```
Maze 28, Mike Rish, Callecat, DJ Bird | Sunset Progressive House Mix 2026
```

73 caracteres. Donde el título se corta, que depende de la pantalla, lo primero que se pierde es el año. Los cuatro nombres y "Sunset" quedan adelante.

**Por qué este:** los nombres de los artistas son la búsqueda de poca competencia que este video puede ganar, y además hacen que aparezca como sugerido al lado de los uploads oficiales de los temas. Maze 28 va primero porque es el nombre de más peso según el pedido. No lo medí con volumen de búsqueda. "Sunset progressive house mix" describe lo que es con las palabras del nicho. Usé "Mix" y no "Set" por criterio: es el término más común para este formato, pero tampoco está medido.

Descartados:
- `Sunset Progressive House Mix | Maze 28, Mike Rish, Callecat, DJ Bird`: adelante pone el término genérico y saturado, donde un canal nuevo no rankea, y en el celular manda los nombres (la búsqueda que sí se gana) a la zona que se corta.
- `Maze 28 Style | Sunset Progressive House`: es el formato de la serie tal cual, pero "Style" miente, porque Maze 28 es uno de cuatro temas y no la referencia del set. Además tira tres nombres que son términos de búsqueda y hace que se confunda con un capítulo de la serie.

## Descripción

**Definitiva, dictada por el DJ (2026-09-28):** "deja los track list y algo mas de agradecimiento, fin". Nada de presentación ni de explicar la imagen, y NUNCA un cierre tipo "compralo y bancá al artista". Es la que está cargada en el video.

```
0:00 Mike Rish - Wait for Me (Original Mix) [tornn]
6:03 Callecat - A New Beginning [The Soundgarden]
11:25 DJ Bird - In Space [Consapevole Recordings]
18:41 Maze 28 - Mindloop (Original Mix) [Balance Music]

Gracias por escuchar.
```

## Tracklist

Los tiempos son los del master, verificados contra el audio (`data/video/2026-09-23_capitulos.json`). **Cada capítulo arranca en la mitad del blend**, no cuando el tema empieza a sonar: es la regla de `scripts/video_rasgos.py`. El nombre del tema aparece en pantalla 4 s después de esa marca.

| # | Capítulo | Artista | Título | Sello | BPM original → tocado | Key | E |
|---|----------|---------|--------|-------|-----------------------|-----|---|
| 1 | 0:00 | Mike Rish | Wait for Me (Original Mix) | tornn | 118 → 118.0 | 7A | 5.1 |
| 2 | 6:03 | Callecat | A New Beginning | The Soundgarden | 118 → 119.0 | 7A | 6.3 |
| 3 | 11:25 | DJ Bird | In Space | Consapevole Recordings | 119 → 120.0 | 6A | 5.8 |
| 4 | 18:41 | Maze 28 | Mindloop (Original Mix) | Balance Music | 120 → 120.0 | 6A | 5.8 |

El BPM tocado sale del BPM de `data/pool.json` por el ratio de tempo de la alineación. Sellos verificados: los cuatro coinciden entre el campo `label` de `data/pool.json` y el nombre del archivo que usó la alineación. Corrección: el título de Callecat está como `'A New Beginning '` en la biblioteca, con un espacio al final, y se normalizó a `A New Beginning`.

## Tags

```
Maze 28, Maze 28 Mindloop, Mike Rish, Mike Rish Wait for Me, Callecat, Callecat A New Beginning, DJ Bird, DJ Bird In Space, Balance Music, The Soundgarden, Consapevole Recordings, tornn, progressive house, progressive house mix, sunset progressive house, sunset mix, sunset dj set, organic house, melodic progressive, progressive house 2026, dj set at home
```

Son 21 tags y 356 caracteres. Contando como cuenta YouTube, que suma las comillas de los tags con espacio, dan 374 de 500. Cada artista va dos veces, solo y con su tema, porque "Maze 28 Mindloop" es una búsqueda distinta de "Maze 28". "organic house" está porque la biblioteca tiene a Callecat catalogado así. No van "hernan cattaneo style" ni "sonido argentino": ninguno de los dos describe este set.

## Miniatura

**Propuesta armada:** `data/youtube/2026-09-23_atardecer_miniatura.jpg` (1280x720, 94 KB). Se puede subir así o usarla de referencia.

**Concepto: el mismo horizonte, visto dos veces.** A la izquierda, el cielo de la animación. A la derecha, la ventana real. La cortina hace de costura entre los dos y la franja naranja cruza el cuadro entero a la misma altura, al 56% del alto.

- **Cuadro real:** `grabaciones/video/IMG_1688.MOV`, **minuto 6:00 del video del teléfono** (el master va 2.36 s atrás del teléfono, así que en el master es 5:57.6, justo antes de que entre Callecat). Se eligió entre 1:30, 3:00, 4:00, 5:00, 6:00, 7:00 y 8:00 porque en el 6:00 los edificios ya son silueta, el cielo es gris azulado y la franja naranja sigue entera: es donde hay más contraste sin perder el naranja. Recorte sobre el cuadro de 2160x3840: x 400–1640, y 497–1937 (de la cortina al parante de la ventana), escalado a 620x720 y pegado a la derecha con un fundido de 90 px sobre la cortina.
- **Cuadro de la animación:** master **23:00.5**, que cae en los compases posteriores al drop de Mindloop. Es el cuadro de horizonte más naranja y saturado de los que se probaron (2:24, 5:00, 11:52, 23:00). A esa hora el resplandor ya no sale del cielo sino de las luces del equipo, y por eso es más naranja que al principio. Se renderiza con `scripts/video_animar.py --desde 1380 --segundos 1 --res 1920x1080` sin cartel de tema.
- **Texto:** `SUNSET` grande (Bahnschrift Bold Condensed, crema) arriba a la izquierda, sobre el cielo oscuro de la animación, y `AT HOME` más chico en naranja debajo. "Sunset" confirma lo que buscó el que llega y "at home" es la escala honesta: una ventana, no un beach club. `MAZE 28` en la miniatura se descartó porque ya va primero en el título y a 120 px competiría con SUNSET.
- **A 120 px** (se probó bajándola a 120x68) se leen tres cosas: la palabra SUNSET, la franja naranja continua de punta a punta y la silueta de los edificios con el tanque de agua. AT HOME se lee desde unos 250 px.
- **Abajo a la derecha no hay nada importante**, porque ahí YouTube pone la duración.
- **Ojo:** el recorte muestra la vista real desde la casa, y los edificios son reconocibles para quien conozca la zona. Decidir si importa.

## Momentos para shorts

**DESCARTADOS (2026-09-28).** Se renderizó el primero (drop de Wait for Me, 36 s, vertical, solo la animación con el nombre del tema) y el DJ dijo: "descarta el short malisimo es". Los tiempos de abajo quedan como registro, no como plan.

Salen de `data/video/2026-09-23_rasgos.npz`. Se buscaron los saltos de `cuerpo` (loudness de 3 s) de menos de 0.35 a casi 1 y el drop se ajustó al golpe de bombo más fuerte de la grilla de beats. Cada clip entra **2 compases antes del drop** (4 s de subida, así el drop cae en el segundo 4) y sale **16 compases después**. Los tres terminan con la energía todavía arriba, ninguno en un breakdown.

| # | In | Drop | Out | Dur | Tema | Por qué |
|---|----|------|-----|-----|------|---------|
| 1 | 22:45.2 | 22:49.2 | 23:21.2 | 36 s | Maze 28 - Mindloop | El drop de mayor contraste de la segunda mitad: cuerpo 0.03 en los 16 s previos → 0.91 sostenido. Antes del drop el filtro dejó el agudo en cero (`aire` 0.00 entre 22:30 y 22:42), así que la imagen arranca blanda y se abre con el golpe. Es de noche. Nombre más buscado del set. |
| 2 | 4:49.4 | 4:53.4 | 5:25.4 | 36 s | Mike Rish - Wait for Me | El contraste más alto del set entero: 0.03 → 0.96. Golpe de bombo de fuerza 0.99. Es el atardecer todavía naranja. |
| 3 | 11:33.4 | 11:37.4 | 12:09.4 | 36 s | DJ Bird - In Space | El pico absoluto: los 32 s más fuertes del set (cuerpo 0.99, bajo 0.92). Es el cambio de bajos. El grave cae a cero en 11:36 y a las 11:37.4 entra el bajo de In Space, 32 compases dentro del tema. Callecat todavía puede estar arriba en la mezcla. Es la hora de transición del cielo. |

Los tres juntos cuentan la tarde en orden: naranja, transición, noche. Conviene publicarlos en ese orden, uno por semana.

Reserva, por si se hacen más:
- 16:53.7 / drop 16:57.7 / 17:29.7, DJ Bird: después del tramo largo con los agudos filtrados.
- 20:37.4 / drop 20:41.4 / 21:13.4, Maze 28: el filtro se cierra en 12 s y abre con el drop. Es el cambio de imagen más visible, pero la salida cae con la energía bajando (0.79).

**Render vertical:** `.venv/Scripts/python.exe scripts/video_animar.py --nombre 2026-09-23 --master <master> --desde <In> --segundos 36 --res 1080x1920 --mostrar-titulo --salida <archivo>`. Se probó con 2 s de Mindloop y anda, con el cartel del tema incluido. **Problema:** en vertical el cartel cae al 81-90% del alto, que es la franja que tapa la interfaz de Shorts (nombre del canal, texto, audio). Hay que subirlo al 60-65% para los shorts, o el nombre del tema no se va a ver.

## Comentario fijado

Descartado: tenía el mismo tono de informe que la primera descripción. Si se quiere uno, que lo escriba el DJ.

## Antes de subir

- **Cuenta verificada:** el video dura más de 15 min y lleva miniatura personalizada. Sin verificar (verificación por teléfono), no se puede ninguna de las dos cosas.
- **Content ID va a reclamar** los cuatro temas y los ingresos van a los sellos. Es lo esperado (`docs/YOUTUBE_SERIE.md`: vidriera, no ingreso). Conviene subirlo primero como **privado** y esperar el paso de "Comprobaciones" de YouTube: ahí aparecen los reclamos antes de publicar, y si algún titular eligió bloquear en algún país se ve ahí y no con el video ya público.
- **RESUELTO (2026-09-28, después de escrito esto):** el master final es
  `grabaciones/2026-09-23_set_master_youtube.wav`, CON el +1.5 dB a Callecat. El
  recorte siguió en 21.50 s, así que capítulos y shorts no se movieron; los rasgos
  se recalcularon y el render final (`postproduction/video/2026-09-23_atardecer.mov`)
  usa ese master. Lo que sigue queda como registro de la advertencia original.
- **El master que usan los rasgos y los capítulos** es `v2_master_youtube.wav`: dura 1549.48 s y tiene un recorte de 21.504 s, lo mismo que los capítulos. Vive en la carpeta temporal de la sesión (`C:\Users\gonza\AppData\Local\Temp\claude\...\scratchpad\`), **no en `grabaciones/`**. Su informe dice que **se hizo sin ganancias por tramo**, o sea sin el +1.5 dB de Callecat de `data/video/2026-09-23_ganancias.json`. Si el render final va con ese ajuste, hay que regenerar el master con `scripts/pulir_master.py --ganancias ...`, verificar que el recorte siga dando 21.504 s (si da eso, los capítulos y los shorts no se mueven) y recalcular los rasgos. Si no, el video sale con Callecat unos 2 dB abajo de los otros tres, que es como se tocó.

---

Armado a mano por el agente `video`, 2026-09-28. No publicar sin que Gonzalo lo decida.
