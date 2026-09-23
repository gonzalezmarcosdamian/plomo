# 139 · Cumple Zorro · 1 a 3 AM

Boliche con sistema grande. Recibe la pista de otro DJ a la 1 y la entrega a otro
a las 3. Progressive con color e intensidad, y **Sizer** (Agustin Pietrocola) como
tema modelo. Config: `data/set_configs/cumple_zorro.json`.

## v8 — la zona, no los temas (2026-09-23)

"Estan o muy oscuros o muy pasados o muy lentos". Las tres cosas estaban
medidas: ibamos 1-3 BPM debajo del piso de los pros y 1.5 puntos de energia
arriba de su techo.

| set | BPM med | E med | E max | mayor | groove |
|---|---|---|---|---|---|
| 140 warm | 122 | 6.0 | 6.9 | 6% | 1.04 |
| 142 warm col | 122 | 6.0 | 6.9 | 24% | 0.83 |
| 139 | 123 | 6.6 | 8.6 | 18% | 0.95 |
| 143 col | 123 | 6.4 | 8.6 | 24% | 1.04 |
| 141 | 123 | 6.7 | 8.5 | 6% | 0.83 |
| 144 col | 124 | 6.6 | 7.3 | 24% | 0.98 |
| 145 | 122 | 6.3 | 7.5 | 6% | 0.72 |
| los pros | 123 | 5.7 | 6.9 (p90) | 11% | 1.25 |

El unico tema arriba de 7.5 en cada set es el pico anclado: Alafia (E8.6) en
el 139 y el 143, The Whiteroom (E8.5) en el 141. Todo lo demas vive en la
banda de la referencia.

---

## v7 — el colorido deja de ser un nombre (2026-09-23)

"Escuche entero el de 1 a 3, un par medios oscuro para ser el colorido". Los
dos eran los dos primeros: Imentet (percentil 33 de brillo) y Open Sea (43), que
la colorida heredaba del config base. Pero el problema era mas grande: los siete
sets tenian 0% de temas en tonalidad mayor.

| set | mayor | cambios de modo | brillo |
|---|---|---|---|
| 139 | 0% | 0% | 19.3 |
| 140 | 0% | 0% | 22.3 |
| 141 | 18% | 38% | 20.6 |
| 142 colorido | 29% | 12% | 25.6 |
| 143 colorido | 24% | 44% | 25.8 |
| 144 colorido | 24% | 38% | 27.0 |
| 145 | 6% | 6% | 17.8 |
| los pros | 11% | 25% | |

El 143 ahora abre con Kamilo Sanclemente en 2B y cruza a mayor cuatro veces.

**El 139 y el 140 siguen en 0%, y es por sus anclas.** El 139 tiene 8 de 17
posiciones fijas entre anclas, apertura y cierre, y las ocho son temas en menor;
el 140 tiene siete. Material mayor hay (17% de su pool elegible), pero con medio
set clavado la cuota no tiene donde moverse. Son los temas que eligio el DJ: si
quiere color ahi tambien, hay que soltar alguna ancla.

---

## v6 — la noche entera con el criterio entrenado (2026-09-23)

El DJ escucho y saco tres cosas: Llego La Hora, Meduza - Friends y "nada afro"
como categoria. Despues dijo donde estaba el problema real: la cuota de genero
tenia que ser lo ultimo, no lo primero. Ver APRENDIZAJES.md, "La jerarquia
estaba escrita en la doc y al reves en el codigo".

Los siete sets se rearmaron con reglas 1.6.1, cuyos pesos los eligio
`scripts/entrenar_criterio.py` midiendo contra los 40 setlists de referencia
(perdida 3.750 -> 2.467). Verificado sobre los sets escritos:

| set | temas | vetados | ajenos | afro | groove | paso E | corr | top-5 |
|---|---|---|---|---|---|---|---|---|
| 139 | 17 | 0 | 0 | 0 | 1.19 | 0.55 | +0.73 | 29% |
| 140 | 17 | 0 | 0 | 0 | 0.97 | 0.40 | +0.42 | 29% |
| 141 | 17 | 0 | 1 | 0 | 0.95 | 0.45 | +0.18 | 29% |
| 142 | 17 | 0 | 0 | 0 | 0.82 | 0.45 | +0.55 | 35% |
| 143 | 17 | 0 | 0 | 0 | 1.23 | 0.50 | +0.70 | 35% |
| 144 | 17 | 0 | 0 | 0 | 0.97 | 0.65 | +0.08 | 29% |
| 145 | 17 | 0 | 0 | 0 | 0.79 | 0.70 | +0.80 | 71% |
| pro | | 0 | | 0 | 1.25 | 1.00 | +0.11 | 50% |

Lo que cierra: vetos, procedencia y groove. Lo que no: seguimos dando pasos de
energia de la mitad que ellos. Y la correlacion posicion-energia no es
comparable de frente: el +0.11 de los pros sale de sets que cubren una noche
entera, y estos son tramos de dos horas que reciben y entregan la pista, asi
que un 139 que sube esta haciendo lo que tiene que hacer.

---

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

