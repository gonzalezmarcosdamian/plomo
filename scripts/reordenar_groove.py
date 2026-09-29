# -*- coding: utf-8 -*-
"""Reordena un set para que el GROOVE no se caiga entre tema y tema.

POR QUE
-------
"Reordenemos para mantener groove estilo maze, la lista esta muy bien" (el DJ,
2026-09-29). La lista ya le gusta: no hay que cambiar temas, hay que cambiar el
orden.

Maze 28 --su referencia de groove-- vive entre 14.5 y 15.3 de densidad, parejo.
El 143 arrancaba en 15-16 y se caia a 8-11 desde el puesto diez: cuatro temas
seguidos por debajo de 11 despues de venir de 15. Eso no es un respiro, es el
piso que se hunde.

Asi que al costo de siempre --arco de energia, Camelot, BPM-- se le suma el
SALTO DE DENSIDAD entre temas consecutivos. Los temas son los mismos; lo que
cambia es que los de densidad baja no queden todos juntos ni pegados a los mas
densos.

USO
---
    python scripts/reordenar_groove.py 143 --peso 3 --dry
    python scripts/reordenar_groove.py 143
"""
from __future__ import annotations

import argparse
import heapq
import json
import statistics as st
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from plomo.camelot import distance as cam  # noqa: E402
from plomo.rules import R  # noqa: E402

TOLERANCIA_GROOVE = 1.5     # cuanto puede cambiar la densidad sin que moleste
PISO_GROOVE = 12.0          # debajo de esto el tema no sostiene el groove solo


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("num", type=int)
    ap.add_argument("--peso", type=float, default=3.0)
    ap.add_argument("--cierre-denso", type=int, default=0,
                    help="cuantos temas del final tienen que sostener el groove")
    ap.add_argument("--cam", type=int, default=None,
                    help="tope de Camelot para ESTE reorden; por defecto el de la regla")
    ap.add_argument("--beam", type=int, default=4000)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    POOL = {t["id"]: t for t in json.loads((RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
    TR = json.loads((RAIZ / "data/groove_index.json").read_text(encoding="utf-8"))["tracks"]
    P = json.loads((RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8"))
    f = RAIZ / "data/set_targets" / f"set_{args.num}.json"
    doc = json.loads(f.read_text(encoding="utf-8"))
    ids = [t["content_id"] for t in doc["tracks"]]
    n = len(ids)
    sin_medir = [c for c in ids if c not in TR]
    if sin_medir:
        print(f"OJO: {len(sin_medir)} temas sin densidad medida, se les pone la mediana")
    med = st.median(TR[c][0] for c in ids if c in TR)

    def dens(c):
        return TR[c][0] if c in TR else med

    def E(c):
        v = P.get(c)
        return v.get("E", POOL[c]["energy"]) if isinstance(v, dict) else POOL[c]["energy"]

    max_cam = args.cam or R.get("armonia.max_camelot_dist", 2)
    max_bpm = R.get("bpm.max_salto", 3.0)

    def enlaza(a, b):
        return (cam(POOL[a]["key"], POOL[b]["key"]) <= max_cam
                and abs(POOL[a]["bpm"] - POOL[b]["bpm"]) <= max_bpm)

    hi = max(E(c) for c in ids)
    lo = min(E(c) for c in ids)
    pico = R.get("energia.pico_en_pct", 0.6)

    def arco(i):
        t = i / (n - 1)
        if t <= pico:
            return lo + (hi - lo) * (t / pico)
        return hi - (hi - (lo + hi) / 2) * ((t - pico) / (1 - pico))

    def costo(seq, c):
        k = max(0.0, abs(E(c) - arco(len(seq))) - 0.9) * 3.0
        if seq:
            p = seq[-1]
            k += cam(POOL[p]["key"], POOL[c]["key"]) * 0.8
            k += abs(POOL[p]["bpm"] - POOL[c]["bpm"]) * 0.4
            # El salto de densidad, PERO poco: castigarlo fuerte agrupa a los
            # densos adelante y deja el ultimo tercio entero sin groove, que es
            # lo contrario de lo que se pide.
            k += max(0.0, abs(dens(p) - dens(c)) - TOLERANCIA_GROOVE) * (args.peso * 0.25)
            # LO QUE DE VERDAD MANTIENE EL GROOVE: que no haya dos flojos
            # seguidos. Un tema de densidad baja entre dos densos es un respiro;
            # dos seguidos es el piso que se hunde, que es lo que pasaba con
            # In Another Time, Sizer, Go y Little Mushroom pegados.
            if dens(p) < PISO_GROOVE and dens(c) < PISO_GROOVE:
                k += args.peso * 2.0
            if E(c) < E(p) - 0.15 and len(seq) >= 2 and E(p) < E(seq[-2]) - 0.15:
                k += 3.0
        return k

    estados = [(0.0, [], frozenset())]
    for paso in range(n):
        sig = []
        for k, seq, usados in estados:
            for c in ids:
                if c in usados or (seq and not enlaza(seq[-1], c)):
                    continue
                # El final no puede quedar sin groove: es lo ultimo que escucha
                # la pista y es justo donde el orden por metricas lo deja caer.
                if args.cierre_denso and paso >= n - args.cierre_denso and dens(c) < PISO_GROOVE:
                    continue
                sig.append((k + costo(seq, c), seq + [c], usados | {c}))
        if not sig:
            sys.exit(f"SIN SOLUCION en el paso {paso + 1}")
        estados = heapq.nsmallest(args.beam, sig, key=lambda x: x[0])
    mejor = estados[0][1]

    def informe(orden, nombre):
        ds = [dens(c) for c in orden]
        es = [E(c) for c in orden]
        saltos = [abs(ds[i + 1] - ds[i]) for i in range(n - 1)]
        peor = run = 0
        for i in range(1, n):
            run = run + 1 if es[i] < es[i - 1] - 0.15 else 0
            peor = max(peor, run)
        pares = sum(1 for i in range(n - 1)
                    if ds[i] < PISO_GROOVE and ds[i + 1] < PISO_GROOVE)
        corrida = mayor = 0
        for x in ds:
            corrida = corrida + 1 if x < PISO_GROOVE else 0
            mayor = max(mayor, corrida)
        print(f"  {nombre:8s} flojos seguidos: {pares} pares, corrida mas larga {mayor} "
              f"| salto medio {st.mean(saltos):.2f} | {es[0]:.1f} -> {es[-1]:.1f} "
              f"cima al {es.index(max(es)) / (n - 1):.0%} | racha energia {peor}")

    print(f"{doc['name'][:54]}")
    informe(ids, "antes")
    informe(mejor, "despues")
    print()
    for i, c in enumerate(mejor, 1):
        t = POOL[c]
        movio = ids.index(c) + 1
        flecha = "" if movio == i else f"  (estaba {movio})"
        print(f"{i:2d}. dens{dens(c):5.1f} E{E(c):4.1f} {t['bpm']:5.1f} {t['key']:>3s} "
              f"{t['artist'][:20]:20s} - {t['title'][:28]}{flecha}")
    if args.dry:
        print("\n--dry: no se escribio nada")
        return
    doc["tracks"] = [{"artist": POOL[c]["artist"], "title": POOL[c]["title"], "content_id": c}
                     for c in mejor]
    doc["keep_order"] = True
    f.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {f.name}")
    subprocess.run([sys.executable, str(RAIZ / "scripts/build_set.py"), str(args.num)],
                   cwd=str(RAIZ))


if __name__ == "__main__":
    main()
