# Plan: arreglar el orden de los sets — v2

v1 escrita el 2026-09-12 por la mañana. **Esta v2 es del 2026-09-12 a la tarde,
con las fases 1, 2, 4, 5 y 6 YA EJECUTADAS.** Lo que sigue dice qué se hizo, qué
dieron los números, y qué queda — incluida la fase de descargas, que en la v1 no
existía.

Pedido original: *"mejorar el orden de los sets armados, se hizo mucho lío"*,
*"mucha energía sin que los BPM se vayan para arriba"*, *"Maze lo hace muy bien"*,
*"que todo esto dé un salto de calidad"*.

---

## Lo que se ejecutó, con el antes y el después

| | antes | después |
|---|---|---|
| Tracks E≥7 con BPM ≤122 | 9% (16 de 180) | **60%** (122 de 204) |
| Transiciones flojas en los sets armados | 488 | **220** |
| Sets con cero transiciones flojas | — | **27 de 67** |
| Transiciones que no mueven la rueda (mediana) | 38% | **27%** |
| Setlists de referencia en el corpus | 6 | **40** |
| Transiciones medibles para el backtest | 63 | **243** |

### Fase 1 — La energía dejó de contener al BPM ✔

`src/plomo/energy.py` sumaba `(bpm - 118) / 8 * 3` sobre 10: el 30% del score
era el tempo. Un tema de 118 BPM tenía techo E7.0 por construcción. Se sacó ese
componente y se reescalaron los otros cuatro —intro, breakdown, drop, largo del
peak— a 10.

Los 1883 tracks se recalcularon **desde los cues ya guardados**, sin re-analizar
audio: los markers v8 en `djmdCue` tienen Bass IN, Breakdown, DROP y Mix-OUT, que
es exactamente lo que la fórmula necesita (`scripts/recalcular_energia.py`). El
valor viejo quedó guardado como `v1:X.X` en el comentario de cada track.

Los `e_lo`/`e_hi` de los configs se tradujeron **por percentil** y no por delta
(`scripts/migrar_configs_energia.py`): "E5.4" no quería decir 5.4, quería decir
"el track del percentil 42".

### Fase 2 — Una sola distancia Camelot ✔

Había dos definiciones y el solver optimizaba con una mientras el auditor medía
con la otra. Queda la de `src/plomo/camelot.py`. Impacto medido: 0-3% de las
transiciones. Era higiene, no la causa.

### Fase 4 — La escalera camina ✔

Quedarse en la misma rueda costaba cero, y por eso pasaba el 38% de las veces
contra el 23% de lo que el DJ toca en vivo. Se agregaron dos reglas a
`rules/curaduria.json` (v1.1.0), con su porqué y su evidencia:
`armonia.penal_quedarse_en_la_rueda` = 0.8 y `armonia.monotonia_desde` = 2.

### Fase 5 — El auditor mira el set, no solo el par ✔

`audit_sets.py` ahora reporta % de transiciones que no mueven la rueda, corrida
monótona más larga, sellos pegados y `corr(BPM, energía)`. **Encontró sets con
cero transiciones flojas y 55% de quietos**: esa era la ceguera que hacía dudar
del resultado.

### Fase 6 — Se rehicieron los 67 sets ✔

Los que tienen config se reseleccionaron. Los viejos —curados a mano en sesiones
anteriores— se **reordenaron sin tocarles un track** con
`scripts/reordenar_set.py`. Ese script no reusa el solver de selección a
propósito: aquel filtra por restricciones duras y con la lista fija casi nunca
existe una permutación que las cumpla todas, así que devolvía "sin solución" para
sets que se podían mejorar mucho. El nuevo penaliza en vez de filtrar, y siempre
devuelve el mejor orden posible. Mejoró 37 sets; los más rotos, 25→8, 23→9 y
20→7 transiciones flojas.

---

## Lo que los DJs de referencia dicen ahora que el corpus es grande

Con 40 setlists y n=243 (antes n=63):

- `armonia.max_camelot_dist = 1` → **REFUTADA**: 58% de las transiciones reales
  la violan, media 2.28 hops. Bajó del 73% que daba con n=63, pero sigue muy
  arriba del umbral del 15%.
- `bpm.max_salto = 2.0` → **REFUTADA**: 27%, media 2.52, máximo 44.
- `energia.max_escalon = 1.3` → **MUESTRA INSUFICIENTE**. El backtest la daba por
  refutada con **n=9**; se le puso un piso de 40 transiciones para animarse a
  refutar. Un veredicto falso es peor que ninguno, porque después se usa para
  cambiar una regla.

**Maze 28 sigue siendo el contraejemplo que importa.** En su mix de Proton baja
de 130 a 117 BPM, salta hasta 6 BPM entre temas —la regla permite 2— y en
Camelot es más estricto que todos: 0 de 10 por encima de 1. Confirma el pedido
—la energía no la pone el tempo— y a la vez desaconseja relajar Camelot.

---

## Fase 7 — Descargas *(pendiente, es la que sigue)*

El corpus de 40 setlists produce una lista de compras que no es "lo que salió"
sino **lo que se está tocando**. La genera `scripts/lista_de_compras.py`, que
ordena por cuántos DJs distintos tocaron cada tema.

**Qué hay hoy: 705 temas del corpus que no están en la biblioteca, 295
confirmados en Muzpa**, en `data/batch_referencia_2026-09-12.txt`.

Artistas que varios DJs tocan y de los que casi no hay nada:

| Artista | DJs que lo tocan | apariciones | en biblioteca |
|---|---|---|---|
| Sasha | 3 | 7 | 2 |
| The Chemical Brothers | 3 | 4 | 1 |
| COQUEIT | 3 | 3 | 1 |
| Drunken Kong | 3 | 3 | 1 |
| Fran Garay | 2 | 4 | **0** |
| D-Shift | 2 | 4 | 1 |
| Rezident | 2 | 3 | **0** |
| Slam | 2 | 3 | **0** |
| Deestopia | 2 | 3 | 1 |

Sellos con presencia fuerte en los sets y poca en la biblioteca: **Early
Morning** (4 apariciones, 9 tracks), **Moments** (3 / 13), **Keep My Letters**
(2 / 3), **Movement Recordings** (2 / 6), **Warung Recordings** (2 / 9),
**Global Underground** (2 / 6). Van al radar fijo.

**Cómo se ejecuta:**

1. Revisar el batch y sacar lo que no sea del estilo — 295 temas de 40 sets
   incluyen cosas que entraron por un b2b o un cierre raro.
2. `python scripts/muzpa_download.py --batch data/batch_referencia_2026-09-12.txt`
3. `python scripts/import_all.py` → Rekordbox **File > Import > Add Folder**
   (RB6 no auto-importa) → esperar el análisis → cerrar RB.
4. `python scripts/post_import.py` → `python scripts/import_all.py --archive`
5. `python scripts/dump_pool.py` y `python scripts/build_views.py`

**Criterio de éxito:** que los artistas de la tabla pasen de 0-2 tracks a por lo
menos 4, y que la cobertura del corpus contra la biblioteca propia suba del 6-30%
actual — eso es lo que haría que los setlists de referencia midan transiciones
con energía, que hoy es el dato que falta.

**Ojo con el volumen.** 295 temas son unas cuatro horas de descarga y ~3 GB. Si
hay que priorizar, el orden del archivo ya es el correcto: primero lo que tocó
más de un DJ.

---

## Lo que queda después de las descargas

- **Fase 3, el BPM como regla blanda.** No se hizo: cambiar dos reglas en la
  misma vuelta hace imposible saber cuál mejoró qué. El experimento está
  definido: rearmar los sets con `max_salto` en 2.0, 3.0 y 4.0 y comparar
  artistas distintos, movimiento de Camelot y subida de BPM al pico. Decide la
  escucha entre las opciones que los números no descarten.
- **Energía en el corpus de referencia.** Muzpa da key y BPM pero no energía, que
  la calcula el pipeline propio sobre el archivo. Por eso `energia.max_escalon`
  sigue sin evidencia externa. Se destraba bajando los temas (Fase 7).
- **Los conflictos de `repeticion.*`**, marcados hace rato: `max_por_artista`
  dice 2 en la regla y 1 en el código; `separacion_minima` dice 5 y 3. Merece su
  propia vuelta.
- **Los 8 sets que siguen con 8 o más transiciones flojas.** El reordenador no
  puede arreglarlos porque el problema no es el orden: es que la selección no
  cierra. Hay que rearmarlos eligiendo de nuevo, o aceptar que son listas de
  referencia y no sets para tocar.

---

## Qué NO hacer

- **No relajar Camelot todavía**, aunque el backtest lo dé refutado dos veces
  seguidas. Los DJs de festival lo violan; Maze, que es la referencia elegida,
  no. No es una ley universal: depende del registro.
- **No confiar en "0 transiciones flojas"** solo. Ahora hay métricas de set;
  usarlas.
- **No refutar con muestras chicas.** Ya pasó con n=9.
- **No bajar los 295 temas sin mirarlos.** El corpus incluye b2b y cierres que no
  son el estilo.
