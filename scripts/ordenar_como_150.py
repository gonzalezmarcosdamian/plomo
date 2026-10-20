# -*- coding: utf-8 -*-
"""Elige y ordena un set de un pool chico con el criterio del 150: subir sin desinflarse.

POR QUE
-------
"El 150 lo toque, es la session 2, tomalo como algo modelo" (el DJ, 2026-10-19). El 150
sube de punta a punta --bajar energia costaba 12 por punto despues de que el DJ dijera
"arranca los 3 primeros top y luego cae"-- y no tiene un solo salto de rueda mayor a 1.
select_set.py esta calibrado para pools de mil temas: con los 27 de Cumple del 20 armo
15 temas que suben y bajan (5.8, 4.2, 5.8, 6.3, 5.2...) y seis saltos de 2. Con un pool
chico se puede buscar casi todo: haz de busqueda sobre secuencias, con el costo del 150.

COSTO (por paso)
----------------
  bajar energia      12 por punto (el del 150)
  subir mas de 1.2   2 por punto de mas (un escalon, no un acantilado)
  rueda a 2 pasos    15; a 3 o mas, prohibido
  BPM a mas de 2     prohibido
  tema en `preferir` -3 (los que pasan el sonido del 150)
Las `anclas` tienen que estar, y en la parte del set que dice `anclas_desde`.

LO AJENO NO ENTRA SOLO
----------------------
Un tema cuyo artista Y sello no aparecen nunca en lo que el DJ toco (data/mundo_propio.json)
sale del pool, salvo que sea ancla o `preferir`: lo que el DJ eligio se respeta aunque sea
ajeno, lo que agrega el buscador no. "El tema fly for me algo asi no va... aprende por que lo
pusiste mal" (2026-10-20): en el 157, Habitatt - Fly With Me (sello Experts Only) era el unico
ajeno de los 9 temas que sume yo, el 21 de 25 en parecido, y entro porque daba el 6A que la
rueda pedia entre 5A y 6B. Cobrarlo con el 2.0 de sonido_propio.peso_ajeno no alcanzaba: un
salto de rueda cuesta 15. `--con-ajenos` los deja, marcados.

USO
---
    python scripts/ordenar_como_150.py data/pool_cumple_del_20.json --n 18
        --anclas 6435521 83535228 --preferir 240643135 ...
        --nombre "153. Session 03 · Cumple del 20 — 1h45 — 2026-10-19" --salida data/set_targets/set_153.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from plomo.camelot import distance  # noqa: E402

COSTO_BAJAR = 12.0
ESCALON = 1.2
COSTO_SUBIR_DE_MAS = 2.0
COSTO_RUEDA_2 = 15.0
PREMIO_PREFERIDO = 3.0
MAX_BPM = 2.0
MAX_POR_ARTISTA = 4   # rules/curaduria.json repeticion.max_por_artista_en_set
HAZ = 30000


def paso(a: dict, b: dict) -> float | None:
    rueda = distance(a["key"], b["key"])
    if rueda > 2 or abs(a["bpm"] - b["bpm"]) > MAX_BPM:
        return None
    d = b["energy"] - a["energy"]
    costo = COSTO_RUEDA_2 if rueda == 2 else 0.0
    costo += COSTO_BAJAR * -d if d < 0 else COSTO_SUBIR_DE_MAS * max(0.0, d - ESCALON)
    return costo


def _norm(s: str | None) -> str:
    # los tags de la biblioteca traen espacios de mas ("All Day I Dream ")
    return " ".join((s or "").split()).lower()


def mundo() -> tuple[set[str], set[str]]:
    """Los artistas y sellos de lo que el DJ toco o marco como favorito."""
    mp = json.loads((RAIZ / "data" / "mundo_propio.json").read_text(encoding="utf-8"))
    return {_norm(a) for a in mp["artistas"]}, {_norm(s) for s in mp["sellos"]}


def es_ajeno(t: dict, artistas: set[str], sellos: set[str]) -> bool:
    nombres = {_norm(x) for x in re.split(r",|&| x | feat\.? ", t["artist"]) if x.strip()}
    return not (nombres & artistas) and _norm(t.get("label")) not in sellos


def buscar(pool: list[dict], n: int, anclas: set[str], preferir: set[str], anclas_desde: float) -> tuple[float, list[int]]:
    premio = [-PREMIO_PREFERIDO if t["id"] in preferir else 0.0 for t in pool]
    minimo_ancla = int(anclas_desde * n)
    haz = [(premio[i], [i]) for i, t in enumerate(pool) if t["id"] not in anclas or minimo_ancla == 0]
    for pos in range(1, n):
        nuevos = {}
        for costo, seq in haz:
            usados = set(seq)
            por_artista = Counter(pool[i]["artist"] for i in seq)
            faltan = [a for a in anclas if a not in {pool[i]["id"] for i in seq}]
            if len(faltan) > n - pos:
                continue
            for j, t in enumerate(pool):
                if j in usados or por_artista[t["artist"]] >= MAX_POR_ARTISTA:
                    continue
                if t["id"] in anclas and pos < minimo_ancla:
                    continue
                c = paso(pool[seq[-1]], t)
                if c is None:
                    continue
                clave = (frozenset(usados | {j}), j)
                total = costo + c + premio[j]
                if clave not in nuevos or nuevos[clave][0] > total:
                    nuevos[clave] = (total, seq + [j])
        haz = sorted(nuevos.values())[:HAZ]
    completos = [(c, s) for c, s in haz if anclas <= {pool[i]["id"] for i in s}]
    if not completos:
        sys.exit("no hay un orden que cumpla: probar con menos temas o sin alguna ancla")
    return completos[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pool")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--anclas", nargs="*", default=[])
    ap.add_argument("--anclas-desde", type=float, default=0.55, help="fraccion del set desde donde van las anclas")
    ap.add_argument("--preferir", nargs="*", default=[])
    ap.add_argument("--con-ajenos", action="store_true", help="no saca los ajenos que no son ancla ni preferir")
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--nota", default="")
    ap.add_argument("--salida")
    a = ap.parse_args()

    pool = json.loads((RAIZ / a.pool).read_text(encoding="utf-8"))
    artistas, sellos = mundo()
    elegidos = set(a.anclas) | set(a.preferir)
    ajenos = {t["id"] for t in pool if t["id"] not in elegidos and es_ajeno(t, artistas, sellos)}
    if ajenos and not a.con_ajenos:
        print(f"fuera del pool por ajenos ({len(ajenos)}): "
              + "; ".join(f"{t['artist']} - {t['title']}" for t in pool if t["id"] in ajenos))
        pool = [t for t in pool if t["id"] not in ajenos]
    costo, seq = buscar(pool, a.n, set(a.anclas), set(a.preferir), a.anclas_desde)
    temas = [pool[i] for i in seq]
    print(f"{a.nombre}  (costo {costo:.1f})")
    for k, t in enumerate(temas):
        r = distance(temas[k - 1]["key"], t["key"]) if k else 0
        print(f"{k + 1:3d}. E{t['energy']:.1f} {t['bpm']:5.1f} {t['key']:>4}{'  <-- rueda 2' if r == 2 else ''}"
              f"{'  *' if t['id'] in a.preferir else ''}{'  ANCLA' if t['id'] in a.anclas else ''}"
              f"{'  AJENO' if t['id'] in ajenos else ''}   {t['artist']} - {t['title']}")
    bajadas = [round(temas[k - 1]["energy"] - temas[k]["energy"], 1) for k in range(1, len(temas))
               if temas[k]["energy"] < temas[k - 1]["energy"]]
    print(f"duracion de los archivos {sum(t['dur_seg'] for t in temas) / 60:.0f} min; bajadas de energia: {bajadas or 'ninguna'}")
    if a.salida:
        doc = {"name": a.nombre, "duration_h": 0, "bpm_range": [100, 140], "max_per_artist": MAX_POR_ARTISTA,
               "keep_order": True, "_nota": a.nota,
               "tracks": [{"artist": t["artist"], "title": t["title"], "content_id": t["id"]} for t in temas]}
        Path(RAIZ / a.salida).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"-> {a.salida}")


if __name__ == "__main__":
    main()
