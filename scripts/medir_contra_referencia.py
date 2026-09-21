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
BASE=Path(sys.argv[1]) if len(sys.argv)>1 else Path("data/set_targets")

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
for num in range(109,139):
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
