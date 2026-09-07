# El circuito de vuelta — de la métrica del corte al criterio del set

Un corte publicado sin registro es una anécdota. Un registro que no se cruza
contra nada es una planilla. Esto define exactamente qué campo va contra qué,
quién lo corre y qué decisión cambia.

---

## La llave

**`publicaciones[].track.content_id`.**

Es `djmdContent.ID`, y es la misma llave que usan `data/pool.json` (`id`),
`data/mi_sonido.json` (`mas_sonados[].id`) y `data/redes/guion_cortes.json`
(`cortes[].content_id`). Sin ese campo la entrada no cierra el circuito y hay
que borrarla: un registro por título es un registro que no se puede cruzar
(hay remixes con el mismo título y títulos con espacios de más).

---

## Los cruces, campo contra campo

| De `data/publicaciones.json` | Contra | Qué pregunta responde |
|---|---|---|
| `metricas_7d.avg_view_seg` ÷ `ventana.largo_seg` | `ventana.gap_breakdown_drop_seg` | ¿La tensión larga retiene, o aburre? |
| `metricas_7d.avg_view_seg` ÷ `ventana.largo_seg` | `track.energy` (energía v2 calculada) | ¿La energía que rinde en 30 segundos es la misma que rinde en un set? |
| `metricas_7d.compartidos` + `guardados` ÷ `views` | `tipo_momento` | ¿Qué clase de momento genera acción y no sólo vista? |
| `metricas_7d.*` | `posicion_en_set.porcentaje_set` | ¿Un momento del minuto 20 rinde distinto a uno del minuto 70? |
| `track.content_id` | `djmdContent.DJPlayCount` + `djmdHistory` (`scripts/mi_sonido.py`) | **El cruce central**: ¿el track que rinde en corte es el mismo que se toca en vivo? |
| `track.label` | `mi_sonido.json → sellos[].lift` | ¿El sello de lift alto también rinde afuera, o es hábito personal? |
| `metricas_7d.clics_al_largo` | `set_origen` | ¿Qué concepto de set convierte del corte al video? |

Dos ratios que hay que usar en vez de los absolutos, porque los absolutos crecen
con la cuenta y confunden crecimiento con calidad:

- **retención del corte** = `avg_view_seg / largo_seg`
- **acción por vista** = `(compartidos + guardados) / views`

Con una cuenta chica y creciendo, `views` sube mes a mes por razones que no
tienen nada que ver con el track. Los ratios no.

---

## El cruce central, explicado

Esta es la razón de existir del registro.

Un track puede rendir en dos contextos que no son el mismo:

- **En 30 segundos verticales** gana el que tiene un momento legible sin
  contexto: breakdown largo, entrada de kick clara, algo reconocible.
- **En el minuto 40 de un set** gana el que sostiene sin llamar la atención:
  meseta, kick anclado, retiene sin que se pueda explicar por qué. Es
  literalmente lo que `docs/MI_SONIDO.md` describe como el registro
  "oscuro / hipnótico" — y es el registro que peor debería rendir en formato
  corto, porque su virtud es que no pasa nada.

Si eso se confirma, hay un dato accionable: **los tracks que sostienen el set y
los tracks que venden el set no son el mismo conjunto**, y elegir cortes
maximizando rendimiento vertical le miente a la marca. La consecuencia no es
dejar de publicar: es que el corte de un track hipnótico se arma distinto
(más largo, con más contexto antes) que el de un track heroico.

**El dato que hoy no existe:** 30 de los 60 cortes del guion caen en tracks con
`DJPlayCount = 0` — nunca sonaron. El set 84 (Sudbeat Sessions) tiene los seis
cortes en tracks sin tocar. Eso los vuelve el banco de pruebas más barato que
hay: validar un track cuesta un corte, no una noche.

---

## Quién corre qué

**`redes` (yo)** — completa `metricas_7d` a los 7 días exactos de cada
publicación. Nada de mirar antes: el ruido de los primeros tres días hace tomar
decisiones falsas. Una fila por publicación, sin borrar las que fueron mal.

**`analista`** — a partir de 12 entradas con métricas cerradas, cruza contra
`mi_sonido.json`, `pool.json` y la taxonomía de registros de
`docs/MI_SONIDO.md`, y devuelve `data/redes/rendimiento_tracks.json` con, por
`content_id`: retención del corte, acción por vista, `DJPlayCount`, registro
taxonómico y la diferencia entre rendimiento vertical y uso en vivo.

**`curador`** — usa esa diferencia como una señal más, nunca como la única. Un
track que rindió en un corte no gana un lugar en el set: gana una prueba.

---

## La primera hipótesis a testear

> **H1 — En formato vertical, el largo del breakdown predice la retención mejor
> que la energía del track.**

Va primera porque es la única de las tres candidatas que cambia una decisión
concreta y barata: los pesos del generador
(`data/redes/generar_cortes.py`, hoy 30% tensión / 20% energía). Si es falsa, se
invierten y los 60 cortes se recalculan en un segundo.

**Diseño — pareado por energía.** Hay una trampa que hay que sacar del medio: el
generador rankea usando gap *y* energía, así que si se agarran los cortes de gap
alto sin más, vienen con energía más alta de regalo (mediana 6.6 contra 5.8) y
el test mide las dos cosas mezcladas. La solución es fijar la energía y variar
sólo el gap. Los doce cortes ya están elegidos:

**Grupo A — gap largo** (mediana gap 83s, mediana E6.35)

| Set | # | E | gap | Track |
|---|---|---|---|---|
| 82 | 1 | 6.3 | 79s | Cendryma — Override — PURRFECTION |
| 87 | 1 | 6.7 | 92s | Emi Galván — Never Ending Summer — Mango Alley |
| 83 | 1 | 6.4 | 94s | Dmitry Molosh — The Moon Lights the Way — Mango Alley |
| 88 | 1 | 6.1 | 87s | Dmitry Molosh — Glide — Late Night Music |
| 89 | 1 | 5.9 | 71s | Emi Galván — Vibration — Melody Of the Soul |
| 80 | 3 | 6.6 | 79s | Navar & Dmitry Molosh — Small Wonders (Cattaneo & Vasami Remix) — Proportion |

**Grupo B — gap corto** (mediana gap 35s, mediana E6.2)

| Set | # | E | gap | Track |
|---|---|---|---|---|
| 80 | 5 | 6.0 | 29s | FAERO, Tom Pavicich, Analog Sense — The Landing — Balkan Connection |
| 81 | 5 | 6.4 | 31s | Ezequiel Arias — Eterno — Anjunadeep |
| 87 | 6 | 6.1 | 32s | Tali Muss — Garip — Heinz Music |
| 84 | 5 | 6.6 | 39s | D-Nox & Sharon Graziani — Shining (Hicky & Kalo Remix) — Plaisirs Sonores |
| 85 | 6 | 6.3 | 47s | Kostya Outta, Greta Meier, Alisha — Far Above — Mango Alley |
| 83 | 3 | 5.8 | 48s | Rauschhaus, GRAZZE — Canacona — Sudbeat |

Energía prácticamente igual (6.35 contra 6.2), gap 2,4 veces más largo en A.
Es lo más limpio que permite este material.

Doce semanas, uno por semana, **alternando A y B** para que el crecimiento de la
cuenta se reparta entre los dos grupos. Se fijan los confusores que se puedan
fijar: misma plataforma, mismo día y hora, mismo formato de texto, misma
plantilla de primer frame.

**Dependencia de calendario — mirarla antes de arrancar.** Los doce cortes salen
de nueve sets distintos (80, 81, 82, 83, 84, 85, 87, 88, 89), y ninguno existe
hasta que ese set esté grabado. Con la cadencia del plan — un video cada dos
semanas — los nueve tardan cuatro meses y medio, más que las doce semanas del
test. Dos salidas posibles, y la decisión es de Gonzalo:

- **Grabar en tandas.** Seis sets en dos o tres sesiones largas y después
  publicar. Es lo que vuelve viable el test y además destraba el corte semanal.
- **Empezar el test más tarde.** Publicar cortes igual desde el primer set
  grabado — se registran igual y sirven para todo lo demás — y arrancar el
  conteo de H1 recién cuando haya seis de los nueve sets disponibles.

Lo que no sirve es arrancar con dos sets y completar los grupos con lo que vaya
apareciendo: ahí el orden de grabación entra como variable y el test se cae.

**Métrica.** Mediana de `avg_view_seg / largo_seg` por grupo.

**Criterio de decisión, fijado de antemano.** Con 6 contra 6 no hay
significancia estadística y no vale la pena pretenderla; hay señal o no hay.

- Diferencia ≥ 25% a favor de A → subir el peso de tensión a 0.40 y bajar
  energía a 0.10.
- Diferencia ≥ 25% a favor de B → invertir: energía 0.35, tensión 0.15.
- Diferencia < 25% → **empate, no se toca nada** y se pasa a H2. Este caso es el
  más probable y hay que aceptarlo sin buscarle una historia.

**Lo que puede invalidar el test.** Que un corte enganche por algo ajeno al
audio (un comentario, un repost, el clima del algoritmo esa semana). Si una
publicación se sale tres veces de la mediana de su grupo, se anota en `notas` y
se reporta con y sin ella. No se borra.

---

### Las que siguen, por si H1 empata

**H2 — Los tracks del registro "oscuro / hipnótico" rinden peor en corte que en
set.** Cruce: `tipo_momento` + registro taxonómico contra retención del corte,
todo contra `DJPlayCount`. Es la hipótesis más interesante del proyecto porque
si se confirma, la marca tiene que elegir entre mostrar lo que la define y
mostrar lo que funciona. Va segunda y no primera porque necesita que la
taxonomía de `docs/MI_SONIDO.md` esté aplicada a los 60 tracks, y hoy cubre
alrededor de veinte.

**H3 — El sello nombrado en el texto mueve más que el artista.** Cruce:
`track.label` contra `mi_sonido.json → sellos[].lift` y contra acción por vista.
Si un sello chico devuelve tráfico, cambia a quién se le manda el video largo
antes de publicarlo. Requiere primero relevar a mano si esos sellos tienen
actividad real en redes — media hora de trabajo que todavía no se hizo.
