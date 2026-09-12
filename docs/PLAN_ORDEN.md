# Plan: arreglar el orden de los sets

Escrito el 2026-09-12. Pedido del DJ: *"quiero mejorar el orden de los sets
armados, se hizo mucho lío"*, *"la idea es de mucha energía, sin necesidad de
que los BPM se vayan para arriba siempre"*, *"Maze lo hace muy bien"*.

Todo lo que sigue está medido sobre el repo. Los comandos que lo reproducen
están al lado de cada número.

---

## 1. Diagnóstico

### 1.1 La energía CONTIENE el BPM. Ese es el problema de fondo

`src/plomo/energy.py` arma el score con cinco componentes que suman 10:

| Componente | Máximo |
|---|---|
| **BPM** — `(bpm - 118) / 8 * 3`, satura en 126 | **3.0** |
| Intro (qué tan rápido entra el bajo) | 2.0 |
| Breakdown (duración de la tensión) | 2.5 |
| Drop presente | 1.0 |
| Largo del peak | 1.5 |

O sea: **el 30% de la "energía" es literalmente el BPM**. Un tema de 118 BPM
tiene un techo teórico de E7.0 y no puede pasarlo aunque tenga el drop más
grande del mundo.

En la biblioteca real:

- De los 180 tracks con E≥7.0, **solo 16 (9%) están en 122 BPM o menos**.
- De los 14 con E≥8.0, **uno solo**.
- El track más energético por debajo de 121 BPM llega a E7.1.

**Consecuencia:** pedirle al solver "un set de mucha energía" es pedirle
"un set de BPM alto". No es un defecto del solver, es la definición de la
métrica. Mientras eso no cambie, "energía alta sin subir BPM" es imposible por
construcción, no por criterio.

### 1.2 Los sets del solver no caminan armónicamente

Distribución del paso de Camelot con signo, sobre transiciones consecutivas:

| Corpus | paso 0 (misma rueda) | dentro de {-1, 0, +1} | n |
|---|---|---|---|
| **Solver** (`data/set_targets`) | **38%** | **90%** | 566 |
| Tocado real (`data/tocados`) | 23% | 59% | 315 |
| Referencia, otros DJs (`data/setlists`) | 14% | 33% | 69 |

Más de un tercio de las transiciones que arma el solver **no mueven la
tonalidad**, y nueve de cada diez se quedan a un paso. Los sets no suenan mal
transición por transición — suenan iguales de principio a fin. Eso es el "lío":
no es que las mezclas fallen, es que el set no va a ningún lado.

### 1.3 Maze 28 hace exactamente lo contrario con el BPM

Su mix Proton Curator (13 tracks, 67 min) está cargado en
`data/setlists/maze-28_proton-curator-mix-summer-2025_2025-08-01.json`:

- Empieza en **130 BPM** y termina en **117**. El set **baja 13 BPM**.
- Entre temas consecutivos salta **±3, ±4, ±5, ±6 BPM**. Nuestra regla
  `bpm.max_salto` es **2.0**: el solver no podría armar ese set ni queriendo.
- En Camelot es **más estricto** que los DJs de festival: 0 de 10 transiciones
  saltan más de 1 (media 0.50), contra 72% en Eze Arias / Simon / Colyn.
- Los últimos 5 temas los deja clavados en 9A.

**Lo que enseña:** la energía de un set no la sostiene el tempo. Maze usa el BPM
como recurso libre —lo sube y lo baja— y la continuidad la sostienen la
tonalidad y la textura. Nosotros hacemos al revés: BPM casi fijo y tonalidad
casi fija.

### 1.4 Nuestros sets suben más el BPM que los que el DJ toca de verdad

| | corr(BPM, energía) por set | BPM del track 1 al pico |
|---|---|---|
| Solver | **+0.63** | **+3.0** (21 de 40 sets suben ≥3) |
| Tocado real | +0.52 | +2.0 (9 de 21) |

### 1.5 Dos definiciones de distancia Camelot en el repo

`scripts/select_set.py::cam_dist` dice que el cambio de relativa (8A↔8B) vale
**0**; `src/plomo/camelot.py::distance` dice que vale **1**. El solver optimiza
con una y el auditor y el backtest miden con la otra.

**Impacto real: casi nulo** — ese caso aparece en el 0% de las transiciones de
referencia y el 3% de las tocadas. Es un defecto latente que hay que unificar
antes de tocar los pesos, no la explicación del problema.

### 1.6 Lo que `audit_sets.py` NO mira

Da "0 transiciones flojas" en los sets 97 a 105 y aun así el DJ duda. Mira cada
par aislado y no mira el set:

- si la escalera de Camelot es monótona o va y vuelve;
- cuántas transiciones no mueven nada;
- agrupamiento de sellos y de texturas parecidas;
- si el BPM sube porque tiene que subir o porque se arrastra con la energía;
- si el pico cae donde el concepto del set dice que caiga.

---

## 2. Fases

### Fase 1 — Separar energía de BPM *(la que desbloquea todo)*

**Qué se toca.** `src/plomo/energy.py`: se saca el componente BPM del score y se
reescalan los otros cuatro a 10. La energía pasa a medir estructura —intro,
breakdown, drop, largo del peak— y nada más. El BPM queda como lo que es, un
campo aparte que el solver ya usa.

**Antes de tocar nada.** Guardar `energy` viejo en `energy_v1` para todos los
tracks, y correr `medir_horizontalidad.py` y `backtest_rules.py` para tener la
foto previa.

**Cómo se mide el éxito.** Recontar cuántos tracks con E≥7.0 quedan por debajo
de 122 BPM. Hoy son 9%. Si el cambio sirve, tiene que subir a por lo menos 25%:
esa es la evidencia de que ahora existe material de mucha energía y BPM bajo.

**Ojo.** Esto recalcula la energía de 1883 tracks y mueve todos los `e_lo`/`e_hi`
de los configs existentes. Los sets viejos no se rompen (guardan ContentIDs)
pero sus rangos dejan de significar lo mismo. Hay que anotarlo en la bitácora.

### Fase 2 — Unificar la distancia Camelot

**Qué se toca.** `select_set.py` importa `distance` de `src/plomo/camelot.py` y
se borra `cam_dist`. Una sola definición.

**Éxito.** `backtest_rules.py` y `audit_sets.py` dan los mismos números que el
solver optimiza. Los sets 97-105 reauditados no cambian de veredicto (el impacto
medido es 0-3%; si cambia mucho, algo más está mal y hay que frenar).

### Fase 3 — Que el BPM deje de ser una regla dura

**Qué se toca.** `rules/curaduria.json`: `bpm.max_salto` pasa de dura a
penalizada con peso. Maze salta 6 BPM y funciona; el 22% de las transiciones de
referencia la violan.

**El experimento que lo decide** (y no la opinión): rearmar los sets 97-105 con
`max_salto` en 2.0 (hoy), 3.0 y 4.0, y comparar tres cosas — cuántos artistas
distintos entran, cuánto se mueve la escalera Camelot, y cuánto sube el BPM
hasta el pico. **Criterio:** se adopta el valor más alto que no empeore el
movimiento de Camelot ni meta transiciones que el DJ escuche y rechace. La
escucha decide el empate, los números descartan las opciones malas.

### Fase 4 — Que la escalera camine

**Qué se toca.** Un término nuevo en el costo de `select_set.py` que penalice
quedarse: hoy `paso 0` cuesta cero y por eso sale 38% de las veces. Se penaliza
el paso 0 y se penalizan las corridas monótonas largas (cinco veces +1 seguidas
aburre igual que no moverse).

**Éxito.** El paso 0 baja del 38% a la zona del 23% que el DJ toca de verdad, sin
que aparezcan transiciones flojas. Es el número objetivo: no imitar a los DJs de
festival (14%), imitar lo que este DJ ya hace cuando decide en vivo.

### Fase 5 — Ampliar el auditor

**Qué se toca.** `audit_sets.py` suma métricas de SET, no de par: % de paso 0,
corrida monótona más larga, sellos repetidos y a qué distancia, correlación
BPM-energía, y posición real del pico contra la declarada en `_identidad`.

**Éxito.** El auditor marca los sets 97-105 actuales con lo que hoy no ve. Si
sale todo limpio, la métrica no sirve y hay que pensarla de nuevo.

### Fase 6 — Rearmar todos los sets armados

Recién acá. `select_set.py` sobre todos los configs, `build_set.py`,
`audit_sets.py` con el auditor nuevo, y comparar contra la foto de la Fase 1.

**Éxito.** Ningún set empeora en transiciones flojas y la mediana de paso 0 baja.
Lo que empeore se revisa a mano antes de escribirlo en Rekordbox.

---

## 3. Qué NO hacer

- **No relajar `armonia.max_camelot_dist` todavía.** El backtest lo dio
  REFUTADA porque los DJs de festival la violan el 72% de las veces, pero Maze
  —que es la referencia que el DJ eligió— la cumple 10 de 10. No es una ley
  universal: depende del registro. Relajarla ahora, con el problema real siendo
  que el set no se mueve, va a producir saltos sin resolver lo otro.
- **No tocar dos reglas en la misma vuelta.** Si cambia energía y BPM juntos no
  hay forma de saber cuál mejoró qué.
- **No confiar en "0 transiciones flojas".** Los 97-105 dan 0 y el problema
  existe igual. Mientras el auditor no crezca, ese número prueba poco.
- **No medir el resultado solo contra los sets propios.** Es circular: el solver
  impone las reglas. La comparación que vale es contra `data/tocados` —lo que se
  tocó de verdad— y contra `data/setlists`.
- **No resolver los conflictos de `repeticion.*` de paso.** `max_por_artista`
  dice 2 en la regla y 1 en el código; `separacion_minima` dice 5 y 3. Están
  marcados hace rato en la salida de `backtest_rules.py`. Es una decisión
  independiente y merece su propia vuelta.

---

## 4. Orden sugerido y por qué

Fase 1 primero porque sin separar energía de BPM el pedido central —*mucha
energía sin subir el tempo*— no se puede cumplir con ninguna regla. Fase 2
después porque es barata y hay que medir con una sola vara antes de tocar pesos.
Fases 3 y 4 son las que cambian cómo suena, una por vez. Fase 5 antes de la 6
porque rearmar todo sin haber ampliado el auditor es volver a entregar sets que
dan 0 y no convencen.
