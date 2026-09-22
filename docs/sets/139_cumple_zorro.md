# 139 · Cumple Zorro · 1 a 3 AM

Boliche con sistema grande. Recibe la pista de otro DJ a la 1 y la entrega a otro
a las 3. Progressive con color e intensidad, y **Sizer** (Agustin Pietrocola) como
tema modelo. Config: `data/set_configs/cumple_zorro.json`.

## Versiones

Cada version es un tag de git. Para volver a una:

```bash
git checkout set139-v2 -- data/set_targets/set_139.json
python scripts/build_set.py 139        # con Rekordbox cerrado
```

| tag | commit | que cambio | por que |
|---|---|---|---|
| `set139-v1` | ae02a16 | Primera version. Pool = los 150 temas mas parecidos a la FORMA de Sizer + los 30 mas parecidos entre los intensos. Sizer abre. Pico con Passenger 2:09, Olimpo 2:47. | Arco propio por set: la regla global dejaba la energia libre y la primera prueba salio con el pico en el tema 2. |
| `set139-v2` | 25cefe6 | La rueda se mueve en cada paso (31% -> 0% quieto). Entran Rescue Me, Astronauts Nightmares, Wakefeld, Disorder. | **Error:** se "mejoro" contra un 14% de referencia viejo. Medido contra los pros era 29%: esta version se ALEJO de ellos. |
| `set139-v3` | 823c9a3 | Armonia calibrada contra 11 DJs: rueda hasta 2 pasos, castigo por quedarse 0.3, BPM hasta 3. Pico 2:15 con Inertia. | "Siempre referencia pro es la clave." Distancia al perfil pro 97 -> 67. |
| `set139-v4` | 7ff0971 | **Escucha del DJ.** Abre Imentet -> Open Sea; Sizer al pico (2:10); Olimpo 2:44; seis temas vocales; afuera High On, Anja, Low Era, Inertia, A Story Retold y los que comparten su firma. | La energia calculada estaba invertida en varios pares (error medio 1.3 contra el oido del DJ). Lo que escucho pisa el calculo. |

## La escucha que produjo la v4

| tema | calculada | lo que escucho el DJ |
|---|---|---|
| Sizer | 5.2 | mas adelante, mas peak -> 7.7 |
| Touch The Sky | 6.8 | parecida a Sizer -> 7.5 |
| Imentet | 5.7 | arranca mas tranqui que Sizer -> 5.4 |
| Open Sea | 6.1 | menos que Imentet, mas oscuro, mucho groove -> 5.2 |
| High On | 6.5 | pasado, muy tecnoso -> afuera |
| Anja | 6.9 | mas lento -> afuera |
| Inertia | 7.8 | se cae en energia fortisimo -> afuera |
| Low Era | 7.5 | oscuro, baja energia -> afuera |
| A Story Retold | 6.7 | poca energia para entregar, quiero mas voces -> afuera |

Queda en `data/energia_percibida.json`, que leen el solver y el auditor.

| `set139-v5` | (este commit) | Cierra con Fragma: Olimpo 2:36 -> Alafia (E8.6) 2:44 -> Fragma 2:53. Placebo afuera. | Escucha del DJ: "Placebo no esta bueno, quiero terminar mas arriba; Fragma tremendo tema, mi sonido totalmente". |

## La noche completa

| set | horario | config | tag |
|---|---|---|---|
| 140 · Warm organico estilo Maze 28 | 23 a 1 | `cumple_zorro_warm.json` | `set140-v1` |
| 139 · Sizer | 1 a 3 | `cumple_zorro.json` | `set139-v5` |
| 141 · House/progressive vocal, cierre heroico y romantico | 3 a 5 | `cumple_zorro_3a5.json` | `set141-v1` |

Ninguna cancion se repite en la noche (tampoco en otra version). Cada set empalma
con el siguiente: el ultimo del warm es compatible con Imentet (`salida_hacia`), y
el primero del 3 a 5 con Fragma (`entrada_desde`).

- **140**: BPM en rampa 118 -> 122 (`bpm_arco`). En la biblioteca hay solo 40
  organicos a 117-119 y el ranking por forma de Maze los dejaba afuera: se
  sumaron aparte. El arranque es suave (Juri, E4.1) porque lo organico a 118 lo es.
- **141**: Jumbo (heroico) hacia las 4:21, The Whiteroom E8.5 a las 4:28, y
  cierre fijo Your Light -> Haunted (`cierre_fijo`). La primera version llegaba a
  Haunted con un salto de 5 en la rueda: fijar el ultimo le salteaba el control
  de key al anteultimo. Corregido en el solver.

