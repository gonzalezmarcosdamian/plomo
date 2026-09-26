# -*- coding: utf-8 -*-
"""Mi sonido, separado por momento de la noche, y escrito como carpetas en Rekordbox.

POR QUE
-------
"Mi sonido agregale un nivel por momento del set en la biblio" (el DJ,
2026-09-26). Hasta ahora `data/energia_percibida.json` marcaba favoritos sin
distinguir para que sirven, y no es lo mismo un tema que le gusta para abrir a
las once que uno para las tres de la manana. Juri (E4.5) y Fragma (E7.5) son los
dos "mi sonido" y no comparten ningun momento.

COMO SE DECIDE EL MOMENTO
-------------------------
No por opinion: por las bandas que salen de sus propios sets de la noche,
medidas en data/momentos.json.

    warm    E 4.8-6.9 (mediana 6.0)   BPM 120-123
    pico    E 5.5-7.9 (mediana 6.6)   BPM 122-124
    cierre  E 6.0-7.7 (mediana 6.8)   BPM 122-125

Las bandas se pisan, y esta bien que se pisen: un tema de E6.5 sirve en los
tres. Por eso un tema puede quedar en mas de un momento, y el orden adentro de
cada carpeta es por cercania a la MEDIANA de ese momento, que es el centro de
gravedad de lo que el DJ toca ahi.

QUE ESCRIBE EN REKORDBOX
------------------------
Una carpeta `MI SONIDO` con una playlist por momento. Son playlists de
referencia, no sets: no llevan numero, no se tocan de corrido, y sirven para
buscar material cuando se arma.

USO
---
    python scripts/mi_sonido.py --dry
    python scripts/mi_sonido.py
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
import sqlcipher3  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CARPETA = "MI SONIDO"


def conectar():
    con = sqlcipher3.connect(os.environ["REKORDBOX_DB_PATH"])
    con.execute(f"PRAGMA key='{os.environ['SQLCIPHER_KEY']}'")
    con.execute("PRAGMA cipher_compatibility=4")
    return con


def clasificar(t: dict, e: float, bandas: dict) -> list[str]:
    """En que momentos entra un tema. Puede ser en mas de uno, o en ninguno."""
    out = []
    for nom, b in bandas.items():
        if b["e"][0] <= e <= b["e"][1] and b["bpm"][0] - 1 <= t["bpm"] <= b["bpm"][1] + 1:
            out.append(nom)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    POOL = {t["id"]: t for t in json.loads((RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
    PERC = json.loads((RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8"))
    bandas = json.loads((RAIZ / "data/momentos.json").read_text(encoding="utf-8"))

    por_momento: dict[str, list] = {k: [] for k in bandas}
    huerfanos = []
    for cid, v in PERC.items():
        if not v.get("favorito"):
            continue
        t = POOL.get(cid)
        if not t:
            continue
        e = v.get("E", t["energy"])
        momentos = clasificar(t, e, bandas)
        v["momentos"] = momentos            # queda anotado en el archivo
        if not momentos:
            huerfanos.append((cid, t, e))
        for m in momentos:
            por_momento[m].append((abs(e - bandas[m]["e_med"]), cid, t, e))

    (RAIZ / "data/energia_percibida.json").write_text(
        json.dumps(PERC, indent=1, ensure_ascii=False), encoding="utf-8")

    for m, filas in por_momento.items():
        filas.sort()
        print(f"\n{m.upper()}  ({len(filas)} temas, banda E {bandas[m]['e'][0]}-{bandas[m]['e'][1]})")
        for _, cid, t, e in filas:
            print(f"   E{e:.1f} {t['bpm']:.0f} {t['key']:>3s}  {t['artist'][:24]} - {t['title'][:34]}")
    if huerfanos:
        print(f"\nFUERA DE TODA BANDA ({len(huerfanos)}): le gustan pero no entran en "
              f"ningun momento de esta noche")
        for cid, t, e in huerfanos:
            print(f"   E{e:.1f} {t['bpm']:.0f}  {t['artist'][:24]} - {t['title'][:34]}")

    if args.dry:
        print("\n--dry: no se escribio en Rekordbox")
        return

    con = conectar()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    raiz = con.execute("SELECT ID FROM djmdPlaylist WHERE Name=? AND rb_local_deleted=0",
                       (CARPETA,)).fetchone()
    if raiz:
        raiz = raiz[0]
    else:
        raiz = str(random.randint(100000000, 999999999))
        con.execute("""INSERT INTO djmdPlaylist (ID, Seq, Name, ImagePath, Attribute, ParentID,
            SmartList, UUID, rb_data_status, rb_local_data_status, rb_local_deleted,
            rb_local_synced, usn, rb_local_usn, created_at, updated_at)
            VALUES (?,?,?,NULL,1,'root',NULL,?,0,0,0,0,NULL,NULL,?,?)""",
            (raiz, 99, CARPETA, str(uuid_lib.uuid4()), ahora, ahora))
        print(f"\ncarpeta {CARPETA} creada")

    for i, (m, filas) in enumerate(por_momento.items(), 1):
        nombre = f"{CARPETA} · {m}"
        vieja = con.execute("SELECT ID FROM djmdPlaylist WHERE Name=? AND rb_local_deleted=0",
                            (nombre,)).fetchone()
        if vieja:
            con.execute("UPDATE djmdSongPlaylist SET rb_local_deleted=1 WHERE PlaylistID=?", (vieja[0],))
            pid = vieja[0]
        else:
            pid = str(random.randint(100000000, 999999999))
            con.execute("""INSERT INTO djmdPlaylist (ID, Seq, Name, ImagePath, Attribute, ParentID,
                SmartList, UUID, rb_data_status, rb_local_data_status, rb_local_deleted,
                rb_local_synced, usn, rb_local_usn, created_at, updated_at)
                VALUES (?,?,?,NULL,0,?,NULL,?,0,0,0,0,NULL,NULL,?,?)""",
                (pid, i, nombre, raiz, str(uuid_lib.uuid4()), ahora, ahora))
        for n, (_, cid, _t, _e) in enumerate(filas, 1):
            con.execute("""INSERT INTO djmdSongPlaylist (ID, PlaylistID, ContentID, TrackNo,
                UUID, rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
                usn, rb_local_usn, created_at, updated_at)
                VALUES (?,?,?,?,?,0,0,0,0,NULL,NULL,?,?)""",
                (str(random.randint(100000000, 999999999)), pid, cid, n,
                 str(uuid_lib.uuid4()), ahora, ahora))
        print(f"  {nombre}: {len(filas)} temas")
    con.commit()
    print("\nintegridad:", con.execute("PRAGMA quick_check").fetchone()[0])


if __name__ == "__main__":
    main()
