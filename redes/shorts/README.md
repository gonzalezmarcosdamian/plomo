# Shorts

Lo que se sube a Instagram y TikTok. Los videos largos NO viven aca: pesan
gigas y no se versionan. Aca queda lo que se publica, que pesa megas.

## De donde sale

Los originales estan en `C:\Users\gonza\Music\plomo\grabaciones\`:

- `video/IMG_XXXX.MOV` — lo que filmo el telefono, 4K 60, varios GB
- `2026-09-23_set_consola_REC001.wav` — lo que grabo la consola, WAV
- `2026-09-23_set_master_*.wav` — los masters

## Como se hace un short

```bash
python scripts/short_rapido.py <video largo> --segundos 20
python scripts/short_rapido.py <video largo> --segundos 20 --horizontal
```

Sale mudo a proposito: la musica se le pone arriba en la app, que ademas es lo
que el algoritmo premia.

## El audio bueno no es el del telefono

La camara graba el ambiente de la sala; la consola graba la mezcla. Para
cualquier pieza con sonido se usa el master de consola, sincronizado por
correlacion de las dos pistas (el audio del telefono sirve de puente y despues
se descarta). En la grabacion del 2026-09-23 el desfase fue de 19.14 s, medido
en tres ventanas distintas que coincidieron dentro de 10 ms.

La primera medicion que hice daba lo mismo pero con una confianza de 0.67 contra
un segundo pico de 0.60: demasiado parecidos para creerle. Un desfase se da por
bueno cuando varias ventanas independientes coinciden, no cuando una sola tiene
el pico mas alto.
