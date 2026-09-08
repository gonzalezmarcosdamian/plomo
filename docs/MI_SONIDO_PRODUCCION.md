# Mi Sonido — perfil de producción medido

Este documento existe para que un agente productor no tenga que preguntar "¿qué
te gusta?". Todo lo que sigue sale de una medición sobre la biblioteca y el
historial de reproducción reales. Si un número no está acá, es porque no se
midió — y entonces no se afirma.

`docs/MI_SONIDO.md` es el documento hermano: ahí está la intención y la
taxonomía de registros, escritas a mano. Acá está la señal.

**Fecha de la medición:** 2026-09-08
**Muestra:** 1816 tracks en biblioteca, 348 tocados alguna vez, 510
reproducciones registradas en Rekordbox.

---

## 0. De dónde sale cada número

| Bloque | Herramienta | n |
|---|---|---|
| Gustos por lift | `data/mi_sonido.json` | 1816 / 348 |
| BPM, duración, tonalidad | consulta directa a `djmdContent` | 1816 |
| Estructura, LUFS, balance, ancho | `scripts/reverse_engineer.py` | 48 más tocados |
| Grupo de control | `scripts/reverse_engineer.py` | 20 nunca tocados |
| Densidad de arreglo | `data/arreglos_medidos.json` (7) + 2 medidos acá | 9 |
| Repiques | `scripts/repiques.py` | 9 |
| Color melódico | `scripts/color_melodico.py` sobre stems cacheados | 21 |

Las mediciones crudas quedaron guardadas para no volver a pagarlas:
`data/recetas/mas_tocados_48.json`, `data/recetas/control_nunca_tocados_20.json`,
`data/recetas/color_melodico_21.json` y
`data/recetas/arreglos_extra_candidatos.json` (los 8 candidatos extra de arreglo,
incluidos los 6 que el detector descartó — sirven para calibrarlo).

Los 48 son los más sonados con archivo localizable (49 rutas, una duplicada por
un bug de matcheo que se explica en el punto 8). El control son 20 tracks nunca
tocados, filtrados al mismo género, BPM 118-126 y duración 6-10 min, para que la
comparación no sea contra otro estilo.

---

## 1. Qué suena y qué no

El ranking no es "quién sonó más" sino **lift**: cuánto se elige respecto de lo
que su presencia en la biblioteca justificaría. Lift 1.0 = suena lo que le toca.

**Artistas sobrerrepresentados** (piso: 4 en biblioteca, 3 apariciones)

| Lift | Quiénes |
|---|---|
| 7-10 | FAERO (10.1), Analog Sense (7.8), Ferry Corsten (7.0) |
| 4-6 | HANA (5.8), Soundexile (4.5) |
| 3-4 | Cendryma, Marcelo Vasami, Matter, Mazayr, Fur Coat, Lee Burridge (3.9), GMJ (3.6), Tom Pavicich (3.6), Marsh (3.6), Emi Galvan (3.3), Dmitry Molosh (3.2) |
| 2-3 | Lost Desert, PROFF, Rockka, Dowden, Hraach, **Ezequiel Arias (2.07)**, Nicolas Rada, Rauschhaus, **Hernán Cattaneo (2.00)** |

**Sellos:** Cydana Sounds 6.3, PURRFECTION 6.2, Balkan Connection 5.0, UV Noir
3.5, Hoomidaas 3.5, TRYBESof 3.1, Replug 3.0, Sudbeat 2.5, All Day I Dream 2.1,
Mango Alley 1.95 (y es el sello con más reproducciones absolutas: 45).

**Géneros:** Progressive House 1.43 · Organic House 1.25 · Melodic House &
Techno **0.89** · Techno **0.42** · Afro House **0.12**.

Tres cosas que conviene leer bien:

1. **Melodic House & Techno tiene lift por debajo de 1.** Hay 287 tracks en la
   biblioteca y se tocan menos de lo que corresponde. El centro real es
   progressive house, no melodic.
2. **Ezequiel Arias y Hernán Cattaneo están al fondo de la tabla**, con lift 2,
   la mitad que Cendryma o Vasami. Son referencia declarada en
   `docs/MI_SONIDO.md`, no lo más elegido en cabina.
3. **John Digweed: 4 tracks en biblioteca, 0 reproducciones.** Es la referencia
   de arquitectura de set, no material de pista. Cuando se usa "Digweed" como
   objetivo sonoro se está apuntando a algo que nunca se tocó — hay que decidirlo
   a conciencia, no por inercia.

---

## 2. El perfil de producción medido

### 2.1 Tempo — el dato es el techo, no la mediana

|  | tocados (n=348) | nunca tocados (n=1462) |
|---|---|---|
| p10 / p25 / mediana / p75 / p90 | 120 / 121 / **122** / 123 / 124 | 120 / 121 / 122 / 124 / 126 |
| debajo de 120 | 5% | 6% |
| **arriba de 125** | **1%** | **12%** |

La mediana es la misma en los dos grupos: 122 no es una preferencia, es el
centro del género. Lo que sí es una decisión es el techo — arriba de 125 BPM
prácticamente no se toca nada, y en la biblioteca hay 12% de material ahí.
Mann-Whitney sobre la distribución completa: p = 1.3e-9.

**Para escribir: 120-124. 125 es el borde. 126+ no.**

### 2.2 Duración — la diferencia más sólida de todo el documento

|  | tocados | nunca tocados |
|---|---|---|
| mediana | **7.5 min** (450 s) | 7.0 min (420 s) |
| p10 | 6.4 min | 5.2 min |
| p90 | 8.6 min | 8.4 min |

Mann-Whitney p = 4.1e-18 sobre los 1816. No es ruido: los tracks cortos se
compran y no se tocan. El piso está en ~6.5 min.

**Para escribir: 7 a 8 minutos y medio. Nada abajo de 6:30.**

### 2.3 Tonalidad — no hay preferencia, hay un sesgo de biblioteca

87% de lo tocado está en tonalidad menor (Camelot A). En la biblioteca entera es
85%. El orden de las claves más sonadas (6A, 7A, 8A, 4A, 5A, 9A) es exactamente
el orden de las claves más presentes en la biblioteca (6A 243, 7A 195, 8A 178,
4A 170, 5A 167). Lift ≈ 1 en todas.

**Conclusión honesta: la tonalidad no distingue nada.** Se toca menor porque el
progressive es menor. No hay evidencia de que 6A "funcione mejor" que 8A; hay
evidencia de que hay más tracks en 6A. Cualquier clave menor sirve para un
boceto; elegirla por mezcla con el resto del set, no por gusto.

### 2.4 Estructura (n=41 con segmentación confiable)

|  | p25 | mediana | p75 |
|---|---|---|---|
| compases totales | 224 | **240** | 251 |
| el breakdown arranca en el compás | 105 | **120** | 131 |
| largo del breakdown | 25 | **31** | 39 |
| largo del drop (kick de vuelta) | 62 | **73** | 89 |
| secciones detectadas | 4 | 5 | 7 |

Redondeando el largo del breakdown a múltiplos de 8, la moda es clarísima:

| 8 | 16 | 24 | **32** | 40 | 48 | 56 | 64 |
|---|---|---|---|---|---|---|---|
| 1 | 8 | 4 | **16** | 7 | 2 | 2 | 1 |

**32 compases de breakdown, arrancando en la mitad exacta del track
(compás 120 de 240).** Eso es una plantilla, no un promedio: 16 de 41 caen ahí y
otros 7 en 40.

La intro sin kick se detecta en sólo 13 de 41 tracks (mediana 15 compases). En
los otros 28 el bombo ya está desde el compás 1 — son ediciones para mezclar, no
para escuchar de cero.

### 2.5 Densidad de arreglo (n=9, 8 compases del pico de energía de cada tema)

| Métrica | mediana | mínimo | máximo |
|---|---|---|---|
| bombos por compás | **4.25** | 3.88 | 4.38 |
| enganche del bombo a la grilla (±20 ms) | **0.95** | 0.87 | 1.00 |
| agudos (hats/shakers) por compás | **9.75** | 8.25 | 14.62 |
| notas de bajo por compás | **3.5** | 2.88 | 6.12 |
| alturas de bajo distintas en 8 compases | **4.5** | 1 | 10 |
| cambios de acorde en 8 compases | **2** | 0 | 5 |

Cuatro por cuatro literal y clavado: el bombo engancha la grilla el 95% de las
veces, con un mínimo de 87%. Eso es "kick seco anclado" convertido en número.

### 2.6 Dónde cae el bajo — lo más específico que se midió

| Métrica | mediana | rango |
|---|---|---|
| fracción de notas de bajo en el pulso (1, 2, 3, 4) | **0.14** | 0.00 - 0.26 |
| fracción en el contratiempo (el "y" de cada tiempo) | **0.34** | 0.16 - 0.72 |
| resto (semicorcheas fuera de pulso y contratiempo) | **0.52** | 0.20 - 0.60 |

**El bajo esquiva el downbeat.** En 7 de los 8 temas con bajo hay más notas en
contratiempo que en pulso; el único al revés es Shades Of Blue de Vasami (0.26
pulso / 0.16 contra). El bajo no dobla el bombo: se cuelga entre medio. Eso es
la diferencia audible entre un progressive que rueda y uno que trota.

### 2.7 Percusión: base y adorno (n=9)

| Tema | repiques/compás | % de la percusión que es adorno |
|---|---|---|
| Cendryma — Typical Use | 0.0 | 0% |
| Cendryma — Mythica | 0.2 | 1% |
| Dowden — Pacifist | 1.2 | 6% |
| Maze 28 — Flux | 1.4 | 6% |
| Vasami — Shades Of Blue | 1.6 | 8% |
| Simon Vuarambón — Afrika | 2.0 | 9% |
| Cendryma — Repressure | 2.1 | 6% |
| Anderson vs Ivan Aliaga — Breakdown | 3.1 | 15% |
| Cendryma — Moonflare | 3.5 | 16% |

Mediana 1.6 repiques por compás, ~6% de los golpes. Casi toda la percusión es
patrón fijo. El adorno existe pero es minoría — y la dispersión (0 a 3.5) dice
que es decisión de tema, no regla del estilo.

### 2.8 Color de la capa melódica (n=21 stems `other` de Demucs)

Global de los 21: centroide **1261 Hz**, rolloff85 **2089 Hz**, planitud
**0.0014**, ataque 5.8. Reparto de energía: **0-500 Hz 34%, 500-2000 Hz 41%,
2-6 kHz 16%, 6 kHz+ 3.7%**.

Traducido: la melodía vive **abajo de 2 kHz**, es puramente armónica (planitud
tres órdenes de magnitud por debajo del ruido) y tiene ataque blando. Pads,
cuerdas filtradas, plucks apagados, leads con paso-bajo. Cualquier familia con
parciales inarmónicos en 3-6 kHz (vibráfono, campana, marimba, pluck brillante)
queda descartada por medición, no por opinión.

Rango completo de los 21: centroide 835 - 2580 Hz, planitud 0.0003 - 0.0274.

---

## 3. Los rangos: qué es regla y qué es gusto

Lo que todos los temas comparten se puede imponer. Lo disperso, no.

**Regla — coinciden todos, se puede escribir sin preguntar**

| Qué | Valor | Evidencia |
|---|---|---|
| Sub en mono | correlación L/R = 1.00 en los 48 (mínimo 0.99) | sin una sola excepción |
| Bombo cuatro por cuatro | 3.88 - 4.38 por compás en los 9 | rango cerradísimo |
| Bombo clavado a la grilla | enganche 0.87 - 1.00 | |
| Melodía debajo de 2 kHz | mediana 75% de su energía en 0-2 kHz | 20 de 21 por encima del 60% |
| Bajo fuera del pulso | contra > pulso en 7 de 8 | |
| Duración 6.5 - 8.5 min | p10 6.4, p90 8.6 | p = 4e-18 contra el resto |
| Techo de BPM en 125 | 1% arriba de 125 | 12% en la biblioteca |
| LUFS entre -10 y -8.5 | p25 -9.8, p75 -8.6 | |
| Bajo casi mono | ancho 0.94 - 0.98 | |

**Gusto — hay dispersión real, se pregunta o se decide caso por caso**

| Qué | Rango medido |
|---|---|
| Cambios de acorde en 8 compases | 0 a 5 (mediana 2) — hay temas de un acorde y temas que giran cada compás |
| Alturas de bajo distintas | 1 a 10 (mediana 4.5) |
| Repiques por compás | 0 a 3.5 |
| Agudos por compás | 8.25 a 14.6 |
| Brillo de la melodía (centroide) | 835 a 2580 Hz |
| Aire en la mezcla | 0.9% a 14.9% de la energía |
| Ancho del medio y del aire | 0.16 a 0.81 — desde casi mono hasta muy abierto |
| Rango dinámico | 1.8 a 9.8 dB (más un outlier de 24.3) |

Un boceto que respete la columna de la izquierda ya está adentro del estilo. La
de la derecha es donde se decide qué tema es, y ahí no hay número que ayude.

---

## 4. Qué distingue a los subgrupos

### Color melódico — acá sí hay diferencias reales

| Grupo | n | centroide | rolloff85 | planitud | ataque | 0-500 | 0.5-2k | 2-6k | 6k+ |
|---|---|---|---|---|---|---|---|---|---|
| Ezequiel Arias | 4 | **1059** | 1542 | **0.0006** | 6.6 | **54%** | 33% | 9% | 4% |
| Resto (Emi Galvan, GMJ, Dowden, Maze 28, Anderson, Vuarambón) | 6 | 1141 | 1943 | 0.0010 | 5.5 | 33% | 41% | 18% | 3% |
| Cendryma (solo y en colaboración) | 7 | 1307 | 2180 | 0.0018 | 5.3 | 34% | 43% | 16% | 3% |
| Marcelo Vasami | 1 | 1376 | 3063 | 0.0022 | 8.9 | 58% | 21% | 13% | 8% |
| Digweed / Nick Muir | 3 | **1996** | **3984** | **0.0130** | 8.2 | 22% | 43% | **25%** | **9%** |

**Digweed contra Eze Arias es la diferencia más grande medida en todo el
documento:** el centroide casi duplica (1996 vs 1059) y la planitud espectral es
**20 veces mayor** (0.0130 vs 0.0006). No es matiz. Eze Arias es una capa
melódica de tono puro con el peso abajo de 500 Hz; Digweed es material con
componente ruidosa y un cuarto de la energía en 2-6 kHz — texturas, percusión
tonal, sintetizadores sucios.

Con la salvedad de que el grupo Digweed es heterogéneo: Captain Mustache 2580,
Santiago 1996, y el remix de Waves de 8Kays 1261 — este último cae dentro del
rango del resto del corpus. La mediana del grupo la sostienen dos temas.

Cendryma queda exactamente en el medio (1307). Es también el artista que combina
volumen y preferencia: 35 reproducciones con lift 3.89, contra Emi Galvan que
suma 36 pero con lift 3.26 (tiene más tracks en la biblioteca). **El centro de
gravedad del gusto está en Cendryma, no en los extremos.**

Vasami con n=1 no permite conclusión de grupo. Lo que sí se puede decir de ese
tema en particular: Shades Of Blue es el track más sonado de todos (5 veces) y
tiene el aire más alto de los 48 medidos (14.9% contra una mediana de 4.4%). Es
un dato de un tema, no de un artista.

**Advertencia importante sobre este cuadro:** los 3 tracks de Digweed / Muir
tienen **0 reproducciones**. El grupo más brillante que se midió es justamente el
que nunca se tocó. Con n=3 y confundido con el artista, esto no prueba "el brillo
espanta"; sí prueba que "sonar como Digweed" y "sonar como lo que este DJ pone"
son dos objetivos que miden distinto, y que hay que elegir cuál se persigue.

### Mezcla por artista — acá NO hay diferencias

| Grupo | n | LUFS | DR | sub | bajo | medio | aire |
|---|---|---|---|---|---|---|---|
| Cendryma | 6 | -9.2 | 4.2 | 47.0 | 39.0 | 10.1 | 4.6 |
| Emi Galvan | 4 | -9.1 | 3.5 | 46.9 | 33.5 | 12.8 | 4.9 |
| Vasami (incl. remixes) | 3 | -9.9 | 3.8 | 53.7 | 31.1 | 6.9 | 3.7 |
| Mango Alley (sello) | 6 | -8.9 | 3.7 | 47.5 | 39.1 | 8.8 | 5.2 |
| Ezequiel Arias | 1 | -6.7 | 3.0 | 36.7 | 47.6 | 10.6 | 5.0 |

Todos adentro del ruido de la muestra general. **El balance espectral y el
loudness no distinguen a un productor de otro dentro de este estilo.** Lo que
distingue es el color del instrumento (cuadro anterior) y el arreglo. Si el
objetivo es "sonar como X", el ecualizador del master no es donde se decide.

---

## 5. Balance espectral, LUFS y ancho estéreo (n=48 más tocados)

| Métrica | p25 | mediana | p75 | mín | máx |
|---|---|---|---|---|---|
| LUFS integrado | -9.8 | **-9.1** | -8.6 | -11.7 | -6.7 |
| Rango dinámico | 3.0 | **4.6 dB** | 6.0 | 1.8 | 24.3 |
| Pico | +0.6 | **+0.8 dBFS** | +1.1 | 0.0 | +1.8 |
| sub (20-60 Hz) | 38.9 | **48.5%** | 53.2 | 18.8 | 70.4 |
| bajo (60-250 Hz) | 33.4 | **38.0%** | 44.2 | 21.4 | 68.9 |
| medio (250-2000 Hz) | 7.2 | **9.3%** | 12.3 | 3.7 | 20.2 |
| aire (2000+ Hz) | 3.4 | **4.4%** | 5.5 | 0.9 | 14.9 |
| ancho sub | 1.00 | **1.00** | 1.00 | 0.99 | 1.00 |
| ancho bajo | 0.94 | **0.96** | 0.98 | 0.82 | 1.00 |
| ancho medio | 0.34 | **0.47** | 0.61 | -0.05 | 0.81 |
| ancho aire | 0.34 | **0.45** | 0.62 | -0.49 | 0.91 |

Lecturas:

- **El sub es mono en los 48 sin excepción.** Correlación mínima 0.99. No hay
  un solo track en el corpus que se juegue eso. Es la regla más dura del
  documento.
- **El estéreo entra desde el medio para arriba**, y ahí sí hay libertad: 0.34 a
  0.62 en el cuartil central, con casos casi mono (-0.05) y muy abiertos (0.81).
- **86% de la energía está abajo de 250 Hz.** Es un estilo de peso grave, con la
  melodía sostenida por presencia y no por nivel.
- **-9 LUFS con 4.6 dB de rango**: comprimido, en línea con el master de club
  contemporáneo, sin llegar al aplastamiento del tech house.
- El pico mide +0.8 dBFS. Esto se midió sobre el MP3 decodificado, así que los
  picos arriba de 0 son sobrepasos intersample del codec, no prueba de que el
  master original clipee. No lo uses como objetivo.

**Cuidado con los porcentajes de banda:** son fracción de potencia espectral
total, y la potencia está dominada por el extremo grave por construcción. "48% en
el sub" no significa que se escuche mitad sub. Sirven para comparar mediciones
del mismo script entre sí, no como objetivo absoluto de ecualización.

---

## 6. El grupo de control: qué NO distingue lo que se toca

Se midieron 20 tracks **nunca tocados**, filtrados al mismo género, BPM y
duración, con el mismo script.

| Métrica | tocados (n=48) | control (n=20) | p (Mann-Whitney) |
|---|---|---|---|
| LUFS | -9.05 | -9.55 | 0.46 |
| Rango dinámico | 4.6 | 4.8 | 0.27 |
| sub % | 48.5 | 43.6 | 0.17 |
| medio % | 9.3 | 11.1 | 0.17 |
| ancho sub | 1.00 | 1.00 | — |
| **duración** | **7.85 min** | 7.37 min | **0.046** |
| **compases** | **240** | 224 | **0.035** |
| **breakdown (compases)** | **31** | 24 | **0.033** |

Esta es la conclusión menos cómoda y la más útil del documento:

**La mezcla no explica nada.** LUFS, rango dinámico, balance espectral y ancho
estéreo son iguales en lo que se toca y en lo que nunca se tocó. Toda la
biblioteca está masterizada parecido, porque todo viene del mismo circuito de
sellos. Un track no se gana la cabina por la mezcla.

**Lo que sí separa es el tiempo: el track dura más y el breakdown dura más.**
240 compases contra 224, breakdown de 32 contra 24. Con n=20 y siete
comparaciones, esas p≈0.04 no sobrevivirían una corrección de Bonferroni por sí
solas — pero la duración se corrobora en la biblioteca entera (1816 tracks,
p=4e-18), así que el efecto es real aunque el test del control sea débil.

**Para el productor: perseguir el master es perseguir lo que ya viene gratis.
Lo que hay que perseguir es un track de 7-8 minutos con un breakdown de 32
compases en la mitad.**

---

## 7. Receta corta

Si hay que escribir un boceto ahora mismo sin preguntar nada:

```
BPM              121-123, techo duro en 125
Tonalidad        menor, cualquiera (no discrimina)
Duración         7:30 aprox = 240 compases
Forma            groove hasta el compás 120 · breakdown 32 compases ·
                 drop de ~73 compases · salida
Bombo            4 por compás, clavado a la grilla (>90% de enganche)
Agudos           ~10 eventos por compás
Bajo             3-4 notas por compás, 4-5 alturas distintas,
                 con el peso en el contratiempo (14% en pulso / 34% en contra)
Armonía          2 cambios de acorde cada 8 compases
Percusión extra  ~1.6 repiques por compás, 6% del total de golpes
Melodía          centroide ~1250 Hz, planitud <0.003, ataque blando,
                 75% de su energía abajo de 2 kHz
Master           -9 LUFS, 4-5 dB de rango, sub estrictamente mono,
                 estéreo desde 250 Hz para arriba
```

Y lo que no está en la lista: **el sonido**. Nada de esto dice qué sintetizador,
qué sample de bombo ni qué textura. La medición descarta familias enteras y
acota rangos; adentro de eso la elección es de una persona. Un boceto que cumpla
los diez renglones puede ser perfectamente insoportable.

---

## 8. Límites explícitos

**Qué NO prueba esta medición**

1. **La muestra es lo que este DJ elige tocar, no lo que funciona.** 510
   reproducciones de una biblioteca que él mismo compró. Si nunca compró un
   género, ese género aparece con lift bajo y no significa que no funcione en
   pista. Sólo un setlist real de otro DJ puede refutar algo de acá.
2. **El historial mezcla contextos.** No distingue una prueba en casa de un set
   en un club. `DJPlayCount` cuenta las dos.
3. **Correlación, no causa.** Que los tracks más tocados duren más no prueba que
   alargar un track lo haga más tocable.
4. **n chico donde importa.** El arreglo son 9 temas, los repiques 9, el color
   21, la mezcla 48. Los subgrupos por artista van de 1 a 7. Vasami con n=1 no es
   un artista medido, es un tema medido.

**Métricas con sesgo del detector — descartadas o marcadas**

1. **`clap_x_compas` está rota y no se usa.** Da 5 a 14.6 claps por compás cuando
   en house son 2. La banda de 200-1400 Hz del stem de batería agarra cuerpo de
   bombo, toms y percusión: mide "energía en el medio", no claps. Ya estaba
   declarada rota en `data/arreglos_medidos.json` y esta medición lo confirma.
2. **La densidad de onsets de `reverse_engineer` satura.** Sobre 129 secciones
   con kick da mediana 15.4 y máximo 16.1 onsets por compás: es el techo del
   detector, no del track. **No sirve para comparar tracks entre sí.** Sí sirve
   para comparar secciones dentro de un track (groove 15.4 vs breakdown 11.8).
3. **La segmentación falla en 7 de 48.** El script lo avisa solo (`confiable:
   false`) cuando no hay contraste en la banda grave: Pacifist, G-Force, Sin
   Control, Step by Step, No Warm, Tremolo Man, Anomaly. Los números de
   estructura de este documento excluyen esos 7.
4. **El detector de arreglo descarta mucho más de lo que mide.** De 8 temas
   adicionales con stems ya separados, sólo 2 pasaron los filtros de calidad
   (enganche del bombo ≥0.70 y 3.5-4.5 bombos por compás). Los otros 6 dieron
   cosas como 7.25 bombos por compás o 39% de enganche — el detector, no el tema.
   Por eso la muestra de arreglo es 9 y no 15: **está sesgada hacia los temas con
   bombo fácil de detectar**, o sea los más secos y directos. Un tema con bombo
   con cola o con swing queda afuera por construcción.
5. **Los porcentajes de banda son fracciones de potencia** dominadas por el
   grave. Comparables entre sí, no como objetivo de ecualización.
6. **El pico se midió sobre MP3 decodificado.** Los +0.8 dBFS son intersample del
   codec, no evidencia de clipping en el master.
7. **El color melódico se mide sobre el stem `other` de Demucs**, que además de
   pad y lead puede arrastrar percusión tonal y residuo de vocal. En material con
   voz procesada el centroide sube por una razón que no es el sintetizador.

**Un bug encontrado en un script existente (no lo toqué)**

`scripts/medir_arreglos.py::_buscar()` — y el mismo patrón en el `--patron` de
`scripts/color_melodico.py` — resuelve el archivo por subcadena y se queda con la
**primera** coincidencia. Eso hace que resuelva a la versión equivocada cuando
hay varias:

- "Cardamom (Original Mix)" → resolvió al archivo del **FAERO Remix**
- "Deflator (Original Mix)" → resolvió al **Montw Remix**
- "The Landing (Original Mix)" → resolvió al **Club Mix**

Para derivar un estilo general el daño es chico (siguen siendo temas del corpus),
pero **cualquier número atribuido a una versión puntual puede estar mal**. En
esta medición produjo además una fila duplicada: "Cardamom (Original Mix)" y
"Cardamom (FAERO Remix)" salieron con números idénticos porque son el mismo
archivo. Se dedupló antes de calcular (48 únicos de 49 filas). Arreglarlo pide
comparar también el paréntesis del título, no sólo el núcleo.

---

## 9. Qué falta medir

- **Sidechain**: cuánta compresión mete el bombo sobre pad y bajo, y con qué
  tiempo de recuperación. Es probablemente el parámetro más audible del estilo y
  no está medido.
- **Automatización de filtro** en el breakdown: cómo entra el track de vuelta.
- **Reverb y cola**: el largo de cola es parte del "aire" y no se separa del
  balance espectral.
- **Un corpus de control más grande**: 20 es poco para cerrar la conclusión del
  punto 6. Con 100 el resultado dejaría de depender del azar de la muestra.
- **Nada de esto está cruzado con la taxonomía de registros** de
  `docs/MI_SONIDO.md` (oscuro/hipnótico, heroico, peak firme…). Medir qué separa
  un heroico de un peak firme sigue siendo la pregunta abierta más útil.
