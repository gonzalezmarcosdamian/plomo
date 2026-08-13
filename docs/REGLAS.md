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

9 markers por track:

| # | Tipo | Color | Posición |
|---|------|-------|----------|
| Cue 1 / M1 | Mix-IN First Beat | Rojo | Primer onset absoluto |
| Cue 2 / M2 | Bass IN | Verde | Primer kick sustained |
| Cue 3 / M3 | Breakdown | Cyan | Longest kick-absent stretch |
| Cue 4 / M4 | DROP | Azul | Kick re-entry post-breakdown |
| Cue 5 | Mix-OUT | Amarillo | 16 bars antes del último kick |

**Sin loops** (desde 2026-08-06). El engine no escribe ningún cue con `OutMsec`
ni `BeatLoopSize`. El loop se arma a mano en el CDJ.

## Reglas de curaduría de sets (2026-08-13)

### Repetición: lo que escucha el que te vio dos veces

La regla vieja era "un artista por set". Medida contra la biblioteca, no estaba
midiendo lo que importa: había un track en **14 sets** distintos, otro en 13 y dos
en 10 — y como eran de artistas distintos, la regla no los detectaba.

Regla nueva:

```
dentro de un SET:
  máx 2 tracks por artista        (separación mínima 5 tracks)
  máx 3 tracks por remixer/mano   ← el remixer cuenta como artista
  máx 4 tracks por sello

entre SETS CONSECUTIVOS:
  0 tracks repetidos
  0 detonantes (E>=7.5) repetidos
```

El remixer se cuenta parseando `(X Remix|Mix|Edit|Version)` del título además
del campo artista — ver `names()` en `scripts/select_set.py`. Cuidado con los
sufijos: "Marsh's Extended Mix" tiene que normalizar a `marsh`, si no el solver
mete dos temas del mismo productor sin darse cuenta.

**Efecto lateral de la regla vieja:** con 31 tracks de Kamilo y techo de 1 por
set, hacían falta 31 sets para usarlos. Por eso había 78 sets. La regla no
limitaba la pereza dentro del set: la exportaba hacia afuera.

### Restricciones duras de tocabilidad

Sin estas, el optimizador produce sets que se ven bien en la planilla y son
injugables. Están implementadas en `select_set.py` como condiciones duras:

1. Escalón de energía **<= 1.3** entre tracks consecutivos
2. El cierre baja **al menos 0.6** del pico — nunca terminar arriba
3. Sin retroceso de energía durante la subida (tolerancia 0.4)
4. Key a distancia **<= 1** en Camelot, BPM **±2**
5. Penalizar quedarse en la misma key más de 2 tracks seguidos

**Prioridad cuando compiten:** el arco de energía manda. Un salto de Camelot se
tapa con una transición larga o un corte de bajos; un bache de energía en el
medio del set no se tapa con nada.

### Detonantes

Los tracks de E>=7.5 (23 en la biblioteca) viven en `[POOL] Detonantes`.
Todo set de 2h+ lleva **uno o dos**, ubicados entre el 70% y el 85% del set.
Nunca al final, nunca dos seguidos, y no se repite el mismo en dos sets
consecutivos.

El peak de un set progressive no lo hace el track de peak: lo hacen las dos
horas de contención anteriores.

### Caja, no playlist

Un set de 1h30 lleva **18-20 tracks**, no 12. Con 12 tracks a 7:30 cada uno no
hay margen para estirar, saltar ni leer la pista — eso es una playlist para
reproducir, no una caja para tocar. Se eligen los 12 arriba del escenario.

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
