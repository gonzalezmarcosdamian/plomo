# plomo 🎧

Automation toolkit para Rekordbox 6. Importa música nueva, aplica cues automáticos con análisis de audio, calcula energy scores y mantiene playlists ordenadas por Camelot + energía.

## Qué hace

- **Cues automáticos (v8)**: detecta first beat, bass in, breakdown, drop, outro y escribe 11 markers en Rekordbox
- **Energy score (0-10)**: calcula la energía de cada track desde los timings de cues (intro length, breakdown duration, drop presence)
- **Orden Camelot**: ordena sets minimizando saltos armónicos entre tracks
- **Pipeline completo**: mueve archivos de Downloads → Music, Rekordbox importa, luego aplica todo lo anterior
- **Export al pen**: fija DeliveryControl y copia ANLZ para que los tracks exporten al USB sin error

## Setup

```bash
# 1. Clonar
git clone https://github.com/gonzalezmarcosdamian/plomo.git
cd plomo

# 2. Entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 3. Dependencias
pip install -r requirements.txt
pip install -e .

# 4. Configuración
cp .env.example .env
# Editar .env con tus paths
```

## Configuración (.env)

```env
# Path a tu master.db de Rekordbox 6
REKORDBOX_DB_PATH=C:\Users\TU_USUARIO\AppData\Roaming\Pioneer\rekordbox\master.db

# Clave SQLCipher — igual para todas las instalaciones de Rekordbox 6
SQLCIPHER_KEY=402fd482c38817c35ffa8ffb8c7d93143b749e7d315df7a81732a1ff43608497

# Carpeta raíz de tu música
MUSIC_LIBRARY_ROOT=C:\Users\TU_USUARIO\Music

# Destino para música nueva (se crea con YYYY-MM automáticamente)
MUSIC_NEW_FOLDER=C:\Users\TU_USUARIO\Music\2026\Nuevos\2026-05

# Carpeta de descargas
DOWNLOADS_FOLDER=C:\Users\TU_USUARIO\Downloads

# Backups de la DB
BACKUP_FOLDER=C:\Users\TU_USUARIO\Music\plomo\outputs
```

## Flujo de uso

### Cada vez que descargás música nueva

```
1. Descargar tracks a la carpeta Downloads
2. Cerrar Rekordbox  →  System Tray → Quit (no la X)
3. python scripts/import_all.py        ← mueve archivos + prepara metadata
4. Abrir Rekordbox  →  detecta los nuevos, los analiza (BPM + key + waveform)
5. Cerrar Rekordbox  →  System Tray → Quit
6. python scripts/post_import.py       ← cues v8 + energy score + playlists
7. Abrir Rekordbox  →  Sync al pen USB
```

> ⚠️ **Importante:** Rekordbox debe importar los tracks él mismo en el paso 4 (File → Import → Add Folder, o tener la carpeta monitoreada). No importar via pyrekordbox directamente — genera IDs inválidos que bloquean el export USB con error [2].

### Scripts

| Script | Descripción |
|--------|-------------|
| `scripts/import_all.py` | Mueve archivos de Downloads → Music, fix metadata |
| `scripts/post_import.py` | Cues v8, energy score, restaura/asigna playlists |
| `scripts/reorder_sets_energy.py` | Reordena sets por Camelot + energía |
| `scripts/reorganize_sets.py` | Crea y reorganiza playlists en Sets Armados |

### CLI

```bash
plomo stats        # Estado de la colección: tracks, BPM, playlists
plomo verify       # Integrity check de la DB
plomo backup       # Backup manual de master.db
```

## Estructura

```
src/plomo/
├── cue_engine.py    # Análisis de audio con librosa, algoritmo v8
├── energy.py        # Energy score 0-10 desde timings de cues
├── camelot.py       # Camelot wheel: distancias, greedy order
├── rekordbox_db.py  # Wrapper SQLCipher (backup automático, preflight, rollback)
├── config.py        # Configuración desde .env
└── cli.py           # CLI con Click
```

## Algoritmo de cues v8

11 markers por track:

| # | Nombre | Descripción |
|---|--------|-------------|
| 1 | Mix-IN First Beat | Primer onset absoluto |
| 2 | Bass IN | Primer kick sostenido |
| 3 | Breakdown | Inicio del breakdown más largo |
| 4 | DROP | Re-entrada del kick post-breakdown |
| 5 | Mix-OUT | 16 bars antes del último kick |
| — | Loop Intro 16b | Inactivo (configuración manual) |
| — | Loop Outro 16b | **ACTIVE** — auto-loop al final ⭐ |

## Energy Score (0–10)

Calculado desde los timings de cues:

- **BPM** (0–3 pts)
- **Intro tightness** (0–2 pts): bass entra rápido = más energía
- **Breakdown tension** (0–2.5 pts): breakdown largo = más tensión
- **Drop presence** (0–1 pt)
- **Peak section length** (0–1.5 pts)

| Score | Label |
|-------|-------|
| 0–2.4 | ambient |
| 2.5–3.9 | warmup |
| 4–5.4 | build |
| 5.5–6.9 | mid |
| 7–8.4 | peak |
| 8.5–10 | peak+ |

El score se guarda en el campo `Comment` de cada track en Rekordbox (formato `E:7.5`).

## Reglas críticas

```
❌ Nunca modificar master.db con Rekordbox corriendo
❌ Nunca cerrar Rekordbox con la X  →  siempre System Tray → Quit
✅ Backup automático antes de cada cambio
✅ IDs 32-bit safe  →  random.randint(1500000000, 4000000000)
✅ rb_local_usn incremental
```

## Dependencias

- `librosa` — análisis de audio
- `pyrekordbox` — wrapper para Rekordbox 6 DB
- `sqlcipher3` — SQLCipher para acceso directo a master.db
- `mutagen` — lectura de tags ID3
- `click` — CLI
- `psutil` — preflight check (Rekordbox no debe estar corriendo)

## Requisitos

- Python 3.11+
- Rekordbox 6.x
- Windows (paths probados en Windows, adaptable a Mac)

## License

Personal project — uso libre, sin garantías.
