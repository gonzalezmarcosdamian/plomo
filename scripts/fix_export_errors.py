"""Fix errores del export log: [2] DeliveryControl NULL en carpeta Nuevos/."""
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with RekordboxDB() as db:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    # Fix [2]: DeliveryControl NULL en cualquier carpeta Nuevos
    bad = con.execute("""
        SELECT ID, Title, FolderPath FROM djmdContent
        WHERE FolderPath LIKE '%Nuevos%'
        AND (DeliveryControl IS NULL OR DeliveryControl='')
        AND rb_local_deleted=0
    """).fetchall()

    print(f"Tracks [2] a corregir: {len(bad)}")
    for cid, title, path in bad:
        fixed = (path or "").replace("\\", "/")
        con.execute(
            "UPDATE djmdContent SET DeliveryControl='on', FolderPath=?, updated_at=? WHERE ID=?",
            (fixed, ts, str(cid))
        )
        print(f"  OK: {title}")

    # Verificar tracks con FolderPath vacío (causa [1])
    empty = con.execute("""
        SELECT COUNT(*) FROM djmdContent
        WHERE rb_local_deleted=0 AND (FolderPath IS NULL OR FolderPath='')
    """).fetchone()[0]
    print(f"\nTracks con FolderPath vacío ([1]): {empty}")
    if empty > 0:
        # Marcarlos como deleted si no tienen path
        con.execute("""
            UPDATE djmdContent SET rb_local_deleted=1, updated_at=?
            WHERE rb_local_deleted=0 AND (FolderPath IS NULL OR FolderPath='')
        """, (ts,))
        print(f"  → Marcados como deleted")

    con.commit()
    con.close()

with RekordboxDB() as db2:
    print(f"DB integrity: {db2.integrity_check()}")
print("Abrí Rekordbox y hacé sync.")
