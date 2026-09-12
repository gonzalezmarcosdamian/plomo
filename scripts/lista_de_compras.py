"""Que falta comprar, segun lo que los DJs de referencia tocan de verdad.

El radar de sellos y el escaneo por artista dicen que SALIO. Esto dice otra cosa:
que se ESTA TOCANDO. Cruza los setlists reales de `data/setlists/` contra la
biblioteca y ordena lo que falta por cuantas veces aparece y en cuantos sets
distintos — un tema que tocaron cuatro DJs distintos pesa mas que uno que toco
uno solo cuatro veces.

Saca tres cosas:
  1. TEMAS   - los que faltan y estan confirmados en Muzpa, en formato batch.
  2. ARTISTAS - quien aparece mucho en los sets y poco en la biblioteca.
  3. SELLOS  - lo mismo por sello, para el radar fijo.

Uso:
    python scripts/lista_de_compras.py
    python scripts/lista_de_compras.py --min-djs 2
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from plomo.matching import clave, GENERICOS  # noqa: E402

_P = re.compile(r"[(\[]([^)\]]*)[)\]]")
_N = re.compile(r"[^a-z0-9]")
SEPS = (",", "&", " feat", " ft", " vs", " x ", " and ")


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()


def base_titulo(t: str) -> str:
    return _N.sub("", _ascii(_P.sub("", t or "")).lower())


def tokens(s: str) -> set[str]:
    return {p for p in _N.sub(" ", _ascii(s).lower()).split() if len(p) > 2}


def artistas(campo: str) -> list[str]:
    partes = [campo or ""]
    for sep in SEPS:
        partes = [p for ch in partes for p in ch.split(sep)]
    out = []
    for p in partes:
        p = re.sub(r"\(.*?\)", "", p).strip()
        if len(p) > 2:
            out.append(p)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-djs", type=int, default=1,
                    help="minimo de DJs distintos que lo tocaron")
    ap.add_argument("--bpm", nargs=2, type=float, metavar=("MIN", "MAX"),
                    help="descartar lo que caiga fuera del rango (sin BPM no entra)")
    args = ap.parse_args()

    pool = json.loads((RAIZ / "data" / "pool.json").read_text(encoding="utf-8"))
    por_clave = {clave(t["artist"], t["title"]) for t in pool}
    por_base: dict[str, list[dict]] = defaultdict(list)
    for t in pool:
        por_base[base_titulo(t["title"])].append(t)
    art_lib = Counter()
    for t in pool:
        for a in artistas(t["artist"]):
            art_lib[a.lower()] += 1
    sello_lib = Counter((t.get("label") or "").lower() for t in pool)

    def en_biblioteca(t: dict) -> bool:
        if clave(t["artist"], t["title"]) in por_clave:
            return True
        b = base_titulo(t["title"])
        if len(b) < 4:
            return False
        obj = tokens(t["artist"]) | tokens(t["title"])
        return any(tokens(c["artist"]) & obj for c in por_base.get(b, []))

    faltan: dict[str, dict] = {}
    art_ref, art_djs = Counter(), defaultdict(set)
    sello_ref = Counter()
    n_sets = 0
    for f in sorted((RAIZ / "data" / "setlists").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        dj = d.get("dj", "?")
        n_sets += 1
        for t in d["tracks"]:
            if t.get("es_id") or (t.get("title") or "").strip().lower() == "id":
                continue
            for a in artistas(t["artist"]):
                art_ref[a.lower()] += 1
                art_djs[a.lower()].add(dj)
            if t.get("label"):
                sello_ref[t["label"].lower()] += 1
            if en_biblioteca(t):
                continue
            k = clave(t["artist"], t["title"])
            e = faltan.setdefault(k, {"artist": t["artist"], "title": t["title"],
                                      "veces": 0, "djs": set(), "bpm": None,
                                      "key": None, "muzpa": ""})
            e["veces"] += 1
            e["djs"].add(dj)
            e["bpm"] = e["bpm"] or t.get("bpm")
            e["key"] = e["key"] or t.get("key")
            e["muzpa"] = e["muzpa"] or t.get("muzpa_fullname", "")

    print(f"{n_sets} setlists de referencia | {len(faltan)} temas que no estan en la biblioteca\n")

    conf = [e for e in faltan.values()
            if e["muzpa"] and len(e["djs"]) >= args.min_djs]
    if args.bpm:
        # Un corpus de 40 sets de tres horas roza drum & bass, trance y cierres
        # a 147 BPM. El rango es el filtro de estilo mas barato que hay, y sin
        # BPM el track no se puede ubicar: queda afuera y se avisa.
        lo, hi = args.bpm
        fuera = [e for e in conf if not e["bpm"] or not (lo <= e["bpm"] <= hi)]
        conf = [e for e in conf if e["bpm"] and lo <= e["bpm"] <= hi]
        print(f"(filtro BPM {lo:.0f}-{hi:.0f}: quedaron {len(conf)}, "
              f"se descartaron {len(fuera)})\n")
    conf.sort(key=lambda e: (-len(e["djs"]), -e["veces"], e["artist"]))
    sin_muzpa = [e for e in faltan.values() if not e["muzpa"]]

    print("=== TEMAS confirmados en Muzpa y ausentes de la biblioteca ===")
    for e in conf[:25]:
        print(f"  {len(e['djs'])} DJs x{e['veces']:<2} | {e['artist'][:26]} - {e['title'][:38]}"
              f"  ({e['bpm']} {e['key']})")
    if len(conf) > 25:
        print(f"  ... y {len(conf)-25} mas")

    print("\n=== ARTISTAS que se tocan y casi no tenemos ===")
    filas = [(a, n, len(art_djs[a]), art_lib.get(a, 0))
             for a, n in art_ref.items() if art_lib.get(a, 0) <= 2 and n >= 2]
    filas.sort(key=lambda r: (-r[2], -r[1]))
    for a, n, djs, lib in filas[:20]:
        print(f"  {djs} DJs, {n:>2} apariciones, {lib} en biblioteca | {a}")

    print("\n=== SELLOS del corpus ===")
    for s, n in sello_ref.most_common(15):
        print(f"  {n:>3} apariciones, {sello_lib.get(s,0):>3} en biblioteca | {s}")

    dest = RAIZ / "data" / f"batch_referencia_{date.today()}.txt"
    L = [f"# Lo que tocan los DJs de referencia y no esta en la biblioteca",
         f"# {n_sets} setlists en data/setlists/ | {len(conf)} temas confirmados en Muzpa",
         f"# Ordenado por cuantos DJs distintos lo tocaron, despues por cuantas veces.", ""]
    for e in conf:
        L.append(f"{e['artist']} - {e['title']}   # {len(e['djs'])}DJs x{e['veces']} "
                 f"{e['bpm']} {e['key']}")
    if sin_muzpa:
        L += ["", f"# No confirmados en Muzpa ({len(sin_muzpa)}) — edits, inéditos o mal escritos:"]
        L += [f"#   {e['artist']} - {e['title']}" for e in
              sorted(sin_muzpa, key=lambda x: -x["veces"])[:60]]
    dest.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\n-> {dest.relative_to(RAIZ)}  ({len(conf)} para bajar)")


if __name__ == "__main__":
    main()
