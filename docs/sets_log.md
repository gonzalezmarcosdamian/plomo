# Sets Log

Documento vivo — sets armados por fecha, mantenido en orden numerico.
**Regla:** Ningun set queda sin la cantidad de tracks que le corresponde
(sean los originales del DJ o elegidos por nosotros con la misma vibe).

---

## Formato de entrada

Cada set registra:
- Fecha de armado
- Duracion objetivo y real
- Tracks en orden de playlist (con origen: libreria / descargado / reemplazo)
- BPM range y arco de energia

---

## Sets 01–13 — Propios (algoritmo movimientos + anclas)

Reconstruidos en sesion 2026-05-21 con `rebuild_all_sets.py`.
Ver commits de esa fecha para detalle de tracks.

| Set | Nombre | Duracion | Tracks | Armado |
|-----|--------|----------|--------|--------|
| 01 | Cattaneo Style — Camelot puro | 2h | ~18 | 2026-05-21 |
| 02 | Progressive Deep — Vuarambon Style | 2h | ~18 | 2026-05-21 |
| 03 | Progressive Peak — Warren Style | 1.75h | ~16 | 2026-05-21 |
| 04 | Progressive Melodic — Eze Arias Style | 1.5h | ~14 | 2026-05-21 |
| 05 | Romantico | 1h | ~10 | 2026-05-21 |
| 06 | Cena & Progressive | 3h | ~27 | 2026-05-21 |
| 07 | Progressive 2h | 2h | ~18 | 2026-05-21 |
| 08 | Progressive 2h v2 | 2h | ~18 | 2026-05-21 |
| 09 | Progressive Dark — Sonido Plomo | 3h | ~27 | 2026-05-21 |
| 10 | — | — | — | — |
| 11 | — | — | — | — |
| 12 | Progressive — Nuevo Material | 3h | ~27 | 2026-05-21 |
| 13 | — | — | — | — |

---

## Sets 14–20 — Referencia (estilos DJ pro, con completado de libreria)

Sets originalmente armados como referencia de DJ sets profesionales.
Estaban cortos (~8-10 tracks). Se completan con `plan_set.py` + `build_set.py`.

| Set | Nombre | Target | Estado | Armado |
|-----|--------|--------|--------|--------|
| 14 | — | — | pendiente | — |
| 15 | — | — | pendiente | — |
| 16 | Eze Arias Style | 18 tracks / 2h | pendiente import | — |
| 17 | Progressive Melodic Alt | 18 tracks / 2h | pendiente import | — |
| 18 | Digweed Style | 28 tracks / 3h | pendiente import | — |
| 19 | Vuarambon Style | 20 tracks / 2h | pendiente import | — |
| 20 | Emi Galvan Style | 18 tracks / 2h | pendiente import | — |

---

## Set 21 — Gina Set

**Armado:** 2026-05-21  
**Duracion:** 2h  
**Script:** `rebuild_all_sets.py`  
**Tracks:** ~18 (7 huerfanos + complementarios de libreria)  
**BPM range:** 120-125  
**Estilo:** Progressive peak — Maze 28, Sasha, Nicolas Rada, Kamilo

---

## Set 22 — Melodic Deep

**Armado:** 2026-05-21  
**Duracion:** 1h  
**Uso:** Llegada en cumple (16:00)

---

## Sets 23–26 — DJ Profesionales (completados con libreria)

Completados en sesion 2026-05-23 con `scripts/archive/complete_pro_sets.py`.
Tracks originales del DJ preservados donde existian, completados con libreria
por BPM/genero/energia compatible.

### Set 23 — Cattaneo Sunsetstrip Dia 2 BA 2026
**Armado:** 2026-05-23  
**Duracion:** 2h30  
**Tracks:** 25 (19 originales + 6 libreria intercalados por energia)  
**BPM range:** 120-127  
**Estrategia:** Orden original Cattaneo preservado, 6 tracks nuevos insertados por energia  
**Tracks agregados:** NOIYSE PROJECT Remember Me (E:7.3), Maze 28 Leave the World Behind (E:7.0),
Einmusik Centaurio (E:7.3), D-Nox Shine (E:7.4), Sasha Phaxon (E:7.0), Nicolas Rada Glasgow (E:4.4)

### Set 24 — Vuarambon Stereo Montreal 2024-09-21
**Armado:** 2026-05-23  
**Duracion:** 2h  
**Tracks:** 22 (10 originales + 12 libreria)  
**BPM range:** 118-124  
**Estrategia:** Ordenados por energia — arco E:1.4→6.7  

### Set 25 — Vuarambon Palacio Alsina BA 01.08.2025
**Armado:** 2026-05-23  
**Duracion:** 1h30  
**Tracks:** 17 (7 originales + 10 libreria)  
**BPM range:** 118-124  
**Estrategia:** Ordenados por energia — arco E:2.7→7.1  

### Set 26 — Digweed Forja Cordoba 18.04.2026
**Armado:** 2026-05-23  
**Duracion:** 4h  
**Tracks:** 34 (4 originales + 30 libreria)  
**BPM range:** 118-127  
**Estrategia:** Ordenados por energia — arco E:1.0→7.3  

---

## Proximos pasos

1. Cerrar Rekordbox
2. `python scripts/import_all.py` — mueve tracks descargados
3. Abrir Rekordbox → import folder `Nuevos/2026-05`
4. Cerrar Rekordbox
5. `python scripts/post_import.py` — cues + energy + playlists
6. Para cada set 16-20:
   - `python scripts/plan_set.py XX` — verifica y planifica
   - `python scripts/build_set.py XX` — construye en DB
7. Sync al pen

## Set 16. 16. Eze Arias — Balance Croatia 021 — 2025
**Armado:** 2026-09-12  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mazayr | Without Permission | 121 | 5.0 |
| 2 | Mazayr | Falling | 120 | 5.0 |
| 3 | Of Norway | I Miss You (Sentre Remix) | 123 | 5.5 |
| 4 | Luke Santos | I Am Human (Kasper Koman & Alex O'Rion Remix) | 122 | 5.5 |
| 5 | MoodFreak & Campaner (BR) | Surge (Kebin Van Reeken Remix) | 121 | 5.0 |
| 6 | Anton Borin (RU) | May Spring Come (Original Mix) | 123 | 5.5 |
| 7 | Kyotto | Sorry I'm Late (HAFT Remix) | 123 | 5.5 |
| 8 | Jon Towell | 49 Miles (Original Mix) | 123 | 5.5 |
| 9 | WhoMadeWho & Blue Hawaii | Kiss Me Hard (Adam Ten Remix) | 123 | 5.5 |
| 10 | Supacooks, Bondarev | Activator (Original Mix) | 123 | 5.5 |
| 11 | Blake Jarrell | Twenty Miami's Ago (Cendryma Extended Mix) | 122 | 5.5 |
| 12 | Jody Wisternoff, PROFF, James Grant, Siobhan Wilson, Takeshi Furukawa | Mui (Ezequiel Arias Extended Mix) | 125 | 5.5 |
| 13 | Pedro Capelossi, Aeikus | Topaz (Original Mix) | 123 | 5.5 |
| 14 | Remcord | Out Of It (Original Mix) | 123 | 5.5 |
| 15 | Kamilo Sanclemente | Anagram (Mayro Extended Remix) | 123 | 5.5 |
| 16 | Guy J | Silver Lake (Original Mix) | 122 | 5.5 |
| 17 | Kamilo Sanclemente | Astronauts Nightmares (DJ Ruby Extended Remix) | 123 | 5.5 |
| 18 | Ezequiel Arias | Passenger (Original Mix) | 122 | 5.5 |


## Set 17. 17. Eze Arias — Lollapalooza / Rosario — 2025
**Armado:** 2026-09-12  
**Duracion:** 2.0h  
**Tracks:** 8  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hermanez | Eight Years (Original Mix) | 122 | 5.5 |
| 2 | Juan Deminicis | Deep Rock Galactic (Original Mix) | 122 | 5.5 |
| 3 | Simon Vuarambon | 1996 (Original Mix) | 122 | 5.5 |
| 4 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 5.0 |
| 5 | Mike Rish | Tú Attair (Original Mix) | 119 | 3.5 |
| 6 | Simon Vuarambon | Diafana (Original Mix) | 121 | 5.0 |
| 7 | Simon Vuarambón | Afrika | 121 | 5.0 |
| 8 | Simon Vuarambon | Prodiga | 122 | 5.5 |


## Set 18. 18. Digweed — Transitions 2025 Selection
**Armado:** 2026-09-12  
**Duracion:** 3.0h  
**Tracks:** 17  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Panorama Channel | Kinly Estellar | 120 | 5.0 |
| 2 | Jon Towell | 49 Miles (Original Mix) | 123 | 5.5 |
| 3 | Benja Molina | Aura (Original Mix) | 123 | 5.5 |
| 4 | Hermanez | Eight Years (Original Mix) | 122 | 5.5 |
| 5 | Cubicolor | Hardly A Day, Hardly A Night | 120 | 5.0 |
| 6 | Juan Deminicis | Under Control (Original Mix) | 121 | 5.0 |
| 7 | Michael A | Hunting Flowers (Radio Edit) | 120 | 5.0 |
| 8 | Nicolas Rada | Glasgow (Original Mix) | 122 | 5.5 |
| 9 | Tantum | Out Of Nowhere (Original Mix) | 121 | 5.0 |
| 10 | Mike Rish | Tú Attair (Original Mix) | 119 | 3.5 |
| 11 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 5.0 |
| 12 | Fer Torti | Star Trip | 120 | 5.0 |
| 13 | Cornucopia | Early Morning (Original Mix) | 118 | 3.5 |
| 14 | Dmitry Molosh | Bird Flight (Original Mix) | 120 | 5.0 |
| 15 | Remcord | Out Of It (Original Mix) | 123 | 5.5 |
| 16 | Sebastian Sellares | Limbo (Extended Mix) | 120 | 5.0 |
| 17 | John Cosani | Snano (Original Mix) | 123 | 5.5 |


## Set 19. 19. Vuarambon — We Are Lost / Forja 2025
**Armado:** 2026-09-12  
**Duracion:** 2.0h  
**Tracks:** 9  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | John Cosani | Snano (Original Mix) | 123 | 5.5 |
| 2 | Hermanez | Eight Years (Original Mix) | 122 | 5.5 |
| 3 | Benja Molina | Aura (Original Mix) | 123 | 5.5 |
| 4 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 5.0 |
| 5 | Simon Vuarambon | 1996 (Original Mix) | 122 | 5.5 |
| 6 | Mike Rish | Tú Attair (Original Mix) | 119 | 3.5 |
| 7 | Simon Vuarambon | Diafana (Original Mix) | 121 | 5.0 |
| 8 | Simon Vuarambón | Afrika | 121 | 5.0 |
| 9 | Simon Vuarambon | Prodiga | 122 | 5.5 |


## Set 20. 20. Emi Galvan — Flowing 058 / Balance 2026
**Armado:** 2026-09-12  
**Duracion:** 2.0h  
**Tracks:** 10  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Jon Towell | 49 Miles (Original Mix) | 123 | 5.5 |
| 2 | Hermanez | Eight Years (Original Mix) | 122 | 5.5 |
| 3 | Tantum | Out Of Nowhere (Original Mix) | 121 | 5.0 |
| 4 | Emi Galvan | Lies (Original Mix) | 122 | 5.5 |
| 5 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 5.0 |
| 6 | Emi Galvan | Flowing | 121 | 5.0 |
| 7 | Ezequiel Arias | Passenger (Original Mix) | 122 | 5.5 |
| 8 | Kamilo Sanclemente | Anagram (Original Mix) | 123 | 5.5 |
| 9 | Simon Vuarambon | Diafana (Original Mix) | 121 | 5.0 |
| 10 | Simon Vuarambón | Afrika | 121 | 5.0 |


## Set 27. 27. Progressive Colorido A — 2h — 2026-05-27
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 10  
**BPM range:** 118-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Ben Böhmer | Begin Again (Original Mix) | 121 | 5.0 |
| 2 | Ben Böhmer | Blossoms | 123 | 5.5 |
| 3 | N'to | Alter Ego | 123 | 5.5 |
| 4 | Monolink | Don't Hold Back | 120 | 5.0 |
| 5 | Lane 8 | Keep On (Extended Mix) | 122 | 5.5 |
| 6 | Khen | The Lighthouse (Original Mix) | 124 | 6.0 |
| 7 | Ben Bohmer | In Memoriam | 124 | 6.0 |
| 8 | Tinlicker, Helsloot | Because You Move Me (Extended Mix) | 123 | 5.5 |
| 9 | Ben Bohmer | Beyond Beliefs (Original Mix) | 124 | 6.0 |
| 10 | Monolink | The Prey | 108 | 2.5 |


## Set 28. 28. Progressive Colorido B — 2h — 2026-05-27
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 14  
**BPM range:** 119-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Rufus Du Sol | Eyes | 124 | 6.0 |
| 2 | Solomun | Hypnotize | 125 | 6.0 |
| 3 | Rufus Du Sol | Treat You Better | 122 | 5.5 |
| 4 | Anyma & Chris Avantgarde | Eternity | 125 | 6.0 |
| 5 | Solomun | Customer Is King | 123 | 5.5 |
| 6 | Rufus Du Sol | Innerbloom (Original Mix) | 122 | 5.5 |
| 7 | Solomun | Kackvogel | 118 | 3.5 |
| 8 | Kasper Koman | The Blind Navigator (Extended Mix) | 122 | 5.5 |
| 9 | Massano | Falling | 122 | 5.5 |
| 10 | Anyma | Explore Your Future | 124 | 6.0 |
| 11 | Armen Miran | Heavenly Life | 118 | 3.5 |
| 12 | Tale Of Us & Mind Against | Astral (Original Mix) | 124 | 6.0 |
| 13 | Bicep | Glue (Original Mix) | 130 | 6.5 |
| 14 | Joris Voorn | Incident (Original Mix) | 135 | 6.5 |


## Set 29. 29. Mango Alley Deep — 2h — 2026-06-01
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 15  
**BPM range:** 120-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Dowden | Urias | 121 | 5.0 |
| 2 | Dowden | Gavia (Original Mix) | 122 | 5.5 |
| 3 | Rockka | Decryptor | 122 | 5.5 |
| 4 | Rauschhaus, Cary Crank | Bright Things in Front of Us (Extended Mix) | 122 | 5.5 |
| 5 | Maze 28 | Stardust (Original Mix) | 121 | 5.0 |
| 6 | Rockka | Elevation | 122 | 5.5 |
| 7 | Maze 28 | Redux | 122 | 5.5 |
| 8 | Rockka | Subversion | 123 | 5.5 |
| 9 | Maze 28 | Nocte | 122 | 5.5 |
| 10 | Ruben Karapetyan, Maze 28 | Cosmic Dot | 123 | 5.5 |
| 11 | Maze 28 | C Moon (Original Mix) | 122 | 5.5 |
| 12 | Dowden | Pacifist (Original Mix) | 121 | 5.0 |
| 13 | Rauschhaus, Cary Crank | Bekal (Extended Mix) | 120 | 5.0 |
| 14 | Rockka, Maze 28 | Chroma (Original Mix) | 122 | 5.5 |
| 15 | Dowden | Eternity | 121 | 5.0 |


## Set 30. 30. Hobin & Cendryma — 2h — 2026-06-01
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 17  
**BPM range:** 119-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hobin Rude | Prism (Original Mix) | 121 | 5.0 |
| 2 | Ewan Rill | Omega Torra | 122 | 5.5 |
| 3 | Cendryma | Destination (Original Mix) | 122 | 5.5 |
| 4 | Nicolas Rada | El Oro De Los Tigres | 122 | 5.5 |
| 5 | Ewan Rill, Shayan Pasha | Hidden Path (Original Mix) | 120 | 5.0 |
| 6 | Armen Miran & Nicolas Rada | Fall Away (Original Mix) | 120 | 5.0 |
| 7 | Cendryma | Orbitation (Extended Mix) | 122 | 5.5 |
| 8 | Armen Miran & Nicolas Rada | Pull (Original Mix) | 122 | 5.5 |
| 9 | Cendryma | Opulence (Original Mix) | 122 | 5.5 |
| 10 | Hobin Rude | Nether (Original Mix) | 120 | 5.0 |
| 11 | Cendryma | Evasive (Extended Mix) | 121 | 5.0 |
| 12 | Nicolas Rada | The Wind Phone | 123 | 5.5 |
| 13 | Nicolas Rada, Antrim | Daydream (Original Mix) | 121 | 5.0 |
| 14 | Hobin Rude | Shrouded Glint (Original Mix) | 122 | 5.5 |
| 15 | Nicolas Rada | Cascadia | 122 | 5.5 |
| 16 | Hobin Rude | Dusk Petals (Original Mix) | 121 | 5.0 |
| 17 | Ewan Rill, K Loveski | Jala (Original Mix) | 122 | 5.5 |


## Set 31. 31. Gai Barone Universe — 2h — 2026-06-01
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 10  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hermanez | Tale of the Unexpected (Original Mix) | 123 | 5.5 |
| 2 | Chelakhov | Rawai (Extended Mix) | 122 | 5.5 |
| 3 | Hermanez | Areia (Original Mix) | 120 | 5.0 |
| 4 | Chelakhov | Crystal Fall (Original Mix) | 120 | 5.0 |
| 5 | Gai Barone | Weird Behaviours (Original Mix) | 122 | 5.5 |
| 6 | Hermanez | Dust Town | 122 | 5.5 |
| 7 | Hermanez | Third Decade | 120 | 5.0 |
| 8 | Gai Barone | MoMa | 123 | 5.5 |
| 9 | Gai Barone | Shuttered (Original Mix) | 122 | 5.5 |
| 10 | Gai Barone | Hemels (Original Mix) | 122 | 5.5 |


## Set 32. 32. Emi Style — 2h — 2026-06-01
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 17  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Emi Galvan | Timeless (Original Mix) | 121 | 5.0 |
| 2 | Hraach | Cosmic Drama (Original Mix) | 120 | 5.0 |
| 3 | Tantum | Another Day (Original Mix) | 120 | 5.0 |
| 4 | Mike Rish | Shokl (Original Mix) | 118 | 3.5 |
| 5 | Hraach | Delirio (Original Mix) | 120 | 5.0 |
| 6 | Mike Rish | Dope Riddim (Original Mix) | 122 | 5.5 |
| 7 | Kamilo Sanclemente | Theia | 122 | 5.5 |
| 8 | Mike Rish | Sunset on Mars (Original Mix) | 120 | 5.0 |
| 9 | Hraach | Promises (Original Mix) | 121 | 5.0 |
| 10 | Kamilo Sanclemente, Juan Pablo Torrez | Mantura | 122 | 5.5 |
| 11 | Hraach | Lonely Sun (Original Mix) | 122 | 5.5 |
| 12 | Emi Galvan | Trust (Original Mix) | 122 | 5.5 |
| 13 | Tantum | Bonsai (Original Mix) | 124 | 6.0 |
| 14 | Emi Galvan | Samsara | 122 | 5.5 |
| 15 | Kamilo Sanclemente | Go Home (Original Mix) | 121 | 5.0 |
| 16 | Emi Galvan | Vibration (Original Mix) | 122 | 5.5 |
| 17 | Mike Rish | Tunnel People (Original Mix) | 120 | 5.0 |


## Set 33. 33. GMJ Universe — Hipnotico Oscuro — 2026-06-04
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 17  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Dmitry Molosh | Cascade | 122 | 5.5 |
| 2 | Hernan Cattaneo & Soundexile | Deneb | 122 | 5.5 |
| 3 | Armen Miran & Felix Raphael | Ghost | 121 | 5.0 |
| 4 | GMJ & Matter | Soular (Original Mix) | 120 | 5.0 |
| 5 | Hernan Cattaneo & Soundexile | Astron (Original Mix) | 122 | 5.5 |
| 6 | GMJ & Matter | Metanoia | 122 | 5.5 |
| 7 | Marcelo Vasami | Shades Of Blue (Original Mix) | 122 | 5.5 |
| 8 | Dmitry Molosh | Glide | 121 | 5.0 |
| 9 | Hernan Cattaneo & Soundexile | Pressure Drop | 122 | 5.5 |
| 10 | GMJ & Matter | Arkeron (Original Mix) | 120 | 5.0 |
| 11 | Ruben Karapetyan | State of Progression (Original Mix) | 122 | 5.5 |
| 12 | GMJ, Matter | Telomeres (Original Mix) | 121 | 5.0 |
| 13 | Ruben Karapetyan | Nostalgic Moments (Original Mix) | 121 | 5.0 |
| 14 | Cid Inc. | Citadel (Original Mix) | 123 | 5.5 |
| 15 | Cid Inc. | Rescue Me (Original Mix) | 123 | 5.5 |
| 16 | Dmitry Molosh | Only U | 120 | 5.0 |
| 17 | Jamie Stevens & GMJ | Force of Nature (Original Mix) | 120 | 5.0 |


## Set 34. 34. Tom Pavicich & Friends — 2026-06-04
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 12  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Rodriguez Jr. | 1PM Sunrise | 124 | 6.0 |
| 2 | Tom Pavicich | Sugar Rush (Original Mix) | 123 | 5.5 |
| 3 | Tom Pavicich, Analog Sense | Anger (Original Mix) | 123 | 5.5 |
| 4 | Rodriguez Jr. | Nairobi (Original Mix) | 124 | 6.0 |
| 5 | Tom Pavicich | Fly Home (Original Mix) | 122 | 5.5 |
| 6 | Tom Pavicich | Volver (Original Mix) | 123 | 5.5 |
| 7 | Rodriguez Jr. | Hydra | 122 | 5.5 |
| 8 | Tali Muss & Bondarev | Algorythm | 122 | 5.5 |
| 9 | Gorkiz & Tonaco | Serenity | 122 | 5.5 |
| 10 | Gorkiz | Fired (Original Mix) | 123 | 5.5 |
| 11 | Gorkiz & Gastón Sosa | All Night Long | 122 | 5.5 |
| 12 | Rodriguez Jr. | Twilight Language (Extended Version) | 123 | 5.5 |


## Set 35. 35. Lee Burridge Deep — Organic — 2026-06-04
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 16  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy Mantzur, Roy Rosenfeld | Epika (Original Mix) | 120 | 5.0 |
| 2 | Jamie Stevens | Cdx5 | 124 | 6.0 |
| 3 | Guy Mantzur & Khen | Where Is Home (Original Mix) | 122 | 5.5 |
| 4 | Simon Vuarambon | Quimera (Original Mix) | 121 | 5.0 |
| 5 | Lee Burridge, Lost Desert | Chicago Drive (Original Mix) | 121 | 5.0 |
| 6 | Guy Mantzur | My Wild Flower (Original Mix) | 123 | 5.5 |
| 7 | Lee Burridge, Lost Desert | Moogami (Original Mix) | 121 | 5.0 |
| 8 | Lee Burridge, Lost Desert | In the Dark (Original Mix) | 122 | 5.5 |
| 9 | PROFF | Reverie | 122 | 5.5 |
| 10 | Simon Vuarambon | Alcyon | 120 | 5.0 |
| 11 | Simon Vuarambon | DEC (Original Mix) | 121 | 5.0 |
| 12 | Guy Mantzur, Tamir Regev | Stargazer (Original Mix) | 122 | 5.5 |
| 13 | Jamie Stevens | Creature of Comfort | 123 | 5.5 |
| 14 | Lee Burridge, Lost Desert | Forget (Original Mix) | 121 | 5.0 |
| 15 | Simon Vuarambon | Lazos (Original Mix) | 120 | 5.0 |
| 16 | PROFF, Khen, Volen Sentir | Mirage (Extended Mix) | 122 | 5.5 |


## Set 36. 36. This Guy Ben Peak — 2026-06-04
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 16  
**BPM range:** 121-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | This Guy Ben | Condor (Extended Mix) | 124 | 6.0 |
| 2 | Fur Coat | Ethereal | 124 | 6.0 |
| 3 | This Guy Ben | Hey Sally (Extended Mix) | 122 | 5.5 |
| 4 | Massano | System | 122 | 5.5 |
| 5 | This Guy Ben | Corbiere (Extended Mix) | 124 | 6.0 |
| 6 | Fur Coat | Modular Theory | 124 | 6.0 |
| 7 | This Guy Ben | Kapalla (Extended Mix) | 122 | 5.5 |
| 8 | Tinlicker | Compound (Extended Mix) | 124 | 6.0 |
| 9 | Fur Coat | Pandora's Dream (Original Mix) | 124 | 6.0 |
| 10 | Tinlicker | All That I Lost | 124 | 6.0 |
| 11 | Cristoph, ADZ | Solpaz | 123 | 5.5 |
| 12 | Massano | Solitude | 123 | 5.5 |
| 13 | Oliver Schories | Lymn (Original Mix) | 124 | 6.0 |
| 14 | Massano | Odyssey | 122 | 5.5 |
| 15 | Oliver Schories | Peron (Original Mix) | 123 | 5.5 |
| 16 | Fur Coat | Doppler Effect | 124 | 6.0 |


## Set 37. 37. Bedouin x Monolink — Peluqueria — 2026-06-13
**Armado:** 2026-09-12  
**Duracion:** 3h  
**Tracks:** 11  
**BPM range:** 116-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hot Oasis | Bedouin Joy (Original Mix) | 121 | 5.0 |
| 2 | Monolink | Don't Hold Back | 120 | 5.0 |
| 3 | Nils Hoffmann, Julia Church | 9 Days (Dosem Extended Mix) | 125 | 6.0 |
| 4 | Monolink, Stephan Jolk | The Silence (Original Mix) | 124 | 6.0 |
| 5 | Ben Böhmer, Nils Hoffmann & Malou | Breathing (Extended Mix) | 122 | 5.5 |
| 6 | Adam Port, Monolink | Point Of No Return (Extended Mix) | 122 | 5.5 |
| 7 | Bedouin | Petra (Extended Version) | 120 | 5.0 |
| 8 | Nils Hoffmann, Julia Church | 9 Days (Extended Mix) | 120 | 5.0 |
| 9 | Bedouin | Flight of Birds | 120 | 5.0 |
| 10 | Bedouin | Straight To The Heart | 116 | 2.5 |
| 11 | Bedouin | Set The Controls For The Heart Of The Sun (Original Mix) | 118 | 3.5 |


## Set 38. 38. Rodriguez Jr. x Adriatique — Oscuro Progresivo — 2026-06-13
**Armado:** 2026-09-12  
**Duracion:** 3h  
**Tracks:** 19  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Adriatique | Voices From The Dawn | 121 | 5.0 |
| 2 | Rodriguez Jr. | 1PM Sunrise | 124 | 6.0 |
| 3 | Adriatique | Mystery (Isolee Remix) | 121 | 5.0 |
| 4 | Jeremy Olander | Panorama (Original Mix) | 123 | 5.5 |
| 5 | Rodriguez Jr. | Hydra | 122 | 5.5 |
| 6 | Adriatique | Ray | 123 | 5.5 |
| 7 | Adriatique, Delhia De France, Marino Canal | Home (Original Mix) | 120 | 5.0 |
| 8 | Adriatique | Grinding Rhythm | 123 | 5.5 |
| 9 | Rodriguez Jr. | Twilight Language (Extended Version) | 123 | 5.5 |
| 10 | Jeremy Olander | Passagen (Original Mix) | 125 | 6.0 |
| 11 | Jeremy Olander | Steps (Original Mix) | 126 | 6.5 |
| 12 | Rodriguez Jr. | Nairobi (Original Mix) | 124 | 6.0 |
| 13 | Adriatique, Argy | RACER (Extended Mix) | 125 | 6.0 |
| 14 | Rodriguez Jr. | Kilian | 125 | 6.0 |
| 15 | Pional | Tempest | 120 | 5.0 |
| 16 | Kiko & Rodriguez Jr. | Miller | 123 | 5.5 |
| 17 | Jeremy Olander | Leftwoods (Original Mix) | 120 | 5.0 |
| 18 | Jeremy Olander | Nattuggla | 123 | 5.5 |
| 19 | Jeremy Olander | Saigon | 123 | 5.5 |


## Set 39. 39. Guy Mantzur x Max Cooper — Dark Melodico — 2026-06-13
**Armado:** 2026-09-12  
**Duracion:** 3h  
**Tracks:** 18  
**BPM range:** 115-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Max Cooper | Resynthesis (Original Mix) | 120 | 5.0 |
| 2 | Max Cooper | Music of the Tides (Original Mix) | 121 | 5.0 |
| 3 | Hernan Cattaneo, Hicky & Kalo | Voyage | 123 | 5.5 |
| 4 | Max Cooper | Hope | 120 | 5.0 |
| 5 | Nick Warren | Balance | 122 | 5.5 |
| 6 | Hernan Cattaneo & Soundexile | Pick Up | 122 | 5.5 |
| 7 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 5.0 |
| 8 | Hernan Cattaneo & Soundexile | Deneb | 122 | 5.5 |
| 9 | Guy Mantzur, Roy Rosenfeld | Epika (Original Mix) | 120 | 5.0 |
| 10 | Hernan Cattaneo & Soundexile | Wind Down (Outro Mix) | 122 | 5.5 |
| 11 | Max Cooper | Balance Perc Tool (Original Mix) | 119 | 3.5 |
| 12 | Hernan Cattaneo, Husa & Zeyada | Love Is Coming Back (Club Mix) | 121 | 5.0 |
| 13 | Guy Mantzur & Khen | Where Is Home (Original Mix) | 122 | 5.5 |
| 14 | Guy Mantzur | Blackout Station (Original Mix) | 125 | 6.0 |
| 15 | Guy Mantzur | My Wild Flower (Original Mix) | 123 | 5.5 |
| 16 | Guy Mantzur, Khen | My Golden Cage (Original Mix) | 122 | 5.5 |
| 17 | Nick Warren | Dreamcatcher | 115 | 2.5 |
| 18 | Hernan Cattaneo & Soundexile | Astron (Original Mix) | 122 | 5.5 |


## Set 40. 40. Gorje Hewek x Hraach — Armenio Profundo — 2026-06-13
**Armado:** 2026-09-12  
**Duracion:** 3h  
**Tracks:** 25  
**BPM range:** 116-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hraach | Cosmic Drama (Original Mix) | 120 | 5.0 |
| 2 | Armen Miran & Nicolas Rada | Pull (Original Mix) | 122 | 5.5 |
| 3 | Jan Blomqvist, Alar, Korolova | Time Again (Original Mix) | 123 | 5.5 |
| 4 | Roy Rosenfeld, Gorje Hewek, Dulus | Vida (Original Mix) | 122 | 5.5 |
| 5 | Hraach | Promises (Original Mix) | 121 | 5.0 |
| 6 | Gorje Hewek & Izhevski | When I Was Young (Original Mix) | 120 | 5.0 |
| 7 | Hraach | Lonely Sun (Original Mix) | 122 | 5.5 |
| 8 | Gorje Hewek | U & Eyeye | 122 | 5.5 |
| 9 | Hraach, Armen Miran | Traveller (Original Mix) | 122 | 5.5 |
| 10 | Gorje Hewek | Solovey (Original Mix) | 122 | 5.5 |
| 11 | Hraach | Delirio (Original Mix) | 120 | 5.0 |
| 12 | Gorje Hewek, Molac, Dulus | Astro World (Original Mix) | 120 | 5.0 |
| 13 | Armen Miran & Felix Raphael | Ghost | 121 | 5.0 |
| 14 | Gorje Hewek | Changes (Extended Mix) | 122 | 5.5 |
| 15 | Armen Miran & Lost Desert | Don't Worry | 124 | 6.0 |
| 16 | Gorje Hewek, Dulus | Earth (Original Mix) | 123 | 5.5 |
| 17 | Armen Miran | Nani Jan (Original) | 120 | 5.0 |
| 18 | Gorje Hewek, Makebo & Amonita | Never Been | 122 | 5.5 |
| 19 | Armen Miran & Nicolas Rada | Fall Away (Original Mix) | 120 | 5.0 |
| 20 | Gorje Hewek | Actrice (Original Mix) | 120 | 5.0 |
| 21 | Hraach, Armen Miran | Nervous Layers (Original Mix) | 118 | 3.5 |
| 22 | Hraach, Armen Miran | Krunk (Original Mix) | 116 | 2.5 |
| 23 | Armen Miran & Hraach | Aldebaran | 116 | 2.5 |
| 24 | Hraach, Armen Miran | Mysterious World (Original Mix) | 118 | 3.5 |
| 25 | Armen Miran | Save My Soul (Original Mix) | 116 | 2.5 |


## Set 41. 41. Dulce Progresivo — Loveland Style — 2026-06-13
**Armado:** 2026-09-12  
**Duracion:** 3h  
**Tracks:** 21  
**BPM range:** 120-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Joan Retamero, Greta Meier | The Beginning (Original Mix) | 122 | 5.0 |
| 2 | Sebastien Leger | Firefly (Original Mix) | 121 | 5.0 |
| 3 | Christopher Erre, Greta Meier | Giza (Original Mix) | 122 | 5.5 |
| 4 | Sebastien Leger | Stevie (Original Mix) | 121 | 5.0 |
| 5 | Roy Rosenfeld | Hypnosa De La Rosa | 123 | 5.5 |
| 6 | Greta Meier, Maze 28 | Acceptance (Original Mix) | 122 | 5.5 |
| 7 | Sebastien Leger | Quand Je Serai Seul | 120 | 5.0 |
| 8 | Roy Rosenfeld | Kala | 120 | 5.0 |
| 9 | Ezequiel Arias | Púrpura | 122 | 5.5 |
| 10 | Roy Rosenfeld | Halomot | 123 | 5.5 |
| 11 | Christopher Erre, Greta Meier | Osiris (Original Mix) | 123 | 5.5 |
| 12 | Simon Doty | Solstice (Extended Mix) | 124 | 6.0 |
| 13 | Ezequiel Arias | Esperanza (Extended Mix) | 124 | 6.0 |
| 14 | Simon Doty | Solstice (Extended Mix) | 124 | 6.0 |
| 15 | Ezequiel Arias | Solar (Extended Mix) | 123 | 5.5 |
| 16 | Sebastien Leger, Roy Rosenfeld | Panko Day (Extended Mix) | 121 | 5.0 |
| 17 | Melodiam | Old Garden | 122 | 5.5 |
| 18 | Roy Rosenfeld | Skyhook (Original Mix) | 121 | 5.0 |
| 19 | Ezequiel Arias | Modern Memory (Extended Mix) | 122 | 5.5 |
| 20 | Sebastian Sellares, Greta Meier | Benevolence (Extended Mix) | 121 | 5.0 |
| 21 | Simon Doty | The Beacon | 124 | 6.0 |


## Set 42. 42. Emi & Kamilo — Colorido Progresivo — 2026-06-13
**Armado:** 2026-09-12  
**Duracion:** 3h  
**Tracks:** 17  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Emi Galvan | Taking Over (Rogier Remix) | 121 | 5.0 |
| 2 | Kamilo Sanclemente | Divine Eternity (K Loveski Remix) | 121 | 5.0 |
| 3 | Emi Galvan | No Regrets (Original Mix) | 123 | 5.5 |
| 4 | Amir Telem | How To Learn Something New (Greg Ochman Remix) | 120 | 5.0 |
| 5 | Emi Galvan | Crabo (Original Mix) | 122 | 5.5 |
| 6 | Greg Ochman | In Between Dreams | 120 | 5.0 |
| 7 | Kamilo Sanclemente | Go Home (Original Mix) | 121 | 5.0 |
| 8 | Emi Galvan | Around the World | 122 | 5.5 |
| 9 | Emi Galvan | Trust (Original Mix) | 122 | 5.5 |
| 10 | Kamilo Sanclemente | Delusion (Original Mix) | 122 | 5.5 |
| 11 | Kamilo Sanclemente | Parallel Moon (Original Mix) | 123 | 5.5 |
| 12 | Kamilo Sanclemente | Strange Days (Original Mix) | 121 | 5.0 |
| 13 | Greg Ochman | Blinking Stars (Luka Sambe Remix) | 123 | 5.5 |
| 14 | Emi Galvan | Timeless (Original Mix) | 121 | 5.0 |
| 15 | Kamilo Sanclemente | The Last Mermaid | 122 | 5.5 |
| 16 | Emi Galvan | Free Your Mind | 122 | 5.5 |
| 17 | Emi Galvan | Supernova (Original Mix) | 123 | 5.5 |


## Set 43. 43. Maze 28 + Cendryma — Nuevo Prog — 2026-06-13
**Armado:** 2026-09-12  
**Duracion:** 3h  
**Tracks:** 24  
**BPM range:** 120-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Cendryma | Parabolic (Original Mix) | 122 | 5.5 |
| 2 | Gai Barone | Fractals (HAFT Extended Remix) | 122 | 5.5 |
| 3 | Cendryma | Typical Use (Original Mix) | 121 | 5.0 |
| 4 | Rockka | Initiation | 123 | 5.5 |
| 5 | Maze 28 | Stardust (Original Mix) | 121 | 5.0 |
| 6 | Gai Barone | Weird Behaviours (Original Mix) | 122 | 5.5 |
| 7 | Hobin Rude | Nothing's Gonna Hurt You | 122 | 5.5 |
| 8 | Cendryma | Orbitation (Extended Mix) | 122 | 5.5 |
| 9 | Maze 28 | Redux | 122 | 5.5 |
| 10 | Rockka | Elevation | 122 | 5.5 |
| 11 | Hobin Rude | Nether (Original Mix) | 120 | 5.0 |
| 12 | Cendryma | Effective Loss (Original Mix) | 121 | 5.0 |
| 13 | Chelakhov | Rawai (Extended Mix) | 122 | 5.5 |
| 14 | Rockka | The Fade (Dave Walker Remix) | 122 | 5.5 |
| 15 | Rockka | Subversion | 123 | 5.5 |
| 16 | Maze 28 | Nocte | 122 | 5.5 |
| 17 | Chelakhov | Crystal Fall (Original Mix) | 120 | 5.0 |
| 18 | Cary Crank | Inner Atlas (Kyotto Remix) | 122 | 5.5 |
| 19 | Maze 28 | Leave the World Behind (Original Mix) | 122 | 5.5 |
| 20 | Chelakhov | Searching (Gero Pellizzon Remix) | 122 | 5.5 |
| 21 | Gai Barone | Hemels (Original Mix) | 122 | 5.5 |
| 22 | Hobin Rude | Shrouded Glint (Original Mix) | 122 | 5.5 |
| 23 | Gai Barone | MoMa | 123 | 5.5 |
| 24 | Cary Crank | Deep Forest (Extended Mix) | 122 | 5.5 |


## Set 44. 44. Dowden + Guy J — Progressive Profundo — 2026-06-13
**Armado:** 2026-09-12  
**Duracion:** 2.5h  
**Tracks:** 15  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy J | Karma (Original Mix) | 122 | 5.5 |
| 2 | Guy J | State of Trance | 122 | 5.5 |
| 3 | Dowden & Ric Niels | Coil | 121 | 5.0 |
| 4 | Dmitry Molosh | Bird Flight (Original Mix) | 120 | 5.0 |
| 5 | Dowden | Urias | 121 | 5.0 |
| 6 | Dmitry Molosh | Step by Step feat. Sasha Bartashevich (Original Dub Mix) | 121 | 5.0 |
| 7 | Dowden | Gavia (Original Mix) | 122 | 5.5 |
| 8 | Guy J | Day Of Light (Original Mix) | 123 | 5.5 |
| 9 | Yotto | Radiate (Extended Mix) | 124 | 6.0 |
| 10 | Ric Niels & Dowden | Spiral (GMJ Remix) | 121 | 5.0 |
| 11 | Dmitry Molosh | Ambition (Original Mix) | 121 | 5.0 |
| 12 | Guy J | Nirvana | 120 | 5.0 |
| 13 | Dowden | Eternity | 121 | 5.0 |
| 14 | Orbital, Yotto | Belfast - Yotto Remix | 123 | 5.5 |
| 15 | Dmitry Molosh | Glide | 121 | 5.0 |


## Set 45. 45. Tom Pavicich + Durante — Prog Argentino — 2026-06-13
**Armado:** 2026-09-12  
**Duracion:** 2.5h  
**Tracks:** 15  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hraach | Cosmic Drama (Original Mix) | 120 | 5.0 |
| 2 | Nicolas Rada | El Oro De Los Tigres | 122 | 5.5 |
| 3 | Tom Pavicich | Fly Home (Original Mix) | 122 | 5.5 |
| 4 | Durante | Winder | 122 | 5.5 |
| 5 | Tom Pavicich | Volver (Original Mix) | 123 | 5.5 |
| 6 | Tom Pavicich | About Her (Unai Garcia Remix) | 121 | 5.0 |
| 7 | Hraach | Delirio (Original Mix) | 120 | 5.0 |
| 8 | Tom Pavicich | About Her (Original Mix) | 122 | 5.5 |
| 9 | Hraach | Lonely Sun (Original Mix) | 122 | 5.5 |
| 10 | Hraach | Promises (Original Mix) | 121 | 5.0 |
| 11 | Nicolas Rada | Prana | 119 | 3.5 |
| 12 | Simon Vaurambon | Leman (Original Mix) | 120 | 5.0 |
| 13 | Nicolas Rada | The Wind Phone | 123 | 5.5 |
| 14 | Nicolas Rada | Cascadia | 122 | 5.5 |
| 15 | Durante | Thread Tension | 122 | 5.5 |


## Set 46. 46. Hernan Cattaneo — Warung Last Set Style — 2026-06-17
**Armado:** 2026-09-12  
**Duracion:** 3h  
**Tracks:** 13  
**BPM range:** 114-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy Gerber | Timing (Original) | 126 | 6.5 |
| 2 | EdOne, Weizman | Misery (Original Mix) | 123 | 5.5 |
| 3 | David August | Epikur (Original Mix) | 118 | 3.5 |
| 4 | Radio Slave | Strobe Queen | 120 | 5.0 |
| 5 | Simos Tagias, Tonaco | Alnilam (Original Mix) | 122 | 5.5 |
| 6 | Pachanga Boys | Time | 124 | 6.0 |
| 7 | Gorje Hewek & Izhevski | Calinerie | 120 | 5.0 |
| 8 | Seth Schwarz & Be Svendsen | The Bar Tender | 121 | 5.0 |
| 9 | Hot Tuneik, Sarah Chilanti | Soul on Fire (Original Mix) | 120 | 5.0 |
| 10 | Nora En Pure | Spring Embers (Extended Mix) | 122 | 5.5 |
| 11 | Makebo & Amonita | Back To The Roots (Extended Mix) | 122 | 5.5 |
| 12 | Guy J | Dizzy Moments | 125 | 6.0 |
| 13 | Ezequiel Arias | Psychodelia (Extended Mix) | 125 | 6.0 |


## Set 55. 55. Radar Oscuro — Hipnotico — 2h — 2026-08-03
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 16  
**BPM range:** 118-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Danny Howells, Lloyd Barwood | One More Sky (Original Mix) | 124 | 6.0 |
| 2 | Cendryma | Point Capricorn (Original Mix) | 122 | 5.5 |
| 3 | Maze 28 | Personal Space (Extended Mix) | 122 | 5.5 |
| 4 | Guy J | Rise (Original Mix) | 122 | 5.5 |
| 5 | Cendryma | Dividing Parts (Original Mix) | 121 | 5.0 |
| 6 | Maze 28 | Mindloop (Original Mix) | 120 | 5.0 |
| 7 | Cendryma | Crow's Cradle (Original Mix) | 118 | 3.5 |
| 8 | Guy J | Piece of Cake (Original Mix) | 122 | 5.5 |
| 9 | Dowden | Night Emeralds (Original Mix) | 122 | 5.5 |
| 10 | Cendryma | Fortress (Original Mix) | 122 | 5.5 |
| 11 | Lost Desert | Black Panther (Original Mix) | 124 | 6.0 |
| 12 | Simon Vuarambon | Stamina (Extended Mix) | 121 | 5.0 |
| 13 | Maze 28 | Tell Me Again (Extended Mix) | 120 | 5.0 |
| 14 | Simon Vuarambon | Estigia (Extended Mix) | 121 | 5.0 |
| 15 | Cendryma | Stasis Drive (Original Mix) | 120 | 5.0 |
| 16 | Cendryma | Meridian Isle (Original Mix) | 118 | 3.5 |


## Set 56. 56. Radar Colorido — Emi/Kamilo — 2h — 2026-08-03
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 14  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Ezequiel Arias | Sin Control (Extended Mix) | 124 | 6.0 |
| 2 | Emi Galvan | Boomera (Original Mix) | 123 | 5.5 |
| 3 | Antrim | Curved (Original Mix) | 123 | 5.5 |
| 4 | Emi Galvan | Reborn (Original Mix) | 124 | 6.0 |
| 5 | Kamilo Sanclemente | Auriga Moon (Original Mix) | 122 | 5.5 |
| 6 | GMJ, Matter | Verticality (Original Mix) | 121 | 5.0 |
| 7 | Makebo | Balance (Original Mix) | 122 | 5.5 |
| 8 | Kamilo Sanclemente | Just Come Back (Extended Mix) | 124 | 6.0 |
| 9 | Emi Galvan | Mily (Original Mix) | 122 | 5.5 |
| 10 | Kamilo Sanclemente, Mauro Aguirre | Looking For You (Extended Mix) | 123 | 5.5 |
| 11 | Emi Galvan | I Wish (Original Mix) | 123 | 5.5 |
| 12 | Kamilo Sanclemente | Tangiers (Original Mix) | 123 | 5.5 |
| 13 | Durante, Emi Galvan | Lunar Circuit (Extended Mix) | 124 | 6.0 |
| 14 | Emi Galvan | Never Ending Summer (Original Mix) | 123 | 5.5 |


## Set 57. 57. Radar Argentina — Driving — 2h — 2026-08-03
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 18  
**BPM range:** 119-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Kasey Taylor, Gai Barone | Spiral (Original Mix) | 124 | 6.0 |
| 2 | Andre Moret | Gaxyda (Original Mix) | 122 | 5.5 |
| 3 | Gai Barone | Taking Credits (Extended Mix) | 122 | 5.5 |
| 4 | Tom Pavicich, Gonzalo Cotroneo | Radiance (Original Mix) | 121 | 5.0 |
| 5 | Zankee Gulati | Arakeen (Original Mix) | 121 | 5.0 |
| 6 | Gai Barone, Greta Meier | Elysium (Original Mix) | 121 | 5.0 |
| 7 | Rockka | Rebit (Original Mix) | 122 | 5.5 |
| 8 | GMJ, Matter, Zankee Gulati | Emerge (Original Mix) | 120 | 5.0 |
| 9 | Mercurio, Hernan Cattaneo | Diluted (Original Mix) | 121 | 5.0 |
| 10 | Nicolas Rada | Roots (Original Mix) | 119 | 3.5 |
| 11 | Gai Barone | All About Her (Original Mix) | 122 | 5.5 |
| 12 | Tom Pavicich | You (Original Mix) | 123 | 5.5 |
| 13 | Andre Moret | Kryon (Original Mix) | 123 | 5.5 |
| 14 | Rockka | Cinimatic (Original Mix) | 123 | 5.5 |
| 15 | Gai Barone | Kromaky (Original Mix) | 123 | 5.5 |
| 16 | Hernan Cattaneo, Tom Pavicich | Bloom (Original Mix) | 125 | 6.0 |
| 17 | Nick Warren & Nicolas Rada | Fuego (Extended Mix) | 124 | 6.0 |
| 18 | Jamie Stevens, Anthony Pappa | We Emerge (Original Mix) | 124 | 6.0 |


## Set 58. 58. Cocina I — Amanecer — 50min — 2026-08-06
**Armado:** 2026-09-12  
**Duracion:** 1h  
**Tracks:** 8  
**BPM range:** 118-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Sebastian Sellares | Timeless Era (Extended Mix) | 122 | 5.5 |
| 2 | Ben Bohmer & Neils Hoffmann feat. Malou | Breathing | 122 | 5.5 |
| 3 | Nils Hoffmann, Julia Church | 9 Days (Extended Mix) | 120 | 5.0 |
| 4 | Lane 8 ft. Solomon Grey | Diamonds (Original Mix) | 120 | 5.0 |
| 5 | Braxton | Torn (feat. Danni Wells) [Extended Mix] | 121 | 5.0 |
| 6 | Jakatta | American Dream (PROFF Extended Interpretation) | 122 | 5.5 |
| 7 | Jody Wisternoff & James Grant | Blue Space (feat. Jinadu) | 120 | 5.0 |
| 8 | Ezequiel Arias | Modern Memory (Extended Mix) | 122 | 5.5 |


## Set 59. 59. Cocina II — Ritual — 50min — 2026-08-06
**Armado:** 2026-09-12  
**Duracion:** 1h  
**Tracks:** 8  
**BPM range:** 118-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hraach | Apricot Tree (Original Mix) | 118 | 3.5 |
| 2 | Armen Miran, Felix Raphael | Ghost (Hernan Cattaneo & Marcelo Vasami Remix) | 120 | 5.0 |
| 3 | Seth Schwarz & Be Svendsen | The Bar Tender | 121 | 5.0 |
| 4 | Lee Burridge, Lost Desert | Forget (Original Mix) | 121 | 5.0 |
| 5 | Bedouin | Flight of Birds | 120 | 5.0 |
| 6 | Gorje Hewek | Actrice (Original Mix) | 120 | 5.0 |
| 7 | Hermanez | Third Decade | 120 | 5.0 |
| 8 | Lee Burridge, Lost Desert | Moogami (Original Mix) | 121 | 5.0 |


## Set 60. 60. Cocina III — Mediodia — 50min — 2026-08-06
**Armado:** 2026-09-12  
**Duracion:** 1h  
**Tracks:** 8  
**BPM range:** 119-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Roy Rosenfeld | Skyhook (Original Mix) | 121 | 5.0 |
| 2 | Sebastien Leger | Firefly (Original Mix) | 121 | 5.0 |
| 3 | Khen | Out Of A Dream (Original Mix) | 121 | 5.0 |
| 4 | Kasper Koman | The Observer | 121 | 5.0 |
| 5 | Sebastien Leger | Stevie (Original Mix) | 121 | 5.0 |
| 6 | Cary Crank | Deep Forest (Extended Mix) | 122 | 5.5 |
| 7 | Sébastien Léger | Forbidden Garden (Tim Green Remix) | 122 | 5.5 |
| 8 | Chicola | Blueberries (Extended) | 122 | 5.5 |


## Set 61. 61. Progresivo Noche — 3h — 2026-08-06
**Armado:** 2026-09-12  
**Duracion:** 3h  
**Tracks:** 39  
**BPM range:** 120-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Maze 28, Rockka | Corrosive | 122 | 5.5 |
| 2 | Guy J | Airborne (Original Mix) | 123 | 5.5 |
| 3 | Nicolas Rada | Glasgow (Original Mix) | 122 | 5.5 |
| 4 | Tom Pavicich, Gonzalo Cotroneo | Radiance (Original Mix) | 121 | 5.0 |
| 5 | Ruben Karapetyan | State of Progression (Original Mix) | 122 | 5.5 |
| 6 | Hobin Rude | Low Light Memory (Original Mix) | 121 | 5.0 |
| 7 | Emi Galvan | Dharma (Original Mix) | 120 | 5.0 |
| 8 | Maze 28 | Aer8 | 122 | 5.5 |
| 9 | Nick Warren | Ultravox (Hernan Cattaneo & Kevin Di Serna Remix) | 123 | 5.5 |
| 10 | Teho | Ashes (Original Mix) | 125 | 6.0 |
| 11 | Miro | Paradise (Quivver Extended Remix) | 124 | 6.0 |
| 12 | Gai Barone | Fractals (HAFT Extended Remix) | 122 | 5.5 |
| 13 | Guy Mantzur & Khen | Where Is Home (Original Mix) | 122 | 5.5 |
| 14 | Tali Muss | Interlocutor (Extended Mix) | 122 | 5.5 |
| 15 | Hobin Rude | Nothing's Gonna Hurt You | 122 | 5.5 |
| 16 | GMJ, Matter, Zankee Gulati | Emerge (Original Mix) | 120 | 5.0 |
| 17 | Max Wexem | Confined (Original Mix) | 120 | 5.0 |
| 18 | Quivver | Forest Moon (Dmitry Molosh Remix) | 121 | 5.0 |
| 19 | Ezequiel Arias | Passenger (Original Mix) | 122 | 5.5 |
| 20 | Nick Warren | Freebird (Emi Galvan Remix) | 123 | 5.5 |
| 21 | GMJ & Matter | Metanoia | 122 | 5.5 |
| 22 | Kasper Koman | Hi (Cid Inc. Remix) | 122 | 5.5 |
| 23 | Lost Desert | Aalam Waahid (Original Mix) | 124 | 6.0 |
| 24 | Paul Arcane | Vortice (Extended Mix) | 123 | 5.5 |
| 25 | Kamilo Sanclemente | Fragma (GORKIZ Remix) | 123 | 5.5 |
| 26 | Artic White | Once We Were (Extended Mix) | 123 | 5.5 |
| 27 | Sébastien Léger, Lost Miracle | Dodonpachi (Original Mix) | 122 | 5.5 |
| 28 | NUFECTS | Inferno (Extended Mix) | 123 | 5.5 |
| 29 | GHEIST | Good Life (Original Mix) | 126 | 6.5 |
| 30 | Guy J | Dizzy Moments | 125 | 6.0 |
| 31 | Gai Barone, Aman Anand | Low Era (Kebin Van Reeken Remix) | 122 | 5.5 |
| 32 | Dmitry Molosh | Ambition (Original Mix) | 121 | 5.0 |
| 33 | Ezequiel Arias | Control Is an Illusion (Original Mix) | 122 | 5.5 |
| 34 | Cendryma | Repressure (Extended Mix) | 121 | 5.0 |
| 35 | Mike Rish | Cloudbreaker | 120 | 5.0 |
| 36 | Kamilo Sanclemente | Whale Voices (Original Mix) | 122 | 5.5 |
| 37 | Mike Rish | Sunset on Mars (Original Mix) | 120 | 5.0 |
| 38 | Tali Muss | Reward (Extended Mix) | 123 | 5.5 |
| 39 | Sahar Z & Guy Mantzur | Survivors Guilt | 125 | 6.0 |


## Set 62. 62. Plano Suspendido — Afterhours — 1h30 — 2026-08-06
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Alex O'Rion | Hartseer (Original Mix) | 120 | 5.0 |
| 2 | Fran Baigo | Levitate (Original Mix) | 123 | 5.5 |
| 3 | Rauschhaus, Cary Crank | Perihelion (Hernan Cattaneo & Mercurio Remix) | 123 | 5.5 |
| 4 | Ignacio Hernández, Tato Seco | Sleepwalker (Original Mix) | 122 | 5.5 |
| 5 | Steven McCreery | Shadows (Original Mix) | 122 | 5.5 |
| 6 | Tonaco, Kebin Van Reeken | Chroma (Original Mix) | 121 | 5.0 |
| 7 | Max Wexem | Override (Original Mix) | 121 | 5.0 |
| 8 | Katzen | What's Beyond (Original Mix) | 120 | 5.0 |
| 9 | MXV | Witch King (Original Mix) | 120 | 5.0 |
| 10 | Shayan Pasha | Phobos (Extended Mix) | 120 | 5.0 |
| 11 | Roger Martinez, Simos Tagias | Inner Light (Original Mix) | 120 | 5.0 |
| 12 | KAZKO | Fading Control (Original Mix) | 122 | 5.5 |


## Set 63. 63. Color Sin Azucar — Prime Time — 1h30 — 2026-08-06
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Christian Smith | Illusion (Ezequiel Arias Remix) | 125 | 6.0 |
| 2 | Emil Toledo, Rinzen | The Shape of Memory (Extended Mix) | 123 | 5.5 |
| 3 | Zankee Gulati | Goofball (Original Mix) | 121 | 5.0 |
| 4 | Hobin Rude | The Quiet Between Us (Original Mix) | 121 | 5.0 |
| 5 | Dmitry Molosh | The Moon Lights the Way (Original Mix) | 122 | 5.5 |
| 6 | GRAZZE | Miami (Extended Mix) | 123 | 5.5 |
| 7 | Florian Gasperini | Third Eye Awakening (Extended Mix) | 123 | 5.5 |
| 8 | Julian Nates | A Better Place (Original Mix) | 124 | 6.0 |
| 9 | Hicky & Kalo, Sinca | Breathe Again (Original Mix) | 123 | 5.5 |
| 10 | Sezer Uysal | Yutori (Ruben Karapetyan Remix) | 122 | 5.5 |
| 11 | Kasey Taylor | Emerging From the Skyline (Original Mix) | 122 | 5.5 |
| 12 | Tali Muss, 84 Avenue | Nebula (Extended Mix) | 123 | 5.5 |


## Set 64. 64. Presion Constante — Peak — 1h30 — 2026-08-06
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Township Rebellion | Birds Fly First Class (Original Mix) | 126 | 6.5 |
| 2 | Anthony Pappa, Aubrey Fry | Itajai (Original Mix) | 125 | 6.0 |
| 3 | Dilby | Body Talk (Original Mix) | 124 | 6.0 |
| 4 | Kit Lawson | Ruff (Original Mix) | 124 | 6.0 |
| 5 | Das Pharaoh, SHERRNX | Astral Abyss (Extended Mix) | 122 | 5.5 |
| 6 | QuiQui, Thom Rich | Victorious (Gai Barone Dark Extended Remix) | 123 | 5.5 |
| 7 | Rodriguez Jr. | Off Gerlach (Original Mix) | 125 | 6.0 |
| 8 | Redspace, Diego Riga | Phantom Sun (Extended Mix) | 124 | 6.0 |
| 9 | Graziano Raffa | Carbonia (Original Mix) | 125 | 6.0 |
| 10 | Serious Dancers | Canopus (Extended Mix) | 124 | 6.0 |
| 11 | D-Nox, Andre Moret | Breath (Original Mix) | 122 | 5.5 |
| 12 | Kabi (AR), Ric Niels | Crossed Paths (Original Mix) | 124 | 6.0 |


## Set 65. 65. Previa Colorida — Warmup — 1h — 2026-08-08
**Armado:** 2026-09-12  
**Duracion:** 1.0h  
**Tracks:** 9  
**BPM range:** 118-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mike Rish | Sunset on Mars (Original Mix) | 120 | 5.0 |
| 2 | Kasper Koman | Loco Motif (Tantum Remix) | 121 | 5.0 |
| 3 | Emi Galvan | Dopamine (Forniva Remix) | 123 | 5.5 |
| 4 | Kamilo Sanclemente, Andre Moret | Spectre (Extended Mix) | 122 | 5.5 |
| 5 | Maze 28 | Stardust (Original Mix) | 121 | 5.0 |
| 6 | D-Nox & Beckers | Bitter Rain (Cid Inc. Remix) | 123 | 5.5 |
| 7 | Kostya Outta, Greta Meier, Alisha (PL) | Far Above (Original Mix) | 123 | 5.5 |
| 8 | Tali Muss, Mayro | Dimension Of Space (Original Mix) | 123 | 5.5 |
| 9 | Tonaco, Kebin Van Reeken | Chroma (Original Mix) | 121 | 5.0 |


## Set 66. 66. Previa Organica — Groove — 1h — 2026-08-08
**Armado:** 2026-09-12  
**Duracion:** 1.0h  
**Tracks:** 9  
**BPM range:** 118-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Gorje Hewek & Izhevski | When I Was Young (Original Mix) | 120 | 5.0 |
| 2 | Monolink | Sirens (H3RMES Edit) | 120 | 5.0 |
| 3 | Sebastien Leger | Firefly (Original Mix) | 121 | 5.0 |
| 4 | Hraach | Promises (Original Mix) | 121 | 5.0 |
| 5 | Khen & Freedom Fighters | Levantine | 122 | 5.5 |
| 6 | Hermanez | Gamma Ray | 123 | 5.5 |
| 7 | Lee Burridge, Lost Desert | Forget (Original Mix) | 121 | 5.0 |
| 8 | Armen Miran & Nicolas Rada | Pull (Original Mix) | 122 | 5.5 |
| 9 | Rodriguez Jr. | Nairobi (Original Mix) | 124 | 6.0 |


## Set 67. 67. Previa Brillante — Vocal — 1h — 2026-08-08
**Armado:** 2026-09-12  
**Duracion:** 1.0h  
**Tracks:** 9  
**BPM range:** 118-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Jody Wisternoff & James Grant | Blue Space (feat. Jinadu) [Extended Mix] | 120 | 5.0 |
| 2 | Muuk', Cendryma | G-Force (Original Mix) | 120 | 5.0 |
| 3 | Panama, Nils Hoffmann | Far Behind (Jeremy Olander Extended Mix) | 123 | 5.5 |
| 4 | Spencer Brown | Comeback Kids (Original Mix) | 124 | 6.0 |
| 5 | Hana, Durante | Celestia (Extended Mix) | 124 | 6.0 |
| 6 | Tinlicker | Compound (Extended Mix) | 124 | 6.0 |
| 7 | Ben Bohmer | In Memoriam | 124 | 6.0 |
| 8 | Tom Pavicich, Analog Sense | Cardamom (Original Mix) | 122 | 5.5 |
| 9 | Lane 8 | Keep On (Extended Mix) | 122 | 5.5 |


## Set 68. 68. Superficie — Groove Directo — 1h30 — 2026-08-09
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 121-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mita Gami | San Pedro | 122 | 5.5 |
| 2 | Pavel Petrov, Rafael Cerato | Reflections (Original mix) | 122 | 5.5 |
| 3 | Jeremy Olander | Panorama (Original Mix) | 123 | 5.5 |
| 4 | Dilby | Soul Vision (Original Mix) | 125 | 6.0 |
| 5 | Ric Niels & Juan Buitrago | Glide | 123 | 5.5 |
| 6 | Dowden, Mazayr | Deflator (Original Mix) | 121 | 5.0 |
| 7 | Danny Serrano | The Haven (Dilby Extended Remix) | 123 | 5.5 |
| 8 | Kit Lawson | Ruff (Original Mix) | 124 | 6.0 |
| 9 | Nox Vahn | Brainwasher (Warung Extended Mix) | 123 | 5.5 |
| 10 | Dosem | Chosen | 124 | 6.0 |
| 11 | Redspace, Diego Riga | Phantom Sun (Extended Mix) | 124 | 6.0 |
| 12 | Durante, Enamour | Taos Hum | 126 | 6.5 |


## Set 69. 69. Superficie — Sudbeat Argentino — 1h30 — 2026-08-09
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Paul Deep (AR) | Melodramatic (Original Mix) | 122 | 5.5 |
| 2 | Melodiam (AR) | Juno | 120 | 5.0 |
| 3 | Hernan Cattaneo & Soundexile | Deneb | 122 | 5.5 |
| 4 | Chicola, Guy Mantzur | Neon Bible (Original Mix) | 122 | 5.5 |
| 5 | Beckers, D-Nox | Skylab (Original Mix) | 122 | 5.5 |
| 6 | Julian Nates | A Better Place (Original Mix) | 124 | 6.0 |
| 7 | Gai Barone | Kromaky (Original Mix) | 123 | 5.5 |
| 8 | Antrim | Curved (Original Mix) | 123 | 5.5 |
| 9 | Roger Martinez | Cosmic Drum (Paul Deep Remix) | 123 | 5.5 |
| 10 | Cid Inc. | Citadel (Original Mix) | 123 | 5.5 |
| 11 | Marcelo Vasami | Shades Of Blue (Original Mix) | 122 | 5.5 |
| 12 | Melodiam | No Way Out | 122 | 5.5 |


## Set 70. 70. Superficie — Colorize Vocal — 1h30 — 2026-08-09
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Le Youth | About Us (Extended Mix) | 122 | 5.5 |
| 2 | GMJ, Matter, Zankee Gulati | Emerge (Original Mix) | 120 | 5.0 |
| 3 | Rockka | Rebit (Original Mix) | 122 | 5.5 |
| 4 | GRAZZE | Miami (Extended Mix) | 123 | 5.5 |
| 5 | Ruben Karapetyan | Neurotransmitter (Extended Mix) | 123 | 5.5 |
| 6 | Braxton | Torn (feat. Danni Wells) [Extended Mix] | 121 | 5.0 |
| 7 | Cary Crank | Inner Atlas (Kyotto Remix) | 122 | 5.5 |
| 8 | Rauschhaus | If I Had Wings | 121 | 5.0 |
| 9 | Hobin Rude | Shrouded Glint (Original Mix) | 122 | 5.5 |
| 10 | Bondarev, Max Wexem | The Lotus (Original Mix) | 123 | 5.5 |
| 11 | Orbital, Yotto | Belfast - Yotto Remix | 123 | 5.5 |
| 12 | Ursula Rucker, Simon Doty | Hometown feat. Ursula Rucker (Extended Mix) | 124 | 6.0 |


## Set 71. 71. Presion — Peak Groove — 1h30 — 2026-08-11
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 121-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Khen | Out Of A Dream (Original Mix) | 121 | 5.0 |
| 2 | D-Nox, Stereo Underground | Salt & Pepper (Original Mix) | 123 | 5.5 |
| 3 | Dilby | Sensei (Original Mix) | 124 | 6.0 |
| 4 | DJ Paul (AR), Andre Moret & Nahs | Spiritual Balance | 124 | 6.0 |
| 5 | Maze 28 | Cry of the Deserts (Molac & Nicolas Viana Remix) | 122 | 5.5 |
| 6 | Dmitry Molosh, Michael A | Integral (Original Mix) | 122 | 5.5 |
| 7 | Roy Rosenfeld | Hypnosa De La Rosa | 123 | 5.5 |
| 8 | Spencer Brown | Blue Magic (feat. Danny Shamoun) | 123 | 5.5 |
| 9 | Kamilo Sanclemente | Fragma (GORKIZ Remix) | 123 | 5.5 |
| 10 | Massano | The Feeling (2022 Remaster) | 124 | 6.0 |
| 11 | Tali Muss | Azal (Original Mix) | 123 | 5.5 |
| 12 | Durante & Altieri, James, Ron Carroll | I Like The Way (Ron Carroll Chicago Disko Mix) | 124 | 6.0 |


## Set 72. [POOL] Nuevos Agosto 2026 — Dilby / D-Nox / Moret / Durante
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 16  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Durante & Altieri, James, Ron Carroll | I Like The Way (Ron Carroll Chicago Disko Mix) | 124 | 6.0 |
| 2 | Dilby | Addicted | 124 | 6.0 |
| 3 | Hernan Cattaneo, Audio Junkies | A Major Minor (D-Nox & Beckers Remix) | 125 | 6.0 |
| 4 | Dilby | Sensei (Original Mix) | 124 | 6.0 |
| 5 | DJ Paul (AR), Andre Moret & Nahs | Spiritual Balance | 124 | 6.0 |
| 6 | Dilby | Last Word (Original Mix) | 124 | 6.0 |
| 7 | Danny Serrano | The Haven (Dilby Extended Remix) | 123 | 5.5 |
| 8 | Dilby | Soul Vision (Original Mix) | 125 | 6.0 |
| 9 | D-Nox, Stereo Underground | Salt & Pepper (Original Mix) | 123 | 5.5 |
| 10 | Dilby | Pranayama | 124 | 6.0 |
| 11 | Stereo Underground feat. Sealine | Flashes (D-Nox & Beckers Remix) | 123 | 5.5 |
| 12 | DJ Paul (AR), Andre Moret & Nahs | Experience | 124 | 6.0 |
| 13 | D-Nox | Full Moon (Original Mix) | 125 | 6.0 |
| 14 | Dilby | Connect the Dots (Oliver Schories & Gorge Remix) | 124 | 6.0 |
| 15 | Andre Moret | Young Movements | 120 | 5.0 |
| 16 | Dilby | Remember Me (Extended Mix) | 124 | 6.0 |


## Set 73. 73. Dilby & Co — Showcase Groove — 1h30 — 2026-08-12
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 121-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Dilby | Remember Me (Extended Mix) | 124 | 6.0 |
| 2 | Durante | Thread Tension | 122 | 5.5 |
| 3 | Jeremy Olander | Saigon | 123 | 5.5 |
| 4 | Sebastien Leger, Roy Rosenfeld | Panko Day (Extended Mix) | 121 | 5.0 |
| 5 | Cid Inc. | Abyss | 123 | 5.5 |
| 6 | Dilby | Connect the Dots (Oliver Schories & Gorge Remix) | 124 | 6.0 |
| 7 | DJ Paul (AR), Andre Moret & Nahs | Experience | 124 | 6.0 |
| 8 | Stereo Underground feat. Sealine | Flashes (D-Nox & Beckers Remix) | 123 | 5.5 |
| 9 | Hermanez, Lost Desert | Other Side (Original Mix) | 123 | 5.5 |
| 10 | Sahar Z & Guy Mantzur | Future Memories | 125 | 6.0 |
| 11 | Dilby | Pranayama | 124 | 6.0 |
| 12 | Hana, Durante | Starglow (Extended Mix) | 124 | 6.0 |


## Set 74. 74. Puerta — Apertura — 2h — 2026-08-13
**Armado:** 2026-09-12  
**Duracion:** 2.0h  
**Tracks:** 16  
**BPM range:** 117-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Estiva | What Is Love (Extended Mix)  | 124 | 3.6 |
| 2 | Nox Vahn | When I'm With You (Extended Mix)  | 123 | 4.1 |
| 3 | Ezequiel Arias, Sebastian Sellares | Alba (Extended Mix) | 124 | 6.0 |
| 4 | This Guy Ben | Corbiere (Extended Mix) | 124 | 6.0 |
| 5 | Kamilo Sanclemente, Andre Moret, Mariusso | Atenea (HAFT Remix) | 122 | 5.5 |
| 6 | Le Youth, Sultan + Shepard, Panama | New Love (Extended Mix) | 123 | 5.5 |
| 7 | PACS | Omnia (Original Mix) | 124 | 6.0 |
| 8 | Durante | Orca (Original Mix) | 124 | 6.0 |
| 9 | New Jackson | The Night Mail (Simon Vuarambon Remix) | 123 | 5.5 |
| 10 | Emi Galvan, NOIYSE PROJECT | Connection | 122 | 5.5 |
| 11 | Cendryma | Circles (Kebin van Reeken Remix) | 122 | 5.5 |
| 12 | Khen | April Storm | 122 | 5.5 |
| 13 | Lexer | Obscurity | 123 | 5.5 |
| 14 | Redspace | Not the Same Anymore (Original Mix) | 123 | 5.5 |
| 15 | Bigfett | Takatum (Original Mix) | 124 | 6.0 |
| 16 | Supermode | Tell Me Why (James Carter Extended Mix) | 124 | 6.0 |


## Set 75. 75. La Ultima Hora — Cierre Euforico — 1h15 — 2026-08-13
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 122-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Cary Crank | Inner Atlas (Kyotto Remix) | 122 | 5.5 |
| 2 | Greta Meier | Enlightenment (Gaston Sosa Remix) | 122 | 5.5 |
| 3 | Nick Warren | Freebird (Emi Galvan Remix) | 123 | 5.5 |
| 4 | Kamilo Sanclemente | Astronauts Nightmares (DJ Ruby Extended Remix) | 123 | 5.5 |
| 5 | Cendryma | Wakefeld (Original Mix) | 122 | 5.5 |
| 6 | Maze 28 | Leave the World Behind (Original Mix) | 122 | 5.5 |
| 7 | Jakatta | American Dream (PROFF Extended Interpretation) | 122 | 5.5 |
| 8 | NOIYSE PROJECT, Hernan Cattaneo, Jamie Stevens | Remember Me - Hernan Cattaneo & Jamie Stevens Remix | 122 | 5.5 |
| 9 | Blancah, NeoClassic | Travessia (Hicky & Kalo Remix) | 123 | 7.9 |
| 10 | Andy Moor & Adam White | The Whiteroom (feat. Whiteroom) [Marsh Extended Mix] | 125 | 6.0 |
| 11 | Mike Griego | Antidote | 123 | 7.9 |
| 12 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 5.5 |


## Set 76. [POOL] Detonantes — E>=7.5 — uno o dos por set, al 70-85%
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 24  
**BPM range:** 118-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Colyn | The Future Is the Past | 126 | 6.5 |
| 2 | Carlita & Calussa | Fell In Luv (Black Circle Extended Remix) | 126 | 6.5 |
| 3 | Ferry Corsten, Dirty South | Carte Blanche (Extended Mix) | 124 | 6.0 |
| 4 | Jamie Stevens, Zankee Gulati | Low Tide (Ezequiel Arias Remix) | 125 | 6.0 |
| 5 | D-Nox, Stereo Underground | Shooting Stars (Extended Version) | 125 | 6.0 |
| 6 | After Sunrise | Tequila Sunrise (Original Mix) | 128 | 6.5 |
| 7 | Ferry Corsten, Marsh | Attraction (Marsh's Extended Mix) | 126 | 6.5 |
| 8 | Fuscarini | Le Souffle (Kevin Di Serna & Santor Remix) | 127 | 6.5 |
| 9 | Graziano Raffa | Carbonia (Original Mix) | 125 | 6.0 |
| 10 | Rauschhaus | Galapagos (Original Mix) | 124 | 6.0 |
| 11 | Lost Desert | Black Panther (Original Mix) | 124 | 6.0 |
| 12 | Rockka | Cinimatic (Original Mix) | 123 | 5.5 |
| 13 | Artic White | Once We Were (Extended Mix) | 123 | 5.5 |
| 14 | CamelPhat, Jem Cooke, Cristoph | Breathe (Original Mix) | 125 | 6.0 |
| 15 | Gorje Hewek | Forest Song in the Night (Original Mix) | 123 | 5.5 |
| 16 | Lost Desert | Aalam Waahid (Original Mix) | 124 | 6.0 |
| 17 | Maze 28 | Great Attractor (Ruben Karapetyan Remix) | 124 | 6.0 |
| 18 | Andy Moor & Adam White | The Whiteroom (feat. Whiteroom) [Marsh Extended Mix] | 125 | 6.0 |
| 19 | Adriatique | Mystery (Tale Of Us & Mathame Remix) | 124 | 6.0 |
| 20 | Cid Inc., Dmitry Molosh | Impending Storm (Navar Remix) | 122 | 5.5 |
| 21 | Emi Galvan | Free Your Mind | 122 | 5.5 |
| 22 | ECHO DAFT, Kebin Van Reeken | Years of Ascent (Original Mix) | 122 | 5.5 |
| 23 | Ben Bohmer | Beyond Beliefs (Original Mix) | 124 | 6.0 |
| 24 | Mrak, Braev | The World Is Yours (Extended Mix) | 126 | 6.5 |


## Set 80. 80. Hernan Cattaneo Style — Progressive Argentino
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Ezequiel Arias | So Many Stars (Extended Mix) | 123 | 5.5 |
| 2 | Nicolas Rada | Glasgow (Original Mix) | 122 | 5.5 |
| 3 | Simply City, Juan Ibanez | Auralis (Original Mix) | 123 | 5.5 |
| 4 | Guy Mantzur | My Wild Flower (Original Mix) | 123 | 5.5 |
| 5 | Tom Pavicich, Gonzalo Cotroneo | Radiance (Original Mix) | 121 | 5.0 |
| 6 | Durante | Days Pass (Extended Mix) | 122 | 5.5 |
| 7 | Guy Mantzur | Requiem for Us | 122 | 5.5 |
| 8 | Ezequiel Arias | Púrpura | 122 | 5.5 |
| 9 | Simon Vuarambon | Diafana (Original Mix) | 121 | 5.0 |
| 10 | Kamilo Sanclemente | From The Sky (Original Mix) | 123 | 5.5 |
| 11 | Tonaco, Kebin Van Reeken | Chroma (Original Mix) | 121 | 5.0 |
| 12 | Emi Galvan & Albuquerque | Don't Kill the Messenger | 123 | 5.5 |
| 13 | Kamilo Sanclemente | Anagram (Original Mix) | 123 | 5.5 |
| 14 | Cary Crank | Inner Atlas (Kyotto Remix) | 122 | 5.5 |
| 15 | Dmitry Molosh | Glide | 121 | 5.0 |
| 16 | Chaum, Hobin Rude | Cressida (Tonaco Remix) | 122 | 5.5 |
| 17 | Armen Miran & Nicolas Rada | Fall Away (Original Mix) | 120 | 5.0 |
| 18 | Dowden | Night Emeralds (Original Mix) | 122 | 5.5 |


## Set 81. 81. Ezequiel Arias Style — Peak Vocal
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy J | My Existence (Original Mix) | 123 | 5.5 |
| 2 | Ezequiel Arias, FJL | Color Divino (Extended Mix) | 124 | 6.0 |
| 3 | D-Nox, Andre Moret | Six (Extended Mix) | 122 | 5.5 |
| 4 | Tom Pavicich | About Her (Original Mix) | 122 | 5.5 |
| 5 | Christopher Erre, Greta Meier | Giza (Original Mix) | 122 | 5.5 |
| 6 | Durante, Mayro | Mantra (Extended Mix) | 124 | 6.0 |
| 7 | Kamilo Sanclemente, Andre Moret | Spectre (Extended Mix) | 122 | 5.5 |
| 8 | Dowden & Ric Niels | Coil (John Cosani Remix) | 122 | 5.5 |
| 9 | Rolasoul, Greta Meier | Reflections (Extended Version) | 124 | 6.0 |
| 10 | Tom Pavicich | Josefina (Casnik Remix) | 123 | 5.5 |
| 11 | Lane 8, Sultan + Shepard | The Little Mushroom That Got Away (Extended Mix) | 122 | 5.5 |
| 12 | Ezequiel Arias | Perfect Dream (Extended Mix) | 124 | 6.0 |
| 13 | Cendryma | Focus Bend (Extended Mix) | 122 | 5.5 |
| 14 | D-Nox, Baya, LENN V | Silence (Extended Mix) | 124 | 6.0 |
| 15 | Maze 28 | Great Attractor (Ruben Karapetyan Remix) | 124 | 6.0 |
| 16 | Gorkiz, Luca Abayan | Drowner (Extended Mix) | 122 | 5.5 |
| 17 | Kamilo Sanclemente, Mauro Aguirre | Looking For You (Extended Mix) | 123 | 5.5 |
| 18 | Dmitry Molosh, Michael A | Integral (Original Mix) | 122 | 5.5 |


## Set 82. 82. Emi Galvan Style — Progresivo Colorido
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy Mantzur | Homecoming (Original Mix) | 123 | 5.5 |
| 2 | Guy J | A Moment Of Clarity (Original Mix) | 123 | 4.4 |
| 3 | Kebin Van Reeken | Endurance (Original Mix) | 121 | 5.0 |
| 4 | Chicola, Guy Mantzur | Galactica (Original Mix) | 122 | 5.5 |
| 5 | Kamilo Sanclemente, Andre Moret, Mariusso | Atenea (HAFT Remix) | 122 | 5.5 |
| 6 | Emi Galvan | Alfa Zeta (Original Mix) | 120 | 5.0 |
| 7 | Kasper Koman | Loco Motif (Tantum Remix) | 121 | 5.0 |
| 8 | Cendryma | Dividing Parts (Original Mix) | 121 | 5.0 |
| 9 | Emi Galvan | Mily (Original Mix) | 122 | 5.5 |
| 10 | Quivver, Dave Seaman | The Water's Edge (Original Mix) | 122 | 5.5 |
| 11 | Ezequiel Arias | Mad Man - Original Mix | 123 | 6.4 |
| 12 | Cendryma | Opulence (Original Mix) | 122 | 5.5 |
| 13 | Paul Deep (AR) | Tique (Original Mix) | 123 | 5.5 |
| 14 | Kamilo Sanclemente | Horizons (Original Mix) | 121 | 5.0 |
| 15 | Cid Inc. | Citadel (Original Mix) | 123 | 5.5 |
| 16 | Melodiam | No Way Out | 122 | 5.5 |
| 17 | Nicolas Rada | The Wind Phone | 123 | 5.5 |
| 18 | Dowden | Feather (Original Mix) | 122 | 5.5 |


## Set 83. 83. Kamilo Sanclemente Style — Colombia Progresiva
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Nicolas Rada | El Oro De Los Tigres | 122 | 5.5 |
| 2 | Guy J | Alive Again (Original Mix) | 122 | 4.5 |
| 3 | Rauschhaus, Cary Crank | Tapestry of Perception (Extended Mix) | 120 | 5.0 |
| 4 | Paul Deep (AR) | Melodramatic (Original Mix) | 122 | 5.5 |
| 5 | Kamilo Sanclemente | Jupiter Code (Original Mix) | 123 | 5.5 |
| 6 | Andre Moret | Beyond Us (Extended Mix) | 122 | 5.5 |
| 7 | Chicola, Guy Mantzur | Neon Bible (Original Mix) | 122 | 5.5 |
| 8 | Rauschhaus | Mindworm (Ruben Karapetyan Remix) | 123 | 5.5 |
| 9 | Kamilo Sanclemente | Canon (Original Mix) | 123 | 5.5 |
| 10 | Emi Galvan | Crabo (Original Mix) | 122 | 5.5 |
| 11 | Leandro Murua, Martin Fredes | Interference (Original Mix) | 122 | 5.5 |
| 12 | Gai Barone | Shuttered (Original Mix) | 122 | 5.5 |
| 13 | Roy Rosenfeld | The Biggest Heart | 123 | 5.5 |
| 14 | Tom Pavicich | Insight (Original Mix) | 122 | 5.5 |
| 15 | Kabi (AR), Ric Niels | Kimica | 122 | 5.5 |
| 16 | Maze 28 | Aer8 (Juan Pablo Torrez Remix) | 122 | 5.5 |
| 17 | Antrim | Curved (Original Mix) | 123 | 5.5 |
| 18 | Jamie Stevens, Kasey Taylor | Verlaine (Original Mix) | 122 | 5.5 |


## Set 84. 84. Sudbeat Sessions — Driving Progressive
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Ezequiel Arias | Delirio (Extended Mix) | 125 | 4.2 |
| 2 | Simon Vuarambon | Mars (Original Mix) | 123 | 5.5 |
| 3 | Durante | Orca (Original Mix) | 124 | 6.0 |
| 4 | Khen | April Storm | 122 | 5.5 |
| 5 | Melodiam (AR) | Jupiter (Extended Mix) | 121 | 5.0 |
| 6 | Andre Moret | Generator (Extended Mix) | 121 | 5.5 |
| 7 | Cid Inc., Dmitry Molosh | Aquamarine (Original Mix) | 122 | 5.5 |
| 8 | Kamilo Sanclemente | Whale Voices (Original Mix) | 122 | 5.5 |
| 9 | Cendryma | Possible Interlude (Extended Mix) | 121 | 6.3 |
| 10 | Nick Warren, Martin Fredes | Wanderlust (Original Mix) | 123 | 5.5 |
| 11 | Maze 28 | Cry of the Deserts (Aman Anand Remix) | 121 | 5.0 |
| 12 | Greta Meier | Enlightenment (Gaston Sosa Remix) | 122 | 5.5 |
| 13 | Nick Warren | Freebird (Emi Galvan Remix) | 123 | 5.5 |
| 14 | Cendryma | Evasive (Extended Mix) | 121 | 5.0 |
| 15 | Kamilo Sanclemente | Delusion (Original Mix) | 122 | 5.5 |
| 16 | Marcelo Vasami | Shades Of Blue (Original Mix) | 122 | 5.5 |
| 17 | Dmitry Molosh | The Moon Lights the Way (Original Mix) | 122 | 5.5 |
| 18 | Cid Inc. | Forgotten | 123 | 5.5 |


## Set 85. 85. Mango Alley — Deep Progressive
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy Mantzur, Kamila, Khen | Children With No Name Feat. Kamila (Original Mix) | 120 | 5.0 |
| 2 | Sebastian Sellares, Greta Meier | Benevolence (Paul Thomas Extended Remix) | 122 | 5.5 |
| 3 | Emi Galvan | Dopamine (Forniva Remix) | 123 | 5.5 |
| 4 | Hernan Cattaneo & Soundexile | Pick Up | 122 | 5.5 |
| 5 | Mike Rish | Dope Riddim (Original Mix) | 122 | 5.5 |
| 6 | Hobin Rude | Opposite (Original Mix) | 122 | 5.5 |
| 7 | Jamie Stevens, Kasey Taylor | Hocu Pocu (Original Mix) | 123 | 5.5 |
| 8 | Kamilo Sanclemente | Theia | 122 | 5.5 |
| 9 | Dimas Mixon, Cendryma | Minicube (Original Mix) | 120 | 5.0 |
| 10 | Maze 28 | Cry of the Deserts (Molac & Nicolas Viana Remix) | 122 | 5.5 |
| 11 | Tom Pavicich | About Her (Martin Fredes Remix) | 122 | 5.5 |
| 12 | Rauschhaus, GRAZZE | Canacona (Original Mix) | 121 | 5.0 |
| 13 | Guy J | Placebo (Original Mix) | 122 | 5.5 |
| 14 | Rockka | Operator (Maze 28 Remix) | 122 | 5.5 |
| 15 | Kamilo Sanclemente | Astronauts Nightmares (DJ Ruby Extended Remix) | 123 | 5.5 |
| 16 | Hernan Cattaneo & Soundexile | Astron (Davi Remix) | 122 | 5.5 |
| 17 | Cendryma, THMS (US) | Moonflare (Extended Mix) | 121 | 5.0 |
| 18 | D-Nox, Andre Moret | Brisa (Extended Mix) | 123 | 5.5 |


## Set 86. 86. Simon Vuarambon Style — Hipnotico
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hraach, Armen Miran | Sarer Jan feat. Iveta Mukuchyan (Original Mix) | 122 | 5.5 |
| 2 | Hernan Cattaneo & Soundexile | Wind Down (Outro Mix) | 122 | 5.5 |
| 3 | Michael A | Hunting Flowers (Radio Edit) | 120 | 5.0 |
| 4 | Maze 28, Rockka | Corrosive | 122 | 5.5 |
| 5 | Mike Rish | Election Day (Original Mix) | 122 | 5.5 |
| 6 | Hraach | Cosmic Drama (Original Mix) | 120 | 5.0 |
| 7 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 5.0 |
| 8 | Cendryma | Buildup Trap (Simos Tagias Remix) | 121 | 5.0 |
| 9 | Tom Pavicich | You (Original Mix) | 123 | 5.5 |
| 10 | Melodiam (AR) | Molicocha (Extended Mix) | 123 | 5.5 |
| 11 | Kamilo Sanclemente | Distant Blips (Dowden Remix) | 122 | 5.5 |
| 12 | Hobin Rude | Nothing's Gonna Hurt You | 122 | 5.5 |
| 13 | Emi Galvan | Trust (Original Mix) | 122 | 5.5 |
| 14 | Kebin Van Reeken | Muse (Original Mix) | 120 | 5.0 |
| 15 | Cendryma | Override (Original Mix) | 122 | 5.5 |
| 16 | Gai Barone, Cary Crank | You Are Becoming (Extended Mix) | 122 | 5.5 |
| 17 | Ezequiel Arias | Heat Above - Original Mix | 124 | 6.0 |
| 18 | Melodiam (AR) | Dizzy (Extended Mix) | 122 | 5.5 |


## Set 87. 87. Nick Warren Style — The Soundgarden
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Ezequiel Arias, Sebastian Sellares | Alba (Extended Mix) | 124 | 6.0 |
| 2 | Emi Galvan | I Wish (Original Mix) | 123 | 5.5 |
| 3 | Leandro Murua, Martin Fredes | Mistakes (Original Mix) | 122 | 5.5 |
| 4 | Rockka | Rebit (Original Mix) | 122 | 5.5 |
| 5 | Kamilo Sanclemente, Andre Moret | Mirage (Original Mix) | 122 | 5.5 |
| 6 | Martin Fredes, Unai Garcia | The Artefact (Original Mix) | 120 | 5.0 |
| 7 | Rockka, Maze 28 | Mirage (Juan Ibanez Extended Mix) | 122 | 5.5 |
| 8 | Cendryma | Pure Junction (Berdu Remix) | 120 | 5.0 |
| 9 | Guy J | Anonymous | 122 | 5.9 |
| 10 | Antrim, Kamilo Sanclemente, Paula OS | Once and Again (Bluum Extended Mix) | 120 | 5.0 |
| 11 | Simon Vuarambon | Lazos (Original Mix) | 120 | 5.0 |
| 12 | Greta Meier, Maze 28 | Acceptance (Original Mix) | 122 | 5.5 |
| 13 | Rauschhaus | If I Had Wings | 121 | 5.0 |
| 14 | Paul Deep AR | Milo | 123 | 7.1 |
| 15 | Guy J | Illusion (Original Mix) | 122 | 5.5 |
| 16 | Kasper Koman | Sinking Sky | 122 | 5.5 |
| 17 | Ric Niels | Osmio (Original Mix) | 120 | 5.0 |
| 18 | Cendryma | Bending Speed (Rabiee Ahmad Remix) | 122 | 5.5 |


## Set 88. 88. Cordoba Progressive — Gai Barone Style
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Durante, Ezequiel Arias | Logical (Extended Mix) | 125 | 6.0 |
| 2 | Kasey Taylor, Karl Pilbrow | Mount Epicon (Original Mix) | 125 | 6.0 |
| 3 | Anthony Pappa, Aubrey Fry | Itajai (Original Mix) | 125 | 6.0 |
| 4 | Guy Mantzur, Khen | Where Is Home (Matthias Meyer Remix) | 124 | 6.0 |
| 5 | Julian Nates | A Better Place (Original Mix) | 124 | 6.0 |
| 6 | Hobin Rude | Last Glimpse | 123 | 5.5 |
| 7 | Gai Barone | In the Blink of an Eye (Original Mix) | 122 | 5.5 |
| 8 | Antrim | Rescue | 122 | 5.5 |
| 9 | Michael A | Zero Dawn (Kebin Van Reeken Remix) | 121 | 5.0 |
| 10 | Melodiam (AR) | Repro Days (Original Mix) | 122 | 5.5 |
| 11 | Kamilo Sanclemente | Show Me the Stars (Original Mix) | 121 | 5.0 |
| 12 | Guy J | Surreal (Original Mix) | 121 | 5.0 |
| 13 | Emi Galvan | Samsara | 122 | 5.5 |
| 14 | Paul Deep (AR) | Aeras (Original Mix) | 121 | 5.0 |
| 15 | Ruben Karapetyan | Nostalgic Moments (Original Mix) | 121 | 5.0 |
| 16 | Kostya Outta | Seguro (Paul James Nolan Remix) | 122 | 5.5 |
| 17 | Kamilo Sanclemente | Just Come Back (Extended Mix) | 124 | 6.0 |
| 18 | Guy Mantzur, Tamir Regev | Mystica (Original Mix) | 122 | 5.5 |


## Set 89. 89. Argentina Peak Time
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 121-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Facundo Borras | Whispers from Dawn | 123 | 5.5 |
| 2 | Stephan Bodzin, Jem Cooke, Massano | Healing (Extended Mix) | 124 | 6.0 |
| 3 | Graziano Raffa | Sturm Und Drang (Original Mix) | 126 | 6.5 |
| 4 | Kit Lawson | Ruff (Original Mix) | 124 | 6.0 |
| 5 | Durante, Amtrac | Gather (Original Mix) | 122 | 5.5 |
| 6 | Kamilo Sanclemente, Phillipe Lois | Acid Dreams (Original Mix) | 124 | 6.0 |
| 7 | ALPHA21, Cendryma | Resonance (Extended Mix) | 122 | 6.5 |
| 8 | Madloch & Antti Rasi | Salty Roads (Cid Inc Remix) | 123 | 5.5 |
| 9 | Will DeKeizer, Maze 28 | Cornerstone (Kostya Outta & Alisha Remix) | 121 | 7.0 |
| 10 | Massano | Function | 122 | 5.5 |
| 11 | Ric Niels | Invasion | 123 | 5.5 |
| 12 | Greta Meier | Enlightenment (Poli Siufi Remix) | 122 | 5.5 |
| 13 | Cary Crank | Deep Forest (Extended Mix) | 122 | 5.5 |
| 14 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 5.5 |
| 15 | NOIYSE PROJECT, Hernan Cattaneo, Jamie Stevens | Remember Me - Hernan Cattaneo & Jamie Stevens Remix | 122 | 5.5 |
| 16 | Maze 28 | Leave the World Behind (Original Mix) | 122 | 5.5 |
| 17 | Cendryma | Wakefeld (Original Mix) | 122 | 5.5 |
| 18 | D-Nox, Andre Moret | Shine (Extended Mix) | 124 | 6.0 |


## Set 96. 96. Luminoso — 1h20 — 2026-09-07
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Durante, Ezequiel Arias | Logical (Extended Mix) | 125 | 6.0 |
| 2 | Monolink | Laura (ARGY & Omnya Remix) | 125 | 6.0 |
| 3 | Dosem | Not Leaving | 124 | 6.0 |
| 4 | Mariano Mellino with FOLGAR & Gio Santi | Never Enough (Original Mix) | 122 | 5.2 |
| 5 | Khen | Ango (Club Mix) | 123 | 5.5 |
| 6 | Marsh | Calling (Extended Mix) | 124 | 6.0 |
| 7 | Dosem | What If (Extended Mix) | 124 | 6.0 |
| 8 | Guy Mantzur, Khen | Where Is Home (Matthias Meyer Remix) | 124 | 6.0 |
| 9 | Durante | Maia | 124 | 6.0 |
| 10 | Mike Rish | Leaving Brixton (Extended Mix) | 122 | 5.5 |
| 11 | Emi Galvan & Albuquerque | Stay High | 122 | 5.5 |
| 12 | Tinlicker | Blackbirds (Extended Mix) | 123 | 5.5 |
| 13 | Lost Desert, Reigan, Amand | Open Form feat. Reigan (Original Mix) | 123 | 5.5 |
| 14 | Monolink | Otherside (Fideles Remix) | 123 | 5.5 |
| 15 | YOTTO | Aero (Original Mix) | 125 | 7.5 |
| 16 | Marsh | Warrior (Extended Mix) | 126 | 6.9 |
| 17 | D-Nox, Emi Galvan | Dualidad (Guy Mantzur Edit) | 124 | 6.0 |
| 18 | Ric Niels | Desire (Original Mix)  | 122 | 5.5 |


## Set 95. 95. Terraza Atardecer — 3h — 2026-09-07
**Armado:** 2026-09-12  
**Duracion:** 3h  
**Tracks:** 46  
**BPM range:** 105-121  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | El Buho | Anglo-Colombian Expedition (Sun Sone Detour) | 112 | 2.5 |
| 2 | Sabo, Tooker | Quieres Sol (Original Mix) | 111 | 2.5 |
| 3 | Kermesse, Pedro Perelman, Yuvi Gerstein | Pinto (Original Mix) | 112 | 2.5 |
| 4 | Chris Zippel & Bahramji | Sands (Original Instrumental Mix) | 113 | 2.5 |
| 5 | Rodrigo Gallardo, Claudio Arditti, Cafe De Anatolia | Yin Yang (Original Mix) | 114 | 2.5 |
| 6 | Betelgeize | Luz Clara (Kermesse Remix) | 116 | 2.5 |
| 7 | Mike Rish | Wait for Me (Original Mix) | 118 | 3.5 |
| 8 | Jamie Stevens, Guy J | Tassolem (Don't Worry 'bout Me) (Guy J Remix) | 120 | 5.0 |
| 9 | Cubicolor | Got This Feeling (Original Mix) | 118 | 3.5 |
| 10 | Mike Rish | Patenz (Original Mix) | 120 | 5.0 |
| 11 | Sao Paulo Deep | Fragmented Scene (Original Mix) | 120 | 5.0 |
| 12 | Santi & Tuğçe | Nana (Rodrigo Gallardo Remix) | 118 | 3.5 |
| 13 | Durante | Remedy (Mixed) | 120 | 5.0 |
| 14 | Nandu, Radeckt, Tripolism | Dope Dance (Extended Mix) | 120 | 5.0 |
| 15 | Gorje Hewek, Izhevski, Lost Desert | Yurta (Original Mix) | 119 | 3.5 |
| 16 | Solomun | The Way Back (Original Mix) | 120 | 5.0 |
| 17 | Goldcap, Budajevo, Munaylayt | East Route (Ohxala Remix) | 118 | 3.5 |
| 18 | GMJ | Silver Sky (Original Mix) | 120 | 5.0 |
| 19 | Tali Muss | Zafer (Original Mix) | 120 | 5.0 |
| 20 | DAVI | Deepest Mind | 119 | 3.5 |
| 21 | Boys Noize, &ME, Rampa, Adam Port, Keinemusik, Vinson | Crazy For It (feat. Vinson) | 120 | 5.0 |
| 22 | Kiasmos | Bound (Original Mix) | 121 | 5.0 |
| 23 | Michael A | Look Closer (Original Mix) | 121 | 5.0 |
| 24 | Dowden, Ciro Riveiro | Northern (Original Mix) | 120 | 5.0 |
| 25 | Seyah | Dope (Maze 28 & Kyotto Remix) | 121 | 5.0 |
| 26 | Brann (AR) | Evolution (Hobin Rude Extended Remix) | 121 | 5.0 |
| 27 | Nandu | Your Heart Stole My Life (Original Mix) | 121 | 5.0 |
| 28 | Jody Wisternoff, James Grant | Dapple (Extended Mix) | 120 | 5.0 |
| 29 | Izhevski, Talemates | AfrikaBurn (Extended Mix) | 121 | 5.0 |
| 30 | Guy Mantzur | Moongazer | 120 | 5.0 |
| 31 | Kebin Van Reeken | Enjoy the Present (Original Mix) | 120 | 5.0 |
| 32 | Sound Quelle | Fofan (Extended Mix) | 120 | 5.0 |
| 33 | Juliane Wolf, Callecat | Journey of Species (Mashk Remix) | 120 | 5.0 |
| 34 | Max Cooper, Rob Clouth | Candeleda (Original Mix) | 120 | 5.0 |
| 35 | Fideksen | Unbreakable Promise (Hobin Rude Remix) | 121 | 5.0 |
| 36 | Anton Make | Warppiness (Original Mix) | 121 | 5.0 |
| 37 | Nick Warren, Martin Fredes | Kairos (Original Mix) | 120 | 5.0 |
| 38 | Namito, Robbie Akbal | Feraq (Armen Miran Remix) | 119 | 3.5 |
| 39 | CHIRUKA | Ashes Don't Fade (Anton Make Remix) | 121 | 5.0 |
| 40 | Shayan Pasha, Redspace | Pantheon (Original Mix) | 121 | 5.0 |
| 41 | Adriatique, Delhia De France, Marino Canal | Home (Original Mix) | 120 | 5.0 |
| 42 | DAVI | The Bay 6 (Pt.2) | 121 | 5.0 |
| 43 | ODAX | Soundexile (Original Mix) | 121 | 5.0 |
| 44 | Messier | Kevlar (Hernan Cattaneo, Marcelo Vasami Remix) | 120 | 5.0 |
| 45 | Fabri Lopez & Callecat | Mutual Horizons (Original Mix) | 121 | 5.0 |
| 46 | Hot Oasis | Farfasha feat. Bahramji (Sabo & Sarkis Mikael Remix) | 120 | 5.0 |


## Set 97. 97. After Hipnotico — 1h — 2026-09-10
**Armado:** 2026-09-12  
**Duracion:** 1.0h  
**Tracks:** 12  
**BPM range:** 121-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Blake.08 | The Change Of Love (Extended Mix) | 126 | 6.5 |
| 2 | Hernan Cattaneo, Audio Junkies | A Major Minor (D-Nox & Beckers Remix) | 125 | 6.0 |
| 3 | Kit Lawson | Ruff (Original Mix) | 124 | 6.0 |
| 4 | Budakid | Hearts (Argia Remix) | 123 | 5.8 |
| 5 | Habitatt | Fly With Me (Extended Mix) | 122 | 5.5 |
| 6 | Colyn, Read the News | See the Light (Original Mix) | 123 | 6.1 |
| 7 | Boxer, Jody Wisternoff & James Grant | Sun Kissed (Extended Mix) | 124 | 6.0 |
| 8 | Che Jose | THE VOID (Extended) | 124 | 6.0 |
| 9 | Tinlicker, Ben Böhmer | Voodoo (Extended Mix) | 124 | 6.0 |
| 10 | David Guetta, MORTEN | The Future is Now | 125 | 6.0 |
| 11 | Monolink | Return to Oz (Artbat Remix) | 124 | 6.0 |
| 12 | Sasha | Singularity (Fur Coat Remix) | 125 | 6.0 |


## Set 98. 98. After Oscuro — 1h — 2026-09-10
**Armado:** 2026-09-12  
**Duracion:** 1.0h  
**Tracks:** 12  
**BPM range:** 123-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Coeus | Paramount (Original Mix) | 126 | 6.5 |
| 2 | Rodriguez Jr. | Off Gerlach (Original Mix) | 125 | 6.0 |
| 3 | Sahar Z & Guy Mantzur | Survivors Guilt | 125 | 6.0 |
| 4 | ANMA | Adya | 124 | 6.0 |
| 5 | Adam Ten, Mita Gami | High On | 123 | 5.5 |
| 6 | Jonas Saalbach, Luna Semara | Midnight Sky (Carlo Whale Remix) | 123 | 5.5 |
| 7 | R.Hz | Gleam (Giuliano Rodrigues Rmx) | 123 | 5.5 |
| 8 | Mauro Picotto, CRW, Kamilo Sanclemente | I Feel Love (Extended Mix) | 123 | 5.5 |
| 9 | Nick Warren | Freebird (Emi Galvan Remix) | 123 | 5.5 |
| 10 | Marsh | Free (Extended Mix) | 124 | 6.0 |
| 11 | Jan Blomqvist, Mahri | Deeper Grounds feat. Mahri (Extended Mix) | 124 | 6.0 |
| 12 | InfeXus & ANZA | Africa (Extended Mix) | 124 | 6.0 |


## Set 99. 99. After Luminoso — 1h — 2026-09-10
**Armado:** 2026-09-12  
**Duracion:** 1.0h  
**Tracks:** 12  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Adriatique | Ray | 123 | 5.5 |
| 2 | Lane 8 | Keep On (Extended Mix) | 122 | 5.5 |
| 3 | Enamour, Nox Vahn | Sleep Paralysis (Extended Mix) | 121 | 5.0 |
| 4 | Hraach | Promises (Original Mix) | 121 | 5.0 |
| 5 | Kasper Koman | The Blind Navigator (Extended Mix) | 122 | 5.5 |
| 6 | Gorkiz, K Loveski | Echos Of Eons (Greenage Remix) | 122 | 5.5 |
| 7 | Bedrock | Heaven Scent (Eagles & Butterflies Remix) | 123 | 5.5 |
| 8 | Dubfire & Oliver Huntemann | Terra (Joseph Capriati Remix) | 124 | 6.1 |
| 9 | Andrew Bayer | Immortal Lover (8kays Extended Mix) | 125 | 6.0 |
| 10 | Teho | Ashes (Original Mix) | 125 | 6.0 |
| 11 | Korolova & Monophase (IT) | Reactive (Extended Mix) | 125 | 6.0 |
| 12 | Innēr Sense (ofc) | Older (Extended Mix) | 125 | 6.0 |


## Set 100. 100. Con el material de Ezequiel Arias - Metropolitano Rosario - 2026-06-27
**Armado:** 2026-09-12  
**Duracion:** 1.2h  
**Tracks:** 13  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Christian Smith | Illusion (Ezequiel Arias Remix) | 125 | 6.0 |
| 2 | TPS | Control (Kostya Outta Remix) | 123 | 5.4 |
| 3 | Andre Moret | Kryon (Original Mix) | 123 | 5.5 |
| 4 | Drunken Kong, D-SHIFT | Where You Need To Be (Original Mix) | 121 | 5.6 |
| 5 | Cendryma | Parabolic (Original Mix) | 122 | 5.5 |
| 6 | Durante, Mayro | Mantra (Extended Mix) | 124 | 6.0 |
| 7 | Kamilo Sanclemente | Distant Blips (Dowden Remix) | 122 | 5.5 |
| 8 | Armen Miran & Nicolas Rada | Fall Away (Original Mix) | 120 | 5.0 |
| 9 | Rodrigo Pochelu, Cristian Hidalgo | Entrophee (Original Mix) | 122 | 7.0 |
| 10 | Rauschhaus | Waiting For The Birds | 123 | 5.5 |
| 11 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 5.5 |
| 12 | Gorkiz, Luca Abayan | Drowner (Extended Mix) | 122 | 5.5 |
| 13 | Chelakhov | Insomnia (Original Mix) | 122 | 5.5 |


## Set 101. 101. Con el material de Ezequiel Arias - Metropolitano Rosario - 2025-06-28
**Armado:** 2026-09-12  
**Duracion:** 1.8h  
**Tracks:** 20  
**BPM range:** 122-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Kamilo Sanclemente | Anagram (Mayro Extended Remix) | 123 | 5.5 |
| 2 | Claudio Cornejo (AR) | Alnitak (Original Mix) | 122 | 4.7 |
| 3 | Santi Mossman | Exitz (Original Mix) | 123 | 6.0 |
| 4 | Blake Jarrell | Twenty Miami's Ago (Cendryma Extended Mix) | 122 | 5.5 |
| 5 | FJL | Rider (Original Mix) | 124 | 5.3 |
| 6 | Luis Damora | Illuminate (Original Mix) | 123 | 6.1 |
| 7 | Supacooks, Bondarev | Activator (Original Mix) | 123 | 5.5 |
| 8 | Guy J | Silver Lake (Original Mix) | 122 | 5.5 |
| 9 | Gai Barone | Fractals (HAFT Extended Remix) | 122 | 5.5 |
| 10 | Lonya | Sadness (Ziger Remix) | 122 | 6.2 |
| 11 | Tiefstone, Das Pharaoh | Endless Summer (Extended Mix) | 122 | 5.5 |
| 12 | Antrim | Morning Changes (Original Mix) | 123 | 5.4 |
| 13 | Anton Borin (RU) | May Spring Come (Original Mix) | 123 | 5.5 |
| 14 | Ezequiel Arias | ReAnimation (Extended Mix) | 125 | 5.7 |
| 15 | Kyotto | Sorry I'm Late (HAFT Remix) | 123 | 5.5 |
| 16 | Antrim | Curved (Original Mix) | 123 | 5.5 |
| 17 | Tali Muss | Azal (Original Mix) | 123 | 5.5 |
| 18 | Niko Ava | Freedom (Original Mix) | 122 | 7.3 |
| 19 | Cid Inc. | Forgotten | 123 | 5.5 |
| 20 | Paul Arcane | Vortice (Extended Mix) | 123 | 5.5 |


## Set 102. 102. Con el material de Ezequiel Arias - Dahaus x Fruta Cordoba - 2026-04-12
**Armado:** 2026-09-12  
**Duracion:** 1.8h  
**Tracks:** 20  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Nox Vahn | When I'm With You (Extended Mix)  | 123 | 4.1 |
| 2 | Montw | Lost on the Road (Arnas D Remix) | 121 | 5.0 |
| 3 | Simos Tagias | Plexus | 122 | 5.1 |
| 4 | Paul (AR) & EANP | Insane (Lexicon Avenue Remix) | 122 | 5.1 |
| 5 | Dabeat | Etna (Ivan Aliaga Remix) | 121 | 5.7 |
| 6 | Hobin Rude | Dusk Petals (Original Mix) | 121 | 5.0 |
| 7 | Simos Tagias | Reality | 122 | 5.8 |
| 8 | Martin Fredes & GEØVHÄN | Deep Story (Ruben Karapetyan Remix) | 123 | 7.1 |
| 9 | Cid Inc. | Forgotten | 123 | 5.5 |
| 10 | Andrew Bayer | Immortal Lover (8kays Extended Mix) | 125 | 6.0 |
| 11 | Emi Galvan & Albuquerque | Don't Kill the Messenger | 123 | 5.5 |
| 12 | Estiva & Julia Church | On the Line | 124 | 6.9 |
| 13 | JESSIN | Babylon (North Echo Remix) | 125 | 6.5 |
| 14 | Eric Lune & Juan Sapia | Tension Release (Original Mix)  | 123 | 6.9 |
| 15 | Rodriguez Jr. & Liset Alea | What Is Real (Deep in the Playa Mix) | 123 | 5.5 |
| 16 | Maze 28 | Aer8 (Juan Pablo Torrez Remix) | 122 | 5.5 |
| 17 | Fran Garay | Illusion  | 120 | 7.0 |
| 18 | Tali Muss | Interlocutor (Kebin Van Reeken Extended Remix) | 122 | 5.5 |
| 19 | Sebastian Sellares | Abaddon (Extended Mix) | 121 | 5.0 |
| 20 | Kabi (AR) & Agustin Ficarra | The Return (Original Mix) | 123 | 5.7 |


## Set 103. 103. Con el material de Simon Vuarambon - Dahaus Palacio Alsina Cordoba - 2026-03-01
**Armado:** 2026-09-12  
**Duracion:** 1.8h  
**Tracks:** 20  
**BPM range:** 120-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Markus Homm & Nici Faerber | Basement Room (Dilby Remix) | 125 | 5.2 |
| 2 | DAVI | Self ASCND (Original Mix)  | 124 | 5.8 |
| 3 | Rockka, Maze 28 | Mirage (Juan Ibanez Extended Mix) | 122 | 5.5 |
| 4 | Neuralis | Ethereum (Original Mix) | 120 | 5.0 |
| 5 | Tantum, Hyunji-A | Keep My Letters (Simon Vuarambon Remix) | 122 | 5.5 |
| 6 | Tobi Amuchastegui | Night Loop (Original Mix) | 121 | 6.2 |
| 7 | Agustin Pengov | Trumpert (Original Mix) | 120 | 6.1 |
| 8 | Aman Anand | Disastro (Thomas Ferell Remix) | 120 | 6.8 |
| 9 | Dr. Mirzoyan | Destruction (Ruben Karapetyan Remix) | 122 | 7.0 |
| 10 | Juan Buitrago | Anja | 121 | 6.9 |
| 11 | Mind Echoes | Unsafe Numbers (Tonaco & Tomas Garcia Remix) | 123 | 6.7 |
| 12 | Doki | Luminus (Cedren & Manu-l Remix) | 123 | 6.6 |
| 13 | Brian Cid | Habitat | 121 | 5.0 |
| 14 | Tobi Amuchastegui | You Are Not Alone (Original Mix) | 121 | 6.4 |
| 15 | Taylan | Earthbound (Andre Moret Remix) | 120 | 5.0 |
| 16 | Ciro Riveiro | Asia | 121 | 7.1 |
| 17 | Jody Wisternoff | Paramour (Original Mix) | 123 | 5.5 |
| 18 | Cristoph | Signal (Original Mix) | 125 | 6.0 |
| 19 | Jel Ford | Overcast (Original Mix) | 126 | 6.0 |
| 20 | N'to | Trauma (Worakls Remix) | 128 | 6.5 |


## Set 104. 104. Previa Mellino — 1h30 — 2026-09-12
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 18  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Maze 28, Rockka | Corrosive | 122 | 5.5 |
| 2 | Ezequiel Arias | Sin Control (Extended Mix) | 124 | 6.0 |
| 3 | Iovino, Tom Pavicich | Seamless (Original Mix) | 123 | 5.5 |
| 4 | Mayro | Chimi (Original Mix) | 122 | 5.5 |
| 5 | Dmitry Molosh | Carousel (Original Mix) | 123 | 5.5 |
| 6 | Dowden | Pacifist (Original Mix) | 121 | 5.0 |
| 7 | D-Nox, Andre Moret | Cosmic (Extended Mix) | 121 | 5.0 |
| 8 | Khen | Some Little Secrets | 122 | 5.5 |
| 9 | Hobin Rude | Prism (Original Mix) | 121 | 5.0 |
| 10 | NUFECTS | Inferno (Extended Mix) | 123 | 5.5 |
| 11 | Cendryma | Bending Speed (Rabiee Ahmad Remix) | 122 | 5.5 |
| 12 | GMJ, Matter | Telomeres (Original Mix) | 121 | 5.0 |
| 13 | Gai Barone | Shuttered (Original Mix) | 122 | 5.5 |
| 14 | Sebastian Sellares | Abaddon (Extended Mix) | 121 | 5.0 |
| 15 | Fideles, Be No Rain | See You In Dreams (Original Mix) | 123 | 5.5 |
| 16 | Tali Muss | Garip (Original Mix) | 122 | 5.5 |
| 17 | Emi Galvan | Vibration (Original Mix) | 122 | 5.5 |
| 18 | Kostya Outta, Liam Garcia | If I Win (Extended Mix) | 123 | 5.5 |


## Set 105. 105. After Mellino — 1h30 — 2026-09-12
**Armado:** 2026-09-12  
**Duracion:** 1.5h  
**Tracks:** 18  
**BPM range:** 122-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Greg Ochman | Blinking Stars (Luka Sambe Remix) | 123 | 5.5 |
| 2 | Nicolas Viana | Fog Machine (Extended Mix) | 124 | 6.0 |
| 3 | WELKER (BR) | Batucada (Original Mix) | 124 | 6.0 |
| 4 | Anyma, Rebūke | Syren | 125 | 6.0 |
| 5 | Reflekt, Delline Bass | Need To Feel Loved (Cristoph Remix) | 125 | 6.0 |
| 6 | Budakid | The Curse | 124 | 6.0 |
| 7 | Gorje Hewek, Moya (US) & Dulus | Margaret (Extended Mix) | 122 | 5.5 |
| 8 | Nox Vahn | Brainwasher (Warung Extended Mix) | 123 | 5.5 |
| 9 | Fluke | Bullet (Nick Warren & Nicolas Rada Remix) | 125 | 6.0 |
| 10 | Artic White | Linea Zero (Extended Mix) | 123 | 5.5 |
| 11 | Serious Dancers | Echo (Kebin van Reeken Extended Remix) | 122 | 5.5 |
| 12 | K3V (SL) & Jayy Vibes | Kingdom of Dreams (Juan Ibanez Remix) | 122 | 5.5 |
| 13 | Blancah, NeoClassic | Travessia (Hicky & Kalo Remix) | 123 | 7.9 |
| 14 | Cary Crank | Deep Forest (Extended Mix) | 122 | 5.5 |
| 15 | Lost Desert | Aalam Waahid (Original Mix) | 124 | 6.0 |
| 16 | Sounom & Sagou | Everyday Moments (Kamilo Sanclemente Remix) | 122 | 5.5 |
| 17 | Sébastien Léger | Forbidden Garden (Tim Green Remix) | 122 | 5.5 |
| 18 | Kabi (AR), Ric Niels | Kimica | 122 | 5.5 |


## Set 47. 47. Colyn x Mind Against — Afterlife Dark — Viaje 2026
**Armado:** 2026-09-12  
**Duracion:** 2h  
**Tracks:** 18  
**BPM range:** 116-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Rodriguez Jr. | 1PM Sunrise | 124 | 6.0 |
| 2 | Hermanez | Eight Years (Original Mix) | 122 | 5.5 |
| 3 | Rodriguez Jr. | Nairobi (Original Mix) | 124 | 6.0 |
| 4 | Rodriguez Jr. | Twilight Language (Extended Version) | 123 | 5.5 |
| 5 | Lee Burridge, Lost Desert | Chicago Drive (Original Mix) | 121 | 5.0 |
| 6 | Nils Hoffmann, Julia Church | 9 Days (Extended Mix) | 120 | 5.0 |
| 7 | Lane 8 | Keep On (Extended Mix) | 122 | 5.5 |
| 8 | Adriatique | Ray | 123 | 5.5 |
| 9 | Hermanez | Gamma Ray | 123 | 5.5 |
| 10 | Bedouin | Flight of Birds | 120 | 5.0 |
| 11 | Monolink | Don't Hold Back | 120 | 5.0 |
| 12 | Hermanez | Areia (Original Mix) | 120 | 5.0 |
| 13 | N'to | Alter Ego | 123 | 5.5 |
| 14 | Lee Burridge, Lost Desert | Ash & Ember (Extended Mix) | 123 | 5.5 |
| 15 | Ben Böhmer | Blossoms | 123 | 5.5 |
| 16 | Ben Böhmer | Begin Again (Original Mix) | 121 | 5.0 |
| 17 | Lee Burridge, Lost Desert | In the Dark (Original Mix) | 122 | 5.5 |
| 18 | Bedouin | Straight To The Heart | 116 | 2.5 |


## Set 106. 106. Groove de Entrada — Dilby — 2h — 2026-09-18
**Armado:** 2026-09-18  
**Duracion:** 2.0h  
**Tracks:** 24  
**BPM range:** 120-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy Gerber | What To Do (Dor Danino Remix) | 124 | 5.1 |
| 2 | Sezer Uysal | Yutori (Ruben Karapetyan Remix) | 122 | 5.5 |
| 3 | Chaim, Mads Paige | Phoenix Rising (Original Mix) | 124 | 4.6 |
| 4 | Dilby | Addicted | 124 | 6.0 |
| 5 | Tinlicker, Helsloot | Because You Move Me (Jan Oberlaender Extended Remix) | 122 | 5.5 |
| 6 | Kasper Koman, Shai T | Islander | 122 | 5.5 |
| 7 | Dilby | Body Talk (Original Mix) | 124 | 6.0 |
| 8 | Hardy Heller, Alex Connors, Sven Kegel | Musiq (Gorge Remix) | 123 | 5.2 |
| 9 | DAVI | The Bay 6 (Pt.2) | 121 | 5.0 |
| 10 | Chaim | The Piano One (Kino Todo Remix) | 122 | 5.9 |
| 11 | Shai T | Where The Heart Is (Original Mix) | 122 | 5.5 |
| 12 | Juan Pablo Torrez, Kamilo Sanclemente | Unknown Destination (Extended Mix) | 124 | 6.0 |
| 13 | DAVI | Self ASCND (Original Mix)  | 124 | 5.8 |
| 14 | Gorge, Marc Lenz | Yuna (Original Mix)  | 123 | 5.8 |
| 15 | James Cole | Go With Me (Original Mix)  | 123 | 6.0 |
| 16 | Death on the Balcony | Quiet Storm (Martin Fredes & Matthew Sona Remix) | 122 | 5.7 |
| 17 | Cari Golden, Marc Lenz | Woman in the Wild (Original Mix) | 124 | 6.2 |
| 18 | Tiefstone, Das Pharaoh | Endless Summer (Extended Mix) | 122 | 5.5 |
| 19 | K Loveski | Check-a-Change (Federico Monachesi Remix) | 122 | 5.5 |
| 20 | James Cole | Got You (Original Mix)  | 124 | 6.5 |
| 21 | Maze 28 | Mandala | 124 | 6.0 |
| 22 | Armen Miran & Nicolas Rada | Pull (Original Mix) | 122 | 5.5 |
| 23 | ODAX | Soundexile (Original Mix) | 121 | 5.0 |
| 24 | Ewan Rill, Shayan Pasha | Hidden Path (Original Mix) | 120 | 5.0 |


## Set 107. 107. Nanda — Dilby — 2h — 2026-09-18
**Armado:** 2026-09-18  
**Duracion:** 2.0h  
**Tracks:** 24  
**BPM range:** 121-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Jeremy Olander | Panorama (Original Mix) | 123 | 5.5 |
| 2 | TAEF | FILTH (Extended) | 124 | 6.0 |
| 3 | M.O.S. | Nanda (Dilby Remix) | 123 | 6.1 |
| 4 | Emi Galvan | Flowing | 121 | 5.0 |
| 5 | This Guy Ben | Kapalla (Extended Mix) | 122 | 5.5 |
| 6 | Circulation | Swank (Hobin Rude Remix) | 123 | 5.5 |
| 7 | Alex O'Rion | Tunnel (Original Mix) | 122 | 5.5 |
| 8 | Khen | Closing Doors (Original Mix) | 124 | 6.0 |
| 9 | Hermanez | Tale of the Unexpected (Original Mix) | 123 | 5.5 |
| 10 | Moshic | Love Made Me Do It (Guy J Remix) | 124 | 6.0 |
| 11 | Budakid | Hearts (Argia Remix) | 123 | 5.8 |
| 12 | Nick Newman | Rituals (Hobin Rude Remix) | 122 | 5.5 |
| 13 | Durante, Amtrac | Gather (Original Mix) | 122 | 5.5 |
| 14 | djimboh | Be Brave (Extended Mix) | 122 | 5.5 |
| 15 | Ezequiel Arias | Heat Above - Original Mix | 124 | 6.0 |
| 16 | Oliver Schories | Lymn (Original Mix) | 124 | 6.0 |
| 17 | Che Jose | THE VOID (Extended) | 124 | 6.0 |
| 18 | Ezequiel Arias | Mad Man - Original Mix | 123 | 6.4 |
| 19 | Kamilo Sanclemente | Show Me the Stars (Original Mix) | 121 | 5.0 |
| 20 | Freedo Mosho | Paradise Lost (Maze 28 Reform) | 122 | 5.5 |
| 21 | Rockka | Subversion | 123 | 5.5 |
| 22 | D-Nox & Beckers | Serenade (Doctor Dru Remix) | 122 | 5.5 |
| 23 | Cendryma | Override (Luis Damora Remix) | 122 | 5.5 |
| 24 | Tinlicker | All That I Lost | 124 | 6.0 |


## Set 108. 108. Cierre Groovero — Dilby — 2h — 2026-09-18
**Armado:** 2026-09-18  
**Duracion:** 2.0h  
**Tracks:** 24  
**BPM range:** 121-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Marc Lenz | Shujaa (Original Mix) | 125 | 6.4 |
| 2 | Durante | Never B Alone (Extended Mix) | 123 | 5.5 |
| 3 | Alex Connors, Hardy Heller | Paris (Mihai Popoviciu Remix) | 124 | 5.8 |
| 4 | DAVI | Self R3B00T (Original Mix) | 124 | 5.6 |
| 5 | Juan Pablo Torrez, Kamilo Sanclemente | Ghost Train (Original Mix) | 122 | 5.5 |
| 6 | Dilby | Connect the Dots (Oliver Schories & Gorge Remix) | 124 | 6.0 |
| 7 | DAVI | Self CNTRL (Original Mix) | 125 | 6.6 |
| 8 | James Cole | Khumba (Original Mix)  | 125 | 6.3 |
| 9 | Hardy Heller, Alex Connors | Paris (Original) | 124 | 6.2 |
| 10 | Marc Lenz | People Are People | 123 | 6.5 |
| 11 | Tinlicker | Just To Hear You Say (Joseph Ray Extended Mix) | 124 | 6.0 |
| 12 | Tali Muss | Garip (Original Mix) | 122 | 5.5 |
| 13 | Shai T | Illusions | 122 | 7.0 |
| 14 | Fabri Lopez, Callecat | Mutual Horizons (Rauschhaus Remix) | 121 | 6.7 |
| 15 | Emi Galvan | Samsara | 122 | 5.5 |
| 16 | Chaim | Sun Tease (Doctor Dru Edit) | 122 | 5.5 |
| 17 | Dilby, Simon Mattson, Lazarusman | Give It To Them (Dilby Extended 2022 Rework)  | 124 | 6.6 |
| 18 | Shai T | Summer Oclock (Original Mix)  | 123 | 6.3 |
| 19 | Tom Pavicich | Insight (Original Mix) | 122 | 5.5 |
| 20 | Cid Inc. | Citadel (Original Mix) | 123 | 5.5 |
| 21 | Chaim | Pow Pow (The Organism Remix)  | 121 | 6.0 |
| 22 | Dmitry Molosh | Glide | 121 | 5.0 |
| 23 | Cary Crank | Inner Atlas (Kyotto Remix) | 122 | 5.5 |
| 24 | Nicolas Rada | The Wind Phone | 123 | 5.5 |


## Set 109. 109. Apertura · Color — 2h — 2026-09-19
**Armado:** 2026-09-19  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 118-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Gorje Hewek & Facundo Losardo | Endless History (12" Version) | 122 | 5.5 |
| 2 | House Mafia | Si No Creyera | 123 | 5.5 |
| 3 | FAERO, Tom Pavicich, Analog Sense | Evolve (Original Mix) | 123 | 5.5 |
| 4 | Ed Ed, JJ Dawson | Higher Than Me (Stimming Remix) | 121 | 5.0 |
| 5 | Guy J | Airborne (Original Mix) | 123 | 5.5 |
| 6 | Chaim | Pow Pow (Zombies In Miami Remix)  | 122 | 5.1 |
| 7 | Greg Ochman | In Between Dreams | 120 | 5.0 |
| 8 | Dowden | Pacifist (Original Mix) | 121 | 5.0 |
| 9 | Lane 8 & Yotto | I / Y (Original Mix) | 122 | 5.5 |
| 10 | Mayro | Chimi (Original Mix) | 122 | 5.5 |
| 11 | Powel | Johannesburg (Original Mix) | 120 | 5.0 |
| 12 | Mike Rish | The Likes of You (Original Mix) | 120 | 5.0 |
| 13 | Hernan Cattaneo, Husa & Zeyada | Love Is Coming Back (Club Mix) | 121 | 5.0 |
| 14 | Dor Danino, DvirNuns | Sax A Boom  | 123 | 4.2 |
| 15 | Kasper Koman | In Circles (Extended Mix) | 121 | 5.0 |
| 16 | Durante & Elliot Toller | Ceres | 122 | 5.5 |
| 17 | Antrim | Morning Changes (Original Mix) | 123 | 5.4 |
| 18 | Maze 28, Rockka | Corrosive | 122 | 5.5 |


## Set 110. 110. Apertura · Oscuro — 2h — 2026-09-19
**Armado:** 2026-09-19  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 118-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Dimuth K | Abyssal (Emi Galvan Remix) | 122 | 5.5 |
| 2 | Gorje Hewek | U & Eyeye | 122 | 5.5 |
| 3 | Cristoph | Elements (Maze 28 & Ricky Ryan Reform) | 122 | 3.7 |
| 4 | Chicola, Guy Mantzur | Galactica (Original Mix) | 122 | 5.5 |
| 5 | djimboh | Be Brave (Extended Mix) | 122 | 5.5 |
| 6 | This Guy Ben | Kapalla (Extended Mix) | 122 | 5.5 |
| 7 | Habitatt | Fly With Me (Extended Mix) | 122 | 5.5 |
| 8 | Albuquerque, D-Nox | Brasilisco | 123 | 5.5 |
| 9 | WhoMadeWho & Blue Hawaii | Kiss Me Hard (Adam Ten Remix) | 123 | 5.5 |
| 10 | BOg, Diana Miro, 19:26 | Underwater (Hernan Cattaneo & Marcelo Vasami Remix) | 122 | 5.5 |
| 11 | Massano | System | 122 | 5.5 |
| 12 | Durante, Amtrac | Gather (Original Mix) | 122 | 5.5 |
| 13 | Tantum, Hyunji-A | Keep My Letters (Simon Vuarambon Remix) | 122 | 5.5 |
| 14 | Gorkiz, K Loveski | Echos Of Eons (Greenage Remix) | 122 | 5.5 |
| 15 | Guy J | Karma (Original Mix) | 122 | 5.5 |
| 16 | Aera, Redfreya | Reverse The Process (Aera Remix) | 122 | 3.5 |
| 17 | Kamilo Sanclemente, Sebastian Valencia (COL) | Anomaly (Original Mix) | 123 | 5.5 |
| 18 | Lane 8 | Keep On (Extended Mix) | 122 | 5.5 |


## Set 111. 111. Apertura · Organico — 2h — 2026-09-19
**Armado:** 2026-09-19  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 118-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Ezequiel Arias & Folgar ft Paula Os | Dreamlike feat. Paula Os | 123 | 5.5 |
| 2 | Le Youth, Sultan + Shepard, Panama | New Love (Extended Mix) | 123 | 5.5 |
| 3 | Dor Danino, Yamagucci | Seven Eleven (Adam Ten Remix) | 123 | 5.5 |
| 4 | Armin van Buuren | Part Of Me (feat. Louis III) (Extended Mix) | 122 | 5.5 |
| 5 | Jonathan Rosa, Kyla Milette | Daylight (Simon Doty Extended Mix) | 120 | 5.0 |
| 6 | Benja Molina | Astrea (Original Mix) | 122 | 5.5 |
| 7 | Lee Burridge, Lost Desert | Ash & Ember (Extended Mix) | 123 | 5.5 |
| 8 | Andre Moret | Generator (Extended Mix) | 121 | 5.5 |
| 9 | Kamilo Sanclemente | Whale Voices (Original Mix) | 122 | 5.5 |
| 10 | Super Flu, CIOZ | Body Juice  | 123 | 5.5 |
| 11 | Dowden & Ric Niels | Coil (John Cosani Remix) | 122 | 5.5 |
| 12 | Sébastien Léger, Lost Miracle | Grooba (Original Mix) | 120 | 4.8 |
| 13 | Simone Vitullo, Seraphiel | Every Breath You Take (Extended Mix) | 121 | 5.0 |
| 14 | Juan Deminicis | We Are All Connected (Original Mix) | 122 | 4.4 |
| 15 | Cristoph | Elements (Maze 28 & Ricky Ryan Reform) | 122 | 3.7 |
| 16 | Guy J | My Existence (Original Mix) | 123 | 5.5 |
| 17 | Rockka | Rebit (Original Mix) | 122 | 5.5 |
| 18 | Aera, Redfreya | Reverse The Process (Aera Remix) | 122 | 3.5 |


## Set 112. 112. Previa · Color — 1h30 — 2026-09-19
**Armado:** 2026-09-19  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Cioz | Rain | 123 | 5.2 |
| 2 | Kidnap ft Leo Stannard | Moments (Ben Bohmer & Nils Hoffmann Extended Remix) | 121 | 5.0 |
| 3 | Gai Barone | Weird Behaviours (Original Mix) | 122 | 5.5 |
| 4 | Massane | Horizon | 122 | 5.5 |
| 5 | Rockka | Decryptor | 122 | 5.5 |
| 6 | Budakid | The Curse | 124 | 6.0 |
| 7 | Nicolas Viana | Fog Machine (Extended Mix) | 124 | 6.0 |
| 8 | Greg Ochman | Blinking Stars (Luka Sambe Remix) | 123 | 5.5 |
| 9 | Tali Muss, Vakabular | Solar Focus (Extended Mix) | 123 | 5.5 |
| 10 | WELKER (BR) | Batucada (Original Mix) | 124 | 6.0 |
| 11 | Gorje Hewek, Moya (US) & Dulus | Margaret (Extended Mix) | 122 | 5.5 |
| 12 | DAVI | Forbidden City (Khen Remix) | 123 | 5.5 |
| 13 | Seyah | Dope (Maze 28 & Kyotto Remix) | 121 | 5.0 |


## Set 113. 113. Previa · Oscuro — 1h30 — 2026-09-19
**Armado:** 2026-09-19  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Felix Raphael, Armen Miran & Cafe De Anatolia | Soul Guardian | 122 | 5.5 |
| 2 | DORIANN, ORISS | REVOLUTION (Original Mix) | 124 | 6.0 |
| 3 | D-Nox, Andre Moret | Brisa (Extended Mix) | 123 | 5.5 |
| 4 | Kasper Koman | The Blind Navigator (Extended Mix) | 122 | 5.5 |
| 5 | Cary Crank | Inner Atlas (Kyotto Remix) | 122 | 5.5 |
| 6 | Oliver Schories | Lymn (Original Mix) | 124 | 6.0 |
| 7 | InfeXus & ANZA | Africa (Extended Mix) | 124 | 6.0 |
| 8 | Moshic | Love Made Me Do It (Guy J Remix) | 124 | 6.0 |
| 9 | ANMA | Adya | 124 | 6.0 |
| 10 | Artem Kalalb | Satellites (Emi Galvan Dub Mix) | 122 | 5.5 |
| 11 | TAEF | FILTH (Extended) | 124 | 6.0 |
| 12 | Bedouin, Miluhska | Started Something (feat. Miluhska) | 123 | 5.5 |
| 13 | Quivver, Dave Seaman | The Water's Edge (Original Mix) | 122 | 5.5 |


## Set 114. 114. Previa · Organico — 1h30 — 2026-09-19
**Armado:** 2026-09-19  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Audio Junkies | Aspects of Rhythm  | 123 | 4.0 |
| 2 | Juan Pablo Torrez, Kamilo Sanclemente | Unknown Destination (Extended Mix) | 124 | 6.0 |
| 3 | Eli Nissan | Karnaval (Roy Rosenfeld Remix)  | 122 | 6.4 |
| 4 | Ricardo Criollo House | Papi | 124 | 6.0 |
| 5 | D-Nox, Lonya, DJ Zombi | Fuze (Citizen Kain & D-Formation Remix)  | 123 | 6.8 |
| 6 | Mayro | Harvest (Original Mix) | 123 | 5.5 |
| 7 | Gorje Hewek | Unite feat. Volen Sentir, Makebo & Amonita | 123 | 5.5 |
| 8 | Quivver, Dave Seaman | The Water's Edge (Original Mix) | 122 | 5.5 |
| 9 | Monkey Safari | Goodbye (Lee Burridge & Lost Desert Remix) | 124 | 6.0 |
| 10 | Rodri | BONITA | 122 | 5.5 |
| 11 | Benja Molina | Feeling (Original Mix) | 122 | 5.5 |
| 12 | Hermanez | Areia (Original Mix) | 120 | 5.0 |
| 13 | Ben Böhmer & Tinlicker | Run Away (feat. Felix Raphael) [Extended Mix] | 122 | 5.5 |


## Set 115. 115. Prime Time · Color — 2h — 2026-09-19
**Armado:** 2026-09-19  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Garden City Movement, Mita Gami | Untouchable (Original Mix) | 123 | 5.0 |
| 2 | Roy Rosenfeld | Halomot | 123 | 5.5 |
| 3 | Abity | Roots (Gai Barone Remix) | 122 | 5.5 |
| 4 | Cesar Borra | Don't Kill My Vibe (Steven Flynn Remix) | 123 | 6.0 |
| 5 | Maze 28 | Aer8 (Juan Pablo Torrez Remix) | 122 | 5.5 |
| 6 | Monolink | Father Ocean (Ben Böhmer Remix) | 122 | 5.5 |
| 7 | Shai T | Illusions | 122 | 7.0 |
| 8 | Tali Muss | Garip (Original Mix) | 122 | 5.5 |
| 9 | Eric Lune & Juan Sapia | Tension Release (Original Mix)  | 123 | 6.9 |
| 10 | Kabi (AR), Ric Niels | Kimica | 122 | 5.5 |
| 11 | Kamilo Sanclemente, Andre Moret | Dichotomy (Original Mix) | 122 | 5.5 |
| 12 | Dee Montero & Newman I Love | Shadows | 120 | 5.0 |
| 13 | Guy J | Stranger In A Strange World (Original Mix) | 122 | 5.5 |
| 14 | Santos (AR), Jussto | This Is Rocking It (Original Mix) | 124 | 6.0 |
| 15 | Emi Galvan | Crabo (Original Mix) | 122 | 5.5 |
| 16 | Rodriguez Jr. & Liset Alea | What Is Real (Deep in the Playa Mix) | 123 | 5.5 |
| 17 | Kyotto | Sorry I'm Late (HAFT Remix) | 123 | 5.5 |
| 18 | Sebastian Sellares | Abaddon (Extended Mix) | 121 | 5.0 |


## Set 116. 116. Prime Time · Oscuro — 2h — 2026-09-19
**Armado:** 2026-09-19  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Quivver | Dovetail (Original Mix) | 125 | 6.0 |
| 2 | Tinlicker | Blackbirds (Extended Mix) | 123 | 5.5 |
| 3 | Dmitry Molosh | Glide | 121 | 5.0 |
| 4 | SCRIPT | On The Low (Extended Mix) | 122 | 5.5 |
| 5 | Cid Inc. | Citadel (Original Mix) | 123 | 5.5 |
| 6 | Roy Rosenfeld | Hypnosa De La Rosa | 123 | 5.5 |
| 7 | Carlo Whale, Th;en | Say It | 124 | 6.0 |
| 8 | Cristoph | Signal (Original Mix) | 125 | 6.0 |
| 9 | Innēr Sense (ofc) | Older (Extended Mix) | 125 | 6.0 |
| 10 | Rubmak | Fortuna (Extended Mix) | 125 | 6.0 |
| 11 | Monolink | Otherside (Fideles Remix) | 123 | 5.5 |
| 12 | DAVI | Self ASCND (Original Mix)  | 124 | 5.8 |
| 13 | Kabi (AR) | Rainbow (Extended Mix) | 125 | 6.0 |
| 14 | 8Kays x Juan Hansen | Falling Down (Chris Avantgarde Remix) | 124 | 6.0 |
| 15 | Einmusik, Dirty Doering | Centaurio | 125 | 6.0 |
| 16 | Che Jose | THE VOID (Extended) | 124 | 6.0 |
| 17 | D-Nox, Andre Moret | Shine (Extended Mix) | 124 | 6.0 |
| 18 | Lexer | Odyssey (Original Mix) | 122 | 5.5 |


## Set 117. 117. Prime Time · Organico — 2h — 2026-09-19
**Armado:** 2026-09-19  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | RUFUS | Innerbloom (Lane 8 Remix) | 124 | 5.5 |
| 2 | Dowden | Night Emeralds (Original Mix) | 122 | 5.5 |
| 3 | Sebastien Leger | Stevie (Original Mix) | 121 | 5.0 |
| 4 | Culoe De Song | Mount Zion (Jonathan Kaspar Remix) | 122 | 6.5 |
| 5 | Carlo Whale, Th;en | Say It | 124 | 6.0 |
| 6 | Cristoph | Signal (Original Mix) | 125 | 6.0 |
| 7 | Roisin Murphy | Dear Miami (Bedouin Extended Remix) | 124 | 6.0 |
| 8 | Cid Inc. | Forgotten | 123 | 5.5 |
| 9 | Kamilo Sanclemente, Giovanny Aparicio | Magic Carpet (Original Mix) | 121 | 5.0 |
| 10 | Moe Turk, Nad Merheb | Esto Puede Pasar (Original Mix) | 120 | 5.0 |
| 11 | Emi Galvan & Albuquerque | Stay High (RIGOONI Remix) | 121 | 5.0 |
| 12 | D-Nox, Two Of A Kind, Gai Barone | Vida (DJ Zombi Remix) | 120 | 5.0 |
| 13 | Dmitry Molosh | Bustle (Original Mix) | 120 | 5.0 |
| 14 | Máximo Lasso | Breathe Me In (Kebin Van Reeken Remix) | 122 | 5.5 |
| 15 | Dee Montero | Aria (Newman (I Love) Remix) | 123 | 5.5 |
| 16 | Quivver | Another Storm (Mike Rish Remix) | 122 | 5.5 |
| 17 | Hermanez | Dust Town | 122 | 5.5 |
| 18 | Aaron Sevilla, RBØR, El Gato CHP | Gitanos (Original Mix) | 120 | 5.0 |


## Set 118. 118. Peak · Color — 1h30 — 2026-09-19
**Armado:** 2026-09-19  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 121-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Monolink | Father Ocean (Ben Boehmer Remix) | 122 | 5.5 |
| 2 | Kamilo Sanclemente | Go Home (Original Mix) | 121 | 5.0 |
| 3 | Digital Mess | Raspberry Porridge (Cosmonaut Extended Remix) | 123 | 5.6 |
| 4 | Fideles, Be No Rain | See You In Dreams (Original Mix) | 123 | 5.5 |
| 5 | Bondarev, Max Wexem | The Lotus (Original Mix) | 123 | 5.5 |
| 6 | Tali Muss | Interlocutor (Kebin Van Reeken Extended Remix) | 122 | 5.5 |
| 7 | Shai T | Summer Oclock (Original Mix)  | 123 | 6.3 |
| 8 | Sébastien Léger | Forbidden Garden (Tim Green Remix) | 122 | 5.5 |
| 9 | Rockka, Maze 28 | Chroma (Original Mix) | 122 | 5.5 |
| 10 | Amine K (Moroko Loko), WAHM (FR) | Kill the Anger (Rodriguez Jr. Remix) | 124 | 6.0 |
| 11 | Gai Barone | MoMa | 123 | 5.5 |
| 12 | Patrice Bäumel | Clair (Cioz Neapolis Remix) | 121 | 7.0 |
| 13 | Anton Borin (RU) | May Spring Come (Original Mix) | 123 | 5.5 |


## Set 119. 119. Peak · Oscuro — 1h30 — 2026-09-19
**Armado:** 2026-09-20  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 121-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | SHOUSE | Sunrise (Adam Ten Remix)  | 124 | 5.6 |
| 2 | Jonas Saalbach, Luna Semara | Midnight Sky (Carlo Whale Remix) | 123 | 5.5 |
| 3 | Cezar Nica & Tapski | Midnight Sun | 121 | 5.0 |
| 4 | Nick Warren | Freebird (Emi Galvan Remix) | 123 | 5.5 |
| 5 | NOIYSE PROJECT, Hernan Cattaneo, Jamie Stevens | Remember Me - Hernan Cattaneo & Jamie Stevens Remix | 122 | 5.5 |
| 6 | Tinlicker, Helsloot | Because You Move Me (Extended Mix) | 123 | 5.5 |
| 7 | David Guetta, MORTEN | The Future is Now | 125 | 6.0 |
| 8 | DAVI | Among Us (Original Mix) | 123 | 5.5 |
| 9 | Simon Vuarambon | Kaskazi | 122 | 5.5 |
| 10 | Kamilo Sanclemente | Parallel Moon (Original Mix) | 123 | 5.5 |
| 11 | Bedrock | Heaven Scent (Eagles & Butterflies Remix) | 123 | 5.5 |
| 12 | Shar, Gruuve | Teller (Original Mix) | 125 | 7.0 |
| 13 | Sudhaus & The Wash | Spectron (DJ Ruby Remix) | 123 | 5.5 |


## Set 120. 120. Peak · Organico — 1h30 — 2026-09-19
**Armado:** 2026-09-20  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 121-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | No Hopes | Sounds Like a Melody (Extended Mix) | 124 | 6.0 |
| 2 | Sebastien Leger | Ariana | 122 | 5.5 |
| 3 | Brian Cid | Allure (Original Mix) | 122 | 5.5 |
| 4 | Pachanga Boys | Time | 124 | 6.0 |
| 5 | Andy Moor & Adam White | The Whiteroom (feat. Whiteroom) [Marsh Extended Mix] | 125 | 6.0 |
| 6 | Mike Griego | Antidote | 123 | 7.9 |
| 7 | Artic White | Vivere (Extended Mix) | 123 | 5.5 |
| 8 | Kamilo Sanclemente | Delusion (Original Mix) | 122 | 5.5 |
| 9 | Ale Russo | Wake Up (Original Mix) | 121 | 5.0 |
| 10 | Bedrock | Heaven Scent (Eagles & Butterflies Remix) | 123 | 5.5 |
| 11 | Paul Thomas & Christian Burns | Enjoy the Silence (Extended Mix) | 122 | 5.5 |
| 12 | Roy Rosenfeld, Gorje Hewek, Dulus | Vida (Original Mix) | 122 | 5.5 |
| 13 | Aaron Montes, Havana Hustlers | Where Have You Been (George Calle Exclusive Traxsource Mix) | 124 | 6.0 |


## Set 121. 121. Cierre · Color — 1h30 — 2026-09-19
**Armado:** 2026-09-20  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Jamie Stevens x Kasey Taylor | Verlaine (Mixed) | 124 | 5.5 |
| 2 | Alex Connors, Hardy Heller | Colourblind (Original Mix) | 123 | 6.6 |
| 3 | Durante, Ezequiel Arias | Dream Controller (Extended Mix) | 124 | 6.0 |
| 4 | Jeremy Olander | Andköln (Hunter/Game Remix) | 124 | 6.0 |
| 5 | Agustin Pietrocola | Endeavor (Unusual Soul Remix) | 122 | 5.5 |
| 6 | KAZKO | Fading Control (Original Mix) | 122 | 5.5 |
| 7 | Raphael Palacci | Big Jet Plane (Remix) | 124 | 6.0 |
| 8 | Anyma, Rebūke | Syren | 125 | 6.0 |
| 9 | Artic White | Paradigm (Extended Mix) | 123 | 5.5 |
| 10 | Rauschhaus, Cary Crank | Bright Things in Front of Us (Extended Mix) | 122 | 5.5 |
| 11 | Nox Vahn | Brainwasher (Warung Extended Mix) | 123 | 5.5 |
| 12 | Emi Galvan | Karma (Original Mix) | 121 | 5.0 |
| 13 | Dowden, Mazayr | Deflator (Montw Remix) | 120 | 5.0 |


## Set 122. 122. Cierre · Oscuro — 1h30 — 2026-09-19
**Armado:** 2026-09-20  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Marc DePulse, Rafael Cerato | Cocobolo | 123 | 5.5 |
| 2 | Hana, Durante | Starglow (Extended Mix) | 124 | 6.0 |
| 3 | D-Nox, Stereo Underground | Shooting Stars (Extended Version) | 125 | 6.0 |
| 4 | Tinlicker, Ben Böhmer | Voodoo (Extended Mix) | 124 | 6.0 |
| 5 | Ric Niels | Invasion | 123 | 5.5 |
| 6 | Seth Schwarz & Be Svendsen | The Bar Tender | 121 | 5.0 |
| 7 | Budakid, Rromarin | Better O'be New (Roy Rosenfeld Extended Remix) | 122 | 5.5 |
| 8 | Brian Cid | Observe (Original Mix) | 121 | 5.0 |
| 9 | Adriatique, Delhia De France, Marino Canal | Home (Mind Against Remix) | 120 | 5.0 |
| 10 | Blake Jarrell | Twenty Miami's Ago (Cendryma Extended Mix) | 122 | 5.5 |
| 11 | Hraach, Armen Miran | Menq (Nick Warren & Nicolas Rada Remix) | 122 | 5.5 |
| 12 | Rufus Du Sol | Innerbloom (Original Mix) | 122 | 5.5 |
| 13 | Kamilo Sanclemente, Andre Moret | Mirage (Original Mix) | 122 | 5.5 |


## Set 123. 123. Cierre · Organico — 1h30 — 2026-09-19
**Armado:** 2026-09-20  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Marc DePulse, Rafael Cerato | Cocobolo | 123 | 5.5 |
| 2 | FAERO, Tom Pavicich, Analog Sense | The Landing (Club Mix) | 123 | 5.5 |
| 3 | Kamilo Sanclemente | No Regrets (Artic White Extended Remix) | 122 | 7.2 |
| 4 | Raúl Vidal | Lamour | 121 | 5.0 |
| 5 | Jan Blomqvist | The Space In Between (Ben Böhmer Extended Remix) | 122 | 5.5 |
| 6 | Cendryma, THMS (US) | Moonflare (Extended Mix) | 121 | 5.0 |
| 7 | Guy Mantzur | Moongazer | 120 | 5.0 |
| 8 | Redspace | Don't Think (Original Mix) | 121 | 5.0 |
| 9 | Maze 28 | Cry of the Deserts (Molac & Nicolas Viana Remix) | 122 | 6.2 |
| 10 | Kiko Franco | LOW (Extended Mix) | 124 | 6.0 |
| 11 | D-Nox, Stereo Underground | Shooting Stars (Extended Version) | 125 | 6.0 |
| 12 | Solis [US] | Una Volta (Extended Mix) | 123 | 5.5 |
| 13 | UNDERMOON | Enjoy the Silence (Original Mix) | 125 | 6.0 |


## Set 124. 124. After · Color — 2h — 2026-09-19
**Armado:** 2026-09-20  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | GMJ & Matter | Arkeron (Original Mix) | 120 | 5.0 |
| 2 | GARDEN CITY MOVEMENT | UNTOUCHABLE (MITA GAMI EDIT) | 121 | 5.3 |
| 3 | Leandro Murua, Martin Fredes | Interference (Original Mix) | 122 | 5.5 |
| 4 | Rauschhaus | Faunus (Original Mix) | 123 | 5.5 |
| 5 | Kamilo Sanclemente | Canon (Original Mix) | 123 | 5.5 |
| 6 | Rockka | Synthesis | 123 | 5.5 |
| 7 | Lane 8 | Oh, Miles (feat. Julia Church) | 124 | 6.0 |
| 8 | Kostya Outta, Liam Garcia | If I Win (Extended Mix) | 123 | 5.5 |
| 9 | Sebastian Sellares | Garden of Eden (Extended Mix) | 122 | 5.5 |
| 10 | Redspace, IAM LILITH & Cafe De Anatolia | Ashigane | 122 | 6.4 |
| 11 | Marsh | Beech Street (Simon Doty Extended Mix) | 122 | 5.5 |
| 12 | Melodiam | Old Garden | 122 | 5.5 |
| 13 | Audio Junkies, AVIV BENS | Perico (Original Mix) | 122 | 5.5 |
| 14 | Durante, Running Touch | Follow feat. Running Touch (Extended Mix) | 122 | 5.5 |
| 15 | Roy Rosenfeld | Skyhook (Original Mix) | 121 | 5.0 |
| 16 | Fabricio Gutierrez | Reedmov (Kebin van Reeken Remix) | 120 | 6.7 |
| 17 | Made In TLV & Dor Danino | Make a Wish | 120 | 5.7 |
| 18 | Mazayr | Falling | 120 | 5.0 |


## Set 125. 125. After · Oscuro — 2h — 2026-09-19
**Armado:** 2026-09-20  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Space Motion | Baiana (Original Mix) | 122 | 5.5 |
| 2 | Monolink | Don't Hold Back (Yotto Remix) | 122 | 5.5 |
| 3 | Emi Galvan | Trust (Original Mix) | 122 | 5.5 |
| 4 | Cioz & Nairobi D | Haunted | 123 | 5.7 |
| 5 | Juan Deminicis | Disorder (Andrea Cassino Remix)  | 122 | 6.7 |
| 6 | Tuccillo | Summer Slam | 123 | 5.8 |
| 7 | Rezident | Hunter (Enamour Remix)  | 124 | 7.0 |
| 8 | Kamilo Sanclemente, Mauro Aguirre | Goldes Eyes (Original Mix) | 123 | 5.5 |
| 9 | Fur Coat | Ethereal | 124 | 6.0 |
| 10 | Supacooks, Bondarev | Activator (Original Mix) | 123 | 5.5 |
| 11 | Cary Crank, OBL | Spitfire (Original Mix)  | 124 | 6.6 |
| 12 | DAVI | Future Avenue | 125 | 6.0 |
| 13 | Ezequiel Arias | Heat Above - Original Mix | 124 | 6.0 |
| 14 | Vintage Culture, Paige Cavell | Promised Land (Innellea Remix / Extended) | 125 | 6.0 |
| 15 | Rolasoul, Greta Meier | Reflections (Extended Version) | 124 | 6.0 |
| 16 | Stephan Bodzin, Jem Cooke, Massano | Healing (Extended Mix) | 124 | 6.0 |
| 17 | Julian Nates, Julieta Kühnle | Fever (Extended Mix) | 123 | 5.5 |
| 18 | Boxer, Jody Wisternoff & James Grant | Sun Kissed (Extended Mix) | 124 | 6.0 |


## Set 126. 126. After · Organico — 2h — 2026-09-19
**Armado:** 2026-09-20  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Jimpster | Becoming Cyclonic (Tim Green Edit) | 122 | 4.6 |
| 2 | Guy J | Worlds Apart (Original Mix) | 122 | 5.5 |
| 3 | Kamilo Sanclemente | Show Me the Stars (Original Mix) | 121 | 5.0 |
| 4 | Beckers, D-Nox | Skylab (Original Mix) | 122 | 5.5 |
| 5 | Lee Burridge | Fading Out (Extended Mix) | 122 | 6.8 |
| 6 | Maze 28 | Stardust (Original Mix) | 121 | 5.0 |
| 7 | Zakem | Albadia (Original Mix)  | 120 | 7.0 |
| 8 | Juan Deminicis | Virtual Escape (Original Mix) | 121 | 5.0 |
| 9 | Izhevski, Talemates | I Got Soul (Extended Mix) | 121 | 5.0 |
| 10 | Bosknegra | Primavera (Original Mix) | 120 | 5.0 |
| 11 | Shayan Pasha, Redspace | Pantheon (Original Mix) | 121 | 5.0 |
| 12 | Nora En Pure | Spring Embers (Extended Mix) | 122 | 5.5 |
| 13 | BOg, GHEIST | Venere (Fideles Remix) | 122 | 5.5 |
| 14 | Chicola | Blueberries (Extended) | 122 | 5.5 |
| 15 | Gorje Hewek, Dulus | Earth (Original Mix) | 123 | 5.5 |
| 16 | Emi Galvan & Albuquerque | Stay High | 122 | 5.5 |
| 17 | Sebastien Leger | Feel (Original Mix) | 122 | 5.5 |
| 18 | Nico de Andrea, THEMBA (SA), Tasan | Disappear feat. Tasan (Andrea Oliva Extended Remix) | 123 | 5.5 |


## Set 127. 127. Apertura · Nuevo — 2h — 2026-09-20
**Armado:** 2026-09-21  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 118-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Ewan Rill, Shayan Pasha | Hidden Path (Can Costa & Futura City Remix) | 120 | 5.3 |
| 2 | Sebastien Leger, Roy Rosenfeld, Lost Miracle | Closer To You (Extended Mix) | 120 | 5.0 |
| 3 | Indigo Man | Similarity (Mayro Remix) | 122 | 4.0 |
| 4 | Agustin Pietrocola | Amethyst (Original Mix) | 123 | 5.2 |
| 5 | Frezz | Venom Groove (Praise (BR) Remix) | 122 | 5.8 |
| 6 | House Mafia | Si No Creyera | 123 | 5.5 |
| 7 | Hydrah, Enamour | Hypertrophy of Heart feat. Hydrah (Extended Mix)  | 122 | 6.0 |
| 8 | Khen | Some Little Secrets | 122 | 5.5 |
| 9 | Dmitry Molosh | Carousel (Original Mix) | 123 | 5.5 |
| 10 | Kyotto | District (Original Mix) | 122 | 5.5 |
| 11 | D-Nox, Andre Moret | Cosmic (Extended Mix) | 121 | 5.0 |
| 12 | Maze 28, Rockka | Inertia | 122 | 5.5 |
| 13 | FAERO, Tom Pavicich, Analog Sense | Evolve (Original Mix) | 123 | 5.5 |
| 14 | Ed Ed, JJ Dawson | Higher Than Me (Stimming Remix) | 121 | 5.0 |
| 15 | Serge Canteros | Delusions (Original Mix) | 122 | 5.4 |
| 16 | Redspace, Unusual Soul | White Room (Original Mix) | 122 | 5.9 |
| 17 | Soulmade (AR) | Thunderdome (Original Mix) | 121 | 5.1 |
| 18 | Digital Mess | Raspberry Porridge (Extended Mix) | 120 | 4.1 |


## Set 128. 128. Apertura · Bailable — 2h — 2026-09-20
**Armado:** 2026-09-20  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 118-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy Mantzur, Roy Rosenfeld | Epika (Original Mix) | 120 | 5.0 |
| 2 | Guy J | Alive Again (Original Mix) | 122 | 4.5 |
| 3 | Maze 28 | Mindloop (Original Mix) | 120 | 5.0 |
| 4 | Dark Soul Project & Replicanth | Zicatela (Original Mix) | 122 | 5.4 |
| 5 | Malone, BLOND.ISH, Archila | Voices Above (Original Mix) | 122 | 5.5 |
| 6 | Of Norway | I Miss You (Sentre Remix) | 123 | 5.5 |
| 7 | Emi Galvan | Flowing | 121 | 5.0 |
| 8 | Cendryma | Parabolic (Original Mix) | 122 | 5.5 |
| 9 | Pomboklap, Aaron Sevilla, P.Rivas | Se Fundieron (Original Mix) | 120 | 5.0 |
| 10 | Rafael Cerato | Silverscreen | 120 | 5.0 |
| 11 | djimboh | Be Brave (Extended Mix) | 122 | 5.5 |
| 12 | Kamilo Sanclemente | Intense Delirium (Original Mix) | 123 | 5.1 |
| 13 | GMJ & Matter | Metanoia | 122 | 5.5 |
| 14 | D-Nox, Andre Moret | Six (Extended Mix) | 122 | 5.5 |
| 15 | Buika & Kiko Navarro | El Silencio (Club Version) | 120 | 5.2 |
| 16 | Mita Gami | San Pedro | 122 | 5.5 |
| 17 | Tantum, Hyunji-A | Keep My Letters (Simon Vuarambon Remix) | 122 | 5.5 |
| 18 | Cioz | Soul Fixer | 122 | 4.1 |


## Set 129. 129. Previa · Nuevo — 1.5h — 2026-09-20
**Armado:** 2026-09-21  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | DJ Bird | In Space | 119 | 5.8 |
| 2 | Dmitry Molosh | Flower Field (Original Mix) | 120 | 6.2 |
| 3 | Mind Echoes | Answers (Original Mix) | 120 | 6.6 |
| 4 | Ignacio Hernandez | Circle Of Lights (Claudio Cornejo (AR) Night Mix) | 121 | 5.0 |
| 5 | Rich Trelo, Sineforma | Lost in Brooklyn (Gabbe (AR) Remix) | 123 | 6.4 |
| 6 | Paul Hazendonk, Return To Saturn | You Can Have It All (Peter Makto & Matthew Sona Remix) | 121 | 5.0 |
| 7 | ANix JAy | Crazy (Juan Ibanez Remix) | 122 | 4.6 |
| 8 | Gogol | Desert Rose | 120 | 5.0 |
| 9 | Redspace, 4T6 | Trust You (Original Mix) | 120 | 6.8 |
| 10 | Ewan Rill | Nature Pentacles (Original Mix) | 122 | 5.5 |
| 11 | Menori | Lunar (Viktop Extended Remix) | 123 | 5.3 |
| 12 | This Guy Ben | Troubador (Extended Mix) | 124 | 6.0 |
| 13 | Freddy Be, Dilby, Floorplay (LA) | Lovely Day (Extended Mix)  | 124 | 4.4 |


## Set 130. 130. Previa · Bailable — 1.5h — 2026-09-20
**Armado:** 2026-09-20  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Felix Raphael, Armen Miran & Cafe De Anatolia | Soul Guardian | 122 | 5.5 |
| 2 | Dmitry Molosh | Bird Flight (Original Mix) | 120 | 5.0 |
| 3 | Radio Slave | Strobe Queen | 120 | 5.0 |
| 4 | Mita Gami | Allenby | 120 | 5.6 |
| 5 | Tuna, Quentro, Kuntay Cevizci | Perreo (Extended Mix) | 120 | 5.0 |
| 6 | Kamilo Sanclemente, M.O.S., Andre Moret | Perception (Original Mix) | 122 | 5.5 |
| 7 | Dilby | Feel It | 123 | 5.9 |
| 8 | BIG Mouth (DXB), Under Control (LB) | Radio Ga Ga (Extended Mix) | 123 | 5.5 |
| 9 | Fran Bonetti, RRØDD | Ride or Die (Kamikaze BR Remix) | 124 | 6.0 |
| 10 | Adeva, Groove P | Hold On Honey (Extended Mix) | 124 | 6.0 |
| 11 | Quivver, Dave Seaman | The Water's Edge (Original Mix) | 122 | 5.5 |
| 12 | Artem Kalalb | Satellites (Emi Galvan Dub Mix) | 122 | 5.5 |
| 13 | CIOZ | Cookie Man (Original Mix) | 124 | 4.7 |


## Set 131. 131. Prime Time · Nuevo — 2h — 2026-09-20
**Armado:** 2026-09-21  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Agustin Pietrocola | Sizer (Original Mix) | 123 | 5.2 |
| 2 | Drunken Kong, D-SHIFT | City Lights (Original Mix) | 122 | 6.4 |
| 3 | Evelynka, Jean Vayat, Artaria | Sun Is Setting  | 124 | 6.9 |
| 4 | Cesar Borra | Don't Kill My Vibe (Steven Flynn Remix) | 123 | 6.0 |
| 5 | Quivver | Deception (Original Mix) | 124 | 5.2 |
| 6 | Fernando Olaya | Lost In Marrakesh (Extended Mix)  | 124 | 4.9 |
| 7 | Andre Moret, Mariusso | Cygnus (Cosmonaut Extended Mix) | 123 | 5.5 |
| 8 | Monolink | Father Ocean (Ben Böhmer Remix) | 122 | 5.5 |
| 9 | Iovino | Deep Jungle (Tom Pavicich Remix) | 124 | 6.0 |
| 10 | Kamilo Sanclemente, Sebastian Valencia (COL) | Test Flight (Original Mix) | 123 | 5.5 |
| 11 | Eric Lune & Juan Sapia | Tension Release (Original Mix)  | 123 | 6.9 |
| 12 | Khen | Yellow (Original Mix) | 122 | 5.5 |
| 13 | Maze 28 | Flux | 122 | 5.5 |
| 14 | Rodriguez Jr. & Liset Alea | What Is Real (Deep in the Playa Mix) | 123 | 5.5 |
| 15 | Ezequiel Arias | ReAnimation (Extended Mix) | 125 | 5.7 |
| 16 | Kiko Navarro | Soñando Contigo (feat. Buika) [Kiko's Rework Of Yotam Avni Remix] | 125 | 6.1 |
| 17 | Chemical Brothers | Out of control (Teiko Yume's Frequent Flyer remix) | 125 | 6.0 |
| 18 | Santos (AR), Jussto | This Is Rocking It (Original Mix) | 124 | 6.0 |


## Set 132. 132. Prime Time · Bailable — 2h — 2026-09-20
**Armado:** 2026-09-20  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Bedouin | Tijuana (Vintage Culture Remix) | 125 | 6.0 |
| 2 | Nick Curly & Jansons | Chip Butty (Alex Kennon Remix) | 124 | 5.9 |
| 3 | Kasper Koman | Sinking Sky | 122 | 5.5 |
| 4 | Maz (BR), VXSION | Amana | 123 | 5.5 |
| 5 | Rafael, Adam Ten | Sweet Boy (Original Mix) | 125 | 6.1 |
| 6 | D-Nox, Andre Moret | Shine (Extended Mix) | 124 | 6.0 |
| 7 | Mayro | Enchanted Forest (Extended Mix) | 123 | 6.6 |
| 8 | Helsloot | Disco Maxi (Extended Mix) | 124 | 6.0 |
| 9 | Culoe De Song | The Spiker (Manoo Club Remix) | 122 | 6.7 |
| 10 | Tiefstone, Das Pharaoh | Endless Summer (Extended Mix) | 122 | 5.5 |
| 11 | Peer Kusiv | Nightdrive Feat Fynn (Rauschhaus Remix) | 124 | 6.0 |
| 12 | Scippo | Wave (Original Mix) | 123 | 5.5 |
| 13 | Rubmak | Fortuna (Extended Mix) | 125 | 6.0 |
| 14 | Budakid | Infinity | 124 | 6.0 |
| 15 | Rodriguez Jr. | Twilight Language (Extended Version) | 123 | 5.5 |
| 16 | Emi Galvan & Albuquerque | Stay High (RIGOONI Remix) | 121 | 5.0 |
| 17 | Cid Inc & Dmitry Molosh | Coalition | 122 | 5.5 |
| 18 | Gassan, Salahaddin & Maztrofikx | Dale Rakata (Extended Vocal Club Mix) | 120 | 5.0 |


## Set 133. 133. Peak · Nuevo — 1.5h — 2026-09-20
**Armado:** 2026-09-21  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 121-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy J | Everyday (Original Mix) | 122 | 5.5 |
| 2 | Juan Buitrago | Anja | 121 | 6.9 |
| 3 | Heller & Farley Project | Ultra Flava (David Penn Extended Remix)  | 123 | 8.1 |
| 4 | Franco Camiolo | Torch (Extended Mix) | 121 | 5.0 |
| 5 | Eli Nissan | Karnaval (Original Mix)  | 122 | 8.2 |
| 6 | Artic White | Vivere (Extended Mix) | 123 | 5.5 |
| 7 | Cary Crank | Echoes From Below (Weird Sounding Dude Remix) | 121 | 5.0 |
| 8 | DAVI | Among Us (Original Mix) | 123 | 5.5 |
| 9 | Scatman John | Scatman (Ellie Sax Mix) | 125 | 6.0 |
| 10 | Aaron Montes, Havana Hustlers | Where Have You Been (George Calle Exclusive Traxsource Mix) | 124 | 6.0 |
| 11 | Jan Blomqvist, Rodriguez Jr. | Destination Lost (Arodes Extended Remix) | 125 | 6.0 |
| 12 | Anturage, Alar | Moet (Original Mix) | 123 | 5.5 |
| 13 | mOat (UK) | Brian (Extended Mix) | 125 | 6.0 |


## Set 134. 134. Peak · Bailable — 1.5h — 2026-09-20
**Armado:** 2026-09-20  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 121-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Kamilo Sanclemente | Sunset Love | 121 | 5.0 |
| 2 | Jody Wisternoff | Paramour (Original Mix) | 123 | 5.5 |
| 3 | Maze 28 | Great Attractor (Ruben Karapetyan Remix) | 124 | 6.0 |
| 4 | Keith Mac | The Chant - Extended Mix | 125 | 6.0 |
| 5 | XANDL | Get Over It (Original Mix) | 124 | 6.0 |
| 6 | Ric Niels | Phantom (Original Mix) | 122 | 5.5 |
| 7 | Analog Jungs | Ocaris (Original Mix)  | 123 | 8.1 |
| 8 | Pachanga Boys | Time | 124 | 6.0 |
| 9 | Favio Inker, Rodrigo Am | Have a Dance | 124 | 6.0 |
| 10 | ECHO DAFT, Kebin Van Reeken | Mysterious Drag (Original Mix) | 122 | 7.5 |
| 11 | Spencer Brown | Blue Magic (feat. Danny Shamoun) | 123 | 5.5 |
| 12 | NOIYSE PROJECT, Hernan Cattaneo, Jamie Stevens | Remember Me - Hernan Cattaneo & Jamie Stevens Remix | 122 | 5.5 |
| 13 | David Penn | That Vibe (Original Mix) | 123 | 6.9 |


## Set 135. 135. Cierre · Nuevo — 1.5h — 2026-09-20
**Armado:** 2026-09-21  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Vini Pistori | Sanctify Your Love (Original Mix) | 123 | 5.5 |
| 2 | Emphi | Dust (John Cosani Remix) | 122 | 6.1 |
| 3 | Brian Cid | Observe (Original Mix) | 121 | 5.0 |
| 4 | Adriatique, Delhia De France, Marino Canal | Home (Mind Against Remix) | 120 | 5.0 |
| 5 | Dmitry Molosh | With Me (Original Mix) | 119 | 3.5 |
| 6 | Fraser Rix | Strawberry Cake (Mind Echoes Remix) | 120 | 7.6 |
| 7 | Kamilo Sanclemente | Orb (Original Mix) | 121 | 5.0 |
| 8 | Fur Coat, Running Pine | Hurricane (Tim Green Remix) | 123 | 7.5 |
| 9 | D-Nox & Beckers | Serenade (Doctor Dru Remix) | 122 | 5.5 |
| 10 | Hugel, GROSSOMODDO | Andalucia (Extended Mix) | 120 | 5.0 |
| 11 | Guy Mantzur | Chasing The Fog | 122 | 5.5 |
| 12 | Afro Exotiq | Covenant | 120 | 5.0 |
| 13 | Samantha Loveridge, Treetalk | Losing My Religion (Extended Mix) | 122 | 5.5 |


## Set 136. 136. Cierre · Bailable — 1.5h — 2026-09-20
**Armado:** 2026-09-20  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Nandu | Neglecting the Facts (Original Mix) | 119 | 3.5 |
| 2 | Sound Quelle | Fofan (Extended Mix) | 120 | 5.0 |
| 3 | Ciro Riveiro | Asia | 121 | 7.1 |
| 4 | LUCH | Shepard's Tone (Original Mix) | 123 | 5.5 |
| 5 | Eriva | Black Eyes (EHDU Extended Mix) | 121 | 5.0 |
| 6 | Sophie Lloyd, Dames Brown, David Penn | Calling Out (David Penn Extended Remix) | 123 | 6.6 |
| 7 | Ric Niels | Invasion | 123 | 5.5 |
| 8 | Kinky Sound | Blow (Rafael Cerato Remix) | 124 | 6.0 |
| 9 | LEFSOUL | Sweet Dreams (Extended Mix) | 125 | 6.0 |
| 10 | Ezequiel Arias | Perfect Dream (Extended Mix) | 124 | 6.0 |
| 11 | Tale Of Us | North Star | 122 | 5.5 |
| 12 | Cendryma, THMS (US) | Moonflare (Extended Mix) | 121 | 5.0 |
| 13 | Dowden | Urias | 121 | 5.0 |


## Set 137. 137. After · Nuevo — 2h — 2026-09-20
**Armado:** 2026-09-21  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Space Motion | Baiana (Original Mix) | 122 | 5.5 |
| 2 | Nico de Andrea, THEMBA (SA), Tasan | Disappear feat. Tasan (Andrea Oliva Extended Remix) | 123 | 5.5 |
| 3 | Ferdinand Dreyssig & Marvin Hey | Coeur De La Nuit (Worakls Remix) | 124 | 6.0 |
| 4 | Gadi Mitrani | Gone (Alex O'Rion Remix)  | 123 | 6.0 |
| 5 | Lee Burridge | Fading Out (Extended Mix) | 122 | 6.8 |
| 6 | Alfonso Muchacho | Heartless (Cosmonaut Remix) | 122 | 5.5 |
| 7 | Rodrigo Pochelu, Cristian Hidalgo | Entrophee (Original Mix) | 122 | 7.0 |
| 8 | Anton Borin (RU), Bondarev | Samadhi (Kasper Koman Remix) | 122 | 5.5 |
| 9 | Safar | Love Parade | 123 | 5.5 |
| 10 | Kamilo Sanclemente | A Lonely Pink Cloud (Original Mix) | 122 | 5.5 |
| 11 | Axone, Arodes, ACNØR | Volume Up (Original Mix) | 123 | 5.5 |
| 12 | Amine K (Moroko Loko), WAHM (FR) | Kill the Anger (Original Mix) | 124 | 6.0 |
| 13 | Tali Muss & Mayro | Fantom (Max Freegrant & Slow Fish Remix) | 123 | 5.5 |
| 14 | WhoMadeWho | Silence & Secrets (Adriatique Remix) | 124 | 6.0 |
| 15 | Joris Voorn, Mees Salomé, Celine Cairo | Fool's Paradise (Joris Voorn Remix) | 124 | 6.0 |
| 16 | Vintage Culture, Paige Cavell | Promised Land (Innellea Remix / Extended) | 125 | 6.0 |
| 17 | Aaron Sevilla, Mijangos, Tom Novy | Your Body (Original Mix) | 124 | 6.0 |
| 18 | Harry Romero | The Get Down (Extended Mix) | 125 | 6.0 |


## Set 138. 138. After · Bailable — 2h — 2026-09-20
**Armado:** 2026-09-20  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Final Request, ant art | Driven by the Stars (Olivier Giacomotto Remix) | 124 | 6.0 |
| 2 | Enclips | Astronomy (Original) | 124 | 5.9 |
| 3 | Ferdinand Dreyssig & Marvin Hey | Coeur De La Nuit (Worakls Remix) | 124 | 6.0 |
| 4 | Nico de Andrea, THEMBA (SA), Tasan | Disappear feat. Tasan (Andrea Oliva Extended Remix) | 123 | 5.5 |
| 5 | Rafael Cerato, Kinky Sound | Attack (Original Mix) | 123 | 5.5 |
| 6 | Mayro | Tactical (Extended Mix) | 122 | 6.6 |
| 7 | Sébastien Léger, Lost Miracle | Dodonpachi (Original Mix) | 122 | 5.5 |
| 8 | Zakem | Adameyo (Original Mix) | 123 | 6.3 |
| 9 | Axone, Arodes, ACNØR | Volume Up (Original Mix) | 123 | 5.5 |
| 10 | Anderson vs Ivan Aliaga | Breakdown (Original Mix) | 123 | 5.5 |
| 11 | Emi Galvan & Albuquerque | Don't Kill the Messenger | 123 | 5.5 |
| 12 | Masayno | One Side (Abel Ray Remix) | 122 | 5.5 |
| 13 | Michael A | Zero Dawn (Kebin Van Reeken Remix) | 121 | 5.0 |
| 14 | Samm (BE) | I'm Wondering (feat. LAUD) | 120 | 5.0 |
| 15 | Chaim | Pow Pow (The Organism Remix)  | 121 | 6.0 |
| 16 | DAVI | The Bay 6 (Pt.2) | 121 | 5.0 |
| 17 | Shayan Pasha, Redspace | Pantheon (Original Mix) | 121 | 5.0 |
| 18 | Bosknegra | Primavera (Original Mix) | 120 | 5.0 |


## Set 139. 139. Cumple Zorro · 1 a 3 AM — 2h — 2026-09-21
**Armado:** 2026-09-30  
**Duracion:** 2.0h  
**Tracks:** 17  
**BPM range:** 119-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Luciano Scheffer | Boonlake (Original Mix) | 120 | 6.0 |
| 2 | Noraj Cue, John Woods | The Youth Substance (Original Mix) | 122 | 7.4 |
| 3 | Second Sine | Motor City (Sebastian Haas Remix)  | 123 | 6.1 |
| 4 | Luciano Lozz | Follow Me (Original Mix) | 125 | 6.5 |
| 5 | Agustin Pietrocola | Sizer (Original Mix) | 123 | 5.2 |
| 6 | Boxer | I'm Lighter With You (feat. GAALIA) (Extended Mix) | 123 | 5.7 |
| 7 | HANA, Ezequiel Arias | Go (Extended Mix) | 124 | 6.2 |
| 8 | Meriva, MATTIC (BR) | Piece of Hope (D-Nox & Kamilo Sanclemente Extended Remix) | 123 | 6.6 |
| 9 | Supacooks | Un Mundo En Paz (Extended Mix) | 122 | 7.1 |
| 10 | Mind Echoes | Unsafe Numbers (Original Mix) | 121 | 7.2 |
| 11 | Quivver | Visitor (Original Mix) | 124 | 6.2 |
| 12 | Che Jose | THE VOID (Extended) | 124 | 6.3 |
| 13 | Andrew Bayer | Immortal Lover (8kays Extended Mix) | 125 | 6.3 |
| 14 | Kamilo Sanclemente | Fragma (GORKIZ Remix) | 123 | 7.5 |
| 15 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 7.9 |
| 16 | Zakem | When We Meet (Original Mix) | 120 | 8.9 |
| 17 | Andy Moor & Adam White | The Whiteroom (feat. Whiteroom) [Marsh Extended Mix] | 125 | 8.5 |


## Set 141. 141. Cumple Zorro · 3 a 5 AM — 2h — 2026-09-22
**Armado:** 2026-10-01  
**Duracion:** 2.0h  
**Tracks:** 17  
**BPM range:** 119-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Ignacio Salgado, Ezequiel Perini | Modul8 (Sacha Rener Remix) | 123 | 6.0 |
| 2 | Rockka | Initiation | 123 | 5.8 |
| 3 | ALLKNIGHT | If Here Was Forever (feat. MØØNE) (Extended Mix) | 124 | 7.6 |
| 4 | KYOTTO | Knock Knock | 121 | 6.1 |
| 5 | Jamie Stevens | Neofine (Original Mix) | 124 | 6.1 |
| 6 | Cendryma | Wakefeld (Original Mix) | 122 | 7.6 |
| 7 | Robag Wruhme | Ratibor Numida (Original Mix) | 126 | 5.2 |
| 8 | 8Kays | Waves (John Digweed & Nick Muir Remix) | 125 | 5.3 |
| 9 | Maezbi, Nicolas Viana | Smooth (Original Mix) | 123 | 6.8 |
| 10 | Ruben Karapetyan | 1982 (Matthew Sona Extended Mix) | 121 | 7.1 |
| 11 | Paul Thomas | Jumbo (Jamie Stevens Remix) | 124 | 6.1 |
| 12 | Andy Moor & Adam White | The Whiteroom (feat. Whiteroom) [Marsh Extended Mix] | 125 | 8.5 |
| 13 | UnbrokenOne | Wilderness (Original Mix) | 122 | 6.2 |
| 14 | Maze 28 | Superbloom | 122 | 6.5 |
| 15 | Melodiam (AR) | Words Are Weapons (Original Mix) | 122 | 6.3 |
| 16 | Kamilo Sanclemente, Dabeat | Vekants | 124 | 7.0 |
| 17 | Just Her | Floating Clouds (Original Mix) | 124 | 6.2 |


## Set 140. 140. Cumple Zorro · Warm · 23 a 1 AM — 2h — 2026-09-22
**Armado:** 2026-09-30  
**Duracion:** 2.0h  
**Tracks:** 17  
**BPM range:** 117-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Parra for Cuva | Juri (Original Mix) | 118 | 4.1 |
| 2 | Artic White | Futuro Infinito (Extended Mix) | 122 | 8.0 |
| 3 | Fulltone, Izhevski | Orange Gardens (Original Mix)  | 122 | 8.0 |
| 4 | Maze 28 | Mindloop (Original Mix) | 120 | 5.8 |
| 5 | Cendryma | Pure Junction (Berdu Remix) | 120 | 5.9 |
| 6 | Gorje Hewek, Molac, Dulus | Astro World (Original Mix) | 120 | 6.0 |
| 7 | Gai Barone | Fractals (Nicolas Viana Extended Remix) | 121 | 6.0 |
| 8 | Roy Rosenfeld | Forgotten (Extended) | 124 | 6.2 |
| 9 | Tim Green, Sébastien Léger | Duel | 124 | 7.1 |
| 10 | Amber Long, Hot Tuneik | Peace Within (Original Mix) | 122 | 7.3 |
| 11 | Simon Vuarambon | Lazos (Original Mix) | 120 | 6.4 |
| 12 | Grance & Soulmac | Happy Incident (Ale Russo Remix) | 120 | 6.9 |
| 13 | Sebastien Leger | Ariana | 122 | 6.9 |
| 14 | Augusto Dassano | Agorim | 120 | 7.5 |
| 15 | Tim Green | Minds (Original Mix) | 122 | 6.5 |
| 16 | Just Her | Secrets (Original Mix) | 125 | 4.6 |
| 17 | Kostya Outta, Liam Garcia | If I Win (Cosmonaut Extended Remix) | 123 | 6.3 |


## Set 142. 142. Cumple Zorro · Warm Colorido · 23 a 1 AM — 2h — 2026-09-22
**Armado:** 2026-09-30  
**Duracion:** 2.0h  
**Tracks:** 17  
**BPM range:** 117-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Parra for Cuva | Juri (Original Mix) | 118 | 4.1 |
| 2 | Lee Burridge, Lost Desert | April Fools (Extended Mix) | 122 | 7.8 |
| 3 | Dion Paola (AUS) | Galaxy (Facundo Sval Remix) | 122 | 6.9 |
| 4 | Cendryma | Pure Junction (Berdu Remix) | 120 | 5.9 |
| 5 | Gorje Hewek, Molac, Dulus | Astro World (Original Mix) | 120 | 6.0 |
| 6 | Simon Vuarambon | Lazos (Original Mix) | 120 | 6.4 |
| 7 | Maze 28 | Mindloop (Original Mix) | 120 | 5.8 |
| 8 | Grance & Soulmac | Happy Incident (Ale Russo Remix) | 120 | 6.9 |
| 9 | Tom Bryder | Vector (Original Mix) | 123 | 7.3 |
| 10 | Paul Deep (AR) | Tique (Original Mix) | 123 | 6.9 |
| 11 | Paul Deep AR & Luciano Lozz | Create | 123 | 6.9 |
| 12 | Ruben Karapetyan | The Ways (Kamilo Sanclemente Extended Mix) | 123 | 6.4 |
| 13 | Melodiam (AR) | Molicocha (Extended Mix) | 123 | 6.1 |
| 14 | Nora En Pure | Spring Embers (Extended Mix) | 122 | 6.7 |
| 15 | Dabeat, Kamilo Sanclemente | Incense (Original Mix) | 123 | 6.8 |
| 16 | Tim Green | Monster It (Original Mix)  | 124 | 7.6 |
| 17 | Kostya Outta, Liam Garcia | If I Win (Cosmonaut Extended Remix) | 123 | 6.3 |


## Set 143. 143. Cumple Zorro · Colorido · 1 a 3 AM — 2h — 2026-09-22
**Armado:** 2026-09-30  
**Duracion:** 0h  
**Tracks:** 22  
**BPM range:** 100-140  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | HANA, Ezequiel Arias | Go (Extended Mix) | 124 | 6.2 |
| 2 | Alex Kennon | Last Call (Karmon Remix) | 122 | 6.3 |
| 3 | Lane 8, Sultan + Shepard | The Little Mushroom That Got Away (Extended Mix) | 122 | 6.6 |
| 4 | Wailey | Droplets (Taylan Remix) | 122 | 5.3 |
| 5 | Durante | Portal Six (Extended Mix) | 124 | 5.9 |
| 6 | Andre Moret | One World (Extended Mix) | 122 | 5.6 |
| 7 | Greg Ochman | The Silver Lily (Original Mix) | 120 | 5.5 |
| 8 | COQUEIT | Lost in My Head (Original Mix) | 122 | 6.2 |
| 9 | Dmitry Molosh | The Moon Lights the Way (Original Mix) | 122 | 7.0 |
| 10 | Ruben Karapetyan | The Ways (Extended Mix) | 123 | 5.5 |
| 11 | Rockka | Amnesia (Fuenka Remix) | 123 | 7.2 |
| 12 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 7.9 |
| 13 | Jeff Ozmits, Miguel Ante | Crossing the Styx (DJ Ruby Extended Remix) | 123 | 7.9 |
| 14 | Maze 28 | Leave the World Behind (Original Mix) | 122 | 7.9 |
| 15 | Rezident, Kate Morgan | Muse feat. Kate Morgan (L.GU. Extended Mix) | 125 | 7.1 |
| 16 | Kamilo Sanclemente | Fragma (GORKIZ Remix) | 123 | 7.5 |
| 17 | Rabiee Ahmad, Hassan Tariq Khan | In Another Time (Original Mix) | 122 | 7.5 |
| 18 | Abity | Roots (Gai Barone Remix) | 122 | 6.6 |
| 19 | Agustin Pietrocola | Sizer (Original Mix) | 123 | 5.2 |
| 20 | Hobin Rude | Fading Silhouettes (Pierre Sebastiano Remix) | 122 | 8.0 |
| 21 | Rauschhaus, Cary Crank | Bekal (Extended Mix) | 120 | 7.9 |
| 22 | Sébastien Léger, Lost Miracle | Dodonpachi (Original Mix) | 122 | 7.0 |


## Set 144. 144. Cumple Zorro · Colorido · 3 a 5 AM — 2h — 2026-09-22
**Armado:** 2026-10-01  
**Duracion:** 2.0h  
**Tracks:** 17  
**BPM range:** 119-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Artic White | Flashback (Extended Mix) | 123 | 6.7 |
| 2 | Blake Toth, Kilowatt | Valhalla Sonique (Extended Mix) | 126 | 5.4 |
| 3 | Tobi Amuchastegui | Voices (Original Mix) | 123 | 6.9 |
| 4 | Zankee Gulati | Plonker (Original Mix) | 122 | 5.2 |
| 5 | Beswerda | All for Me (Original Mix) | 124 | 5.8 |
| 6 | Teleport-X, DILE (LK) | Sick of All (Redspace Remix) | 124 | 6.9 |
| 7 | Elliot Moriarty | Only Time (Original Mix) | 123 | 6.0 |
| 8 | Paul Thomas | Jumbo (Jamie Stevens Remix) | 124 | 6.1 |
| 9 | Tali Muss, Vakabular | Uniqueness (D-Nox & Ed Steele Remix) | 125 | 6.7 |
| 10 | Blancah, NeoClassic | Travessia (Hicky & Kalo Remix) | 123 | 7.9 |
| 11 | Lipa Tazzioli | Complex Society (Original Mix) | 122 | 5.9 |
| 12 | Ramsay | Call My Name (Cetrini Remix) | 123 | 6.3 |
| 13 | Colyn | The Future Is the Past | 126 | 6.6 |
| 14 | This Guy Ben | The Drip (Original Mix) | 124 | 6.8 |
| 15 | Estiva, Cosmosky | Ecstasy (Extended Mix) | 124 | 6.8 |
| 16 | Gorje Hewek | My Heart (Original Mix) | 124 | 6.1 |
| 17 | Hermanez | Twenty Four | 122 | 6.3 |


## Set 145. 145. Cumple Zorro · Vecindario · 1 a 3 AM — 2h — 2026-09-22
**Armado:** 2026-09-30  
**Duracion:** 2.0h  
**Tracks:** 17  
**BPM range:** 119-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Tim Green | You Look Good (Original Mix) | 123 | 7.5 |
| 2 | Gru V & Rockka | Closer (Fourthstate Remix) | 122 | 7.8 |
| 3 | Rockka | Elevation | 122 | 6.2 |
| 4 | Francisco Manrique | The Fine Universe (Cendryma Remix) | 121 | 7.7 |
| 5 | Sebastien Leger, Tim Green | Iso (Original Mix)  | 121 | 7.3 |
| 6 | Maze 28 | Fogbows | 122 | 6.3 |
| 7 | Freedo Mosho | Paradise Lost (Maze 28 Reform) | 122 | 6.6 |
| 8 | Kamilo Sanclemente | Orb (Original Mix) | 121 | 7.0 |
| 9 | Alex O'Rion, Antrim | Imagine (Original Mix)  | 120 | 6.6 |
| 10 | Sebastian Busto | December (Zankee Gulati Remix) | 122 | 7.3 |
| 11 | Matt Oliver & Mind Echoes | Reborn Crystal (Original Mix) | 121 | 7.6 |
| 12 | Taylan | Earthbound (Andre Moret Remix) | 120 | 6.7 |
| 13 | Tripswitch | Box Fresh (Emi Galvan Remix) | 122 | 6.8 |
| 14 | Dilby, Amine K (Moroko Loko) | Confusion (Extended Mix) | 124 | 6.2 |
| 15 | Maze 28 | Great Attractor (Ruben Karapetyan Remix) | 124 | 7.5 |
| 16 | Rockka | Amnesia (Fuenka Remix) | 123 | 7.2 |
| 17 | Just Her, AmyElle | Feel Again (Original Mix) | 126 | 6.8 |


## Set 146. 146. Maze 28 + Cendryma · Vecindario — 3h — 2026-09-22
**Armado:** 2026-09-30  
**Duracion:** 3.0h  
**Tracks:** 25  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Tim Green | Coriolis (Original Mix)  | 122 | 8.0 |
| 2 | Lost Desert & Hermanez | Jinx (Volen Sentir Pure Magic Healing) | 122 | 7.1 |
| 3 | Taylan, Shani Zen | Geronimo (Kamilo Sanclemente Remix) | 122 | 6.3 |
| 4 | Simos Tagias | Melted Pot (Maze 28 Remix) | 122 | 6.7 |
| 5 | Mathew Jonson & Quenum | Cyclops (Tim Green Remix) | 120 | 6.6 |
| 6 | Patch Park | Hips and Dips (Zankee Gulati Remix) | 121 | 6.2 |
| 7 | Chelakhov | Searching (Gero Pellizzon Remix) | 122 | 6.2 |
| 8 | Cary Crank | Deep Voltage (NOIYSE PROJECT Remix) | 122 | 6.3 |
| 9 | Hobin Rude | Until the End of Time | 122 | 6.6 |
| 10 | Cendryma | Focus Bend (Extended Mix) | 122 | 7.0 |
| 11 | Rockka | Operator (Maze 28 Remix) | 122 | 7.2 |
| 12 | Cary Crank | Inner Atlas (Kyotto Remix) | 122 | 6.8 |
| 13 | Forty Cats | Ledokol (Cid Inc. Remix)  | 122 | 6.7 |
| 14 | Rockka | Subversion | 123 | 6.5 |
| 15 | Rockka | Amnesia (Fuenka Remix) | 123 | 7.2 |
| 16 | Cendryma | Wakefeld (Original Mix) | 122 | 7.6 |
| 17 | Cary Crank | Deep Forest (Extended Mix) | 122 | 7.9 |
| 18 | Cendryma | Evasive (Extended Mix) | 121 | 7.4 |
| 19 | Maze 28 | Leave the World Behind (Original Mix) | 122 | 7.9 |
| 20 | Mind Echoes | Answers (Original Mix) | 120 | 6.6 |
| 21 | Hobin Rude | The Only Thing That Matters | 120 | 7.2 |
| 22 | Guy J | Million Years from Now | 123 | 6.3 |
| 23 | Maze 28 | Great Attractor (Ruben Karapetyan Remix) | 124 | 7.5 |
| 24 | Guy Mantzur, Kamilo Sanclemente | The Future is in the Past (Original Mix) | 124 | 6.6 |
| 25 | Kabi (AR) | Rainbow (Extended Mix) | 125 | 6.6 |


## Set 147. 147. Cumple Zorro · Peak Maze 28 · 1 a 2:30 AM — 1.5h — 2026-09-23
**Armado:** 2026-09-30  
**Duracion:** 1.5h  
**Tracks:** 13  
**BPM range:** 120-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Kostya Outta, Frameloue | Altitude (Feat. Frameloue Extended Mix) | 122 | 6.6 |
| 2 | Maze 28 | Aer8 (Juan Pablo Torrez Remix) | 122 | 7.0 |
| 3 | Paul Deep AR | Milo | 123 | 7.1 |
| 4 | Niko Ava | Freedom (Original Mix) | 122 | 7.3 |
| 5 | Lost Desert | When Sun Rises (Volen Sentir Extended Remix) | 124 | 6.9 |
| 6 | Emi Galvan | Everlong (Ruben Karapetyan Remix) | 123 | 7.8 |
| 7 | NOIYSE PROJECT, Hernan Cattaneo, Jamie Stevens | Remember Me - Hernan Cattaneo & Jamie Stevens Remix | 122 | 8.2 |
| 8 | Sebastien Leger | Lava (Original Mix) | 122 | 6.3 |
| 9 | Sounom & Sagou | Everyday Moments (Kamilo Sanclemente Remix) | 122 | 7.8 |
| 10 | Fordal | Luminize (Original Mix) | 124 | 7.5 |
| 11 | Kamilo Sanclemente | Astronauts Nightmares (DJ Ruby Extended Remix) | 123 | 7.4 |
| 12 | Praise (BR) | Kiwi (Extended Mix) | 123 | 7.3 |
| 13 | Supacooks | Un Mundo En Paz (Serious Dancers Extended Remix) | 124 | 7.5 |


## Set 148. 148. Housero Progresivo · 1 a 3 AM — 2h — 2026-09-28
**Armado:** 2026-10-01  
**Duracion:** 2.0h  
**Tracks:** 16  
**BPM range:** 119-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Aman Anand & Da Luka | Mythical Creatures (Golan Zocher & Kamilo Sanclemente Remix) | 122 | 6.3 |
| 2 | Envotion | Adrift (Sebastian Sellares Remix) | 123 | 6.6 |
| 3 | Paul Thomas, Maze 28 | Abundance (Original Mix) | 123 | 7.1 |
| 4 | COQUEIT | Dock (Original Mix) | 122 | 7.0 |
| 5 | Digital Mess, Astral Base | Turbulence (Extended Mix) | 121 | 6.3 |
| 6 | Maze 28 | Fogbows | 122 | 6.3 |
| 7 | Rauschhaus | Morning Walks | 121 | 7.1 |
| 8 | MuscleDyke | Dark White (Mind Echoes Remix) | 122 | 6.5 |
| 9 | Gonzalo Cotroneo | Thrill (Extended Mix) | 122 | 7.2 |
| 10 | Wassu | From Here (feat. MØØNE) (Extended Mix) | 124 | 7.0 |
| 11 | Hernan Cattaneo, Khen | Rogelito (Original Mix) | 123 | 6.2 |
| 12 | Mindlancholic | Mirages in Space | 123 | 6.9 |
| 13 | Albuquerque, Anonimat | Like First Time Flight (Extended Mix) | 123 | 7.0 |
| 14 | Rabiee Ahmad, Hassan Tariq Khan | Terminator (Original Mix) | 123 | 6.2 |
| 15 | Ziger & Mind Conspiracy | The Light (Original) | 122 | 6.5 |
| 16 | Marsh, Simon Doty | Touch The Sky (Extended Mix) | 124 | 6.8 |


## Set 149. 149. Cumple Zorro · Colorido · version corta — 1h30 — 2026-09-22
**Armado:** 2026-10-01  
**Duracion:** 0h  
**Tracks:** 19  
**BPM range:** 100-140  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Lane 8, Sultan + Shepard | The Little Mushroom That Got Away (Extended Mix) | 122 | 6.6 |
| 2 | Andre Moret | One World (Extended Mix) | 122 | 5.6 |
| 3 | Ruben Karapetyan | The Ways (Extended Mix) | 123 | 5.5 |
| 4 | COQUEIT | Lost in My Head (Original Mix) | 122 | 6.2 |
| 5 | Greg Ochman | The Silver Lily (Original Mix) | 120 | 5.5 |
| 6 | Andre Moret | Aria (Gorkiz Remix) | 125 | 5.8 |
| 7 | Emi Galvan | Mily (Original Mix) | 122 | 5.9 |
| 8 | Ilias Katelanos, Plecta, Anonimat | Coaster (Durante Remix) | 124 | 6.3 |
| 9 | DJ Ruby | Goldrake (Original Mix) | 123 | 4.8 |
| 10 | Maze 28 | Fogbows | 122 | 6.3 |
| 11 | Rockka | Amnesia (Fuenka Remix) | 123 | 7.2 |
| 12 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 7.9 |
| 13 | Kamilo Sanclemente | Fragma (GORKIZ Remix) | 123 | 7.5 |
| 14 | Ruben Karapetyan | Perceptual Isolation (Original Mix) | 121 | 6.2 |
| 15 | Rabiee Ahmad, Hassan Tariq Khan | In Another Time (Original Mix) | 122 | 7.5 |
| 16 | Agustin Pietrocola | Sizer (Original Mix) | 123 | 5.2 |
| 17 | Ruben Karapetyan | Between the Lines (Original Mix) | 122 | 6.5 |
| 18 | Hobin Rude | Fading Silhouettes (Pierre Sebastiano Remix) | 122 | 8.0 |
| 19 | Sébastien Léger, Lost Miracle | Dodonpachi (Original Mix) | 122 | 7.0 |


## Set 150. 150. Housero + Colorido · lo mejor de los dos — 2h — 2026-10-01
**Armado:** 2026-10-02  
**Duracion:** 0h  
**Tracks:** 18  
**BPM range:** 100-140  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Paul Thomas, Maze 28 | Abundance (Original Mix) | 123 | 7.1 |
| 2 | Agustin Pietrocola | Sizer (Original Mix) | 123 | 5.2 |
| 3 | Rabiee Ahmad, Hassan Tariq Khan | In Another Time (Original Mix) | 122 | 7.5 |
| 4 | Hobin Rude | Fading Silhouettes (Pierre Sebastiano Remix) | 122 | 8.0 |
| 5 | Ruben Karapetyan | Midnight Current (Original Mix) | 121 | 6.2 |
| 6 | Kostya Outta | Seguro (Paul James Nolan Remix) | 122 | 7.0 |
| 7 | Maze 28 | Fogbows | 122 | 6.3 |
| 8 | Ilias Katelanos, Plecta, Anonimat | Coaster (Durante Remix) | 124 | 6.3 |
| 9 | Cendryma | Pure Junction (Berdu Remix) | 120 | 5.9 |
| 10 | Cendryma | Wakefeld (Original Mix) | 122 | 7.6 |
| 11 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 7.9 |
| 12 | Rockka | Amnesia (Fuenka Remix) | 123 | 7.2 |
| 13 | Gonzalo Cotroneo | Thrill (Extended Mix) | 122 | 7.2 |
| 14 | Andre Moret | Aria (Gorkiz Remix) | 125 | 5.8 |
| 15 | Greg Ochman | The Silver Lily (Original Mix) | 120 | 5.5 |
| 16 | Wailey | Droplets (Taylan Remix) | 122 | 5.3 |
| 17 | Wassu | From Here (feat. MØØNE) (Extended Mix) | 124 | 7.0 |
| 18 | Marsh, Simon Doty | Touch The Sky (Extended Mix) | 124 | 6.8 |


## Set 151. 151. Catalogo del DJ · 3h — 2026-10-01
**Armado:** 2026-10-01  
**Duracion:** 0h  
**Tracks:** 45  
**BPM range:** 100-140  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Paul Thomas, Maze 28 | Abundance (Original Mix) | 123 | 7.1 |
| 2 | Jonas Saalbach | Keep Spirit High (Original Mix) | 123 | 7.7 |
| 3 | Agustin Pietrocola | Sizer (Original Mix) | 123 | 5.2 |
| 4 | Ra Duh | Ganymede (Original Mix)  | 121 | 6.1 |
| 5 | Rabiee Ahmad, Hassan Tariq Khan | In Another Time (Original Mix) | 122 | 7.5 |
| 6 | Hobin Rude | Fading Silhouettes (Pierre Sebastiano Remix) | 122 | 8.0 |
| 7 | COQUEIT | Dock (Original Mix) | 122 | 7.0 |
| 8 | Samuel (LK) | Pulse (Casnik Remix) | 123 | 6.8 |
| 9 | Kamilo Sanclemente | Fragma (GORKIZ Remix) | 123 | 7.5 |
| 10 | Maze 28 | Fogbows | 122 | 6.3 |
| 11 | Cendryma | Pure Junction (Berdu Remix) | 120 | 5.9 |
| 12 | Cendryma | Wakefeld (Original Mix) | 122 | 7.6 |
| 13 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 7.9 |
| 14 | Rockka | Amnesia (Fuenka Remix) | 123 | 7.2 |
| 15 | Gonzalo Cotroneo | Dark Rain (Extended Mix) | 121 | 7.3 |
| 16 | Gonzalo Cotroneo | Thrill (Extended Mix) | 122 | 7.2 |
| 17 | MuscleDyke | Dark White (Mind Echoes Remix) | 122 | 6.5 |
| 18 | Andre Moret | Aria (Gorkiz Remix) | 125 | 5.8 |
| 19 | Wailey | Droplets (Taylan Remix) | 122 | 5.3 |
| 20 | Wassu | From Here (feat. MØØNE) (Extended Mix) | 124 | 7.0 |
| 21 | Marsh, Simon Doty | Touch The Sky (Extended Mix) | 124 | 6.8 |
| 22 | Ziger & Mind Conspiracy | The Light (Original) | 122 | 6.5 |
| 23 | Durante | Never B Alone (Extended Mix) | 123 | 6.0 |
| 24 | Lane 8, Sultan + Shepard | The Little Mushroom That Got Away (Extended Mix) | 122 | 6.6 |
| 25 | Sunchain | Neurosonic Drift (Taylan Extended Mix) | 121 | 6.4 |
| 26 | COQUEIT | Lost in My Head (Original Mix) | 122 | 6.2 |
| 27 | Andre Moret | One World (Extended Mix) | 122 | 5.6 |
| 28 | Greg Ochman | The Silver Lily (Original Mix) | 120 | 5.5 |
| 29 | Ruben Karapetyan | The Ways (Extended Mix) | 123 | 5.5 |
| 30 | Emi Galvan | Mily (Original Mix) | 122 | 5.9 |
| 31 | Ilias Katelanos, Plecta, Anonimat | Coaster (Durante Remix) | 124 | 6.3 |
| 32 | Subconscious Tales | Magnectares (Kasper Koman Remix)  | 120 | 5.7 |
| 33 | Jamie Stevens, GMJ, Matter, Wilma (AU) | Tell You Later feat. Wilma (AU) (GMJ & Matter Remix) | 122 | 5.6 |
| 34 | Paul Hazendonk | One Plus One (Jack Lazarus Club Mix) | 122 | 6.7 |
| 35 | Togni, Mind Echoes | Questions (Original Mix) | 120 | 6.9 |
| 36 | Togni, Rodrives | Existence (Original Mix) | 121 | 5.4 |
| 37 | Anton Make | You My Rhythm (Original Mix) | 121 | 5.9 |
| 38 | Nick Stoynoff, Gai Barone | Post Boutique (Original Mix) | 123 | 5.5 |
| 39 | Zuccasam | Come Home (Dowden Remix) | 121 | 5.9 |
| 40 | Gorkiz & Mind Echoes | Without Your Noose (Paul Arcane Remix) | 122 | 5.9 |
| 41 | Kasper Koman | Rocking Boat | 123 | 5.8 |
| 42 | Molac | Crisopea (Ilias Katelanos & Plecta Remix) | 124 | 5.2 |
| 43 | Sinkix | Hyperion (Original Mix) | 122 | 6.6 |
| 44 | Maze 28 | Constant Daydream (TEELCO Remix) | 122 | 6.9 |
| 45 | Cristoph, Franky Wah, Artche | The World You See (Original Mix)  | 126 | 7.8 |


## Set 152. 152. Housero Nuevo · modelo Fogbows + From Here — 1h52 — 2026-10-02
**Armado:** 2026-10-02  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Choopie, Golan Zocher | Alush (Leon Lobato Remix)  | 120 | 7.0 |
| 2 | Moritz | Echoes | 122 | 5.2 |
| 3 | Dabeat, Kamilo Sanclemente | Seriously (Original Mix) | 122 | 7.2 |
| 4 | Simos Tagias | Atom (Not Demure Remix) | 122 | 7.8 |
| 5 | Hobin Rude | 33rd (Ric Niels & Dowden Remix) | 121 | 6.2 |
| 6 | Andrés Moris | Rust (Rockka Remix) | 123 | 7.0 |
| 7 | Ismail M & Redspace | Know Yourself | 120 | 6.3 |
| 8 | Redspace, Al Park | Trends (Original Mix) | 122 | 6.4 |
| 9 | NekliFF, Rafael Cerato | Marrakesh (Kasper Koman Remix) | 121 | 6.2 |
| 10 | Digital Mess, Meeting Molly | Binauraler (Original Mix) | 120 | 6.8 |
| 11 | Cendryma | Raven (Extended Mix) | 121 | 6.4 |
| 12 | Abity, Ewan Rill | La Cumbre (Original Mix) | 123 | 6.2 |
| 13 | STEREO MUNK, Mind Echoes | Field of Steel (Original Mix) | 122 | 6.5 |
| 14 | Unusual Soul | Exhale  | 120 | 5.7 |
| 15 | Malou, Ben Bohmer | Lost In Mind (Volen Sentir Extended Vision) | 124 | 5.4 |
| 16 | Ric Niels | Morning Dew (Original Mix) | 120 | 5.0 |
| 17 | D-Nox, Lonya, DJ Zombi, Amber Long | Red Light Stories (Original Mix)  | 122 | 6.6 |
| 18 | Tripswitch | Dose (Hernan Cattaneo & Marcelo Vasami Remix) | 120 | 6.4 |

