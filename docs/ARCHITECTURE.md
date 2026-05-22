# Arquitectura del Proyecto Plomo

Toolkit Python para automatización de DJ workflow con Rekordbox 6.

---

## A) Estructura del Proyecto

```
plomo/
├── src/plomo/          # Módulos core reutilizables (NO tocar sin refactor)
├── scripts/            # Scripts de pipeline activos
│   └── archive/        # Scripts one-off ya ejecutados (solo referencia)
├── data/               # JSONs de datos y estado (ignorados por git si son personales)
├── docs/               # Documentación técnica y artística
├── tests/              # Tests automatizados (pytest)
├── postproduction/     # Output de postproducción (ignorado por git)
├── .env                # Secrets locales (NUNCA al repo)
├── pyproject.toml      # Config del proyecto
├── requirements.txt    # Dependencias
└── README.md           # Documentación principal
```

### Reglas por carpeta

| Carpeta | Qué va | Qué NO va |
|---------|--------|-----------|
| `src/plomo/` | Módulos importables, clases, engines | Scripts ejecutables, lógica one-off |
| `scripts/` | Scripts del pipeline activo usados regularmente | Archivos de prueba, one-offs |
| `scripts/archive/` | Scripts one-off ya ejecutados exitosamente | Scripts activos del pipeline |
| `data/` | JSONs de datos, setlists, batches, state | Código, configs del repo |
| `docs/` | Markdown técnico y artístico | Código, datos |
| Raíz | `.env`, `pyproject.toml`, `requirements.txt`, `README.md`, `.gitignore` | Scripts, JSONs de datos, audio |

---

## B) Scripts Activos del Pipeline

| Script | Cuándo usarlo | Qué hace |
|--------|---------------|----------|
| `scripts/import_all.py` | Fase 1 del pipeline | Mueve archivos de Downloads → Music/YYYY-MM. Para tracks ya en DB: fija FolderPath y DeliveryControl para export USB sin error [2]. NO importa a DB ni aplica cues. |
| `scripts/post_import.py` | Fase 3 del pipeline (después de que RB analice) | Aplica cues v8, energy score, restaura playlists para tracks recién importados. |
| `scripts/muzpa_download.py` | Cuando hay tracks nuevos en Muzpa | Descarga tracks desde la plataforma Muzpa. |
| `scripts/build_set_v2.py` | Construcción de sets nuevos | Set builder con movimientos de energía y anclas Camelot. |
| `scripts/rebuild_all_sets.py` | Reconstrucción total | Reconstruye todos los sets desde cero. |
| `scripts/reorder_sets_energy.py` | Reordenar por energía | Reordena tracks dentro de sets siguiendo curva de energía. |
| `scripts/apply_energy_v2.py` | Aplicar energy score v2 | Aplica el algoritmo energy score v2 a la biblioteca. |
| `scripts/build_setlist_sets.py` | Sets en orden de setlist real | Construye playlists en Rekordbox siguiendo el orden de un setlist histórico. |
| `scripts/analyze_set.py` | Análisis y exploración | Analiza composición y métricas de un set. |
| `scripts/watcher.py` | Daemon en background | Vigila la carpeta Downloads y procesa nuevos archivos automáticamente. |

### Flujo correcto del pipeline de importación

```
1. python scripts/import_all.py         # Mueve archivos, fix metadata
2. Abrir Rekordbox                       # RB detecta, analiza BPM/key/waveform
3. Cerrar Rekordbox (System Tray → Quit)
4. python scripts/post_import.py        # Cues v8 + energy + playlists
5. Abrir Rekordbox → sync pen           # Export a USB
```

---

## C) Archivos que se movieron / deben estar en `data/`

Los siguientes archivos viven en `data/` y NO en la raíz:

| Archivo | Tipo | Va al repo |
|---------|------|------------|
| `data/muzpa_batch.json` | Batch de tracks Muzpa | NO |
| `data/muzpa_batch_50.json` | Batch Muzpa 50 tracks | NO |
| `data/muzpa_batch_set3h.txt` | Texto de batch Muzpa | NO |
| `data/muzpa_api_calls.json` | Registro de llamadas API | NO |
| `data/setlists_muzpa.json` | Setlists desde Muzpa | NO |
| `data/available_ids.json` | IDs disponibles | NO |
| `data/dj_sets_new.json` | Sets generados | NO |
| `data/sunset_day2.json` | Set sunset day 2 | NO |
| `data/sunset_trip_muzpa.json` | Set sunset trip | NO |
| `data/track_playlist_mapping.json` | Mapeo track→playlist | NO (dato personal) |
| `data/transition_feedback.json` | Feedback de transiciones | SI (config del sistema) |

> Regla: JSONs de datos personales → NO al repo. JSONs de configuración del sistema (que afectan el comportamiento del pipeline) → SÍ al repo.

---

## D) Naming de Nuevos Scripts

| Prefijo | Uso | Destino final |
|---------|-----|---------------|
| `pipeline_*.py` | Pasos del pipeline principal | `scripts/` permanente |
| `build_*.py` | Construcción de sets o playlists | `scripts/` permanente |
| `fix_*.py` | Fixes one-off puntuales | `scripts/archive/` después de ejecutar |
| `muzpa_*.py` | Operaciones con plataforma Muzpa | `scripts/` si es recurrente, `archive/` si es one-off |
| `analyze_*.py` | Análisis y exploración de datos | `scripts/` si es recurrente, `archive/` si es one-off |

**Regla general:** si un script se ejecuta más de una vez → `scripts/`. Si se ejecutó una sola vez para resolver algo puntual → moverlo a `scripts/archive/` inmediatamente después.

---

## E) Reglas de Commits

### Qué NUNCA va al repo

```gitignore
.env                          # Secrets locales
data/muzpa_batch*.json        # Datos personales de batches
data/setlists_muzpa.json      # Setlists personales
data/track_playlist_mapping.json  # Mapeo personal
data/available_ids.json
data/dj_sets_new.json
data/sunset_*.json
*.mp3 *.flac *.wav *.aiff     # Audio (copyright / tamaño)
*.mov *.MOV *.mp4             # Video (tamaño)
postproduction/               # Output de postproducción
```

### Qué SÍ va al repo

- Todo código en `src/plomo/` y `scripts/`
- `data/transition_feedback.json` (config del sistema, no dato personal)
- `docs/` completo
- `tests/` completo
- `pyproject.toml`, `requirements.txt`, `README.md`, `.gitignore`

### Formato de commits

```
<tipo>: <descripción en español o inglés>

Tipos: feat, fix, refactor, docs, test, chore, perf
```

---

## F) Módulos Core (`src/plomo/`)

| Módulo | Responsabilidad |
|--------|----------------|
| `config.py` | Paths y variables de entorno |
| `rekordbox_db.py` | Acceso a la base de datos SQLCipher de Rekordbox |
| `cue_engine.py` | Análisis de tracks y aplicación de cues v8 |
| `energy.py` | Energy score v1 |
| `energy_v2.py` | Energy score v2 (groove ratio + features) |
| `set_builder.py` | Lógica de construcción de sets |
| `camelot.py` | Utilidades de Camelot wheel (compatibilidad de keys) |
| `cli.py` | Interfaz de línea de comandos |
