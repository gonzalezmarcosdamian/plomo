# Paquetes de publicacion — serie "Sonido Argentino"

Un archivo por video con titulo, descripcion, tracklist con timestamps, tags,
concepto de portada y seis momentos para shorts. Nada de esto esta publicado:
los sets todavia no se grabaron y subir lo decide Gonzalo.

Timestamps calculados con blend fijo de 3:00 sobre las duraciones
reales de `data/pool.json`. Hay que verificarlos contra el audio despues de grabar.

| # | Set | Titulo | Duracion proyectada | Tracks | Estado | Archivo |
|---|-----|--------|---------------------|--------|--------|---------|
| 01 | 80 | Hernan Cattaneo Style \| Progressive Argentino | 1:28:51 | 18 | listo para grabar | [set_80.md](set_80.md) |
| 02 | 81 | Ezequiel Arias Style \| Peak Vocal | 1:22:04 | 18 | listo para grabar | [set_81.md](set_81.md) |
| 03 | 82 | Emi Galvan Style \| Progresivo Colorido | 1:29:06 | 18 | listo para grabar | [set_82.md](set_82.md) |
| 04 | 83 | Kamilo Sanclemente Style \| Colombia Progresiva | 1:27:09 | 18 | listo para grabar | [set_83.md](set_83.md) |
| 05 | 84 | Sudbeat Sessions \| Driving Progressive | 1:25:26 | 18 | listo para grabar | [set_84.md](set_84.md) |
| 06 | 85 | Mango Alley \| Deep Progressive | 1:18:48 | 18 | listo para grabar | [set_85.md](set_85.md) |
| 07 | 86 | Simon Vuarambon Style \| Hipnotico | 1:31:03 | 18 | listo para grabar | [set_86.md](set_86.md) |
| 08 | 87 | Nick Warren Style \| The Soundgarden | 1:23:22 | 18 | listo para grabar | [set_87.md](set_87.md) |
| 09 | 88 | Cordoba Progressive \| Gai Barone Style | 1:27:53 | 18 | listo para grabar | [set_88.md](set_88.md) |
| 10 | 89 | Argentina Peak Time \| Melodic Progressive | 1:23:24 | 18 | listo para grabar | [set_89.md](set_89.md) |
| 11 | 96 | Anjunadeep Style \| Luminoso | — | — | pendiente — el set todavia no existe | — |

Rango de duraciones: **1:18:48 a 1:31:03**, promedio 1:25:43.

## Como se regenera

```
python data/youtube/_generar_paquetes.py        # los diez
python data/youtube/_generar_paquetes.py 96     # el video 11, cuando el set exista
```

El texto editorial (titulo, descripcion, portada, nicho) vive en `_editorial.json`;
todo lo demas sale de Rekordbox y de `data/pool.json` y no se escribe a mano.
El script abre master.db en modo solo lectura.

## Orden de publicacion

Un video cada dos semanas, un short por semana entre medio. El 01 y el 10 son los
dos extremos de la serie: el primero define el tono, el ultimo da adonde ir despues.
