# v1 — F#m, 123 BPM, 240 compases (7:48)

Progressive / organic house. 2026-09-09.

## Cómo volver a esta versión

```
git checkout tema-v1 -- postproduction/bocetos/v1 scripts/ data/set_live.json
python scripts/armar_set.py          # las 14 pistas de Live, con sus efectos
python scripts/montar.py v1          # el arreglo, y arranca a sonar
```

El `.als` no está en el repo porque Live no deja guardarlo por código. No hace
falta: el set es el resultado de la receta, no un original. Ver
[CLAUDE.md](../../../CLAUDE.md).

## La forma

| compases | parte | largo | capas | empieza → termina |
|---|---|---|---|---|
| 1-32 | intro | 32 | 3-3 | 122 → 443 |
| 33-64 | tema | 32 | 6-6 | 762 → 1041 |
| 65-80 | subida1 | 16 | 6-8 | 751 → 1366 |
| 81-112 | drop1 | 32 | 9-10 | 1738 → 2214 |
| 113-144 | bajada | 32 | 3-6 | 82 → 315 |
| 145-160 | subida2 | 16 | 6-8 | 856 → 1545 |
| 161-192 | drop2 | 32 | 10-11 | 2036 → 2617 |
| 193-208 | salida | 16 | 10-11 | 2096 → 2617 |
| 209-240 | salida_dj | 32 | 4-4 | 500 → 596 |

Las nueve secciones suben por dentro. El número de capas no baja nunca de la
intro al segundo drop.

## De dónde salen los números

- **La forma** de medir Minicube, Go y Cryo con `scripts/estructura.py`: 7.2 a
  8.1 min, intro de DJ de 16-32 compases, bajada grande pasada la mitad, salida
  de 24-32.
- **El bajo** de la célula medida de Simon Vuarambón.
- **El arpegio** de que Eze Arias no toca solos: 13.75 ataques melódicos por
  compás, que es una línea corriendo y no un lead.
- **La humanización** de medir clap, hat y percusión contra el bombo en las
  referencias, no de inventar milisegundos.
- **Los defectos** los revisa `scripts/escuchar.py`. Al cerrar esta versión:
  seis partes limpias de nueve; los dos drops y la salida avisan "en el límite
  de lo denso" (25.9 notas por compás contra 17.7 medido), que se deja a
  propósito y está anotado.

## Lo que falta

- **No hay audio.** AbletonOSC no tiene handler de export; el render va a mano.
- **No hay mezcla.** Los niveles son los de cargar cada pista, no una mezcla.
- **No hay automatización.** Ni filtros que se abren ni volúmenes que se mueven:
  el puente OSC no llega a los envelopes.
