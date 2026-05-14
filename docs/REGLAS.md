# Reglas del proyecto DJ IA

> Sincronizado con `C:\Users\gonza\OneDrive\Documentos\Music\_Rekordbox\DJ_IA_PROJECT_REGLAS.md`

## Reglas de oro (NUNCA romper)

- ❌ Modificar master.db con `rekordbox.exe` corriendo (sobrescribe los cambios al cerrar)
- ❌ Cerrar Rekordbox con la X (siempre System Tray → Quit)
- ❌ Generar IDs > 32-bit unsigned (max 4,294,967,295) — Rekordbox UI los ignora
- ❌ Crear playlist en DB sin agregar `<NODE>` en `masterPlaylists6.xml`
- ❌ Setear `rb_local_usn = NULL` en filas nuevas
- ❌ Marcar cues manualmente
- ❌ Pagar herramientas comerciales (Mixed In Key, Beatport DJ)

## Estructura de carpetas

- `Music\2026\Nuevos\YYYY-MM\` — subcarpeta por mes de descarga (ej: `2026-05`)
- Permite saber qué temas son más recientes dentro de Nuevos

## Siempre

- ✅ Backup de master.db Y masterPlaylists6.xml antes de cada cambio
- ✅ Per-track commit (no bulk inserts >50)
- ✅ IDs random `random.randint(1500000000, 4000000000)`
- ✅ `rb_local_usn` incremental (leer MAX, sumar +1)
- ✅ DB integrity check después de cada cambio (`PRAGMA integrity_check`)
- ✅ Verificar en Rekordbox antes de avanzar al siguiente lote

## Algoritmo de cues v8

11 markers por track:

| # | Tipo | Color | Posición | Active Loop |
|---|------|-------|----------|-------------|
| Cue 1 / M1 | Mix-IN First Beat | Rojo | Primer onset absoluto | — |
| Cue 2 / M2 | Bass IN | Verde | Primer kick sustained | — |
| Cue 3 / M3 | Breakdown | Cyan | Longest kick-absent stretch | — |
| Cue 4 / M4 | DROP | Azul | Kick re-entry post-breakdown | — |
| Cue 5 | Mix-OUT | Amarillo | 16 bars antes del último kick | — |
| Loop Intro | — | Naranja | 16 bars desde Bass IN | `0` (manual) |
| Loop Outro | — | **Rojo** | 16 bars antes de Mix-OUT | **`1` (auto)** ⭐ |

## Aprendizajes técnicos críticos

### Problema: Playlist visible pero VACÍA en Rekordbox UI

**Root cause:** ID > 32-bit no se mapea a hex de 8 chars en `masterPlaylists6.xml`.

**Fix permanente:** ID generado con `random.randint(1500000000, 4000000000)` + agregar NODE al XML.

### Problema: Rekordbox sobrescribe cambios al cerrar

**Root cause:** Rekordbox carga master.db en memoria al abrir. Cualquier cambio externo se sobrescribe al cerrar (Quit).

**Fix:** Verificar `psutil` que `rekordbox.exe` NO esté corriendo antes de tocar DB.

### Problema: Cowork mount async write lag (sandbox-specific)

**Root cause:** El cowork mount no propaga writes inmediatamente.

**Fix:** `cp -f` shell + `sync` + `time.sleep(0.3)`. NO aplica corriendo local nativo.

### Problema: DB corruption por timeout

**Root cause:** Si el bash sandbox corta a mitad de un commit SQL, master.db queda corrupto.

**Fix sandbox:** batches de 3-5 tracks. **Fix local:** sin timeouts, no aplica.

### Problema: librosa key detection es impreciso

**Root cause:** Krumhansl-Schmuckler simple yerra ~30% de keys mayor (B-side).

**Workaround actual:** confiar en Rekordbox post-Analyze para keys reales. Fix futuro: Essentia o madmom.

## Checklist obligatorio antes de tocar DB

1. ¿Rekordbox cerrado? (`psutil` no detecta `rekordbox.exe`)
2. ¿Backup hecho? (master.db + masterPlaylists6.xml)
3. ¿IDs en rango 1.5B-4.0B?
4. ¿`rb_local_usn` incremental?
5. ¿NODE agregado al XML para playlists nuevas?
6. ¿DB integrity check después?
