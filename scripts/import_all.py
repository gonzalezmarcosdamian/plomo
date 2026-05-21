"""
Pipeline de importación — Fase 1 (pre-Rekordbox).

Qué hace:
1. Mueve archivos de Downloads → Music/YYYY-MM
2. Para tracks que YA EXISTEN en la DB: fija FolderPath (forward slashes)
   y DeliveryControl='on' para que el export USB funcione sin error [2]

Qué NO hace:
- NO importa tracks a la DB (Rekordbox lo hace él mismo al abrirse)
- NO aplica cues ni energy — eso es post_import.py

Flujo correcto:
  1. python scripts/import_all.py     ← este script
  2. Abrir Rekordbox → detecta y analiza nuevos (BPM + key + waveform)
  3. Cerrar Rekordbox (System Tray → Quit)
  4. python scripts/post_import.py    ← cues v8 + energy + playlists
"""
import sys
import shutil
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
import sqlcipher3

DOWNLOADS = config.DOWNLOADS_FOLDER
DEST = config.MUSIC_NEW_FOLDER
DEST.mkdir(parents=True, exist_ok=True)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fix_existing_tracks(moved: list[Path]) -> None:
    """Fix FolderPath + DeliveryControl for tracks that already exist in the DB."""
    if not moved:
        return

    ts = now_str()
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    fixed = 0
    for dest_file in moved:
        folder = str(dest_file).replace("\\", "/")
        row = con.execute(
            "SELECT ID FROM djmdContent WHERE FileNameL=? AND rb_local_deleted=0",
            (dest_file.name,),
        ).fetchone()
        if row:
            con.execute(
                "UPDATE djmdContent SET FolderPath=?, DeliveryControl='on', updated_at=? WHERE ID=?",
                (folder, ts, row[0]),
            )
            fixed += 1

    con.commit()
    con.close()

    if fixed:
        print(f"\n  Fix metadata: {fixed} tracks existentes actualizados (FolderPath + DeliveryControl)")


def main() -> None:
    tracks = sorted(list(DOWNLOADS.glob("*.mp3")) + list(DOWNLOADS.glob("*.flac")))
    print(f"Tracks en Downloads: {len(tracks)}")
    for t in tracks:
        print(f"  {t.name}")

    if not tracks:
        print("Nada que procesar.")
        return

    moved: list[Path] = []

    for i, src in enumerate(tracks, 1):
        dest_file = DEST / src.name
        print(f"[{i}/{len(tracks)}] {src.name}")

        if dest_file.exists():
            # Archivo ya en destino — eliminar duplicado de Downloads
            if src.exists():
                src.unlink()
            print(f"  → Ya existía en destino, duplicado removido de Downloads")
        else:
            shutil.move(str(src), str(dest_file))
            print(f"  → Movido a {DEST.name}/")

        moved.append(dest_file)

    print(f"\n{len(moved)} archivos movidos a {DEST}")

    # Fix metadata sólo para los que ya estaban en la DB antes de que RB los importe.
    # Los nuevos los fijará post_import.py después del análisis de Rekordbox.
    try:
        fix_existing_tracks(moved)
    except Exception as e:
        print(f"  Advertencia: no se pudo conectar a la DB ({e})")
        print("  Rekordbox no debe estar corriendo — cerralo primero.")

    print("\n=== LISTO ===")
    print("Abrí Rekordbox → va a detectar los nuevos, analizarlos (BPM + key + waveform).")
    print("Cuando termine: cerrá RB (System Tray → Quit) y corré post_import.py.")


if __name__ == "__main__":
    main()
