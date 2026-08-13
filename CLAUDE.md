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
- `data/` → JSONs de datos personales (en .gitignore)
- `docs/` → documentación técnica y artística
- Raíz → solo config files
