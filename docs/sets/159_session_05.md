# Session 05 — el 159 en paisajes, plan eficiente

> **2026-11-01: la Session 05 NO es paisajes, es el video de las almas.** "No si era hacer el
> video de las almas" (el DJ). El 27/10 la maqueta de las almas quedó aprobada "como base para el
> video largo del 159" (`data/video/veredictos.json`), y este plan de paisajes siguió por error.
> Lo de abajo queda como registro y como receta, si algún día se hace un video de paisajes del
> 159:
> - la asignación de los 76 planos, bloqueada por el final;
> - los scripts `revisar_clips.py` y `estirar_planos.py`, que sirven para cualquier Session de
>   paisajes;
> - unos 11 GB de clips bajados.
>
> El video de las almas: la historia pasa una vez por el set (se conocen en Aura y Bambook, vuelan
> juntas hasta Summer O'clock, se separan en Dichotomy, una se apaga en State of Progression, el
> primer intento en Conviction, la cura en el drop de Dodonpachi, vuelan en Mutant, se separan
> brillando en Omira). La hace el director con `almas.py`.

"Fijate como esta el set 159 en spoty empata rekor y hace sync y hace el plan para video
eficiente" (el DJ, 2026-10-31). El video sale del 159 tal como está en Spotify (v8c, 17 temas) y
con la receta de "una tarde" del 26/10. Este plan es para no repetir lo de ese día: una vuelta
del editor costó ~380 mil tokens, la del revisor ~230 mil, y la hoja quedó bloqueada igual.

**Tope: unos 300 mil tokens por el video entero, de la hoja a la subida**, contra los ~610 mil
que costó una sola vuelta de la hoja el 26/10. Cada número de abajo es una estimación. Antes de
lanzar cada agente le aviso al DJ el costo y espero el OK.

## Para seguir (parado el 2026-10-31 a las 21 h)

"Hace todo y publicalo en youtube", y un rato después: "paralo y documenta para seguir en otra
sesion" (el DJ, 2026-10-31). Con lo primero el DJ dio el OK al plan y a publicar en YouTube; la
puesta y el título los decidí yo (ver abajo).

**Hecho:**
- A: la receta y los 76 planos.
- La mezcla: 105:13, las 16 transiciones ok.
- Los capítulos, en `data/video/session_05_capitulos.json`. Los nombres quedaron prolijos para
  el texto en pantalla: Sébastien Léger, André Moret, Summer O'clock.
- Disco: 34 GB libres; el render necesita ~26.

**Cortado a los pocos minutos, sin resultado:**
- B, `revisar_clips.py`: no llegó a escribir nada. Solo volvió a bajar 116206, el de la estela,
  que se borró en la limpieza y hace falta para probar el script.
- C, buscar los ~35 clips que faltan: no corrió ninguna búsqueda ni bajó nada.
- `session_05_candidatos.json` sigue como el 26/10.

**Decidido sin preguntar, porque dijo "hace todo"** (se puede cambiar):
- la puesta en el drop de Dodonpachi (92:03);
- el título: "Sébastien Léger, Kamilo Sanclemente, Guy Mantzur, Roy Rosenfeld | Organic House
  Mix · Session 05". `paquete_session.py` escribe "Progressive House Mix" fijo, así que hay que
  cambiarlo en el paquete;
- no se esperó a que el DJ escuche la mezcla.

**Cómo seguir, en orden:**
1. Lanzar B y C en paralelo, nuevos, con `model: sonnet` y un tope de 40 herramientas cada uno.
   Los encargos están abajo, en "Encargos B y C".
2. Correr `revisar_clips.py --etapas data/video/session_05_candidatos.json` sobre todos los clips.
3. Lanzar al editor, nuevo y con tope de 30 herramientas:
   - asigna los 76 planos en `data/video/session_05_etapa_<n>.json`, con el formato de
     `session_04_etapa_3.json` (`n`, `id` o `archivo`, `desde`, `paso`, `encuadre`, `grado`,
     `nota`);
   - mira solo las hojas de `revisar_clips`;
   - arma la hoja de recorrido v2 en `C:\Users\gonza\Pictures\plomo_session_05_recorrido.jpg`,
     una imagen por etapa de hasta 1600 px.
4. Lanzar al revisor, nuevo y con tope de 15. Si bloquea, un editor nuevo arregla solo lo
   marcado, una vez.
5. `naturaleza.py validar` y después `render`:
   - por WMI, uno solo, con `--codificador cpu` si lo pide (ver la memoria
     `feedback_procesos_largos`);
   - avisarle antes a las otras sesiones de plomo: no mezclar.py ni otros renders mientras tanto.
6. Verificar que el audio sea igual a la mezcla (md5).
7. El revisor mira el video, nuevo y con tope de 15.
8. Paquete y subida:
   - `paquete_session.py --mix postproduction/mixes/159_mix.json --numero 5 --artistas "..."
     --video postproduction/video/session_05_naturaleza.mov --cuadro <cuadro de la puesta>`;
   - corregir el título en el paquete y que el revisor mire los textos;
   - `youtube_publicar.py subir` (privado), esperar el HD, `publicar`;
   - `session_salio.py`: el destacado del canal y la web.

### Estado al 2026-11-01, madrugada (retomado con "ahora si continua")

- B y C, hechos:
  - `revisar_clips.py` marca la estela de 116206 y casi nada más;
  - 44 clips nuevos, revisados los 64.
  - Marcados por estela: 116206, 119242, 218961, 285882 y 221728.
- **Ningún plano entra a velocidad real.** Los planos de 32 compases piden de 63 a 134 s y los
  clips cubren de 20 a 78. Se estira casi todo, x1.3 a x2.5, con `estirar_planos.py` (RIFE).
  RIFE a 1440p en la RTX 4050 hace unos 16 cuadros por segundo: 5 a 6 horas para los 76 planos.
- **Disco: el orden importa.** Hay 28 GB libres. Los estirados ocupan unos 15 GB, los tramos del
  render unos 14,5 y el video final otros 14,5. El orden:
  1. `estirar_planos.py --nombre session_05`;
  2. borrar los originales de Pixabay de los clips que solo usa la 05 (se vuelven a bajar por
     id);
  3. `naturaleza.py render ... --tramos` con todos los tramos, que no une;
  4. borrar `postproduction/stock/estirados` (cada plano guarda en `fuente` cómo rehacerlo);
  5. unir llamando a `naturaleza.unir(...)` directo, porque `render` sin `--tramos` valida y pide
     los estirados.
- El editor, a cargo de D, asigna los planos en `session_05_etapa_<n>.json` y arma la hoja v2.

### Hoja v2: BLOQUEADA (2026-11-01, madrugada). Parado antes del RIFE

Lo que hizo el editor:
- asignó los 76 planos: `validar` da 0 errores y el factor máximo es x2.84;
- la puesta única quedó en P68, con 178710;
- las hojas están en `C:\Users\gonza\Pictures\plomo_session_05_recorrido_etapa_<n>.jpg`;
- el script que eligió está en `scripts/archive/elegir_session_05.py`.

El revisor bloqueó:
1. **P16 (103195)**: un camino de tierra en el pie, y se ve procesado.
2. **P69 y P72 (203676)**: hay una estela, y el sol se ve en la bruma después de la puesta.
   Sale el clip entero.
3. **P33 y P50 (119784)**: es sol en el horizonte, [C], marcado [B]. La luz vuelve atrás.
4. **P20 (230417)**: la nota dice sol bajo y sombras largas, y después P21-32 vuelven a sol alto.
5. **Carrusel en el último tercio**: 12 clips, cada uno dos veces, intercalados (P54-59, P61-66,
   P69-73). Cada plano usa el clip entero estirado, así que la segunda vez es el mismo clip
   espejado, no "otro tramo". Es la lección de la 04.

No bloquea, pero hay que cuidarlo:
- 221999 tiene un halo magenta en P31;
- en 169565 (P64 y P67) el disco blanco puede leerse como luna: calentarlo en el grado;
- en P60-67 la luz va y viene;
- la etapa 5 termina en [E], sin [F].

**Tokens hasta acá: unos 520 mil**, contra un tope de 300 mil. Por agente:
- revisar_clips, 84 mil;
- la búsqueda, 134 mil (el tope era de 90);
- el editor, 206 mil (estimado: 80-110 mil, junto con el revisor);
- el revisor, 93 mil.

Se paró antes de lanzar otra vuelta para preguntarle al DJ.

**Lo que falta para destrabar:** 15 a 20 clips nuevos:
- [C], sol bajo que no toca el horizonte, para P54-67;
- [E] arrebol y [F] hora azul, para P69-76, ordenados por luz: 200121, después 18503, después
  210790, después lo nuevo;
- [A] de sol alto para P20, y agua [A] para sacar 221999.

Después, el editor cambia SOLO esos planos (su script en archive se puede volver a correr), y el
revisor mira solo esos.

### Vuelta 2: BLOQUEADA otra vez, ahora solo por el final (2026-11-01)

El DJ eligió "una vuelta más, completa". Se hizo esto:
- se bajaron 18 clips dirigidos;
- el editor cambió 25 planos: las etapas 4 y 5 rehechas, la 4 con cada clip una sola vez;
- `validar` da 0 errores y el factor máximo es x2.90;
- el revisor aprobó P16, P20 y P33.

Bloqueó:
1. **P75 (9153) y P76 (292383)**, marcados [F]: son cielos de día oscurecidos (cúmulos blancos
   con sol). El video cierra volviendo a la tarde.
2. **P72 y P74**: la etapa 5 repite su terna (juncos 137113, el del medio y el campo rosa 18503) a
   7 minutos. Además P74 vuelve al rosa después de P73, que ya pasaba a azul.
3. **P50 (301800)**: a 1:1 parece haber techos en el valle de la izquierda.

**El cuello de botella es el material del final.** Después de la puesta hay 8 planos y en
Pixabay casi no hay clips largos de arrebol ni de hora azul. La búsqueda dirigida trajo:
- 4 de arrebol: 3 con el sol en el horizonte (serían otra puesta) y 19409, que el editor descartó
  porque el sol se ve en la mitad del clip;
- 2 de "hora azul" que son día.

Quedan 4 clips limpios para 8 planos. Pasa pero se nota: P65 parece una puesta 4 minutos antes,
y P59/P61 repiten a P54/P55.

**Tokens: unos 860 mil.** La vuelta 2 llevó unos 340 mil: búsqueda 107, editor 157 y revisor
~80. Estimado: 250 a 350 mil tokens más, y después las horas de máquina:
RIFE 5-6 h, render ~4 h y la subida.

### Encargos B y C

Los dos: nuevos, sonnet, máximo 40 herramientas, sin commitear, sin master.db ni Rekordbox, sin
GPU.

**B (agente `tecnico`)**: escribir `scripts/revisar_clips.py` y `tests/test_revisar_clips.py`
según "B: qué marca revisar_clips.py".
- Cómo mira: 1 cuadro cada 2 s, achicado a ~960 px.
- Qué entra: ids, o `--etapas` con `candidatos` y `nuevos`.
- Qué sale:
  - `data/video/session_05_revision.json`;
  - una hoja por etapa con recortes de ~400 px de lo marcado, en
    `postproduction/stock/revision/hoja_etapa_<n>.jpg`, de hasta 1600 px.
- Validación:
  - TIENE que marcar la estela de 116206;
  - contar las marcas en los otros 19 candidatos;
  - mirar como mucho 3 recortes.

**C (agente `general-purpose`)**: buscar y bajar, eligiendo por miniatura, unos 45 clips:
- cuántos por etapa: 1 ~13, 2 ~8, 3 ~15, 4 ~6, 5 ~4;
- etapa 4: sol bajo que no toca el horizonte;
- etapa 5: arrebol y hora azul, sin estrellas ni luna;
- cómo: `stock_pixabay.py buscar` con varias consultas en una llamada; achicar las hojas a
  1600 px antes de mirarlas; un solo `bajar`; tope de 8 GB;
- dónde se anota: en una lista `nuevos` por etapa de `session_05_candidatos.json`, sin tocar lo
  que ya está;
- sin revisar a 1:1.

---

**De dónde salía el gasto.** El 26/10 fueron 368 herramientas para 66 clips: más de cinco por
clip, cada una cargando todo lo anterior. Lo que se baja acá es la cantidad de llamadas. Cada
llamada tiene que tratar una etapa entera, no un clip.

---

## Lo que ya está (2026-10-31)

- **El set**: Spotify, Rekordbox, la copia Sunset y la receta coinciden 17/17 en orden, leído de
  los tres lados.
- **La mezcla nueva**, `postproduction/mixes/159_mix.wav`:
  - 105:13, -14 LUFS y -1,1 dBTP;
  - las 16 transiciones dan ok y ninguna queda para revisar.
- **La receta del video** (`data/video/session_05_recorrido.json`), pasada al set nuevo: planos de
  32 compases, cinco etapas, la luz de una tarde, sin noche.
- **Los planos** (`data/video/session_05_planos.json`): 76, de 47 a 126 s, con una mediana de 79 s.
- **20 clips ya bajados y mirados a 1:1** (`data/video/session_05_candidatos.json`):
  - afuera 116206, por la estela de avión;
  - en duda 221999, que se ve procesada, y 230409, porque la niebla puede leerse como mañana.

## El recorrido con el set nuevo

| Etapa | Temas | Minutos | Planos | Clips que sirven | Faltan |
|---|---|---|---|---|---|
| 1. Bosque con sol entre los árboles | Aura, Bambook, Karnaval, Blazing Ice | 0:00-25:10 | 20 | 3, y 230409 en duda | ~11 |
| 2. Agua con destellos | Earthbound, The Moon Lights the Way, The Future is in the Past | 25:03-44:35 | 13 | 3, y 221999 en duda | ~6 |
| 3. Hora dorada en el campo | Lava, Balaphonia, Summer O'clock, Dichotomy, Winged | 44:27-75:32 | 23 | 4 | ~12 |
| 4. El sol toca el horizonte | State of Progression, Conviction, Dodonpachi | 75:24-93:38 | 12 | 3 | ~5 |
| 5. Después de la puesta | Mutant, Omira | 93:30-105:13 | 8 | 4, dos cortos | ~2 |
| **Total** | | | **76** | **17** | **~35** |

En "Faltan" va un clip cada 1,5 planos, que es lo que la 04 reusó en tramos distintos de un mismo
clip.

**La puesta, propuesta: el drop de Dodonpachi (92:03, el 87% del set).** Antes caía en Redemtion,
que ya no está en el set. El 159 nuevo sube hasta el final: Dodonpachi 7.0, Mutant 7.2, Omira 7.4.
- Así quedan 13 minutos después de la puesta. Es lo que se decidió el 26/10: no cerrar largo y
  oscuro.
- El arrebol, el cielo más encendido del día, cae con el pico del set.
- Para la puesta sirve 178710, la única de los candidatos donde el sol entra de verdad. Para
  antes, 169565 (sol bajo que no toca el horizonte). Para después, 18503 (sin sol a la vista).

## Fases

| # | Qué | Quién | Tokens (estimado) | Sale |
|---|---|---|---|---|
| A | Receta y planos con la mezcla nueva | yo | hecha | la tabla de arriba |
| B | **`revisar_clips.py`** (BACKLOG 0.2): el script mira cada clip y marca lo sospechoso; el agente mira solo eso | tecnico, una vez; sirve para las próximas Sessions | 60-90 mil | el script, con tests |
| C | **Los ~35 clips que faltan, de a etapa**: `stock_pixabay buscar`, una hoja de miniaturas por etapa, elegir mirando la hoja, bajar ~45 de una, `revisar_clips` sobre todos, y una hoja por etapa con lo marcado | un agente con un modelo barato | 60-90 mil | los clips por etapa |
| D | **La hoja de recorrido v2**: la arma un script (de `hoja_reel.py`), una imagen por etapa de no más de 1600 px. El editor la mira una vez y el revisor también | editor y revisor, nuevos y con tope | 80-110 mil | APROBADO del revisor y OK del DJ |
| E | Render: `naturaleza.py validar` y después `render`, uno solo | CPU, horas | ~0 | el video |
| F | El revisor mira las uniones, los drops y el último tercio. Si algo bloquea, `partir` y `render --tramos` solo esos tramos | revisor, nuevo | 30-40 mil | APROBADO |
| G | Subir privado con el APROBADO; publica el DJ | yo | ~5 mil | el link |

**Total: 235-335 mil.** C y D son los que más se pueden pasar: si C llega a los 90 mil, se corta
y vuelve con lo que tiene.

### B: qué marca `revisar_clips.py`

Lo que bloqueó la Session 04 y la 05, en orden de cuánto costó encontrarlo:
- **Estelas y aviones**: líneas rectas y finas en el cielo, con la transformada de Hough en el
  tercio de arriba. Tiene que marcar 116206, la estela que vio el revisor y no el editor. Si no
  la marca, el script no sirve.
- **Sol tocando el horizonte**: el punto más brillante pegado a la línea del horizonte. Así se
  cuentan las puestas; tiene que haber una sola, la de Dodonpachi.
- **Hecho por el hombre**: bordes rectos largos y ángulos de 90°, que delatan casas, postes y
  caminos. Va a marcar de más, y está bien: lo marcado lo mira el agente.
- **Compresión y procesado**: bloques de 8x8 en las zonas lisas. Así se vio 221999.
- **Fase del día**: el brillo y la temperatura del cielo por clip. Así se ve si una etapa vuelve
  atrás.
- **Largo**: si el clip llega al plano tal cual, con RIFE x2 o con `estirar_mixto.py`. 35 de
  los 76 planos pasan los 90 s.

Por cada cuadro marcado saca un recorte de alrededor de 400 px, y los junta en una hoja por
etapa. El agente abre esas cinco hojas, no los clips. Hoy cada clip se mira entero, un cuadro por
segundo.

## Reglas de gasto

1. **Aviso antes de cada agente**: qué hace, cuánto cuesta más o menos, y espero el OK.
2. **Un encargo es una vuelta, con tope de herramientas**:
   - C, 40;
   - el editor en D, 25;
   - el revisor, 15.
   Si llega al tope, vuelve con lo que tiene y no sigue.
3. **Agentes nuevos, nunca retomados con SendMessage**: se les pasa un resumen corto. Retomar uno
   recarga todo lo anterior, como pasó con las almas: se estimaron 75 mil y fueron 243 mil.
4. **El modelo según la tarea**: buscar y bajar, uno barato; el criterio (editor y revisor), opus.
5. **Imágenes chicas y por etapa**: las hojas de 3000 px se leen enteras. Hasta 1600 px.
6. **Lo caro va después del APROBADO**: el render y la subida, nunca en paralelo con una revisión.

## Lo que decide el DJ antes de arrancar

1. **El plan y el tope de ~300 mil.**
2. **La puesta en el drop de Dodonpachi (92:03)**, o dónde la quiere.
3. ~~**Disco**~~: resuelto el 2026-10-31 ("hace limpieza antes"). El render de la 04 ocupó
   13,2 GB terminado y casi el doble mientras se armaba. Se liberaron 16 GB de intermedios y
   quedaron 38 GB libres:
   - los estirados y lentos de la 04;
   - las piezas del Reel en doble exposición;
   - 15 clips de Pixabay que no usa ninguna Session, entre ellos 116206;
   - la prueba de las almas.

   Los .mov finales, las mezclas y los stems siguen. Para volver a renderizar la 04 hay que
   regenerar antes sus estirados con `estirar_mixto.py`.
4. **Escuchar la mezcla entera antes del render.** El video se ata a esta mezcla: si después
   cambia un tema, se rehacen los planos de esa etapa.
