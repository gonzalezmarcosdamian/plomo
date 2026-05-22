# Reglas del proyecto plomo — para Claude

## Loops automáticos (ActiveLoop)

**REGLA:** Nunca activar loops automáticamente (ActiveLoop=1) al importar, cuear o procesar tracks.

- `apply_cues_v8()` → siempre escribe `ActiveLoop=0` en todos los loops
- `post_import.py` → no activa loops
- Solo activar loops cuando el usuario lo pida explícitamente para un set específico

**Cómo activar loops cuando se pide:**
El usuario dirá "activá los loops del Set X antes de tocar". Entonces correr:
```python
# Activar loops solo en los tracks de un set específico
con.execute("UPDATE djmdCue SET ActiveLoop=1 WHERE Comment LIKE '%Loop Outro%' AND ContentID IN (SELECT ContentID FROM djmdSongPlaylist WHERE PlaylistID=?)", (pl_id,))
```

**Por qué:** El loop activo interfiere con el automix de Rekordbox. El usuario lo activa manualmente en el CDJ antes de cada mezcla.

---

## Numeración de sets

- Sets activos: `XX. Nombre — Duración — Fecha` (ej: `09. Progressive Dark — 3h — 2026-05-21`)
- El número más alto = más nuevo
- [POOL] playlists: sin número, son material de referencia
- `Cumple del 20` (pool de 70 tracks): sin número, es un pool especial

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
