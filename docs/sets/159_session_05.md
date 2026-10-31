# Session 05 — el 159 en paisajes, plan eficiente

"Fijate como esta el set 159 en spoty empata rekor y hace sync y hace el plan para video
eficiente" (el DJ, 2026-10-31). El video sale del 159 tal como está en Spotify (v8c, 17 temas) y
con la receta de "una tarde" del 26/10. Este plan es para no repetir lo de ese día: una vuelta
del editor costó ~380 mil tokens, la del revisor ~230 mil, y la hoja quedó bloqueada igual.

**Tope: unos 300 mil tokens por el video entero, de la hoja a la subida**, contra los ~610 mil
que costó una sola vuelta de la hoja el 26/10. Cada número de abajo es una estimación. Antes de
lanzar cada agente le aviso al DJ el costo y espero el OK.

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
