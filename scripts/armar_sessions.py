# -*- coding: utf-8 -*-
"""Arma la carpeta 'Sessions' en Rekordbox: una copia de cada set publicado.

"Haceme un apartado en rekord de las session y sync pen de todo, este 159 va a ser
sunset me gusto para eso" (2026-10-26). Las Sessions estaban sueltas entre los 150
sets de 'Sets Armados'. Esto las junta en Sets Armados / Sessions, que viaja al pen
con el mismo export de 'Sets Armados'.

Son COPIAS, no los sets movidos: el set original sigue donde esta, con su numero
(build_set.py, Spotify y los videos lo buscan por numero). Correrlo de nuevo rehace
cada copia desde su set; agregar una Session es sumar una linea a data/sessions.json.

Uso:
    python scripts/armar_sessions.py --dry
    python scripts/armar_sessions.py
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

MAPA = RAIZ / "data" / "sessions.json"


def concepto(nombre_set: str) -> str:
    """'148. Housero Progresivo · 1 a 3 AM — 2h — 2026-09-28' -> 'Housero Progresivo · 1 a 3 AM'.

    Saca el numero del frente y la duracion y la fecha del final. Si el concepto
    ya empieza con 'Session NN ·' (el 153 y el 157 se llaman asi), lo saca tambien:
    la etiqueta la pone la carpeta.
    """
    s = re.sub(r"^\s*\d+\.\s*", "", nombre_set or "")
    s = s.split(" — ")[0].strip()
    s = re.sub(r"^Session\s+\d+\s*·\s*", "", s, flags=re.I)
    return s


def nombre_lista(etiqueta: str, num: int, nombre_set: str) -> str:
    return f"{etiqueta} · {concepto(nombre_set)} ({num})"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    from build_set import create_playlist, db_connect, now_str, rebuild_playlist, rename_playlist
    from plomo.rekordbox_app import esta_abierto
    from plomo.rekordbox_db import RekordboxDB

    mapa = json.loads(MAPA.read_text(encoding="utf-8"))
    if not args.dry and esta_abierto():
        raise SystemExit("Rekordbox esta abierto: cerralo y volve a correr.")

    con = db_connect()
    vivas = "COALESCE(rb_local_deleted,0)=0"
    padre = con.execute(f"SELECT ID FROM djmdPlaylist WHERE Name=? AND Attribute=1 AND {vivas}",
                        (mapa["padre"],)).fetchone()
    if not padre:
        raise SystemExit(f"no existe la carpeta '{mapa['padre']}'")
    carpeta = con.execute(f"SELECT ID FROM djmdPlaylist WHERE Name=? AND Attribute=1 AND ParentID=? AND {vivas}",
                          (mapa["carpeta"], padre[0])).fetchone()
    if not carpeta:
        if args.dry:
            print(f"  [dry] se crearia la carpeta {mapa['padre']} / {mapa['carpeta']}")
        else:
            con.close()
            subprocess.run([sys.executable, str(RAIZ / "scripts/create_folder.py"), mapa["carpeta"],
                            "--parent", mapa["padre"]], check=True)
            con = db_connect()
            carpeta = con.execute(f"SELECT ID FROM djmdPlaylist WHERE Name=? AND Attribute=1 AND ParentID=? AND {vivas}",
                                  (mapa["carpeta"], padre[0])).fetchone()
    ts = now_str()
    for item in mapa["listas"]:
        fila = con.execute(f"SELECT ID, Name FROM djmdPlaylist WHERE Name LIKE ? AND Attribute=0 AND {vivas}",
                           (f"{item['set']}.%",)).fetchall()
        if len(fila) != 1:
            raise SystemExit(f"el set {item['set']} no esta (o esta repetido) en Rekordbox: {fila}")
        set_id, set_nombre = fila[0]
        temas = [{"id": str(r[0])} for r in con.execute(
            f"SELECT ContentID FROM djmdSongPlaylist WHERE PlaylistID=? AND {vivas} ORDER BY TrackNo", (set_id,))]
        nombre = nombre_lista(item["etiqueta"], item["set"], set_nombre)
        if args.dry or not carpeta:
            print(f"  [dry] {nombre}: {len(temas)} temas")
            continue
        # La copia se encuentra por el numero entre parentesis: asi sobrevive a que
        # cambie el concepto del set.
        existente = con.execute(f"SELECT ID FROM djmdPlaylist WHERE ParentID=? AND Name LIKE ? AND {vivas}",
                                (carpeta[0], f"% ({item['set']})")).fetchone()
        if existente:
            pid = existente[0]
            rename_playlist(con, pid, nombre, ts)   # con usn: el sync del pen ve el cambio
        else:
            with RekordboxDB() as db:
                pid = create_playlist(con, nombre, carpeta[0])
                con.commit()
                db.add_node_to_xml(int(pid), int(carpeta[0]))
        n = rebuild_playlist(con, pid, temas, ts)
        con.commit()
        print(f"  {nombre}: {n} temas")
    print("integridad:", con.execute("PRAGMA quick_check").fetchone()[0])
    con.close()


if __name__ == "__main__":
    main()
