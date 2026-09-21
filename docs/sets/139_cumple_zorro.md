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
