# Lo que el solver no modela

Medido el 2026-09-19 sobre los tres corpus: `data/set_targets/` (73 sets del
solver, 1264 tracks), `data/tocados/` (19 tandas reales del DJ, 307 tracks, dato
completo) y `data/setlists/` (40 setlists de Cattaneo, Digweed, Sasha, Nick
Warren, Guy J, Mellino, Maze 28, Eze Arias, Simon Vuarambon, Colyn, Kamilo;
1059 tracks).

**Dos advertencias sobre los números.** (1) De los 73 sets del solver, sólo 29
cumplen hoy las tres reglas duras de punta a punta — el resto se armó a mano o
por otro camino. Donde hace falta comparar contra "lo que produce el solver" uso
esos 29 y los llamo `solver_puro`. (2) Los setlists de referencia tienen energía
en el 34% de los tracks: sólo cuento pares donde las dos posiciones consecutivas
tienen dato, así que las métricas de transición no están infladas por huecos.
Para la única métrica que sí se infla con datos ralos (reversiones) hice el
control: submuestreé los sets propios al mismo 34% y el resultado no se mueve.

| | solver_puro | tocado | referencia |
|---|---|---|---|
| escalón de energía mediano | **0.20** | 0.60 | 0.90 |
| transiciones con escalón >= 1.3 | **0.2%** | 18.6% | 36.8% |
| transiciones que bajan más de 0.4 | **4.9%** | 27.4% | 36.3% |
| ídem, antes del pico | **1.1%** | 19.6% | 35.1% |
| reversiones de >=1.0 cada 20 tracks | **1.9** | 5.4 | 9.0 |
| rango de energía del set | **2.8** | 3.5 | 5.0 |
| posición del pico | **82%** | 67% | 38% |
| transiciones con salto Camelot >= 2 | **0.0%** | 45.5% | 70.0% |
| recorrido de BPM dentro del set | **4.0** | 4.0 | 13.0 |

---

## 1. El set no tiene secciones: tiene una rampa

**Qué se mide.** Tamaño de los escalones de energía, cuántas veces el set cambia
de dirección con prominencia >= 1.0, y dónde cae el pico.

**Qué dice el dato.** El escalón mediano del solver es 0.20 contra 0.60 de lo
que el DJ toca de verdad y 0.90 de los sets de referencia: se mueve a un tercio
de la escala real. Cambia de dirección 1.9 veces cada 20 tracks contra 9.0 de la
referencia — y el control por submuestreo lo confirma: al mismo 34% de
cobertura, los sets propios dan 2.5 y los de referencia 9.0. El pico cae en el
82% del set en 73 de 73 casos, porque `arc_target()` lo pone ahí por
construcción. Todo esto sale de dos líneas de código: el arco es una recta hasta
el pico y otra recta para abajo, y `max_retroceso_en_subida = 0.4` prohíbe por
regla dura lo que pasa en el 35% de las transiciones de referencia.

**Cómo se implementa.** Dos cambios en el costo, ninguno toca el beam.

- `arc_target()` deja de ser una recta y pasa a ser una poligonal con anclajes
  configurables: presentación plana (0-25%), desarrollo en subida (25-58%),
  **quiebre** (58-65%, con caída pedida de 1.0-1.5), vuelta (65-88%) y cierre.
  Es el mismo término de costo, con otro `tgt`.
- Una **cuota de contraste**, implementada igual que `mezcla_objetivo`: el nodo
  lleva el contador de transiciones con escalón >= 1.0 y se cobra el desvío
  **simétrico** contra una tasa objetivo. Lo simétrico es la parte importante, y
  la lección ya está aprendida con los géneros: si sólo se cobra el exceso, la
  cuota nunca se alcanza. Tasa sugerida: la de `tocado` (28%), no la de festival
  (49%).
- `max_retroceso_en_subida` pasa de duro a penalizado, o al menos se suspende
  dentro de la ventana de quiebre. Hoy es la regla que hace imposible el punto de
  quiebre, no un guardarraíl.

---

## 2. Camelot <= 1 es la regla dura más cara y la menos respaldada

**Qué se mide.** Distancia Camelot canónica (`plomo.camelot.distance`) entre
consecutivos, sólo en pares con las dos keys conocidas.

**Qué dice el dato.** En los setlists de referencia el 70% de las transiciones
salta 2 o más, y el 61% salta 3 o más. En lo que el DJ toca en vivo: 45.5% y
27.8%. En el solver: 0%, porque está prohibido. `rules/curaduria.json` ya tiene
escrito su propio umbral de refutación — "si el backtest muestra >15% de saltos
>=2 en sets reales, la regla tiene que pasar de dura a penalizada". Está cuatro
veces por encima, en el corpus no circular y también en el propio. Y no es una
regla aislada: prohibir el salto es lo que obliga al solver a quedarse en la
rueda, que es el síntoma que ya se atacó con `penal_quedarse` sin tocar la causa.
Mismo patrón en BPM: recorrido de 4.0 dentro del set contra 13.0 de la
referencia, con el techo de ±2 por transición haciendo de tapón.

Hay además una pista de cómo lo hacen: cuando saltan de rueda, el escalón de
energía es **más grande**, no más chico (referencia: 1.00 mediano con salto >=2
contra 0.80 con salto <=1; tocado: 0.70 contra 0.50). El salto de key no se
disimula, se usa — va pegado al cambio de sección. O sea que los gaps 1 y 2 son
el mismo gap visto de dos lados.

**Cómo se implementa.** `max_camelot_dist` baja de dura a 3 (el choque real es
de 4 para arriba) y se cobra `PESO_SALTO_GRANDE * (d - 1)` para d >= 2, con cuota
por set igual que arriba. Precaución obligatoria: no copiar el 70% de festival.
El precedente de `penal_quedarse` ya fijó el criterio — se apunta a lo que el DJ
hace cuando decide en vivo, no a lo que hace Digweed.

---

## 3. El tiempo no existe en ningún lado del solver

**Qué se mide.** `dur_seg` ya está en `data/pool.json` para los 2329 tracks y
`select_set.py` no lo lee ni una vez. Comparo la duración pedida (`duration_h`)
contra la suma real de los tracks elegidos.

**Qué dice el dato.** Con blend de 1.5 min por transición, el 44% de los sets se
queda corto más del 10% y el 36% se pasa más del 10%: **8 de cada 10 sets no
entran en el horario que pidieron**. Los tracks van de 2.1 a 15.2 minutos
(mediana 7.2; p10 5.5; p90 8.4) y entre el más largo y el más corto de un mismo
set hay 3.2 minutos de diferencia en la mediana. Encima, `densidad.tracks_por_hora
= 12` no coincide con lo medido: en `data/tocados` el hueco mediano entre track y
track es de 6.7 minutos, o sea 9 tracks por hora.

La prueba de que esto duele ya está escrita en el repo:
`data/set_configs/terraza_atardecer.json` tiene un campo `_porque_n` con la
cuenta hecha a mano ("46 y no 36... los 46 suman 307 min brutos: con blend de 3
min da 178 min") y una lista de 16 `exclude_ids` que son, textualmente, los
tracks de menos de 5 minutos. El humano está haciendo a mano lo que el solver
podría hacer solo — y lo hizo en 1 de los 20 configs.

**Cómo se implementa.** Tres cosas, de menor a mayor esfuerzo.

- **Lo más barato y de mayor efecto:** `arc_target(i, n, ...)` usa
  `t = i / (n - 1)`. Tiene que usar `t = segundos_acumulados / segundos_totales`.
  Con eso el pico cae en el minuto correcto y no en el track número correcto, que
  con temas de 4 y de 9 minutos no es lo mismo. Son tres líneas: el nodo ya viaja
  con estado acumulado, se le suma un contador de segundos.
- Costo por desvío del reloj: `abs(segundos_acumulados - objetivo(i))`, peso bajo.
- `n` deja de ser un número a ojo en el config y se deriva de `duration_h`, la
  duración mediana del pool filtrado y el blend.

---

## 4. La energía, que pesa 3.0, está apoyada sobre una detección rota

**Qué se mide.** Los cues guardados en `djmdCue` (2331 tracks con marcadores) y
la fórmula de `src/plomo/energy_v2.py`.

**Qué dice el dato.** El 66% de la biblioteca tiene `Bass IN` en 0 ms, que no es
"el bajo entra enseguida" sino "no se detectó": esos tracks cobran 0.3 de
`intro_score` en vez de entre 1.0 y 2.0. Peor: 132 tracks (6%) no tienen `DROP`
ni `Breakdown` detectados y pierden hasta 5.0 puntos de la fórmula — su energía
mediana es **1.4 contra 5.9** del resto. Con E=1.4 y un escalón máximo de 1.3,
esos tracks no pueden ir al lado de nada que pase de 2.7: quedan desterrados a la
primera posición de un set, o a ninguna. Se ve en el uso: aparecen en algún set
el 24% de las veces contra el 39% del resto del pool.

No es un gap de curaduría, es un gap de dato, pero entra en la lista porque el
desvío del arco pesa 3.0 — es el término dominante del costo — y está calculado
sobre un eje que tiene el 6% de la biblioteca clavada en el piso por un fallo de
detección.

**Cómo se implementa.** Nada en `select()`. Se vuelve a correr la detección sobre
los 132 sin DROP y los ~1540 sin Bass IN, o `calculate_energy_v2()` normaliza
sobre los componentes efectivamente detectados en vez de sumar cero por los que
faltan. Lo segundo es una tarde y no requiere tocar audio.

---

## 5. El sello: el problema no es que estén pegados, es la concentración

**Qué se mide.** Sellos repetidos en posiciones consecutivas y máximo de tracks
del mismo sello por set.

**Qué dice el dato.** Contra lo que sugiere el aviso de `audit_sets.py`, la
adyacencia no es el problema: 6.3% en los sets del solver contra 6.2% en los de
referencia. Lo que sí se separa es la concentración — el sello más repetido
aparece 3.6 veces por set en el solver y 2.3 en la referencia, y la variedad
(sellos distintos por track) da 0.72 contra 0.85.
`repeticion.max_por_sello_en_set = 4` está escrito en las reglas y no lo aplica
nadie: ni el solver ni la auditoría.

**Cómo se implementa.** Contador de sello en el estado del nodo, igual que
`gen_cnt`, y costo creciente a partir del tercero. Es copiar el bloque de
`mezcla`. Impacto chico, costo casi nulo.

---

## 6. El track como objeto: lo que falta es la voz, y no hay dato

Acá corresponde desmentir una sospecha antes que confirmarla. **Dos breakdowns
largos seguidos no son un problema medible hoy**: pasa en el 1.7% de los pares
del solver y en el 1.6% de los tocados, sin diferencia. Y el breakdown ya está
parcialmente adentro de la energía — `corr(breakdown_s, energía) = +0.69` sobre
2198 tracks, porque `energy_v2` suma `breakdown_dur / 48`. No inventemos una
regla para algo que el escalar ya captura.

**La voz sí falta, y todavía no se puede modelar**: sólo el 4% de la biblioteca
(97 de 2329) tiene alguna marca vocal en la metadata (feat / ft / vocal / with),
así que medir "dos vocales seguidos" da 0.1% en los tres corpus y no significa
nada. No hay campo en `djmdContent` que sirva de atajo: `Rating` tiene 9 tracks
cargados, `ColorID` tiene 1, `MyTag` no existe.

**Cómo se implementa.** Primero el dato, después la regla. Un detector de voz
sobre la biblioteca — `librosa` ya es dependencia de `cue_engine.py`, y separar
armónico/percusivo más un filtro en 200-4000 Hz alcanza para un flag binario —
que escriba `vocal: true/false` en `dump_pool.py`. Recién ahí tiene sentido una
regla dura de "no dos vocales seguidos" y una cuota de vocales por set. Antes de
eso, cualquier regla sobre voz es una opinión sin dato.

---

## Orden de ataque

1. **Secciones y contraste** (gap 1). Es lo único de la lista que el DJ escucha
   en los primeros diez minutos.
2. **Camelot de dura a penalizada** (gap 2). Sin esto el gap 1 no tiene material
   para construir el quiebre: el solver no puede cambiar de aire si sólo puede
   moverse un paso de rueda.
3. **Reloj en vez de índice** (gap 3, primer punto). Tres líneas, y arregla dónde
   cae el pico de verdad.
4. **Reparar la detección de energía** (gap 4). No cambia el solver: cambia el
   mapa sobre el que el solver decide.
5. Sello (gap 5) y voz (gap 6) son de segundo orden.

**El recordatorio de siempre.** Los gaps 1, 2 y 3 están medidos contra
`data/setlists`, que es el único corpus capaz de refutar una regla propia. Los
gaps 4 y 5 salen de la biblioteca, que no refuta nada: describen el estado del
dato. Y ningún número de acá autoriza a copiar el festival — la referencia dice
dónde está el techo, `data/tocados` dice dónde está el DJ.
