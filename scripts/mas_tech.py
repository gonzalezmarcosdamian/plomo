# -*- coding: utf-8 -*-
"""Hace que un set suene mas tech que el que lo precede en la noche.

QUE ES "TECH", Y POR QUE ES UNA DECISION Y NO UNA MEDICION
El DJ etiqueto dos temas como tecnosos y estan en extremos opuestos de todo lo
que el proyecto mide: High On tiene color p16 y graves 66, Muse color p97 y
graves 42. Lo unico que comparten es DENSIDAD BAJA (11.6 y 8.3, las dos mas
bajas de sus sets). O sea que para el, tech es DESPOJADO, no oscuro.

Con dos casos no alcanza para una regla, asi que esto operacionaliza "mas tech
que el anterior" como: MENOS COLOR y MAS BPM que el set que va antes. Es una
eleccion, no un hallazgo, y esta escrita aca para que se pueda discutir.

Lo que NO se toca: lo que el DJ marco, el piso de graves, ni la estructura que
viene eligiendo --pocas secciones y drop largo--. Mas tech no puede costar
groove.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LIB = RAIZ / "data/recetas/lib"
GLOBAL = re.compile(r"malisimo|horrible|todo lo que no quiero|afro", re.I)
GENEROS = {"Progressive House", "Melodic House & Techno"}


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s or "")
                if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def titulo_base(t: str) -> str:
    return re.sub(r"\s*[\(\[].*$", "", t).strip().lower()


def cam(a: str, b: str) -> int:
    n1, l1 = int(a[:-1]), a[-1]
    n2, l2 = int(b[:-1]), b[-1]
    d = min((n1 - n2) % 12, (n2 - n1) % 12)
    return d + (0 if l1 == l2 or d == 0 else 1)


def est(c: str) -> dict | None:
    fp = LIB / f"{c}.json"
    if not fp.exists():
        return None
    ss = json.loads(fp.read_text(encoding="utf-8"))["referencia"].get("secciones") or []
    if not ss:
        return None
    tot = sum(s["compases"] for s in ss) or 1
    return {"secc": len(ss),
            "drop": max((s["compases"] for s in ss if s["tipo"] == "drop"), default=0) / tot}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", type=int, required=True)
    ap.add_argument("--contra", type=int, required=True,
                    help="el set que va antes en la noche")
    ap.add_argument("--cambiar", type=int, default=5)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    POOL = {str(t["id"]): t for t in json.loads(
        (RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
    G = json.loads((RAIZ / "data/groove_index.json").read_text(encoding="utf-8"))
    DEN, COL = G["tracks"], G["color_pct"]
    EP = json.loads((RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8"))

    f = RAIZ / f"data/set_targets/set_{a.set}.json"
    doc = json.loads(f.read_text(encoding="utf-8"))
    ids = [str(t["content_id"]) for t in doc["tracks"]]
    prev = [str(t["content_id"]) for t in json.loads(
        (RAIZ / f"data/set_targets/set_{a.contra}.json").read_text(encoding="utf-8"))["tracks"]]

    col_prev = st.median([COL.get(c, 0) for c in prev])
    bpm_prev = st.median([POOL[c]["bpm"] for c in prev])
    print(f"set {a.contra} (va antes): color {col_prev:.2f}  BPM {bpm_prev:.0f}")
    print(f"set {a.set} ahora:        color {st.median([COL.get(c, 0) for c in ids]):.2f}  "
          f"BPM {st.median([POOL[c]['bpm'] for c in ids]):.0f}")
    print(f"objetivo: color abajo de {col_prev:.2f}, BPM arriba de {bpm_prev:.0f}\n")

    ajenos = set()
    for g in (RAIZ / "data/set_targets").glob("set_*.json"):
        if g.stem == f"set_{a.set}":
            continue
        try:
            ts = json.loads(g.read_text(encoding="utf-8")).get("tracks") or []
        except Exception:
            continue
        ajenos |= {str(x["content_id"]) for x in ts if "content_id" in x}

    malos = {titulo_base(v.get("title", "")) for v in EP.values()
             if isinstance(v, dict) and (v.get("veto") or re.search(
                 r"oscur|malisimo|horrible", v.get("nota") or "", re.I))}
    fuera = set()
    for k, v in EP.items():
        if not isinstance(v, dict):
            continue
        ve = v.get("veto")
        alc = ve.get("alcance", "") if isinstance(ve, dict) else ""
        if ve and (GLOBAL.search(v.get("nota") or "")
                   or str(a.set) in f"{v.get('fuente', '')} {alc}"):
            fuera.add(k)
        if v.get("gastado") or v.get("groove_ok") is False:
            fuera.add(k)

    def marcado(c: str) -> bool:
        v = EP.get(c, {})
        return bool(v.get("favorito") or v.get("rol") or v.get("referencia_de"))

    # salen los MAS coloridos sin marca: son los que alejan al set de lo tech
    flojos = sorted((c for c in ids if not marcado(c)),
                    key=lambda c: -COL.get(c, 0))[:a.cambiar]
    ocup = {norm(POOL[c]["artist"]) for c in ids}
    # titulos ya presentes en CUALQUIER set: dos remixes del mismo tema en dos
    # sets de la misma noche se escuchan como el mismo tema repetido.
    titulos_set = set()
    for g in (RAIZ / "data/set_targets").glob("set_*.json"):
        try:
            ts = json.loads(g.read_text(encoding="utf-8")).get("tracks") or []
        except Exception:
            continue
        for x in ts:
            if "content_id" in x and str(x["content_id"]) in POOL:
                titulos_set.add(titulo_base(POOL[str(x["content_id"])]["title"]))
    cambios: list[tuple[str, str]] = []
    for viejo in flojos:
        i = ids.index(viejo)
        ant = ids[i - 1] if i else None
        sig = ids[i + 1] if i + 1 < len(ids) else None
        mejor, mk = None, 1e9
        for c, t in POOL.items():
            if c in ids or c in fuera or c in ajenos:
                continue
            if titulo_base(t["title"]) in malos or titulo_base(t["title"]) in titulos_set:
                continue
            if c in [n for _, n in cambios]:
                continue
            if norm(t["artist"]) in ocup - {norm(POOL[viejo]["artist"])}:
                continue
            if t.get("genre") not in GENEROS:
                continue
            if t["bpm"] < bpm_prev or not (119 <= t["bpm"] <= 127):
                continue
            # BANDA, no minimo. Minimizar el color trae lo mas gris de la
            # biblioteca --p03 a p14-- y eso no es "mas tech que el anterior",
            # es otro set. Se busca claramente por debajo del anterior pero
            # dentro de lo que el DJ viene aprobando.
            col = COL.get(c, 1)
            if not (col_prev - 0.45 <= col <= col_prev - 0.15):
                continue
            d, e = DEN.get(c), est(c)
            if not d or not e or d[1] < 40:
                continue
            if e["secc"] > 8 or e["drop"] < 0.30:
                continue
            if abs(t["energy"] - POOL[viejo]["energy"]) > 1.0:
                continue
            if ant and cam(POOL[ant]["key"], t["key"]) > 2:
                continue
            if sig and cam(t["key"], POOL[sig]["key"]) > 2:
                continue
            # se premia el BPM y el groove, no el color bajo: el color ya
            # quedo acotado por la banda de arriba.
            k = -(t["bpm"] - bpm_prev) * 0.05 - d[1] / 100 - e["drop"]
            if k < mk:
                mejor, mk = c, k
        if mejor:
            cambios.append((viejo, mejor))
            ocup.add(norm(POOL[mejor]["artist"]))

    if not cambios:
        print("sin candidatos que bajen el color sin romper groove ni estructura")
        return
    for viejo, nuevo in cambios:
        ids[ids.index(viejo)] = nuevo
        print(f"  color {COL.get(viejo, 0):.2f} -> {COL.get(nuevo, 0):.2f}   "
              f"BPM {POOL[viejo]['bpm']:.0f} -> {POOL[nuevo]['bpm']:.0f}   "
              f"sale {POOL[viejo]['title'][:30]}")
        print(f"      entra {POOL[nuevo]['artist']} - {POOL[nuevo]['title']}")
    print(f"\nset {a.set} queda: color {st.median([COL.get(c, 0) for c in ids]):.2f}  "
          f"BPM {st.median([POOL[c]['bpm'] for c in ids]):.0f}  "
          f"graves {st.median([DEN.get(c, [0, 0])[1] for c in ids]):.1f}")
    if a.dry:
        return
    doc["tracks"] = [{"artist": POOL[c]["artist"], "title": POOL[c]["title"],
                      "content_id": c} for c in ids]
    doc["_nota"] = doc.get("_nota", "") + (
        f" | 2026-10-01: mas tech que el set {a.contra}, que va antes en la noche. 'Tech' se "
        "operacionalizo como menos color y mas BPM, porque los dos temas que el DJ llamo tecnosos "
        "--High On color p16 y Muse color p97-- solo coinciden en densidad baja y no alcanzan para "
        "una regla. Es una eleccion, no un hallazgo. No se toco lo marcado por el DJ, ni el piso de "
        "graves, ni la estructura de pocas secciones y drop largo.")
    f.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
