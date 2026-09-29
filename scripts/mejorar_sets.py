# -*- coding: utf-8 -*-
"""Pone los sets de una tanda a la altura del que el DJ ya aprobo.

POR QUE
-------
"Itera los demas sets para tener pool de temas por si acaso" y "mejoralo en pos
de como quedo el 143 para esa fecha" (el DJ, 2026-09-29). Y despues: "el 143 es
bastante modelo".

El 143 se trabajo tema por tema con el DJ escuchando. Los otros ocho quedaron
como salieron del solver hace una semana: antes de 258 temas nuevos y antes de
que se midiera nada de lo que el escucha. Esto los alinea con lo que quedo
probado ahi:

  1. Ningun tema VETADO ni GASTADO de esta tanda.
  2. El groove no se cae: nunca dos temas de densidad baja seguidos. Es lo que
     separa a Ipanema y Fogbows --los que el DJ aprobo-- de Milo, que no.
  3. El arco no se desinfla despues del pico.

LO QUE NO HACE, A PROPOSITO
Descartar por medio/aire. Ese filtro se refuto el mismo dia que se escribio:
descarta 8 de los 23 temas que el DJ aprobo, incluidos Amnesia, Citadel, Fragma e
Ipanema Twilight. Sirve para ordenar, no para excluir.

Tampoco mide el ataque de la capa melodica, que es lo unico que separa de verdad
lo que el llama oscuro. Cuesta un minuto por tema con Demucs y aca son ciento
cincuenta. Para eso esta `color_melodico.py` sobre una lista corta.

USO
---
    python scripts/mejorar_sets.py 139 140 141 --dry
    python scripts/mejorar_sets.py 139 140 141 142 144 145 146 147 148
"""
from __future__ import annotations

import argparse
import heapq
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import select_set as S  # noqa: E402
from plomo.camelot import distance as cam  # noqa: E402

PISO_GROOVE = 12.0
GEN = {"Progressive House", "House", "Melodic House & Techno"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("nums", type=int, nargs="+")
    ap.add_argument("--beam", type=int, default=6000)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    POOL = {t["id"]: t for t in json.loads((RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
    G = json.loads((RAIZ / "data/groove_index.json").read_text(encoding="utf-8"))
    TR, COL = G["tracks"], G["color_pct"]
    P = json.loads((RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8"))
    VET = {k for k, v in P.items() if isinstance(v, dict) and v.get("veto")}
    GAST = {k for k, v in P.items() if isinstance(v, dict) and v.get("gastado")}

    def dato(c):
        v = P.get(c)
        return v if isinstance(v, dict) else {}

    def E(c):
        return dato(c).get("E", POOL[c]["energy"])

    def dens(c):
        return TR[c][0] if c in TR else 13.4

    def enlaza(a, b):
        return (cam(POOL[a]["key"], POOL[b]["key"]) <= 2
                and abs(POOL[a]["bpm"] - POOL[b]["bpm"]) <= 3.0)

    # Lo que suena en CUALQUIER set de la tanda, para no repetir al reemplazar.
    todos = set()
    for n in args.nums + [143]:
        f = RAIZ / "data/set_targets" / f"set_{n}.json"
        if f.exists():
            todos |= {t["content_id"] for t in json.loads(f.read_text(encoding="utf-8"))["tracks"]}

    for num in args.nums:
        f = RAIZ / "data/set_targets" / f"set_{num}.json"
        if not f.exists():
            print(f"set {num}: no existe")
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        ids = [t["content_id"] for t in doc["tracks"]]
        fuera = [c for c in ids if c in VET or c in GAST]
        quedan = [c for c in ids if c not in fuera]
        ocup = set()
        for c in quedan:
            ocup |= S.names(POOL[c]["artist"], POOL[c]["title"])

        nuevos: list[str] = []
        for viejo in fuera:
            e0, k0 = E(viejo), POOL[viejo]["key"]
            mejor, mejor_k = None, 1e9
            for c, t in POOL.items():
                if c in todos or c in VET or c in GAST or c not in TR or c in nuevos:
                    continue
                if t.get("genre") not in GEN or abs(t["energy"] - e0) > 0.7:
                    continue
                if not (119 <= t["bpm"] <= 127) or dens(c) < 13.0:
                    continue
                if cam(k0, t["key"]) > 1:
                    continue
                if S.names(t["artist"], t["title"]) & ocup:
                    continue
                k = abs(t["energy"] - e0) - COL.get(c, 0) - dens(c) / 20
                if k < mejor_k:
                    mejor, mejor_k = c, k
            if mejor:
                nuevos.append(mejor)
                ocup |= S.names(POOL[mejor]["artist"], POOL[mejor]["title"])
        temas = quedan + nuevos
        n = len(temas)
        if n < 4:
            print(f"set {num}: quedan {n} temas, no lo toco")
            continue

        lo, hi = min(E(c) for c in temas), max(E(c) for c in temas)
        # CADA FRANJA ENTREGA A LA SIGUIENTE, menos la ultima. Un set que pica y
        # se desinfla le deja la pista fria al que sigue; por eso el 143, que es
        # el modelo, sube hasta el final.
        nom = doc["name"]
        if "3 a 5" in nom:
            forma, pico = "cierre", 0.72      # el ultimo: pica y baja controlado
        elif "23 a 1" in nom:
            forma, pico = "entrega", 0.90     # warm: entrega caliente a la 1
        else:
            forma, pico = "entrega", 0.88     # 1 a 3 y peak: entrega al main

        def arco(i, lo=lo, hi=hi, n=n, pico=pico, forma=forma):
            t = i / (n - 1)
            if t <= pico:
                return lo + (hi - lo) * (t / pico) ** 0.9
            piso = (lo + hi) / 2 if forma == "cierre" else hi - (hi - lo) * 0.18
            return hi - (hi - piso) * ((t - pico) / (1 - pico))

        def costo(seq, c):
            k = max(0.0, abs(E(c) - arco(len(seq))) - 1.0) * 2.5
            if seq:
                p = seq[-1]
                k += cam(POOL[p]["key"], POOL[c]["key"]) * 0.6
                k += abs(POOL[p]["bpm"] - POOL[c]["bpm"]) * 0.3
                if dens(p) < PISO_GROOVE and dens(c) < PISO_GROOVE:
                    k += 4.0
                if E(c) < E(p) - 0.15 and len(seq) >= 2 and E(p) < E(seq[-2]) - 0.15:
                    k += 3.0
            return k - COL.get(c, 0.5) * 0.8

        # Beam con desempate de Warnsdorff: entre dos estados parecidos gana el
        # que deja mas salidas. Sin esto el beam descarta recorridos que existen
        # -- paso en el 143 y decia SIN SOLUCION teniendo camino.
        cierre_min = lo + (hi - lo) * 0.62 if forma == "entrega" else 0.0
        VEC = {c: {y for y in temas if y != c and enlaza(c, y)} for c in temas}
        estados = [(0.0, 0.0, [], frozenset())]
        roto = False
        for paso in range(n):
            sig = []
            for _, k, seq, us in estados:
                ultimo = len(seq) == n - 1
                for c in temas:
                    if c in us or (seq and not enlaza(seq[-1], c)):
                        continue
                    # El que ENTREGA no puede terminar abajo: la pista pasa al
                    # que sigue como se la dejan. El que CIERRA si puede bajar.
                    if ultimo and forma == "entrega" and E(c) < cierre_min:
                        continue
                    nu = us | {c}
                    libres = [x for x in temas if x not in nu]
                    salidas = len(VEC[c] & set(libres)) if libres else 0
                    if libres and salidas == 0:
                        continue
                    if libres and any(not (VEC[x] & (set(libres) | {c})) for x in libres):
                        continue
                    nk = k + costo(seq, c)
                    sig.append((nk - salidas * 0.35, nk, seq + [c], nu))
            if not sig:
                print(f"set {num}: SIN SOLUCION en el paso {paso + 1}, queda como estaba")
                roto = True
                break
            estados = heapq.nsmallest(args.beam, sig, key=lambda x: x[0])
        if roto:
            continue
        mejor_orden = min(estados, key=lambda x: x[1])[2]

        def flojos(orden):
            return sum(1 for i in range(len(orden) - 1)
                       if dens(orden[i]) < PISO_GROOVE and dens(orden[i + 1]) < PISO_GROOVE)

        es = [E(c) for c in mejor_orden]
        peor = run = 0
        for i in range(1, n):
            run = run + 1 if es[i] < es[i - 1] - 0.15 else 0
            peor = max(peor, run)
        print(f"set {num} [{forma}]: {len(fuera)} fuera, {len(nuevos)} nuevos | flojos seguidos "
              f"{flojos(ids)} -> {flojos(mejor_orden)} | {es[0]:.1f} -> {es[-1]:.1f} "
              f"| cima al {es.index(max(es)) / (n - 1):.0%} | racha {peor}")
        for c in fuera:
            print(f"      sale  {POOL[c]['artist'][:20]:20s} - {POOL[c]['title'][:30]}")
        for c in nuevos:
            print(f"      entra {POOL[c]['artist'][:20]:20s} - {POOL[c]['title'][:30]}"
                  f"  (dens {dens(c):.1f}, col {COL.get(c, 0):.2f})")
        if args.dry:
            continue
        doc["tracks"] = [{"artist": POOL[c]["artist"], "title": POOL[c]["title"], "content_id": c}
                         for c in mejor_orden]
        doc["keep_order"] = True
        f.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        subprocess.run([sys.executable, str(RAIZ / "scripts/build_set.py"), str(num)],
                       cwd=str(RAIZ), capture_output=True)
        todos |= set(mejor_orden)


if __name__ == "__main__":
    main()
