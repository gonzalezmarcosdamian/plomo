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
| 8 | Kamilo Sanclemente | Anagram (Mayro Extended Remix) | 123 | 5.5 |
| 9 | Jon Towell | 49 Miles (Original Mix) | 123 | 5.5 |
| 10 | WhoMadeWho & Blue Hawaii | Kiss Me Hard (Adam Ten Remix) | 123 | 5.5 |
| 11 | Supacooks, Bondarev | Activator (Original Mix) | 123 | 5.5 |
| 12 | Blake Jarrell | Twenty Miami's Ago (Cendryma Extended Mix) | 122 | 5.5 |
| 13 | Pedro Capelossi, Aeikus | Topaz (Original Mix) | 123 | 5.5 |
| 14 | Remcord | Out Of It (Original Mix) | 123 | 5.5 |
| 15 | Guy J | Silver Lake (Original Mix) | 122 | 5.5 |
| 16 | Kamilo Sanclemente | Astronauts Nightmares (DJ Ruby Extended Remix) | 123 | 5.5 |
| 17 | Ezequiel Arias | Passenger (Original Mix) | 122 | 5.5 |
| 18 | Jody Wisternoff, PROFF, James Grant, Siobhan Wilson, Takeshi Furukawa | Mui (Ezequiel Arias Extended Mix) | 125 | 6.0 |


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
**Tracks:** 26  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Gai Barone, Luke Brancaccio, Kiki Cave | All I Need (Hernan Cattaneo & Mercurio remix) | 119 | 3.5 |
| 2 | Panorama Channel | Kinly Estellar | 120 | 5.0 |
| 3 | Cornucopia | Early Morning (Original Mix) | 118 | 3.5 |
| 4 | Chris Isaak | Wicked Game (Mass Digital Remix) | 119 | 3.5 |
| 5 | Cid Inc & Dmitry Molosh | Impending Storm | 120 | 5.0 |
| 6 | Antrim & Juan Fernandez | Hide and Seek (Ric Niels Remix) | 120 | 5.0 |
| 7 | Juan Deminicis | Under Control (Original Mix) | 121 | 5.0 |
| 8 | Tantum | Out Of Nowhere (Original Mix) | 121 | 5.0 |
| 9 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 5.0 |
| 10 | Hermanez | Eight Years (Original Mix) | 122 | 5.5 |
| 11 | Hobin Rude | Seraph (Liam Garcia Remix) | 120 | 5.0 |
| 12 | Fer Torti | Star Trip | 120 | 5.0 |
| 13 | Jon Towell | 49 Miles (Original Mix) | 123 | 5.5 |
| 14 | Of Norway | I Miss You (Sentre Remix) | 123 | 5.5 |
| 15 | Dmitry Molosh | Bird Flight (Original Mix) | 120 | 5.0 |
| 16 | Sebastian Sellares | Limbo (Extended Mix) | 120 | 5.0 |
| 17 | Nicolas Rada | Glasgow (Original Mix) | 122 | 5.5 |
| 18 | Michael A | Hunting Flowers (Radio Edit) | 120 | 5.0 |
| 19 | Pedro Capelossi, Aeikus | Topaz (Original Mix) | 123 | 5.5 |
| 20 | Remcord | Out Of It (Original Mix) | 123 | 5.5 |
| 21 | WhoMadeWho & Blue Hawaii | Kiss Me Hard (Adam Ten Remix) | 123 | 5.5 |
| 22 | Einmusik, Dirty Doering | Centaurio | 125 | 6.0 |
| 23 | D-Nox, Stereo Underground | Dolby (Original Mix) | 125 | 6.0 |
| 24 | Supacooks, Bondarev | Activator (Original Mix) | 123 | 5.5 |
| 25 | Benja Molina | Aura (Original Mix) | 123 | 5.5 |
| 26 | John Cosani | Snano (Original Mix) | 123 | 5.5 |


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
| 1 | Estiva | What Is Love (Extended Mix)  | 124 | 6.0 |
| 2 | Nox Vahn | When I'm With You (Extended Mix)  | 123 | 5.5 |
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
| 1 | Solis [US] | Una Volta (Extended Mix) | 123 | 5.5 |
| 2 | Hernan Cattaneo & Soundexile | Astron (Davi Remix) | 122 | 5.5 |
| 3 | Francisco Manrique | The Fine Universe (Mike Kohl Remix) | 122 | 5.5 |
| 4 | Marcelo Vasami | Shades Of Blue (Original Mix) | 122 | 5.5 |
| 5 | Greta Meier | Enlightenment (Poli Siufi Remix) | 122 | 5.5 |
| 6 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 5.5 |
| 7 | Cary Crank | Deep Forest (Extended Mix) | 122 | 5.5 |
| 8 | Jakatta | American Dream (PROFF Extended Interpretation) | 122 | 5.5 |
| 9 | Mike Griego | Antidote | 123 | 5.5 |
| 10 | Andy Moor & Adam White | The Whiteroom (feat. Whiteroom) [Marsh Extended Mix] | 125 | 6.0 |
| 11 | Ric Niels | Invasion | 123 | 5.5 |
| 12 | Maze 28 | Leave the World Behind (Original Mix) | 122 | 5.5 |


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
| 2 | Kebin Van Reeken | Endurance (Original Mix) | 121 | 5.0 |
| 3 | Rauschhaus, Cary Crank | Tapestry of Perception (Extended Mix) | 120 | 5.0 |
| 4 | Chicola, Guy Mantzur | Galactica (Original Mix) | 122 | 5.5 |
| 5 | Kamilo Sanclemente, Andre Moret, Mariusso | Atenea (HAFT Remix) | 122 | 5.5 |
| 6 | Emi Galvan | Alfa Zeta (Original Mix) | 120 | 5.0 |
| 7 | Kasper Koman | Loco Motif (Tantum Remix) | 121 | 5.0 |
| 8 | Cendryma | Dividing Parts (Original Mix) | 121 | 5.0 |
| 9 | Emi Galvan | Mily (Original Mix) | 122 | 5.5 |
| 10 | Quivver, Dave Seaman | The Water's Edge (Original Mix) | 122 | 5.5 |
| 11 | Ezequiel Arias | Mad Man - Original Mix | 123 | 5.5 |
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
| 2 | Mike Rish | Election Day (Original Mix) | 122 | 5.5 |
| 3 | Guy Mantzur, Khen | Shine Tomorrow (Original Mix) | 123 | 5.5 |
| 4 | Roy Rosenfeld | Toco | 124 | 6.0 |
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
| 1 | Ezequiel Arias, Sebastian Sellares | Alba (Extended Mix) | 124 | 6.0 |
| 2 | Emi Galvan | Dopamine (Forniva Remix) | 123 | 5.5 |
| 3 | Hernan Cattaneo & Soundexile | Pick Up | 122 | 5.5 |
| 4 | Kamilo Sanclemente, Andre Moret | Mirage (Original Mix) | 122 | 5.5 |
| 5 | Durante, PaulWetz | Evaporate ft. PaulWetz (Original Mix) | 120 | 5.0 |
| 6 | Cid Inc., Dmitry Molosh | Aquamarine (Original Mix) | 122 | 5.5 |
| 7 | Mike Rish | Drifter (Original Mix) | 120 | 5.0 |
| 8 | Durante, Amtrac | Gather (Original Mix) | 122 | 5.5 |
| 9 | Kamilo Sanclemente, Phillipe Lois | Acid Dreams (Original Mix) | 124 | 6.0 |
| 10 | D-Nox, Andre Moret | Brisa (Extended Mix) | 123 | 5.5 |
| 11 | Cendryma, THMS (US) | Moonflare (Extended Mix) | 121 | 5.0 |
| 12 | Hernan Cattaneo & Soundexile | Astron (Davi Remix) | 122 | 5.5 |
| 13 | Rockka | Operator (Maze 28 Remix) | 122 | 5.5 |
| 14 | Gorkiz & Matt Oliver | Big Bottom (Kebin Van Reeken Reinterpretation) | 121 | 5.0 |
| 15 | Ric Niels | Invasion | 123 | 5.5 |
| 16 | Cendryma | Evasive (Extended Mix) | 121 | 5.0 |
| 17 | Greta Meier | Enlightenment (Gaston Sosa Remix) | 122 | 5.5 |
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
| 3 | Emi Galvan | I Wish (Original Mix) | 123 | 5.5 |
| 4 | Guy J | Karma (Original Mix) | 122 | 5.5 |
| 5 | Mike Rish | Dope Riddim (Original Mix) | 122 | 5.5 |
| 6 | GMJ, Matter, Zankee Gulati | Emerge (Original Mix) | 120 | 5.0 |
| 7 | Hobin Rude | Opposite (Original Mix) | 122 | 5.5 |
| 8 | Jamie Stevens, Kasey Taylor | Hocu Pocu (Original Mix) | 123 | 5.5 |
| 9 | Cendryma | Focus Bend (Tiefstone Remix) | 123 | 5.5 |
| 10 | Simon Vuarambon | Kaskazi | 122 | 5.5 |
| 11 | Tom Pavicich | About Her (Martin Fredes Remix) | 122 | 5.5 |
| 12 | Rauschhaus, GRAZZE | Canacona (Original Mix) | 121 | 5.0 |
| 13 | Kamilo Sanclemente | Orb (Original Mix) | 121 | 5.0 |
| 14 | Rockka | Amnesia (Fuenka Remix) | 123 | 5.5 |
| 15 | D-Nox, Andre Moret | Shine (Extended Mix) | 124 | 6.0 |
| 16 | Kasper Koman | Sinking Sky | 122 | 5.5 |
| 17 | Guy J | Surreal (Original Mix) | 121 | 5.0 |
| 18 | Emi Galvan | Trust (Original Mix) | 122 | 5.5 |


## Set 86. 86. Simon Vuarambon Style — Hipnotico
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hernan Cattaneo & Soundexile | Wind Down (Outro Mix) | 122 | 5.5 |
| 2 | Tali Muss | Istanbul (Original Mix) | 122 | 5.5 |
| 3 | Guy Mantzur, Roy Rosenfeld | Epika (Original Mix) | 120 | 5.0 |
| 4 | Mike Rish | Tú Attair (Original Mix) | 119 | 3.5 |
| 5 | Hraach | Cosmic Drama (Original Mix) | 120 | 5.0 |
| 6 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 5.0 |
| 7 | Sebastien Leger, Roy Rosenfeld, Lost Miracle | Closer To You (Extended Mix) | 120 | 5.0 |
| 8 | Tom Pavicich | About Her (Unai Garcia Remix) | 121 | 5.0 |
| 9 | Ric Niels & Juan Buitrago | Glide | 123 | 5.5 |
| 10 | Melodiam (AR) | Dizzy (Extended Mix) | 122 | 5.5 |
| 11 | Kamilo Sanclemente | Theia | 122 | 5.5 |
| 12 | Hobin Rude | Nothing's Gonna Hurt You | 122 | 5.5 |
| 13 | Guy J | Placebo (Original Mix) | 122 | 5.5 |
| 14 | Kamilo Sanclemente | Just Come Back (Extended Mix) | 124 | 6.0 |
| 15 | Melodiam (AR) | Molicocha (Extended Mix) | 123 | 5.5 |
| 16 | Greta Meier, Maze 28 | Acceptance (Original Mix) | 122 | 5.5 |
| 17 | Kasper Koman | Hi (Cid Inc. Remix) | 122 | 5.5 |
| 18 | Julian Nates, Julieta Kühnle | Fever (Extended Mix) | 123 | 5.5 |


## Set 87. 87. Nick Warren Style — The Soundgarden
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Cendryma | Buildup Trap (Simos Tagias Remix) | 121 | 5.0 |
| 2 | Paul Deep (AR) | Melodramatic (Original Mix) | 122 | 5.5 |
| 3 | Leandro Murua, Martin Fredes | Mistakes (Original Mix) | 122 | 5.5 |
| 4 | Facundo Borras | Whispers from Dawn | 123 | 5.5 |
| 5 | Khen | Out Of A Dream (Original Mix) | 121 | 5.0 |
| 6 | Martin Fredes, Unai Garcia | The Artefact (Original Mix) | 120 | 5.0 |
| 7 | Rockka, Maze 28 | Mirage (Juan Ibanez Extended Mix) | 122 | 5.5 |
| 8 | Cendryma | Pure Junction (Berdu Remix) | 120 | 5.0 |
| 9 | Gorkiz, K Loveski | Echos Of Eons (Greenage Remix) | 122 | 5.5 |
| 10 | Hobin Rude | Nether (Original Mix) | 120 | 5.0 |
| 11 | Guy J | Silver Lake (Original Mix) | 122 | 5.5 |
| 12 | Dmitry Molosh | Bustle (Original Mix) | 120 | 5.0 |
| 13 | Melodiam (AR) | Martian | 120 | 5.0 |
| 14 | Rauschhaus | Morning Walks | 121 | 5.0 |
| 15 | Nick Warren | Freebird (Emi Galvan Remix) | 123 | 5.5 |
| 16 | Dmitry Molosh | The Moon Lights the Way (Original Mix) | 122 | 5.5 |
| 17 | Guy Mantzur, Kamilo Sanclemente | The Future is in the Past (Original Mix) | 124 | 6.0 |
| 18 | Rockka | The Fade (Dave Walker Remix) | 122 | 5.5 |


## Set 88. 88. Cordoba Progressive — Gai Barone Style
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Maze 28, Rockka | Corrosive | 122 | 5.5 |
| 2 | Ezequiel Arias | Sin Control (Extended Mix) | 124 | 6.0 |
| 3 | Kasey Taylor, Karl Pilbrow | Mount Epicon (Original Mix) | 125 | 6.0 |
| 4 | Anthony Pappa, Aubrey Fry | Itajai (Original Mix) | 125 | 6.0 |
| 5 | Emi Galvan | Reborn (Original Mix) | 124 | 6.0 |
| 6 | Dmitry Molosh, Michael A | Twelve Days (Original Mix) | 122 | 5.5 |
| 7 | Gai Barone | In the Blink of an Eye (Original Mix) | 122 | 5.5 |
| 8 | Antrim | Rescue | 122 | 5.5 |
| 9 | Michael A | Zero Dawn (Kebin Van Reeken Remix) | 121 | 5.0 |
| 10 | Melodiam (AR) | Repro Days (Original Mix) | 122 | 5.5 |
| 11 | Rockka | Subversion | 123 | 5.5 |
| 12 | Kamilo Sanclemente, Giovanny Aparicio | Redemtion (Original Mix) | 121 | 5.0 |
| 13 | Emi Galvan | Samsara | 122 | 5.5 |
| 14 | Paul Deep (AR) | Aeras (Original Mix) | 121 | 5.0 |
| 15 | Sebastian Sellares | Timeless Era (Extended Mix) | 122 | 5.5 |
| 16 | Nicolas Rada | Cascadia | 122 | 5.5 |
| 17 | Ruben Karapetyan, Maze 28 | Cosmic Dot | 123 | 5.5 |
| 18 | Andre Moret | Drift Whispers (Original Mix) | 123 | 5.5 |


## Set 89. 89. Argentina Peak Time
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 121-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Andre Moret | Gaxyda (Original Mix) | 122 | 5.5 |
| 2 | Kasey Taylor | Emerging From the Skyline (Original Mix) | 122 | 5.5 |
| 3 | Durante, Ezequiel Arias | Prisma (Original Mix) | 124 | 6.0 |
| 4 | Tiefstone, Das Pharaoh | Endless Summer (Extended Mix) | 122 | 5.5 |
| 5 | Ruben Karapetyan, Maze 28 | Cosmic Dot (The Wash Remix) | 121 | 5.0 |
| 6 | D-Nox & Beckers | Serenade (Doctor Dru Remix) | 122 | 5.5 |
| 7 | Kamilo Sanclemente | Show Me the Stars (Original Mix) | 121 | 5.0 |
| 8 | Simon Vuarambon & Tantum | Lake Of Fire | 122 | 5.5 |
| 9 | Cendryma | Override (Original Mix) | 122 | 5.5 |
| 10 | Guy J | Illusion (Original Mix) | 122 | 5.5 |
| 11 | Marcelo Vasami | Shades Of Blue (Original Mix) | 122 | 5.5 |
| 12 | Kamilo Sanclemente | Delusion (Original Mix) | 122 | 5.5 |
| 13 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 5.5 |
| 14 | NOIYSE PROJECT, Hernan Cattaneo, Jamie Stevens | Remember Me - Hernan Cattaneo & Jamie Stevens Remix | 122 | 5.5 |
| 15 | Cary Crank | Deep Forest (Extended Mix) | 122 | 5.5 |
| 16 | Cendryma | Wakefeld (Original Mix) | 122 | 5.5 |
| 17 | Greta Meier | Enlightenment (Poli Siufi Remix) | 122 | 5.5 |
| 18 | Guy J | Catfish (Jonas Saalbach Remix) | 124 | 6.0 |


## Set 96. 96. Luminoso — 1h20 — 2026-09-07
**Armado:** 2026-09-12  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Kasper Koman | Gertrude (Extended Mix) | 122 | 5.5 |
| 2 | Dosem | On Board | 123 | 5.5 |
| 3 | Khen | April Storm | 122 | 5.5 |
| 4 | Durante | Orca (Original Mix) | 124 | 6.0 |
| 5 | Emi Galvan | Hunter (Original Mix) | 125 | 6.0 |
| 6 | Ezequiel Arias, FJL | Color Divino (Extended Mix) | 124 | 6.0 |
| 7 | Nox Vahn | When I'm With You (Extended Mix)  | 123 | 5.5 |
| 8 | Emi Galvan | Distorsion (Original Mix) | 124 | 6.0 |
| 9 | Marsh & Leo Wood | Fall To Pieces | 126 | 6.5 |
| 10 | FJL | Rider (Original Mix) | 124 | 6.0 |
| 11 | Monolink | Don't Hold Back (Yotto Remix) | 122 | 5.5 |
| 12 | Durante, Amtrac | Gather (Original Mix) | 122 | 5.5 |
| 13 | Tinlicker, Ben Böhmer | Voodoo (Extended Mix) | 124 | 6.0 |
| 14 | Guy Mantzur, Kamilo Sanclemente | The Future is in the Past (Original Mix) | 124 | 6.0 |
| 15 | Fur Coat, Running Pine | Hurricane (Tim Green Remix) | 123 | 5.5 |
| 16 | Jody Wisternoff | Paramour (Original Mix) | 123 | 5.5 |
| 17 | Luttrell, Molly Moonwater | Something Right feat. Molly Moonwater (Ezequiel Arias Extended Mix) | 125 | 6.0 |
| 18 | Robert Miles, Tinlicker | Children (Extended Mix) | 124 | 6.0 |


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
| 1 | Fur Coat | Modular Theory | 124 | 6.0 |
| 2 | Hernan Cattaneo, Audio Junkies | A Major Minor (D-Nox & Beckers Remix) | 125 | 6.0 |
| 3 | Kit Lawson | Ruff (Original Mix) | 124 | 6.0 |
| 4 | Massano | Solitude | 123 | 5.5 |
| 5 | Gorkiz, K Loveski | Echos Of Eons (Greenage Remix) | 122 | 5.5 |
| 6 | Bedrock | Heaven Scent (Eagles & Butterflies Remix) | 123 | 5.5 |
| 7 | Jonas Saalbach | Second Surface (Original Mix) | 123 | 5.5 |
| 8 | Simon Vuarambon | Kaskazi | 122 | 5.5 |
| 9 | Melarmony | Aurora (Extended Mix) | 122 | 5.5 |
| 10 | Gorje Hewek, Lost Desert, Volen Sentir | Fluminnese (Dub) | 123 | 5.5 |
| 11 | ANMA | Adya | 124 | 6.0 |
| 12 | Cristoph, ADZ | Solpaz | 123 | 5.5 |


## Set 98. 98. After Oscuro — 1h — 2026-09-10
**Armado:** 2026-09-12  
**Duracion:** 1.0h  
**Tracks:** 12  
**BPM range:** 123-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Coeus | Paramount (Original Mix) | 126 | 6.5 |
| 2 | Rodriguez Jr. | Off Gerlach (Original Mix) | 125 | 6.0 |
| 3 | Boxer, Jody Wisternoff & James Grant | Sun Kissed (Extended Mix) | 124 | 6.0 |
| 4 | Monolink | Return to Oz (Artbat Remix) | 124 | 6.0 |
| 5 | Tinlicker, Ben Böhmer | Voodoo (Extended Mix) | 124 | 6.0 |
| 6 | InfeXus & ANZA | Africa (Extended Mix) | 124 | 6.0 |
| 7 | R.Hz | Gleam (Giuliano Rodrigues Rmx) | 123 | 5.5 |
| 8 | Mauro Picotto, CRW, Kamilo Sanclemente | I Feel Love (Extended Mix) | 123 | 5.5 |
| 9 | Nick Warren | Freebird (Emi Galvan Remix) | 123 | 5.5 |
| 10 | Marsh | Free (Extended Mix) | 124 | 6.0 |
| 11 | Jan Blomqvist, Mahri | Deeper Grounds feat. Mahri (Extended Mix) | 124 | 6.0 |
| 12 | Colyn | It's All Over | 125 | 6.0 |


## Set 99. 99. After Luminoso — 1h — 2026-09-10
**Armado:** 2026-09-12  
**Duracion:** 1.0h  
**Tracks:** 12  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Sahar Z & Guy Mantzur | Our Foggy Trips | 123 | 5.5 |
| 2 | WhoMadeWho | Never Alone (Patrice Bäumel Remix) | 124 | 6.0 |
| 3 | Lexer | Obscurity | 123 | 5.5 |
| 4 | Lane 8 | No Captain feat. Polica (Dirty South Remix) | 122 | 5.5 |
| 5 | Iveta, Bedouin | Better Than This ft. IVETA (Original Mix) | 123 | 5.5 |
| 6 | àmou | I WISH I COULD FLY (Extended) | 124 | 6.0 |
| 7 | Anatolie | Release Yourself | 125 | 6.0 |
| 8 | Guy J & Astrix | River | 124 | 6.0 |
| 9 | Simon Doty | Solstice (Extended Mix) | 124 | 6.0 |
| 10 | Teho | Ashes (Original Mix) | 125 | 6.0 |
| 11 | Korolova & Monophase (IT) | Reactive (Extended Mix) | 125 | 6.0 |
| 12 | Innēr Sense (ofc) | Older (Extended Mix) | 125 | 6.0 |


## Set 100. 100. Con el material de Ezequiel Arias - Metropolitano Rosario - 2026-06-27
**Armado:** 2026-09-12  
**Duracion:** 1.2h  
**Tracks:** 13  
**BPM range:** 121-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Christian Smith | Illusion (Ezequiel Arias Remix) | 125 | 6.0 |
| 2 | TPS | Control (Kostya Outta Remix) | 123 | 5.5 |
| 3 | Andre Moret | Kryon (Original Mix) | 123 | 5.5 |
| 4 | Drunken Kong, D-SHIFT | Where You Need To Be (Original Mix) | 121 | 5.0 |
| 5 | Cendryma | Parabolic (Original Mix) | 122 | 5.5 |
| 6 | Durante, Mayro | Mantra (Extended Mix) | 124 | 6.0 |
| 7 | Rockka | Initiation | 123 | 5.5 |
| 8 | Paul Arcane | Vortice (Extended Mix) | 123 | 5.5 |
| 9 | Kamilo Sanclemente | Horizons (Original Mix) | 121 | 5.0 |
| 10 | Rauschhaus | Waiting For The Birds | 123 | 5.5 |
| 11 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 5.5 |
| 12 | Gorkiz, Luca Abayan | Drowner (Extended Mix) | 122 | 5.5 |
| 13 | Chelakhov | Insomnia (Original Mix) | 122 | 5.5 |


## Set 101. 101. Con el material de Ezequiel Arias - Metropolitano Rosario - 2025-06-28
**Armado:** 2026-09-12  
**Duracion:** 1.7h  
**Tracks:** 19  
**BPM range:** 121-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Kamilo Sanclemente | Anagram (Mayro Extended Remix) | 123 | 5.5 |
| 2 | Claudio Cornejo (AR) | Alnitak (Original Mix) | 122 | 5.5 |
| 3 | Tinlicker, Helsloot | Because You Move Me (Jan Oberlaender Extended Remix) | 122 | 5.5 |
| 4 | FJL | Rider (Original Mix) | 124 | 6.0 |
| 5 | Blake Jarrell | Twenty Miami's Ago (Cendryma Extended Mix) | 122 | 5.5 |
| 6 | Luis Damora | Illuminate (Original Mix) | 123 | 5.5 |
| 7 | Supacooks, Bondarev | Activator (Original Mix) | 123 | 5.5 |
| 8 | Santi Mossman | Exitz (Original Mix) | 123 | 5.5 |
| 9 | Guy J | Silver Lake (Original Mix) | 122 | 5.5 |
| 10 | Melodiam (AR) | Repro Days (Original Mix) | 122 | 5.5 |
| 11 | Lonya | Sadness (Ziger Remix) | 122 | 5.5 |
| 12 | Guy J | Surreal (Original Mix) | 121 | 5.0 |
| 13 | Niko Ava | Freedom (Original Mix) | 122 | 5.5 |
| 14 | Roger Martinez | Cosmic Drum (Paul Deep Remix) | 123 | 5.5 |
| 15 | Cid Inc. | Citadel (Original Mix) | 123 | 5.5 |
| 16 | Ruben Karapetyan | Nostalgic Moments (Original Mix) | 121 | 5.0 |
| 17 | Soma Soul | Symphony Lake (Brian Cid Remix) | 121 | 5.0 |
| 18 | Emi Galvan | Samsara | 122 | 5.5 |
| 19 | Anton Borin (RU) | May Spring Come (Original Mix) | 123 | 5.5 |


## Set 102. 102. Con el material de Ezequiel Arias - Dahaus x Fruta Cordoba - 2026-04-12
**Armado:** 2026-09-12  
**Duracion:** 1.8h  
**Tracks:** 20  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Nox Vahn | When I'm With You (Extended Mix)  | 123 | 5.5 |
| 2 | Montw | Lost on the Road (Arnas D Remix) | 121 | 5.0 |
| 3 | Simos Tagias | Plexus | 122 | 5.5 |
| 4 | Paul (AR) & EANP | Insane (Lexicon Avenue Remix) | 122 | 5.5 |
| 5 | Dabeat | Etna (Ivan Aliaga Remix) | 121 | 5.0 |
| 6 | Simos Tagias | Epos | 122 | 5.5 |
| 7 | Melodiam (AR) | Molicocha (Extended Mix) | 123 | 5.5 |
| 8 | Estiva & Julia Church | On the Line | 124 | 6.0 |
| 9 | JESSIN | Babylon (North Echo Remix) | 125 | 6.0 |
| 10 | Emi Galvan & Albuquerque | Don't Kill the Messenger | 123 | 5.5 |
| 11 | Maze 28 | Red Lights From Afar | 122 | 5.5 |
| 12 | Kabi (AR) & Agustin Ficarra | The Return (Original Mix) | 123 | 5.5 |
| 13 | Melodiam (AR) | Words Are Weapons (Original Mix) | 122 | 5.5 |
| 14 | Estiva, Cosmosky | Ecstasy (Extended Mix) | 124 | 6.0 |
| 15 | Melodiam | Old Garden | 122 | 5.5 |
| 16 | Fabricio Gutierrez | Reedmov (Kebin van Reeken Remix) | 120 | 5.0 |
| 17 | Kamilo Sanclemente | Urania (Alex O'Rion Remix) | 120 | 5.0 |
| 18 | Ruben Karapetyan | Mindful Harmony (Dowden Remix) | 122 | 5.5 |
| 19 | Weird Sounding Dude | Step Up | 121 | 5.0 |
| 20 | Andre Moret | Generator (Extended Mix) | 121 | 5.0 |


## Set 103. 103. Con el material de Simon Vuarambon - Dahaus Palacio Alsina Cordoba - 2026-03-01
**Armado:** 2026-09-12  
**Duracion:** 1.8h  
**Tracks:** 20  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Markus Homm & Nici Faerber | Basement Room (Dilby Remix) | 125 | 6.0 |
| 2 | DAVI | Self ASCND (Original Mix)  | 124 | 6.0 |
| 3 | Rockka, Maze 28 | Mirage (Juan Ibanez Extended Mix) | 122 | 5.5 |
| 4 | Neuralis | Ethereum (Original Mix) | 120 | 5.0 |
| 5 | Tantum, Hyunji-A | Keep My Letters (Simon Vuarambon Remix) | 122 | 5.5 |
| 6 | Tobi Amuchastegui | Night Loop (Original Mix) | 121 | 5.0 |
| 7 | Agustin Pengov | Trumpert (Original Mix) | 120 | 5.0 |
| 8 | Aman Anand | Disastro (Thomas Ferell Remix) | 120 | 5.0 |
| 9 | Dr. Mirzoyan | Destruction (Ruben Karapetyan Remix) | 122 | 5.5 |
| 10 | Juan Buitrago | Anja | 121 | 5.0 |
| 11 | Mind Echoes | Unsafe Numbers (Tonaco & Tomas Garcia Remix) | 123 | 5.5 |
| 12 | Doki | Luminus (Cedren & Manu-l Remix) | 123 | 5.5 |
| 13 | Anton Borin (RU), Bondarev | Samadhi (Kasper Koman Remix) | 122 | 5.5 |
| 14 | Tobi Amuchastegui | You Are Not Alone (Original Mix) | 121 | 5.0 |
| 15 | Taylan | Earthbound (Andre Moret Remix) | 120 | 5.0 |
| 16 | Ciro Riveiro | Asia | 121 | 5.0 |
| 17 | Jody Wisternoff | Paramour (Original Mix) | 123 | 5.5 |
| 18 | Paul Thomas & Christian Burns | Enjoy the Silence (Extended Mix) | 122 | 5.5 |
| 19 | Kamilo Sanclemente | A Lonely Pink Cloud (Original Mix) | 122 | 5.5 |
| 20 | Ezequiel Arias | Heat Above - Original Mix | 124 | 6.0 |


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
| 1 | Santos (AR), Jussto | This Is Rocking It (Original Mix) | 124 | 6.0 |
| 2 | Rauschhaus | Faunus (Original Mix) | 123 | 5.5 |
| 3 | Kyotto | District (Original Mix) | 122 | 5.5 |
| 4 | Guy J | Stranger In A Strange World (Original Mix) | 122 | 5.5 |
| 5 | Kamilo Sanclemente | Canon (Original Mix) | 123 | 5.5 |
| 6 | Leandro Murua, Martin Fredes | Interference (Original Mix) | 122 | 5.5 |
| 7 | Amine K (Moroko Loko), WAHM (FR) | Kill the Anger (Rodriguez Jr. Remix) | 124 | 6.0 |
| 8 | Antrim | Curved (Original Mix) | 123 | 5.5 |
| 9 | Jamie Stevens, Kasey Taylor | Verlaine (Original Mix) | 122 | 5.5 |
| 10 | Kabi (AR), Ric Niels | Kimica | 122 | 5.5 |
| 11 | Bondarev, Max Wexem | The Lotus (Original Mix) | 123 | 5.5 |
| 12 | Sébastien Léger | Forbidden Garden (Tim Green Remix) | 122 | 5.5 |
| 13 | Carlo Whale, Th;en | Say It | 124 | 6.0 |
| 14 | Lost Desert | Aalam Waahid (Original Mix) | 124 | 6.0 |
| 15 | Cary Crank | Deep Forest (Extended Mix) | 122 | 5.5 |
| 16 | Nox Vahn | Brainwasher (Warung Extended Mix) | 123 | 5.5 |
| 17 | Artic White | Paradigm (Extended Mix) | 123 | 5.5 |
| 18 | K3V (SL) & Jayy Vibes | Kingdom of Dreams (Juan Ibanez Remix) | 122 | 5.5 |


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

