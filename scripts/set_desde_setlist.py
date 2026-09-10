"""Reconstruye un setlist de referencia como set propio, en el orden original.

No es lo mismo que armar un set: aca no se elige nada. Se toma la secuencia de
otro DJ y se escribe con los tracks que SI estan en la biblioteca, respetando el
orden y dejando el hueco donde falta material. Sirve para escucharla en el CDJ y
para ver de que tamano es el hueco.

Los tracks se cruzan por titulo + remixer, no por artista: cada fuente escribe el
artista distinto ("HANA, Ezequiel Arias" vs "Ezequiel Arias") y por ese lado se
pierde un tercio de los matches.

Uso:
    python scripts/set_desde_setlist.py data/setlists/x.json --num 100
    python scripts/set_desde_setlist.py data/setlists/x.json --num 100 --dry
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from plomo.matching import clave, GENERICOS  # noqa: E402

_P = re.compile(r"[(\[]([^)\]]*)[)\]]")
_N = re.compile(r"[^a-z0-9]")


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()


def clave_titulo(titulo: str) -> str:
    manos = []
    for tramo in _P.findall(titulo or ""):
        manos += [p for p in _N.sub(" ", _ascii(tramo).lower()).split()
                  if p and p not in GENERICOS]
    return _N.sub("", _ascii(_P.sub("", titulo or "")).lower()) + "".join(sorted(set(manos)))


def base_titulo(titulo: str) -> str:
    """Solo el titulo, sin el parentesis. 'Movin Thru (Cattaneo Remix)' -> movinthru."""
    return _N.sub("", _ascii(_P.sub("", titulo or "")).lower())


def tokens(s: str) -> set[str]:
    return {p for p in _N.sub(" ", _ascii(s).lower()).split() if len(p) > 2}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("setlist", type=Path)
    ap.add_argument("--num", type=int, required=True)
    ap.add_argument("--nombre", help="nombre del set; por defecto se arma del setlist")
    ap.add_argument("--carpeta", default=None)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    doc = json.loads(args.setlist.read_text(encoding="utf-8"))
    pool = json.loads((RAIZ / "data" / "pool.json").read_text(encoding="utf-8"))
    por_clave = {clave(t["artist"], t["title"]): t for t in pool}
    por_titulo: dict[str, dict] = {}
    por_base: dict[str, list[dict]] = {}
    for t in pool:
        por_titulo.setdefault(clave_titulo(t["title"]), t)
        por_base.setdefault(base_titulo(t["title"]), []).append(t)

    tracks, faltan, huecos = [], [], 0
    for t in doc["tracks"]:
        if t.get("es_id") or t["title"].strip().lower() == "id":
            huecos += 1
            continue
        m = por_clave.get(clave(t["artist"], t["title"])) or por_titulo.get(clave_titulo(t["title"]))
        if not m:
            # Ultimo intento: el remixer puede estar en el campo ARTISTA y no en
            # el titulo ("Jark Prongo, Hernan Cattaneo, ... - Movin Thru Your
            # System (Extended Mix)"), asi que el titulo con remixer no matchea.
            # Se cruza por titulo pelado y se confirma con el artista.
            b = base_titulo(t["title"])
            if len(b) >= 6:
                cands = por_base.get(b, [])
                objetivo = tokens(t["artist"]) | tokens(t["title"])
                for c in cands:
                    if tokens(c["artist"]) & objetivo:
                        m = c
                        break
        if m:
            tracks.append({"artist": m["artist"], "title": m["title"], "content_id": m["id"]})
        else:
            faltan.append(f"{t['artist']} - {t['title']}")

    nombre = args.nombre or (f"{args.num}. {doc.get('dj','?')} — "
                             f"{doc.get('evento','?')} — {doc.get('fecha','')}")
    bpms = [x["bpm"] for x in pool if x["id"] in {t["content_id"] for t in tracks}]
    target = {
        "name": nombre,
        "_identidad": (f"Reconstruccion del set real de {doc.get('dj')} en "
                       f"{doc.get('evento')} ({doc.get('fecha')}), en el orden que lo toco. "
                       f"Fuente: {doc.get('fuente','')}"),
        "duration_h": round(len(tracks) * 5.5 / 60, 1),
        "bpm_range": [int(min(bpms)), int(max(bpms))] if bpms else [0, 0],
        "max_per_artist": 99,
        "keep_order": True,
        "tracks": tracks,
    }
    if args.carpeta:
        target["carpeta"] = args.carpeta

    print(f"{nombre}")
    print(f"  {len(tracks)} de {len(doc['tracks'])} posiciones "
          f"({huecos} eran ID sin identificar, {len(faltan)} no estan en la biblioteca)")
    for f in faltan:
        print(f"    falta: {f}")
    if args.dry:
        print("  [dry] no se escribio el target")
        return
    out = RAIZ / "data" / "set_targets" / f"set_{args.num}.json"
    out.write_text(json.dumps(target, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {out.relative_to(RAIZ)}   (ahora: build_set.py {args.num})")


if __name__ == "__main__":
    main()
