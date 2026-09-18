# El giro Dilby — 2026-09-18

El DJ mandó una playlist de Spotify y una frase: *"quiero que mi sonido vaya por
acá, Nanda tremendo tema"*. No es un pedido de sets: es un cambio de dirección, y
por eso queda escrito.

## Qué es este sonido

No es el progressive de la casa. Es **tech house y melodic house groovero**:
menos pad y menos arco largo, más bajo redondo y más percusión adelante. El tema
que lo define es **M.O.S. – Nanda (Dilby Remix)**, 123 BPM en Gm.

Medido sobre las doce semillas:

| | |
|---|---|
| BPM | 120 – 128, mediana **124** |
| Tonalidad | casi todo **menor** (Dbm, F#m, Cm, Em, Dm, Ebm, Gm) |
| Contra el sonido propio | la mediana de lo tocado es 122 BPM — esto vive **2 BPM más arriba** |

Dos BPM no suenan a mucho escrito, pero es la diferencia entre un set que respira
y uno que empuja. Es el cambio real.

## La playlist semilla

| # | Tema | En la biblioteca |
|---|---|---|
| 1 | Dilby – Remember Me | sí |
| 2 | DAVI – Self R3B00T | no |
| 3 | Deep Dish – Flashdance (Shai T Remix) | no |
| 4 | Dor Danino – Like A Stone | no |
| 5 | Tom Evans, Bruno Blanc – Play It Twice (Dilby Remix) | sí |
| 6 | Dilby, Liv Campbell – Trippin' | no |
| 7 | Marc Lenz, Dilby – Arabic Soul (Dilby Remix) | no |
| 8 | Hardy Heller, Alex Connors – Ever Growing (Dilby Mix) | no |
| 9 | Butch, Nic Fanciulli – I Want You | no |
| 10 | James Cole – Khumba | no |
| 11 | Dilby, Trice Be – Feel It | no |
| 12 | **M.O.S., Dilby – Nanda (Dilby Remix)** | no |

## Quiénes son

- **Dilby** — el centro de gravedad: aparece como productor o remixer en **seis
  de los doce**. Australiano radicado en Berlín, tech house con groove melódico.
  Ya había 13 tracks suyos en la biblioteca y un set armado (73, *Dilby & Co —
  Showcase Groove*), así que no es un descubrimiento: es una preferencia que
  estaba y ahora se declara.
- **DAVI** — 10 tracks en la biblioteca. Melódico y espacioso, el más cercano a
  lo que ya se toca; es el puente natural entre el sonido viejo y este.
- **Butch** y **Nic Fanciulli** — peso pesado del house europeo. Cero en la
  biblioteca. *I Want You* va a 128, el techo del rango.
- **Deep Dish** — el nombre grande del lote, con el remix de Shai T de
  *Flashdance*. De Shai T ya había un track (*Islander*, con Kasper Koman).
- **Dor Danino**, **Marc Lenz**, **Hardy Heller**, **James Cole**, **Liv
  Campbell**, **Trice Be**, **Alex Connors** — cero en la biblioteca. Son la
  parte nueva de verdad.

## Qué se hizo

Las doce semillas están en Muzpa: diez para bajar, dos ya estaban. El escaneo
**por artista** de los catorce nombres dio 124 temas más en el rango 118-130.
Todo junto en `data/batch_sonido_dilby_2026-09-18.txt`.

## Lo que falta para que esto se mida solo

`scripts/spotify_radio.py` trae la radio de un tema y la cruza contra la
biblioteca, que es la tercera fuente de descubrimiento que faltaba: el radar de
sellos dice lo que SALE, los setlists dicen lo que se TOCA, y la radio dice a
dónde lleva un tema que pegó.

**No corre todavía**: `SPOTIFY_CLIENT_ID` y `SPOTIFY_CLIENT_SECRET` están en el
`.env` pero vacíos. Se sacan en developer.spotify.com creando una app. Ojo que
Spotify cerró `/recommendations` y `/related-artists` para apps nuevas: el script
detecta si el endpoint responde y, si no, arma la radio con los artistas que
comparten disco con la semilla. Avisa cuál de los dos caminos usó.
