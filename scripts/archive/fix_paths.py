"""Fix broken track paths in Nuevos/ folder."""
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

    nuevos = Path(r"C:\Users\gonza\OneDrive\Documentos\Music\2026\Nuevos")
    fixed = 0
    not_found = []

    for id_, path in broken:
        if Path(path).exists():
            continue
        filename = Path(path).name
        found = list(nuevos.rglob(filename))
        if found:
            new_path = str(found[0]).replace("\\", "/")
            con.execute("UPDATE djmdContent SET FolderPath=? WHERE ID=?", (new_path, id_))
            print(f"OK: {filename}")
            fixed += 1
        else:
            not_found.append(filename)

    con.commit()
    con.close()
    print(f"\nCorregidos: {fixed}")
    if not_found:
        print(f"No encontrados ({len(not_found)}):")
        for f in not_found:
            print(f"  {f}")
    print(f"DB integrity: {db.integrity_check()}")
