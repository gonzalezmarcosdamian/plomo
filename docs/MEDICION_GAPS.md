# Donde se delata el solver

Medicion del 2026-09-19. No mide reglas — eso lo hace `scripts/backtest_rules.py`.
Mide **las dimensiones que el solver ni mira**: la forma de la curva de energia, la
duracion de los tracks, la variedad de artistas y sellos, la repeticion de
tonalidad, y con que energia se arranca y se termina en proporcion al pico.

Se reproduce con:

```bash
python scripts/medir_gaps.py                 # tabla por corpus
python scripts/medir_gaps.py --json out.json
```

## Los tres corpus, y que puede decir cada uno

| corpus | sets | tracks | cobertura de energia | que vale |
|---|---|---|---|---|
| PROPIO (`data/set_targets/`) | 70 | 1200 | 100% | lo armo el solver |
| TOCADO (`data/tocados/`) | 25 | 340 | 100% | matiza, no refuta |
| REFERENCIA (`data/setlists/`) | 40 | 1059 | 34% energia, 46% key, 28% duracion | **el unico que refuta** |

Se excluyen los `[POOL]` y `set_990.json` (copia de trabajo del 106).

**El control de cobertura importa y esta hecho.** La referencia solo tiene energia
en los tracks que ademas estan en la biblioteca propia. Para que eso no invente
diferencias, cada metrica de forma se recalculo sobre el corpus PROPIO **diluido al
34%** (12 semillas). Donde el numero propio sobrevive a la dilucion, la diferencia
es real. Donde no, se dice.

La cobertura del dato en REFERENCIA es pareja a lo largo del set — 38% / 33% / 30%
por tercio —, asi que no hay un sesgo grande de "faltan justo las aperturas".

Piso de muestra: **40 observaciones** para afirmar algo, igual que el backtest.
Debajo de eso se marca `MUESTRA CORTA`.

---

## 1. Forma del set: la rampa no existe afuera

| metrica | PROPIO | PROPIO diluido al 34% | TOCADO | REFERENCIA | n |
|---|---|---|---|---|---|
| R2 del ajuste lineal energia~posicion (mediana por set) | **0.41** | 0.44 | 0.07 | **0.07** | 70 / 19 / 15 sets |
| Spearman posicion~energia (monotonia) | **+0.64** | — | +0.18 | **+0.11** | 70 / 19 / 15 sets |
| ganancia de ajustar una parabola en vez de una recta | +0.13 | — | +0.02 | +0.05 | idem |
| pasos planos (\|ΔE\| <= 0.3) sobre pares adyacentes | 45.0% | 48.6% | 29.5% | **19.6%** | 1130 / 315 / **163** |
| cambios de direccion por paso | 0.45 | 0.41 | 0.64 | 0.62 | idem |
| autocorrelacion lag-1 de los saltos | -0.05 | — | -0.42 | -0.36 | 70 / 20 / 10 sets |

Energia normalizada (z por set) por decil de posicion — la firma mas legible:

| decil | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| PROPIO | **-1.48** | -0.76 | -0.47 | -0.14 | +0.16 | +0.46 | +0.79 | **+1.16** | +0.78 | +0.23 |
| TOCADO | -0.77 | +0.28 | +0.42 | +0.34 | -0.45 | +0.09 | +0.01 | +0.04 | +0.29 | +0.30 |
| REFERENCIA | +0.10 | -0.16 | -0.04 | +0.33 | -0.01 | +0.14 | +0.41 | +0.11 | -0.04 | -0.00 |
| n REFERENCIA | 40 | 40 | 40 | 26 | 35 | 33 | 31 | 26 | 27 | 29 |

**Conclusion: el set propio es una rampa monotona (rho=+0.64) y ninguno de los dos
corpus reales lo es (+0.18 tocado, +0.11 referencia).** El set real no sube en rampa
NI en escalones con mesetas: oscila. Se mueve mas seguido (solo 19.6% de pasos
planos contra 45-49% propios, n=163 > 40) y alterna direccion mas (autocorrelacion
-0.36: sube, baja, sube). La energia real no tiene tendencia; el recorrido esta,
pero repartido en idas y vueltas, no en una pendiente.

Lo que no se puede afirmar: la longitud de las mesetas en referencia (mediana 1
track) es un artefacto de cobertura — una meseta necesita tracks consecutivos con
dato y la referencia tiene 34%. Con PROPIO diluido a la misma cobertura la meseta
tambien cae a 2. `MUESTRA CORTA` para esa metrica.

---

## 2. Longitud de los tracks: la hipotesis se cae, pero aparece otra cosa

| metrica | PROPIO | TOCADO | REFERENCIA | n |
|---|---|---|---|---|
| duracion mediana (seg) | 445 | 451 | 436 | 1189 / 339 / 301 |
| primer tercio | 434 | 447 | 438 | 397 / 114 / 110 |
| tercio medio | 448 | 452 | 429 | 381 / 105 / 93 |
| ultimo tercio | 456 | 454 | 439 | 411 / 120 / 98 |
| 20% mas energetico del set | 464 | 470 | 450 | 206 / 56 / 49 |
| correlacion posicion~duracion (mediana por set) | +0.18 | +0.10 | -0.00 | 69 / 19 / 14 sets |
| share de tracks > 8 min | 24% | 26% | 21% | idem |

**Conclusion: no hay diferencia. Los DJs de referencia NO usan tracks mas largos al
principio ni mas cortos en el pico** (correlacion -0.00, n=14 sets, 301 tracks). La
duracion del archivo no es una dimension curatorial en ningun corpus: ignorarla no
nos delata. Caveat: en referencia la duracion solo existe para los 301 tracks que
ademas estan en la biblioteca (28%).

Lo que si aparece, del reloj del historial (`hora` en `data/tocados/`):

| metrica | valor | n |
|---|---|---|
| minutos reales por track tocado | **6.8** (p10 5.2, p90 8.4) | 315 |
| fraccion del track que suena | 0.93 (p10 0.70) | 314 |
| tracks por hora implicitos en los sets propios | **9.0** (p10 5.7, p90 14.4) | 70 sets |
| lo que dice `densidad.tracks_por_hora` | **12** | regla |

**El segundo hallazgo: la regla de densidad esta 33% arriba de la practica y de la
realidad.** A 6.8 min por track se tocan 8.8 tracks por hora, no 12. Solo 22 de 70
sets propios llegan a 12/h; la mediana es 9.0. Y como los sets se arman contra la
duracion declarada sin mirar duraciones reales, **41% de los sets propios (29/70) no
tienen musica suficiente para cubrir su propia duracion declarada** (cobertura
mediana 1.02, p10 0.64), mientras otro 39% se pasa de 20%. El margen para estirar,
saltar y leer la pista que la regla dice buscar, en la mitad de los sets no existe.

---

## 3. Variedad: el gap esta entre sets, no adentro de cada set

| metrica | PROPIO | TOCADO | REFERENCIA | n |
|---|---|---|---|---|
| artistas distintos / tracks (por set) | 0.83 | 0.58 | 0.81 | 70 / 21 / 40 sets |
| tope de un mismo artista AJENO por set (sin IDs, sin el DJ) | 2.0 (p90 8) | 4.0 (p90 7) | 2.0 (p90 4) | 70 / 21 / 40 sets |
| sets con >=3 del mismo artista ajeno | 36% | 67% | 28% | idem |
| sellos distintos / tracks con sello (por set) | 0.76 | 0.73 | 0.83 | 70 / 21 / **21 sets** |
| share del sello mas repetido (por set) | 0.18 | 0.25 | 0.22 | idem |
| **HHI de sellos a nivel corpus** | **0.0246** | 0.0244 | **0.0121** | 1165 / 329 / 351 |
| sellos distintos rarefaccionados a 351 tracks | **128** | 123 | **176** | idem |
| artistas distintos rarefaccionados a 351 tracks | **154** | 122 | **263** | 1200 / 340 / 936 |
| artistas distintos a 120 tracks, **un DJ por vez** | 77.5 | — | 92 (68 / 92 / 108) | `MUESTRA CORTA`: 3 DJs |
| **tracks reusados entre sets del mismo autor** | **26%** | — | **4%** | 1199 / — / 931 |

**Conclusion 1: adentro de un set, nuestra variedad es igual a la real** (0.83 vs
0.81 artistas distintos; tope 2 vs 2). El problema de repeticion de artista que
existe en el corpus propio es de los showcases (p90=8, sets 40-45), no del solver.

**Conclusion 2: el gap real es de paleta, no de set.** A igual cantidad de tracks,
la referencia usa 176 sellos donde nosotros usamos 128, y 263 artistas donde
nosotros usamos 154; nuestra concentracion de sellos duplica la de referencia
(HHI 0.0246 vs 0.0121, top-5 28% vs 16%). Y 26% de los track-slots propios son
reusos de un track ya usado en otro set, contra 4% en referencia (Mellino 1%,
Guy J 0%, Digweed 1%, Eze Arias 10%). No es un defecto del solver: es el tamano y
la forma de la biblioteca. El solver no puede inventar sellos que no tiene.

Caveats: (a) los sellos de referencia solo se conocen para los 351 tracks que
tenemos, lo que sesga **a favor** de nuestros sellos — el gap medido es el piso;
(b) la comparacion rarefaccionada mete 12 DJs contra 1; controlando por DJ el gap
baja de 154-vs-263 a 77.5-vs-92 y queda `MUESTRA CORTA` (solo 3 DJs tienen 120+
tracks); (c) 12% de los tracks de referencia son ID sin identificar y estan
excluidos del conteo de artistas.

### Anio de edicion

| metrica | PROPIO | TOCADO | REFERENCIA | BIBLIOTECA |
|---|---|---|---|---|
| anio mediano | 2024 | 2023 | **2025** | 2024 |
| share >= 2025 | 40% | 39% | **55%** | 37% |
| share <= 2022 | 38% | 39% | **18%** | 37% |
| n | 1130 | 320 | 282 | 2183 |

**Conclusion: la referencia toca mas nuevo que nosotros** — 55% de los ultimos dos
anios contra 40%, y menos de la mitad de catalogo viejo (18% vs 38%). Nuestros sets
reproducen la distribucion de la biblioteca (37% >= 2025), es decir: no eligen por
novedad, eligen por lo que hay.

`SESGO CONOCIDO, no concluyente`: el anio de un track de referencia solo se conoce
si lo tenemos, y muchos los tenemos **porque** los escuchamos en esos mismos
setlists recientes. La direccion del sesgo infla el numero de referencia. Vale como
sospecha fuerte, no como refutacion.

---

## 4. Repeticion de tonalidad: no hay gap — era un artefacto

| metrica | PROPIO | PROPIO diluido al 46% | TOCADO | REFERENCIA | n |
|---|---|---|---|---|---|
| keys distintas / tracks con key | 0.51 | **0.66** | 0.60 | 0.64 | 70 / 21 / 27 sets |
| share de la key mas repetida | 0.25 | 0.33 | 0.25 | 0.20 | idem |
| pares adyacentes con la MISMA key | 18.3% | 17.7% | 20.3% | **17.8%** | 1117 / 315 / **297** |

**Conclusion: un set real no usa mas tonalidades que uno nuestro.** La diferencia
cruda (0.51 vs 0.64) desaparece al submuestrear el corpus propio a la cobertura de
key de la referencia (0.66 vs 0.64): era un artefacto de medir menos tracks. Y la
repeticion literal de tonalidad entre tracks consecutivos es identica en los tres
corpus (18.3 / 20.3 / 17.8%, n=297 en referencia). La regla
`armonia.penal_misma_key_desde` no esta ni de mas ni de menos: describe algo que
pasa igual en todos lados.

Donde si hay gap es en el **BPM**, que se midio de paso porque tiene mejor
cobertura (55%):

| metrica | PROPIO | TOCADO | REFERENCIA | n |
|---|---|---|---|---|
| **recorrido de BPM por set (max-min)** | **4.0** | 4.0 | **10.0** | 70 / 21 / 27 sets |
| pares consecutivos con el mismo BPM (±0.5) | 28% | 30% | 20% | 1117 / 315 / 296 |
| Spearman posicion~BPM | +0.31 | +0.41 | +0.34 | 69 / 19 / 22 sets |

**Un set de referencia recorre 10 BPM; los nuestros, 4.** Y la cobertura parcial
solo puede **achicar** un recorrido observado, asi que 10 es un piso. El BPM si
sube hacia el final en los tres corpus por igual (+0.31/+0.41/+0.34): la tendencia
de tempo es lo unico de la forma que compartimos con la realidad.

---

## 5. El principio y el final

| metrica | PROPIO | TOCADO | REFERENCIA | n |
|---|---|---|---|---|
| energia media del 15% inicial | 4.84 | 5.40 | 5.58 | 70 / 25 / 20 sets |
| **inicio / pico** | **0.63** | 0.81 | **0.77** | idem |
| sets que arrancan <= 70% del pico | **63%** | 24% | **15%** | idem |
| sets que arrancan >= 80% del pico | 17% | 52% | 20% | idem |
| energia media del 15% final | 6.03 | 5.85 | 5.79 | idem |
| cierre / pico | 0.83 | 0.84 | 0.78 | idem |
| sets que terminan >= 90% del pico | 39% | 28% | 15% | idem |
| sets que terminan <= 70% del pico | 11% | 8% | 20% | idem |
| puntos de energia del pico al cierre | 1.23 | 1.03 | 1.62 | idem |
| posicion relativa del pico | 0.82 | 0.56 | 0.57 (ya medido) | idem |

**Conclusion: el set real arranca casi donde termina, y nosotros arrancamos un
escalon mas abajo que nadie.** La referencia entra al 77% de su pico y el DJ
propio, tocando, al 81%; el solver entra al 63%, y en 63% de los sets arranca
debajo del 70% del pico contra 15% en referencia. Ese arranque bajo es la otra cara
de la rampa del punto 1: para que la recta suba, el solver tiene que empezar abajo.

Del otro lado: **la referencia baja mas al cierre que nosotros** (cae 1.62 puntos
desde el pico contra 1.23; 20% de los sets terminan debajo del 70% del pico contra
11% nuestro). El "nunca terminar arriba" de `energia.baja_minima_al_cierre` apunta
en la direccion correcta pero se aplica poco: 39% de los sets propios terminan arriba
del 90% del pico contra 15% de los de referencia.

`MUESTRA CORTA` para todo este bloque en referencia: **20 sets**, debajo del piso de
40. Los dos numeros grandes (inicio/pico 0.63 vs 0.77, y 63% vs 15% de arranques
bajos) son gruesos y van en la misma direccion que TOCADO, que tiene cobertura 100%
— pero como veredicto formal no alcanza. Para cerrarlo hacen falta mas setlists con
energia.

---

## Resumen: donde se delata el solver

Ordenado por tamano del gap y por solidez de la muestra.

| # | dimension | propio | real | muestra | veredicto |
|---|---|---|---|---|---|
| 1 | monotonia de la energia (Spearman) | +0.64 | +0.11 / +0.18 | 15+19 sets | **se delata** |
| 2 | pasos planos de energia | 45-49% | 19.6% | n=163 | **se delata** |
| 3 | arranque en proporcion al pico | 0.63 | 0.77 / 0.81 | 20+25 sets | se delata (muestra corta) |
| 4 | recorrido de BPM por set | 4.0 | 10.0 | 27 sets | **se delata** |
| 5 | variedad de paleta (sellos/artistas, HHI) | 0.0246 | 0.0121 | n=351 | se delata, pero es la biblioteca |
| 6 | reuso de tracks entre sets | 26% | 4% | n=931 | se delata, pero es la biblioteca |
| 7 | anio de edicion | 40% nuevo | 55% nuevo | n=282 | sospecha con sesgo conocido |
| 8 | densidad declarada vs real | 12/h (regla), 9.0/h (sets) | 8.8/h | n=315 | la regla esta 33% arriba |
| 9 | repeticion de tonalidad | 18.3% | 17.8% | n=297 | **no hay gap** |
| 10 | duracion de los tracks | 445 s | 436 s | n=301 | **no hay gap** |
| 11 | variedad adentro de cada set | 0.83 | 0.81 | 70+40 sets | **no hay gap** |

Nada de esto cambia una regla. Lo que sigue, si se quiere cambiar algo, es el ciclo
de siempre: `R.proponer(ruta, valor, evidencia)`, el numero a la mesa, y recien
despues `R.aplicar`.
