# Energy Algorithm — Documentación e Iteraciones

## Estado actual: v1.0

### Fórmula

```python
score = bpm_score(0-3) + intro_score(0-2) + breakdown_score(0-2.5) + drop_bonus(0-1) + peak_score(0-1.5)
```

| Componente | Rango | Cálculo |
|---|---|---|
| BPM | 0-3 pts | `(bpm - 118) / 8 * 3` |
| Intro tightness | 0-2 pts | `max(0, 2 - bass_in_s / 60)` |
| Breakdown tension | 0-2.5 pts | `min(2.5, breakdown_dur_s / 48)` |
| Drop presence | 0-1 pt | bonus fijo si hay drop |
| Peak section | 0-1.5 pts | `min(1.5, (outro - drop)_s / 120)` |

Score se guarda en campo `Comment` de Rekordbox: `E:5.3`

---

## Bugs confirmados en sesión (2026-05-16) — Cumple del 20 Set

### BUG-01 🔴 bass_in = 0ms — tratado como "entra inmediatamente"
**Síntoma:** Tracks donde no se detectó el bajo (InMsec=0) reciben 1.0 pts neutral. Deberían ser penalizados.
**Impacto:** Tracks flotantes como Lifeline y Unknown Destination reciben bonus incorrecto.
**Tracks afectados:** Unknown Destination (bass_in=0), Lifeline (bass_in=0).

### BUG-02 🔴 Loop Outro dispara antes del último drop
**Síntoma confirmado en sesión:** Unknown Destination tiene DOS drops. Detectamos el primero (278.7s), colocamos Loop Outro en 338.7s. El segundo drop/re-entrada ocurre en ~346s. El loop se activa 8s antes de ese segundo drop.
**Análisis de audio:** groove map confirmó dos secciones: breakdown en 217-283s, segunda re-entrada en 283-395s con mini-breakdown interno en ~343s.
**Causa raíz:** `apply_cues_v8` detecta un único drop y no verifica si hay actividad de kick DESPUÉS del Loop Outro calculado.

### BUG-03 🟡 Hot cues corridos del beat grid
**Síntoma reportado por DJ invitado + confirmado visualmente en screenshot de Lifeline:** Los marcadores aparecen ligeramente desplazados del golpe exacto en el display del CDJ.
**Screenshot evidencia:** Cue "A" en Lifeline visible en posición que no coincide exactamente con un transiente de beat.
**Causa raíz:** Nuestro análisis librosa produce posiciones en ms que no coinciden exactamente con el beat grid que Rekordbox calcula independientemente con su propio análisis de BPM.

### BUG-04 🟡 BPM pesa demasiado (30% del score)
**Síntoma:** Long Time (Quivver, 124 BPM, E:5.5) vs Echosphere (Solis, Cattaneo remix, 122 BPM, E:5.3). En la sesión, Long Time sonó claramente más flotante/menos energético que Echosphere.
**Causa raíz:** 2 BPM de diferencia = 0.75 pts automáticos, ignorando carácter del groove.

### BUG-05 🟡 Track con intro muerta no se diferencia en el score
**Síntoma + imagen:** Lifeline tiene sección celeste/silenciosa muy larga (~7 minutos) antes de que entre el groove (visible en screenshot). El score global no captura esto — puntúa el track igual que uno que "entrega" desde el minuto 1.
**Consecuencia en el set:** Lifeline después de Unknown Destination genera caída de energía percibida brutal aunque el score diga que son similares.
**Nota del DJ:** "la intro se podría mezclar desde el primer drop o ponerlo al inicio del set."
**Implicación:** Necesitamos `E_intro` (energía en los primeros 90s) separada de `E_peak` (energía máxima).

### BUG-06 🟡 Un solo drop detectado — estructuras multi-drop ignoradas
**Extensión del BUG-02.** Tracks de 6-8 min con dos ciclos breakdown/drop (muy común en progressive) solo tienen el primer ciclo reconocido. El segundo drop aparece sin marcadores propios.

---

## Plan de iteraciones

### v1.1 — Fix bass_in = 0ms 🔴 (esfuerzo: bajo, impacto: alto)

```python
# En calculate_energy():
if bass_in_ms is not None and bass_in_ms > 500:   # detección válida
    intro_score = max(0.0, 2.0 - (bass_in_ms / 1000) / 60)
elif bass_in_ms is None or bass_in_ms <= 100:
    intro_score = 0.3  # kick no detectado → penalizar
else:
    intro_score = 1.0  # neutral
```

**Impacto:** Long Time y Lifeline (bass_in=0) bajan ~0.5-0.7 pts en score.

---

### v1.2 — Reducir peso de BPM 🟡 (esfuerzo: bajo, impacto: alto)

```python
# De: bpm_score = min(3.0, max(0.0, (bpm - 118) / 8 * 3))   # pesa 30%
# A:
bpm_score = min(1.5, max(0.0, (bpm - 118) / 12 * 1.5))       # pesa ~15%
```

**Impacto:** Long Time vs Echosphere: ventaja por BPM baja de 0.75 a 0.25 pts. El groove pasa a dominar.

---

### v1.3 — Groove ratio 🟡 (esfuerzo: medio, impacto: alto)

Nuevo componente: fracción del track con kick activo. Diferencia tracks anclados (Echosphere) de flotantes (Long Time).

```python
# Nuevo parámetro en calculate_energy():
# groove_ratio = tiempo_con_kick / duracion_total  (0.0–1.0)

if groove_ratio is not None:
    groove_score = min(2.0, groove_ratio * 2.5)
    score += groove_score
```

Requiere cambio en `cue_engine.py`: calcular y retornar `groove_ratio` junto con los cues.

**Benchmarks esperados:**
- Echosphere (kick oscuro sostenido): groove_ratio ~0.75 → +1.5 pts
- Long Time (flotante): groove_ratio ~0.55 → +1.1 pts → diferencia real ~0.4 pts
- Guy J - Surreal (ambient): groove_ratio ~0.40 → +0.8 pts → queda en zona 2-3

---

### v1.4 — Fix Loop Outro para tracks multi-drop 🔴 (esfuerzo: medio, impacto: crítico)

```python
def find_loop_outro_safe(kick_rms_per_bar, threshold, bar_duration_s, bars_for_outro=16):
    """
    Encuentra posición del Loop Outro garantizando que NO haya
    kick activo significativo DESPUÉS de esa posición hasta el final.
    """
    # Trabajar desde el final hacia atrás
    last_kick_bar = max(i for i, k in enumerate(kick_rms_per_bar) if k > threshold)
    outro_bar = last_kick_bar - bars_for_outro

    # Validar: verificar si hay un drop DESPUÉS del outro_bar calculado
    activity_after = [k for k in kick_rms_per_bar[outro_bar:last_kick_bar] if k > threshold * 1.5]
    if len(activity_after) > bars_for_outro // 2:
        # Hay actividad significativa después → probablemente hay un drop post-outro
        # Buscar el ÚLTIMO gap (breakdown) y poner outro después de ese drop
        # [implementación detallada en cue_engine.py]
        pass

    return outro_bar * bar_duration_s
```

---

### v1.5 — Beat grid snap 🟡 (esfuerzo: medio, impacto: alto)

```python
def snap_to_beat_grid(time_s: float, bpm: float, first_beat_s: float) -> float:
    """Snap al beat más cercano según BPM y referencia."""
    beat_dur = 60.0 / bpm
    beats_from_ref = (time_s - first_beat_s) / beat_dur
    nearest_beat = round(beats_from_ref)
    return first_beat_s + nearest_beat * beat_dur

# Aplicar a todos los cues antes de escribir InMsec:
bass_in_snapped   = snap_to_beat_grid(bass_in_s,    bpm, first_beat_s)
breakdown_snapped = snap_to_beat_grid(breakdown_s,  bpm, first_beat_s)
drop_snapped      = snap_to_beat_grid(drop_s,       bpm, first_beat_s)
outro_snapped     = snap_to_beat_grid(outro_s,      bpm, first_beat_s)
```

**Limitación:** Mejora alineación con beat grid de librosa pero no garantiza match perfecto con el beat grid de Rekordbox (que puede diferir levemente). Corrección perfecta requeriría leer el grid de RB post-análisis.

---

### v1.6 — Intro energy vs Peak energy 🟡 (esfuerzo: alto, impacto: alto)

Separar score en dos dimensiones para decisiones de ordenamiento más inteligentes.

```python
# Calcular en cue_engine:
# E_intro: energía promedio de los primeros 90 segundos
# E_peak:  energía promedio de la ventana [drop, outro]

# Formato extendido en Comment:
# "E:5.3 | Ei:2.1 | Ep:7.4"
# E: global, Ei: intro, Ep: peak
```

Esto permite al reordenador:
- Track con Ei bajo + Ep alto (como Lifeline) → candidato a abrir el set o mezclar desde drop
- Track con Ei alto + Ep alto → bueno para sostener energía mid-set
- Track con Ei alto + Ep bajo → bueno para transiciones suaves al cierre

---

### v2.0 — Override manual del DJ (esfuerzo: bajo, impacto: inmediato)

```python
def effective_energy(commnt: str) -> float:
    """M: tiene prioridad sobre E:. Nunca sobreescribir M:."""
    if commnt and '| M:' in commnt:
        try:
            m_part = [p for p in commnt.split('|') if 'M:' in p][0]
            return float(m_part.replace('M:', '').strip())
        except Exception:
            pass
    if commnt and 'E:' in commnt:
        try:
            e_part = commnt.split('|')[0]
            return float(e_part.replace('E:', '').strip())
        except Exception:
            pass
    return 5.0

def set_auto_score(commnt: str, new_score: float) -> str:
    """Actualiza E: preservando M: y notas del DJ."""
    if commnt and '| M:' in commnt:
        idx = commnt.index('| M:')
        return f"E:{new_score}" + commnt[idx:]
    return f"E:{new_score}"
```

**Uso:** En Rekordbox, campo Comment → escribir `E:5.3 | M:7.0 | dark groove, mezclar desde drop`

---

## Orden de implementación recomendado

| Prioridad | Versión | Esfuerzo | Impacto directo en el set |
|---|---|---|---|
| 1 | v2.0 override manual | bajo | inmediato — corregir Lifeline y Echosphere ahora |
| 2 | v1.1 bass_in fix | bajo | alto — todos los tracks sin kick detectado |
| 3 | v1.4 Loop Outro multi-drop | medio | crítico — Unknown Destination y similares |
| 4 | v1.2 peso BPM | bajo | alto — Long Time vs Echosphere resuelto |
| 5 | v1.5 beat grid snap | medio | alto — cues alineados al golpe |
| 6 | v1.3 groove ratio | medio | alto — diferencia tracks anclados vs flotantes |
| 7 | v1.6 Ei/Ep split | alto | alto — decisiones de ordenamiento más inteligentes |

---

## Log de sesiones

### 2026-05-16 — Cumple del 20 Set (en vivo)
- Long Time suena más flotante que Echosphere → BUG-04
- Loop Outro Unknown Destination antes del último drop → BUG-02
- Lifeline energía bajísima post-Unknown → BUG-05 (imagen: sección celeste larga en waveform)
- Hot cues corridos del golpe (DJ invitado) → BUG-03 (imagen: cue A de Lifeline visualmente desplazado)
- Lifeline: posible uso desde primer drop o inicio del set → dato para v1.6

---

## Benchmarks objetivo

| Track | Tipo | Score esperado | Score actual |
|---|---|---|---|
| Guy J - Surreal | ambient | 2.0–3.0 | 5.7 ❌ |
| Kamilo - Show Me the Stars | warmup orgánico | 3.5–4.5 | 5.7 ❌ |
| Hobin Rude - Seraph | warmup prog | 4.0–5.0 | 2.2 ❌ |
| Lifeline (Cattaneo remix) | build intro larga | 4.0–5.0 | 4.8 ✅ |
| Echosphere (Cattaneo remix) | mid groove oscuro | 5.5–6.5 | 5.3 ❌ |
| Unknown Destination | mid-build | 5.5–6.5 | 6.0 ✅ |
| Deep Truth (JP Torrez) | drop claro | 6.5–7.5 | 6.0 ❌ |
| D-Nox - Shine | peak anclado | 7.5–8.5 | 7.4 ✅ |
| Kabi - Rainbow 125 BPM | peak flotante | 7.0–8.0 | 7.3 ✅ |

---

## Objetivo final

Cuando el DJ describe: *"oscuro y tenso, Cattaneo, empieza suave y va apretando"* →
1. Filtrar por `groove_ratio` alto + BPM 120-124
2. Ordenar con energy curve: Ei bajo → Ei medio → Ep alto → cierre
3. Respetar `M:` overrides donde el algoritmo falla
4. El resultado suena como lo describió
