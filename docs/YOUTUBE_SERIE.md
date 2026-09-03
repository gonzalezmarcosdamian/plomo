# Serie "Sonido Argentino" — 10 videos para YouTube

Plan de producción de la primera ronda. Revisado 2026-09-03.

## La apuesta

**No competir en "Melodic Techno 2026".** Está saturado de canales que resubén
sets de Miss Monique, Anyma y ARTBAT: volumen alto, competencia imposible.

La serie va por el linaje **Cattaneo / Eze Arias / Emi Galván / Kamilo**. Menos
búsquedas, competencia casi nula, y es lo único que esta biblioteca tiene curado
así. La ventaja no es el alcance inmediato: es que el que llega se queda, y que
los sellos del palo son chicos y miran quién los toca.

---

## Cómo se mide esto (verificado, no supuesto)

- **Content ID reclama todo mix con música con derechos.** El sello se lleva los
  ads; el video no se bloquea ni genera strike. **YouTube es vidriera y archivo,
  no ingreso.** Cualquier plan que asuma monetización es falso.
- **La retención en contenido de DJ es baja y eso es normal.** Un canal de gaming
  llega a 50% en 30 min sin esfuerzo; uno de DJ pelea para lograr 50% en 15 min.
  No hay que corregirlo: hay que dejar de mirarlo.
- **La métrica real es watch time total, no % de retención.** Un video de 75 min
  al 25% da 19 minutos por espectador. Uno de 10 min al 60% da 6. El algoritmo
  cuenta minutos.
- **El mix se consume en segundo plano.** Duración larga es un activo, no un
  riesgo: la gente lo pone y sigue con lo suyo.
- **Los Shorts son el motor de descubrimiento**, el long-form es la sustancia.
  Un set grabado rinde 1 video largo + 6 shorts sin trabajo extra.

---

## Tamaño: 75 minutos, 18 tracks

Calculado con la duración real de tus tracks (promedio 6,9 min) y blends de 3 min:

| Video | Tracks |
|-------|--------|
| 45 min | ~11 |
| **75 min** | **~18** |
| 90 min | ~22 |
| 120 min | ~30 |

Tus sets actuales quedan cortos para esto: el 73 (12 tracks) da 55 min, el 75
(10 tracks) da 43 min. **Los sets de la serie se arman a 18 tracks.**

75 minutos es el punto: suficiente watch time por visita, un arco completo que
se sostiene, y una sesión de escucha entera. Los de 2 h suman minutos pero el
arco se diluye y cuesta el triple grabarlos bien.

---

## Los 10 videos

**Se permite repetir tracks entre sets.** Son diez sets que nunca se grabaron, y
cada uno se ve por separado: cada uno lleva lo mejor que tenga el concepto, sin
racionar. El track ancla de un concepto puede aparecer en dos videos si le
corresponde a los dos.

| # | Título del video | Identidad | Material |
|---|------------------|-----------|----------|
| 01 | Hernan Cattaneo Style \| Progressive Argentino | El atardecer que construye sin apurarse | 40 |
| 02 | Ezequiel Arias Style \| Peak Vocal | El puente entre Hernan y Afterlife | 98 |
| 03 | Emi Galván Style \| Progresivo Colorido | Color y emoción, sin oscuridad | 69 |
| 04 | Kamilo Sanclemente Style \| Colombia Progresiva | El primo colombiano del sonido | 85 |
| 05 | Sudbeat Sessions \| Driving Progressive | El sello de Hernan: narrativo | 83 |
| 06 | Mango Alley \| Deep Progressive | La nueva generación | 120 |
| 07 | Simon Vuarambon Style \| Hipnótico | No pasa nada pero pasa todo | 88 |
| 08 | Nick Warren Style \| The Soundgarden | El eje Warren / Fredes / Pavicich | 73 |
| 09 | Córdoba Progressive \| Gai Barone Style | La órbita local | 103 |
| 10 | Argentina Peak Time | El cierre: lo más alto de la biblioteca | 78 |

Numeración interna: **sets 80-89** (no chocan con 74-76 ni con la serie 90+).

---

## Qué sale de cada grabación

Una sola sesión de grabación produce cuatro piezas:

1. **El video largo** — 75 min, cámara fija. Es el activo.
2. **6 Shorts** — 40-60 s cada uno, sacados de los mejores momentos del mismo
   set. Este es el motor de descubrimiento y sale gratis del material ya grabado.
   Uno por semana entre lanzamiento y lanzamiento mantiene el canal vivo.
3. **El tracklist** — va completo en la descripción, con remixers y sellos. Los
   artistas del nicho lo miran; un tracklist mal escrito quema.
4. **La playlist de la serie** — los 10 en auto-play. Sube el watch time de
   sesión y le enseña al algoritmo de qué es el canal.

### Especificaciones de video

- **Cámara fija, sin edición.** Golden hour en terraza si hay luz; si no, plano
  fijo de los CDJs. La escala honesta suma, la escala falsa quema.
- **Audio:** grabar la salida de la mezcladora, no el micrófono. 320 kbps o WAV.
- **Título:** `Hernan Cattaneo Style | Progressive Argentino 2026 | Sonido Argentino #01`
  El formato `DJ + Style + Género + Año` es lo que manda las búsquedas del nicho.
- **Miniatura:** misma plantilla los 10, cambiando color y número. La serie se
  tiene que reconocer de un vistazo en la grilla.

### Cadencia

Un video cada dos semanas, un Short por semana. Diez videos = cinco meses.
Sostenible con trabajo y sin equipo.

---

## Lo que NO hay que hacer

- **No postear el código ni el pipeline.** Trae developers, no fechas, e instala
  que la máquina elige por vos — lo contrario de lo que vende este palo.
- **No abrir con un set de 3 horas.** Nadie escucha tres horas de un desconocido.
- **No usar "track ID?" como gancho.** Es lo más gastado y te mete en la bolsa de
  la que querés diferenciarte: vos vendés lo contrario, decir todo.
- **No mirar el % de retención.** En este formato siempre va a ser bajo. Mirá
  minutos vistos.

---

## Material de refuerzo

Radar Muzpa desde 2026-06-20: **327 lanzamientos** nuevos que no están en la
biblioteca. Filtrados a sellos core y BPM 118-127: 213. De ahí, **62 elegidos
por concepto** en `data/batch_serie_argentina.txt`.

Con repeticiones permitidas, los 62 son opcionales: la biblioteca (1757 tracks)
ya cubre los diez. Sirven para que los videos tengan material que nadie más está
tocando, que es la única ventaja competitiva real en un nicho chico.

---

## Pipeline por video

```
1. python scripts/dump_pool.py
2. editar data/set_configs/serie_argentina.json     (concepto, artistas, energía)
3. python scripts/select_set.py data/set_configs/serie_argentina.json
4. python scripts/build_set.py <num> --dry
5. python scripts/build_set.py <num>
6. python scripts/audit_sets.py <num>               (0 transiciones flojas)
7. grabar 75 min → cortar 6 shorts → subir con tracklist
```
