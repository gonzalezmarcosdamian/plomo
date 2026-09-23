# -*- coding: utf-8 -*-
"""Chequea que cada lista de Spotify diga exactamente lo que dice el set.

POR QUE
-------
"Muy mal, estan en Spotify": el DJ encontro un tema que el script reporto como
ausente y estaba. Un matcheo que falla en silencio es peor que uno que falla
fuerte, porque la lista queda incompleta y nadie se entera hasta que alguien la
escucha.

Esto no confia en el resultado del sync: lee lo que QUEDO en Spotify y lo
compara contra el target del set, URI por URI y en orden. Para cada tema que
falta, ademas, busca el nucleo del titulo a mano y avisa si existe igual: esa es
la diferencia entre "no esta en Spotify" y "mi buscador no lo encontro".

USO
---
    python scripts/spotify_validar.py 139 140 141 142 143 144 145 146 147
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
sys.path.insert(0, str(RAIZ / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import spotify_sync as S  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("nums", type=int, nargs="+")
    args = ap.parse_args()

    tok = S.acceso()
    h = {"Authorization": f"Bearer {tok}"}
    yo = requests.get(S.API + "/me", headers=h, timeout=20).json()["id"]
    cache = json.loads((RAIZ / "data/spotify_matches.json").read_text(encoding="utf-8"))

    # las listas del usuario, por nombre
    listas, off = {}, 0
    while True:
        r = requests.get(S.API + "/me/playlists", headers=h,
                         params={"limit": 50, "offset": off}, timeout=20).json()
        for pl in r["items"]:
            if pl["owner"]["id"] == yo:
                listas[pl["name"]] = pl["id"]
        if not r.get("next"):
            break
        off += 50

    todo_ok = True
    for num in args.nums:
        f = RAIZ / "data" / "set_targets" / f"set_{num}.json"
        doc = json.loads(f.read_text(encoding="utf-8"))
        pid = listas.get(doc["name"])
        if not pid:
            print(f"set {num}: NO existe la lista en Spotify")
            todo_ok = False
            continue
        items = requests.get(f"{S.API}/playlists/{pid}/items", headers=h,
                             params={"limit": 100}, timeout=20).json()["items"]
        en_spotify = [(i.get("track") or i.get("item") or {}).get("uri") for i in items]
        problemas = []
        for n, t in enumerate(doc["tracks"]):
            esperado = (cache.get(t["content_id"]) or {}).get("uri")
            real = en_spotify[n] if n < len(en_spotify) else None
            if esperado is None:
                # el sync no lo encontro: chequear a mano si existe igual
                nucleo = S.PARENTESIS.sub("", t["title"]).strip(" -")
                res = requests.get(S.API + "/search", headers=h,
                                   params={"q": nucleo, "type": "track", "limit": 5},
                                   timeout=20).json()["tracks"]["items"]
                mejor = max((S.parecido(t["title"], x["name"]) * 0.6
                             + max(S.parecido(t["artist"], a["name"]) for a in x["artists"]) * 0.4,
                             x) for x in res) if res else (0, None)
                if mejor[0] >= 0.62:
                    problemas.append(f"#{n+1} {t['artist'][:18]} - {t['title'][:30]}  "
                                     f"SI ESTA en Spotify como: {mejor[1]['artists'][0]['name']} - "
                                     f"{mejor[1]['name']}")
                else:
                    problemas.append(f"#{n+1} {t['artist'][:18]} - {t['title'][:30]}  "
                                     f"no esta (el mas parecido da {mejor[0]:.2f})")
            elif real != esperado:
                problemas.append(f"#{n+1} fuera de orden o cambiado: {t['title'][:38]}")
        estado = "OK" if not problemas else f"{len(problemas)} problemas"
        print(f"  set {num}: {len(en_spotify):2d}/{len(doc['tracks']):2d} temas   {estado}")
        for x in problemas:
            print(f"      {x}")
        todo_ok &= not problemas

    print("\n" + ("todas las listas dicen exactamente lo que dice su set"
                  if todo_ok else "hay listas que no coinciden"))
    sys.exit(0 if todo_ok else 1)


if __name__ == "__main__":
    main()
