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

## Set 16. 16. Eze Arias Style
**Armado:** 2026-06-13  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mazayr | Falling | 120 | 4.5 |
| 2 | Of Norway | I Miss You (Sentre Remix) | 123 | 5.4 |
| 3 | Luke Santos | I Am Human (Kasper Koman & Alex O'Rion Remix) | 122 | 5.2 |
| 4 | Anton Borin (RU) | May Spring Come (Original Mix) | 123 | 5.9 |
| 5 | Kyotto | Sorry I'm Late (HAFT Remix) | 123 | 5.7 |
| 6 | Mazayr | Without Permission | 121 | 5.0 |
| 7 | Jon Towell | 49 Miles (Original Mix) | 123 | 2.9 |
| 8 | WhoMadeWho & Blue Hawaii | Kiss Me Hard (Adam Ten Remix) | 123 | 5.2 |
| 9 | Blake Jarrell | Twenty Miami's Ago (Cendryma Extended Mix) | 122 | 5.5 |
| 10 | Supacooks, Bondarev | Activator (Original Mix) | 123 | 6.1 |
| 11 | Jody Wisternoff, PROFF, James Grant, Siobhan Wilson, Takeshi Furukawa | Mui (Ezequiel Arias Extended Mix) | 125 | 6.4 |
| 12 | Remcord | Out Of It (Original Mix) | 123 | 5.9 |
| 13 | Pedro Capelossi, Aeikus | Topaz (Original Mix) | 123 | 5.8 |
| 14 | MoodFreak & Campaner (BR) | Surge (Kebin Van Reeken Remix) | 121 | 3.9 |
| 15 | Kamilo Sanclemente | Anagram (Mayro Extended Remix)  | 123 | 5.2 |
| 16 | Guy J | Silver Lake (Original Mix) | 122 | 5.9 |
| 17 | Kamilo Sanclemente | Astronauts Nightmares (DJ Ruby Extended Remix) | 123 | 7.1 |
| 18 | Ezequiel Arias | Passenger (Original Mix) | 122 | 7.0 |


## Set 17. 17. Progressive Melodic Alt
**Armado:** 2026-06-13  
**Duracion:** 2.0h  
**Tracks:** 13  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hobin Rude | Seraph (Liam Garcia Remix) | 120 | 2.2 |
| 2 | Golan Zocher & Choopie | SAO (Hernan Cattaneo & Simply City Extended Remix)  | 123 | 2.9 |
| 3 | Maze 28 | This Is Just a Dream (Hernan Cattaneo & Marcelo Vasami Remix)  | 122 | 2.5 |
| 4 | Hermanez | Eight Years (Original Mix) | 122 | 2.5 |
| 5 | Mercurio, Nick Warren | Turbulence (Original Mix) | 124 | 2.7 |
| 6 | Joe Miller | The Last of the Great Days (Jamie Stevens Remix) | 120 | 2.5 |
| 7 | Simon Vuarambon | 1996 (Original Mix) | 122 | 5.8 |
| 8 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 4.0 |
| 9 | Simon Vuarambon | Diafana (Original Mix) | 121 | 5.1 |
| 10 | Simon Vuarambón | Afrika  | 121 | 4.0 |
| 11 | Simon Vuarambon | Prodiga | 122 | 5.0 |
| 12 | D-Nox, Andre Moret | Six (Extended Mix) | 122 | 4.9 |
| 13 | Juan Deminicis | Deep Rock Galactic (Original Mix) | 122 | 4.9 |


## Set 18. 18. Digweed Style
**Armado:** 2026-06-13  
**Duracion:** 3.0h  
**Tracks:** 26  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Gai Barone, Luke Brancaccio, Kiki Cave | All I Need (Hernan Cattaneo & Mercurio remix)  | 119 | 1.4 |
| 2 | Hobin Rude | Seraph (Liam Garcia Remix) | 120 | 2.2 |
| 3 | Panorama Channel | Kinly Estellar | 120 | 1.8 |
| 4 | Juan Deminicis | Under Control (Original Mix) | 121 | 2.1 |
| 5 | Antrim & Juan Fernandez | Hide and Seek (Ric Niels Remix) | 120 | 1.8 |
| 6 | Cid Inc & Dmitry Molosh | Impending Storm | 120 | 1.8 |
| 7 | Hermanez | Eight Years (Original Mix) | 122 | 2.5 |
| 8 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 4.0 |
| 9 | Fer Torti | Star Trip  | 120 | 4.4 |
| 10 | Jon Towell | 49 Miles (Original Mix) | 123 | 2.9 |
| 11 | Of Norway | I Miss You (Sentre Remix) | 123 | 5.4 |
| 12 | Dmitry Molosh | Bird Flight (Original Mix) | 120 | 4.5 |
| 13 | Sebastian Sellares | Limbo (Extended Mix) | 120 | 4.5 |
| 14 | Chris Isaak | Wicked Game (Mass Digital Remix) | 119 | 4.4 |
| 15 | Michael A | Hunting Flowers (Radio Edit) | 120 | 3.1 |
| 16 | Nicolas Rada | Glasgow (Original Mix) | 122 | 4.4 |
| 17 | Tantum | Out Of Nowhere (Original Mix) | 121 | 4.2 |
| 18 | Cornucopia | Early Morning (Original Mix) | 118 | 3.0 |
| 19 | D-Nox, Stereo Underground | Dolby (Original Mix)  | 125 | 4.1 |
| 20 | Supacooks, Bondarev | Activator (Original Mix) | 123 | 6.1 |
| 21 | WhoMadeWho & Blue Hawaii | Kiss Me Hard (Adam Ten Remix) | 123 | 5.2 |
| 22 | Remcord | Out Of It (Original Mix) | 123 | 5.9 |
| 23 | Pedro Capelossi, Aeikus | Topaz (Original Mix) | 123 | 5.8 |
| 24 | Benja Molina | Aura (Original Mix) | 123 | 2.9 |
| 25 | Einmusik, Dirty Doering | Centaurio  | 125 | 7.3 |
| 26 | John Cosani | Snano (Original Mix) | 123 | 2.9 |


## Set 19. 19. Vuarambon Style
**Armado:** 2026-06-13  
**Duracion:** 2.0h  
**Tracks:** 15  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Gai Barone, Luke Brancaccio, Kiki Cave | All I Need (Hernan Cattaneo & Mercurio remix)  | 119 | 1.4 |
| 2 | Hobin Rude | Seraph (Liam Garcia Remix) | 120 | 2.2 |
| 3 | Hermanez | Eight Years (Original Mix) | 122 | 2.5 |
| 4 | Joe Miller | The Last of the Great Days (Jamie Stevens Remix) | 120 | 2.5 |
| 5 | Cid Inc & Dmitry Molosh | Impending Storm | 120 | 1.8 |
| 6 | Maze 28 | This Is Just a Dream (Hernan Cattaneo & Marcelo Vasami Remix)  | 122 | 2.5 |
| 7 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 4.0 |
| 8 | Simon Vuarambon | 1996 (Original Mix) | 122 | 5.8 |
| 9 | Benja Molina | Aura (Original Mix) | 123 | 2.9 |
| 10 | Simon Vuarambon | Diafana (Original Mix) | 121 | 5.1 |
| 11 | Simon Vuarambón | Afrika  | 121 | 4.0 |
| 12 | Simon Vuarambon | Prodiga | 122 | 5.0 |
| 13 | John Cosani | Snano (Original Mix) | 123 | 2.9 |
| 14 | Antrim & Juan Fernandez | Hide and Seek (Ric Niels Remix) | 120 | 1.8 |
| 15 | Mercurio, Nick Warren | Turbulence (Original Mix) | 124 | 2.7 |


## Set 20. 20. Emi Galvan Style
**Armado:** 2026-06-13  
**Duracion:** 2.0h  
**Tracks:** 18  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Antrim & Juan Fernandez | Hide and Seek (Ric Niels Remix) | 120 | 1.8 |
| 2 | Maze 28 | This Is Just a Dream (Hernan Cattaneo & Marcelo Vasami Remix)  | 122 | 2.5 |
| 3 | Emi Galvan | Lies (Original Mix) | 122 | 5.0 |
| 4 | Emi Galvan | Flowing | 121 | 5.1 |
| 5 | Hobin Rude | Seraph (Liam Garcia Remix) | 120 | 2.2 |
| 6 | Of Norway | I Miss You (Sentre Remix) | 123 | 5.4 |
| 7 | Hermanez | Eight Years (Original Mix) | 122 | 2.5 |
| 8 | J Lauda | Lifeline (Hernan Cattaneo & Simply City Extended Remix) | 123 | 4.8 |
| 9 | Kamilo Sanclemente | Anagram (Mayro Extended Remix)  | 123 | 5.2 |
| 10 | Tantum | Out Of Nowhere (Original Mix) | 121 | 4.2 |
| 11 | Simon Vuarambon | Diafana (Original Mix) | 121 | 5.1 |
| 12 | Simon Vuarambón | Afrika  | 121 | 4.0 |
| 13 | WhoMadeWho & Blue Hawaii | Kiss Me Hard (Adam Ten Remix) | 123 | 5.2 |
| 14 | Jon Towell | 49 Miles (Original Mix) | 123 | 2.9 |
| 15 | D-Nox, Andre Moret | Six (Extended Mix) | 122 | 4.9 |
| 16 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 4.0 |
| 17 | Kamilo Sanclemente | Astronauts Nightmares (DJ Ruby Extended Remix) | 123 | 7.1 |
| 18 | Ezequiel Arias | Passenger (Original Mix) | 122 | 7.0 |


## Set 27. 27. Progressive Colorido A — 2h — 2026-05-27
**Armado:** 2026-06-13  
**Duracion:** 2h  
**Tracks:** 28  
**BPM range:** 118-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Ben Böhmer | Begin Again (Original Mix) | 121 | 2.6 |
| 2 | Ben Böhmer | Blossoms | 123 | 4.8 |
| 3 | Malou, Ben Bohmer | Lost In Mind (Volen Sentir Extended Vision) | 124 | 6.0 |
| 4 | Ben Bohmer | In Memoriam | 124 | 6.6 |
| 5 | Ben Bohmer & Neils Hoffmann feat. Malou | Breathing  | 122 | 5.5 |
| 6 | Ben Bohmer | Beyond Beliefs (Original Mix) | 124 | 7.5 |
| 7 | Monolink | The Prey | 108 | 3.0 |
| 8 | Lane 8 | No Captain feat. Polica (Dirty South Remix) | 122 | 5.5 |
| 9 | Tinlicker | Always Will (Mees Salomé Extended Mix)  | 122 | 6.6 |
| 10 | Tinlicker | Just To Hear You Say (Joseph Ray Extended Mix)  | 124 | 6.8 |
| 11 | Lane 8 | Survive (feat. Channy Leaneagh) [Sultan + Shepard Remix] | 123 | 5.8 |
| 12 | Lane 8 feat Polica feat. POLIÇA | Brightest Lights | 125 | 5.8 |
| 13 | Monolink | Sirens (H3RMES Edit)  | 120 | 4.9 |
| 14 | Monolink | Don't Hold Back  | 120 | 4.1 |
| 15 | Lane 8 | Keep On (Extended Mix)  | 122 | 5.1 |
| 16 | Lane 8 ft. Solomon Grey | Diamonds (Original Mix) | 120 | 4.2 |
| 17 | Braxton & Lauren L'aimant | Holding On (Extended Mix) | 120 | 4.6 |
| 18 | ilan Bluestone feat. Giuseppe De Luca | Frozen Ground (Cosmic Gate Remix)  | 130 | 7.4 |
| 19 | ilan Bluestone | Bigger Than Love (feat. Giuseppe De Luca) | 130 | 7.5 |
| 20 | N'to | Alter Ego | 123 | 6.6 |
| 21 | Braxton, Because of Art | Between The Stars (Extended Mix) | 128 | 6.5 |
| 22 | WhoMadeWho | Silence & Secrets (Adriatique Remix)  | 124 | 6.6 |
| 23 | Tinlicker, Helsloot | Because You Move Me (Jan Oberlaender Extended Remix) | 122 | 5.5 |
| 24 | Andrew Bayer | Immortal Lover (8kays Extended Mix) | 125 | 7.0 |
| 25 | Moderat | Bad Kingdom (DJ Koze Remix) | 118 | 1.0 |
| 26 | Khen | The Lighthouse (Original Mix) | 124 | 6.5 |
| 27 | PROFF Ft. Mokka | Your Light (Extended Mix) | 122 | 6.1 |
| 28 | Moderat | Reminder | 160 | 5.8 |


## Set 28. 28. Progressive Colorido B — 2h — 2026-05-27
**Armado:** 2026-06-13  
**Duracion:** 2h  
**Tracks:** 28  
**BPM range:** 119-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Rufus Du Sol | Underwater (Adam Port Remix) | 118 | 2.8 |
| 2 | Armen Miran | Heavenly Life | 118 | 4.7 |
| 3 | Rufus Du Sol | Eyes | 124 | 3.5 |
| 4 | Tale Of Us | Notte Senza Fine (Kiasmos Remix) | 120 | 4.5 |
| 5 | Rufus Du Sol | Treat You Better | 122 | 3.7 |
| 6 | RUFUS DU SOL | Innerbloom (Original Mix) | 122 | 5.4 |
| 7 | HVOB | Tender Skin (DJ Tennis Remix) | 120 | 4.8 |
| 8 | 8Kays x Juan Hansen | Falling Down (Chris Avantgarde Remix) | 124 | 6.2 |
| 9 | Fancy Inc | Something Good (Fabricio Pecanha Remix) | 123 | 5.7 |
| 10 | Innellea | Reflected Wisdom - Five Phases Project (4 / 5) | 124 | 6.2 |
| 11 | N'to | Trauma (Worakls Remix) | 128 | 7.2 |
| 12 | Joris Voorn | Incident (Original Mix) | 135 | 7.3 |
| 13 | Simon Shackleton | Traumstaat (Jody Wisternoff & James Grant Extended Edit) | 130 | 5.1 |
| 14 | Tale Of Us & Mind Against | Astral (Original Mix) | 124 | 5.5 |
| 15 | Solomun | Kackvogel | 118 | 3.0 |
| 16 | Anyma (ofc) & Chris Avantgarde | Consciousness | 126 | 5.6 |
| 17 | Above & Beyond | Sun In Your Eyes (Spencer Brown Club Mix) | 125 | 6.9 |
| 18 | Anyma & Chris Avantgarde | Eternity | 125 | 4.9 |
| 19 | Anyma, Rebūke | Syren | 125 | 6.9 |
| 20 | Solomun | Hypnotize | 125 | 3.6 |
| 21 | Above and Beyond feat. Gemma Hayes | Counting Down The Days  (Above and Beyond Club Mix) | 128 | 8.4 |
| 22 | Bicep | Glue (Original Mix) | 130 | 5.4 |
| 23 | Anyma | Explore Your Future | 124 | 5.4 |
| 24 | Solomun | Customer Is King  | 123 | 4.9 |
| 25 | Kasper Koman | The Blind Navigator (Extended Mix)  | 122 | 5.5 |
| 26 | Massano | Falling | 122 | 5.7 |
| 27 | PROFF Ft. Mokka | Your Light (Extended Mix) | 122 | 6.1 |
| 28 | Adriatique | Mystery (Tale Of Us & Mathame Remix)  | 124 | 8.8 |


## Set 29. 29. Mango Alley Deep — 2h — 2026-06-01
**Armado:** 2026-06-13  
**Duracion:** 2h  
**Tracks:** 18  
**BPM range:** 120-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Maze 28 | Flux | 122 | 5.3 |
| 2 | Maze 28 | C Moon (Original Mix) | 122 | 5.5 |
| 3 | Maze 28 | Nocte | 122 | 6.1 |
| 4 | Maze 28 | Stardust (Original Mix) | 121 | 5.4 |
| 5 | Rockka | Decryptor  | 122 | 5.7 |
| 6 | Cary Crank | Deep Voltage (NOIYSE PROJECT Remix) | 122 | 5.9 |
| 7 | Rockka | The Fade (Dave Walker Remix)  | 122 | 5.9 |
| 8 | Rockka | Elevation  | 122 | 5.9 |
| 9 | Cary Crank | Inner Atlas (Kyotto Remix) | 122 | 6.2 |
| 10 | Ruben Karapetyan, Maze 28 | Cosmic Dot (Cid Inc. Remix) | 123 | 6.1 |
| 11 | Rockka, Maze 28 | Chroma (Original Mix) | 122 | 5.8 |
| 12 | Dowden | Pacifist (Original Mix) | 121 | 4.8 |
| 13 | Rauschhaus, Cary Crank | Bekal (Extended Mix) | 120 | 6.3 |
| 14 | Dowden | Eternity | 121 | 5.9 |
| 15 | Dowden | Urias | 121 | 5.1 |
| 16 | Dowden | Gavia (Original Mix) | 122 | 5.7 |
| 17 | Rauschhaus, Cary Crank | Bright Things in Front of Us (Extended Mix) | 122 | 5.7 |
| 18 | Cary Crank | Echoes From Below (Weird Sounding Dude Remix) | 121 | 5.8 |


## Set 30. 30. Hobin & Cendryma — 2h — 2026-06-01
**Armado:** 2026-06-13  
**Duracion:** 2h  
**Tracks:** 18  
**BPM range:** 119-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Nicolas Rada | Prana  | 119 | 4.6 |
| 2 | Hobin Rude | Dusk Petals (Original Mix) | 121 | 4.9 |
| 3 | Hobin Rude | Nether (Original Mix) | 120 | 5.1 |
| 4 | Hobin Rude | Prism (Original Mix) | 121 | 5.1 |
| 5 | Ewan Rill, K Loveski | Jala (Original Mix)  | 122 | 2.5 |
| 6 | Cendryma | Evasive (Extended Mix) | 121 | 6.3 |
| 7 | Cendryma | Orbitation (Extended Mix) | 122 | 5.6 |
| 8 | Ewan Rill, Shayan Pasha | Hidden Path (Original Mix) | 120 | 4.6 |
| 9 | Hobin Rude | Shrouded Glint (Original Mix) | 122 | 6.7 |
| 10 | Cendryma | Mythica (Extended Mix) | 121 | 6.2 |
| 11 | Cendryma | Fracture (Extended Mix) | 121 | 6.2 |
| 12 | Nicolas Rada | El Oro De Los Tigres | 122 | 4.5 |
| 13 | Armen Miran & Nicolas Rada | Pull (Original Mix)  | 122 | 5.6 |
| 14 | Nicolas Rada, Antrim | Daydream (Original Mix) | 121 | 5.7 |
| 15 | Armen Miran & Nicolas Rada | Fall Away (Original Mix)  | 120 | 5.2 |
| 16 | Chaum, Hobin Rude | Cressida (Tonaco Remix) | 122 | 6.2 |
| 17 | Nicolas Rada | Cascadia | 122 | 6.5 |
| 18 | Ewan Rill | Omega Torra | 122 | 5.2 |


## Set 31. 31. Gai Barone Universe — 2h — 2026-06-01
**Armado:** 2026-06-13  
**Duracion:** 2h  
**Tracks:** 17  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Chelakhov, Redspace | Cosmonauts (Tiefstone Remix) | 121 | 4.2 |
| 2 | Chelakhov | Rami (Khaaron Remix)  | 120 | 4.7 |
| 3 | Chelakhov | Crystal Fall  (Original Mix) | 120 | 5.5 |
| 4 | Deftones | Digital Bath (Blake Jarrell Remix)  | 120 | 3.9 |
| 5 | Hermanez | Third Decade  | 120 | 5.2 |
| 6 | Hermanez | Ensina  | 120 | 4.9 |
| 7 | Gai Barone | Hemels (Original Mix) | 122 | 5.6 |
| 8 | Hermanez | Dust Town  | 122 | 4.9 |
| 9 | Chelakhov | Rawai (Extended Mix) | 122 | 6.1 |
| 10 | Hermanez | Areia (Original Mix)  | 120 | 4.5 |
| 11 | Hraach, Armen Miran | Sarer Jan feat. Iveta Mukuchyan (Original Mix) | 122 | 3.2 |
| 12 | Gai Barone | Shuttered (Original Mix) | 122 | 6.0 |
| 13 | Blake Jarrell | In the End You'll Know (Original Mix) | 124 | 5.9 |
| 14 | D-Nox, Two Of A Kind, Gai Barone | Vida (DJ Zombi Remix)  | 120 | 4.7 |
| 15 | Gai Barone | Weird Behaviours (Original Mix) | 122 | 5.5 |
| 16 | Analog Jungs | Futura (Dowden Remix)  | 122 | 5.9 |
| 17 | Gai Barone, Dougal Fox | Ocean (Club Mix) | 122 | 6.6 |


## Set 32. 32. Emi Style — 2h — 2026-06-01
**Armado:** 2026-06-13  
**Duracion:** 2h  
**Tracks:** 21  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hraach | Cosmic Drama (Original Mix)  | 120 | 3.8 |
| 2 | Mike Rish | Shokl (Original Mix) | 118 | 4.2 |
| 3 | Hraach | Delirio (Original Mix) | 120 | 4.9 |
| 4 | Hraach | Promises (Original Mix)  | 121 | 5.0 |
| 5 | Emi Galvan | Timeless (Original Mix)  | 121 | 2.9 |
| 6 | Emi Galvan | Trust (Original Mix) | 122 | 6.0 |
| 7 | Hraach | Lonely Sun (Original Mix)  | 122 | 5.6 |
| 8 | Nick Warren | Freebird (Emi Galvan Remix)  | 123 | 6.9 |
| 9 | Mike Rish | Sunset on Mars (Original Mix) | 120 | 4.2 |
| 10 | Mike Rish | Tornn (Original Mix) | 120 | 4.2 |
| 11 | Mike Rish | Tunnel People (Original Mix)  | 120 | 3.9 |
| 12 | Emi Galvan | Vibration (Original Mix) | 122 | 5.9 |
| 13 | Tantum | Another Day (Original Mix)  | 120 | 4.0 |
| 14 | Quivver | Another Storm (Mike Rish Remix) | 122 | 5.5 |
| 15 | Kamilo Sanclemente | A Lonely Pink Cloud (Original Mix) | 122 | 6.0 |
| 16 | Kamilo Sanclemente | Theia | 122 | 5.6 |
| 17 | Kasper Koman | Loco Motif (Tantum Remix)  | 121 | 5.0 |
| 18 | Emi Galvan | Samsara | 122 | 6.3 |
| 19 | Tantum | Bonsai (Original Mix)  | 124 | 5.7 |
| 20 | Kamilo Sanclemente | Go Home (Original Mix) | 121 | 5.7 |
| 21 | Kamilo Sanclemente | Divine Eternity (K Loveski Remix) | 121 | 4.8 |


## Set 33. 33. GMJ Universe — Hipnotico Oscuro — 2026-06-04
**Armado:** 2026-06-13  
**Duracion:** 2h  
**Tracks:** 21  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | GMJ & Matter | Soular (Original Mix) | 120 | 4.7 |
| 2 | GMJ & Matter | Metanoia | 122 | 5.7 |
| 3 | GMJ & Matter | Nassaukade (Original Mix) | 121 | 5.8 |
| 4 | GMJ & Matter | Arkeron (Original Mix) | 120 | 4.8 |
| 5 | Jamie Stevens & GMJ | Force of Nature (Original Mix)  | 120 | 1.8 |
| 6 | Dmitry Molosh | Step by Step feat. Sasha Bartashevich (Original Dub Mix)  | 121 | 5.1 |
| 7 | Cid Inc. | Rescue Me (Original Mix)  | 123 | 6.2 |
| 8 | Dmitry Molosh | Only U  | 120 | 1.8 |
| 9 | Dmitry Molosh | Glide  | 121 | 6.1 |
| 10 | Cid Inc. | Citadel (Original Mix)  | 123 | 7.0 |
| 11 | Dmitry Molosh | Cascade  | 122 | 2.5 |
| 12 | Ruben Karapetyan | Nostalgic Moments (Original Mix) | 121 | 5.0 |
| 13 | Rauschhaus | Mindworm (Ruben Karapetyan Remix) | 123 | 6.0 |
| 14 | Ruben Karapetyan | State of Progression (Original Mix) | 122 | 5.6 |
| 15 | D-Nox & Beckers | Bitter Rain (Cid Inc. Remix) | 123 | 6.3 |
| 16 | Kasper Koman | Hi (Cid Inc. Remix)  | 122 | 5.8 |
| 17 | Hernan Cattaneo & Soundexile | Astron (Davi Remix)  | 122 | 6.4 |
| 18 | Hernan Cattaneo & Soundexile | Deneb | 122 | 4.9 |
| 19 | Hernan Cattaneo & Soundexile | Pressure Drop | 122 | 5.5 |
| 20 | Marcelo Vasami | Shades Of Blue (Original Mix)  | 122 | 6.7 |
| 21 | Armen Miran, Felix Raphael | Ghost (Hernan Cattaneo & Marcelo Vasami Remix)  | 120 | 5.2 |


## Set 34. 34. Tom Pavicich & Friends — 2026-06-04
**Armado:** 2026-06-13  
**Duracion:** 2h  
**Tracks:** 19  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | FAERO, Tom Pavicich, Analog Sense | No Warm (Original Mix) | 118 | 3.1 |
| 2 | Tom Pavicich | About Her (Martin Fredes Remix) | 122 | 6.1 |
| 3 | Tom Pavicich, Analog Sense | Anger (Tiefstone Remix) | 123 | 5.3 |
| 4 | Tom Pavicich | Volver (Sinan Arsan Remix) | 121 | 5.6 |
| 5 | FAERO, Tom Pavicich, Analog Sense | Evolve (Original Mix) | 123 | 5.1 |
| 6 | Gorkiz | Fired (Original Mix) | 123 | 5.3 |
| 7 | Gorkiz & Tonaco | Serenity | 122 | 5.2 |
| 8 | Bondarev | Meteora (Cosmonaut Remix)  | 122 | 5.6 |
| 9 | Gorkiz & Gastón Sosa | All Night Long | 122 | 5.4 |
| 10 | Gorkiz, K Loveski | Echos Of Eons (Greenage Remix)  | 122 | 5.7 |
| 11 | Tom Pavicich | Insight (Original Mix) | 122 | 6.5 |
| 12 | Rodriguez Jr. | 1PM Sunrise | 124 | 3.2 |
| 13 | Anton Borin (RU), Bondarev | Samadhi (Kasper Koman Remix)  | 122 | 5.9 |
| 14 | Tali Muss & Bondarev | Algorythm | 122 | 5.5 |
| 15 | Rodriguez Jr. | Nairobi (Original Mix)  | 124 | 5.1 |
| 16 | Rodriguez Jr. | Twilight Language (Extended Version)  | 123 | 5.5 |
| 17 | Bondarev, Jiminy Hop, Tantum | Pale Blue Dot (Tantum Remix) | 121 | 6.0 |
| 18 | Rodriguez Jr. | Hydra  | 122 | 5.7 |
| 19 | Amine K (Moroko Loko), WAHM (FR) | Kill the Anger (Original Mix) | 124 | 5.9 |


## Set 35. 35. Lee Burridge Deep — Organic — 2026-06-04
**Armado:** 2026-06-13  
**Duracion:** 2h  
**Tracks:** 22  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Lee Burridge, Lost Desert | Chicago Drive (Original Mix)  | 121 | 4.9 |
| 2 | Simon Vuarambon | Quimera (Original Mix) | 121 | 5.0 |
| 3 | Lost Desert, Reigan, Amand | Open Form feat. Reigan (Original Mix) | 123 | 6.4 |
| 4 | Lee Burridge, Lost Desert | Forget (Original Mix)  | 121 | 6.5 |
| 5 | Monkey Safari | Goodbye (Lee Burridge & Lost Desert Remix)  | 124 | 5.6 |
| 6 | Lee Burridge, Lost Desert | In the Dark (Original Mix)  | 122 | 6.0 |
| 7 | Simon Vuarambon | Alcyon  | 120 | 4.7 |
| 8 | Simon Vuarambon | DEC (Original Mix) | 121 | 5.0 |
| 9 | Guy Mantzur, Tamir Regev | Stargazer (Original Mix)  | 122 | 6.2 |
| 10 | PROFF | Reverie  | 122 | 5.3 |
| 11 | PROFF, Volen Sentir | Luna Amazonia (PM Mix) | 123 | 6.4 |
| 12 | Jakatta | American Dream (PROFF Extended Interpretation) | 122 | 7.1 |
| 13 | Guy Mantzur & Khen | Where Is Home (Original Mix) | 122 | 5.5 |
| 14 | Simon Vuarambon | Lazos (Original Mix) | 120 | 5.2 |
| 15 | PROFF, Khen, Volen Sentir | Mirage (Extended Mix) | 122 | 6.8 |
| 16 | Guy Mantzur, Roy Rosenfeld | Epika (Original Mix) | 120 | 3.0 |
| 17 | Jamie Stevens | Cdx5 | 124 | 5.7 |
| 18 | Jamie Stevens | Creature of Comfort  | 123 | 5.7 |
| 19 | Sudhaus & The Wash | Spectron (DJ Ruby Remix) | 123 | 5.5 |
| 20 | Jamie Stevens, Zankee Gulati | Low Tide (Ezequiel Arias Remix) | 125 | 7.8 |
| 21 | Gorje Hewek, Hernan Cattaneo & Dulus | Kaleidoscope | 122 | 5.8 |
| 22 | Guy Mantzur | My Wild Flower (Original Mix) | 123 | 5.0 |


## Set 36. 36. This Guy Ben Peak — 2026-06-04
**Armado:** 2026-06-13  
**Duracion:** 2h  
**Tracks:** 19  
**BPM range:** 121-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | This Guy Ben | Kapalla (Extended Mix)  | 122 | 5.2 |
| 2 | This Guy Ben | Hey Sally (Extended Mix)  | 122 | 5.3 |
| 3 | This Guy Ben | Neptuna (Gai Barone Extended Remix) | 123 | 5.5 |
| 4 | This Guy Ben | Five from Fargo (Extended Mix) | 124 | 6.1 |
| 5 | Fur Coat | Doppler Effect  | 124 | 3.2 |
| 6 | Fur Coat | Ethereal  | 124 | 6.2 |
| 7 | Fur Coat | Modular Theory  | 124 | 6.0 |
| 8 | Fur Coat | Pandora's Dream (Original Mix)  | 124 | 6.3 |
| 9 | Massano | System | 122 | 5.0 |
| 10 | Sasha | Singularity (Fur Coat Remix)  | 125 | 6.8 |
| 11 | Massano | The Feeling (2022 Remaster) | 124 | 7.0 |
| 12 | Massano | Odyssey | 122 | 5.6 |
| 13 | Depeche Mode | Ghosts Again (Massano Remix)  | 124 | 6.6 |
| 14 | Tinlicker | All That I Lost | 124 | 6.5 |
| 15 | Tinlicker | Compound (Extended Mix)  | 124 | 6.1 |
| 16 | Cristoph, ADZ | Solpaz  | 123 | 6.1 |
| 17 | Massano | Solitude | 123 | 5.9 |
| 18 | Oliver Schories | Peron (Original Mix) | 123 | 6.1 |
| 19 | Oliver Schories | Lymn (Original Mix) | 124 | 6.6 |


## Set 37. 37. Bedouin x Monolink — Peluqueria — 2026-06-13
**Armado:** 2026-06-13  
**Duracion:** 3h  
**Tracks:** 27  
**BPM range:** 116-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Bedouin | Set The Controls For The Heart Of The Sun (Original Mix) | 118 | 1.0 |
| 2 | Bedouin | Voices In My Head (Damian Lazarus Re-Shape)  | 118 | 4.5 |
| 3 | Bedouin | Straight To The Heart | 116 | 5.1 |
| 4 | Bedouin | Flight of Birds | 120 | 5.6 |
| 5 | Bedouin | Hologram (Original Mix) | 59 | 4.2 |
| 6 | Monolink | Swallow (Oliver Koletzki Remix) | 121 | 4.5 |
| 7 | Monolink | Burning Sun (Davi Remix)  | 121 | 5.2 |
| 8 | DakhaBrakha | Salgir Boyu (Bedouin Reworks) | 121 | 5.0 |
| 9 | Bedouin | Petra (Extended Version) | 120 | 5.5 |
| 10 | Monolink & Zigan Aldi | Fidale (I Feel) [Extended Vocal Version] | 120 | 5.3 |
| 11 | Nils Hoffmann, Julia Church | 9 Days (Dosem Extended Mix) | 125 | 6.2 |
| 12 | Hot Oasis | Bedouin Joy (Original Mix) | 121 | 4.9 |
| 13 | Monolink | Don't Hold Back  | 120 | 4.1 |
| 14 | Adam Port, Monolink | Point Of No Return (Extended Mix) | 122 | 5.1 |
| 15 | Ben Bohmer & Neils Hoffmann feat. Malou | Breathing  | 122 | 5.5 |
| 16 | Monolink | Father Ocean (Ben Boehmer Remix) | 122 | 6.7 |
| 17 | Nils Hoffmann, Tender | Let Me Go (OLAN Extended Mix) | 122 | 5.2 |
| 18 | Soul Of Zoo & Guy Laliberté | Into Your Tribe (feat. Dominique Fils-Aime) [Bedouin Remix] | 121 | 5.8 |
| 19 | Kidnap ft Leo Stannard | Moments (Ben Bohmer & Nils Hoffmann Extended Remix) | 121 | 4.3 |
| 20 | ABDEL HALIM HAFEZ | EL TOBA (BEDOUIN EDIT) | 128 | 4.0 |
| 21 | Malou, Ben Bohmer | Lost In Mind (Volen Sentir Extended Vision) | 124 | 6.0 |
| 22 | Panama, Nils Hoffmann | Far Behind (Jeremy Olander Extended Mix) | 123 | 5.4 |
| 23 | Roisin Murphy | Dear Miami (Bedouin Extended Remix) | 124 | 6.4 |
| 24 | Worakls, Ben Bohmer | Red Dressed feat. Eivor (Ben Bohmer Remix) | 124 | 6.6 |
| 25 | Monolink | Otherside (Fideles Remix) | 123 | 6.7 |
| 26 | Black Coffee | Wish You Were Here (feat. Msaki) [Bedouin Remix] | 123 | 6.2 |
| 27 | Iveta, Bedouin | Better Than This ft. IVETA (Original Mix) | 123 | 5.9 |


## Set 38. 38. Rodriguez Jr. x Adriatique — Oscuro Progresivo — 2026-06-13
**Armado:** 2026-06-13  
**Duracion:** 3h  
**Tracks:** 33  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Eli & Fur | Night Blooming Jasmine (Rodriguez Jr. Remix)  | 120 | 1.8 |
| 2 | RÜFÜS DU SOL | On My Knees (Oliver Schories Remix) | 122 | 5.6 |
| 3 | Jeremy Olander | Leftwoods (Original Mix)  | 120 | 4.6 |
| 4 | Adriatique, Marino Canal | Desire (Original Mix) | 120 | 5.3 |
| 5 | Pional | Tempest  | 120 | 3.8 |
| 6 | Adriatique, Delhia De France, Marino Canal | Home (Mind Against Remix) | 120 | 5.6 |
| 7 | Adriatique | Voices From The Dawn  | 121 | 1.3 |
| 8 | Eagles & Butterflies | The Last Dance | 123 | 6.1 |
| 9 | Rodriguez Jr. | Hydra  | 122 | 5.7 |
| 10 | Adriatique | Ray  | 123 | 5.5 |
| 11 | Stephan Bodzin | River (Adriatique Remix) | 123 | 6.2 |
| 12 | Adriatique | Grinding Rhythm  | 123 | 5.6 |
| 13 | Jeremy Olander, Kamaliza | Zanzibar (Sthlm Edit) | 122 | 4.6 |
| 14 | Nelly Furtado, Adriatique, Timbaland, Notre Dame | Give It To Me 2025 (Extended Version)  | 122 | 5.6 |
| 15 | Jan Blomqvist | Maybe Not (Rodriguez Jr. Extended Remix)  | 122 | 4.6 |
| 16 | Jeremy Olander | Panorama (Original Mix) | 123 | 4.9 |
| 17 | Kiko & Rodriguez Jr. | Miller | 123 | 5.7 |
| 18 | Stereo MC's, Re.you | Relocate (Rodriguez Jr. Remix)  | 123 | 5.6 |
| 19 | RÜFÜS DU SOL | In the Moment (Adriatique Extended Remix) | 124 | 6.7 |
| 20 | Adriatique | Nude (Rampa Remix) | 123 | 6.7 |
| 21 | Jeremy Olander | Nattuggla  | 123 | 5.9 |
| 22 | Jeremy Olander | Saigon  | 123 | 4.9 |
| 23 | Rodriguez Jr. | Twilight Language (Extended Version)  | 123 | 5.5 |
| 24 | Rodriguez Jr. & Liset Alea | What Is Real (Deep in the Playa Mix) | 123 | 6.6 |
| 25 | Rodriguez Jr. | 1PM Sunrise | 124 | 3.2 |
| 26 | Rodriguez Jr. | An Evidence Of Time (Claude Vonstroke Remix) | 124 | 6.5 |
| 27 | Elderbrook | Numb (Joris Voorn Remix) | 126 | 7.1 |
| 28 | Joris Voorn, Mees Salomé, Celine Cairo | Fool's Paradise (Joris Voorn Remix) | 124 | 5.8 |
| 29 | Jan Blomqvist, Rodriguez Jr. | Destination Lost (Arodes Extended Remix) | 125 | 6.8 |
| 30 | Jeremy Olander | Seige  | 124 | 4.6 |
| 31 | Joris Voorn, Alex Kennon | Blinding Lights (Joris Voorn Remix) | 124 | 7.1 |
| 32 | Rodriguez Jr. | Nairobi (Original Mix)  | 124 | 5.1 |
| 33 | Elderbrook | I Need You (Adriatique Extended Remix) | 125 | 5.7 |


## Set 39. 39. Guy Mantzur x Max Cooper — Dark Melodico — 2026-06-13
**Armado:** 2026-06-13  
**Duracion:** 3h  
**Tracks:** 37  
**BPM range:** 115-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Atish & Mark Slee | Chameleon (Nick Warren + Nicolas Rada Remix) | 119 | 1.4 |
| 2 | Max Cooper | Hope | 120 | 3.3 |
| 3 | Max Cooper | Balance Perc Tool (Original Mix) | 119 | 2.9 |
| 4 | Guy Mantzur, Roy Rosenfeld | Epika (Original Mix) | 120 | 3.0 |
| 5 | Husa & Zeyada | On My Own (Hernan Cattaneo & Marcelo Vasami Remix) | 118 | 3.9 |
| 6 | Nick Warren | Dreamcatcher | 115 | 5.5 |
| 7 | Max Cooper | Resynthesis (Original Mix) | 120 | 1.8 |
| 8 | Max Cooper | Music of the Tides (Original Mix) | 121 | 2.1 |
| 9 | Max Cooper | Cyclic (John Tejada Remix) | 121 | 2.1 |
| 10 | Matthias Meyer | Strangely Enough (Guy Mantzur & Tamir Regev Remix)  | 120 | 4.4 |
| 11 | Dominik Eulberg | Sansula (Max Cooper's Lost In Sound Mix) | 121 | 4.0 |
| 12 | Guy Mantzur | Chasing The Fog | 122 | 6.0 |
| 13 | Hernan Cattaneo, Husa & Zeyada | Love Is Coming Back (Club Mix) | 121 | 5.0 |
| 14 | Armen Miran, Felix Raphael | Ghost (Hernan Cattaneo & Marcelo Vasami Remix)  | 120 | 5.2 |
| 15 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 4.0 |
| 16 | Upercent | Pulsacions (Nick Warren Remix)  | 121 | 5.0 |
| 17 | Maga | Trust Me Sometime (Nick Warren & Nicolas Rada Remix) | 121 | 5.9 |
| 18 | Hernan Cattaneo & Soundexile | Wind Down (Outro Mix) | 122 | 3.5 |
| 19 | Guy Mantzur, Khen | My Golden Cage (Original Mix) | 122 | 6.0 |
| 20 | Gorje Hewek, Hernan Cattaneo & Dulus | Kaleidoscope | 122 | 5.8 |
| 21 | Guy Mantzur, Tamir Regev | Stargazer (Original Mix)  | 122 | 6.2 |
| 22 | Nils Frahm | For (Max Cooper Remix) | 122 | 5.3 |
| 23 | Nick Warren | Balance | 122 | 4.9 |
| 24 | Hraach, Armen Miran | Menq (Nick Warren & Nicolas Rada Remix) | 122 | 6.3 |
| 25 | Eelke Kleijn | 8 Bit Era (Nick Warren & Nicolas Rada Extended Remix)  | 122 | 5.9 |
| 26 | Hernan Cattaneo & Soundexile | Pick Up | 122 | 4.8 |
| 27 | Nick Warren | Falling In (Red Axes Remix)  | 122 | 5.3 |
| 28 | Maze 28 | This Is Just a Dream (Hernan Cattaneo & Marcelo Vasami Remix)  | 122 | 2.5 |
| 29 | Mariano Mellino | The Old Seawolf (Hernan Cattaneo & Graziano Raffa Remix) | 122 | 5.7 |
| 30 | Max Cooper | Careless (Locked Groove Remix)  | 124 | 6.3 |
| 31 | Guy Mantzur & Khen | Where Is Home (Original Mix) | 122 | 5.5 |
| 32 | Hernan Cattaneo & Soundexile | Deneb | 122 | 4.9 |
| 33 | Nick Warren | Freebird (Emi Galvan Remix)  | 123 | 6.9 |
| 34 | Hernan Cattaneo & Soundexile | Astron (Davi Remix)  | 122 | 6.4 |
| 35 | Joris Voorn, Mees Salomé, Celine Cairo | Fool's Paradise (Joris Voorn Remix) | 124 | 5.8 |
| 36 | Hernan Cattaneo, Hicky & Kalo | Voyage  | 123 | 2.9 |
| 37 | Hidden Orchestra | Wingbeats (Max Cooper Remix) | 124 | 5.9 |


## Set 40. 40. Gorje Hewek x Hraach — Armenio Profundo — 2026-06-13
**Armado:** 2026-06-13  
**Duracion:** 3h  
**Tracks:** 30  
**BPM range:** 116-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hraach | Apricot Tree (Original Mix)  | 118 | 1.0 |
| 2 | Armen Miran & Hraach | Aldebaran | 116 | 4.8 |
| 3 | Hraach, Armen Miran | Nervous Layers (Original Mix) | 118 | 4.2 |
| 4 | Hraach, Armen Miran | Mysterious World (Original Mix) | 118 | 4.9 |
| 5 | Hraach, Armen Miran | Krunk (Original Mix)  | 116 | 4.2 |
| 6 | Armen Miran | Save My Soul (Original Mix) | 116 | 5.0 |
| 7 | Gorje Hewek | Forest Song in the Morning (Original Mix | 120 | 1.8 |
| 8 | Hraach | Delirio (Original Mix) | 120 | 4.9 |
| 9 | Gorje Hewek & Izhevski | When I Was Young (Original Mix) | 120 | 3.9 |
| 10 | Armen Miran & Nicolas Rada | Fall Away (Original Mix)  | 120 | 5.2 |
| 11 | Hraach | Hidden Dimension (Kora (CA) Remix) | 120 | 5.5 |
| 12 | Hraach | Cosmic Drama (Original Mix)  | 120 | 3.8 |
| 13 | Armen Miran | Nani Jan (Original) | 120 | 5.1 |
| 14 | Gorje Hewek | Leto Ete-Satien (Original Mix) | 120 | 4.8 |
| 15 | Gorje Hewek, Molac, Dulus | Astro World (Original Mix) | 120 | 4.9 |
| 16 | Armen Miran, Felix Raphael | Ghost (Hernan Cattaneo & Marcelo Vasami Remix)  | 120 | 5.2 |
| 17 | Gorje Hewek | Actrice (Original Mix) | 120 | 5.5 |
| 18 | Gorje Hewek | Shroud in Your Warmth feat. Amonita (Original Mix) | 120 | 5.0 |
| 19 | Gorje Hewek | Amulet feat. M.O.S (Original Mix) | 120 | 5.1 |
| 20 | Roy Rosenfeld, Gorje Hewek, Dulus | Vida (Original Mix) | 122 | 5.6 |
| 21 | Hraach | Promises (Original Mix)  | 121 | 5.0 |
| 22 | Gorje Hewek | Aya feat. Lost Desert (Original Mix) | 121 | 6.5 |
| 23 | Jan Blomqvist | Our Broken Mind Embassy (Boris Brejcha Remix)  | 122 | 2.5 |
| 24 | Armen Miran & Lost Desert | Don't Worry | 124 | 6.4 |
| 25 | Armen Miran & Nicolas Rada | Pull (Original Mix)  | 122 | 5.6 |
| 26 | Jan Blomqvist, Alar, Korolova | Time Again (Original Mix)  | 123 | 5.2 |
| 27 | Jan Blomqvist, Mahri | Deeper Grounds feat. Mahri (Extended Mix) | 124 | 7.3 |
| 28 | Jan Blomqvist | The Space In Between (Ben Böhmer Extended Remix) | 122 | 6.8 |
| 29 | Oliver Schories, Jan Blomqvist | Packard (Monkey Safari Extended Remix) | 123 | 5.9 |
| 30 | Felix Raphael, Armen Miran & Cafe De Anatolia | Soul Guardian | 122 | 4.3 |


## Set 41. 41. Dulce Progresivo — Loveland Style — 2026-06-13
**Armado:** 2026-06-13  
**Duracion:** 3h  
**Tracks:** 34  
**BPM range:** 120-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Roy Rosenfeld | Kala  | 120 | 5.0 |
| 2 | Sebastien Leger | Quand Je Serai Seul  | 120 | 5.0 |
| 3 | Greta Meier | Enlightenment (Gaston Sosa Remix)  | 122 | 6.4 |
| 4 | Roy Rosenfeld | Nana (Original Mix) | 121 | 5.0 |
| 5 | Melodiam (AR) | Get Lost | 120 | 5.1 |
| 6 | Ezequiel Arias | Esperanza (Extended Mix) | 124 | 6.8 |
| 7 | Melodiam | Leuben (Orignal Mix)  | 120 | 5.5 |
| 8 | Sebastien Leger | Son of Sun (Original Mix)  | 121 | 5.0 |
| 9 | Joan Retamero, Greta Meier | The Beginning (Original Mix)  | 122 | 4.9 |
| 10 | Sebastian Sellares, Greta Meier | Benevolence (Extended Mix) | 121 | 5.0 |
| 11 | Sebastien Leger | Firefly (Original Mix)  | 121 | 5.0 |
| 12 | Christopher Erre, Greta Meier | Giza (Agustin Pietrocola Remix) | 123 | 5.7 |
| 13 | Sebastien Leger | Stevie (Original Mix)  | 121 | 5.0 |
| 14 | Roy Rosenfeld | Force Major (Original Mix)  | 121 | 5.0 |
| 15 | Roy Rosenfeld | Skyhook (Original Mix)  | 121 | 5.0 |
| 16 | Melodiam | Old Garden | 122 | 6.1 |
| 17 | Marsh | Beech Street (Simon Doty Extended Mix) | 122 | 5.8 |
| 18 | Melodiam (AR) | Flying Sequences (Original Mix)  | 122 | 4.9 |
| 19 | Melodiam (AR) | Trippin  | 122 | 5.4 |
| 20 | Greta Meier, Maze 28 | Acceptance (Original Mix) | 122 | 6.1 |
| 21 | Melodiam (AR) | Moon Arch | 123 | 5.9 |
| 22 | Roland Clark | I Get Deep (Roy Rosenfeld Extended Remix) | 124 | 6.0 |
| 23 | Kostya Outta, Greta Meier, Alisha (PL) | Far Above (Joaquin Salmain Remix) | 121 | 5.7 |
| 24 | Christopher Erre, Greta Meier | Osiris (Mayro Remix) | 123 | 6.2 |
| 25 | Simon Doty | Solstice (Extended Mix)  | 124 | 6.0 |
| 26 | Ezequiel Arias | Solar (Extended Mix) | 123 | 7.2 |
| 27 | Rauschhaus, Greta Meier | Painting in the Sky (Kamilo Sanclemente & Jossem Extended Remix) | 124 | 6.5 |
| 28 | Ezequiel Arias | Modern Memory (Extended Mix) | 122 | 6.3 |
| 29 | Sante, Re.you, Biishop | Do You Write (Roy Rosenfeld Remix)  | 120 | 5.0 |
| 30 | Ursula Rucker, Simon Doty | Hometown feat. Ursula Rucker (Extended Mix)  | 124 | 6.0 |
| 31 | Roy RosenfelD | Hypnosa De La Rosa  | 123 | 5.5 |
| 32 | Guy Gerber | Rainchecks In Montreal (Roy Rosenfeld Remix) | 120 | 6.0 |
| 33 | Simon Doty | The Beacon  | 124 | 6.0 |
| 34 | Roy RosenfelD | Creme  | 123 | 5.5 |


## Set 42. 42. Emi & Kamilo — Colorido Progresivo — 2026-06-13
**Armado:** 2026-06-13  
**Duracion:** 3h  
**Tracks:** 26  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Emi Galvan | Around the World | 122 | 5.8 |
| 2 | Emi Galvan | Trust (Original Mix) | 122 | 6.0 |
| 3 | Emi Galvan | No Regrets (Original Mix) | 123 | 6.5 |
| 4 | Emi Galvan | Supernova (Original Mix) | 123 | 7.3 |
| 5 | Emi Galvan | Free Your Mind | 122 | 7.5 |
| 6 | Emi Galvan | Taking Over (Rogier Remix) | 121 | 2.1 |
| 7 | Emi Galvan | Crabo (Original Mix)  | 122 | 5.9 |
| 8 | Kamilo Sanclemente | The Last Mermaid | 122 | 7.3 |
| 9 | Emi Galvan | Timeless (Original Mix)  | 121 | 2.9 |
| 10 | Kamilo Sanclemente | Delusion (Original Mix)  | 122 | 6.9 |
| 11 | Kamilo Sanclemente, Mauro Aguirre | Essence (Original Mix)  | 122 | 6.9 |
| 12 | Kamilo Sanclemente | Parallel Moon (Original Mix) | 123 | 7.0 |
| 13 | Kamilo Sanclemente | Divine Eternity (K Loveski Remix) | 121 | 4.8 |
| 14 | Kamilo Sanclemente | Go Home (Original Mix) | 121 | 5.7 |
| 15 | Kamilo Sanclemente, Giovanny Aparicio | Magic Carpet (Original Mix)  | 121 | 5.6 |
| 16 | Antrim, Kamilo Sanclemente, Paula OS | Once and Again (Bluum Extended Mix)  | 120 | 5.0 |
| 17 | Kamilo Sanclemente | Strange Days (Original Mix) | 121 | 6.3 |
| 18 | Guy Mantzur, Kamilo Sanclemente | Nectar (Original Mix) | 122 | 5.6 |
| 19 | Giovanny Aparicio, Kamilo Sanclemente | Crystal Cloud (Extended Mix)  | 120 | 4.8 |
| 20 | Greg Ochman | In Between Dreams  | 120 | 4.9 |
| 21 | Amir Telem | How To Learn Something New (Greg Ochman Remix) | 120 | 5.7 |
| 22 | D-Nox, Emi Galvan | Dualidad (Guy Mantzur Edit) | 124 | 6.7 |
| 23 | Mauro Picotto, CRW, Kamilo Sanclemente | I Feel Love (Extended Mix) | 123 | 6.8 |
| 24 | Dabeat, Kamilo Sanclemente | Seriously (Original Mix) | 122 | 6.5 |
| 25 | Ignacio Hernandez | Circle Of Lights (Claudio Cornejo (AR) Night Mix)  | 121 | 5.1 |
| 26 | Greg Ochman | Blinking Stars (Luka Sambe Remix)  | 123 | 5.7 |


## Set 43. 43. Maze 28 + Cendryma — Nuevo Prog — 2026-06-13
**Armado:** 2026-06-13  
**Duracion:** 3h  
**Tracks:** 28  
**BPM range:** 120-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Dimas Mixon, Cendryma | Minicube (Original Mix) | 120 | 4.9 |
| 2 | Cendryma | Effective Loss (Original Mix) | 121 | 5.5 |
| 3 | Muuk', Cendryma | G-Force (Original Mix) | 120 | 5.0 |
| 4 | Cendryma | Repressure (Extended Mix) | 121 | 5.7 |
| 5 | Cendryma | Mythica (Extended Mix) | 121 | 6.2 |
| 6 | Cendryma | Typical Use (Original Mix) | 121 | 5.2 |
| 7 | Maze 28 | Flux | 122 | 5.3 |
| 8 | Rockka | Synthesis  | 123 | 5.9 |
| 9 | Maze 28 | Red Lights From Afar | 122 | 5.6 |
| 10 | Maze 28 | Nocte | 122 | 6.1 |
| 11 | Rockka | Elevation  | 122 | 5.9 |
| 12 | Rockka | Subversion | 123 | 6.5 |
| 13 | Rockka | Initiation | 123 | 5.9 |
| 14 | Maze 28 | Stardust (Original Mix) | 121 | 5.4 |
| 15 | Hobin Rude | Nether (Original Mix) | 120 | 5.1 |
| 16 | Cary Crank | Echoes From Below (Weird Sounding Dude Remix) | 121 | 5.8 |
| 17 | Cary Crank | Deep Forest (Extended Mix) | 122 | 7.0 |
| 18 | Cary Crank | Inner Atlas (Kyotto Remix) | 122 | 6.2 |
| 19 | Gai Barone | Fractals (HAFT Extended Remix) | 122 | 5.7 |
| 20 | Gai Barone | Hemels (Original Mix) | 122 | 5.6 |
| 21 | Gai Barone, Dougal Fox | Ocean (Club Mix) | 122 | 6.6 |
| 22 | Gai Barone | Weird Behaviours (Original Mix) | 122 | 5.5 |
| 23 | Hobin Rude | Nothing's Gonna Hurt You | 122 | 5.8 |
| 24 | Chaum, Hobin Rude | Cressida (Tonaco Remix) | 122 | 6.2 |
| 25 | Hobin Rude | Shrouded Glint (Original Mix) | 122 | 6.7 |
| 26 | Ruben Karapetyan, Maze 28 | Cosmic Dot (Cid Inc. Remix) | 123 | 6.1 |
| 27 | Chelakhov | Rawai (Extended Mix) | 122 | 6.1 |
| 28 | Chelakhov | Searching (Gero Pellizzon Remix) | 122 | 5.8 |


## Set 44. 44. Dowden + Guy J — Progressive Profundo — 2026-06-13
**Armado:** 2026-06-13  
**Duracion:** 2.5h  
**Tracks:** 22  
**BPM range:** 119-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Dowden | Pacifist (Original Mix) | 121 | 4.8 |
| 2 | Dmitry Molosh | With Me (Original Mix) | 119 | 6.1 |
| 3 | Dowden, Mazayr | Deflator (Original Mix) | 121 | 5.3 |
| 4 | Dowden & Ric Niels | Coil (John Cosani Remix) | 122 | 5.7 |
| 5 | Dowden | Urias | 121 | 5.1 |
| 6 | Dmitry Molosh | Bird Flight (Original Mix) | 120 | 5.0 |
| 7 | Dmitry Molosh | Step by Step feat. Sasha Bartashevich (Original Dub Mix)  | 121 | 5.1 |
| 8 | Ric Niels & Dowden | Spiral (GMJ Remix) | 121 | 5.8 |
| 9 | Guy J | Nirvana | 120 | 5.0 |
| 10 | Dmitry Molosh | Butterfly (Analog Jungs Remix) | 121 | 5.1 |
| 11 | Navar & Dmitry Molosh | Small Wonders (Hernan Cattaneo & Marcelo Vasami Remix) | 122 | 6.6 |
| 12 | Navar & Dmitry Molosh | Small Wonders (Hernan Cattaneo & Marcelo Vasami Remix) | 122 | 6.6 |
| 13 | Hernan Cattaneo & Soundexile | Pick Up | 122 | 4.8 |
| 14 | Guy J | Karma (Original Mix) | 122 | 4.9 |
| 15 | Hernan Cattaneo & Soundexile | Astron (Original Mix)  | 122 | 6.3 |
| 16 | Guy J | State of Trance | 122 | 5.5 |
| 17 | Guy J | Illusion (Original Mix)  | 122 | 6.6 |
| 18 | Hernan Cattaneo & Soundexile | Pressure Drop | 122 | 5.5 |
| 19 | Yotto | Radiate (Extended Mix) | 124 | 6.0 |
| 20 | BOg, Diana Miro, 19:26 | Underwater (Hernan Cattaneo & Marcelo Vasami Remix) | 122 | 5.5 |
| 21 | John Digweed, Nick Muir, Captain Mustache | Bleu Cobalt (Alican Remix) | 125 | 6.0 |
| 22 | Orbital, Yotto | Belfast - Yotto Remix | 123 | 6.3 |


## Set 45. 45. Tom Pavicich + Durante — Prog Argentino — 2026-06-13
**Armado:** 2026-06-13  
**Duracion:** 2.5h  
**Tracks:** 24  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | FAERO, Tom Pavicich, Analog Sense | No Warm (Original Mix) | 118 | 3.1 |
| 2 | FAERO, Tom Pavicich, Analog Sense | The Landing (Original Mix) | 118 | 4.1 |
| 3 | Nicolas Rada | Prana  | 119 | 4.6 |
| 4 | Hraach | Cosmic Drama (Original Mix)  | 120 | 3.8 |
| 5 | Tom Pavicich, Analog Sense | Cardamom (FAERO Remix) | 121 | 4.9 |
| 6 | Durante, PaulWetz | Evaporate ft. PaulWetz (Original Mix) | 120 | 4.5 |
| 7 | Hraach | Delirio (Original Mix) | 120 | 4.9 |
| 8 | Tom Pavicich | About Her (Unai Garcia Remix) | 121 | 5.0 |
| 9 | Durante | Reaching (Weird Sounding Dude Extended Mix) | 120 | 4.7 |
| 10 | Tom Pavicich, Analog Sense | Cardamom (Original Mix) | 122 | 5.5 |
| 11 | Tom Pavicich | Volver (Sinan Arsan Remix) | 121 | 5.6 |
| 12 | Tirso Enriquez (AR), Tom Pavicich | Rumble (Original Mix) | 121 | 5.0 |
| 13 | Durante | Thread Tension  | 122 | 3.9 |
| 14 | Nicolas Rada | Tempelhof (Dmitry Molosh Remix) | 121 | 5.0 |
| 15 | Nicolas Rada | Cascadia | 122 | 6.5 |
| 16 | Durante | Winder  | 122 | 5.6 |
| 17 | Nicolas Rada | El Oro De Los Tigres | 122 | 4.5 |
| 18 | Hraach | Promises (Original Mix)  | 121 | 5.0 |
| 19 | FAERO, Tom Pavicich, Analog Sense | The Landing (Club Mix) | 123 | 6.0 |
| 20 | Tirso Enriquez (AR), Tom Pavicich | Mirage Rhythms (Original Mix) | 121 | 5.0 |
| 21 | FAERO, Tom Pavicich, Analog Sense | Evolve (Original Mix) | 123 | 5.1 |
| 22 | Hraach | Lonely Sun (Original Mix)  | 122 | 5.6 |
| 23 | Hana, Durante | Starglow (Extended Mix) | 124 | 6.4 |
| 24 | Simon Vaurambon | Leman (Original Mix) | 120 | 5.0 |


## Set 46. 46. Hernan Cattaneo — Warung Last Set Style — 2026-06-17
**Armado:** 2026-06-17  
**Duracion:** 3h  
**Tracks:** 26  
**BPM range:** 114-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | David August | Epikur (Original Mix) | 118 | 3.5 |
| 2 | Seth Schwarz & Be Svendsen | The Bar Tender | 121 | 5.0 |
| 3 | Troels Abrahamsen, Kolsch | All that Matters (Symphony of Unity - strings reimagined) | 125 | 6.0 |
| 4 | Makebo & Amonita | Back To The Roots (Extended Mix) | 122 | 5.5 |
| 5 | Caribou | Your Love Will Set You Free (C2's Set U Free Remix) | 120 | 5.0 |
| 6 | Gorje Hewek & Izhevski | Calinerie | 120 | 5.0 |
| 7 | Solomun | Never Sleep Again (Keinemusik Remix) | 120 | 5.0 |
| 8 | Hot Tuneik, Sarah Chilanti | Soul on Fire (Original Mix) | 120 | 5.0 |
| 9 | Nora En Pure | Spring Embers (Extended Mix)  | 122 | 5.5 |
| 10 | K Loveski | Check-a-Change (Federico Monachesi Remix) | 122 | 5.6 |
| 11 | Radio Slave | Strobe Queen | 120 | 5.0 |
| 12 | Simos Tagias, Tonaco | Alnilam (Original Mix) | 122 | 5.5 |
| 13 | Joe Goddard | Music Is The Answer (Hot Since 82 Remix) | 123 | 5.5 |
| 14 | Ed Steele, Anna Speedy | Don't Leave Me (D-Nox & André Moret Extended Remix) | 123 | 5.5 |
| 15 | Kostya Outta | Seguro (Paul James Nolan Remix) | 122 | 5.5 |
| 16 | Guy J | Dizzy Moments | 125 | 6.0 |
| 17 | Ezequiel Arias | Psychodelia (Extended Mix) | 125 | 6.0 |
| 18 | EdOne, Weizman | Misery (Original Mix) | 123 | 5.5 |
| 19 | K3V (SL) & Jayy Vibes | Kingdom of Dreams (Juan Ibanez Remix) | 122 | 5.5 |
| 20 | Pachanga Boys | Time | 124 | 6.0 |
| 21 | Depeche Mode | I Feel Loved (Danny Tenaglia's Labor Of Love Edit) | 128 | 6.5 |
| 22 | Guy Gerber | Timing (Original) | 126 | 6.5 |
| 23 | Maceo Plex, Chromatics | Shadow (Maceo Plex Remix) (Original Mix) | 126 | 6.5 |
| 24 | Der Dritte Raum | Hale Bopp (Maceo Plex Edit) | 125 | 6.0 |
| 25 | WhoMadeWho | Never Alone (Patrice Bäumel Remix)  | 124 | 6.0 |
| 26 | Chemical Brothers | Out of control (Teiko Yume's Frequent Flyer remix)  | 125 | 6.0 |


## Set 55. 55. Radar Oscuro — Hipnotico — 2h — 2026-08-03
**Armado:** 2026-08-03  
**Duracion:** 2h  
**Tracks:** 19  
**BPM range:** 118-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Cendryma | Crow's Cradle (Original Mix) | 118 | 3.7 |
| 2 | Maze 28 | Mindloop (Original Mix) | 120 | 4.8 |
| 3 | Maze 28 | Tell Me Again (Extended Mix) | 120 | 4.3 |
| 4 | Cendryma | Stasis Drive (Original Mix) | 120 | 4.7 |
| 5 | Cendryma | Meridian Isle (Original Mix) | 118 | 3.8 |
| 6 | Anthony Pappa, Fauxplay | Forever Seeking (Simon Vuarambon Remix) | 123 | 4.7 |
| 7 | Cendryma | Dividing Parts (Original Mix) | 121 | 5.1 |
| 8 | Guy J | Piece of Cake (Original Mix) | 122 | 5.2 |
| 9 | Dowden | Night Emeralds (Original Mix) | 122 | 5.8 |
| 10 | Cendryma | Fortress (Original Mix) | 122 | 6.2 |
| 11 | Simon Vuarambon | Stamina (Extended Mix)  | 121 | 5.2 |
| 12 | Simon Vuarambon | Estigia (Extended Mix)  | 121 | 5.2 |
| 13 | Danny Howells, Lloyd Barwood | One More Sky (Original Mix) | 124 | 6.0 |
| 14 | Maze 28 | Personal Space (Extended Mix) | 122 | 5.6 |
| 15 | Cendryma | Point Capricorn (Original Mix) | 122 | 6.3 |
| 16 | Halo Varga | Future (Guy J Remix) | 125 | 6.5 |
| 17 | Guy J | Rise (Original Mix) | 122 | 6.5 |
| 18 | Monolink | Perfect World (Colyn Remix) | 126 | 7.0 |
| 19 | Lost Desert | Black Panther (Original Mix) | 124 | 7.5 |


## Set 56. 56. Radar Colorido — Emi/Kamilo — 2h — 2026-08-03
**Armado:** 2026-08-03  
**Duracion:** 2h  
**Tracks:** 19  
**BPM range:** 120-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | GMJ, Matter | Verticality (Original Mix) | 121 | 4.9 |
| 2 | Makebo | Balance (Original Mix) | 122 | 5.6 |
| 3 | Emi Galvan | Mily (Original Mix) | 122 | 5.7 |
| 4 | Emi Galvan | I Wish (Original Mix) | 123 | 5.2 |
| 5 | Ezequiel Arias | Sin Control (Extended Mix) | 124 | 5.3 |
| 6 | Durante, Emi Galvan | Lunar Circuit (Extended Mix) | 124 | 5.7 |
| 7 | HANA, Ezequiel Arias | Go (Extended Mix) | 124 | 6.6 |
| 8 | Solis [US] | Symbiosis (Extended Mix) | 122 | 6.3 |
| 9 | Solis [US] | Una Volta (Extended Mix) | 123 | 6.6 |
| 10 | Kamilo Sanclemente | Auriga Moon (Original Mix) | 122 | 5.7 |
| 11 | Emi Galvan | Reborn (Original Mix) | 124 | 5.9 |
| 12 | Emi Galvan | Boomera (Original Mix) | 123 | 6.3 |
| 13 | Antrim | Curved (Original Mix) | 123 | 6.6 |
| 14 | Emi Galvan | Never Ending Summer (Original Mix) | 123 | 6.7 |
| 15 | Kamilo Sanclemente | Tangiers (Original Mix) | 123 | 6.7 |
| 16 | Kamilo Sanclemente, Mauro Aguirre | Looking For You (Extended Mix) | 123 | 6.7 |
| 17 | Kamilo Sanclemente & Jossem | Inner Motion (Original Mix)  | 123 | 6.9 |
| 18 | Kamilo Sanclemente | Just Come Back (Extended Mix) | 124 | 6.9 |
| 19 | Nicolas Viana | Kalira (Molac Extended Remix) | 124 | 7.2 |


## Set 57. 57. Radar Argentina — Driving — 2h — 2026-08-03
**Armado:** 2026-08-03  
**Duracion:** 2h  
**Tracks:** 19  
**BPM range:** 119-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Nick Warren & Nicolas Rada | Fuego (Extended Mix)  | 124 | 3.2 |
| 2 | GMJ, Matter, Zankee Gulati | Emerge (Original Mix) | 120 | 4.4 |
| 3 | Nicolas Rada | Roots (Original Mix) | 119 | 4.4 |
| 4 | Tom Pavicich, Gonzalo Cotroneo | Radiance (Original Mix) | 121 | 4.5 |
| 5 | Hernan Cattaneo, Tom Pavicich | Bloom (Original Mix) | 125 | 3.6 |
| 6 | Mercurio, Hernan Cattaneo | Diluted (Original Mix) | 121 | 4.8 |
| 7 | Rockka | Rebit (Original Mix) | 122 | 4.9 |
| 8 | Gai Barone | All About Her (Original Mix) | 122 | 5.2 |
| 9 | Tom Pavicich | You (Original Mix) | 123 | 5.5 |
| 10 | Gai Barone, Greta Meier | Elysium (Original Mix) | 121 | 4.9 |
| 11 | Andre Moret | Gaxyda (Original Mix) | 122 | 5.0 |
| 12 | Gai Barone | Taking Credits (Extended Mix)  | 122 | 5.0 |
| 13 | Andre Moret | Kryon (Original Mix) | 123 | 6.1 |
| 14 | Paul Deep (AR) | Tique (Original Mix) | 123 | 6.7 |
| 15 | Rockka | Cinimatic (Original Mix) | 123 | 7.7 |
| 16 | Gai Barone | Kromaky (Original Mix) | 123 | 6.3 |
| 17 | Kasey Taylor, Gai Barone | Spiral (Original Mix) | 124 | 6.5 |
| 18 | Zankee Gulati | Arakeen (Original Mix) | 121 | 4.8 |
| 19 | Jamie Stevens, Anthony Pappa | We Emerge (Original Mix) | 124 | 5.7 |


## Set 58. 58. Cocina I — Amanecer — 50min — 2026-08-06
**Armado:** 2026-08-06  
**Duracion:** 1h  
**Tracks:** 8  
**BPM range:** 118-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Jody Wisternoff & James Grant | Blue Space (feat. Jinadu) [Extended Mix] | 120 | 4.2 |
| 2 | Lane 8 ft. Solomon Grey | Diamonds (Original Mix) | 120 | 4.2 |
| 3 | Nils Hoffmann, Julia Church | 9 Days (Extended Mix)  | 120 | 5.0 |
| 4 | Ben Bohmer & Neils Hoffmann feat. Malou | Breathing  | 122 | 5.5 |
| 5 | Braxton | Torn (feat. Danni Wells) [Extended Mix] | 121 | 5.6 |
| 6 | Ezequiel Arias | Modern Memory (Extended Mix) | 122 | 6.3 |
| 7 | Sebastian Sellares | Timeless Era (Extended Mix) | 122 | 6.6 |
| 8 | Jakatta | American Dream (PROFF Extended Interpretation) | 122 | 7.1 |


## Set 59. 59. Cocina II — Ritual — 50min — 2026-08-06
**Armado:** 2026-08-06  
**Duracion:** 1h  
**Tracks:** 8  
**BPM range:** 118-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hraach | Apricot Tree (Original Mix)  | 118 | 1.0 |
| 2 | Armen Miran, Felix Raphael | Ghost (Hernan Cattaneo & Marcelo Vasami Remix)  | 120 | 5.2 |
| 3 | Hermanez | Third Decade  | 120 | 5.2 |
| 4 | Lee Burridge, Lost Desert | Moogami (Original Mix)  | 121 | 5.3 |
| 5 | Gorje Hewek | Actrice (Original Mix) | 120 | 5.5 |
| 6 | Bedouin | Flight of Birds | 120 | 5.6 |
| 7 | Seth Schwarz & Be Svendsen | The Bar Tender | 121 | 6.1 |
| 8 | Lee Burridge, Lost Desert | Forget (Original Mix)  | 121 | 6.5 |


## Set 60. 60. Cocina III — Mediodia — 50min — 2026-08-06
**Armado:** 2026-08-06  
**Duracion:** 1h  
**Tracks:** 8  
**BPM range:** 119-123  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Khen | Out Of A Dream (Original Mix)  | 121 | 4.7 |
| 2 | Chicola | Blueberries (Extended) | 122 | 5.1 |
| 3 | Roy Rosenfeld | Skyhook (Original Mix)  | 121 | 5.1 |
| 4 | Kasper Koman | The Observer  | 121 | 5.4 |
| 5 | Sebastien Leger | Stevie (Original Mix)  | 121 | 6.0 |
| 6 | Sebastien Leger | Firefly (Original Mix)  | 121 | 5.4 |
| 7 | Sébastien Léger | Forbidden Garden (Tim Green Remix)  | 122 | 6.7 |
| 8 | Cary Crank | Deep Forest (Extended Mix) | 122 | 7.0 |


## Set 61. 61. Progresivo Noche — 3h — 2026-08-06
**Armado:** 2026-08-06  
**Duracion:** 3h  
**Tracks:** 39  
**BPM range:** 120-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mike Rish | Sunset on Mars (Original Mix) | 120 | 4.2 |
| 2 | GMJ, Matter, Zankee Gulati | Emerge (Original Mix) | 120 | 4.4 |
| 3 | Mike rish | Cloudbreaker | 120 | 4.3 |
| 4 | Emi Galvan | Dharma (Original Mix)  | 120 | 4.4 |
| 5 | Hobin Rude | Low Light Memory (Original Mix) | 121 | 5.0 |
| 6 | Tom Pavicich, Gonzalo Cotroneo | Radiance (Original Mix) | 121 | 4.5 |
| 7 | Nicolas Rada | Glasgow (Original Mix) | 122 | 4.4 |
| 8 | Maze 28, Rockka | Corrosive  | 122 | 4.5 |
| 9 | Maze 28 | Aer8 | 122 | 5.6 |
| 10 | Guy J | Airborne (Original Mix) | 123 | 5.7 |
| 11 | Nick Warren | Ultravox (Hernan Cattaneo & Kevin Di Serna Remix) | 123 | 6.0 |
| 12 | Ruben Karapetyan | State of Progression (Original Mix) | 122 | 5.6 |
| 13 | Gai Barone | Fractals (HAFT Extended Remix) | 122 | 5.7 |
| 14 | Guy Mantzur & Khen | Where Is Home (Original Mix) | 122 | 5.7 |
| 15 | Lost Desert | Aalam Waahid (Original Mix) | 124 | 7.7 |
| 16 | GMJ & Matter | Metanoia | 122 | 5.7 |
| 17 | Kamilo Sanclemente | Whale Voices (Original Mix)  | 122 | 5.7 |
| 18 | Cendryma | Repressure (Extended Mix) | 121 | 5.7 |
| 19 | Dmitry Molosh | Ambition (Original Mix) | 121 | 6.3 |
| 20 | Gai Barone, Aman Anand | Low Era (Kebin Van Reeken Remix) | 122 | 6.7 |
| 21 | Ezequiel Arias | Control Is an Illusion (Original Mix) | 122 | 6.9 |
| 22 | Ezequiel Arias | Passenger (Original Mix) | 122 | 7.0 |
| 23 | Sahar Z & Guy Mantzur | Survivors Guilt | 125 | 7.0 |
| 24 | Nick Warren | Freebird (Emi Galvan Remix)  | 123 | 6.9 |
| 25 | NUFECTS | Inferno (Extended Mix) | 123 | 6.0 |
| 26 | Paul Arcane | Vortice (Extended Mix) | 123 | 6.3 |
| 27 | Kamilo Sanclemente | Fragma (GORKIZ Remix) | 123 | 7.1 |
| 28 | Miro | Paradise (Quivver Extended Remix) | 124 | 6.0 |
| 29 | Teho | Ashes (Original Mix) | 125 | 7.1 |
| 30 | GHEIST | Good Life (Original Mix) | 126 | 7.1 |
| 31 | Guy J | Dizzy Moments | 125 | 6.8 |
| 32 | Artic White | Once We Were (Extended Mix) | 123 | 8.0 |
| 33 | Sébastien Léger, Lost Miracle | Dodonpachi (Original Mix) | 122 | 6.4 |
| 34 | Tali Muss | Interlocutor (Extended Mix) | 122 | 5.7 |
| 35 | Hobin Rude | Nothing's Gonna Hurt You | 122 | 5.8 |
| 36 | Kasper Koman | Hi (Cid Inc. Remix)  | 122 | 5.8 |
| 37 | Tali Muss | Reward (Extended Mix) | 123 | 5.9 |
| 38 | Quivver | Forest Moon (Dmitry Molosh Remix) | 121 | 5.8 |
| 39 | Max Wexem | Confined (Original Mix) | 120 | 5.3 |


## Set 62. 62. Plano Suspendido — Afterhours — 1h30 — 2026-08-06
**Armado:** 2026-08-06  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Roger Martinez, Simos Tagias | Inner Light (Original Mix) | 120 | 4.6 |
| 2 | Shayan Pasha | Phobos (Extended Mix) | 120 | 4.9 |
| 3 | Katzen | What's Beyond (Original Mix) | 120 | 5.2 |
| 4 | MXV | Witch King (Original Mix) | 120 | 5.3 |
| 5 | Max Wexem | Override (Original Mix) | 121 | 4.7 |
| 6 | KAZKO | Fading Control (Original Mix) | 122 | 5.8 |
| 7 | Steven McCreery | Shadows (Original Mix) | 122 | 5.5 |
| 8 | Tonaco, Kebin Van Reeken | Chroma (Original Mix) | 121 | 5.4 |
| 9 | Ignacio Hernández, Tato Seco | Sleepwalker (Original Mix) | 122 | 5.4 |
| 10 | Rauschhaus, Cary Crank | Perihelion (Hernan Cattaneo & Mercurio Remix) | 123 | 6.7 |
| 11 | Fran Baigo | Levitate (Original Mix) | 123 | 6.1 |
| 12 | Alex O'Rion | Hartseer (Original Mix) | 120 | 4.3 |


## Set 63. 63. Color Sin Azucar — Prime Time — 1h30 — 2026-08-06
**Armado:** 2026-08-06  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Hobin Rude | The Quiet Between Us (Original Mix) | 121 | 5.1 |
| 2 | Zankee Gulati | Goofball (Original Mix) | 121 | 4.8 |
| 3 | Dmitry Molosh | The Moon Lights the Way (Original Mix) | 122 | 6.4 |
| 4 | Emil Toledo, Rinzen | The Shape of Memory (Extended Mix) | 123 | 5.1 |
| 5 | GRAZZE | Miami (Extended Mix) | 123 | 5.8 |
| 6 | Hicky & Kalo, Sinca | Breathe Again (Original Mix) | 123 | 5.2 |
| 7 | Florian Gasperini | Third Eye Awakening (Extended Mix) | 123 | 6.4 |
| 8 | Julian Nates | A Better Place (Original Mix) | 124 | 5.9 |
| 9 | Christian Smith | Illusion (Ezequiel Arias Remix) | 125 | 5.5 |
| 10 | Tali Muss, 84 Avenue | Nebula (Extended Mix) | 123 | 6.2 |
| 11 | Kasey Taylor | Emerging From the Skyline (Original Mix) | 122 | 5.2 |
| 12 | Sezer Uysal | Yutori (Ruben Karapetyan Remix) | 122 | 4.9 |


## Set 64. 64. Presion Constante — Peak — 1h30 — 2026-08-06
**Armado:** 2026-08-06  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | QuiQui, Thom Rich | Victorious (Gai Barone Dark Extended Remix) | 123 | 5.9 |
| 2 | Das Pharaoh, SHERRNX | Astral Abyss (Extended Mix) | 122 | 5.1 |
| 3 | Redspace, Diego Riga | Phantom Sun (Extended Mix) | 124 | 6.7 |
| 4 | Kit Lawson | Ruff (Original Mix) | 124 | 6.3 |
| 5 | Rodriguez Jr. | Off Gerlach (Original Mix) | 125 | 6.9 |
| 6 | Dilby | Body Talk (Original Mix) | 124 | 5.8 |
| 7 | Anthony Pappa, Aubrey Fry | Itajai (Original Mix) | 125 | 6.0 |
| 8 | Graziano Raffa | Carbonia (Original Mix) | 125 | 7.9 |
| 9 | Township Rebellion | Birds Fly First Class (Original Mix) | 126 | 6.0 |
| 10 | Kabi (AR), Ric Niels | Crossed Paths (Original Mix) | 124 | 6.0 |
| 11 | Serious Dancers | Canopus (Extended Mix) | 124 | 6.7 |
| 12 | D-Nox, Andre Moret | Breath (Original Mix) | 122 | 5.2 |


## Set 65. 65. Previa Colorida — Warmup — 1h — 2026-08-08
**Armado:** 2026-08-08  
**Duracion:** 1.0h  
**Tracks:** 9  
**BPM range:** 118-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mike Rish | Sunset on Mars (Original Mix) | 120 | 4.2 |
| 2 | Kasper Koman | Loco Motif (Tantum Remix)  | 121 | 5.0 |
| 3 | Emi Galvan | Dopamine (Forniva Remix)  | 123 | 5.2 |
| 4 | Kamilo Sanclemente, Andre Moret | Spectre (Extended Mix) | 122 | 5.5 |
| 5 | Maze 28 | Stardust (Original Mix) | 121 | 5.4 |
| 6 | D-Nox & Beckers | Bitter Rain (Cid Inc. Remix) | 123 | 6.3 |
| 7 | Kostya Outta, Greta Meier, Alisha (PL) | Far Above (Original Mix) | 123 | 6.3 |
| 8 | Tali Muss, Mayro | Dimension Of Space (Original Mix)  | 123 | 5.9 |
| 9 | Tonaco, Kebin Van Reeken | Chroma (Original Mix) | 121 | 5.4 |


## Set 66. 66. Previa Organica — Groove — 1h — 2026-08-08
**Armado:** 2026-08-08  
**Duracion:** 1.0h  
**Tracks:** 9  
**BPM range:** 118-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Gorje Hewek & Izhevski | When I Was Young (Original Mix) | 120 | 3.9 |
| 2 | Monolink | Sirens (H3RMES Edit)  | 120 | 4.9 |
| 3 | Sebastien Leger | Firefly (Original Mix)  | 121 | 5.4 |
| 4 | Hraach | Promises (Original Mix)  | 121 | 5.0 |
| 5 | Khen & Freedom Fighters | Levantine | 122 | 5.1 |
| 6 | Hermanez | Gamma Ray | 123 | 6.0 |
| 7 | Lee Burridge, Lost Desert | Forget (Original Mix)  | 121 | 6.5 |
| 8 | Armen Miran & Nicolas Rada | Pull (Original Mix)  | 122 | 5.6 |
| 9 | Rodriguez Jr. | Nairobi (Original Mix)  | 124 | 5.1 |


## Set 67. 67. Previa Brillante — Vocal — 1h — 2026-08-08
**Armado:** 2026-08-08  
**Duracion:** 1.0h  
**Tracks:** 9  
**BPM range:** 118-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Jody Wisternoff & James Grant | Blue Space (feat. Jinadu) [Extended Mix] | 120 | 4.2 |
| 2 | Muuk', Cendryma | G-Force (Original Mix) | 120 | 5.0 |
| 3 | Panama, Nils Hoffmann | Far Behind (Jeremy Olander Extended Mix) | 123 | 5.4 |
| 4 | Spencer Brown | Comeback Kids (Original Mix) | 124 | 6.1 |
| 5 | Hana, Durante | Celestia (Extended Mix)  | 124 | 5.7 |
| 6 | Tinlicker | Compound (Extended Mix)  | 124 | 6.1 |
| 7 | Ben Bohmer | In Memoriam | 124 | 6.6 |
| 8 | Tom Pavicich, Analog Sense | Cardamom (Original Mix) | 122 | 5.7 |
| 9 | Lane 8 | Keep On (Extended Mix)  | 122 | 5.1 |


## Set 68. 68. Superficie — Groove Directo — 1h30 — 2026-08-09
**Armado:** 2026-08-11  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 121-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mita Gami | San Pedro  | 122 | 4.3 |
| 2 | Pavel Petrov, Rafael Cerato | Reflections (Original mix) | 122 | 4.5 |
| 3 | Jeremy Olander | Panorama (Original Mix) | 123 | 4.9 |
| 4 | Dowden, Mazayr | Deflator (Original Mix) | 121 | 5.3 |
| 5 | Ric Niels & Juan Buitrago | Glide  | 123 | 5.5 |
| 6 | Danny Serrano | The Haven (Dilby Extended Remix) | 123 | 5.7 |
| 7 | Dilby | Soul Vision (Original Mix) | 125 | 6.1 |
| 8 | Durante, Enamour | Taos Hum | 126 | 6.3 |
| 9 | Redspace, Diego Riga | Phantom Sun (Extended Mix) | 124 | 6.7 |
| 10 | Dosem | Chosen | 124 | 6.8 |
| 11 | Nox Vahn | Brainwasher (Warung Extended Mix)  | 123 | 6.8 |
| 12 | Kit Lawson | Ruff (Original Mix) | 124 | 6.3 |


## Set 69. 69. Superficie — Sudbeat Argentino — 1h30 — 2026-08-09
**Armado:** 2026-08-11  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Paul Deep (AR) | Melodramatic (Original Mix) | 122 | 4.8 |
| 2 | Melodiam (AR) | Juno | 120 | 4.9 |
| 3 | Hernan Cattaneo & Soundexile | Deneb | 122 | 4.9 |
| 4 | Chicola, Guy Mantzur | Neon Bible (Original Mix) | 122 | 5.3 |
| 5 | Beckers, D-Nox | Skylab (Original Mix)  | 122 | 5.6 |
| 6 | Julian Nates | A Better Place (Original Mix) | 124 | 5.9 |
| 7 | Gai Barone | Kromaky (Original Mix) | 123 | 6.3 |
| 8 | Antrim | Curved (Original Mix) | 123 | 6.6 |
| 9 | Roger Martinez | Cosmic Drum (Paul Deep Remix) | 123 | 6.8 |
| 10 | Cid Inc. | Citadel (Original Mix)  | 123 | 7.0 |
| 11 | Marcelo Vasami | Shades Of Blue (Original Mix)  | 122 | 6.7 |
| 12 | Melodiam | No Way Out | 122 | 6.3 |


## Set 70. 70. Superficie — Colorize Vocal — 1h30 — 2026-08-09
**Armado:** 2026-08-11  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | GMJ, Matter, Zankee Gulati | Emerge (Original Mix) | 120 | 4.4 |
| 2 | Le Youth | About Us (Extended Mix)  | 122 | 4.7 |
| 3 | Rockka | Rebit (Original Mix) | 122 | 4.9 |
| 4 | Ruben Karapetyan | Neurotransmitter (Extended Mix) | 123 | 5.5 |
| 5 | Braxton | Torn (feat. Danni Wells) [Extended Mix] | 121 | 5.6 |
| 6 | GRAZZE | Miami (Extended Mix) | 123 | 5.8 |
| 7 | Cary Crank | Inner Atlas (Kyotto Remix) | 122 | 6.2 |
| 8 | Ursula Rucker, Simon Doty | Hometown feat. Ursula Rucker (Extended Mix)  | 124 | 6.0 |
| 9 | Hobin Rude | Shrouded Glint (Original Mix) | 122 | 6.7 |
| 10 | Bondarev, Max Wexem | The Lotus (Original Mix) | 123 | 7.2 |
| 11 | Orbital, Yotto | Belfast - Yotto Remix | 123 | 6.3 |
| 12 | Rauschhaus | If I Had Wings  | 121 | 5.9 |


## Set 71. 71. Presion — Peak Groove — 1h30 — 2026-08-11
**Armado:** 2026-08-11  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 121-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Khen | Out Of A Dream (Original Mix)  | 121 | 4.7 |
| 2 | D-Nox, Stereo Underground | Salt & Pepper (Original Mix)  | 123 | 5.7 |
| 3 | Dilby | Sensei (Original Mix) | 124 | 5.4 |
| 4 | DJ Paul (AR), Andre Moret & Nahs | Spiritual Balance | 124 | 5.9 |
| 5 | Maze 28 | Cry of the Deserts (Molac & Nicolas Viana Remix) | 122 | 5.8 |
| 6 | Dmitry Molosh, Michael A | Integral (Original Mix)  | 122 | 6.1 |
| 7 | Roy RosenfelD | Hypnosa De La Rosa  | 123 | 6.4 |
| 8 | Spencer Brown | Blue Magic (feat. Danny Shamoun) | 123 | 6.7 |
| 9 | Kamilo Sanclemente | Fragma (GORKIZ Remix) | 123 | 7.1 |
| 10 | Massano | The Feeling (2022 Remaster) | 124 | 7.0 |
| 11 | Tali Muss | Azal (Original Mix) | 123 | 6.9 |
| 12 | Durante & Altieri, James, Ron Carroll | I Like The Way (Ron Carroll Chicago Disko Mix) | 124 | 5.1 |


## Set 72. [POOL] Nuevos Agosto 2026 — Dilby / D-Nox / Moret / Durante
**Armado:** 2026-08-11  
**Duracion:** 1.5h  
**Tracks:** 16  
**BPM range:** 118-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Dilby | Remember Me (Extended Mix)  | 124 | 3.2 |
| 2 | Andre Moret | Young Movements  | 120 | 4.1 |
| 3 | Durante & Altieri, James, Ron Carroll | I Like The Way (Ron Carroll Chicago Disko Mix) | 124 | 5.1 |
| 4 | Dilby | Sensei (Original Mix) | 124 | 5.4 |
| 5 | D-Nox, Stereo Underground | Salt & Pepper (Original Mix)  | 123 | 5.7 |
| 6 | Danny Serrano | The Haven (Dilby Extended Remix) | 123 | 5.7 |
| 7 | Dilby | Addicted | 124 | 5.7 |
| 8 | Dilby | Last Word (Original Mix) | 124 | 5.8 |
| 9 | DJ Paul (AR), Andre Moret & Nahs | Spiritual Balance | 124 | 5.9 |
| 10 | Dilby | Soul Vision (Original Mix) | 125 | 6.1 |
| 11 | Hernan Cattaneo, Audio Junkies | A Major Minor (D-Nox & Beckers Remix)  | 125 | 6.4 |
| 12 | Dilby | Connect the Dots (Oliver Schories & Gorge Remix)  | 124 | 6.6 |
| 13 | DJ Paul (AR), Andre Moret & Nahs | Experience | 124 | 6.7 |
| 14 | Dilby | Pranayama  | 124 | 6.8 |
| 15 | D-Nox | Full Moon (Original Mix)  | 125 | 7.4 |
| 16 | Stereo Underground feat. Sealine | Flashes (D-Nox & Beckers Remix)  | 123 | 7.4 |


## Set 73. 73. Dilby & Co — Showcase Groove — 1h30 — 2026-08-12
**Armado:** 2026-08-13  
**Duracion:** 1.5h  
**Tracks:** 12  
**BPM range:** 121-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Dilby | Remember Me (Extended Mix)  | 124 | 3.2 |
| 2 | Durante | Thread Tension  | 122 | 3.9 |
| 3 | Jeremy Olander | Saigon  | 123 | 4.9 |
| 4 | Sebastien Leger, Roy Rosenfeld | Panko Day (Extended Mix) | 121 | 5.0 |
| 5 | Cid Inc. | Abyss  | 123 | 5.5 |
| 6 | Dilby | Connect the Dots (Oliver Schories & Gorge Remix)  | 124 | 6.6 |
| 7 | DJ Paul (AR), Andre Moret & Nahs | Experience | 124 | 6.7 |
| 8 | Stereo Underground feat. Sealine | Flashes (D-Nox & Beckers Remix)  | 123 | 7.4 |
| 9 | Hermanez, Lost Desert | Other Side (Original Mix) | 123 | 7.1 |
| 10 | Sahar Z & Guy Mantzur | Future Memories | 125 | 6.9 |
| 11 | Dilby | Pranayama  | 124 | 6.8 |
| 12 | Hana, Durante | Starglow (Extended Mix) | 124 | 6.4 |


## Set 74. 74. Puerta — Apertura — 2h — 2026-08-13
**Armado:** 2026-08-13  
**Duracion:** 2.0h  
**Tracks:** 16  
**BPM range:** 117-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Yohai Mor | Keep It Dark (Dowden Reformat) | 121 | 2.1 |
| 2 | Kamilo Sanclemente, Andre Moret | Surge (Original Mix) | 122 | 2.5 |
| 3 | Sudhaus & The Wash | Spectron (Jamie Stevens Remix) | 122 | 2.5 |
| 4 | Nox Vahn & Marsh | Come Together (Extended Mix) | 120 | 3.5 |
| 5 | Sebastien Leger, Roy Rosenfeld, Lost Miracle | Closer To You (Extended Mix) | 120 | 3.9 |
| 6 | Adam Ten, Mita Gami | Lego  | 120 | 4.0 |
| 7 | Emi Galvan | Alfa Zeta (Original Mix) | 120 | 4.4 |
| 8 | 16BL, Nour | Sharks (Extended Mix) | 120 | 4.1 |
| 9 | Jody Wisternoff & James Grant | Blue Space (feat. Jinadu) | 120 | 4.2 |
| 10 | Sebastian Sellares, Greta Meier | Benevolence (Paul Thomas Extended Remix) | 122 | 4.7 |
| 11 | Guy Mantzur | Homecoming (Original Mix) | 123 | 4.8 |
| 12 | Mike Rish | Dope Riddim (Original Mix) | 122 | 5.1 |
| 13 | Dmitry Molosh | Bustle (Original Mix) | 120 | 5.4 |
| 14 | Rockka, Maze 28 | Mirage (Juan Ibanez Extended Mix) | 122 | 5.2 |
| 15 | Paul Hazendonk, Return To Saturn | You Can Have It All  (Peter Makto & Matthew Sona Remix) | 121 | 5.0 |
| 16 | Ben Böhmer & Tinlicker | Run Away (feat. Felix Raphael) [Extended Mix] | 122 | 4.8 |


## Set 75. 75. La Ultima Hora — Cierre Euforico — 1h15 — 2026-08-13
**Armado:** 2026-08-13  
**Duracion:** 1.25h  
**Tracks:** 10  
**BPM range:** 123-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | ANMA | Adya | 124 | 6.8 |
| 2 | Guy J | Catfish (Jonas Saalbach Remix) | 124 | 7.4 |
| 3 | Gorje Hewek, ETNE | Children (Extended Mix) | 124 | 7.3 |
| 4 | Durante & Maz (BR) | Ivory | 126 | 7.4 |
| 5 | Colyn | The Future Is the Past | 126 | 7.6 |
| 6 | Ferry Corsten, Dirty South | Carte Blanche (Extended Mix) | 124 | 7.5 |
| 7 | Jan Blomqvist, Mahri | Deeper Grounds feat. Mahri (Extended Mix) | 124 | 7.3 |
| 8 | D-Nox, Stereo Underground | Shooting Stars (Extended Version)  | 125 | 7.6 |
| 9 | Andy Moor & Adam White | The Whiteroom (feat. Whiteroom) [Marsh Extended Mix] | 125 | 8.6 |
| 10 | Maze 28 | Great Attractor (Ruben Karapetyan Remix) | 124 | 7.5 |


## Set 76. [POOL] Detonantes — E>=7.5 — uno o dos por set, al 70-85%
**Armado:** 2026-08-13  
**Duracion:** 1.5h  
**Tracks:** 24  
**BPM range:** 118-128  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Adriatique | Mystery (Tale Of Us & Mathame Remix)  | 124 | 8.8 |
| 2 | Andy Moor & Adam White | The Whiteroom (feat. Whiteroom) [Marsh Extended Mix] | 125 | 8.6 |
| 3 | CamelPhat, Jem Cooke, Cristoph | Breathe (Original Mix)  | 125 | 8.4 |
| 4 | Fuscarini | Le Souffle (Kevin Di Serna & Santor Remix) | 127 | 8.3 |
| 5 | Ferry Corsten, Marsh | Attraction (Marsh's Extended Mix) | 126 | 8.3 |
| 6 | Carlita & Calussa | Fell In Luv (Black Circle Extended Remix)  | 126 | 8.1 |
| 7 | Mrak, Braev | The World Is Yours (Extended Mix) | 126 | 8.0 |
| 8 | ECHO DAFT, Kebin Van Reeken | Years of Ascent (Original Mix) | 122 | 8.0 |
| 9 | Artic White | Once We Were (Extended Mix) | 123 | 8.0 |
| 10 | Graziano Raffa | Carbonia (Original Mix) | 125 | 7.9 |
| 11 | Jamie Stevens, Zankee Gulati | Low Tide (Ezequiel Arias Remix) | 125 | 7.8 |
| 12 | Gorje Hewek | Forest Song in the Night (Original Mix) | 123 | 7.8 |
| 13 | Rockka | Cinimatic (Original Mix) | 123 | 7.7 |
| 14 | Lost Desert | Aalam Waahid (Original Mix) | 124 | 7.7 |
| 15 | After Sunrise | Tequila Sunrise (Original Mix) | 128 | 7.6 |
| 16 | D-Nox, Stereo Underground | Shooting Stars (Extended Version)  | 125 | 7.6 |
| 17 | Colyn | The Future Is the Past | 126 | 7.6 |
| 18 | Maze 28 | Great Attractor (Ruben Karapetyan Remix) | 124 | 7.5 |
| 19 | Ben Bohmer | Beyond Beliefs (Original Mix) | 124 | 7.5 |
| 20 | Emi Galvan | Free Your Mind | 122 | 7.5 |
| 21 | Cid Inc., Dmitry Molosh | Impending Storm (Navar Remix) | 122 | 7.5 |
| 22 | Ferry Corsten, Dirty South | Carte Blanche (Extended Mix) | 124 | 7.5 |
| 23 | Rauschhaus | Galapagos (Original Mix) | 124 | 7.5 |
| 24 | Lost Desert | Black Panther (Original Mix) | 124 | 7.5 |


## Set 80. 80. Hernan Cattaneo Style — Progressive Argentino
**Armado:** 2026-09-03  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mike Rish | The Likes of You (Original Mix) | 120 | 3.9 |
| 2 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 4.0 |
| 3 | Kebin Van Reeken | Endurance (Original Mix) | 121 | 4.3 |
| 4 | Mike Rish | Primah (Original Mix) | 120 | 4.4 |
| 5 | Durante | Reaching (Weird Sounding Dude Extended Mix) | 120 | 4.7 |
| 6 | Melodiam (AR) | Juno | 120 | 4.9 |
| 7 | Armen Miran & Nicolas Rada | Fall Away (Original Mix)  | 120 | 5.2 |
| 8 | Emi Galvan & Albuquerque | Stay High | 122 | 5.4 |
| 9 | Cendryma | Orbitation (Extended Mix) | 122 | 5.6 |
| 10 | Julian Nates, Julieta Kühnle | Fever (Extended Mix) | 123 | 5.9 |
| 11 | Khen | Closing Doors (Original Mix) | 124 | 6.1 |
| 12 | Kamilo Sanclemente, M.O.S., Andre Moret | Perception (Original Mix) | 122 | 6.3 |
| 13 | Cid Inc. | Forgotten | 123 | 6.6 |
| 14 | Cendryma | Wakefeld (Original Mix) | 122 | 6.8 |
| 15 | Cary Crank | Deep Forest (Extended Mix) | 122 | 7.0 |
| 16 | Paul Deep (AR) | Tique (Original Mix) | 123 | 6.7 |
| 17 | D-Nox, Andre Moret | Brisa (Extended Mix) | 123 | 6.4 |
| 18 | Durante, ALLKNIGHT | How Does It Feel (Extended Mix) | 125 | 6.0 |


## Set 81. 81. Ezequiel Arias Style — Peak Vocal
**Armado:** 2026-09-03  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Kasper Koman | Wilder (Extended Mix)  | 120 | 4.2 |
| 2 | Mike Rish | Primah (Original Mix) | 120 | 4.4 |
| 3 | Khen | Out Of A Dream (Original Mix)  | 121 | 4.7 |
| 4 | D-Nox, Andre Moret | Six (Extended Mix) | 122 | 4.9 |
| 5 | Mike Rish | Dope Riddim (Original Mix) | 122 | 5.1 |
| 6 | Tom Pavicich | Sugar Rush (Original Mix)  | 123 | 5.3 |
| 7 | Roy Rosenfeld, Gorje Hewek, Dulus | Vida (Original Mix) | 122 | 5.6 |
| 8 | Quivver, Dave Seaman | The Water's Edge (Original Mix) | 122 | 5.8 |
| 9 | Kamilo Sanclemente | No Regrets (Extended Mix) | 123 | 6.0 |
| 10 | Cendryma | Evasive (Extended Mix) | 121 | 6.3 |
| 11 | Gorkiz, Luca Abayan | Drowner (Extended Mix) | 122 | 6.5 |
| 12 | Marcelo Vasami | Shades Of Blue (Original Mix)  | 122 | 6.7 |
| 13 | Guy Mantzur, Kamilo Sanclemente | The Future is in the Past (Original Mix) | 124 | 6.9 |
| 14 | Rauschhaus | Waiting For The Birds  | 123 | 7.2 |
| 15 | D-Nox, Andre Moret | Shine (Extended Mix) | 124 | 7.4 |
| 16 | Rockka | Amnesia (Fuenka Remix) | 123 | 6.9 |
| 17 | Cendryma | Wakefeld (Original Mix) | 122 | 6.8 |
| 18 | Armen Miran & Lost Desert | Don't Worry | 124 | 6.4 |


## Set 82. 82. Emi Galvan Style — Progresivo Colorido
**Armado:** 2026-09-03  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy Mantzur | Tremolo Man (Original Mix) | 120 | 4.0 |
| 2 | Kasper Koman | Wilder (Extended Mix)  | 120 | 4.2 |
| 3 | Nicolas Rada | El Oro De Los Tigres | 122 | 4.5 |
| 4 | Durante | Reaching (Weird Sounding Dude Extended Mix) | 120 | 4.7 |
| 5 | Gorje Hewek, Molac, Dulus | Astro World (Original Mix) | 120 | 4.9 |
| 6 | Hobin Rude | Nether (Original Mix) | 120 | 5.1 |
| 7 | Dmitry Molosh | Bustle (Original Mix) | 120 | 5.4 |
| 8 | Cendryma | Orbitation (Extended Mix) | 122 | 5.6 |
| 9 | Rauschhaus, GRAZZE | Canacona (Original Mix) | 121 | 5.8 |
| 10 | Dmitry Molosh, Michael A | Integral (Original Mix)  | 122 | 6.1 |
| 11 | Cendryma | Evasive (Extended Mix) | 121 | 6.3 |
| 12 | Rockka | Subversion | 123 | 6.5 |
| 13 | Marcelo Vasami | Shades Of Blue (Original Mix)  | 122 | 6.7 |
| 14 | Cid Inc. | Citadel (Original Mix)  | 123 | 7.0 |
| 15 | Rauschhaus | Waiting For The Birds  | 123 | 7.2 |
| 16 | Guy Mantzur, Kamilo Sanclemente | The Future is in the Past (Original Mix) | 124 | 6.9 |
| 17 | Cid Inc. | Forgotten | 123 | 6.6 |
| 18 | Simon Vuarambon & Tantum | Lake Of Fire | 122 | 6.2 |


## Set 83. 83. Kamilo Sanclemente Style — Colombia Progresiva
**Armado:** 2026-09-03  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Simon Vuarambon & Tantum | Zenith | 119 | 4.0 |
| 2 | Kebin Van Reeken | Dreaming (Original Mix) | 120 | 4.3 |
| 3 | Tom Pavicich, Gonzalo Cotroneo | Radiance (Original Mix) | 121 | 4.5 |
| 4 | Ric Niels | Lose to Win  | 121 | 4.7 |
| 5 | Dowden | Pacifist (Original Mix) | 121 | 4.8 |
| 6 | Dmitry Molosh | Butterfly (Analog Jungs Remix) | 121 | 5.1 |
| 7 | Ric Niels | Osmio (Original Mix) | 120 | 5.4 |
| 8 | Maze 28 | Aer8 | 122 | 5.6 |
| 9 | Sebastian Sellares | Abaddon (Extended Mix) | 121 | 5.8 |
| 10 | Tali Muss | Garip (Original Mix)  | 122 | 6.1 |
| 11 | Emi Galvan | Boomera (Original Mix) | 123 | 6.3 |
| 12 | Nicolas Rada | Cascadia | 122 | 6.5 |
| 13 | Hobin Rude | Shrouded Glint (Original Mix) | 122 | 6.7 |
| 14 | Tali Muss | Azal (Original Mix) | 123 | 6.9 |
| 15 | Kamilo Sanclemente | Fragma (GORKIZ Remix) | 123 | 7.1 |
| 16 | Cid Inc. | Citadel (Original Mix)  | 123 | 7.0 |
| 17 | Ruben Karapetyan | Pantheon (Emi Galvan Remix) | 124 | 6.6 |
| 18 | Christopher Erre, Greta Meier | Osiris (Mayro Remix) | 123 | 6.2 |


## Set 84. 84. Sudbeat Sessions — Driving Progressive
**Armado:** 2026-09-03  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 120-126  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mike Rish | Tornn (Original Mix) | 120 | 4.2 |
| 2 | Dmitry Molosh | Bird Flight (Original Mix) | 120 | 4.5 |
| 3 | Sebastian Sellares, Greta Meier | Benevolence (Paul Thomas Extended Remix) | 122 | 4.7 |
| 4 | D-Nox, Andre Moret | Six (Extended Mix) | 122 | 4.9 |
| 5 | Mike Rish | Dope Riddim (Original Mix) | 122 | 5.1 |
| 6 | Dmitry Molosh | Bustle (Original Mix) | 120 | 5.4 |
| 7 | Roy Rosenfeld, Gorje Hewek, Dulus | Vida (Original Mix) | 122 | 5.6 |
| 8 | Maze 28 | Cry of the Deserts (Aman Anand Remix) | 121 | 5.9 |
| 9 | Cendryma | Focus Bend (Tiefstone Remix) | 123 | 6.1 |
| 10 | Tom Pavicich | Josefina (Casnik Remix) | 123 | 6.3 |
| 11 | Madloch & Antti Rasi | Salty Roads (Cid Inc Remix) | 123 | 6.6 |
| 12 | Nick Warren | Freebird (Emi Galvan Remix)  | 123 | 6.9 |
| 13 | Kamilo Sanclemente | Parallel Moon (Original Mix) | 123 | 7.0 |
| 14 | D-Nox, Baya, LENN V | Silence (Extended Mix)  | 124 | 7.3 |
| 15 | Durante & Maz (BR) | Ivory | 126 | 7.4 |
| 16 | Kamilo Sanclemente, Zalvador | Elyseum (Weird Sounding Dude Extended Remix) | 124 | 7.0 |
| 17 | Rockka, Maze 28 | Mirage (Extended Mix) | 123 | 6.8 |
| 18 | Gorkiz, Luca Abayan | Drowner (Extended Mix) | 122 | 6.5 |


## Set 85. 85. Mango Alley — Deep Progressive
**Armado:** 2026-09-03  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Simon Vuarambon & Tantum | Zenith | 119 | 4.0 |
| 2 | Kebin Van Reeken | Dreaming (Original Mix) | 120 | 4.3 |
| 3 | Tom Pavicich, Gonzalo Cotroneo | Radiance (Original Mix) | 121 | 4.5 |
| 4 | Ric Niels | Lose to Win  | 121 | 4.7 |
| 5 | Dowden | Pacifist (Original Mix) | 121 | 4.8 |
| 6 | Dmitry Molosh, Michael A | Twelve Days (Original Mix)  | 122 | 5.2 |
| 7 | Emi Galvan & Albuquerque | Stay High | 122 | 5.4 |
| 8 | Guy J | Worlds Apart (Original Mix) | 122 | 5.7 |
| 9 | Julian Nates, Julieta Kühnle | Fever (Extended Mix) | 123 | 5.9 |
| 10 | Ezequiel Arias | Airwave (Original Mix) | 123 | 6.1 |
| 11 | Kamilo Sanclemente, Mauro Aguirre | Goldes Eyes (Original Mix) | 123 | 6.4 |
| 12 | Nicolas Rada | The Wind Phone | 123 | 6.6 |
| 13 | Nick Warren | Freebird (Emi Galvan Remix)  | 123 | 6.9 |
| 14 | Ric Niels | Invasion  | 123 | 7.1 |
| 15 | D-Nox, Baya, LENN V | Silence (Extended Mix)  | 124 | 7.3 |
| 16 | Ezequiel Arias | Perfect Dream (Extended Mix) | 124 | 7.0 |
| 17 | Navar & Dmitry Molosh | Small Wonders (Hernan Cattaneo & Marcelo Vasami Remix) | 122 | 6.6 |
| 18 | Kamilo Sanclemente | Strange Days (Original Mix) | 121 | 6.3 |


## Set 86. 86. Simon Vuarambon Style — Hipnotico
**Armado:** 2026-09-03  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 118-124  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mike Rish | Tú Attair (Original Mix) | 119 | 3.5 |
| 2 | Cendryma | Crow's Cradle (Original Mix) | 118 | 3.7 |
| 3 | Rauschhaus, Cary Crank | Tapestry of Perception (Extended Mix) | 120 | 4.0 |
| 4 | Kebin Van Reeken | Endurance (Original Mix) | 121 | 4.3 |
| 5 | Emi Galvan | Alfa Zeta (Original Mix) | 120 | 4.4 |
| 6 | Gorje Hewek | U & Eyeye | 122 | 4.7 |
| 7 | Kasper Koman | Loco Motif (Tantum Remix)  | 121 | 5.0 |
| 8 | Gorkiz, Andre Moret | H Feelings (Original Mix) | 122 | 5.3 |
| 9 | Cendryma | Effective Loss (Original Mix) | 121 | 5.5 |
| 10 | Quivver, Dave Seaman | The Water's Edge (Original Mix) | 122 | 5.8 |
| 11 | Sebastian Sellares, Greta Meier | Benevolence (Extended Mix) | 121 | 6.0 |
| 12 | Tom Pavicich | Josefina (Casnik Remix) | 123 | 6.3 |
| 13 | Ezequiel Arias | Heat Above - Original Mix | 124 | 6.5 |
| 14 | Kamilo Sanclemente, Mauro Aguirre | Looking For You (Extended Mix) | 123 | 6.7 |
| 15 | Cary Crank | Deep Forest (Extended Mix) | 122 | 7.0 |
| 16 | Nicolas Rada | The Wind Phone | 123 | 6.6 |
| 17 | Kamilo Sanclemente | Strange Days (Original Mix) | 121 | 6.3 |
| 18 | Gorje Hewek | Solovey (Original Mix) | 122 | 5.9 |


## Set 87. 87. Nick Warren Style — The Soundgarden
**Armado:** 2026-09-03  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mike Rish | Tornn (Original Mix) | 120 | 4.2 |
| 2 | Ric Niels | Morning Dew (Original Mix) | 120 | 4.2 |
| 3 | Dmitry Molosh | Bird Flight (Original Mix) | 120 | 4.5 |
| 4 | Sebastian Sellares, Greta Meier | Benevolence (Paul Thomas Extended Remix) | 122 | 4.7 |
| 5 | Chicola, Guy Mantzur | Galactica (Original Mix) | 122 | 4.9 |
| 6 | Cendryma | Dividing Parts (Original Mix) | 121 | 5.1 |
| 7 | Cary Crank | Open Sea (Ric Niels Remix) | 121 | 5.4 |
| 8 | Kamilo Sanclemente | Honest (Leandro Murua Remix) | 122 | 5.6 |
| 9 | Maze 28 | Cry of the Deserts (Molac & Nicolas Viana Remix) | 122 | 5.8 |
| 10 | Cendryma | Focus Bend (Tiefstone Remix) | 123 | 6.1 |
| 11 | Cid Inc. | Rescue Me (Original Mix)  | 123 | 6.2 |
| 12 | Guy J | Rise (Original Mix) | 122 | 6.5 |
| 13 | Kamilo Sanclemente, Mauro Aguirre | Looking For You (Extended Mix) | 123 | 6.7 |
| 14 | Maze 28 | Leave the World Behind (Original Mix) | 122 | 7.0 |
| 15 | NOIYSE PROJECT, Hernan Cattaneo, Jamie Stevens | Remember Me - Hernan Cattaneo & Jamie Stevens Remix | 122 | 7.3 |
| 16 | Rockka | Amnesia (Fuenka Remix) | 123 | 6.9 |
| 17 | Khen | The Lighthouse (Original Mix) | 124 | 6.5 |
| 18 | Simon Vuarambon & Tantum | Lake Of Fire | 122 | 6.2 |


## Set 88. 88. Cordoba Progressive — Gai Barone Style
**Armado:** 2026-09-03  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 119-125  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Mike Rish | The Likes of You (Original Mix) | 120 | 3.9 |
| 2 | Antrim, Kamilo Sanclemente | Once and Again feat. Paula OS (Extended Mix) | 120 | 4.3 |
| 3 | Nicolas Rada | El Oro De Los Tigres | 122 | 4.5 |
| 4 | Roy Rosenfeld | Kala  | 120 | 4.8 |
| 5 | Melodiam (AR) | Juno | 120 | 4.9 |
| 6 | Alex O'Rion | Tunnel (Original Mix) | 122 | 5.2 |
| 7 | Guy J | Everyday (Original Mix) | 122 | 5.4 |
| 8 | Hana, Durante | Celestia (Extended Mix)  | 124 | 5.7 |
| 9 | Dowden | Feather (Original Mix) | 122 | 5.9 |
| 10 | Ezequiel Arias | Airwave (Original Mix) | 123 | 6.1 |
| 11 | Kostya Outta | Seguro (Paul James Nolan Remix) | 122 | 6.4 |
| 12 | Guy J | Illusion (Original Mix)  | 122 | 6.6 |
| 13 | Tali Muss | Azal (Original Mix) | 123 | 6.9 |
| 14 | Kamilo Sanclemente | Fragma (GORKIZ Remix) | 123 | 7.1 |
| 15 | Tom Pavicich | Olimpo (Ignacio Berardi Remix) | 123 | 7.4 |
| 16 | Maze 28 | Leave the World Behind (Original Mix) | 122 | 7.0 |
| 17 | Paul Deep (AR) | Tique (Original Mix) | 123 | 6.7 |
| 18 | Cendryma | Override (Original Mix) | 122 | 6.3 |


## Set 89. 89. Argentina Peak Time
**Armado:** 2026-09-03  
**Duracion:** 1.25h  
**Tracks:** 18  
**BPM range:** 121-127  

| # | Artist | Title | BPM | E |
|---|--------|-------|-----|---|
| 1 | Guy Mantzur, Khen | Shine Tomorrow (Original Mix) | 123 | 5.0 |
| 2 | Kamilo Sanclemente, Sebastian Valencia (COL) | Anomaly  (Original Mix) | 123 | 5.2 |
| 3 | Melodiam (AR) | Cosmic  | 122 | 5.5 |
| 4 | Gorkiz, K Loveski | Echos Of Eons (Greenage Remix)  | 122 | 5.7 |
| 5 | Stephan Bodzin, Jem Cooke, Massano | Healing (Extended Mix) | 124 | 5.9 |
| 6 | Khen | Closing Doors (Original Mix) | 124 | 6.1 |
| 7 | Cendryma | Focus Bend (Extended Mix) | 122 | 6.4 |
| 8 | Navar & Dmitry Molosh | Small Wonders (Hernan Cattaneo & Marcelo Vasami Remix) | 122 | 6.6 |
| 9 | Rockka, Maze 28 | Mirage (Extended Mix) | 123 | 6.8 |
| 10 | Emi Galvan | Everlong (Original Mix) | 124 | 7.1 |
| 11 | Tali Muss, Vakabular | Uniqueness (D-Nox & Ed Steele Remix) | 125 | 7.3 |
| 12 | Maze 28 | Great Attractor (Ruben Karapetyan Remix) | 124 | 7.5 |
| 13 | Jamie Stevens, Zankee Gulati | Low Tide (Ezequiel Arias Remix) | 125 | 7.8 |
| 14 | Durante & Maz (BR) | Ivory | 126 | 7.4 |
| 15 | D-Nox, Stereo Underground | Shooting Stars (Extended Version)  | 125 | 7.6 |
| 16 | Guy J | Catfish (Jonas Saalbach Remix) | 124 | 7.4 |
| 17 | NOIYSE PROJECT, Hernan Cattaneo, Jamie Stevens | Remember Me - Hernan Cattaneo & Jamie Stevens Remix | 122 | 7.3 |
| 18 | Kamilo Sanclemente | Astronauts Nightmares (DJ Ruby Extended Remix) | 123 | 7.1 |

