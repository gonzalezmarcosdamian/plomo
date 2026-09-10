"""Convierte un setlist de referencia en un set propio, con el material que hay.

Hay dos productos distintos y confundirlos arruina los dos:

  --modo fiel     La secuencia real, con los tracks que estan en la biblioteca y
                  nada mas. Cuando falta la mitad de las posiciones, dos tracks
                  que en la noche estaban a veinte minutos quedan pegados: el
                  resultado NO se mezcla, se estudia. El nombre lo dice.

  --modo tocable  (default) Los tracks reales del setlist se usan como ANCLAS y
                  el solver arma alrededor de ellos con el resto de la
                  biblioteca, respetando Camelot, BPM y arco de energia. Ya no es
                  la secuencia de ese DJ: es un set propio hecho con su material.

Lo que costo aprender: la primera version reconstruia el set de Simon Vuarambon
conservando 32 de 59 posiciones y salieron 29 transiciones flojas de 31 —saltos
de media rueda de Camelot y de 11 BPM— porque la mitad de los puentes reales
faltaba. Un setlist al que le sacaste la mitad no es ese setlist.

El cruce contra la biblioteca EXIGE que el artista confirme. Sin eso,
"Julian Jeweil - Mars" matcheaba con "Simon Vuarambon - Mars" y el set se comia
un track de otra tonalidad sin avisar.

Uso:
    python scripts/set_desde_setlist.py data/setlists/x.json --num 100
    python scripts/set_desde_setlist.py data/setlists/x.json --num 100 --modo fiel
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from plomo.matching import clave, GENERICOS  # noqa: E402
from select_set import select, camelot  # noqa: E402

_P = re.compile(r"[(\[]([^)\]]*)[)\]]")
_N = re.compile(r"[^a-z0-9]")


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()


def clave_titulo(titulo: str) -> str:
    manos = []
    for tramo in _P.findall(titulo or ""):
        manos += [p for p in _N.sub(" ", _ascii(tramo).lower()).split()
                  if p and p not in GENERICOS]
    base = _N.sub("", _ascii(_P.sub("", titulo or "")).lower())
    return base + "".join(sorted(set(manos)))


def base_titulo(titulo: str) -> str:
    return _N.sub("", _ascii(_P.sub("", titulo or "")).lower())


def tokens(s: str) -> set[str]:
    return {p for p in _N.sub(" ", _ascii(s).lower()).split() if len(p) > 2}


def resolver(t: dict, por_clave: dict, por_base: dict) -> dict | None:
    """El track del setlist en la biblioteca, o None. El artista SIEMPRE confirma."""
    m = por_clave.get(clave(t["artist"], t["title"]))
    if m:
        return m
    b = base_titulo(t["title"])
    if len(b) < 4:
        return None
    objetivo = tokens(t["artist"]) | tokens(t["title"])
    exacto, aproximado = None, None
    for c in por_base.get(b, []):
        # sin confirmacion del artista no entra, punto: por ahi se colaba
        # "Simon Vuarambon - Mars" cuando el setlist decia "Julian Jeweil - Mars"
        if not (tokens(c["artist"]) & objetivo):
            continue
        if clave_titulo(c["title"]) == clave_titulo(t["title"]):
            exacto = exacto or c
        else:
            aproximado = aproximado or c
    return exacto or aproximado


def anclas_del_setlist(doc: dict, por_clave: dict, por_base: dict):
    anclas, faltan, huecos = [], [], 0
    vistos = set()
    for t in doc["tracks"]:
        if t.get("es_id") or t["title"].strip().lower() == "id":
            huecos += 1
            continue
        m = resolver(t, por_clave, por_base)
        if not m:
            faltan.append(f"{t['artist']} - {t['title']}")
            continue
        if m["id"] not in vistos:
            vistos.add(m["id"])
            anclas.append(m)
    return anclas, faltan, huecos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("setlist", type=Path)
    ap.add_argument("--num", type=int, required=True)
    ap.add_argument("--nombre")
    ap.add_argument("--modo", choices=["tocable", "fiel"], default="tocable")
    ap.add_argument("--n", type=int, help="cantidad de tracks en modo tocable")
    ap.add_argument("--carpeta")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    doc = json.loads(args.setlist.read_text(encoding="utf-8"))
    pool = json.loads((RAIZ / "data" / "pool.json").read_text(encoding="utf-8"))
    por_clave = {clave(t["artist"], t["title"]): t for t in pool}
    por_base: dict[str, list[dict]] = {}
    for t in pool:
        por_base.setdefault(base_titulo(t["title"]), []).append(t)

    anclas, faltan, huecos = anclas_del_setlist(doc, por_clave, por_base)
    dj = doc.get("dj", "?")
    ev = doc.get("evento", "?")
    fe = doc.get("fecha", "")
    print(f"\n{args.setlist.name}")
    print(f"  {len(anclas)} anclas reales | {huecos} posiciones eran ID | "
          f"{len(faltan)} no estan en la biblioteca")

    if args.modo == "fiel":
        tracks = [{"artist": a["artist"], "title": a["title"], "content_id": a["id"]}
                  for a in anclas]
        nombre = args.nombre or f"{args.num}. {dj} - {ev} - {fe} [ESTUDIO, no mezclar]"
        ident = (f"La secuencia real de {dj} en {ev}, con los {len(anclas)} tracks que hay "
                 f"de {len(doc['tracks'])} posiciones. Faltan {huecos + len(faltan)} puentes: "
                 f"NO se mezcla como esta, se escucha para estudiar el orden.")
    else:
        ancla_ids = {a["id"] for a in anclas}
        es = sorted(a["energy"] for a in anclas if a.get("energy"))
        bs = sorted(a["bpm"] for a in anclas if a.get("bpm"))
        if not es or not bs:
            sys.exit("las anclas no tienen energia/BPM — corre backfill_energy.py")
        lo = es[len(es) // 10]
        hi = es[-max(1, len(es) // 10)]
        bmin = bs[len(bs) // 10]
        bmax = bs[-max(1, len(bs) // 10)]
        # Los generos NO se eligen a mano: son los que trae el propio setlist.
        # Sin este filtro los puentes los pone la biblioteca entera y entra house
        # comercial y latin house en un set de melodic techno.
        # Pero tampoco sirve tomarlos todos: un set de tres horas roza generos
        # sueltos —un drum & bass, un trance— y por esa puerta entra cualquier
        # cosa. Se toman los que cubren el 80% de las anclas y nada mas.
        cuenta = Counter((a.get("genre") or "").lower() for a in anclas if a.get("genre"))
        generos, acum = set(), 0
        for g, c in cuenta.most_common():
            if acum >= 0.8 * sum(cuenta.values()):
                break
            generos.add(g)
            acum += c
        cand = [t for t in pool
                if t.get("energy") and t.get("bpm") and camelot(t["key"])
                and bmin - 1 <= t["bpm"] <= bmax + 1
                and lo - 0.8 <= t["energy"] <= hi + 0.8
                and (not generos or (t.get("genre") or "").lower() in generos)]
        print(f"  generos del setlist: {', '.join(sorted(generos)) or '(ninguno)'}")
        n = args.n or min(len(anclas), 20)
        # bonus alto a proposito: el solver tiene que preferir el material real
        # del DJ y recurrir a la biblioteca solo donde el puente no existe.
        best = select(cand, n, lo, hi, max_bpm_jump=2.0,
                      prefer=ancla_ids, bonus=25.0, max_per_artist=2, beam=3000)
        if not best:
            sys.exit("sin solucion — ampliar el rango o bajar --n")
        seq = best[1]
        usadas = sum(1 for t in seq if t["id"] in ancla_ids)
        print(f"  -> {n} tracks: {usadas} del setlist real, {n - usadas} de la biblioteca")
        for i, t in enumerate(seq, 1):
            mk = "*" if t["id"] in ancla_ids else " "
            print(f"   {i:>2}{mk} E{t['energy']:.1f} {t['bpm']:.0f} {t['key']:>3} | "
                  f"{t['artist'][:22]} - {t['title'][:38]}")
        tracks = [{"artist": t["artist"], "title": t["title"], "content_id": t["id"]}
                  for t in seq]
        nombre = args.nombre or f"{args.num}. Con el material de {dj} - {ev} - {fe}"
        ident = (f"Set propio armado con el material que {dj} toco en {ev} ({fe}) como anclas: "
                 f"{usadas} de {n} tracks salen de ese setlist y el resto son puentes de la "
                 f"biblioteca. NO es la secuencia de ese DJ.")

    for f in faltan:
        print(f"    falta: {f}")

    ids = {x["content_id"] for x in tracks}
    bpms = [t["bpm"] for t in pool if t["id"] in ids]
    target = {
        "name": nombre,
        "_identidad": ident,
        "_fuente": doc.get("fuente", ""),
        "duration_h": round(len(tracks) * 5.5 / 60, 1),
        "bpm_range": [int(min(bpms)), int(max(bpms))] if bpms else [0, 0],
        "max_per_artist": 99,
        "keep_order": True,
        "tracks": tracks,
    }
    if args.carpeta:
        target["carpeta"] = args.carpeta
    if args.dry:
        print("  [dry] no se escribio el target")
        return
    out = RAIZ / "data" / "set_targets" / f"set_{args.num}.json"
    out.write_text(json.dumps(target, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {out.relative_to(RAIZ)}   "
          f"(ahora: build_set.py {args.num} && audit_sets.py {args.num})")


if __name__ == "__main__":
    main()
