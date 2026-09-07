"""Simula `sonido_propio` antes de encenderlo.

Corre el mismo beam search de select_set.py sobre el mismo pool, con tres
variantes de costo:

    (a) base   — sin la regla
    (b) lift   — bonus por lift de artista/sello
    (c) lift+  — bonus por lift MENOS penalizacion por reproducciones

y mide, por set: cuantos tracks nunca tocados entran, cuanto se desvia el arco
de energia, cuanto se degrada la escalera Camelot, y si el set sigue teniendo
solucion. Los pesos se barren: la pregunta no es "sirve" sino "a partir de que
peso cambia algo y a partir de cual rompe el arco".

Uso:
    python scripts/sim_sonido_propio.py data/set_configs/serie_argentina.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from select_set import (BAJA_CIERRE, MAX_CAM, MAX_E_STEP, MAX_RETROCESO,  # noqa: E402
                        MIN_GAP, PENAL_MISMA_KEY_DESDE, PESO_ARCO, PESO_CAM,
                        PESO_MISMA_KEY, PICO_PCT, arc_target, cam_dist,
                        camelot, names)


def select_adj(pool, n, e_lo, e_hi, max_bpm_jump=2.0, max_per_artist=1,
               beam=400, adj=None):
    """Igual que select_set.select pero con un ajuste de costo por track.

    `adj[id]` se RESTA del costo: positivo = premio, negativo = castigo.
    Ninguna restriccion dura se toca — la regla nueva solo mueve preferencias.
    """
    adj = adj or {}
    for t in pool:
        if "_names" not in t:
            t["_names"] = names(t["artist"], t["title"])
            t["_cam"] = camelot(t["key"])
    beams = [(0.0, [], set(), {})]
    for i in range(n):
        tgt = arc_target(i, n, e_lo, e_hi)
        nxt = []
        for cost, seq, ids, arts in beams:
            prev = seq[-1] if seq else None
            for t in pool:
                if t["id"] in ids:
                    continue
                na = t["_names"]
                if any(len(arts.get(a, ())) >= max_per_artist for a in na):
                    continue
                if any(i - p < MIN_GAP for a in na for p in arts.get(a, ())):
                    continue
                if prev:
                    d = cam_dist(prev["key"], t["key"])
                    if d > MAX_CAM:
                        continue
                    if abs(t["bpm"] - prev["bpm"]) > max_bpm_jump:
                        continue
                    if i / (n - 1) <= PICO_PCT and t["energy"] < prev["energy"] - MAX_RETROCESO:
                        continue
                    if abs(t["energy"] - prev["energy"]) > MAX_E_STEP:
                        continue
                    if i == n - 1 and t["energy"] > max(x["energy"] for x in seq) - BAJA_CIERRE:
                        continue
                    same = 0
                    for prv in reversed(seq):
                        if prv["_cam"][0] == t["_cam"][0]:
                            same += 1
                        else:
                            break
                    step = d * PESO_CAM + max(0, same - PENAL_MISMA_KEY_DESDE + 1) * PESO_MISMA_KEY
                else:
                    step = 0.0
                c = cost + abs(t["energy"] - tgt) * PESO_ARCO + step - adj.get(t["id"], 0.0)
                na_pos = {a: arts.get(a, ()) + (i,) for a in na}
                nxt.append((c, seq + [t], ids | {t["id"]}, {**arts, **na_pos}))
        if not nxt:
            return None
        nxt.sort(key=lambda x: x[0])
        beams = nxt[:beam]
    return beams[0]


def calidad(seq, e_lo, e_hi):
    """Costo del set descompuesto, SIN el ajuste — para comparar manzanas."""
    n = len(seq)
    arco = sum(abs(t["energy"] - arc_target(i, n, e_lo, e_hi)) for i, t in enumerate(seq)) / n
    cam = [cam_dist(seq[i - 1]["key"], seq[i]["key"]) for i in range(1, n)]
    return {
        "desvio_arco": round(arco, 3),
        "cam_medio": round(sum(cam) / len(cam), 3),
        "cam_max": max(cam),
        "e_min": min(t["energy"] for t in seq),
        "e_max": max(t["energy"] for t in seq),
    }


def mapas_lift(mi_sonido: dict) -> tuple[dict, dict]:
    art = {a["valor"].lower(): a["lift"] for a in mi_sonido["artistas"]}
    sel = {s["valor"]: s["lift"] for s in mi_sonido["sellos"]}
    return art, sel


def lift_de(t, art, sel) -> float:
    la = max([art.get(a, 1.0) for a in names(t["artist"], t["title"])] or [1.0])
    ls = sel.get(t.get("label", ""), 1.0)
    return max(la, ls)


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    pool_all = json.loads((RAIZ / cfg["pool"]).read_text(encoding="utf-8"))
    mi = json.loads((RAIZ / "data/mi_sonido.json").read_text(encoding="utf-8"))
    art, sel = mapas_lift(mi)
    # DJPlayCount y djmdSongHistory son la misma cuenta: mi_sonido.py las suma
    # y duplica. Aca se usa la mitad, que es la reproduccion real.
    veces = json.loads((RAIZ / "data/veces_por_track.json").read_text(encoding="utf-8"))

    for t in pool_all:
        t["_lift"] = lift_de(t, art, sel)
        t["_veces"] = veces.get(t["id"], 0)

    W_LIFT = [float(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["0.0", "0.1", "0.2", "0.4"])]
    W_REP = [float(x) for x in (sys.argv[3].split(",") if len(sys.argv) > 3 else ["0.0", "0.3", "0.6"])]

    filas = []
    for spec in cfg["sets"]:
        artistas = spec.get("artists") or ["*"]
        generos = [g.lower() for g in spec.get("genres", [])]
        pool = [
            t for t in pool_all
            if (artistas == ["*"] or any(a.lower() in t["artist"].lower() for a in artistas))
            and spec["bpm"][0] <= t["bpm"] <= spec["bpm"][1]
            and (not generos or (t.get("genre", "") or "").lower() in generos)
            and (not spec.get("keys") or t["key"] in spec["keys"])
            and camelot(t["key"])
        ]
        for wl in W_LIFT:
            for wr in W_REP:
                adj = {t["id"]: wl * (t["_lift"] - 1.0) - wr * t["_veces"] for t in pool}
                best = select_adj(
                    pool, spec["n"], spec["e_lo"], spec["e_hi"],
                    max_bpm_jump=spec.get("max_bpm_jump", 2.0),
                    max_per_artist=spec.get("max_per_artist", 1),
                    beam=spec.get("beam", 400), adj=adj)
                if not best:
                    filas.append({"set": spec["num"], "w_lift": wl, "w_rep": wr, "sin_solucion": True})
                    continue
                seq = best[1]
                q = calidad(seq, spec["e_lo"], spec["e_hi"])
                filas.append({
                    "set": spec["num"], "n_pool": len(pool), "w_lift": wl, "w_rep": wr,
                    "sin_solucion": False,
                    "nuevos": sum(1 for t in seq if t["_veces"] == 0),
                    "repros_en_set": sum(t["_veces"] for t in seq),
                    "lift_medio": round(sum(t["_lift"] for t in seq) / len(seq), 2),
                    "ids": [t["id"] for t in seq], **q,
                })
                print(f"set {spec['num']} wl={wl} wr={wr} pool={len(pool)} "
                      f"nuevos={filas[-1]['nuevos']}/{len(seq)} repros={filas[-1]['repros_en_set']} "
                      f"lift={filas[-1]['lift_medio']} arco={q['desvio_arco']} cam={q['cam_medio']}")
    out = RAIZ / "data/sim_sonido_propio.json"
    out.write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
    print("->", out)


if __name__ == "__main__":
    main()
