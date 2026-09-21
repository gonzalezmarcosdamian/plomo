# -*- coding: utf-8 -*-
"""Ordena la biblioteca por parecido a la FORMA de un tema modelo.

No es parecido de BPM ni de key —eso ya lo resuelve el solver—: es parecido de
como esta construido el tema. Donde cae el breakdown principal y cuanto dura,
donde arranca el drop final y cuanto dura, cuantas secciones tiene, como reparte
la energia entre graves, medios y aire, y cuanto respira (rango dinamico).

Cada rasgo se normaliza por su desvio en la biblioteca indexada, asi que un
compas de mas en el breakdown pesa distinto que un punto de sub. La distancia es
euclidea sobre eso; el parecido es 1 / (1 + distancia).

Necesita el indice de data/recetas/lib/ (scripts/indexar_forma.py).

Uso:
    python scripts/parecido_forma.py <content_id_modelo>
    python scripts/parecido_forma.py <content_id_modelo> --top 60 --json out.json
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
LIB = RAIZ / "data" / "recetas" / "lib"

RASGOS = ("bd_pos", "bd_len", "drop_pos", "drop_len", "n_secc",
          "sub", "medio", "aire", "rango")


def rasgos(d: dict) -> dict | None:
    """La receta de un tema reducida a los rasgos de forma."""
    r = d["referencia"]
    if not r.get("confiable", True) or not r.get("compases"):
        return None
    tot = r["compases"]
    secs = r["secciones"]
    pausas = [s for s in secs if s["tipo"] in ("breakdown", "respiro")]
    drops = [s for s in secs if s["tipo"] == "drop"]
    if not pausas or not drops:
        return None
    # el breakdown PRINCIPAL es el mas largo, no el primero: esa es la
    # diferencia con los cues, que marcan el primero
    bd = max(pausas, key=lambda s: s["compases"])
    fin = drops[-1]
    return {"bd_pos": bd["compas_inicio"] / tot, "bd_len": bd["compases"],
            "drop_pos": fin["compas_inicio"] / tot, "drop_len": fin["compases"],
            "n_secc": len(secs), "sub": r["balance"]["sub"],
            "medio": r["balance"]["medio"], "aire": r["balance"]["aire"],
            "rango": r["rango_dinamico_db"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("modelo")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    todos = {}
    for f in LIB.glob("*.json"):
        x = rasgos(json.loads(f.read_text(encoding="utf-8")))
        if x:
            todos[f.stem] = x
    if a.modelo not in todos:
        sys.exit(f"el modelo {a.modelo} no esta en el indice (o su receta no es confiable)")
    desvio = {k: (st.pstdev(v[k] for v in todos.values()) or 1.0) for k in RASGOS}
    m = todos[a.modelo]
    orden = []
    for cid, x in todos.items():
        dist = sum(((x[k] - m[k]) / desvio[k]) ** 2 for k in RASGOS) ** 0.5
        orden.append((1 / (1 + dist), cid))
    orden.sort(reverse=True)

    pool = {t["id"]: t for t in json.loads(
        (RAIZ / "data" / "pool.json").read_text(encoding="utf-8"))}
    print(f"indice: {len(todos)} temas.  modelo: "
          f"{pool.get(a.modelo, {}).get('artist', '?')} - {pool.get(a.modelo, {}).get('title', '?')}")
    print(f"  forma del modelo: breakdown {m['bd_len']}c al {m['bd_pos']:.0%}, drop final "
          f"{m['drop_len']}c al {m['drop_pos']:.0%}, {m['n_secc']} secciones, sub {m['sub']:.0f}%\n")
    for p, cid in orden[:a.top]:
        t = pool.get(cid, {}); x = todos[cid]
        print(f"  {p:.2f}  E{t.get('energy', 0):.1f} {t.get('key', '?'):>3} "
              f"bd {x['bd_len']:>2}c@{x['bd_pos']:.0%} drop {x['drop_len']:>2}c | "
              f"{t.get('artist', '?')[:24]} - {t.get('title', '?')[:36]}")
    if a.json:
        a.json.write_text(json.dumps([{"id": c, "parecido": round(p, 3)} for p, c in orden],
                                     indent=1), encoding="utf-8")
        print(f"\n-> {a.json}")


if __name__ == "__main__":
    main()
