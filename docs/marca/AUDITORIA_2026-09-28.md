# Auditoría de marca — Marcos Damian, 2026-09-28

Estado leído alrededor de las 14:00: API de YouTube en solo lectura (`channels`,
`videos`, `playlists`, `channelSections`, `playlistItems`, todos `.list()`), el
sitio en vivo, la página pública del canal y los archivos locales. No se aplicó
nada. Ya tiene en cuenta la regla nueva: **la marca no se ata a un género; los
videos sí pueden nombrarlo.**

## Veredicto

La identidad visual está resuelta y es coherente: el mismo cielo, la misma letra
y los mismos dos colores en el banner, la foto, la web, la imagen para compartir
y la miniatura. Si alguien llega a una, reconoce la otra enseguida. Lo que falla
es lo que rodea a la marca: el canal muestra playlists de programación, la web
lleva a un video privado, y la dirección de la web dice "plomo" y "gonzalez",
justo las dos cosas que la marca decidió no mostrar.

## Lo que está bien (no tocar)

- **El nombre es el mismo en todos lados**: banner, web, título del canal y
  handle. El nombre y el handle ya están aplicados en Studio: la API devuelve
  "Marcos Damian" y `@marcosdamianmusic`.
- **El banner en vivo ya no tiene género**, y el nombre entra en la zona segura
  del celular.
- **La descripción del canal, "Jugando"**, la escribió él en Studio. No se toca, y
  cumple la regla de no cerrarse a un estilo.
- **La descripción del video** es lo que él dictó. El título pone adelante los
  cuatro nombres, que es la búsqueda que un canal nuevo puede ganar. El género
  en el título describe ese set, no a él.
- **La miniatura** usa la misma letra y los mismos colores que el banner, y se lee
  a 120 px.

## Hallazgos por prioridad

### 1. El canal muestra tres playlists públicas de otra época (él, en Studio)

**Qué pasa.** El canal tiene 0 videos públicos, así que la única pestaña con
contenido es Playlists, y ahí aparecen "react", "Taildwind" y "topografía".
Verificado en la página pública del canal.

**Por qué importa.** Es lo primero que va a ver alguien que llegue desde la web o
desde el set. En una escena que se fija en quién es quién, un canal de DJ con
tutoriales de programación parece una cuenta reciclada antes de que suene la
música. Además, YouTube usa las playlists públicas para entender de qué es el
canal.

**Cambio.** En Studio > Contenido > Playlists, pasar a Privada (o borrar):

| Playlist | ID |
|---|---|
| react | `PLHOVnbTScyeqr1i3cqGQGfasXDJQcJ9He` |
| Taildwind | `PLHOVnbTScyeoejppRYVkjNuSSc_nQqh1y` |
| topografía | `PLHOVnbTScyeq_kg2zgR99JkGrqnN8mkb_` |

Las otras cuatro (Selenium, terra, Trading, power bi) ya son privadas. Por API
sería `playlists.update`, pero es una escritura: la decide él.

### 2. La web es pública y su único contenido lleva a un video privado (web: vos)

**Qué pasa.** `plomo.marcosdamiangonzalez.ar` responde 200 y "Último set" apunta
a `youtu.be/cxPG09u-edM`, que sigue privado. El clic termina en "Video privado".
Además, la versión en vivo todavía dice PROGRESSIVE HOUSE: el cambio sin género
está en local y falta desplegarlo.

**Por qué importa.** Es el link que él va a pasar. Si el primer clic termina en un
video privado, el que entró no tiene a dónde seguir.

**Cambio.**
- Si publica hoy o mañana: desplegar la versión local en el mismo momento en que
  el video pasa a público, no antes.
- Si el video sigue privado varios días más: desplegar sin la sección "Último
  set" (el `<section>` de las líneas 24-36 de `web/plomo/index.html`) y volver a
  ponerla el día que se publique.

### 3. La dirección de la web dice "plomo" y "gonzalez" (decide él; lo ejecutan vos y el coordinador)

**Qué pasa.** La página de artista vive en un subdominio de
`marcosdamiangonzalez.ar`, que es su portfolio de Product Manager ("Product
Manager · Inversiones & Banca Digital"). En /privacidad, "Contacto" lleva a ese
portfolio.

**Por qué importa.** El nombre artístico se eligió sin "Gonzalez". Pero la URL,
que es lo único que se ve cuando se comparte el link, trae el apellido y el
nombre de la herramienta. Y el link de contacto lleva a su perfil laboral. Si
quiere esos dos mundos juntos o separados lo decide él (**confirmar con él**),
pero hoy están juntos sin que nadie lo haya decidido.

**Cambio propuesto: separar sin tocar nada en Google.**
- La web de artista pasa a un dominio propio. Según RDAP (NIC.ar y Verisign), hoy
  no están registrados `marcosdamianmusic.com`, `marcosdamian.ar`,
  `marcosdamian.com.ar`, `marcosdamianmusic.ar` ni `marcosdamian.com`: dieron
  404, y los dominios de control dieron 200. Recomiendo **marcosdamianmusic.com**,
  porque es idéntico al handle: el mismo texto sirve para YouTube, la web y, si
  existe, Instagram. `marcosdamian.ar` puede quedar como redirección. Se agrega
  como dominio del proyecto de Vercel `plomo-web`.
- `plomo.marcosdamiangonzalez.ar` queda como la página de la herramienta: inicio
  con el texto de Plomo, más /privacidad y /terminos. Es la URL que ya está
  cargada en la consola de Google, así que allá no cambia nada.
- Así, la web de artista no necesita nombrar a Plomo en ningún lado.

### 4. El pie de la web explica la técnica (web: vos)

**Qué pasa.** El pie dice: "Los sets se publican con Plomo, una herramienta
propia que usa la API de YouTube."

**Por qué importa.** Choca con dos reglas del proyecto. La de voz: nada de
explicar la técnica. Y la de `docs/YOUTUBE_SERIE.md`: "no postear el código ni el
pipeline: trae developers, no fechas, e instala que la máquina elige por vos".
Para alguien del palo, "una herramienta propia que publica los sets" suena a que
los sets los arma una máquina.

**Cambio** (mientras no se haga el 3; si se hace, esto sobra):
- `web/plomo/index.html`, líneas 43-47, reemplazar por:
  ```html
  <nav>
    <a href="/plomo">Plomo</a>
    <a href="/privacidad">Privacidad</a>
    <a href="/terminos">Condiciones</a>
  </nav>
  ```
- Una página nueva, `web/plomo/plomo.html`, con este texto y los links a
  privacidad y condiciones: "Plomo es una herramienta personal de Marcos Damián
  González para subir sus sets a su propio canal de YouTube. Usa la API de
  YouTube con su permiso y no tiene otros usuarios."
- En la consola de Google, a mano: cambiar "Página principal de la aplicación" a
  `https://plomo.marcosdamiangonzalez.ar/plomo`. **No lo probé**: hay que
  confirmar en la consola que acepte una subruta del dominio autorizado.

### 5. En el celular, la web no usa la letra de la marca (web: vos)

**Qué pasa.** `.portada h1` pide Bahnschrift, y si no está, DIN Condensed o Arial
Narrow. Bahnschrift viene con Windows; Android y iPhone no la traen. En iPhone
cae en DIN Condensed, que se parece. En Android no está ninguna de las tres y
cae en la letra del sistema, que es otra y más ancha. Las capturas
`web2_*.png` se sacaron en Windows, por eso no se nota.

**Por qué importa.** Lo más probable es que la gente llegue por un link desde el
celular. El banner, la imagen para compartir y la miniatura están dibujados en
Bahnschrift. La portada de la web solo dice el nombre, y si en Android sale en
otra letra, el nombre no se ve igual que en el banner. Es justo la pieza que une
la web con el canal.

**Cambio.** Bahnschrift no se puede usar como fuente web porque es una fuente de
Windows. La alternativa es servir Barlow Condensed 700 (licencia SIL OFL, la más
parecida a DIN y Bahnschrift) desde
`web/plomo/fuentes/barlow-condensed-700.woff2`, como segunda opción:
```css
@font-face { font-family: "Barlow Condensed"; src: url("/fuentes/barlow-condensed-700.woff2") format("woff2"); font-weight: 700; font-display: swap; }
.portada h1 { font-family: "Bahnschrift", "Barlow Condensed", "DIN Condensed", sans-serif; }
```
Antes de desplegar, verificarlo con una captura sin Bahnschrift o en un Android.
Aprovechando el cambio: los `h2` ("Último set", "Escuchar") en la misma letra,
en mayúsculas y espaciados, repiten el "AT HOME" naranja de la miniatura que
está justo abajo.

### 6. La vista real desde la casa ya está publicada en la web (decide él)

**Qué pasa.** El paquete del video dejó una pregunta abierta: los edificios que
se ven por la ventana son reconocibles para quien conozca la zona, "decidir si
importa". La web ya muestra esa miniatura (`img/sunset-23-09.jpg`) en un sitio
público, antes de que él lo decidiera.

**Por qué importa.** De todo lo que hay en esta lista, es lo único que no se
puede deshacer del todo: una vez que un buscador indexa la imagen, queda en
buscadores y archivos. **Confirmar con él hoy.**

**Cambio si le importa.** En la web, reemplazar la imagen por un cuadro de la
animación sola, y pedirle al agente `video` una miniatura sin la ventana antes
de publicar. Las dos variantes que hay (`thumb_a`, `thumb_b`) la muestran. Si no
le importa, se deja: la ventana es lo que hace honesta a la miniatura.

### 7. Las palabras clave del canal lo cierran a un estilo (vos: `canal.json` + `youtube_canal.py`)

**Qué pasa.** El canal todavía tiene como palabras clave "Marcos Damian",
"progressive house", "melodic progressive", "organic house", "dj set" y
"sunset mix".

**Por qué importa.** Rompe la regla nueva: son etiquetas del canal, no de un
video. Pesan poco en las búsquedas, así que sacarlas casi no cuesta nada. El
género sigue en los tags de cada video, donde describe ese set.

**Cambio** en `data/youtube/canal.json`:
```json
"palabras_clave": ["Marcos Damian", "Marcos Damian DJ", "marcosdamianmusic", "dj set", "dj mix"]
```
Ojo: `youtube_canal.py` manda todos los campos juntos, incluida la descripción.
Tiene que mandar "Jugando", que es lo que ya dice `canal.json`.

### 8. La marca de agua no se distingue y parece un error (vos la preparás, él la aprueba)

**Qué pasa.** `marca_de_agua.png` es un cuadrado de 150x150 del mismo cielo,
opaco (alfa 255 en todo el archivo). Encima del video, que es ese mismo cielo,
parece un recuadro pegado en la esquina y no una firma (ver
`scratchpad/redes_marca_sobre_video.png`). La API no deja leer si quedó
aplicada; se ve en Studio > Personalización > Marca.

**Por qué importa.** La marca de agua funciona como botón de suscripción durante
todo el video. Así como está, no dice de quién es el canal.

**Cambio.** Un PNG transparente de un solo color (crema `#f3ebdd`) con el nombre
en Bahnschrift Bold Condensed en dos renglones (MARCOS / DAMIAN), o un
monograma. **Confirmar con él**: el monograma no está decidido. Si no quiere
ninguno, es mejor sacarla (`watermarks.unset`) que dejar el cuadrado.

### 9. En tamaño chico, la foto del canal no identifica a nadie (él, en Studio)

**Qué pasa.** La foto es el horizonte recortado. A 88 px se lee como un
atardecer. A 24-48 px, que es como se ve en búsquedas, comentarios y sugeridos,
es una raya naranja sobre negro (ver `scratchpad/redes_avatar_tamanos.png`).
Además es el mismo fondo del banner, del video y de la miniatura.

**Por qué importa.** La foto acompaña cada video en las búsquedas y cada
comentario que él deje en los videos de los sellos, que en un nicho chico es la
manera más directa de hacerse ver. Ahí se tiene que reconocer una persona o un
nombre, no un color.

**Cambio** (**confirmar con él**, es su cara): o una foto real suya a contraluz
de esa ventana a la misma hora, que mantiene el horizonte y la escala honesta
que ya eligió la miniatura, o el horizonte con el monograma del punto 8 encima.
La foto la sube él a mano.

### 10. Detalles de coherencia de la web (web: vos)

- "Escuchar → YouTube" apunta a `/channel/UC3KtrwntSd1ZN0zOusx0ntQ`. Ahora que
  existe el handle, conviene `https://www.youtube.com/@marcosdamianmusic`: es la
  dirección que la gente recuerda y la que se ve al pasar el mouse.
- El tracklist de la web no tiene los sellos y el de YouTube sí. En este palo el
  sello es parte del nombre del tema: agregarlos en gris, igual que en la
  descripción (tornn, The Soundgarden, Consapevole Recordings, Balance Music).
- En `web/plomo/estilo.css`, la regla `.portada .genero` ya no se usa. Sacarla,
  así nadie la vuelve a llenar.

## Antes de publicar el video

1. **Pasar a privadas las playlists viejas** (punto 1). Si no, la primera visita
   no entra al canal de un DJ.
2. **Desplegar la web sin género** en el mismo momento en que el video pasa a
   público (punto 2).
3. **Content ID**: mirar "Comprobaciones" en Studio. Ya está en el paquete.
4. **Vínculos del canal** (a mano: Studio > Personalización > Información básica
   > Vínculos): agregar la web. Hoy no hay ninguno, y es el único camino del
   canal a la web.
5. **Playlist pública "Sets"** con el video adentro, sin género en el nombre. Con
   un solo video no suma mucho al canal, pero le da a la web un link que no
   envejece: si "Escuchar" apunta a la playlist, no hay que editar la web con
   cada set nuevo.
6. **Secciones del canal**: con un solo video no hacen falta, la portada lo
   muestra sola. En Studio > Personalización > Diseño, poner el set como video
   destacado para quienes no están suscriptos. Desde el segundo set, agregar una
   sección con la playlist "Sets".
7. **Shorts**: en los tres cortes del paquete, el cartel con el nombre del tema
   queda entre el 81% y el 90% del alto, tapado por la interfaz de Shorts. Hay
   que subirlo al 60-65% antes de renderizar. El orden: el largo pasa a público
   y ese mismo día sale el corte 1 (Wait for Me, 4:49.4) con "Video relacionado"
   apuntando al largo. Después In Space y Mindloop, uno por semana. Con el canal
   en cero, un corte que salga antes que el largo no tiene a dónde mandar a
   nadie.
8. **Registro**: el día que se publique, cargar la entrada en
   `data/publicaciones.json` (plataforma `youtube_largo`, métricas en null hasta
   el día 7). El esquema pide `set_origen` como número de set, y este es un set
   suelto sin número: usar null y `set_nombre` "Atardecer 2026-09-23".

## Preguntas para él

- **¿Tiene Instagram para esto?** En la bitácora del 24 se prepararon 20 s del
  atardecer "para ponerle música en Instagram", pero en el repo no figura ninguna
  cuenta. `@marcosdamian` ya es de otra persona (Marcos Caceres).
  `@marcosdamianmusic` parece libre, aunque Instagram no lo confirma sin iniciar
  sesión. Si abre una, que sea ese: el mismo handle que en YouTube.
- **¿Quiere un contacto para fechas en la web?** Es lo único que la web puede
  ofrecer y el canal no. ¿Con qué mail?
- **¿Dominio propio (punto 3)?** ¿Cuál?
- **¿Le importa que se vea la vista desde su casa (punto 6)?**
- **¿Foto suya o monograma (puntos 8 y 9)?**
- La descripción de la web para buscadores y WhatsApp dice "DJ sets.", y la del
  canal dice "Jugando". Las dos cumplen la regla. **¿Quiere que la web también
  diga "Jugando"?**
