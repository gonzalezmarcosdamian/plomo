# Plan: de generar a calcar

Estado durable del trabajo de producción. **Sobrevive a las sesiones** — cada
sesión nueva empieza leyendo este archivo y `data/juicio/` para saber dónde
quedó todo.

---

## Por qué se cambió de enfoque

Tres semanas generando un tema desde constantes escritas a mano (`FRASE_BAJO`,
`GANCHO`, `PROGRESION`) y ajustándolas contra mediciones. El juicio del DJ no
se movió nunca: *"no me dice nada"* → *"parece un ringtone"* → *"increíblemente
horrible, aunque mejores efectos"*.

Dos agentes midieron por qué, y las dos causas son de origen, no de mezcla:

- **El gancho atacaba 168 de 168 veces encima de un bombo.** El 100%. Negras
  exactas sobre la grilla, sin una síncopa, una figura de cuatro compases
  repetida cuarenta veces. Eso *es* la definición de un ringtone polifónico.
- **El bus melódico tiene el 96% de su banda vacía.** Cresta espectral 33-45 dB
  contra 18-29 de las referencias; centroide 435-950 Hz contra 1210-1992. Tres
  parciales limpios y nada en el medio. Ningún efecto arregla eso — por eso
  *"aunque mejores efectos"*.

Y una tercera, estructural: **nada cambia**. Un compás distinto de 16 contra
10-14 en las referencias; cuatro capas idénticas al 94-100% durante 60
compases.

**La conclusión:** ajustar constantes nunca va a dejar de sonar a constantes
ajustadas. El material tiene que venir de temas reales.

---

## La arquitectura nueva

```
  referencias  ──[calcar.py]──▶  data/vocabulario/*.json
   (mp3 reales)                   patrones, progresiones, células, voicings
                                            │
                                     [armar.py]  ──▶  MIDI
                                            │
                                     [juzgar.py] ──▶  veredicto
                                            │
                                     [render.py] ──▶  audio  ──▶  el DJ escucha
                                            │
                                         ◀── loop ───┘
```

Lo que cambia respecto de `idea.py`: **la fuente del material**. Hoy los
patrones los escribí yo; en la arquitectura nueva se extraen de temas medidos
y se guardan como datos versionados. `armar.py` combina vocabulario, no
inventa.

**Lo que se copia y lo que no.** Los patrones rítmicos y las progresiones no
son material protegible y son lo que define al género: se copian. Una melodía
sí lo es: de ahí se toma el *carácter* medido (dónde cae respecto del pulso,
largo de frase, rango) y las notas se escriben propias. Misma regla que ya rige
para los samples de batería en `data/samples/`: referencia para producir, nunca
material para publicar.

---

## Criterio de convergencia — y su límite

**El loop NO puede converger en "suena profesional".** Puede converger en
mediciones, y ese es exactamente el pozo del que venimos. Así que:

**Lo que el loop cierra solo** (las nueve dimensiones que son invariantes de
género — rango entre referencias menor a 1.5× la tolerancia — más las dos
nuevas):

| dimensión | objetivo | de dónde sale |
|---|---|---|
| bombo x compás | 4.0 ± 0.3 | 4 referencias |
| percusión x compás | 8.2-9.4 | 4 referencias |
| hat x compás | 8.4-10.3 | 4 referencias |
| aire suena | ~100% | 4 referencias |
| cola bajo | 0.05-0.06 s | 4 referencias |
| nivel bajo vs batería | −4 a −6.5 dB | 4 referencias |
| cresta batería | 9.1-11.8 dB | 4 referencias |
| cresta bajo | 13-16 dB | 4 referencias |
| sidechain melódico | −6.8 a −9.6 dB | 4 referencias |
| **cresta espectral batería** | **17.4-18.8 dB** | span de 1.4 dB en 4 refs |
| **ocupación bus melódico** | **44-100%** | propio: 4-25% |
| **compases distintos de 16** | **10-14** | propio: 1 |

**Lo que NO se persigue** (seis dimensiones donde *el mismo tema contra sí
mismo* falla la tolerancia, o donde el rango entre referencias es 4-8× la
tolerancia): bajo ataques, bajo suena, melodía ataques, melodía suena,
sidechain bajo, nivel melódico vs batería. Describen al tema, no al género.

**El test de aceptación es el DJ.** Cada vuelta termina en un render que él
escucha. El loop propone; el oído dispone.

---

## Fases

### Fase 0 — limpiar y fijar (hecha)
- Borrados los catorce bocetos propios. v1 (tag `tema-v1`), v2 y v3 quedan en
  git; las transcripciones de referencias se conservan.
- `revisa_robot()` arreglado: medía sobre la unión de capas y trece capas
  repitiendo verbatim pasaban invisibles. Ahora mide por capa.
- `scripts/timbre.py` nuevo: cresta espectral, ocupación, centroide y ancho de
  banda por bus.

### Fase 1 — aprender
1. **Copiando un tema** — `copiar_tema.py` tiene que dar material usable. La
   batería es fiable (99% de bombos a <20 ms), el bajo pasó de 55 notas todas
   de una semicorchea (69% fuera de tonalidad) a 46 notas con duración real
   (96% en escala), y la armonía pasó de aplastarse en un acorde repetido a
   una progresión real (el bug era puntuar por suma en vez de correlación).
   `tests/test_copiar_tema.py` y `tests/test_juzgar.py` blindan con audio
   sintético la parte de la cadena que causó esos tres bugs — no reemplazan
   probar contra una referencia real, pero evitan que un arreglo se rompa de
   nuevo en silencio.
2. **De foros de productores** — qué dicen sobre arreglo, sound design y
   estructura en este género. Buscar reglas con su porqué, no listas.
3. **De videos de productores** — transcripciones de tutoriales.

Todo lo aprendido va a `data/vocabulario/` como dato versionado con su fuente,
igual que `rules/curaduria.json`: valor, porqué, evidencia.

### Fase 2 — el juez
`escuchar.py` pasa a incorporar timbre y variación, y a bajar las seis
dimensiones que son ruido. Un veredicto, no veinte filas.

### Fase 3 — el loop
Cada vuelta: leer el estado → arreglar **una** dimensión → generar → renderizar
→ medir → escribir la vuelta en `data/juicio/NNN.json` → checkpoint.

Una por vuelta. Cambiar dos cosas y medir no dice cuál de las dos hizo qué.

---

## Estado entre sesiones

| archivo | qué guarda |
|---|---|
| `docs/PLAN.md` | este plan y el criterio de convergencia |
| `data/juicio/NNN.json` | cada vuelta: qué se cambió, qué midió antes y después |
| `data/vocabulario/` | el material extraído de referencias |
| `docs/APRENDIZAJES.md` | las lecciones durables |
| `docs/BITACORA.md` | qué se hizo, por fecha |
| `data/sets/*.json` | la receta de cada set de Live |

Una sesión nueva arranca: leer este archivo, leer la última vuelta de
`data/juicio/`, seguir.
