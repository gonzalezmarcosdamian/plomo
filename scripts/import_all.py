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
  4. python scripts/post_import.py            ← cues v8 + energy + playlists
  5. python scripts/import_all.py --archive   ← vacia el Inbox

El paso 5 no es opcional: Rekordbox reescanea la carpeta monitoreada ENTERA en
cada apertura, no solo lo nuevo. Si el Inbox crece sin limite, cada apertura
reprocesa todo, y cualquier archivo cuya fila se haya borrado vuelve a entrar
como track nuevo -> duplicado. Vaciando el Inbox, Rekordbox solo ve lo que
falta importar.
"""
import sys
import shutil
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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


def archive_imported(con_path: Path) -> None:
    """
    Saca del Inbox los archivos que Rekordbox ya importo, a Nuevos/YYYY-MM.

    Por que: Rekordbox reescanea la carpeta monitoreada ENTERA en cada apertura,
    no solo lo nuevo. Con el Inbox creciendo sin limite (llego a 975 archivos)
    cada apertura reprocesa todo, y cualquier archivo cuya fila se haya borrado
    vuelve a entrar como track nuevo -> duplicado. Vaciando el Inbox despues de
    cada importacion, Rekordbox solo ve lo que falta importar.

    Solo mueve archivos que YA tienen fila activa apuntando a su ruta actual:
    lo que todavia no importo Rekordbox se queda donde esta.
    """
    files = sorted(DEST.glob("*.mp3")) + sorted(DEST.glob("*.flac"))
    if not files:
        return

    con = sqlcipher3.connect(str(con_path))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
    # ruta -> ID. Se actualiza por ID y no por "WHERE LOWER(FolderPath)=?":
    # el LOWER() de SQLite solo baja ASCII, asi que "RÜFÜS" nunca matchea
    # contra el .lower() de Python y la fila queda apuntando al archivo viejo.
    known = {r[1].lower(): str(r[0]) for r in con.execute(
        "SELECT ID, FolderPath FROM djmdContent WHERE rb_local_deleted=0 AND FolderPath IS NOT NULL")}

    ts = now_str()
    moved = 0
    pending = 0
    for src in files:
        current = str(src).replace("\\", "/")
        if current.lower() not in known:
            pending += 1
            continue  # Rekordbox todavia no lo importo

        month = datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m")
        dest_dir = DEST.parent / month
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / src.name
        if dest_file.exists():
            pending += 1
            continue

        shutil.move(str(src), str(dest_file))
        # La fila apunta a la ruta vieja: hay que actualizarla o el track
        # queda como "archivo faltante" en Rekordbox.
        con.execute(
            "UPDATE djmdContent SET FolderPath=?, updated_at=? WHERE ID=?",
            (str(dest_file).replace("\\", "/"), ts, known[current.lower()]),
        )
        moved += 1

    con.commit()
    con.close()
    print(f"\n  Inbox archivado: {moved} movidos a Nuevos/YYYY-MM, {pending} siguen en Inbox")


def main() -> None:
    if "--archive" in sys.argv:
        # Se corre DESPUES de que Rekordbox importo. Vacia el Inbox.
        print(f"Archivando lo ya importado desde {DEST}")
        archive_imported(config.REKORDBOX_DB_PATH)
        return

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
            print(f"  [dup] Ya existia en destino, removido de Downloads")
        else:
            shutil.move(str(src), str(dest_file))
            print(f"  [ok] Movido a {DEST.name}/")

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
    print(f"Tracks movidos a: {DEST}")
    print("")
    print("Si Rekordbox ya tiene 'Nuevos/Inbox' como carpeta vigilada:")
    print("  -> Abri RB -> detecta los nuevos automaticamente -> cerra -> corre post_import.py")
    print("")
    print("Si es la PRIMERA VEZ (setup inicial):")
    print("  1. Abri RB")
    print("  2. File > Preferences > Library > Add Monitor Folder")
    print(f"     Agrega: {DEST}")
    print("  3. RB analiza (BPM + key + waveform) -> cerra -> corre post_import.py")
    print("  (Solo necesitas hacer este setup UNA VEZ)")


if __name__ == "__main__":
    main()
