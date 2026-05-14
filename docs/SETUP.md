# Setup local desde cero

## 1. Push a GitHub

Desde `C:\Users\gonza\Music\plomo\`:

```powershell
cd C:\Users\gonza\Music\plomo
git init
git add .
git commit -m "feat: initial repo structure - cue engine v8 + camelot + CLI skeleton"
git branch -M main
git remote add origin https://github.com/gonzalezmarcosdamian/plomo.git
git push -u origin main
```

## 2. Setup VS Code

```powershell
cd C:\Users\gonza\Music\plomo
code .
```

Una vez abierto:
1. Instalar extensions: **Python**, **Pylance**
2. Crear venv: `Ctrl+Shift+P → Python: Create Environment → venv → Python 3.11+`
3. Activar: `.venv\Scripts\activate`
4. Instalar dependencias: `pip install -e .` (modo editable, lee desde `src/`)
5. Mover `docs/vscode_launch_template.json` a `.vscode/launch.json`

## 3. Configurar `.env`

```powershell
cp .env.example .env
notepad .env
```

Verificar que los paths apunten correctamente a tu instalación.

## 4. Test inicial

```powershell
# Verify config loaded
python -c "from plomo import config; print(config.REKORDBOX_DB_PATH)"

# Run CLI
python -m plomo.cli --help
python -m plomo.cli stats

# Run tests
pytest -v
```

## 5. Daemon Watcher (opcional)

Para que procese Downloads automático en background:

```powershell
python scripts/watcher.py
```

Para que arranque al boot de Windows:
- Task Scheduler → New Task → Trigger: At log on → Action: `pythonw.exe scripts/watcher.py`

## Workflow diario sugerido

```powershell
# Bajaste tracks nuevos a Downloads
python -m plomo.cli analyze   # Mueve, importa, cuea

# Antes de armar set
python -m plomo.cli stats     # Ver cuál cluster Camelot tiene gaps
python -m plomo.cli playlist --style vuarambon --duration 60

# Después de cada session
python -m plomo.cli backup    # Snapshot manual
git commit -am "feat: vuarambon set Sábado"
git push
```

## Troubleshooting

**"Rekordbox is running" error:**
- Ctrl+Shift+Esc → buscar `rekordbox.exe` → End Task
- Si está en system tray: click derecho → Quit

**"database disk image is malformed":**
- Restaurar backup más reciente:
  ```powershell
  $latest = Get-ChildItem outputs\master.db.backup-* | Sort-Object LastWriteTime -Desc | Select -First 1
  Copy-Item $latest.FullName "$env:APPDATA\Pioneer\rekordbox\master.db" -Force
  ```

**ImportError pyrekordbox / sqlcipher3:**
```powershell
pip install --upgrade pyrekordbox sqlcipher3-binary
```

**Tests fallan por falta de ground truth:**
- Es esperado — los `.mp3` están gitignored. Crear los tuyos en `tests/ground_truth/`.

## Migración pendiente (TODO)

Estos scripts viven en `/tmp/` del sandbox y hay que portarlos a módulos:

- `cue_v8.py` → ya migrado a `src/plomo/cue_engine.py` ✅
- `find_vuarambon.py` → portar a `src/plomo/playlist_builder.py`
- `create_vuarambon_pl.py` → portar a `src/plomo/playlist_builder.py`
- `import_batch.py` → portar a `src/plomo/importer.py`
- `detect_keys.py` → reemplazar Krumhansl por essentia/madmom (v9)
- `reorder_with_real_keys.py` → portar a `src/plomo/playlist_builder.py:reorder()`
