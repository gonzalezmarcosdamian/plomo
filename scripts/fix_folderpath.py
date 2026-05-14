"""Fix FolderPath backslashes y flags de sync para tracks del Cumple del 20."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3

CUMPLE_IDS = [
    37723737, 205665671, 246333736, 206004569, 30038355, 88367438,
    191335971, 121667930, 39880106, 264841568, 180819583, 79146277,
    173432985, 24461486, 40162623, 230289841, 238425025, 223928742,
    167162931, 14192861, 227818551, 152689122, 5130344, 31403052,
    221819672, 62725563, 195885751, 250281940, 211255525
]

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with RekordboxDB() as db:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    fixed = 0
    for cid in CUMPLE_IDS:
        row = con.execute(
            "SELECT FolderPath FROM djmdContent WHERE ID=?", (str(cid),)
        ).fetchone()
        if not row:
            continue

        folder = row[0] or ""
        new_folder = folder.replace("\\", "/")

        con.execute("""
            UPDATE djmdContent SET
                FolderPath=?,
                CueUpdated=1,
                AnalysisUpdated=1,
                TrackInfoUpdated=1,
                updated_at=?
            WHERE ID=?
        """, (new_folder, ts, str(cid)))
        fixed += 1
        print(f"  [{cid}] {new_folder[-60:]}")

    con.commit()
    con.close()
    print(f"\nCorregidos: {fixed} tracks")

with RekordboxDB() as db2:
    print(f"DB integrity: {db2.integrity_check()}")
