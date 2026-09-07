# Golpes extraidos de la biblioteca

Los `.wav` de estas carpetas los genera `scripts/extraer_golpes.py`. Cada uno es
un fragmento de entre 110 y 350 ms sacado de un track de
`Music/Biblioteca/` — kick, hat, hat abierto o clap.

## Material con derechos — leer antes de usar

**Esto son pedazos de grabaciones comerciales ajenas.** No son samples propios y
no son samples con licencia.

Lo que si:

- escuchar una maqueta en esta maquina antes de elegir sonidos
- usarlos como referencia de timbre: comparar un kick propio contra el de
  Vasami y ver en que se diferencian, medido
- entender que sonido elige Gonzalo cuando elige un track

Lo que no:

- publicar, distribuir o subir un track que los contenga
- mandarlos a un sello, a un demo o a una plataforma
- tratarlos como una libreria de samples

La carpeta esta en `.gitignore` completa, .wav e indice, justamente por esto.
Cuando el boceto deje de ser un boceto, el golpe se reemplaza por uno propio o
por uno de una libreria con licencia. Esa decision la toma una persona, no el
script.

## De donde sale cada golpe

Cada carpeta tiene un `PROCEDENCIA.json` con el track fuente, el segundo exacto
del que se recorto cada golpe y las metricas de separacion. Sin eso el material
no es rastreable y no se puede volver atras.

Las fuentes no se eligen al azar: por defecto salen de
`data/plantillas/lista_lo_tocado_meta.json`, ordenadas por veces reproducido. El
kick de un track que se toca diez veces es, literalmente, el sonido que se
elige.

## Que tan limpio sale — y que no

Aislar un kick de una mezcla terminada es imposible en sentido estricto. El
script busca el golpe menos contaminado de todo el track, que casi siempre cae
en la intro o el outro, donde el kick esta solo. Lo que queda se mide y se
reporta:

- **`bleed_db`** — energia arriba de 300 Hz pasados los primeros 80 ms,
  relativa al pico del golpe. Es cuanta basura ajena quedo en la cola. Se
  considera limpio en -15 dB o menos.
- **`bleed_db_crudo`** — lo mismo antes de limpiar, para ver cuanto hizo el
  proceso y cuanto ya venia bien.
- **`sub_pct`** — porcentaje de energia en 20-120 Hz. Un kick de progressive da
  arriba de 90.
- **`centroide_hz`** — donde esta el centro de gravedad del timbre. Es el
  control de que la clase sea lo que dice: sin el, el detector de clap agarraba
  hats y los guardaba como clap.

Los golpes marcados con `!` en el reporte **no pasan el umbral**. Sirven para
escuchar la forma; no son un sonido.

### Lo que no funciona bien

`hat_abierto` es la clase que falla. Un hat abierto dura 300 ms y en ese tiempo
se le encima todo lo demas: en la mitad de los tracks medidos no baja de -15 dB.
Es esperable y no tiene arreglo por esta via — un golpe largo en una mezcla
densa no se aisla midiendo. El kick, el hat cerrado y el clap si dan material
utilizable.

## Uso

```bash
# extrae de los 6 tracks mas tocados
python scripts/extraer_golpes.py --top 6

# solo de un artista
python scripts/extraer_golpes.py --artista vasami

# renderiza un boceto con esos golpes en vez de sintetizarlos
python scripts/render_sketch.py postproduction/bocetos/<nombre> \
    --samples data/samples/<carpeta> --plantilla data/plantillas/lo_tocado.json
```

Sin `--samples`, `render_sketch.py` sintetiza todo como siempre. Los samples son
opcionales por diseno: el boceto tiene que seguir funcionando en una maquina que
no tenga esta carpeta.
