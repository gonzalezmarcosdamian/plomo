"""Arma las playlists que se arrastran al pen, para que sincronizar sea un gesto.

El Sync Manager de Rekordbox sincroniza la ESTRUCTURA de playlists pero no copia
los archivos de audio que no esten ya en el dispositivo. Por eso la unica forma
confiable de llevar musica nueva al pen es arrastrar, y arrastrar necesita que
haya una sola cosa que arrastrar.

Esto crea dos playlists planas bajo `Pro DJ Library`:

  PEN — Todo      la union de todos los tracks que usa algun set numerado
  PEN — Activos   solo los de los niveles 1 a 4, sin Archivo ni Referencia

Arrastrar cualquiera de las dos sobre el dispositivo copia TODOS los archivos que
esos sets necesitan. Despues se arrastra `Sets Armados` para llevar la
estructura, que ya no tiene que copiar nada.

Uso:
    python scripts/armar_pen.py --dry
    python scripts/armar_pen.py
"""
from __future__ import annotations

import argparse
import random
import sys
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(RAIZ / ".env")

import sqlcipher3  # noqa: E402
from plomo import config  # noqa: E402

PADRE = "Pro DJ Library"
NIVELES_ACTIVOS = ("1 Apertura", "2 Previa", "3 Prime Time", "4 Peak",
                   "5 Cierre", "6 After")


def _id() -> str:
    return str(random.randint(1_500_000_000, 4_000_000_000))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    filas = con.execute("SELECT ID, Name, ParentID, Attribute FROM djmdPlaylist "
                        "WHERE rb_local_deleted=0").fetchall()
    padre = next((f for f in filas if f[3] == 1 and f[1] == PADRE), None)
    if not padre:
        sys.exit(f"no existe la carpeta '{PADRE}'")

    hijos: dict[str, list] = {}
    for f in filas:
        hijos.setdefault(f[2], []).append(f)

    def sets_bajo(nombre_carpeta: str | None) -> list[str]:
        """IDs de playlists de set; si se pasa una carpeta, solo las de adentro."""
        out = []
        for f in filas:
            if f[3] == 1:
                continue
            if not f[1][:1].isdigit():
                continue
            if nombre_carpeta is None:
                out.append(f[0])
            else:
                pad = next((x for x in filas if x[0] == f[2]), None)
                if pad and pad[1] == nombre_carpeta:
                    out.append(f[0])
        return out

    def tracks_de(pids: list[str]) -> list[str]:
        """ContentIDs unicos, en el orden en que aparecen."""
        vistos, out = set(), []
        for pid in pids:
            for (cid,) in con.execute(
                    "SELECT sp.ContentID FROM djmdSongPlaylist sp "
                    "JOIN djmdContent c ON c.ID = sp.ContentID "
                    "WHERE sp.PlaylistID=? AND sp.rb_local_deleted=0 "
                    "AND c.rb_local_deleted=0 ORDER BY sp.TrackNo", (pid,)):
                if cid not in vistos:
                    vistos.add(cid)
                    out.append(cid)
        return out

    todos = tracks_de(sets_bajo(None))
    activos = tracks_de([p for niv in NIVELES_ACTIVOS for p in sets_bajo(niv)])

    def peso(cids: list[str]) -> float:
        if not cids:
            return 0.0
        q = ",".join("?" * len(cids))
        r = con.execute(f"SELECT SUM(FileSize) FROM djmdContent WHERE ID IN ({q})",
                        cids).fetchone()
        return (r[0] or 0) / 1e9

    print(f"PEN — Todo     : {len(todos):>4} tracks, {peso(todos):.1f} GB")
    print(f"PEN — Activos  : {len(activos):>4} tracks, {peso(activos):.1f} GB")
    if args.dry:
        print("\n[dry] no se escribio nada")
        return

    for nombre, cids in (("PEN — Todo", todos), ("PEN — Activos", activos)):
        fila = next((f for f in filas if f[1] == nombre), None)
        if fila:
            pid = fila[0]
            con.execute("UPDATE djmdSongPlaylist SET rb_local_deleted=1, updated_at=? "
                        "WHERE PlaylistID=?", (ts, pid))
        else:
            pid = _id()
            con.execute(
                "INSERT INTO djmdPlaylist (ID, Seq, Name, ImagePath, Attribute, ParentID,"
                " SmartList, UUID, rb_data_status, rb_local_data_status, rb_local_deleted,"
                " rb_local_synced, created_at, updated_at)"
                " VALUES (?,?,?,NULL,0,?,NULL,?,0,0,0,0,?,?)",
                (pid, 0, nombre, padre[0], str(uuid_lib.uuid4()), ts, ts))
        for i, cid in enumerate(cids, 1):
            con.execute(
                "INSERT INTO djmdSongPlaylist (ID, PlaylistID, ContentID, TrackNo, UUID,"
                " rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,"
                " created_at, updated_at) VALUES (?,?,?,?,?,0,0,0,0,?,?)",
                (_id(), pid, cid, i, str(uuid_lib.uuid4()), ts, ts))
        print(f"  escrita: {nombre} ({len(cids)} tracks)")
    con.commit()
    print("\nintegridad:", con.execute("PRAGMA integrity_check").fetchone()[0])
    print("\nAhora, en Rekordbox modo Export:")
    print("  1. arrastra 'PEN — Todo' (o 'PEN — Activos') sobre el dispositivo -> copia los archivos")
    print("  2. arrastra 'Sets Armados' -> lleva la estructura, ya sin copiar nada")


if __name__ == "__main__":
    main()
