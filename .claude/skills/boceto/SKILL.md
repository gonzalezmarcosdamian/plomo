---
name: boceto
description: Genera el esqueleto de un track para Ableton - clips MIDI (acordes, bajo, arpegio, bateria, melodia) y un plano de arreglo con los compases derivados de un corpus real. Usar para arrancar una produccion sin partir de cero.
---

# Boceto de track

Lo ejecuta el agente `productor`. Dos pasos: derivar la plantilla del corpus, y
generar el boceto con esos numeros.

## 1. Derivar la plantilla (una sola vez por estilo)

```bash
./.venv/Scripts/python.exe scripts/derive_template.py \
  --artista "Ezequiel Arias" --json data/plantillas/eze_arias.json
```

Mide todos los tracks de ese artista que haya en la biblioteca y devuelve la
mediana: BPM, largo, LUFS, rango dinamico, balance espectral, ancho estereo, y
la forma del arreglo.

Tarda unos 15 segundos por track. El JSON guarda el detalle de cada uno, asi que
rehacer las cuentas despues es instantaneo:

```bash
./.venv/Scripts/python.exe scripts/derive_template.py --recalcular data/plantillas/eze_arias.json
```

**La forma se calcula por votacion posicion a posicion**, no promediando
"donde arranca" y "cuanto dura". Esas dos medianas son distribuciones
independientes y dejan huecos: dan un arreglo que no encaja consigo mismo. La
votacion normaliza cada track a 100 posiciones, cada posicion vota que seccion
es, y gana la mayoria. La columna *acuerdo* dice cuanto del corpus vota lo
mismo — abajo del 50% eso es una tendencia, no una regla.

## 2. Generar el boceto

```bash
./.venv/Scripts/python.exe scripts/make_sketch.py --camelot 4A --bpm 123
./.venv/Scripts/python.exe scripts/make_sketch.py --camelot 8A --registro oscuro
```

Sale en `postproduction/bocetos/<nombre>/`: cinco clips MIDI de 8 compases mas
un `ARREGLO.md` con el plano.

| registro | progresion | para que sirve |
|---|---|---|
| `luminoso` | i - VI - III - VII | progressive melodico, empuja hacia arriba |
| `oscuro` | i - VII - VI - VII | no resuelve nunca, sostiene meseta hipnotica |
| `suspendido` | i - v - VI - III | deja todo en suspenso, para breakdowns largos |

La tonalidad se pide en Camelot, igual que en todo el resto del proyecto: `4A`
es Fm, `8A` es Am.

## 3. Escucharlo antes de abrir el DAW

```bash
./.venv/Scripts/python.exe scripts/render_sketch.py postproduction/bocetos/<nombre> --abrir
```

Sintetiza los cinco clips y arma una maqueta de 32 compases (62 s a 123 BPM) que
sigue la forma de la plantilla en miniatura: groove, groove pleno, breakdown,
drop. Deja `maqueta.wav` y `maqueta.mp3` en la misma carpeta.

No hay instrumentos instalados, asi que las voces son sintesis propia: aditiva
para los tonales, ruido filtrado y barrido de frecuencia para la bateria. Lleva
sidechain contra el kick, que es lo que hace respirar a un progressive — sin eso
el pad tapa el bombo y suena a maqueta de teclado.

Al terminar compara el balance espectral contra la plantilla y muestra la
desviacion por banda. **Reportar esa desviacion, no esconderla:** las notas
pueden estar bien y la mezcla no parecerse en nada a la referencia.

El punto es descartar un boceto malo en treinta segundos, no entregar un master.

## 4. Importar a Ableton

Live 12 esta instalado en `C:\ProgramData\Ableton\Live 12 Trial\`. Poner el
proyecto al BPM del boceto y arrastrar cada `.mid` a una pista MIDI vacia.

Los clips son loops de 8 compases a proposito, para trabajar en vista Session y
armar el arreglo siguiendo el plano.

## Lo que esto no hace

Elegir los sonidos, que es donde se decide si el track existe. El esqueleto es
correcto y generico: el caracter sale del pad, del kick y de la mezcla. Decirlo
cada vez que se entrega un boceto — no es falsa modestia, es lo que separa esto
de una promesa que no puede cumplir.
