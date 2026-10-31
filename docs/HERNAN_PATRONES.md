# Hernán Cattaneo: cómo arma un set, medido

Material de base para el agente `hernan`, una lente como `.claude/agents/digweed.md`.
Pedido del DJ: "fijate sets reales, analiza y busca patrones, entonces va a salir".
Lo cargó el agente research el 2026-10-31.

Cada patrón lleva **cuántos sets y cuántos temas lo sostienen**. Lo **medido** sale
de los JSON de `data/setlists/`. Lo **interpretado** es una lectura mía y está
marcado como tal.

---

## 1. El corpus

### Sets en orden (`data/setlists/`)

| Tag | Set | Fecha | Dura | Posiciones | Con nombre | Huecos ID | Key/BPM | Fuente |
|---|---|---|---|---|---|---|---|---|
| R807 | Resident 807 | 2026-10-24 | 60 min | 10 | 10 | 0 | 50% / 40% | feed oficial |
| R806 | Resident 806 | 2026-10-17 | 60 min | 10 | 10 | 0 | 40% / 40% | feed oficial |
| R805 | Resident 805 | 2026-10-10 | 64 min | 10 | 10 | 0 | 70% / 70% | feed oficial |
| R769 | Resident 769 (ya estaba) | 2026-01-31 | 61 min | 10 | 10 | 0 | 70% / 70% | YouTube |
| SUN26 | Sunsetstrip Buenos Aires, día 2 | 2026-04-12 | 7 h 31 | 82 | 58 | 24 | 64% / 60% | descripción de YouTube (a mano) |
| WOOD24 | Woodstock 69, Bloemendaal | 2024 (julio, inferido) | 6 h | 65 | 50 | 15 | 82% / 80% | descripción de YouTube (a mano) |
| DEN24 | All Night Long, Denver | 2024-11-30 | 5 h | 55 | 43 | 12 | 91% / 91% | trackid.net |
| BAL25 | Balance Croatia 2025 (festival) | 2025 | 3 h | 33 | 26 | 7 | 96% / 96% | trackid.net |
| IMB24 | **b2b** Edu Imbernón, Fayer Valencia | 2024-07 | 6 h | 67 | 51 | 16 | 86% / 84% | trackid.net |
| NW25 | **b2b** Nick Warren, Loveland (ya estaba) | 2025-08-10 | 3 h 33 | 38 | 14 | 24 | 86% (de 14) | trackid + set79 |
| BARI20 | Sunsetstream Bariloche (ya estaba) | 2020-12-14 | 3 h 27 | 39 | 36 | 3 | 11% | YouTube |

- **Lo nuevo:** 8 sets y 245 posiciones. Hay 3 Resident, 4 sets largos de club o
  festival y 1 b2b. BARI20 es de 2020 y queda fuera del rango 2024-2026: lo uso
  solo para aperturas y cierres.
- **Key y BPM** salen de la biblioteca y, si el tema no está, de Muzpa
  (`enrich_setlist.py`). La **energía** existe solo para los temas que están en la
  biblioteca. Hay 67 puntos en los sets largos y no se inventó ninguno.
- **Huecos:** donde entre dos temas detectados pasan más de 9.5 min, se agrega un
  `ID - ID` por cada 5.5 min que sobran. Así no se miden transiciones que no
  existieron. El criterio está escrito en el campo `fuente_tracklist` de cada JSON.
- **El año de WOOD24 está inferido.** El video es de noviembre de 2024 y los
  temas son de 2024. El día exacto no está confirmado.

### Corpus de paleta: el feed del Resident (sin orden de transiciones medible)

El podcast oficial `https://podcast.hernancattaneo.com/feed.xml` publica el
tracklist de cada episodio. Tomé los **episodios 676 a 807 (abril 2024 a octubre
2026): 120 episodios y 1174 temas**. Sirve para medir paleta, repeticiones y
densidad. No lo cargué a `data/setlists/` porque son 120 archivos y casi ninguno
tiene key: la mayoría son promos que Muzpa todavía no tiene. 95 de esos temas
están en la biblioteca y tienen energía.

**Corrección al pedido:** el Resident **no dura 2 h**. Desde 2011 el podcast dura
alrededor de 1 h, y en 2024-2026 la mediana es **61.8 min con 10 temas** (120
episodios). En Urbana Play sale los domingos de 00 a 01.

---

## 2. Patrones medidos

### 2.1 BPM: arranca en 120 y sube 2 a 4 BPM en toda la noche

**Medido** (mediana de BPM por tercio del set; entre paréntesis, los temas con dato):

| Set | Arranque (1.os 3) | Tercio 1 | Tercio 2 | Tercio 3 | Final (últ. 3) | Rango |
|---|---|---|---|---|---|---|
| SUN26 (7.5 h) | 120 | 121 (12) | 123 (9) | 124 (14) | 125 | 118-131 |
| WOOD24 (6 h) | 120 | 122 (17) | 122 (11) | 122 (12) | 121 | 116-127 |
| DEN24 (5 h) | 120 | 122 (14) | 123 (13) | 124 (12) | 124 | 109-125 |
| BAL25 (festival 3 h) | 123 | 122 (9) | 123 (9) | 125 (7) | 126 | 121-129 |
| IMB24 (b2b 6 h) | 122 | 123 (16) | 124 (17) | 126 (10) | 128 | 120-132 |
| Resident, 95 temas de 120 episodios | — | 121 (pos 1-3, n=26) | 123 (pos 4-7, n=40) | 122 (pos 8-10, n=29) | — | 119-128 |

- **Los 3 sets largos solos de club (5 a 7.5 h) arrancan en 120.** El festival de
  3 h arranca en 123. Él dice lo mismo (ver §4): "los festivales necesitan
  energía más directa".
- **La subida es lenta:** de +0 a +4 BPM entre el primer tercio y el último (5 sets).
  WOOD24 queda plano en 122 las 6 horas.
- **Entre temas seguidos casi no se mueve:** en 125 pases con BPM en los dos lados,
  la mediana del salto es **1 BPM**, el 57% cambia 1 BPM o menos y el **11% salta
  más de 3**.
- **El Resident no sube:** es una meseta de 121 a 123 en la hora.

### 2.2 Key: o se queda en la misma, o salta lejos. Casi no camina la rueda de a 1

**Medido** sobre 133 pases consecutivos con key en los dos lados (2024-2026, sin BARI20):

| Movimiento | Pases | % |
|---|---|---|
| Misma key | 40 | **30%** |
| ±1 en la rueda | 17 | 13% |
| Relativa (8A↔8B) | 7 | 5% |
| A 2 pasos | 15 | 11% |
| **A 3 pasos o más** | 54 | **41%** |

- **Ojo con la fuente de la key.** Si los dos temas del pase tienen key de la
  biblioteca (Rekordbox), en 18 pases el 56% se queda en la misma key y el 17%
  salta 3 o más. Si las dos keys vienen de Muzpa, en 63 pases da 29% y 46%. La
  key de Muzpa difiere de la de Rekordbox en algunos temas (ver memoria "La key de
  Rekordbox manda"), así que es probable que el 41% de saltos largos esté inflado.
  Lo que **se sostiene con las dos fuentes** es que ir de a 1 en la rueda es
  minoría (13 a 17%) y que quedarse en la misma key es lo más común entre los
  movimientos cortos.
- **No recorre la rueda en un sentido:** de los 17 pasos de ±1, 5 suben y 12
  bajan. Con n=17 no alcanza para hablar de dirección.
- **Rachas en la misma key:** la más larga es de 6 temas (DEN24). En los demás
  sets va de 2 a 4.
- **Modo:** el **84% de sus temas es menor (zona A)**: 185 de 221 con key.
- **Interpretado:** el criterio no es armónico. Mezcla por groove y BPM (el BPM
  casi no se mueve) y deja que la key salte. La regla
  `armonia.max_camelot_dist = 2` del proyecto prohibiría alrededor de 4 de cada
  10 de sus pases, o 2 de cada 10 contando solo la key de la biblioteca.

### 2.3 Densidad: 10 a 11 temas por hora, de unos 5 min cada uno

**Medido:**
- **Resident:** mediana de 10 temas en 61.8 min, o sea **9.7 por hora**, unos
  6.2 min por tema (120 episodios).
- **Sets largos:** el intervalo entre el inicio de un tema y el del siguiente, solo
  entre temas identificados y seguidos, tiene una mediana de **4.7 a 5.4 min**
  según el set. Son 172 intervalos en 5 sets: SUN26 5.3, WOOD24 5.4, DEN24 5.1,
  BAL25 4.7, IMB24 5.1. Con los huecos incluidos, los 5 dan entre 10.9 y 11.2
  posiciones por hora.
- **Para el analista, interpretado:** `densidad.tracks_por_hora = 8.8` queda por
  debajo de lo que hace él (9.7 en radio y unos 11 en club). No toca temas largos:
  en club los mezcla a los 5 minutos.

### 2.4 Paleta: cola larga, ningún sello domina y lo propio es poco

**Medido:**
- **Sellos:** en los sets largos, 133 de 282 temas tienen sello conocido y hay **74
  sellos distintos**. El que más aparece tiene 5 temas: Mango Alley y Anjunadeep
  con 5, y después Meanwhile, Univack, Bedrock, Plastic Fantastic y Sudbeat con 4
  cada uno. **Sudbeat, su sello, es el 3% de los temas con sello.**
- **Manos más repetidas en el Resident** (artista o remixer; 1174 temas): Gai Barone
  33, Gorkiz 22, Hernán Cattaneo 20, André Moret 19, Hobin Rude 18, Tiefstone 15,
  Gowzer 13, Kamilo Sanclemente 13, Will DeKeizer 12, Tato Seco 11, Nicolás Viana
  11, Juan Deminicis 11 y Kasey Taylor 11. Los 13 primeros suman alrededor del 20%
  de los temas, y el resto se reparte.
- **Lo propio:** en el Resident hay 20 de 1174 temas (**1.7%**) con su mano, 10
  como artista y 10 como remixer. En los sets largos hay **15 de 242 (6.2%)**, y
  casi todos son **remixes a cuatro manos**: Simply City 5, Mercurio 4 (3 remixes
  y el original "2009"), Jamie Stevens 2, Marcelo Vasami 2. **Dónde los pone:** 13 de los 15 caen entre el 15% y
  el 60% del set. Solo uno cierra (DEN24, "Feeling", HC & Mercurio Remix) y otro
  va al 90% (SUN26, "Terra Firma").
- **Artista repetido en un set:** con remixes contados, un mismo nombre aparece
  hasta 5 veces en un set largo: Gai Barone 5 en SUN26, Antrim 4 en WOOD24, Cass 4
  en BAL25. En 120 Resident, 16 episodios tienen dos temas seguidos del mismo
  artista, y **7 abren con dos temas seguidos del mismo artista**: Gastón Pérez en
  el 769, Dreamteller en el 806.
- **Argentinos: no lo pude medir con confianza.** MusicBrainz tiene el país de 40
  de los 100 artistas más tocados, con errores de homónimos. Están verificados como
  argentinos Hernán Cattaneo, Juan Deminicis, Paul Deep, Alan Cerra, Luca Abayan,
  Fran Garay, Baunder, Abity y Claudio Cornejo (AR). **Interpretado, sin
  verificar:** del top 30 también serían de la escena argentina Tato Seco, Nicolás
  Viana, Kevin Di Serna, Nicolás Rada y Agustín Pietrocola. Él lo dice así: los
  productores jóvenes "me ayudan a construir mi set" (§4).

### 2.5 No repite: cada set es repertorio nuevo

**Medido:**
- **Entre los 5 sets largos de 2024-2026** (242 temas con nombre) no hay **ningún
  tema repetido**.
- **En el Resident** hay 1157 temas distintos en 120 episodios: **17 aparecen dos
  veces y ninguno tres**.
- **Club contra radio:** un set de club comparte con el Resident de su época entre
  el 0 y el 38% de sus temas. BAL25 comparte 38%, SUN26 22%, DEN24 16%, IMB24 12%
  y WOOD24 0%.
- **Interpretado:** el Resident funciona como vidriera de lo que le llega. Él dice
  "I can support and push some of the tons of tracks I got sent by new
  producers" (§4). El club toma parte de eso, pero no es la playlist de la radio.

### 2.6 Aperturas y cierres: abre profundo en 120, cierra con un clásico o una canción

**Medido** (los primeros 3 y los últimos 4 temas con nombre de cada set largo):

| Set | Cómo abre | Cómo cierra |
|---|---|---|
| SUN26 | Chaim "Sun Tease" (Paul Deep Edit), M.A.N.D.Y "Superstitious" (Chaim Bells Remix), 120-122 | Sumo "Mejor No Hablar de Ciertas Cosas" (Santi Lecot Edit), Ezequiel Arias "Eterno", Jam & Spoon "Stella" (Kölsch Remix), Rogue Audio & Ruby Rose (Cass Is Broken Remix) |
| WOOD24 | DAVIDEE "Full Moksha", Pole Folder "Elo" (Solstice Mix), Anima "Saturn", 120-122 | Edu Imbernón "In Your Head", RY X & Ólafur Arnalds "Colorblind" (WhoMadeWho Remix, 116 BPM), Because of Art "Circle of Light" |
| DEN24 | Liam Sieker (Mike Rish Remix), Gai Barone "Hemels", 120-122 | Antrim "Eternal Journey", Röyksopp "Sordid Affair" (Maceo Plex Remix), Deer Jade, su remix de "Feeling" |
| BAL25 | Ash Mellor (Steve Fokas Remix), Kamilo Sanclemente "Goldes Eyes", 123-126 | Zuccasam, Digweed/Romboy/Muir "Sigani Meomchun", DCLVIII "Revolution", Cass & Slide "Perception" |
| IMB24 (b2b) | Sébastien Léger "Omira", Because of Art "Real High" | Gregor Tresher, DCLVIII, Joy Kitikonti "Dirtysummer 2K6", Rui Da Silva "Touch Me" |
| NW25 (b2b) | Nick Warren "Loveland" (energía 2.2) | Robin Tordjman, Nicolás Viana "Coral", Das Koolies, London Grammar "Hey Now" |
| BARI20 | Marsh "Florence", Draso | AIR "Cherry Blossom Girl" (bootleg), Bonobo "6000ft", Mazzy Star "Into Dust" (edit) |

- **Lo que se repite:** en **7 de 7 sets largos** hay entre los últimos 4 al menos
  un clásico anterior a 2010 o una canción conocida con edit o remix: Sumo, Jam &
  Spoon, Rui Da Silva, Joy Kitikonti, Cass & Slide, Röyksopp, RY X, London
  Grammar, Mazzy Star, AIR. En el medio del set también aparecen: Air "All I Need",
  Bonobo "Closer", Jakatta "American Dream", Depeche Mode, Pet Shop Boys, Joe
  Smooth "Promised Land".
- **Interpretado:** abre con un groove profundo y orgánico, sin melodía grande.
  Cierra con algo que la pista reconoce, y el cierre puede bajar de BPM (RY X a
  116) o de energía.

### 2.7 Energía: meseta con una joroba en el medio, y el último quinto baja

**Medido** (solo los temas que están en la biblioteca; se excluye el bug de E:1.4):

| Tramo del set (6 sets largos) | Temas con energía | Mediana | p25-p75 | Máx |
|---|---|---|---|---|
| Quinto 1 | 15 | 5.7 | 4.5-7.0 | 7.9 |
| Quinto 2 | 19 | 5.4 | 5.1-6.1 | 6.8 |
| Quinto 3 | 16 | **6.4** | 4.9-6.9 | 7.5 |
| Quinto 4 | 9 | 6.2 | 5.2-6.6 | 7.5 |
| Quinto 5 | 8 | **5.4** | 4.9-6.1 | 6.2 |

- **Dónde cae el pico:** en SUN26 (21 puntos de 82) el máximo es 7.9 al **21%**
  (GMJ & Matter "Cryo") y el segundo es 7.5 al **56%** (Gorkiz "Big Bottom").
  Termina en 2.5. En DEN24 (14 de 55) el máximo es 7.5 al **45%**.
- **Bajadas:** en SUN26 hay un valle de 2.2 al 48% (Ezequiel Arias "Estímulo")
  entre dos tramos de 6.6 a 7.5. Es una bajada en el medio de la noche, no al
  final.
- **Resident:** 5.6, 5.7 y 5.7 por tercio (95 temas). **Es plano.**
- **Interpretado, con poca muestra (67 puntos):** la forma no es una rampa
  hasta el final como la de Digweed (pico al 90%). Es una meseta larga que
  respira: sube en el medio y suelta al cierre. Él lo dice así: "no se puede tocar
  a la misma intensidad 14 o 24 horas; hace falta paciencia y dinámica". **Esto
  choca con la decisión del DJ ("quiero que no baje"), y la decisión del DJ manda.**
  El agente `hernan` tiene que decirlo como contraste, no como corrección.

---

## 3. Los patrones más fuertes, en una tabla

| # | Patrón | Sets | Temas o pases que lo sostienen |
|---|---|---|---|
| 1 | Los sets largos de club arrancan en 120 BPM y suben de 2 a 4 BPM en toda la noche; el festival arranca en 123 | 5 largos (+ Resident) | 125 pases con BPM; 185 temas con BPM en los 5 largos |
| 2 | Entre temas seguidos el BPM casi no se mueve: mediana 1, 57% ≤1, 11% >3 | 10 | 125 pases |
| 3 | Va de a 1 en la rueda solo en el 13-18% de los pases. Se queda en la misma key (30%) o salta (41% a 3 o más; menos con la key de Rekordbox) | 10 | 133 pases |
| 4 | El 84% de los temas está en clave menor (zona A) | 10 | 221 temas con key |
| 5 | Densidad de 10-11 temas por hora (9.7 en radio, intervalo de 5 min en club) | 120 Resident + 5 largos | 1174 temas; 172 intervalos |
| 6 | No repite: 0 temas repetidos entre los sets largos; en la radio 17 de 1157 se repiten dos veces y ninguno tres | 5 largos + 120 Resident | 242 + 1157 temas |
| 7 | Cola larga sin sello dominante: 74 sellos en 133 temas, Sudbeat 3%; lo propio es 1.7% en la radio y 6.2% en club, casi todo remixes con socios, puestos en el medio | 6 largos + 120 Resident | 133 temas con sello; 1174 + 242 temas |
| 8 | Cierra con un clásico o una canción conocida | 7 largos | 7 de 7 cierres |
| 9 | Energía: meseta que respira, pico en el medio y bajada en el último quinto | 6 largos | 67 temas con energía (muestra chica) |

---

## 4. Lo que él dice

| Cita | Fuente |
|---|---|
| "I really love long sets because they allow you to tell a much deeper story." / "you can really build emotions slowly and take people on a journey." | INSITE (Croacia), 20 de mayo de 2026: <https://insite-croatia.com/?p=20410> |
| "You cannot play at the same intensity for 14 or 24 hours." / "You need patience and dynamics." | ídem |
| "In clubs I usually go deeper and more subtle, especially if I have more hours." / "Festivals sometimes need more direct energy because the set is shorter" | ídem. **Lo confirma el dato:** BAL25 arranca en 123 y los clubs en 120 |
| "Today the difficult part is filtering because there is too much music." / "What I always look for is emotion and personality." | ídem |
| "My mind-set and the sounds I like to play work much better in a set 5 hours or longer" / "It's always a hard time when a festival give you 90 min to two hours." | Dancing Astronaut, marzo de 2017: <https://dancingastronaut.com/2017/03/techno-tuesday-hernan-cattaneo-history-argentinian-dance-scene-benefits-extended-mix/> |
| Sobre los productores jóvenes: "ellos me ayudan a construir mi set y yo a ellos a mostrarlos." | Los Andes, marzo de 2018: <https://www.losandes.com.ar/hernan-cattaneo-de-la-rave-al-colon> |
| Sobre el Resident: "I can support and push some of the tons of tracks I got sent by new producers all the time." Sobre el b2b con Guy J: "We never ever talk about music before the show, never." | Progresivna Suza, agosto de 2021: <https://www.progresivnasuza.com/2021/08/05/hernan-cattaneo-i-dont-think-i-will-ever-stop-playing/> |

No encontré ninguna entrevista donde explique el warm-up propio paso a paso. Lo
que hay es la idea de construir despacio, la paciencia y la dinámica.

---

## 5. Para el agente `hernan`: qué mirar en un set propio

Esto es interpretación, con el número que la sostiene al lado.

1. **¿El BPM se mueve de a poco?** Que un salto de más de 3 BPM entre dos temas
   seguidos aparezca en 1 de cada 10 pases como mucho (él: 11%). Arranque en 120 si
   el set es largo.
2. **¿La key manda más que el groove?** Él va de a 1 en la rueda solo en el 13-18%
   de los pases. Un set que encadena +1 tras +1 está ordenado por la rueda, no por
   el groove. No es un error, pero no es como lo arma él.
3. **¿Hay meseta?** El Resident es plano (5.6-5.7) y los sets largos respiran en el
   medio. No reclamarle una rampa a un set de 1 hora.
4. **¿Hay algo que la pista reconozca al final?** Un clásico o una canción con edit
   aparece en 7 de 7 cierres.
5. **¿La paleta es variada?** Con 74 sellos en 133 temas, cinco temas del mismo
   sello es mucho. Repetir artista no es problema: él llega a 5 por set y abre el
   Resident con dos temas seguidos del mismo artista.
6. **¿Es material nuevo?** No repite temas entre noches. Para él, un set es
   material nuevo más algunos de la radio del momento (0 a 38%).
7. **Lo que no se dice sin dato:** la energía tiene 67 puntos en 6 sets, así que la
   forma del arco es una pista y no una regla. Y la decisión del DJ ("el set no
   baja") pisa al cierre que baja de Hernán.

---

## 6. Cómo se armó y cómo seguir

- **Fuentes:** el feed del Resident (`podcast.hernancattaneo.com/feed.xml`, 812
  episodios con tracklist desde el 409). La API de trackid
  (`/api/public/audiostreams/<slug>`) **sí trae los temas**, en
  `detectionProcesses[].detectionProcessMusicTracks`. Y las descripciones de
  YouTube con `buscar_setlists.py`. 1001tracklists sigue cerrado.
- **Candidatos que quedaron afuera y se pueden sumar:** Het Sieraad Amsterdam
  2024-04-05 (2 h, trackid 94% de detección); Brunch Electronik Barcelona 2024
  (tracklist en la descripción de YouTube `aTUUaRHsvbY`); la versión HQ Remastered
  del b2b de Loveland 2025 en trackid (23 temas contra los 14 del archivo actual);
  Sasha b2b Hernán, Denver 2023.
- **Para mejorar la key:** volver a medir los temas de Muzpa con la key de
  Rekordbox cuando estén en la biblioteca. El 41% de saltos largos depende de esa
  fuente.
