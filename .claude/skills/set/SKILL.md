---
name: set
description: Arma un set nuevo de punta a punta - concepto, seleccion con key y energia, escritura en Rekordbox y auditoria. Usar cuando se pida un set, una tanda o una playlist para tocar.
---

# Armar un set

Lo ejecuta el agente `curador`. Rekordbox tiene que estar CERRADO en los pasos
2 y 6 (System Tray, Quit — no la X).

## 0. El concepto, antes que cualquier track

Sin esto no se arranca:

- **Donde y a que hora** — una peluqueria a las 3 de la tarde y un cierre a las
  6 de la manana no comparten una sola decision.
- **Cuanto dura** — define cuantos tracks. 12 por hora: 1h30 son 18-20 tracks,
  no 12. Una caja, no una playlist.
- **La identidad en dos frases** — que pregunta contesta este set. Va al campo
  `_identidad` del config. Si no se puede escribir, el set todavia no existe.

## 1. Preparar el pool

```bash
./.venv/Scripts/python.exe scripts/backfill_energy.py   # solo si hay tracks sin E:
./.venv/Scripts/python.exe scripts/dump_pool.py
```

Si `dump_pool` reporta menos tracks de los esperados, hay material invisible
para el selector: correr el backfill antes de seguir.

## 2. Escribir el config

En `data/set_configs/<nombre>.json`. Campos que importan:

| Campo | Que define |
|---|---|
| `num` | numero unico del set — `build_set.py` falla si hay ambiguedad |
| `n` | cantidad de tracks (12 por hora) |
| `bpm` | rango duro del pool |
| `e_pool` | banda de energia del pool, mas ancha que `e_lo`/`e_hi` |
| `e_lo` / `e_hi` | piso y techo del arco |
| `genres` | filtro obligatorio: sin esto entran bootlegs y techno de fiesta |
| `max_per_artist` | tope por productor, contando remixers |
| `prefer_ids` + `prefer_bonus` | forzar un track ancla |
| `beam` | 400 normal, 6000 cuando hay ancla obligatoria |

Tomar `data/set_configs/puerta_y_ultima_hora.json` como modelo.

## 3. Seleccionar, revisar, escribir, auditar

```bash
./.venv/Scripts/python.exe scripts/select_set.py data/set_configs/<nombre>.json
./.venv/Scripts/python.exe scripts/build_set.py <num> --dry
./.venv/Scripts/python.exe scripts/build_set.py <num>
./.venv/Scripts/python.exe scripts/audit_sets.py <num>
```

Leer la salida del selector antes de escribir: marca los saltos de Camelot >=2 y
los de BPM. Un set con tres marcas es un set que hay que rehacer, no publicar.

## Si dice SIN SOLUCION

En este orden, y no otro: ampliar el pool (aflojar genero o BPM), subir el beam,
bajar `n`. Tocar una regla dura es el ultimo recurso y se declara cual y por que.

## Al terminar

Anotarlo en `docs/sets_log.md`. Despues de tocarlo, el feedback de que transicion
funciono va a `data/transition_feedback.json`: es lo unico que despues le permite
al `analista` discutir las reglas con datos propios.
