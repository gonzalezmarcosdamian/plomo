---
name: reglas
description: Desafia las reglas de curaduria con evidencia - corre el backtest, muestra que regla se sostiene y cual no, y propone cambios con el numero que los justifica. Usar cuando haya que revisar el criterio o cuando algo se afirme sin datos.
---

# Desafiar las reglas

Lo ejecuta el agente `analista`. Las reglas viven en `rules/curaduria.json` con
su valor, su porque y su evidencia. Ninguna cambia sin pasar por este ciclo.

## 1. Medir

```bash
./.venv/Scripts/python.exe scripts/backtest_rules.py --json data/informe_reglas.json
```

Salen tres bloques: corpus propio, corpus de referencia y veredictos.

## 2. Leer el veredicto con la trampa a la vista

Que el corpus propio cumpla una regla **no prueba nada**: el solver la impone, es
circular. Solo el corpus de referencia — setlists reales de otros DJs — dice algo.

| Violaciones en sets reales | Veredicto | Que hacer |
|---|---|---|
| >15% | REFUTADA | pasar de filtro duro a penalizacion con peso |
| 5-15% | MATIZADA | default con escape explicito, no filtro |
| <5% | SOSTENIDA | dejarla |

Si dice SIN DATOS, el trabajo no es opinar: es traer setlists.

## 3. El corpus que ya existe y no depende de nadie

```bash
./.venv/Scripts/python.exe scripts/ingest_history.py --dry
./.venv/Scripts/python.exe scripts/ingest_history.py
```

El historial de Rekordbox (`djmdHistory`) guarda que se puso, en que orden y a
que hora, con key y BPM de la misma DB — cobertura 100%, sin matcheo por nombre.
El filtro separa una sesion tocada de una carga de decks por el hueco entre
tracks: tocar deja 6-8 minutos, cargar decks deja segundos. Y parte las sesiones
donde hay una pausa larga, porque el track que sigue a tres horas de nada no es
una transicion.

Hoy da 18 tandas, 299 tracks, 281 transiciones.

## 4. Traer corpus de referencia cuando falta

```bash
./.venv/Scripts/python.exe scripts/ingest_setlist.py \
  --dj "John Digweed" --evento "Transitions 1050" --fecha 2026-01-10 \
  --fuente "URL" --archivo tracklist.txt
```

Prioridad: DJs cuyo repertorio se solapa con la biblioteca propia, porque el
enriquecimiento de key/BPM/energia sale de cruzarlo contra `data/pool.json`. Un
setlist con 20% de cobertura casi no aporta transiciones medibles.

Si la fuente es repertorio y no secuencia, pasar `--orden-dudoso`: queda
guardado pero fuera del corpus de transiciones.

## 4. Proponer, no aplicar

```python
from plomo.rules import R
parche = R.proponer("armonia.max_camelot_dist", 2,
                    "en 12 setlists de referencia (n=340) el 22% de las "
                    "transiciones salta la rueda mas de 1")
```

`proponer` devuelve el parche y no escribe nada. Se le muestra a Gonzalo el
numero, no la intuicion. Aprobado:

```python
R.aplicar(parche, nota="pasa a penalizacion, no a filtro")
```

Sube la version menor y deja historial con el valor viejo y la evidencia.

## Higiene pendiente

`R.conflictos()` lista donde lo escrito no coincide con lo que corre. Hoy hay
dos abiertos y contaminan todo set que se arme encima:

1. `max_por_artista_en_set`: la regla dice 2, el codigo usa 1.
2. `separacion_minima`: la regla dice 5 tracks, el codigo usa 3.

`R.sin_evidencia()` lista las reglas duras que nadie midio nunca.
