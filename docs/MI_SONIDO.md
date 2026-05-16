# Mi Sonido — Referencia y Misión

## La misión

Tocar como **Eze Arias / Simon Vuarambon / John Digweed**.

Progressive house con alma. Sets que son un viaje — no una colección de tracks sino una narrativa que la gente recuerda.

---

## Artistas de referencia

### Eze Arias
- **Origen:** Argentina
- **Sello:** Anjunadeep, sellos prog argentinos
- **Carácter:** Melódico, emotivo, orgánico. El lado luminoso del progressive — te lleva hacia arriba sin que lo notes. Sets con mucho corazón.
- **Qué tomar:** La capacidad de hacer tracks emotivos que no se sientan "pop". El viaje hacia adentro.

### Simon Vuarambon
- **Origen:** Argentina
- **Sello:** Bedrock, Univack, Hernan Cattaneo camp
- **Carácter:** Oscuro, hypnótico, inmersivo. Groove anclado, kick seco. El lado profundo y tenso del progressive. Te captura y no te suelta.
- **Qué tomar:** La meseta hypnótica. El sonido que "retiene" a la gente sin que puedan explicar por qué.

### John Digweed
- **Origen:** UK, Bedrock Records
- **Carácter:** El maestro del viaje largo. Sets de 4-6 horas con narrativa completa — oscuro, luminoso, tenso, emotivo, todo en un arco. Técnica de mezcla impecable. Nunca un track fuera de lugar.
- **Qué tomar:** La arquitectura del set. Cada track tiene un rol. El conjunto cuenta una historia.

---

## Mi sonido — "Sonido Plomo"

La intersección de los tres: **progressive house oscuro y emotivo, con narrativa de largo aliento**.

### Características definitorias
- BPM: 120–124 (no sube de 125 salvo en peak específico)
- Camelot: zona A preferentemente (tonalidades menores)
- Kick: seco, sostenido, anclado — no flotante
- Melodía: presente pero no dominante — sirve al groove, no al revés
- Arco: siempre hay un viaje, nunca una meseta plana durante todo el set

### Dos registros que conviven

| Registro | Descripción | Tracks de referencia |
|---|---|---|
| **Oscuro / hypnótico** | Dark progressive, kick que retiene, sin color melódico que distraiga. Captura a la gente en la meseta. | Breakdown (Anderson vs Ivan Aliaga), Moonflare (Cendryma), Telazar (George X), Shine (D-Nox) |
| **Emotivo / progresivo** | Capas que construyen, emotivo, identitario. El momento en que el set "tiene alma". | Sonoma (Simon Doty), Undertow (djimboh) |

### El arco del set ideal
```
Apertura suave (warmup orgánico)
    ↓
Entrada a la meseta (primer track oscuro/hypnótico)
    ↓
MESETA — captura (tracks oscuros, groove anclado, la gente está adentro)
    ↓
Respiro emotivo (track constructor, intro suave, viaje ascendente)
    ↓
PEAK — el momento (energía máxima, todavía progresivo, no mainstage)
    ↓
Cierre (descenso melódico, dejar la sensación)
```

---

## Compatibilidad confirmada (feedback de sesiones)

### Transiciones que funcionan ✅
| De | A | Por qué |
|---|---|---|
| Undertow (djimboh) | Sonoma (Simon Doty) | Constructor → emotivo, energía que fluye, 9A→10A |

### Transiciones que no funcionan ❌
| De | A | Por qué |
|---|---|---|
| Lifeline (Cattaneo remix) | Breakdown (Anderson) | Color melódico → oscuro abrupto. Choque de registro emocional. |
| Breakdown (Anderson) | Undertow (djimboh) | Groove anclado → intro silenciosa. Contraste demasiado abrupto sin puente. |

### Regla emergente
> Un track "oscuro/hypnótico" no puede ir directo a un track con "intro suave" a menos que haya un breakdown natural dentro del track de salida que funcione como puente.

---

## Feedback de sesiones

### 2026-05-16 — Cumple del 20 Set
- **Breakdown** identificado como track de referencia: inmersivo, meseta, captura a la gente. Registro oscuro/hypnótico confirmado.
- **Moonflare, Telazar, Shine** identificados como parte del mismo registro.
- **Undertow**: emotivo, progresivo, intro muy suave. Necesita energía alta antes para funcionar como respiro.
- **Sonoma**: emotivo, identitario. "El sonido que me representa." Registro emotivo/progresivo.
- **Undertow → Sonoma**: transición que fluye naturalmente.
- **Lifeline → Breakdown**: choca. Registro melódico → oscuro abrupto.
- **Breakdown → Undertow**: difícil. Necesita puente.

---

## Implicaciones para el algoritmo

El sistema debe poder:
1. **Clasificar** cada track en un registro (oscuro / emotivo / neutro) — dimensión `vibe_score`
2. **Respetar el arco narrativo** — no solo energía sino registro emocional en secuencia
3. **Validar transiciones** — detectar cambios de registro abruptos y advertir o evitarlos
4. **Construir sets con narrativa** — cuando el DJ describe "viaje Digweed", el sistema arma el arco completo

La misión del algoritmo es la misma que la misión del DJ: **que el set suene como Eze Arias / Vuarambon / Digweed.**
