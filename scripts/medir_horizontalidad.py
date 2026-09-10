"""Mide cuan HORIZONTAL es un set: cuanto se mueve la energia y el BPM.

Un set "horizontal" —el de after que no promete una bajada— no se define por la
energia promedio sino por su RECORRIDO: cuanto separa al track mas alto del mas
bajo, y de que tamano son los escalones. Un set de 12 tracks entre E5.8 y E6.6 es
horizontal aunque sea intenso; uno que va de E3 a E8 no lo es aunque promedie lo
mismo.

Se mide sobre los tres corpus para no inventar el numero:
  data/tocados/   - lo que el DJ toco de verdad, con energia al 100%
  data/setlists/  - otros DJs; energia casi nunca, BPM y key si
  data/set_targets/ - lo armado por el solver

Uso:
    python scripts/medir_horizontalidad.py
    python scripts/medir_horizontalidad.py --set-target 90
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent


def perfil(tracks: list[dict]) -> dict | None:
    es = [t["energy"] for t in tracks if t.get("energy") is not None]
    bs = [t["bpm"] for t in tracks if t.get("bpm") is not None]
    if len(es) < 4 and len(bs) < 4:
        return None
    d: dict = {"n": len(tracks)}
    if len(es) >= 4:
        pasos = [abs(b - a) for a, b in zip(es, es[1:])]
        d["e_rango"] = max(es) - min(es)
        d["e_min"] = min(es)
        d["e_max"] = max(es)
        d["e_escalon_max"] = max(pasos) if pasos else 0.0
        # La bajada mas grande: es lo que define "sin mucha bajada".
        caidas = [a - b for a, b in zip(es, es[1:]) if a > b]
        d["e_caida_max"] = max(caidas) if caidas else 0.0
        d["e_n"] = len(es)
    if len(bs) >= 4:
        d["bpm_rango"] = max(bs) - min(bs)
        d["bpm_n"] = len(bs)
    return d


def resumir(nombre: str, perfiles: list[dict]) -> None:
    if not perfiles:
        print(f"\n{nombre}: sin datos")
        return
    print(f"\n{nombre}  ({len(perfiles)} sets)")
    for campo, etiqueta in [("e_rango", "recorrido de energia (max-min)"),
                            ("e_caida_max", "bajada mas grande entre 2 tracks"),
                            ("e_escalon_max", "escalon mas grande (sube o baja)"),
                            ("bpm_rango", "recorrido de BPM")]:
        vs = [p[campo] for p in perfiles if campo in p]
        if not vs:
            continue
        vs.sort()
        print(f"  {etiqueta:34} mediana={st.median(vs):5.1f}  "
              f"p10={vs[len(vs)//10]:5.1f}  p90={vs[-max(1,len(vs)//10)]:5.1f}  n={len(vs)}")


def _pool_por_id() -> dict[str, dict]:
    """Los set_targets guardan content_id y nada mas; la energia vive en el pool."""
    f = RAIZ / "data" / "pool.json"
    if not f.exists():
        return {}
    return {t["id"]: t for t in json.loads(f.read_text(encoding="utf-8"))}


def cargar(carpeta: str, solo: set[str] | None = None) -> list[dict]:
    idx = _pool_por_id()
    out = []
    for f in sorted((RAIZ / "data" / carpeta).glob("*.json")):
        if solo and f.stem not in solo:
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        ts = d.get("tracks") or []
        if not (isinstance(ts, list) and ts and isinstance(ts[0], dict)):
            continue
        for t in ts:
            if t.get("energy") is None and t.get("content_id") in idx:
                m = idx[t["content_id"]]
                t["energy"], t["bpm"] = m.get("energy"), m.get("bpm")
        p = perfil(ts)
        if p:
            p["nombre"] = d.get("evento") or d.get("name") or f.stem
            out.append(p)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--detalle", action="store_true")
    ap.add_argument("--sets", nargs="*", help="numeros de set_targets a medir aparte")
    args = ap.parse_args()

    if args.sets:
        solo = {f"set_{n}" for n in args.sets}
        resumir("LOS QUE SE ESTAN MIDIENDO", cargar("set_targets", solo))
        for p in cargar("set_targets", solo):
            print(f"      E{p['e_min']:.1f}-{p['e_max']:.1f} rango={p['e_rango']:.1f} "
                  f"caida={p['e_caida_max']:.1f} bpm={p.get('bpm_rango',0):.0f} | {p['nombre'][:50]}")

    for carpeta, nombre in [("tocados", "TOCADO — sets reales propios"),
                            ("setlists", "REFERENCIA — otros DJs"),
                            ("set_targets", "PROPIO — armado por el solver")]:
        ps = cargar(carpeta)
        resumir(nombre, ps)
        if args.detalle:
            for p in sorted(ps, key=lambda x: x.get("e_rango", 99)):
                if "e_rango" in p:
                    print(f"      E{p['e_min']:.1f}-{p['e_max']:.1f} "
                          f"rango={p['e_rango']:.1f} caida={p['e_caida_max']:.1f} "
                          f"| {p['nombre'][:52]}")


if __name__ == "__main__":
    main()
