# Grabaciones

Lo que se grabó tocando. **Está en el repo pero no en git**: son 8 GB de video 4K
y audio WAV, y un repo con eso adentro se vuelve inmanejable. Lo que sí se
versiona es lo que se publica, que vive en `redes/shorts/` y pesa megas.

## 2026-09-23

| archivo | qué es |
|---|---|
| `2026-09-23_set_consola_REC001.wav` | lo que grabó la consola. 26:16, WAV 44.1/16. El original, intacto |
| `2026-09-23_set_master_streaming.wav` | −14 LUFS, −1 dBTP. Para Instagram, TikTok y YouTube, que normalizan a ese nivel |
| `2026-09-23_set_master_club.wav` | −9 LUFS, −1 dBTP. Para escuchar y para SoundCloud |
| `2026-09-23_set_master_streaming.mp3` | 320k, para mandar por mensaje |
| `video/IMG_1688.MOV` | lo que filmó el teléfono. 25:49, 4K 60, 6.2 GB |
| `video/IMG_168{6,7,9}.MOV` | clips cortos de la misma noche |
| `20s_vertical_IG.mp4` | el short mudo, 1080x1920 |
| `20s_horizontal_IG.mp4` | el mismo en 16:9 |

## Qué se le hizo al audio, y qué no

**Se corrigió solo loudness y true peak.** La grabación venía a −9.2 LUFS con
picos a **+1.41 dBTP**, o sea clippeando, aunque el daño real era chico: 1.800
muestras al tope sobre 69 millones, que son intersample peaks y no clipping
sostenido.

**No se tocó el tono**: ni EQ, ni compresión, ni estéreo. Eso necesita oído y una
referencia, y la decisión es del DJ. Un master "mejorado" a ciegas es una opinión
disfrazada de proceso.

## El audio y el video no arrancan juntos

La consola empezó **19.14 s antes** que el teléfono. El desfase se mide por
correlación de las envolventes de onsets, usando el audio del teléfono como
puente, y después esa pista se descarta: la cámara graba el ambiente de la sala,
la consola graba la mezcla.

Ese número se dio por bueno recién cuando **tres ventanas distintas del set
coincidieron dentro de 10 ms**. La primera medición, sobre el set entero, daba lo
mismo pero con una confianza de 0.67 contra un segundo pico de 0.60 — demasiado
parecidos para creerle. Un desfase se confirma por coincidencia entre ventanas
independientes, no porque un pico sea el más alto.
