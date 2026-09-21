"""Compara la DISTRIBUCION de los sets armados contra la de las ventanas reales.

No medianas: cuantos de nuestros sets caen en el p10-p90 de las ventanas de 8 a
18 temas consecutivos de data/setlists/. Una ventana real cae en su propio
p10-p90 el 80% de las veces: ese es el techo. Los saltos se cuentan solo entre
posiciones CONSECUTIVAS: un tema sin identificar no es una transicion.

Uso:
    python scripts/medir_contra_referencia.py                 # data/set_targets
    python scripts/medir_contra_referencia.py <carpeta_targets>
"""
import json,glob,statistics as st,sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
BASE=Path(next((a for a in sys.argv[1:] if not a.isdigit()),"data/set_targets"))
NUMS=[int(a) for a in sys.argv[1:] if a.isdigit()] or list(range(109,139))

def corr(xs,ys):
    mx,my=st.mean(xs),st.mean(ys)
    dn=(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))**.5
    return sum((xs[i]-mx)*(ys[i]-my) for i in range(len(xs)))/dn if dn else None
def ac(sal):
    if len(sal)<4: return None
    m=st.mean(sal); den=sum((x-m)**2 for x in sal)
    return sum((sal[i]-m)*(sal[i+1]-m) for i in range(len(sal)-1))/den if den else None

# --- referencia: ventanas de 8 a 18 posiciones consecutivas ---
ref_ac,ref_cp,ref_rg=[],[],[]
for f in sorted(glob.glob("data/setlists/*.json")):
    d=json.load(open(f,encoding="utf-8"))
    if not d.get("orden_confiable",True): continue
    ts=[t for t in d["tracks"] if t.get("energy") is not None]
    if len(ts)<8: continue
    for i in range(len(ts)):
        v=[ts[i]]
        for t in ts[i+1:]:
            if t["pos"]!=v[-1]["pos"]+1: break
            v.append(t)
            if len(v)==18: break
        if len(v)<8: continue
        es=[t["energy"] for t in v]
        a=ac([b-a for a,b in zip(es,es[1:])]); c=corr(list(range(len(es))),es)
        if a is not None: ref_ac.append(a)
        if c is not None: ref_cp.append(c)
        ref_rg.append(max(es)-min(es))

pool={t["id"]:t for t in json.loads(Path("data/pool.json").read_text(encoding="utf-8"))}
our_ac,our_cp,our_rg=[],[],[]
for num in NUMS:
    f=BASE/f"set_{num}.json"
    if not f.exists(): continue
    es=[pool[t["content_id"]]["energy"] for t in json.loads(f.read_text(encoding="utf-8"))["tracks"] if t["content_id"] in pool]
    a=ac([b-a for a,b in zip(es,es[1:])]); c=corr(list(range(len(es))),es)
    if a is not None: our_ac.append(a)
    if c is not None: our_cp.append(c)
    our_rg.append(max(es)-min(es))

def compara(nom,ours,refs):
    r=sorted(refs)
    lo,hi=r[len(r)//10],r[(9*len(r))//10]          # p10-p90 de la referencia
    q1,q3=r[len(r)//4],r[(3*len(r))//4]
    dentro_iqr=sum(1 for v in ours if q1<=v<=q3)
    dentro_rango=sum(1 for v in ours if lo<=v<=hi)
    # cuantos de los NUESTROS superan a un valor de referencia al azar
    sup=sum(1 for v in ours for w in refs if v>w)/(len(ours)*len(refs))
    print(f"\n{nom}")
    print(f"  referencia (n={len(refs)}):  mediana {st.median(refs):+.2f}   "
          f"IQR [{q1:+.2f}..{q3:+.2f}]   p10-p90 [{lo:+.2f}..{hi:+.2f}]")
    print(f"  nuestro    (n={len(ours)}):  mediana {st.median(ours):+.2f}   "
          f"{dentro_iqr}/{len(ours)} en el IQR ({dentro_iqr/len(ours):.0%}, un set real da 50%)   "
          f"{dentro_rango}/{len(ours)} en p10-p90 ({dentro_rango/len(ours):.0%}, real 80%)")
    print(f"  probabilidad de que un set nuestro supere a una ventana real: {sup:.0%} "
          f"(0.50 = misma distribucion)")

print(f"targets medidos: {BASE}")
compara("autocorrelacion de saltos",our_ac,ref_ac)
compara("corr(posicion, energia)",our_cp,ref_cp)
compara("rango de energia",our_rg,ref_rg)


# --- Armonia y tempo contra los pros -----------------------------------------
# Agregado el 2026-09-21. El set 139 se "mejoro" de 31% a 0% de pasos sin mover
# la rueda usando un 14% de referencia citado en un comentario viejo; medido ese
# dia contra 11 DJs era 29%, y la mejora lo alejo de los profesionales. Desde
# aca, cualquier ajuste de armonia se mide contra ellos en el momento.
def _armonia(sets_propios: list[list[dict]]) -> None:
    from collections import Counter
    from itertools import groupby
    CAM = {f"{i}{L}": (i, L) for i in range(1, 13) for L in "AB"}

    def dist(a, b):
        (x, lx), (y, ly) = CAM[a], CAM[b]
        r = min((x - y) % 12, (y - x) % 12)
        return r if lx == ly else r + 1

    def paso(a, b):
        dl = (CAM[b][0] - CAM[a][0] + 6) % 12 - 6
        return "+" if dl > 0 else "-" if dl < 0 else "="

    def metricas(tramos):
        dc, n, quieto, runs, bpm = Counter(), 0, 0, [], []
        for tr in tramos:
            ps = []
            for a, b in zip(tr, tr[1:]):
                if a.get("key") in CAM and b.get("key") in CAM:
                    dc[min(dist(a["key"], b["key"]), 3)] += 1
                    n += 1
                    quieto += CAM[a["key"]][0] == CAM[b["key"]][0]
                    ps.append(paso(a["key"], b["key"]))
                if a.get("bpm") and b.get("bpm"):
                    bpm.append(abs(b["bpm"] - a["bpm"]))
            runs += [len(list(g)) for k, g in groupby(ps) if k != "="]
        return dc, n, quieto, runs, bpm

    ref = []
    for f in sorted(glob.glob("data/setlists/*.json")):
        d = json.load(open(f, encoding="utf-8"))
        if not d.get("orden_confiable", True):
            continue
        cur = []
        for t in d["tracks"]:
            if not t.get("key") or (cur and t["pos"] != cur[-1]["pos"] + 1):
                if len(cur) > 1:
                    ref.append(cur)
                cur = []
            if t.get("key"):
                cur.append(t)
        if len(cur) > 1:
            ref.append(cur)
    R, O = metricas(ref), metricas(sets_propios)
    print("\nARMONIA Y TEMPO (transiciones consecutivas)")
    print(f"  {'':30} {'pros':>7} {'nuestro':>8}")
    for k, lab in ((0, "misma key"), (1, "un paso (o relativa)"), (2, "dos pasos"), (3, "tres o mas")):
        print(f"  {lab:<30} {R[0][k]/R[1]:>7.0%} {O[0][k]/max(1, O[1]):>8.0%}")
    print(f"  {'sin mover el numero':<30} {R[2]/R[1]:>7.0%} {O[2]/max(1, O[1]):>8.0%}")
    print(f"  {'escalera mas larga':<30} {max(R[3]):>7} {max(O[3] or [0]):>8}")
    print(f"  {'saltos de BPM > 2':<30} {sum(1 for x in R[4] if x > 2)/len(R[4]):>7.0%} "
          f"{sum(1 for x in O[4] if x > 2)/max(1, len(O[4])):>8.0%}")
    print(f"  (pros: {R[1]} transiciones con key)")


if __name__ == "__main__":
    _pool = {t["id"]: t for t in json.loads(Path("data/pool.json").read_text(encoding="utf-8"))}
    _nums = NUMS
    _sets = []
    for _n in _nums:
        _f = BASE / f"set_{_n}.json"
        if _f.exists():
            _sets.append([_pool[t["content_id"]] for t in
                          json.loads(_f.read_text(encoding="utf-8"))["tracks"]
                          if t["content_id"] in _pool])
    _armonia(_sets)
