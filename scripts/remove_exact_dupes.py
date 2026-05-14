"""Remove duplicate DB entries with identical file paths, keeping the one with most cues."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3

with RekordboxDB() as db:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    # Encontrar paths duplicados exactos
    dupes = con.execute("""
        SELECT FolderPath, COUNT(*) as cnt, GROUP_CONCAT(ID, ',') as ids
        FROM djmdContent
        WHERE rb_local_deleted=0
        GROUP BY FolderPath
        HAVING cnt > 1
    """).fetchall()

    print(f"Paths duplicados exactos: {len(dupes)}")
    deleted = 0

    for path, cnt, ids_str in dupes:
        ids = ids_str.split(",")
        # Para cada grupo, ver cuál tiene más cues
        best_id = None
        best_cues = -1
        for id_ in ids:
            cue_count = con.execute(
                "SELECT COUNT(*) FROM djmdCue WHERE ContentID=?", (id_,)
            ).fetchone()[0]
            if cue_count > best_cues:
                best_cues = cue_count
                best_id = id_

        # Marcar el resto como deleted
        for id_ in ids:
            if id_ != best_id:
                con.execute(
                    "UPDATE djmdContent SET rb_local_deleted=1 WHERE ID=?", (id_,)
                )
                deleted += 1
                print(f"  Deleted ID={id_} (kept {best_id} with {best_cues} cues): {Path(path).name}")

    con.commit()
    con.close()
    print(f"\nTotal eliminados: {deleted}")
    print(f"DB integrity: {db.integrity_check()}")
