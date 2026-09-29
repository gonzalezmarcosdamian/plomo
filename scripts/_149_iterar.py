# -*- coding: utf-8 -*-
"""Reescribe el 149 cambiando el que abre y el del levante, y manda Silver Lily al 5.

Parte de los content_id que YA estan en set_149.json y nunca resuelve por nombre:
buscar "Amnesia" por substring trae la Mike Isai en vez de la Fuenka, y
"Fading Silhouettes" trae la Fabri Lopez en vez de la Pierre Sebastiano. Los dos
temas suenan distinto y la lista quedaria diciendo otra cosa que el set.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ABRE_VIEJO = "6719392"       # Wailey - Droplets (Taylan Remix)
LEVANTE_VIEJO = "216332867"  # Dmitry Molosh - The Moon Lights the Way
SILVER_LILY = "80536228"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--abre", required=True, help="content_id del tema que abre")
    ap.add_argument("--levante", required=True, help="content_id del tema del levante")
    ap.add_argument("--nota", default="")
    args = ap.parse_args()

    pool = {str(t["id"]): t for t in json.loads(
        (RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
    f = RAIZ / "data/set_targets/set_149.json"
    doc = json.loads(f.read_text(encoding="utf-8"))
    ids = [str(t["content_id"]) for t in doc["tracks"]]

    for viejo, nuevo in ((ABRE_VIEJO, args.abre), (LEVANTE_VIEJO, args.levante)):
        if viejo not in ids:
            sys.exit(f"{viejo} no esta en el 149 — el set cambio, revisar antes de escribir")
        if nuevo not in pool:
            sys.exit(f"{nuevo} no esta en la biblioteca")
        ids[ids.index(viejo)] = nuevo

    # Silver Lily al 5: es lo mas adelante que entra sin romper la subida.
    ids.remove(SILVER_LILY)
    ids.insert(4, SILVER_LILY)

    doc["tracks"] = [{"artist": pool[c]["artist"], "title": pool[c]["title"],
                      "content_id": c} for c in ids]
    if args.nota:
        doc["_nota"] = doc.get("_nota", "") + " | " + args.nota
    f.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    tot = sum(pool[c]["dur_seg"] for c in ids)
    p = tot * 0.93
    prev = None
    print(f"{'#':>2}  {'tema':<52} {'key':>4} {'E':>4} {'min':>5} {'pasoE':>6}")
    for i, c in enumerate(ids, 1):
        t = pool[c]
        paso = "" if prev is None else f"{t['energy'] - prev:+.1f}"
        prev = t["energy"]
        print(f"{i:>2}  {t['artist'] + ' - ' + t['title']:<52.52} "
              f"{t['key']:>4} {t['energy']:>4.1f} {t['dur_seg']/60:>5.1f} {paso:>6}")
    print(f"\n{len(ids)} temas -> {int(p//3600)}h{int((p%3600)//60):02d} tocado")


if __name__ == "__main__":
    main()
