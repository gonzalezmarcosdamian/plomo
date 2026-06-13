# Workflow: YouTube Set → Set Armado

Flujo para tomar un set de YouTube como referencia y armar uno propio
con tracks verificados en Muzpa y sin duplicados en la librería.

## Cuándo usar esto

Cuando el usuario dice: "Quiero armar un set estilo [este video de YouTube]"
o "Fijate en este set de YouTube y armame algo parecido".

---

## Pasos

### 1. Analizar el video de referencia

Buscar el tracklist en:
- La descripción del video (Cercle siempre los pone)
- 1001tracklists.com → buscar el nombre del artista + fecha
- Comentarios de YouTube (muchos usuarios los comparten)

Extraer la lista de artistas únicos del set.

**Señales de calidad del set de referencia:**
- Cercle sets: producción garantizada, tracklist siempre disponible
- +1M views = estilo probado con audiencia amplia
- +5M views = clásico del género

### 2. Verificar cobertura Muzpa

```bash
python scripts/muzpa_artist_scan.py "Artista1" "Artista2" "Artista3" ...
```

Clasifica artistas en tres grupos:
- ✅ **Cubierto**: artista encontrado con tracks nuevos (no en librería)
- ⚠️ **Parcial**: algunos tracks, no todos los del set original
- ❌ **Sin cobertura**: artista sin tracks en Muzpa

**Cobertura conocida de Muzpa (actualizar si cambia):**

| Artista / Label | Cobertura |
|-----------------|-----------|
| Bedouin | ✅ Completo |
| Monolink (Anjunadeep) | ✅ Completo |
| Ben Böhmer (Anjunadeep) | ⚠️ Parcial |
| Nils Hoffmann | ✅ Completo |
| Lee Burridge / Lost Desert (All Day I Dream) | ✅ Completo |
| Guy Mantzur (Bedrock) | ✅ Completo |
| Jamie Stevens | ✅ Completo |
| PROFF / Simon Vuarambon | ✅ Completo |
| Rodriguez Jr. | ✅ Completo |
| GMJ / Cid Inc. (Sudbeat/Replug) | ✅ Completo |
| WhoMadeWho | ❌ Sin cobertura |
| Stavroz | ❌ Sin cobertura |
| Roy Rosenfeld | ❌ Sin cobertura |
| Sébastien Léger | ❌ Sin cobertura |
| Yotto | ⚠️ Parcial |

Si los artistas principales NO están en Muzpa:
→ Buscar artistas del mismo label o estilo que sí estén
→ Usar el tracklist solo como referencia de vibe, no de tracks

### 3. Filtrar duplicados en librería

El scan de muzpa_artist_scan.py ya filtra los tracks que están en la librería.
Los tracks que aparecen en el output = nuevos + disponibles en Muzpa.

### 4. Crear batch de descarga

Crear `data/batch_NombreSet.txt` con:
```
# Comentario explicando el set

# Sección por zona del set (opcional, para documentación)
Artista - Titulo exacto del scan
Artista - Titulo exacto del scan
...
```

**Importante**: usar los nombres EXACTOS del scan de Muzpa, no inventarlos.

```bash
python scripts/muzpa_download.py --batch data/batch_NombreSet.txt
```

### 5. Importar en Rekordbox

Seguir el pipeline estándar:
```
File → Import → Add Folder → Music/Inbox
→ Dejar que RB analice (BPM + key + waveform)
→ python scripts/post_import.py
```

### 6. Crear set target JSON

Crear `data/set_targets/set_NN.json` con:

```json
{
  "name": "NN. Nombre — Contexto — Fecha",
  "duration_h": 3,
  "bpm_range": [116, 128],
  "max_per_artist": 5,
  "movements": [
    {"name": "warmup", "e_min": 2.0, "e_max": 4.0, "e_center": 3.0, "fraction": 0.20, "anchor_ids": []},
    {"name": "build",  "e_min": 4.0, "e_max": 6.0, "e_center": 5.0, "fraction": 0.25, "anchor_ids": []},
    {"name": "mid",    "e_min": 5.5, "e_max": 7.0, "e_center": 6.0, "fraction": 0.25, "anchor_ids": []},
    {"name": "peak",   "e_min": 6.5, "e_max": 9.0, "e_center": 7.5, "fraction": 0.30, "anchor_ids": []}
  ],
  "tracks": [
    {"artist": "Artista", "title": "Titulo"},
    ...
  ]
}
```

**Arcos típicos:**

| Contexto | Warmup | Build | Mid | Peak |
|----------|--------|-------|-----|------|
| Peluquería / íntimo | 20% | 25% | 25% | 30% |
| Club (late night) | 10% | 25% | 30% | 35% |
| Sunset/rooftop | 25% | 30% | 25% | 20% |

### 7. Armar el set

```bash
python scripts/build_set.py --target data/set_targets/set_NN.json
```

---

## Ejemplo aplicado: Peluquería Organic/Progressive House

**Referencia usada:**
- Ben Böhmer - Live above Cappadocia (Cercle) — 34M views
- Bedouin - The Treasury, Petra (Cercle) — 1M+ views

**Artistas en el set de referencia:** Ben Böhmer, Monolink, Nils Hoffmann, Bedouin

**Cobertura Muzpa verificada (2026-06-13):**
- Ben Böhmer: 2 tracks nuevos ⚠️
- Monolink: 10 tracks únicos nuevos ✅
- Nils Hoffmann: 12 tracks únicos nuevos ✅
- Bedouin: 15 tracks únicos nuevos ✅

**Resultado:** set_37.json, batch_peluqueria.txt (33 tracks, 0 duplicados)

---

## Notas

- Muzpa filtra duplicados automáticamente en muzpa_artist_scan.py
- Si un artista del set original no tiene cobertura en Muzpa, sustituir por
  otro artista del mismo label o estilo que sí esté
- Los sets Cercle son la mejor referencia: tracklist siempre disponible,
  artistas de calidad garantizada, views validadas por audiencia masiva
- No buscar tracks por título en Muzpa (75% de fallo). Siempre por artista.
