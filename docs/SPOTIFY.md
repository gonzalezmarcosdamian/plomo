# Publicar los sets en Spotify

Cómo llevar un set de Rekordbox a una lista de Spotify, en orden, y mantenerla
al día en cada iteración. Escrito el 2026-09-23, después de hacerlo funcionar.

## Para qué sirve

El set vive en Rekordbox, que es donde se toca. La lista de Spotify es para
**escucharlo en el auto, en el teléfono, en cualquier lado**, y para mandárselo
a alguien. No reemplaza al set: lo refleja.

Por eso la regla es que la lista diga exactamente lo que dice el set. Si un tema
no está en Spotify **no se reemplaza** por el radio edit ni por otro remix: una
lista con otra versión suena distinto de lo que se va a tocar, y entonces sirve
para chequear nada.

## Los tres comandos

```bash
python scripts/spotify_auth.py                       # una sola vez en la vida
python scripts/spotify_sync.py 143                   # una lista
python scripts/spotify_sync.py 139 140 141 142 143 144 145
```

El sync **no crea una lista nueva cada vez**: la busca por nombre y reemplaza su
contenido. Conserva la URL, la carpeta donde esté y la portada. Cada iteración
de un set es otro `spotify_sync.py NNN`.

## El permiso, una sola vez

`spotify_auth.py` abre el navegador, levanta un servidor local en el redirect y
recibe el código cuando el DJ acepta. Nadie copia y pega un token. Queda un
refresh token en `data/spotify_token.json`, fuera de git.

Pide todos los scopes de usuario, no solo los de playlist: la idea es autorizar
una vez y no frenarse cuando haga falta algo nuevo.

**Dos cosas que hay que tener bien en el dashboard de Spotify**
(https://developer.spotify.com/dashboard → la app → Settings):

1. El Redirect URI tiene que ser **`http://127.0.0.1:8888/callback`**. Desde
   2025 Spotify rechaza `localhost` en los redirect de loopback y pide la IP. El
   error que devuelve es `redirect_uri: Not matching configured`, que suena a
   otra cosa.
2. La cuenta de escucha tiene que estar en **User Management** si la app está en
   modo desarrollo y la cuenta de desarrollador es distinta.

## Los endpoints: los viejos dan 403

Esto costó una tarde y es lo más importante de esta página.

| lo que NO anda | lo que SÍ anda |
|---|---|
| `POST /users/{id}/playlists` → 403 | `POST /me/playlists` → 201 |
| `POST /playlists/{id}/tracks` → 403 | `POST /playlists/{id}/items` → 201 |
| `PUT /playlists/{id}/tracks` → 403 | `PUT /playlists/{id}/items` → 200 |
| `GET /playlists/{id}/tracks` → 403 | `GET /playlists/{id}/items` → 200 |

Los de la izquierda están deprecados. Spotify **no** devuelve 404 ni un mensaje
que lo diga: devuelve `403 Forbidden` con el cuerpo vacío, que se lee como un
problema de permisos y manda a revisar scopes, cuenta, modo desarrollo y
Extended Quota Mode. Ver `docs/APRENDIZAJES.md`, "Un 403 sin cuerpo puede ser un
endpoint viejo, no un permiso".

## Cómo encuentra cada tema

La biblioteca tiene Extended Mixes de sellos chicos; Spotify los publica con
otro nombre. El matcheo prueba en orden:

1. `artist:"X" track:"Y"` con el título limpio de `(Extended Mix)` y parecidos
2. el título más el remixer, que es lo que distingue dos versiones del mismo tema
3. título y artista sueltos

Puntúa cada candidato por parecido de título (60%) y de artista (40%), y no
acepta nada por debajo de 0.62. El título se compara **con y sin** el sufijo:
Spotify publica "Juri" y la biblioteca lo tiene como "Juri (Original Mix)", y
comparar solo la forma larga daba 0.47 y lo dejaba afuera.

Resultado sobre los siete sets del cumple: **119 de 119**. Los matches quedan
cacheados en `data/spotify_matches.json`, así que la segunda corrida es
instantánea.

## Lo que el conector de claude.ai puede y no puede

El conector de Spotify tiene cinco herramientas: generar una lista desde una
descripción, buscar, guardar y sacar de la biblioteca, y ver qué está sonando.

- **Sí** respeta una lista de temas nombrados: pedidos cinco, puso los cinco, y
  eligió bien las versiones.
- **No** respeta el orden. Devolvió siempre el mismo, distinto del pedido.
- Con 17 temas y un pedido largo y numerado, creó la lista **vacía**.

Para un set el orden es la mitad del trabajo, así que las listas las hace el
script. El conector queda para buscar y para descubrir.

## Si algo falla

- `falta el permiso de usuario` → correr `spotify_auth.py`.
- `redirect_uri: Not matching configured` → el redirect del dashboard no es
  `http://127.0.0.1:8888/callback`.
- Un 403 nuevo → probar la versión `/items` del endpoint antes de tocar nada más.
- Un tema que dice "no está en Spotify" → buscarlo a mano antes de creerlo; dos
  bugs del matcheo se comieron el 15% de los temas al principio, los dos por
  tratar el sufijo del título como si fuera información.
