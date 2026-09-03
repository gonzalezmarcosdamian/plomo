"""Crea una carpeta de playlists en Rekordbox (Attribute=1).

Rekordbox necesita DOS cosas para mostrar una carpeta: la fila en djmdPlaylist
y el <NODE> correspondiente en masterPlaylists6.xml. Si falta el nodo, la
carpeta aparece vacia o no aparece.

Uso:
    python scripts/create_folder.py "SERIE YOUTUBE" --parent "Sets Armados"
    python scripts/create_folder.py "SERIE YOUTUBE" --parent-id 1975667623
"""
from __future__ import annotations

import argparse
import random
import sys
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402
from plomo.rekordbox_db import RekordboxDB  # noqa: E402


def safe_id() -> str:
    """IDs > 32-bit los ignora la UI de Rekordbox."""
    return str(random.randint(1500000000, 4000000000))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--parent", help="nombre de la carpeta padre")
    ap.add_argument("--parent-id", help="id de la carpeta padre")
    args = ap.parse_args()

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

    if args.parent_id:
        parent = args.parent_id
    elif args.parent:
        row = con.execute(
            "SELECT ID FROM djmdPlaylist WHERE Name=? AND Attribute=1 AND rb_local_deleted=0",
            (args.parent,),
        ).fetchone()
        if not row:
            raise SystemExit(f"No existe la carpeta padre: {args.parent}")
        parent = row[0]
    else:
        parent = "root"

    ya = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND rb_local_deleted=0", (args.name,)
    ).fetchone()
    if ya:
        print(f"Ya existe: {args.name} (id={ya[0]})")
        con.close()
        return

    pl_id = safe_id()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
    con.execute(
        """INSERT INTO djmdPlaylist
           (ID, Seq, Name, ImagePath, Attribute, ParentID, SmartList, UUID,
            rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
            usn, rb_local_usn, created_at, updated_at)
           VALUES (?,0,?,NULL,1,?,NULL,?,0,0,0,0,NULL,?,?,?)""",
        (pl_id, args.name, parent, str(uuid_lib.uuid4()), max_usn + 1, ts, ts),
    )
    con.commit()
    print("Integridad:", con.execute("PRAGMA integrity_check").fetchone()[0])
    con.close()

    # El nodo XML va aparte: sin el, Rekordbox no dibuja la carpeta.
    if parent != "root":
        db = RekordboxDB()
        db.add_node_to_xml(int(pl_id), int(parent), attribute=1)
        print("NODE agregado al XML")

    print(f"Carpeta creada: {args.name} (id={pl_id}, parent={parent})")


if __name__ == "__main__":
    main()
