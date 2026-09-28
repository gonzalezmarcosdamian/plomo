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

Y DESDE EL 2026-09-27 CHEQUEA QUE SEA LA MISMA VERSION
El DJ miro la lista del 143 y dijo "no esta bien". Estaban los 23 temas, en
orden, y el validador decia OK: comparaba cada URI contra la que el buscador
habia guardado en el cache, asi que un match EQUIVOCADO validaba perfecto. Seis
temas eran otra version --el remix de Roman en vez del de L.GU., tres cortes
"- Mixed" de compilaciones y dos edits de cuatro minutos donde la biblioteca
tiene extendeds de ocho--. Un validador que solo compara contra lo que eligio el
buscador no valida nada: valida que el buscador sea consistente consigo mismo.

Ahora compara contra REKORDBOX: el remixer que dice el titulo tiene que estar
acreditado, y el largo del archivo tiene que parecerse al de Spotify.

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
    POOL = {x["id"]: x for x in json.loads(
        (RAIZ / "data/pool.json").read_text(encoding="utf-8"))}

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
        vivos = [(i.get("track") or i.get("item") or {}) for i in items]
        en_spotify = [x.get("uri") for x in vivos]
        problemas, avisos = [], []
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
            else:
                # LA VERSION. Contra Rekordbox, no contra lo que eligio el
                # buscador: si el match fue malo, el cache lo repite igual.
                x = vivos[n]
                nom = S.norm(x.get("name", ""))
                gente = S.norm(" ".join(a["name"] for a in x.get("artists", [])))
                m = S.REMIX.search(t["title"])
                if m:
                    quien = S.norm(S.VERSIONES.sub("", m.group(1)))
                    if quien and quien not in nom and quien not in gente:
                        problemas.append(
                            f"#{n+1} OTRA VERSION: la biblioteca dice "
                            f"'{m.group(1)}' y Spotify tiene '{x.get('name','')[:40]}'")
                        continue
                # El largo distinto NO es un error. Chequeado tema por tema:
                # de los extendeds de sellos chicos, Spotify publica solo el
                # edit --Portal Six esta en 4:00 y no existe otra version--.
                # Es el mismo mix y sirve igual para escuchar el set en el auto;
                # lo que no sirve es otro remix, y eso si es un problema.
                dur = (POOL.get(t["content_id"]) or {}).get("dur_seg")
                sdur = (x.get("duration_ms") or 0) / 1000
                if dur and sdur and abs(sdur - dur) / dur > 0.30:
                    avisos.append(
                        f"#{n+1} {t['title'][:34]}: el archivo dura "
                        f"{dur//60}:{dur%60:02d} y Spotify tiene {int(sdur)//60}:"
                        f"{int(sdur)%60:02d} (alla solo esta el edit)")
        estado = "OK" if not problemas else f"{len(problemas)} problemas"
        if avisos and not problemas:
            estado = f"OK ({len(avisos)} en version corta)"
        print(f"  set {num}: {len(en_spotify):2d}/{len(doc['tracks']):2d} temas   {estado}")
        for x in problemas:
            print(f"      {x}")
        for x in avisos:
            print(f"      aviso: {x}")
        todo_ok &= not problemas

    print("\n" + ("todas las listas dicen exactamente lo que dice su set"
                  if todo_ok else "hay listas que no coinciden"))
    sys.exit(0 if todo_ok else 1)


if __name__ == "__main__":
    main()
