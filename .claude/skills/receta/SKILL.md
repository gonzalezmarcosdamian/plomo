---
name: receta
description: Ingenieria inversa de un track de referencia - estructura por compases, curva de energia, balance espectral, ancho estereo y LUFS. Usar para entender por que un track suena como suena o para comparar lo propio contra una referencia.
---

# Receta de un track

Lo ejecuta el agente `productor`.

## Correr

```bash
./.venv/Scripts/python.exe scripts/reverse_engineer.py "C:\ruta\track.mp3"
./.venv/Scripts/python.exe scripts/reverse_engineer.py ref.mp3 --contra propio.mp3
./.venv/Scripts/python.exe scripts/reverse_engineer.py track.mp3 --json data/recetas/nombre.json
```

Las rutas van en formato Windows (`C:\...`), no estilo Unix.

Tarda unos 15 segundos por track de 7 minutos.

## Que devuelve, y que significa

- **Estructura por compases** — secciones detectadas por presencia de kick, con
  su largo en compases y en segundos. Un breakdown de 23 compases a los 3:48 es
  una decision de arreglo, no un accidente.
- **Curva de energia** — RMS por compas, dibujada como sparkline. Es la forma del
  track vista como se ve la forma de un set.
- **Balance espectral** — reparto de energia entre sub (20-60), bajo (60-250),
  medio (250-2000) y aire (2000+). Ponderado por potencia, asi que los graves
  siempre dominan el porcentaje: **sirve para comparar tracks entre si**, no como
  numero absoluto.
- **Ancho estereo por banda** — correlacion L/R. 1.00 es mono. El sub tiene que
  estar cerca de 1.00; si no, se cancela en un sistema grande y el script lo avisa.
- **LUFS y rango dinamico** — cuanto esta comprimido.
- **Densidad de eventos** — onsets por compas por seccion: cuanto pasa en cada parte.

## Como se lee

Un numero solo no dice nada. La receta se lee en contraste: analizar al menos dos
referencias del mismo registro antes de concluir, y usar `--contra` para poner lo
propio al lado.

Los registros estan en `docs/MI_SONIDO.md`: oscuro/hipnotico, oscuro con alma,
meseta bailable, constructor, emotivo, heroico, peak firme, cierre romantico. La
pregunta util es "que distingue medible a un heroico de un peak firme", no "que
LUFS tiene este track".

## Limites que hay que declarar

Mide senal, no intencion: no detecta acordes, no identifica instrumentos y no
dice como se hizo un sonido. La segmentacion es heuristica sobre presencia de
kick — en material sin kick claro (organic, downtempo, ambient) el propio script
avisa que no es confiable, y ese aviso se reporta en vez de tapar.

## Referencia medida

`Simon Vuarambon & Tantum - Zenith` (Bedrock): 6.8 min, 120.2 BPM, 201 compases.
-9.5 LUFS, rango 6.9 dB. Sub y bajo se llevan el 95% de la potencia, sub en mono
perfecto (1.00), medio y aire abiertos (0.50 / 0.44). Estructura: 113 compases de
groove, breakdown de 23 al 56% del track, drop de 61, outro de 4.
