# Guion de cortes — serie "Sonido Argentino" (sets 80-89)

Generado por `data/redes/generar_cortes.py`. **Nada de esto esta publicado ni programado.** Es material preparado; la decision de que sale y cuando la toma Gonzalo.

## Como se eligio cada momento

El momento no se elige a ojo. Cada track del set se evalua con sus cues v8 y su energia, y despues se filtra y se rankea.

**Filtros duros** (si falla uno, el track queda afuera):

- Tiene los cuatro cues: `Bass IN`, `Breakdown`, `DROP`, `Mix-OUT`.
- El archivo existe en disco en el `FolderPath` actual (`Music/Biblioteca/AAAA-MM/`).
- El gap `Breakdown -> DROP` es de **15s o mas**. Menos que eso no da tension para llenar la primera mitad del corte.
- La ventana **no arranca antes del `Bass IN`** y **no pisa el `Mix-OUT`**.

**La ventana**: arranca en `DROP - min(60% del gap, 25s)` y dura 30s. Arranca *antes* del momento, no en el momento: la tension es la mitad del corte.

**El ranking** pondera cuatro cosas:

| Peso | Que mide |
|---|---|
| 35% identidad | lift medido del artista y del sello en `data/mi_sonido.json`, con piso de 3 tracks en biblioteca. Es lo que hace que el corte hable de este proyecto y no de cualquiera. |
| 30% tension | largo del gap `Breakdown -> DROP`, entre 15 y 90s. |
| 20% energia | premia la franja E5.5-7.5, arriba de la mediana medida (5.7) porque el formato corto no tiene tiempo de construir. |
| 15% arco | la zona 55-85% del set vale mas; el primer tercio vale menos. |

**Diversidad**: los 6 cortes de un set caen en 6 tracks distintos, separados por al menos 2 posiciones, y sin repetir artista mientras haya con que. Verificado: 0 colisiones de track entre los 10 sets, asi que los 60 cortes son 60 tracks distintos.

**El reloj del set** asume blends de 180s (`docs/YOUTUBE_SERIE.md`). Es una estimacion sobre la grabacion planificada: cuando el set este grabado de verdad, el minuto real se corrige contra el audio y esta tabla vuelve a correr.

## Notas de produccion

- El `-ss` de cada comando esta en **segundos del set grabado**, no del track. Sale del reloj estimado; hay que corregirlo contra el audio real antes de cortar.
- El crop es centrado (`crop=ih*9/16:ih`). Si la camara no esta centrada en los CDJs hay que agregar el offset `x=` a mano.
- El `loudnorm` va en una pasada, que alcanza para 30 segundos. Si se van a publicar varios cortes seguidos y se nota diferencia de volumen entre ellos, conviene medir con `pyloudnorm` sobre los seis y aplicar una ganancia fija por corte en vez de normalizar cada uno por separado.
- `docs/YOUTUBE_SERIE.md` habla de cortes de 40-60s y aca son de 30s. **Es una diferencia sin resolver.** 30s entra en la regla de 15-40s del formato vertical; si se prefieren 60s, hay que volver a correr los filtros porque varias ventanas empiezan a pisar el `Mix-OUT`.

---

## 80. Hernan Cattaneo Style — Progressive Argentino

18 tracks · ~89 min estimados · 17 de 18 tracks pasaron los filtros

| # | min del set | seg en track | ventana | gap | E | tipo | linea |
|---|---|---|---|---|---|---|---|
| 1 | 48.7 | 225 | 225-255s (drop 250) | 61s | 6.1 | kick tras breakdown largo | Dmitry Molosh, Michael A — Integral (Original Mix) — Replug — 122 BPM — minuto 48 del set |
| 2 | 39.6 | 274 | 274-304s (drop 299) | 47s | 5.6 | kick tras breakdown largo | Cendryma — Orbitation (Extended Mix) — UV Noir — 122 BPM — minuto 39 del set |
| 3 | 76.4 | 306 | 306-336s (drop 330) | 79s | 6.6 | kick tras breakdown largo | Navar & Dmitry Molosh — Small Wonders (Hernan Cattaneo & Marcelo Vasami Remix) — Proportion — 122 BPM — minuto 76 del set |
| 4 | 27.5 | 261 | 261-291s (drop 286) | 48s | 4.9 | kick tras breakdown largo | Tom Pavicich, Analog Sense — Cardamom (FAERO Remix) — Transensations Records — 121 BPM — minuto 27 del set |
| 5 | 84.0 | 105 | 105-135s (drop 123) | 29s | 6.0 | track identitario | FAERO, Tom Pavicich, Analog Sense — The Landing (Club Mix) — Balkan Connection — 123 BPM — minuto 84 del set |
| 6 | 60.8 | 256 | 256-286s (drop 281) | 62s | 6.2 | kick tras breakdown largo | Hernan Cattaneo, Khen — Rogelito (Original Mix) — Closure — 123 BPM — minuto 60 del set |

<details><summary>Comandos ffmpeg</summary>

```bash
ffmpeg -ss 2922.0 -t 30 -i "grabacion_set80.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_80_1.mp4"
ffmpeg -ss 2376.0 -t 30 -i "grabacion_set80.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_80_2.mp4"
ffmpeg -ss 4584.0 -t 30 -i "grabacion_set80.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_80_3.mp4"
ffmpeg -ss 1650.0 -t 30 -i "grabacion_set80.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_80_4.mp4"
ffmpeg -ss 5040.0 -t 30 -i "grabacion_set80.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_80_5.mp4"
ffmpeg -ss 3648.0 -t 30 -i "grabacion_set80.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_80_6.mp4"
```

</details>

## 81. Ezequiel Arias Style — Peak Vocal

18 tracks · ~82 min estimados · 17 de 18 tracks pasaron los filtros

| # | min del set | seg en track | ventana | gap | E | tipo | linea |
|---|---|---|---|---|---|---|---|
| 1 | 57.9 | 287 | 287-317s (drop 312) | 100s | 7.0 | kick tras breakdown largo | Cid Inc. — Citadel (Original Mix) — Replug — 123 BPM — minuto 57 del set |
| 2 | 41.7 | 272 | 272-302s (drop 297) | 55s | 6.3 | kick tras breakdown largo | Emi Galvan — Boomera (Original Mix) — Sudbeat Music — 123 BPM — minuto 41 del set |
| 3 | 70.4 | 225 | 225-255s (drop 250) | 62s | 6.9 | kick tras breakdown largo | Rockka — Amnesia (Fuenka Remix) — Mango Alley — 123 BPM — minuto 70 del set |
| 4 | 78.3 | 225 | 225-255s (drop 250) | 55s | 6.4 | kick tras breakdown largo | Kamilo Sanclemente, Mauro Aguirre — Goldes Eyes (Original Mix) — Sudbeat Music — 123 BPM — minuto 78 del set |
| 5 | 29.3 | 43 | 43-73s (drop 62) | 31s | 6.4 | entrada de kick | Ezequiel Arias — Eterno (Extended Mix) — Anjunadeep — 124 BPM — minuto 29 del set |
| 6 | 20.2 | 292 | 292-322s (drop 317) | 64s | 5.1 | kick tras breakdown largo | Simon Vuarambon — Diafana (Original Mix) — Moments — 121 BPM — minuto 20 del set |

<details><summary>Comandos ffmpeg</summary>

```bash
ffmpeg -ss 3474.0 -t 30 -i "grabacion_set81.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_81_1.mp4"
ffmpeg -ss 2502.0 -t 30 -i "grabacion_set81.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_81_2.mp4"
ffmpeg -ss 4224.0 -t 30 -i "grabacion_set81.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_81_3.mp4"
ffmpeg -ss 4698.0 -t 30 -i "grabacion_set81.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_81_4.mp4"
ffmpeg -ss 1758.0 -t 30 -i "grabacion_set81.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_81_5.mp4"
ffmpeg -ss 1212.0 -t 30 -i "grabacion_set81.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_81_6.mp4"
```

</details>

## 82. Emi Galvan Style — Progresivo Colorido

18 tracks · ~89 min estimados · 18 de 18 tracks pasaron los filtros

| # | min del set | seg en track | ventana | gap | E | tipo | linea |
|---|---|---|---|---|---|---|---|
| 1 | 50.2 | 242 | 242-272s (drop 268) | 79s | 6.3 | kick tras breakdown largo | Cendryma — Override (Original Mix) — PURRFECTION — 122 BPM — minuto 50 del set |
| 2 | 66.9 | 346 | 346-376s (drop 371) | 109s | 7.0 | kick tras breakdown largo | Kamilo Sanclemente — Parallel Moon (Original Mix) — Sudbeat Music — 123 BPM — minuto 66 del set |
| 3 | 76.2 | 262 | 262-292s (drop 287) | 68s | 6.8 | kick tras breakdown largo | Rockka, Maze 28 — Mirage (Extended Mix) — Clubsonica Records — 123 BPM — minuto 76 del set |
| 4 | 23.1 | 237 | 237-267s (drop 256) | 32s | 4.9 | track identitario | Dimas Mixon, Cendryma — Minicube (Original Mix) — Cydana Sounds — 120 BPM — minuto 23 del set |
| 5 | 86.6 | 321 | 321-351s (drop 346) | 94s | 6.2 | kick tras breakdown largo | Cary Crank — Inner Atlas (Kyotto Remix) — Sunexplosion — 122 BPM — minuto 86 del set |
| 6 | 41.5 | 258 | 258-288s (drop 283) | 63s | 5.8 | kick tras breakdown largo | Melodiam (AR) — Repro Days (Original Mix) — Future Avenue — 122 BPM — minuto 41 del set |

<details><summary>Comandos ffmpeg</summary>

```bash
ffmpeg -ss 3012.0 -t 30 -i "grabacion_set82.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_82_1.mp4"
ffmpeg -ss 4014.0 -t 30 -i "grabacion_set82.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_82_2.mp4"
ffmpeg -ss 4572.0 -t 30 -i "grabacion_set82.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_82_3.mp4"
ffmpeg -ss 1386.0 -t 30 -i "grabacion_set82.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_82_4.mp4"
ffmpeg -ss 5196.0 -t 30 -i "grabacion_set82.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_82_5.mp4"
ffmpeg -ss 2490.0 -t 30 -i "grabacion_set82.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_82_6.mp4"
```

</details>

## 83. Kamilo Sanclemente Style — Colombia Progresiva

18 tracks · ~87 min estimados · 18 de 18 tracks pasaron los filtros

| # | min del set | seg en track | ventana | gap | E | tipo | linea |
|---|---|---|---|---|---|---|---|
| 1 | 55.4 | 321 | 321-351s (drop 346) | 94s | 6.4 | kick tras breakdown largo | Dmitry Molosh — The Moon Lights the Way (Original Mix) — Mango Alley — 122 BPM — minuto 55 del set |
| 2 | 69.8 | 223 | 223-253s (drop 248) | 43s | 7.1 | pico del set | Emi Galvan — Everlong (Original Mix) — Mango Alley — 124 BPM — minuto 69 del set |
| 3 | 38.3 | 243 | 243-273s (drop 268) | 48s | 5.8 | kick tras breakdown largo | Rauschhaus, GRAZZE — Canacona (Original Mix) — Sudbeat Music — 121 BPM — minuto 38 del set |
| 4 | 80.0 | 287 | 287-317s (drop 312) | 86s | 6.6 | kick tras breakdown largo | Cid Inc. — Forgotten — Balance Music — 123 BPM — minuto 80 del set |
| 5 | 25.7 | 233 | 233-263s (drop 252) | 32s | 5.1 | entrada de kick | Cendryma — Parabolic (Original Mix) — Transensations Records — 122 BPM — minuto 25 del set |
| 6 | 18.3 | 219 | 219-249s (drop 238) | 32s | 4.6 | entrada de kick | Tom Pavicich — About Her (Unai Garcia Remix) — Starlight Music Group — 121 BPM — minuto 18 del set |

<details><summary>Comandos ffmpeg</summary>

```bash
ffmpeg -ss 3324.0 -t 30 -i "grabacion_set83.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_83_1.mp4"
ffmpeg -ss 4188.0 -t 30 -i "grabacion_set83.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_83_2.mp4"
ffmpeg -ss 2298.0 -t 30 -i "grabacion_set83.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_83_3.mp4"
ffmpeg -ss 4800.0 -t 30 -i "grabacion_set83.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_83_4.mp4"
ffmpeg -ss 1542.0 -t 30 -i "grabacion_set83.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_83_5.mp4"
ffmpeg -ss 1098.0 -t 30 -i "grabacion_set83.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_83_6.mp4"
```

</details>

## 84. Sudbeat Sessions — Driving Progressive

18 tracks · ~85 min estimados · 18 de 18 tracks pasaron los filtros

| # | min del set | seg en track | ventana | gap | E | tipo | linea |
|---|---|---|---|---|---|---|---|
| 1 | 76.3 | 276 | 276-306s (drop 301) | 69s | 7.0 | kick tras breakdown largo | Ezequiel Arias — Passenger (Original Mix) — Sudbeat Music — 122 BPM — minuto 76 del set |
| 2 | 67.4 | 288 | 288-318s (drop 314) | 97s | 7.5 | pico del set | Maze 28 — Great Attractor (Ruben Karapetyan Remix) — UV — 124 BPM — minuto 67 del set |
| 3 | 25.3 | 327 | 327-357s (drop 352) | 67s | 5.9 | kick tras breakdown largo | Cid Inc., Dmitry Molosh — Aquamarine (Original Mix) — Balance Music — 122 BPM — minuto 25 del set |
| 4 | 43.6 | 314 | 314-344s (drop 339) | 44s | 6.1 | entrada de kick | Guy Mantzur — Love in a Bottle (Original Mix) — Lost & Found — 124 BPM — minuto 43 del set |
| 5 | 48.9 | 132 | 132-162s (drop 155) | 39s | 6.6 | entrada de kick | D-Nox & Sharon Graziani — Shining (Hicky & Kalo Remix) — Plaisirs Sonores Records — 124 BPM — minuto 48 del set |
| 6 | 33.1 | 233 | 233-263s (drop 252) | 32s | 5.6 | entrada de kick | Kamilo Sanclemente — Honest (Leandro Murua Remix) — Magnitude Recordings — 122 BPM — minuto 33 del set |

<details><summary>Comandos ffmpeg</summary>

```bash
ffmpeg -ss 4578.0 -t 30 -i "grabacion_set84.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_84_1.mp4"
ffmpeg -ss 4044.0 -t 30 -i "grabacion_set84.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_84_2.mp4"
ffmpeg -ss 1518.0 -t 30 -i "grabacion_set84.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_84_3.mp4"
ffmpeg -ss 2616.0 -t 30 -i "grabacion_set84.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_84_4.mp4"
ffmpeg -ss 2934.0 -t 30 -i "grabacion_set84.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_84_5.mp4"
ffmpeg -ss 1986.0 -t 30 -i "grabacion_set84.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_84_6.mp4"
```

</details>

## 85. Mango Alley — Deep Progressive

18 tracks · ~79 min estimados · 16 de 18 tracks pasaron los filtros

| # | min del set | seg en track | ventana | gap | E | tipo | linea |
|---|---|---|---|---|---|---|---|
| 1 | 65.9 | 287 | 287-317s (drop 312) | 80s | 7.3 | kick tras breakdown largo | Emi Galvan — Everlong (Ruben Karapetyan Remix) — Mango Alley — 123 BPM — minuto 65 del set |
| 2 | 46.1 | 192 | 192-222s (drop 217) | 41s | 6.4 | track identitario | Hana, Durante — Starglow (Extended Mix) — Anjunadeep — 124 BPM — minuto 46 del set |
| 3 | 54.3 | 213 | 213-243s (drop 238) | 52s | 6.7 | kick tras breakdown largo | Kamilo Sanclemente, Phillipe Lois — Acid Dreams (Original Mix) — Melody Of the Soul — 124 BPM — minuto 54 del set |
| 4 | 37.1 | 229 | 229-259s (drop 254) | 62s | 5.9 | kick tras breakdown largo | Maze 28 — Cry of the Deserts (Aman Anand Remix) — Juicebox Music — 121 BPM — minuto 37 del set |
| 5 | 27.7 | 227 | 227-257s (drop 252) | 63s | 5.8 | kick tras breakdown largo | Hobin Rude — Opposite (Original Mix) — Other Side Sounds — 122 BPM — minuto 27 del set |
| 6 | 74.9 | 240 | 240-270s (drop 265) | 47s | 6.3 | kick tras breakdown largo | Kostya Outta, Greta Meier, Alisha (PL) — Far Above (Original Mix) — Mango Alley — 123 BPM — minuto 74 del set |

<details><summary>Comandos ffmpeg</summary>

```bash
ffmpeg -ss 3954.0 -t 30 -i "grabacion_set85.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_85_1.mp4"
ffmpeg -ss 2766.0 -t 30 -i "grabacion_set85.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_85_2.mp4"
ffmpeg -ss 3258.0 -t 30 -i "grabacion_set85.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_85_3.mp4"
ffmpeg -ss 2226.0 -t 30 -i "grabacion_set85.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_85_4.mp4"
ffmpeg -ss 1662.0 -t 30 -i "grabacion_set85.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_85_5.mp4"
ffmpeg -ss 4494.0 -t 30 -i "grabacion_set85.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_85_6.mp4"
```

</details>

## 86. Simon Vuarambon Style — Hipnotico

18 tracks · ~91 min estimados · 15 de 18 tracks pasaron los filtros

| # | min del set | seg en track | ventana | gap | E | tipo | linea |
|---|---|---|---|---|---|---|---|
| 1 | 83.1 | 274 | 274-304s (drop 299) | 79s | 6.3 | kick tras breakdown largo | Melodiam — No Way Out — Balkan Connection — 122 BPM — minuto 83 del set |
| 2 | 56.9 | 355 | 355-385s (drop 380) | 55s | 6.3 | kick tras breakdown largo | Hraach, Armen Miran — Menq (Nick Warren & Nicolas Rada Remix) — Hoomidaas — 122 BPM — minuto 56 del set |
| 3 | 66.4 | 353 | 353-383s (drop 378) | 94s | 6.9 | kick tras breakdown largo | Kamilo Sanclemente — Delusion (Original Mix) — Univack — 122 BPM — minuto 66 del set |
| 4 | 33.1 | 234 | 234-264s (drop 254) | 34s | 5.1 | track identitario | Dmitry Molosh — Step by Step feat. Sasha Bartashevich (Original Dub Mix) — Replug — 121 BPM — minuto 33 del set |
| 5 | 44.9 | 258 | 258-288s (drop 283) | 55s | 5.7 | kick tras breakdown largo | Melodiam (AR) — Dizzy (Extended Mix) — Clubsonica Records — 122 BPM — minuto 44 del set |
| 6 | 5.1 | 304 | 304-334s (drop 325) | 37s | 3.8 | entrada de kick | Cendryma — Meridian Isle (Original Mix) — onedotsixtwo — 118 BPM — minuto 5 del set |

<details><summary>Comandos ffmpeg</summary>

```bash
ffmpeg -ss 4986.0 -t 30 -i "grabacion_set86.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_86_1.mp4"
ffmpeg -ss 3414.0 -t 30 -i "grabacion_set86.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_86_2.mp4"
ffmpeg -ss 3984.0 -t 30 -i "grabacion_set86.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_86_3.mp4"
ffmpeg -ss 1986.0 -t 30 -i "grabacion_set86.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_86_4.mp4"
ffmpeg -ss 2694.0 -t 30 -i "grabacion_set86.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_86_5.mp4"
ffmpeg -ss 306.0 -t 30 -i "grabacion_set86.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_86_6.mp4"
```

</details>

## 87. Nick Warren Style — The Soundgarden

18 tracks · ~83 min estimados · 16 de 18 tracks pasaron los filtros

| # | min del set | seg en track | ventana | gap | E | tipo | linea |
|---|---|---|---|---|---|---|---|
| 1 | 57.1 | 287 | 287-317s (drop 312) | 92s | 6.7 | kick tras breakdown largo | Emi Galvan — Never Ending Summer (Original Mix) — Mango Alley — 123 BPM — minuto 57 del set |
| 2 | 66.1 | 287 | 287-317s (drop 312) | 76s | 7.2 | pico del set | Ezequiel Arias — Solar (Extended Mix) — Anjunadeep — 123 BPM — minuto 66 del set |
| 3 | 75.6 | 276 | 276-306s (drop 301) | 59s | 6.5 | kick tras breakdown largo | Nicolas Rada — Cascadia — Sudbeat Music — 122 BPM — minuto 75 del set |
| 4 | 21.7 | 229 | 229-259s (drop 254) | 46s | 4.9 | kick tras breakdown largo | Cendryma — Pure Junction (Berdu Remix) — Transensations Records — 120 BPM — minuto 21 del set |
| 5 | 38.3 | 242 | 242-272s (drop 268) | 47s | 5.6 | kick tras breakdown largo | Maze 28 — Aer8 — Mango Alley — 122 BPM — minuto 38 del set |
| 6 | 45.8 | 201 | 201-231s (drop 220) | 32s | 6.1 | entrada de kick | Tali Muss — Garip (Original Mix) — Heinz Music — 122 BPM — minuto 45 del set |

<details><summary>Comandos ffmpeg</summary>

```bash
ffmpeg -ss 3426.0 -t 30 -i "grabacion_set87.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_87_1.mp4"
ffmpeg -ss 3966.0 -t 30 -i "grabacion_set87.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_87_2.mp4"
ffmpeg -ss 4536.0 -t 30 -i "grabacion_set87.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_87_3.mp4"
ffmpeg -ss 1302.0 -t 30 -i "grabacion_set87.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_87_4.mp4"
ffmpeg -ss 2298.0 -t 30 -i "grabacion_set87.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_87_5.mp4"
ffmpeg -ss 2748.0 -t 30 -i "grabacion_set87.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_87_6.mp4"
```

</details>

## 88. Cordoba Progressive — Gai Barone Style

18 tracks · ~88 min estimados · 18 de 18 tracks pasaron los filtros

| # | min del set | seg en track | ventana | gap | E | tipo | linea |
|---|---|---|---|---|---|---|---|
| 1 | 47.1 | 284 | 284-314s (drop 309) | 87s | 6.1 | kick tras breakdown largo | Dmitry Molosh — Glide — Late Night Music — 121 BPM — minuto 47 del set |
| 2 | 75.3 | 291 | 291-321s (drop 316) | 98s | 7.1 | kick tras breakdown largo | Kamilo Sanclemente — Fragma (GORKIZ Remix) — Transensations Records — 123 BPM — minuto 75 del set |
| 3 | 55.8 | 195 | 195-225s (drop 220) | 79s | 6.6 | kick tras breakdown largo | Guy J — Illusion (Original Mix) — Lost & Found — 122 BPM — minuto 55 del set |
| 4 | 31.3 | 353 | 353-383s (drop 378) | 65s | 5.9 | kick tras breakdown largo | Gai Barone — In the Blink of an Eye (Original Mix) — Stripped Recordings — 122 BPM — minuto 31 del set |
| 5 | 63.3 | 59 | 59-89s (drop 78) | 31s | 6.9 | entrada de kick | Tali Muss — Azal (Original Mix) — Outta Limits — 123 BPM — minuto 63 del set |
| 6 | 11.6 | 288 | 288-318s (drop 302) | 22s | 4.5 | entrada de kick | Tom Pavicich, Gonzalo Cotroneo — Radiance (Original Mix) — onedotsixtwo — 121 BPM — minuto 11 del set |

<details><summary>Comandos ffmpeg</summary>

```bash
ffmpeg -ss 2826.0 -t 30 -i "grabacion_set88.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_88_1.mp4"
ffmpeg -ss 4518.0 -t 30 -i "grabacion_set88.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_88_2.mp4"
ffmpeg -ss 3348.0 -t 30 -i "grabacion_set88.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_88_3.mp4"
ffmpeg -ss 1878.0 -t 30 -i "grabacion_set88.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_88_4.mp4"
ffmpeg -ss 3798.0 -t 30 -i "grabacion_set88.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_88_5.mp4"
ffmpeg -ss 696.0 -t 30 -i "grabacion_set88.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_88_6.mp4"
```

</details>

## 89. Argentina Peak Time

18 tracks · ~83 min estimados · 18 de 18 tracks pasaron los filtros

| # | min del set | seg en track | ventana | gap | E | tipo | linea |
|---|---|---|---|---|---|---|---|
| 1 | 22.7 | 274 | 274-304s (drop 299) | 71s | 5.9 | kick tras breakdown largo | Emi Galvan — Vibration (Original Mix) — Melody Of the Soul — 122 BPM — minuto 22 del set |
| 2 | 62.3 | 194 | 194-224s (drop 218) | 76s | 7.7 | kick tras breakdown largo | Rockka — Cinimatic (Original Mix) — Lamp — 123 BPM — minuto 62 del set |
| 3 | 53.8 | 212 | 212-242s (drop 232) | 34s | 7.3 | track identitario | Hana, Durante, Gorje Hewek — Elysia (Original Mix) — Watergate Records — 126 BPM — minuto 53 del set |
| 4 | 12.8 | 261 | 261-291s (drop 286) | 67s | 5.6 | kick tras breakdown largo | Rauschhaus, Cary Crank — Perihelion (Extended Mix) — Sunexplosion — 121 BPM — minuto 12 del set |
| 5 | 74.7 | 168 | 168-198s (drop 194) | 76s | 7.0 | kick tras breakdown largo | Massano — The Feeling (2022 Remaster) — Afterlife Records — 124 BPM — minuto 74 del set |
| 6 | 41.7 | 43 | 43-73s (drop 61) | 31s | 6.8 | entrada de kick | Ezequiel Arias — Psychodelia (Extended Mix) — Anjunadeep — 125 BPM — minuto 41 del set |

<details><summary>Comandos ffmpeg</summary>

```bash
ffmpeg -ss 1362.0 -t 30 -i "grabacion_set89.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_89_1.mp4"
ffmpeg -ss 3738.0 -t 30 -i "grabacion_set89.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_89_2.mp4"
ffmpeg -ss 3228.0 -t 30 -i "grabacion_set89.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_89_3.mp4"
ffmpeg -ss 768.0 -t 30 -i "grabacion_set89.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_89_4.mp4"
ffmpeg -ss 4482.0 -t 30 -i "grabacion_set89.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_89_5.mp4"
ffmpeg -ss 2502.0 -t 30 -i "grabacion_set89.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:v libx264 -crf 18 -preset slow -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 256k "corte_89_6.mp4"
```

</details>

---

## Tracks descartados (9)

No es un problema de curaduria: son tracks buenos que no tienen un momento vertical. Un breakdown de 8 segundos funciona en una mezcla y no da para un corte.

| Set | Pos | Track | Motivo |
|---|---|---|---|
| 80 | 7 | Kamilo Sanclemente, Sebastian Valencia (COL) — Anomaly (Original Mix) | gap Breakdown->DROP 8s < 15s |
| 81 | 2 | Nicolas Rada — Glasgow (Original Mix) | gap Breakdown->DROP 8s < 15s |
| 85 | 1 | Jamie Stevens, Kasey Taylor — L'alba (Original Mix) | sin cue Breakdown; sin cue DROP |
| 85 | 2 | D-Nox, Stereo Underground — Dolby (Original Mix) | sin cue Breakdown; sin cue DROP |
| 86 | 3 | Andre Moret — Young Movements | gap Breakdown->DROP 14s < 15s |
| 86 | 4 | Melodiam (AR) — Jupiter (Extended Mix) | gap Breakdown->DROP 8s < 15s |
| 86 | 9 | Guy J — My Existence (Original Mix) | gap Breakdown->DROP 14s < 15s |
| 87 | 1 | Alex O'Rion — Blackout (Original Mix) | gap Breakdown->DROP 8s < 15s |
| 87 | 4 | Leandro Murua, Martin Fredes — Mistakes (Original Mix) | gap Breakdown->DROP 14s < 15s |

## Colisiones entre sets

Ninguna. Los 60 cortes salen de 60 tracks distintos.
