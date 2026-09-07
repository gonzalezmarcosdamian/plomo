"""Exporta la biblioteca a un JSON plano que consume `select_set.py`.

Saca de la DB los tracks con energia calculada y los deja en un archivo con
artista, titulo, BPM, key Camelot, energia y sello. Marca cuales ya estan en
algun set numerado, para poder priorizar lo que nunca se uso.

Uso:
    python scripts/dump_pool.py                      # data/pool.json
    python scripts/dump_pool.py --out otro.json --bpm 118 127
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

ENERGY_RE = re.compile(r"E:(\d+(?:\.\d+)?)")
DEFAULT_OUT = Path(__file__).parent.parent / "data" / "pool.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--bpm", type=float, nargs=2, default=[100.0, 140.0])
    args = ap.parse_args()

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

    # ContentIDs que ya viven en algun set numerado (NN. Nombre)
    usados: set[str] = set()
    for (pid,) in con.execute(
        "SELECT ID FROM djmdPlaylist WHERE rb_local_deleted=0 AND Attribute=0"
        " AND Name GLOB '[0-9][0-9].*'"
    ).fetchall():
        for (cid,) in con.execute(
            "SELECT ContentID FROM djmdSongPlaylist"
            " WHERE PlaylistID=? AND rb_local_deleted=0",
            (pid,),
        ):
            usados.add(str(cid))

    rows = con.execute(
        """
        SELECT c.ID, a.Name, c.Title, c.BPM, k.ScaleName, c.Commnt, l.Name,
               g.Name, c.FolderPath, c.Length
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        LEFT JOIN djmdKey   k ON k.ID = c.KeyID
        LEFT JOIN djmdLabel l ON l.ID = c.LabelID
        LEFT JOIN djmdGenre g ON g.ID = c.GenreID
        WHERE c.rb_local_deleted = 0 AND c.Commnt LIKE 'E:%'
        """
    ).fetchall()
    con.close()

    pool, vistos = [], set()
    for cid, artist, title, bpm_raw, key, commnt, label, genre, folder, largo in rows:
        m = ENERGY_RE.match(commnt or "")
        if not m:
            continue
        bpm = (bpm_raw or 0) / 100
        if not args.bpm[0] <= bpm <= args.bpm[1]:
            continue
        firma = ((artist or "").lower().strip(), (title or "").lower().strip())
        if firma in vistos:  # la biblioteca no deberia tener duplicados, pero por las dudas
            continue
        vistos.add(firma)
        pool.append(
            {
                "id": str(cid),
                "artist": artist or "?",
                "title": title or "?",
                "bpm": bpm,
                "key": key or "?",
                "energy": float(m.group(1)),
                "label": label or "",
                "genre": genre or "",
                "carpeta": Path(folder).parent.name if folder else "",
                # Duracion en segundos. Sin esto no se puede proyectar cuanto
                # dura un set y hay que estimarlo con un promedio inventado.
                "dur_seg": int(largo or 0),
                "usado": str(cid) in usados,
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
    sin_usar = sum(1 for t in pool if not t["usado"])
    print(f"{len(pool)} tracks -> {args.out}  ({sin_usar} sin usar en ningun set)")


if __name__ == "__main__":
    main()
