# -*- coding: utf-8 -*-
"""Rearma data/pool_159.json, el pool del set 159 (Work · Organic con brillo).

No toca master.db: lee data/pool.json (dump_pool.py), data/groove_index.json y las
recetas de data/recetas/lib. Correrlo despues de un dump_pool si entro material nuevo.

QUE ENTRA (organic + su orbita)
  - genero Organic House u Organic House / Downtempo, o
  - genero vecino (Deep, Progressive, Melodic H&T, House, Downtempo, Electronica) de un
    sello o artista de la orbita organica: >= 40% de su material en la biblioteca es
    organic (con >= 2 temas organic el sello, >= 3 el artista), o nombrado en el pedido
    del DJ (Univack, Sol Selectas, Zenebona, Bedouin).

QUE SE FILTRA (duro)
  - BRILLO:  color_pct < --color (0.35; el minimo del 150, que el DJ aprobo, es 0.37)
  - GUSTO:   medio < 5 o aire < 2 (armar_noche_zorro.gusto_ok: sin medios el DJ lo
             escucha 'oscuro, baja energia'; sin aire, 'tecnoso')
  - TRABAJO: breakdown que conserva menos de --bd (0.30) de la energia del groove.
             Inertia, que el DJ escucho 'se cae fortisimo', conserva 0.26.

E:1.4 (fallo del cue engine: bajo leido en 0 s y sin breakdown ni drop) se estima y se
marca en el tema (energy_calc 1.4, energy_fuente). La DB no se toca:
  1. via de la receta: plomo.energy sobre la segmentacion de la receta, calibrada con la
     mediana de la E de la DB de los temas con la misma E de receta (+-0.2) y el mismo
     caso de bajo (como The Final Lap y Give It Up Again en el 158);
  2. si la receta no la puede medir (no confiable, o un solo groove sin breakdown):
     mediana de los 25 vecinos por densidad, graves y color (como Eight Years en el 156).

Uso:
    python scripts/archive/pool_159_2026-10-25.py
    python scripts/archive/pool_159_2026-10-25.py --color 0.5     # mas brillo, pool mas chico
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import math
import statistics as st
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from plomo.energy import calculate_energy  # noqa: E402

LIB = RAIZ / "data" / "recetas" / "lib"
ORG = {"organic house", "organic house / downtempo", "organic house  downtempo"}
GEN_ORBITA = {"deep house", "progressive house", "melodic house & techno", "melodic house",
              "house", "downtempo", "electronica", "electronic", "electronica / downtempo"}
SELLOS_NOMBRADOS = {"univack", "sol selectas", "zenebona"}
ARTISTAS_NOMBRADOS = {"bedouin"}
CUOTA_ORBITA = 0.4
VECINOS = 25


def _arts(t: dict) -> list[str]:
    return [a.strip().lower() for a in t["artist"].replace("&", ",").split(",") if a.strip()]


def orbita(pool: list[dict]) -> tuple[set[str], set[str]]:
    org = [t for t in pool if t["genre"].lower().strip() in ORG]
    lo = collections.Counter(t["label"].strip().lower() for t in org)
    la = collections.Counter(t["label"].strip().lower() for t in pool)
    sellos = {s for s, n in la.items() if s and lo.get(s, 0) >= 2 and lo[s] / n >= CUOTA_ORBITA}
    ao = collections.Counter(a for t in org for a in _arts(t))
    aa = collections.Counter(a for t in pool for a in _arts(t))
    artistas = {a for a, n in aa.items() if ao.get(a, 0) >= 3 and ao[a] / n >= CUOTA_ORBITA}
    return sellos | SELLOS_NOMBRADOS, artistas | ARTISTAS_NOMBRADOS


def _ref(i: str) -> dict | None:
    f = LIB / f"{i}.json"
    return json.loads(f.read_text(encoding="utf-8"))["referencia"] if f.exists() else None


def medidas(r: dict) -> dict:
    secs = r["secciones"]
    alta = [x["energia"] for x in secs if x["tipo"] in ("groove", "drop")]
    baja = [x["energia"] for x in secs if x["tipo"] in ("breakdown", "respiro")]
    ea = st.mean(alta) if alta else 0
    return {"medio": r["balance"]["medio"], "aire": r["balance"]["aire"],
            "bd": min(baja) / ea if baja and ea else 1.0}


def e_receta(r: dict) -> float | None:
    """plomo.energy con los cues sacados de la segmentacion de la receta."""
    secs = r["secciones"]
    kick = [s for s in secs if s["tipo"] in ("groove", "drop")]
    if not kick or r.get("confiable") is False:
        return None
    bajos = ([s for s in secs if s["tipo"] == "breakdown"]
             or [s for s in secs if s["tipo"] == "respiro"])
    bd = drop = None
    if bajos:
        b = max(bajos, key=lambda s: s["compases"])
        k = secs.index(b)
        if k + 1 < len(secs):
            bd, drop = b["seg_inicio"], secs[k + 1]["seg_inicio"]
    seg_bar = r["duracion_seg"] / max(1, r["compases"])
    outro = kick[-1]["seg_inicio"] + kick[-1]["seg_dur"] - 16 * seg_bar
    return calculate_energy(
        bpm=r.get("bpm") or 122, bass_in_ms=int(kick[0]["seg_inicio"] * 1000),
        breakdown_ms=int(bd * 1000) if bd is not None else None,
        drop_ms=int(drop * 1000) if drop is not None else None,
        outro_ms=int(outro * 1000), track_length_ms=None)


def _bajo_temprano(r: dict) -> bool:
    kick = [s for s in r["secciones"] if s["tipo"] in ("groove", "drop")]
    return bool(kick) and kick[0]["seg_inicio"] <= 0.1


def estimar(t: dict, pool: list[dict], tabla: list, groove: dict, hoy: str) -> tuple[float, str]:
    r = _ref(t["id"])
    er = e_receta(r) if r else None
    if er is not None and er > 2.0:      # <= 2 es otra vez "sin breakdown ni drop"
        bt = _bajo_temprano(r)
        par = [db for (e, b, db) in tabla if abs(e - er) <= 0.2 and b == bt]
        if len(par) >= 15:
            q = st.quantiles(par, n=4)
            return (round(st.median(par), 1),
                    f"estimada {hoy} por la via de la receta: plomo.energy sobre la segmentacion de "
                    f"data/recetas/lib da {er}; calibrada contra la DB: mediana de los {len(par)} temas "
                    f"con receta {er}+-0.2 y el mismo caso de bajo (IQR {q[0]:.1f}-{q[2]:.1f}). "
                    f"La DB dice 1.4 por el fallo del cue engine")
    tr, col, sd = groove["tracks"], groove["color_pct"], groove["desvios"]
    if t["id"] not in tr:
        return 5.8, f"estimada {hoy}: sin receta ni groove; mediana de la biblioteca. La DB dice 1.4"
    p0 = (tr[t["id"]][0] / sd[0], tr[t["id"]][1] / sd[1], col.get(t["id"], 0.5))
    dist = sorted((math.dist(p0, (tr[u["id"]][0] / sd[0], tr[u["id"]][1] / sd[1],
                                  col.get(u["id"], 0.5))), u["energy"])
                  for u in pool if u["energy"] != 1.4 and u["id"] in tr)
    motivo = ("receta no confiable ('poco contraste en la banda grave')" if r and r.get("confiable") is False
              else "la receta no ve breakdown ni drop (un solo groove)")
    return (round(st.median(e for _, e in dist[:VECINOS]), 1),
            f"estimada {hoy}: {motivo}, asi que ninguna de las dos vias la mide; mediana de sus "
            f"{VECINOS} vecinos por densidad, graves y color (groove_index). La DB dice 1.4")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--color", type=float, default=0.35)
    ap.add_argument("--bd", type=float, default=0.30)
    ap.add_argument("--out", type=Path, default=RAIZ / "data" / "pool_159.json")
    a = ap.parse_args()
    hoy = dt.date.today().isoformat()
    pool = json.loads((RAIZ / "data" / "pool.json").read_text(encoding="utf-8"))
    groove = json.loads((RAIZ / "data" / "groove_index.json").read_text(encoding="utf-8"))
    sellos, artistas = orbita(pool)
    tabla = []
    for t in pool:
        r = _ref(t["id"]) if t["energy"] != 1.4 else None
        er = e_receta(r) if r else None
        if er is not None:
            tabla.append((er, _bajo_temprano(r), t["energy"]))
    sale, fuera = [], collections.Counter()
    for t in pool:
        g = t["genre"].lower().strip()
        if g in ORG:
            por = "genero"
        elif g in GEN_ORBITA and t["label"].strip().lower() in sellos:
            por = "sello"
        elif g in GEN_ORBITA and set(_arts(t)) & artistas:
            por = "artista"
        else:
            continue
        r, c = _ref(t["id"]), groove["color_pct"].get(t["id"])
        m = medidas(r) if r else None
        if m is None or c is None:
            fuera["sin medida"] += 1
        elif c < a.color:
            fuera["color"] += 1
        elif m["medio"] < 5 or m["aire"] < 2:
            fuera["medio/aire"] += 1
        elif m["bd"] < a.bd:
            fuera["breakdown profundo"] += 1
        else:
            x = dict(t, orbita=por)
            if x["energy"] == 1.4:
                e, fuente = estimar(x, pool, tabla, groove, hoy)
                x.update(energy_calc=1.4, energy=e, energy_fuente=fuente)
                print(f"  E estimada {e:>4}  {x['artist'][:28]} - {x['title'][:48]}")
            sale.append(x)
    a.out.write_text(json.dumps(sale, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(sale)} temas -> {a.out}   fuera: {dict(fuera)}")


if __name__ == "__main__":
    main()
