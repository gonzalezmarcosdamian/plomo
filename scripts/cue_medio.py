# -*- coding: utf-8 -*-
"""Agrega el hot cue "Medio" a los temas que ya estan en la biblioteca.

POR QUE
-------
En un tema con drop largo quedaban dos minutos sin un solo punto donde
agarrarse: del DROP al Mix-OUT, y si el tema no tenia drop detectado, del
Breakdown al Mix-OUT. Pedido del DJ el 2026-09-23 mirando Lane 8, Sultan +
Shepard - The Little Mushroom That Got Away, que tiene el ultimo tercio entero
sin cue.

Para los temas que entren de ahora en mas lo resuelve el cue engine (layout v9,
src/plomo/cue_engine.py). Este script es para los ~2800 que ya estan.

POR QUE NO REANALIZA EL AUDIO
-----------------------------
No hace falta: los cues que ya tiene el tema dicen donde empieza y termina el
tramo, y el BPM dice cuanto dura un compas. Reanalizar 2800 temas serian horas
de CPU para recalcular algo que la base ya sabe. Lo unico que se pierde es
elegir el respiro adentro del tramo —para eso si hay que escuchar el audio—, asi
que aca el cue va a la frase de 16 compases mas cercana a la mitad.

QUE TOCA DE LA BASE
-------------------
Inserta UN cue nuevo (Kind 5) y mueve el Mix-OUT existente de Kind 5 a Kind 6,
para que las letras sigan el orden del tiempo. No borra ni reescribe ningun otro
cue, y no toca ningun tema cuyo tramo final sea corto.

Sin loops: el cue no lleva OutMsec ni BeatLoopSize (ver CLAUDE.md).

USO
---
    python scripts/cue_medio.py --dry                 # que haria, sin escribir
    python scripts/cue_medio.py --sets 139 140 141    # solo esos sets
    python scripts/cue_medio.py --todo                # toda la biblioteca
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

MIN_TRAMO = 32   # compases; el mismo umbral que el cue engine
FRASE = 16
BORDE = 16
KIND_MEDIO = 5
KIND_MIXOUT_NUEVO = 6
COLOR_MEDIO = 2


def conectar():
    con = sqlcipher3.connect(os.environ["REKORDBOX_DB_PATH"])
    con.execute(f"PRAGMA key='{os.environ['SQLCIPHER_KEY']}'")
    con.execute("PRAGMA cipher_compatibility=4")
    return con


def ids_de_sets(con, nums: list[int]) -> set[str]:
    ids = set()
    for n in nums:
        filas = con.execute(
            "SELECT ID FROM djmdPlaylist WHERE Name LIKE ? AND rb_local_deleted=0",
            (f"{n}.%",)).fetchall()
        if len(filas) != 1:
            print(f"  set {n}: {len(filas)} playlists coinciden, se saltea")
            continue
        ids |= {str(r[0]) for r in con.execute(
            "SELECT ContentID FROM djmdSongPlaylist WHERE PlaylistID=? AND rb_local_deleted=0",
            (filas[0][0],))}
    return ids


def plan(con, content_ids: set[str] | None) -> list[dict]:
    """Que temas necesitan el cue Medio y donde va."""
    filas = con.execute("""
        SELECT c.ID, c.Title, c.BPM, cu.Comment, cu.InMsec, cu.Kind, cu.ID
        FROM djmdContent c JOIN djmdCue cu ON cu.ContentID = c.ID
        WHERE c.rb_local_deleted = 0 AND cu.rb_local_deleted = 0 AND cu.Kind > 0
        ORDER BY c.ID, cu.InMsec""").fetchall()
    por_track: dict[str, dict] = {}
    for cid, titulo, bpm, comment, in_ms, kind, cue_id in filas:
        cid = str(cid)
        if content_ids is not None and cid not in content_ids:
            continue
        t = por_track.setdefault(cid, {"titulo": titulo, "bpm": (bpm or 0) / 100.0, "cues": []})
        t["cues"].append({"nombre": comment or "", "ms": in_ms, "kind": kind, "id": cue_id})

    salida = []
    for cid, t in por_track.items():
        nombres = {c["nombre"]: c for c in t["cues"]}
        if any(c["kind"] == KIND_MEDIO and c["nombre"] == "Medio" for c in t["cues"]):
            continue                                   # ya lo tiene
        mixout = nombres.get("Mix-OUT")
        if not mixout or t["bpm"] <= 0:
            continue
        # el tramo arranca en el DROP, y si no hay, en el Breakdown o el Bass IN
        arranque = nombres.get("DROP") or nombres.get("Breakdown") or nombres.get("Bass IN")
        if not arranque:
            continue
        compas_ms = 60_000 / t["bpm"] * 4
        largo = (mixout["ms"] - arranque["ms"]) / compas_ms
        if largo < MIN_TRAMO:
            continue
        k = round((largo / 2) / FRASE) * FRASE
        k = max(FRASE, min(k, int(largo) - BORDE))
        salida.append({
            "cid": cid, "titulo": t["titulo"], "bpm": t["bpm"],
            "desde": arranque["nombre"], "largo_compases": round(largo),
            "ms": int(arranque["ms"] + k * compas_ms),
            "mixout_cue_id": mixout["id"], "mixout_kind": mixout["kind"],
            "compases_desde_el_drop": k,
        })
    return salida


def escribir(con, tareas: list[dict]) -> int:
    ahora = datetime.now()
    now_str = ahora.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    now_iso = ahora.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
    hechos = 0
    for t in tareas:
        uuid_content = con.execute(
            "SELECT UUID FROM djmdContent WHERE ID=?", (t["cid"],)).fetchone()[0]
        cue_id = str(random.randint(100000000, 999999999))
        # misma forma exacta que usa el cue engine (apply_cues_v8_direct)
        con.execute("""
            INSERT INTO djmdCue (
                ID, ContentID, InMsec, InFrame, InMpegFrame, InMpegAbs,
                OutMsec, OutFrame, OutMpegFrame, OutMpegAbs,
                Kind, Color, ColorTableIndex, ActiveLoop,
                Comment, BeatLoopSize, ContentUUID, UUID,
                rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
                usn, rb_local_usn, created_at, updated_at
            ) VALUES (?,?,?,?,0,0, -1,0,0,0, ?,?,NULL,NULL, 'Medio',NULL,?,?, 0,0,0,0,
                      NULL,NULL,?,?)""",
            (cue_id, t["cid"], t["ms"], int(t["ms"] * 0.150), KIND_MEDIO, COLOR_MEDIO,
             uuid_content, str(uuid_lib.uuid4()), now_str, now_str))
        # el Mix-OUT se corre a F para que las letras sigan el orden del tiempo
        con.execute("UPDATE djmdCue SET Kind=?, updated_at=? WHERE ID=?",
                    (KIND_MIXOUT_NUEVO, now_str, t["mixout_cue_id"]))
        # ContentCue (sin prefijo djmd) guarda el JSON de todos los cues del tema: hay que rehacerlo
        cues = con.execute("""
            SELECT ID, ContentID, InMsec, InFrame, OutMsec, OutFrame, Kind, Color,
                   ContentUUID, UUID, BeatLoopSize, ActiveLoop, Comment
            FROM djmdCue WHERE ContentID=? AND rb_local_deleted=0 ORDER BY InMsec""",
            (t["cid"],)).fetchall()
        payload = [{
            "ID": str(c[0]), "ContentID": str(c[1]), "InMsec": c[2], "InFrame": c[3] or 0,
            "InMpegFrame": 0, "InMpegAbs": 0, "OutMsec": c[4], "OutFrame": c[5] or 0,
            "OutMpegFrame": 0, "OutMpegAbs": 0, "Kind": c[6], "Color": c[7],
            "ContentUUID": c[8], "UUID": c[9], "BeatLoopSize": c[10], "ActiveLoop": c[11],
            "Comment": c[12], "created_at": now_iso, "updated_at": now_iso,
        } for c in cues]
        con.execute("UPDATE ContentCue SET Cues=?, updated_at=? WHERE ContentID=?",
                    (json.dumps(payload), now_str, t["cid"]))
        hechos += 1
    return hechos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--sets", type=int, nargs="*")
    ap.add_argument("--todo", action="store_true")
    ap.add_argument("--limite", type=int, default=0)
    args = ap.parse_args()
    if not (args.sets or args.todo):
        ap.error("elegi --sets N N N o --todo")

    con = conectar()
    objetivo = None if args.todo else ids_de_sets(con, args.sets or [])
    if objetivo is not None:
        print(f"{len(objetivo)} temas en esos sets")
    tareas = plan(con, objetivo)
    if args.limite:
        tareas = tareas[:args.limite]

    print(f"\n{len(tareas)} temas con tramo final de {MIN_TRAMO}+ compases y sin cue Medio\n")
    for t in sorted(tareas, key=lambda x: -x["largo_compases"])[:15]:
        m, s = divmod(t["ms"] // 1000, 60)
        print(f"  {t['largo_compases']:3d} compases desde {t['desde']:10s} "
              f"-> Medio a {m}:{s:02d} (+{t['compases_desde_el_drop']})  {t['titulo'][:44]}")
    if len(tareas) > 15:
        print(f"  ... y {len(tareas) - 15} mas")

    if args.dry:
        print("\n--dry: no se escribio nada")
        return
    n = escribir(con, tareas)
    con.commit()
    print(f"\n{n} cues Medio escritos. El Mix-OUT de esos temas paso de E a F.")
    print("Abri Rekordbox y hace sync al pen.")


if __name__ == "__main__":
    main()
