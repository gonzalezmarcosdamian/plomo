"""Actualiza XML para las 4 carpetas nuevas en Sets Armados."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo.rekordbox_db import RekordboxDB
from plomo import config
import sqlcipher3

SETS_ARMADOS = "1975667623"
FOLDER_NAMES = ["Para Tocar", "Mis Sets", "Referencia Pro", "[POOL]"]

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

folder_ids = []
for name in FOLDER_NAMES:
    row = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND ParentID=? AND Attribute=1 AND rb_local_deleted=0",
        (name, SETS_ARMADOS)
    ).fetchone()
    if row:
        folder_ids.append((name, row[0]))
        print(f"  {name}: ID={row[0]}")
    else:
        print(f"  [warn] no encontrada: {name}")
con.close()

with RekordboxDB() as db:
    for name, fid in folder_ids:
        db.add_node_to_xml(int(fid), int(SETS_ARMADOS))
        print(f"  XML actualizado: {name}")

print("Listo.")
