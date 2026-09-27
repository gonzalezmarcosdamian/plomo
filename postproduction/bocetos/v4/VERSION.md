# v4 — F#m (11A), 123 BPM, 256 compases (8:19)

Progressive house. Las nueve partes de `FORMA` en `scripts/idea.py`, una
carpeta por parte y un archivo MIDI por instrumento.

**Esta version no la describio nadie todavia.** Lo que sigue es lo que se puede
leer de los archivos y del generador; la intencion musical —que funciona, que
no, que hay que cambiar— la pone el DJ o el agente `productor` al escucharla.

## Como volver a esta version

```
git checkout tema-v4 -- postproduction/bocetos/v4 scripts/ data/set_live.json
python scripts/armar_set.py          # las pistas de Live, con sus efectos
python scripts/montar.py v4          # el arreglo, y arranca a sonar
```

El `.als` no esta en el repo porque Live no deja guardarlo por codigo: el set
es el resultado de la receta. Ver [CLAUDE.md](../../../CLAUDE.md).

## La forma

| compases | parte | largo | tipo | pistas |
|---|---|---|---|---|
| 1-32 | intro | 32 | groove | 7 |
| 33-80 | pleno1 | 48 | pleno | 13 |
| 81-88 | bajon1 | 8 | bajon | 10 |
| 89-136 | pleno2 | 48 | pleno | 13 |
| 137-140 | bajon2 | 4 | bajon | 10 |
| 141-156 | breakdown | 16 | breakdown | 12 |
| 157-216 | drop | 60 | drop | 16 |
| 217-224 | bajon3 | 8 | bajon | 10 |
| 225-256 | salida_dj | 32 | salida_dj | 12 |

Plenos largos (48 compases) con bajones cortos de 4 a 8 en el medio, que es lo
que `forma_bandas.py` midio en Tunnel, Panorama, Rubicks, Closing Doors y
Flowing. El breakdown son 16 compases: cuarenta es lo que hace que un tema
progresivo se muera.

## Los instrumentos

Los 20 archivos que aparecen en alguna parte:

- `01_atmosfera.mid`
- `02_acordes.mid`
- `03_bajo.mid`
- `04_bateria.mid`
- `05_gancho.mid`
- `06_arpegio.mid`
- `07_cierre.mid`
- `08_anchos.mid`
- `09_sub.mid`
- `10_repiques.mid`
- `11_splash.mid`
- `12_reversa.mid`
- `13_lead.mid`
- `14_riser.mid`
- `15_bajo2.mid`
- `16_textura.mid`
- `17_subkick.mid`
- `18_metales.mid`
- `19_hats.mid`
- `20_abiertos.mid`

## Lo que falta

- **No hay audio ni mezcla.** El MIDI es el tema; el render va a mano porque
  AbletonOSC no tiene handler de export.
- **No hay VERSION.md escrito a oido.** El de `v1` cuenta de donde sale cada
  decision. Este cuenta lo que se puede medir, y no mas que eso.
