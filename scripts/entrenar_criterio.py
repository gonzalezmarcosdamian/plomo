# -*- coding: utf-8 -*-
"""Ajusta los pesos del solver contra los DJ de referencia, en vez de a ojo.

QUE HACE
--------
Arma sets de prueba con distintos juegos de pesos, mide cada uno con la misma
vara que a los setlists reales de `data/setlists/`, y se queda con el juego que
deja nuestros sets mas cerca de ellos. Es descenso por coordenadas: mueve un
peso por vez, dos pasadas, arrancando de lo que dicen las reglas.

LA JERARQUIA ES UNA RESTRICCION, NO UN RESULTADO
------------------------------------------------
El DJ fijo el orden el 2026-09-23: "quiero que domine la energia y groove
constante, luego lo progresivo y luego recien la cuota de genero; artistas le
gana, productores le gana a cuota de genero". El loop NO puede romperlo: solo
prueba combinaciones donde

    arco >= groove >= progresivo >= ajeno >= mezcla,   con arco > mezcla

Lo que el loop elige es cuanto vale cada escalon, no quien va arriba. Si el
optimo numerico quisiera poner la cuota de genero primera, no se puede llegar
ahi, y esta bien que no se pueda: el criterio lo pone el DJ y los numeros lo
afinan.

QUE SE MIDE
-----------
Todo sobre pares CONSECUTIVOS, porque un hueco en un setlist no es una
transicion. Cinco rasgos, cada uno con su objetivo medido en el momento:

    paso de energia     cuanto se mueve la energia entre dos temas
    salto de groove     densidad ritmica y graves (data/groove_index.json)
    paso de BPM         cuanto tempo se mueve
    corr(pos, energia)  si el set es una rampa o respira
    top-5 artistas      que fraccion del set aportan los 5 mas repetidos

La perdida es la suma de las diferencias relativas. No se promedia con el
objetivo de "parecerse en todo": un set que empata en cuatro rasgos y se va al
doble en el quinto pierde contra uno parejo, que es lo que se quiere.

OJO CON LA CIRCULARIDAD
-----------------------
Esto ajusta contra SETLISTS AJENOS, no contra nuestros sets: medir el solver
contra lo que el solver produjo no prueba nada. Ver
docs/APRENDIZAJES.md, "El backtest contra sets propios es circular".

USO
---
    python scripts/entrenar_criterio.py                 # entrena y muestra
    python scripts/entrenar_criterio.py --aplicar       # ademas escribe reglas
    python scripts/entrenar_criterio.py --beam 200      # mas fino, mas lento
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import select_set as S  # noqa: E402

CONFIGS = ["cumple_zorro_warm.json", "cumple_zorro.json", "cumple_zorro_3a5.json"]

# que peso mueve cada coordenada, y que valores se le prueban
CANDIDATOS = {
    "PESO_ARCO": [4.0, 6.0, 8.0],
    "PESO_GROOVE": [2.0, 4.0, 6.0],
    "PESO_PROG": [1.0, 2.5, 4.0],
    "PESO_AJENO": [0.5, 2.0, 3.5],
    "PESO_MEZCLA": [0.5, 1.5, 3.0],
}
ORDEN = ["PESO_ARCO", "PESO_GROOVE", "PESO_PROG", "PESO_AJENO", "PESO_MEZCLA"]

# Los TECHOS no son pesos: son restricciones duras que recortan lo que el solver
# puede siquiera considerar. Entraron al loop porque la primera corrida se clavo
# en una perdida de 2.55 con nuestros sets dando pasos de energia de 0.60 contra
# 1.00 de los pros: con max_escalon en 1.3 y un p90 de referencia de 2.50, no
# habia peso capaz de cerrar esa diferencia. Ajustar pesos contra un techo que
# aprieta es girar la perilla equivocada.
TECHOS = {
    "MAX_E_STEP": [1.3, 1.8, 2.3, 2.8],
    "MAX_BPM_JUMP": [2.0, 3.0, 4.0, 5.0],
}
CANDIDATOS.update(TECHOS)
ORDEN = ORDEN + list(TECHOS)


def jerarquia_ok(p: dict) -> bool:
    """El orden del DJ: energia y groove arriba, cuota de genero abajo.

    Se pide NO CRECIENTE con empates permitidos, y que la punta este
    estrictamente arriba del final. Con desigualdades estrictas en cada escalon
    la grilla se vaciaba: de 15 candidatos quedaban 2, y el loop no exploraba
    nada. Un empate entre dos escalones vecinos no rompe el criterio del DJ; que
    la cuota de genero le gane a la energia, si.
    """
    v = [p[k] for k in ORDEN if k.startswith("PESO_")]
    return all(a >= b for a, b in zip(v, v[1:])) and v[0] > v[-1]


# --------------------------------------------------------------- los objetivos
def _groove_de(ids: list[str]) -> list[tuple[float, float]]:
    g = S._GROOVE.get("tracks", {})
    sd = S._GR_SD
    return [(g[i][0] / sd[0], g[i][1] / sd[1]) if i in g else None for i in ids]


def rasgos(energias, bpms, keys, artistas, grooves) -> dict:
    """Los cinco rasgos de una secuencia. None donde no hay dato suficiente."""
    pasos = [abs(b - a) for a, b in zip(energias, energias[1:])
             if a is not None and b is not None]
    pbpm = [abs(b - a) for a, b in zip(bpms, bpms[1:]) if a and b]
    saltos = [abs(b[0] - a[0]) + abs(b[1] - a[1])
              for a, b in zip(grooves, grooves[1:]) if a and b]
    e_val = [e for e in energias if e is not None]
    corr = None
    if len(e_val) >= 8 and st.pstdev(e_val) > 0:
        corr = float(np.corrcoef(np.arange(len(e_val)), e_val)[0, 1])
    top5 = None
    if len(artistas) >= 10:
        from collections import Counter
        c = Counter(a for a in artistas if a)
        if c:
            top5 = sum(n for _, n in c.most_common(5)) / sum(c.values())
    return {
        "paso_energia": float(np.median(pasos)) if pasos else None,
        "salto_groove": float(np.median(saltos)) if saltos else None,
        "paso_bpm": float(np.median(pbpm)) if pbpm else None,
        "corr_pos_energia": corr,
        "top5_artistas": top5,
    }


def objetivos() -> dict:
    """Los rasgos de los DJ de referencia, medidos en el momento."""
    acum = {k: [] for k in ("paso_energia", "salto_groove", "paso_bpm",
                            "corr_pos_energia", "top5_artistas")}
    # el indice de groove esta por content id; para los setlists hay que ir por
    # titulo, asi que se reusa el mismo criterio que scripts/groove por nombre
    idx_titulo = {}
    for cid, v in S._GROOVE.get("tracks", {}).items():
        idx_titulo[cid] = v
    n = 0
    for f in sorted((RAIZ / "data" / "setlists").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if not d.get("orden_confiable"):
            continue
        n += 1
        tr = d["tracks"]
        # cortar en tramos consecutivos: un hueco no es una transicion
        tramos, actual = [], []
        for t in tr:
            if actual and t["pos"] != actual[-1]["pos"] + 1:
                tramos.append(actual)
                actual = []
            actual.append(t)
        tramos.append(actual)
        for tramo in tramos:
            if len(tramo) < 3:
                continue
            r = rasgos([t.get("energy") for t in tramo],
                       [t.get("bpm") for t in tramo],
                       [t.get("key") for t in tramo],
                       [t.get("artist") for t in tramo],
                       [None] * len(tramo))
            for k, v in r.items():
                if v is not None:
                    acum[k].append(v)
        # top-5 y correlacion se miden sobre el set entero, no por tramo
        r = rasgos([t.get("energy") for t in tr], [t.get("bpm") for t in tr],
                   [t.get("key") for t in tr], [t.get("artist") for t in tr],
                   [None] * len(tr))
        for k in ("corr_pos_energia", "top5_artistas"):
            if r[k] is not None:
                acum[k].append(r[k])
    obj = {k: float(np.median(v)) for k, v in acum.items() if v}
    # el salto de groove no sale de los setlists (no todos sus temas estan en la
    # biblioteca indexada): viene medido aparte, sobre los 236 pares que si
    obj["salto_groove"] = S._GROOVE.get("referencia_salto_mediano", 1.25)
    obj["_n_setlists"] = n
    return obj


# ------------------------------------------------------------------ evaluacion
def armar(pesos: dict, beam: int) -> list:
    """Arma los sets de prueba con esos pesos. Devuelve las secuencias."""
    for k, v in pesos.items():
        setattr(S, k, v)
    # El beam del entrenamiento se fuerza acá: los configs traen el suyo, y
    # respetarlo hacía que --beam no cambiara nada. Un beam chico no busca peor
    # criterio, busca menos: sirve para comparar pesos entre sí, y el set final
    # se arma después con el beam de produccion.
    original = S.select
    S.MAX_E_STEP = pesos["MAX_E_STEP"]
    forzar = {"beam": beam, "max_bpm_jump": pesos["MAX_BPM_JUMP"]}
    S.select = lambda *a, **k: original(*a, **{**k, **forzar})
    try:
        seqs = []
        for nombre in CONFIGS:
            for _spec, seq in S.correr(RAIZ / "data/set_configs" / nombre,
                                       escribir=False, callado=True):
                seqs.append(seq)
    finally:
        S.select = original
    return seqs


def medir(seqs: list) -> dict:
    vals = {k: [] for k in ("paso_energia", "salto_groove", "paso_bpm",
                            "corr_pos_energia", "top5_artistas")}
    for seq in seqs:
        r = rasgos([t["energy"] for t in seq], [t["bpm"] for t in seq],
                   [t["key"] for t in seq], [t["artist"] for t in seq],
                   _groove_de([t["id"] for t in seq]))
        for k, v in r.items():
            if v is not None:
                vals[k].append(v)
    return {k: float(np.median(v)) for k, v in vals.items() if v}


def perdida(nuestro: dict, obj: dict) -> float:
    """Suma de diferencias relativas. Cada rasgo pesa igual."""
    total = 0.0
    for k, o in obj.items():
        if k.startswith("_") or k not in nuestro:
            continue
        escala = abs(o) if abs(o) > 0.2 else 0.2
        total += abs(nuestro[k] - o) / escala
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--beam", type=int, default=120,
                    help="beam del entrenamiento; mas alto es mas fiel y mas lento")
    ap.add_argument("--pasadas", type=int, default=2)
    ap.add_argument("--aplicar", action="store_true", help="escribe los pesos ganadores en las reglas")
    args = ap.parse_args()

    obj = objetivos()
    print(f"objetivos, medidos sobre {obj.pop('_n_setlists')} setlists de referencia:")
    for k, v in obj.items():
        print(f"   {k:20s} {v:+.2f}")

    pesos = {k: float(getattr(S, k)) for k in ORDEN if k.startswith("PESO_")}
    pesos["MAX_E_STEP"] = float(S.MAX_E_STEP)
    pesos["MAX_BPM_JUMP"] = 2.0
    print(f"\narranque (reglas {json.loads((RAIZ/'rules/curaduria.json').read_text(encoding='utf-8'))['_meta']['version']}): "
          + "  ".join(f"{k.replace('PESO_','').lower()} {v}" for k, v in pesos.items()))

    base = medir(armar(pesos, args.beam))
    mejor = perdida(base, obj)
    print(f"perdida de arranque: {mejor:.3f}")
    for k, v in base.items():
        print(f"   {k:20s} {v:+.2f}   (pro {obj[k]:+.2f})")

    print("\n--- descenso por coordenadas " + "-" * 40)
    for pasada in range(1, args.pasadas + 1):
        for coord in ORDEN:
            for val in CANDIDATOS[coord]:
                if val == pesos[coord]:
                    continue
                prueba = dict(pesos, **{coord: val})
                if not jerarquia_ok(prueba):
                    continue
                p = perdida(medir(armar(prueba, args.beam)), obj)
                marca = ""
                if p < mejor - 1e-6:
                    mejor, pesos = p, prueba
                    marca = "  <-- mejora"
                print(f"  p{pasada} {coord.replace('PESO_','').lower():9s} {val:>4}  "
                      f"perdida {p:.3f}{marca}")

    final = medir(armar(pesos, args.beam))
    print("\n" + "=" * 62)
    print(f"pesos entrenados (perdida {mejor:.3f}):")
    for k, v in pesos.items():
        print(f"   {k.replace('PESO_','').lower():12s} {v}")
    print("\nrasgo                 nuestro      pro")
    for k, v in final.items():
        print(f"   {k:20s} {v:+.2f}    {obj[k]:+.2f}")

    destino = RAIZ / "data" / "criterio_entrenado.json"
    destino.write_text(json.dumps(
        {"generado": "scripts/entrenar_criterio.py", "beam_entrenamiento": args.beam,
         "objetivos_pro": obj, "pesos": pesos, "rasgos_finales": final,
         "perdida": mejor}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n-> {destino.relative_to(RAIZ)}")

    if args.aplicar:
        rp = RAIZ / "rules" / "curaduria.json"
        r = json.loads(rp.read_text(encoding="utf-8"))
        donde = {"MAX_E_STEP": ("energia", "max_escalon"),
                 "PESO_ARCO": ("energia", "peso_desvio_arco"),
                 "PESO_GROOVE": ("groove", "peso_continuidad"),
                 "PESO_PROG": ("estilo", "peso_progresivo"),
                 "PESO_AJENO": ("sonido_propio", "peso_ajeno"),
                 "PESO_MEZCLA": ("genero", "peso_mezcla")}
        for k, (sec, campo) in donde.items():
            r[sec][campo]["valor"] = pesos[k]
            r[sec][campo]["porque"] += (f" | Entrenado contra los setlists de referencia el "
                                        f"2026-09-23 (scripts/entrenar_criterio.py, perdida {mejor:.3f}).")
        rp.write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
        print("reglas actualizadas con los pesos entrenados")


if __name__ == "__main__":
    main()
