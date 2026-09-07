# Setlists de referencia

Corpus de setlists reales de otros DJs, en orden de ejecucion. Es lo unico que
permite refutar una regla de curaduria: medir las reglas contra los sets propios
es circular, porque el solver las impone y siempre da 100% de cumplimiento.

Los consume `scripts/backtest_rules.py`. Se cargan con:

```bash
./.venv/Scripts/python.exe scripts/ingest_setlist.py \
  --dj "John Digweed" --evento "Transitions 1050" --fecha 2026-01-10 \
  --fuente "https://..." --archivo tracklist.txt
```

El script parsea lineas `Artista - Titulo` (tolera numeracion y timestamps) y
enriquece key, BPM y energia cruzando contra `data/pool.json`. Lo que no matchea
queda en `null` y el backtest lo saltea.

## Que priorizar

DJs cuyo repertorio se solapa con la biblioteca propia — si no, la cobertura de
datos es baja y el setlist casi no aporta transiciones medibles. En orden:
Simon Vuarambon, John Digweed, Hernan Cattaneo, Ezequiel Arias, Emi Galvan.

## Orden dudoso

Si la fuente es repertorio y no secuencia, cargar con `--orden-dudoso`. Queda
guardado pero fuera del corpus de transiciones.

`data/setlists_muzpa.json` es exactamente ese caso: 89 tracks etiquetados por DJ
(Vuarambon 33, Digweed 28, Eze Arias 22, Emi Galvan 6) sin orden de ejecucion.
Sirve para medir paleta — BPM, keys, sellos — no transiciones.
