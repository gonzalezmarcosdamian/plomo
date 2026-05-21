"""Remove duplicate DB entries pointing to missing files in Nuevos/ folder."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3

with RekordboxDB() as db:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    broken = con.execute("""
        SELECT ID, FolderPath FROM djmdContent
        WHERE rb_local_deleted=0
        AND FolderPath LIKE '%2026/Nuevos/%'
    """).fetchall()

    to_delete = []
    for id_, path in broken:
        if not Path(path).exists():
            to_delete.append(id_)

    print(f"Entradas huerfanas a marcar como deleted: {len(to_delete)}")
    for id_ in to_delete:
        con.execute("UPDATE djmdContent SET rb_local_deleted=1 WHERE ID=?", (id_,))

    con.commit()
    con.close()
    print(f"DB integrity: {db.integrity_check()}")
