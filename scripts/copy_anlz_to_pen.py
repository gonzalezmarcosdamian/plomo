"""
Copia los archivos ANLZ desde el cache local de Rekordbox al pen drive.
Rekordbox los tiene localmente pero no los está copiando al export.
"""
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
import sqlcipher3

SHARE = Path(r"C:\Users\gonza\AppData\Roaming\Pioneer\rekordbox\share")
PEN = Path("D:/")

# Todos los tracks del Cumple del 20 (pool + set)
PLAYLIST_IDS = ["2144500797", "3205391658"]

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

copied = 0
skipped = 0
errors = 0

seen_ids = set()
for pl_id in PLAYLIST_IDS:
    tracks = con.execute("""
        SELECT c.ID, c.Title, c.AnalysisDataPath
        FROM djmdSongPlaylist sp JOIN djmdContent c ON c.ID=sp.ContentID
        WHERE sp.PlaylistID=? ORDER BY sp.TrackNo
    """, (pl_id,)).fetchall()

    for cid, title, apath in tracks:
        if cid in seen_ids or not apath:
            continue
        seen_ids.add(cid)

        # apath = /PIONEER/USBANLZ/xxx/yyy/ANLZ0000.DAT
        rel = apath.lstrip("/")

        local_src = SHARE / rel
        pen_dst = PEN / rel.replace("/", "\\")

        if not local_src.exists():
            print(f"  MISS_LOCAL | {title[:40]}")
            errors += 1
            continue

        if pen_dst.exists():
            print(f"  ALREADY    | {title[:40]}")
            skipped += 1
            continue

        # Crear carpeta destino y copiar
        pen_dst.parent.mkdir(parents=True, exist_ok=True)

        # Copiar ANLZ0000.DAT y también ANLZ0001.EXT si existe
        base_dir = local_src.parent
        for anlz_file in base_dir.iterdir():
            dst_file = pen_dst.parent / anlz_file.name
            shutil.copy2(anlz_file, dst_file)

        print(f"  COPIED     | {title[:40]}")
        copied += 1

con.close()

print(f"\nCopiados: {copied}")
print(f"Ya existían: {skipped}")
print(f"Errores: {errors}")
print("\nAhora abrí Rekordbox y hacé Sync al pen — los tracks deberían aparecer.")
