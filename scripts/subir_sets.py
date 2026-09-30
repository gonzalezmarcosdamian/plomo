# -*- coding: utf-8 -*-
"""Sube la energia de un set SIN romper el groove.

POR QUE
El DJ, 2026-09-30: "los otros sets necesito que sean mas arriba pero mismo groove
para poder subir o cambiar de set si quiero". O sea: quiere poder saltar de un set
a otro en vivo, y para eso los sets tienen que estar a la misma altura y con el
mismo pulso. Un set que arranca en 4.1 no se puede intercalar con uno que va por 7.

QUE HACE
Cambia los temas mas bajos --y solo los que el DJ NO marco-- por otros con mas
energia que ademas NO corten el groove: el que entra tiene que tener graves >= 40
(groove.piso_graves) y un salto de densidad+graves contra sus dos vecinos menor o
igual al que tenia el que sale.

QUE NO HACE
No toca nada marcado por el DJ: favorito, rol, referencia_de o groove_ok. Lo que
el escucho y aprobo no se mueve por un numero.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PISO_GRAVES = 40.0          # rules/curaduria.json -> groove.piso_graves
GLOBAL = re.compile(r"malisimo|horrible|todo lo que no quiero|afro", re.I)


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s or "")
                if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def cam(a: str, b: str) -> int:
    n1, l1 = int(a[:-1]), a[-1]
    n2, l2 = int(b[:-1]), b[-1]
    d = min((n1 - n2) % 12, (n2 - n1) % 12)
    return d + (0 if l1 == l2 or d == 0 else 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("nums", type=int, nargs="+")
    ap.add_argument("--piso", type=float, default=6.0,
                    help="energia minima que se busca para el set")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    POOL = {str(t["id"]): t for t in json.loads(
        (RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
    G = json.loads((RAIZ / "data/groove_index.json").read_text(encoding="utf-8"))
    DEN, COL = G["tracks"], G["color_pct"]
    EP = json.loads((RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8"))

    def E(c):
        v = EP.get(c, {})
        return v.get("E", POOL[c]["energy"]) if isinstance(v, dict) else POOL[c]["energy"]

    def salto(x, y):
        if not (DEN.get(x, [0])[0] and DEN.get(y, [0])[0]):
            return 0.0
        return abs(DEN[x][0] - DEN[y][0]) + abs(DEN[x][1] - DEN[y][1]) / 10

    # LO QUE YA SUENA EN OTRO SET NO PUEDE ENTRAR. La regla es
    # repeticion.repetidos_entre_sets_consecutivos = 0: es lo que escucha el que
    # te vio dos veces. Sin esto el buscador elige el mismo "mejor" tema para
    # todos los sets --en la primera corrida Remember Me entraba en cuatro-- y
    # ademas se pisa con los que ya estan armados.
    en_otros: dict[str, set[str]] = {}
    todos_los_sets = {}
    for g in sorted((RAIZ / "data/set_targets").glob("set_*.json")):
        try:
            todos_los_sets[g.stem] = {str(t["content_id"]) for t in
                                      json.loads(g.read_text(encoding="utf-8"))["tracks"]}
        except Exception:
            pass
    usados_global: set[str] = set()

    for num in a.nums:
        ajenos = set()
        for nom, ids_otro in todos_los_sets.items():
            if nom != f"set_{num}":
                ajenos |= ids_otro
        f = RAIZ / "data/set_targets" / f"set_{num}.json"
        if not f.exists():
            print(f"set {num}: no existe")
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        ids = [str(t["content_id"]) for t in doc["tracks"]]

        fuera = set()
        for k, v in EP.items():
            if not isinstance(v, dict):
                continue
            ve = v.get("veto")
            alc = ve.get("alcance", "") if isinstance(ve, dict) else ""
            marca = f"{v.get('fuente', '')} {alc}"
            if ve and (GLOBAL.search(v.get("nota") or "") or str(num) in marca):
                fuera.add(k)
            if v.get("gastado") or v.get("groove_ok") is False:
                fuera.add(k)

        def marcado(c):
            v = EP.get(c, {})
            return bool(v.get("favorito") or v.get("rol") or v.get("referencia_de")
                        or v.get("groove_ok") is True)

        ocup = {norm(POOL[c]["artist"]) for c in ids}
        cambios = []
        # de abajo hacia arriba: primero el mas flojo
        for i in sorted(range(len(ids)), key=lambda i: E(ids[i])):
            viejo = ids[i]
            if marcado(viejo) or E(viejo) >= a.piso:
                continue
            ant = ids[i - 1] if i else None
            sig = ids[i + 1] if i + 1 < len(ids) else None
            tope = (salto(ant, viejo) if ant else 0) + (salto(viejo, sig) if sig else 0)
            mejor, mejor_k = None, 1e9
            for c, t in POOL.items():
                if c in ids or c in fuera or c in [x for _, x, _ in cambios]:
                    continue
                if c in ajenos or c in usados_global:
                    continue
                if norm(t["artist"]) in ocup - {norm(POOL[viejo]["artist"])}:
                    continue
                d = DEN.get(c)
                if not d or d[1] < PISO_GRAVES:
                    continue
                if E(c) < max(a.piso, E(viejo) + 0.5):
                    continue
                if not (119 <= (t.get("bpm") or 0) <= 126):
                    continue
                if abs(t["dur_seg"] - POOL[viejo]["dur_seg"]) > 150:
                    continue
                if ant and cam(POOL[ant]["key"], t["key"]) > 2:
                    continue
                if sig and cam(t["key"], POOL[sig]["key"]) > 2:
                    continue
                nuevo_salto = (salto(ant, c) if ant else 0) + (salto(c, sig) if sig else 0)
                if nuevo_salto > tope + 0.3:      # no puede cortar mas de lo que ya cortaba
                    continue
                k = nuevo_salto - COL.get(c, 0) - (E(c) - E(viejo)) * 0.5
                if k < mejor_k:
                    mejor, mejor_k = c, k
            if mejor:
                cambios.append((i, mejor, viejo))
                ocup.add(norm(POOL[mejor]["artist"]))
                usados_global.add(mejor)

        if not cambios:
            print(f"set {num}: nada que subir sin romper el groove")
            continue
        for i, nuevo, viejo in cambios:
            ids[i] = nuevo
        todos_los_sets[f"set_{num}"] = set(ids)
        es = [E(c) for c in ids]
        sal = [salto(x, y) for x, y in zip(ids, ids[1:]) if salto(x, y)]
        med = sorted(sal)[len(sal) // 2] if sal else 0
        print(f"set {num}: {len(cambios)} cambios | minima {min(es):.1f} | salto groove {med:.2f}")
        for i, nuevo, viejo in cambios:
            print(f"      {E(viejo):.1f} -> {E(nuevo):.1f}  {POOL[viejo]['title'][:30]:<30} "
                  f"por {POOL[nuevo]['artist']} - {POOL[nuevo]['title']}"[:104])
        if a.dry:
            continue
        doc["tracks"] = [{"artist": POOL[c]["artist"], "title": POOL[c]["title"],
                          "content_id": c} for c in ids]
        doc["_nota"] = doc.get("_nota", "") + (
            f" | 2026-09-30: subido con subir_sets.py --piso {a.piso}. El DJ quiere poder saltar "
            "entre sets en vivo, y para eso tienen que estar a la misma altura. Solo se cambiaron "
            "temas que el no marco, y el que entra no corta el groove mas que el que sale.")
        f.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
