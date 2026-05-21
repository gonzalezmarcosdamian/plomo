"""Fix backslashes en FolderPath y copia ANLZ al pen para los tracks afectados."""
import sys, shutil
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from plomo import config
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3

SHARE = Path(r"C:\Users\gonza\AppData\Roaming\Pioneer\rekordbox\share")
PEN = Path("D:/")
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with RekordboxDB() as db:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    # Buscar tracks activos con backslash en FolderPath
    tracks = con.execute("""
        SELECT ID, Title, FolderPath, AnalysisDataPath FROM djmdContent
        WHERE rb_local_deleted=0 AND FolderPath LIKE ?
    """, ("%\\%",)).fetchall()

    print(f"Tracks con backslash en FolderPath: {len(tracks)}")
    fixed_count = 0
    anlz_count = 0

    for cid, title, path, apath in tracks:
        # Fix backslash
        fixed = path.replace("\\", "/") if path else path
        con.execute(
            "UPDATE djmdContent SET FolderPath=?, DeliveryControl='on', updated_at=? WHERE ID=?",
            (fixed, ts, str(cid))
        )
        fixed_count += 1
        print(f"  Fixed: {title[:55]}")

        # Copiar ANLZ al pen si falta
        if apath and PEN.exists():
            rel = apath.lstrip("/")
            pen_dst = PEN / rel.replace("/", "\\")
            local_src = SHARE / rel
            if local_src.exists() and not pen_dst.exists():
                pen_dst.parent.mkdir(parents=True, exist_ok=True)
                for f in local_src.parent.iterdir():
                    shutil.copy2(f, pen_dst.parent / f.name)
                anlz_count += 1
                print(f"    → ANLZ copiado al pen")

    con.commit()
    con.close()

with RekordboxDB() as db2:
    print(f"\nFixed: {fixed_count} | ANLZ copiados: {anlz_count}")
    print(f"DB integrity: {db2.integrity_check()}")
print("Abrí Rekordbox y hacé sync.")
