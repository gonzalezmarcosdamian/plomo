---
name: vistas
description: Regenera el arbol de carpetas navegable de la biblioteca - por rol de set, energia, genero, key, BPM y sello. Usar despues de importar musica, de un backfill de energia, o cuando se quiera cambiar como se ve la coleccion.
---

# Vistas de la biblioteca

Lo ejecuta el agente `archivista`.

## La idea

El disco guarda; no organiza. Los archivos viven en su carpeta por fecha de
ingreso y no se mueven — asi ningun path de Rekordbox se rompe. La organizacion
vive en `C:\Users\gonza\Music\Vistas`, un arbol de hardlinks que se borra y se
regenera entero sin consecuencias.

Un hardlink no copia el archivo: apunta al mismo dato en disco. 10.123 enlaces
sobre 1816 tracks ocupan cero bytes extra, y un track que aparece en seis vistas
sigue siendo un solo archivo.

Vive fuera de OneDrive a proposito: OneDrive convierte archivos en placeholders
en la nube y trata mal los hardlinks.

## Regenerar

```bash
./.venv/Scripts/python.exe scripts/build_views.py --dry     # que haria
./.venv/Scripts/python.exe scripts/build_views.py --m3u     # regenerar
./.venv/Scripts/python.exe scripts/build_views.py --solo rol energia
```

Vistas actuales: `rol`, `energia`, `genero`, `key`, `bpm`, `sello`.

Cada archivo queda nombrado `E5.7 122 8A - Artista - Titulo.mp3`, asi el orden
alfabetico de la carpeta ya dice algo.

## Cambiar las vistas

Se agregan en el diccionario `VISTAS` de `scripts/build_views.py`: una entrada
con el nombre de la carpeta y una funcion que, dado un track, devuelve el grupo
al que pertenece o `None` si no entra. Los cortes de rol estan en la constante
`ROLES`.

Cambiar de opinion sobre como ver la coleccion cuesta una funcion de tres lineas
y una corrida. Ese es el punto de todo el diseño.

## Cuando regenerar

Despues de importar musica, despues de un `backfill_energy.py`, y despues de
cualquier mudanza de archivos. Las vistas no se actualizan solas.

## Si falla

El script cae solo de hardlink a symlink, y si ninguno funciona lo dice. En ese
caso `--m3u` genera playlists `.m3u8` por grupo, que funcionan siempre y
Rekordbox lee igual.
