# Reglas del proyecto plomo — para Claude

## Loops — NO SE USAN (2026-08-06)

**REGLA:** El proyecto no genera loops. Ningún cue lleva `OutMsec` ni `BeatLoopSize`.

- `apply_cues_v8()` → escribe 9 markers, ninguno es loop
- `post_import.py` → no crea loops
- Nunca agregar loops "porque sí" al tocar cues

Se eliminaron los 2204 loops que existían (`Loop Intro 16b` / `Loop Outro 4b`)
con `scripts/remove_loops.py`. Ese script sigue disponible por si vuelven a
aparecer desde Rekordbox.

**Por qué:** el loop interfiere con el automix y ensucia la waveform. El loop se
arma a mano en el CDJ en el momento, que es donde se decide.

---

## Numeración de sets

- Sets activos: `XX. Nombre — Duración — Fecha` (ej: `09. Progressive Dark — 3h — 2026-05-21`)
- El número más alto = más nuevo
- **El número tiene que ser único** — `build_set.py` resuelve la playlist por
  `LIKE 'NN.%'` y ahora falla si hay ambigüedad en vez de agarrar cualquiera.
  Los `NN. Artista Style` viejos se movieron a la serie 90+ por esto.
- [POOL] playlists: sin número, son material de referencia
- `Cumple del 20` (pool de 70 tracks): sin número, es un pool especial

## Armar sets

Ver `docs/REGLAS.md` → "Reglas de curaduría de sets" para el criterio, y
`docs/ARCHITECTURE.md` → "Flujo para armar un set" para los comandos.

Lo esencial:
- Se **selecciona** con key y energía a la vez (`select_set.py`), no se elige
  por vibe y se ordena después — una selección incoherente no se arregla
  reordenando.
- Tope: 2 tracks por artista, 3 por remixer, 0 repetidos entre sets consecutivos.
- Un set de 1h30 son 18-20 tracks (una caja), no 12 (una playlist).

## Energía faltante

`post_import.py` procesa por CARPETA (`FolderPath LIKE '%Inbox%'`), así que lo
que entró a la biblioteca por otro camino nunca recibe energía y queda invisible
para `select_set.py`. Para eso está `backfill_energy.py`, que procesa por ESTADO.
Correrlo cuando `dump_pool.py` reporte menos tracks de los esperados.

## Pipeline de importación

```
1. muzpa_download.py     → Downloads/
2. import_all.py         → mueve a Nuevos/2026-05, fix metadata  
3. Rekordbox             → File → Import → Add Folder → Nuevos/2026-05
4. post_import.py        → cues v8 + energy + playlists
5. Rekordbox Sync        → sync al pen
```

## Estructura de archivos

Ver `docs/ARCHITECTURE.md` para reglas completas.

Resumen:
- `src/plomo/` → módulos core únicamente
- `scripts/` → scripts de pipeline activos
- `scripts/archive/` → one-offs ya ejecutados
- `scripts/hooks/` → hooks de Claude Code (guardarrailes)
- `rules/` → reglas de curaduría como dato versionado
- `data/` → JSONs de datos personales (en .gitignore)
- `docs/` → documentación técnica y artística
- `.claude/agents/` → los agentes del proyecto
- `.claude/skills/` → los flujos invocables (`/sesion`, `/set`, `/reglas`, …)
- Raíz → solo config files

---

## Agentes y orquestación (2026-09-07)

Ver `docs/AGENTES.md`. Resumen de lo que cambia el modo de trabajo:

**Los agentes** viven en `.claude/agents/`: `master` orquesta, y reparte entre
`curador` (sets), `analista` (medir y discutir reglas), `research` (buscar
música y setlists), `tecnico` (pipeline y DB), `archivista` (carpetas),
`productor` (ingeniería inversa de tracks), `video` y `redes`.

**Las skills** en `.claude/skills/`: `/sesion` para arrancar, `/set` para armar,
`/reglas` para desafiar el criterio, `/vistas` para regenerar carpetas,
`/receta` para analizar un track.

**Las reglas ya no están hardcodeadas.** `scripts/select_set.py` lee sus números
de `rules/curaduria.json` vía `src/plomo/rules.py`. Cada regla lleva su valor, su
porqué y su evidencia. No se cambia una regla sin pasar por
`scripts/backtest_rules.py` y sin aprobación humana.

**Ojo con la circularidad:** medir las reglas contra los sets propios no prueba
nada — el solver las impone. Solo refuta una regla un setlist real de otro DJ que
la viole y funcione igual. Por eso `data/setlists/` (cargado con
`scripts/ingest_setlist.py`) es el trabajo pendiente más valioso.

**Carpetas: depósito y vistas.** El disco guarda, no organiza. Los archivos no se
mueven (así no se rompe ningún path de Rekordbox); la forma de navegar la
colección vive en `C:\Users\gonza\Music\Vistas`, un árbol de hardlinks que genera
`scripts/build_views.py` y que se borra y regenera sin consecuencias.

---

## Bitacora y aprendizajes (2026-09-08)

Dos archivos distintos, y confundirlos los arruina a los dos:

- `docs/BITACORA.md` — que se hizo, por fecha, lo nuevo arriba. No se edita lo
  viejo: si algo resulto estar mal, se corrige en una entrada nueva.
- `docs/APRENDIZAJES.md` — la leccion durable, sin la anecdota, con que paso,
  por que y como se aplica.

Para saber en cual va: si dentro de seis meses, en otro proyecto, la seguirias
aplicando, es aprendizaje. Si solo explica una fecha, es bitacora.

`arquetipo/` tiene el metodo empaquetado para arrancar otro proyecto con esta
forma de trabajo: `python arquetipo/nuevo_proyecto.py <destino> --nombre X`.

---

## El set de Live no se guarda: se reconstruye (2026-09-09)

Live no le expone `save` a los Remote Scripts, asi que el `.als` no se puede
escribir por codigo. En vez de tratarlo como un original que hay que cuidar, el
set se trata como el RESULTADO de una receta versionada:

```
python scripts/armar_set.py          # 13 pistas, instrumentos, efectos, niveles
python scripts/idea.py --nombre v1 --tema
python scripts/montar.py v1 --desde 161
```

Tres comandos, cinco minutos, y el tema entero vuelve a estar. Perder el set es
perder tiempo de maquina, no trabajo.

- `data/set_live.json` — la receta. Se regenera desde Live con
  `python scripts/armar_set.py --capturar`, y hay que hacerlo cada vez que se
  cambie algo a mano en Live, o deja de coincidir con la realidad.
- Cada instrumento lleva alternativas en `ALTERNATIVAS`, y la ultima de cada
  lista es siempre un MOTOR (Drift, Drum Rack, Simpler), no un preset. Esos tres
  estan en las tres ediciones de Live, asi que la receta sigue funcionando en
  Intro aunque falte el preset lindo.
- El MIDI de las versiones (`postproduction/bocetos/v1/`) SI se versiona. Las
  carpetas `repiques_*` y `comparacion_*` no: son transcripciones de temas
  comerciales, material de referencia como los samples.

**El tempo esta en dos lados y tienen que coincidir**: `BPM` en `armar_set.py` y
`--bpm` en `idea.py`. Estuvieron en 121 y 123 sin que nadie lo notara.

