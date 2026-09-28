# -*- coding: utf-8 -*-
"""Rearma el 148 manteniendo lo que el DJ ya aprobo.

POR QUE
-------
"Iterame la lista que la voy a volver a escuchar, no saques los que destaque y
sabes que son favoritos" (el DJ, 2026-09-28). Una iteracion no es un set nuevo:
los temas que el ya escucho y aprobo son lo unico del set que tiene veredicto, y
sacarlos tira justamente la informacion que costo conseguir.

Asi que los favoritos que ya estan en el set entran FIJOS, y se rearma el resto.

QUE PIDE PARA LOS QUE ENTRAN
----------------------------
    color >= --color         el brillo, que es lo que el DJ viene pidiendo
    techo >= 15.5 y piso <= 78% de la media    el groove de Ipanema

El segundo es `estilo.groove_del_dj`, todavia una PROPUESTA: sale de tres casos
suyos --Ipanema y Fogbows si, Milo no-- y lo que la puede refutar son sus
veredictos sobre temas que la regla no vio.

USO
---
    python scripts/iterar_148.py --dry
    python scripts/iterar_148.py --num 148 --color 0.55
"""
from __future__ import annotations

import argparse
import heapq
import json
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import select_set as S  # noqa: E402
from plomo.camelot import distance as cam  # noqa: E402

LIB = RAIZ / "data/recetas/lib"
GEN = {"Progressive House", "House", "Melodic House & Techno"}


def secciones(cid: str) -> list[float] | None:
    f = LIB / f"{cid}.json"
    if not f.exists():
        return None
    ref = json.loads(f.read_text(encoding="utf-8"))["referencia"]
    d = [x["densidad"] for x in (ref.get("secciones") or [])]
    return d if len(d) >= 3 else None


def groove_ok(cid: str) -> bool:
    """El groove que el DJ aprobo: pega fuerte arriba y vacia de verdad abajo."""
    d = secciones(cid)
    return bool(d) and max(d) >= 15.5 and min(d) / (sum(d) / len(d)) <= 0.78


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--num", type=int, default=148)
    ap.add_argument("--n", type=int, default=17)
    ap.add_argument("--color", type=float, default=0.55)
    ap.add_argument("--solo-publicables", action="store_true",
                    help="solo temas con URI de Spotify ya resuelta")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    POOL = {t["id"]: t for t in json.loads((RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
    COL = json.loads((RAIZ / "data/groove_index.json").read_text(encoding="utf-8"))["color_pct"]
    P = json.loads((RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8"))
    cache = json.loads((RAIZ / "data/spotify_matches.json").read_text(encoding="utf-8"))
    dic = lambda c: P.get(c) if isinstance(P.get(c), dict) else {}          # noqa: E731
    VET = {k for k, v in P.items() if isinstance(v, dict) and v.get("veto")}
    GAST = {k for k, v in P.items() if isinstance(v, dict) and v.get("gastado")}

    destino = RAIZ / "data/set_targets" / f"set_{args.num}.json"
    doc = json.loads(destino.read_text(encoding="utf-8"))
    actuales = [t["content_id"] for t in doc["tracks"]]
    fijos = [c for c in actuales if dic(c).get("favorito")]

    def E(c):
        return dic(c).get("E", POOL[c]["energy"])

    def enlaza(a, b):
        return (cam(POOL[a]["key"], POOL[b]["key"]) <= 2
                and abs(POOL[a]["bpm"] - POOL[b]["bpm"]) <= 3.0)

    extra = [c for c, t in POOL.items()
             if c not in fijos and c not in VET and c not in GAST
             and 119 <= t["bpm"] <= 127 and t.get("genre") in GEN
             and COL.get(c, 0) >= args.color and groove_ok(c)
             and (not args.solo_publicables or (cache.get(c) or {}).get("uri"))]
    cands = fijos + extra
    print(f"fijos (favoritos que ya estaban): {len(fijos)}")
    print(f"candidatos nuevos: {len(extra)}"
          + ("  (solo los publicables en Spotify hoy)" if args.solo_publicables else ""))

    N = args.n
    E_INI, PICO, TOL = 5.8, 0.80, 0.9

    def arco(i):
        t = i / (N - 1)
        if t <= PICO:
            return E_INI + (8.0 - E_INI) * (t / PICO)
        return 8.0 - (8.0 - 7.4) * ((t - PICO) / (1 - PICO))

    def costo(seq, c):
        k = max(0.0, abs(E(c) - arco(len(seq))) - TOL) * 3.0
        if seq:
            p = seq[-1]
            k += cam(POOL[p]["key"], POOL[c]["key"]) * 0.8
            k += abs(POOL[p]["bpm"] - POOL[c]["bpm"]) * 0.4
            if E(c) < E(p) - 0.15 and len(seq) >= 2 and E(p) < E(seq[-2]) - 0.15:
                k += 3.0
        k -= COL.get(c, 0.5) * 2.5
        if c in fijos:
            k -= 2.0
        return k

    estados = [(0.0, [], frozenset(), frozenset())]
    for paso in range(N):
        sig, quedan, ultimo = [], N - paso, paso == N - 1
        for k, seq, usados, arts in estados:
            faltan = len([c for c in fijos if c not in usados])
            for c in cands:
                if c in usados:
                    continue
                nom = S.names(POOL[c]["artist"], POOL[c]["title"])
                if nom & arts:
                    continue
                if ultimo and E(c) < 7.2:
                    continue
                if seq and not enlaza(seq[-1], c):
                    continue
                if faltan - (1 if c in fijos else 0) > quedan - 1:
                    continue
                sig.append((k + costo(seq, c), seq + [c], usados | {c}, arts | nom))
        if not sig:
            sys.exit(f"SIN SOLUCION en el paso {paso + 1}")
        estados = heapq.nsmallest(3000, sig, key=lambda x: x[0])
    mejor = next((s for _, s, u, _ in estados if all(c in u for c in fijos)), None)
    if mejor is None:
        sys.exit("no entraron todos los favoritos")

    es = [E(c) for c in mejor]
    peor = run = 0
    for i in range(1, len(es)):
        run = run + 1 if es[i] < es[i - 1] - 0.15 else 0
        peor = max(peor, run)
    for i, c in enumerate(mejor, 1):
        t = POOL[c]
        d = secciones(c) or [1]
        marca = "  <- lo dijiste SI" if c in fijos else ("  <- NUEVO" if c not in actuales else "")
        print(f"{i:2d}. E{E(c):4.1f} {t['bpm']:5.1f} {t['key']:>3s} col{COL.get(c, 0):.2f} "
              f"piso{min(d) / (sum(d) / len(d)):4.0%} {(t.get('label') or '?')[:14]:14s} "
              f"{t['artist'][:20]:20s} - {t['title'][:28]}{marca}")
    dur = sum(POOL[c]["dur_seg"] for c in mejor)
    print(f"\n{N} temas, {dur // 3600}h{(dur % 3600) // 60:02d} | {es[0]:.1f} -> {es[-1]:.1f} "
          f"cima {max(es):.1f} al {es.index(max(es)) / (N - 1):.0%} | racha {peor}")
    print(f"color mediano {st.median(COL.get(c, 0) for c in mejor):.2f}")
    if args.dry:
        print("\n--dry: no se escribio nada")
        return
    doc["tracks"] = [{"artist": POOL[c]["artist"], "title": POOL[c]["title"], "content_id": c}
                     for c in mejor]
    doc["keep_order"] = True
    destino.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {destino.name}")


if __name__ == "__main__":
    main()
