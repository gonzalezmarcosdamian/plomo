# -*- coding: utf-8 -*-
"""Rearma la noche del cumple de Zorro: warm (140), Sizer (139) y cierre (141).

Los tres comparten el groove de Mindloop (Maze 28), que el DJ pidio despues de
escuchar el warm: "extremadamente bueno Mindloop, quiero el warm en este flow".
El sesgo entra como PREFERENCIA, no como filtro: en el 139 y el 141 son retoques,
no un set nuevo, y los temas que el DJ llamo "mi sonido" quedan anclados.

Orden: 139 -> 141 (excluye 139) -> 140 (excluye los dos). Ninguna cancion se
repite en la noche, ni en otra version.

Uso:
    python scripts/armar_noche_zorro.py            # regenera configs y resuelve
    python scripts/armar_noche_zorro.py --solo-config
"""
from __future__ import annotations

import json
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
PY = str(RAIZ / ".venv" / "Scripts" / "python.exe")
LIB = RAIZ / "data" / "recetas" / "lib"

POOL = {t["id"]: t for t in json.loads((RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
PERC = json.loads((RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8"))
E = lambda i: PERC.get(i, {}).get("E", POOL[i].get("energy") or 0)  # noqa: E731
MINDLOOP = "177299920"


def base(t: dict) -> str:
    """El titulo sin version ni feat.: la identidad de la CANCION."""
    x = re.sub(r"\s+feat\.?.*|\s+ft\.?.*", "", t["title"], flags=re.I)
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\s*[\(\[].*", "", x).lower())


def receta(i: str) -> dict | None:
    f = LIB / f"{i}.json"
    if not f.exists():
        return None
    r = json.loads(f.read_text(encoding="utf-8"))["referencia"]
    secs = r["secciones"]
    alta = [x["energia"] for x in secs if x["tipo"] in ("groove", "drop")]
    baja = [x["energia"] for x in secs if x["tipo"] in ("breakdown", "respiro")]
    ea = st.mean(alta) if alta else 0
    return {"medio": r["balance"]["medio"], "aire": r["balance"]["aire"],
            "bd": (min(baja) / ea if baja and ea else 1)}


def gusto_ok(i: str) -> bool:
    """Los filtros que salieron de la escucha del DJ, no reglas del oficio."""
    x = receta(i)
    return x is None or not (x["medio"] < 5 or x["aire"] < 2 or (x["bd"] < 0.30 and E(i) >= 7))


VETOS = {k for k, v in PERC.items()
         if any(w in v.get("nota", "") for w in
                ("tecnoso", "oscuro, baja", "poca energia", "se cae", "lento", "no esta bueno"))}
RANK_MIND = [r["id"] for r in
             json.loads((RAIZ / "data/parecido_mindloop.json").read_text(encoding="utf-8"))
             if r["id"] in POOL]


def ids_de(num: int) -> list[str]:
    f = RAIZ / f"data/set_targets/set_{num}.json"
    return [t["content_id"] for t in json.loads(f.read_text(encoding="utf-8"))["tracks"]] if f.exists() else []


def buscar(titulo: str, artista: str) -> str:
    return next(i for i, t in POOL.items()
                if t["title"].lower().startswith(titulo.lower()) and artista.lower() in t["artist"].lower())


def guardar(nombre: str, cfg: dict) -> Path:
    p = RAIZ / "data/set_configs" / nombre
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def resolver(p: Path) -> None:
    subprocess.run([PY, str(RAIZ / "scripts/select_set.py"), str(p)], cwd=str(RAIZ))


GEN_PROG = {"Progressive House", "Melodic House & Techno"}
GEN_HOUSE = {"House", "Progressive House", "Melodic House & Techno", "Indie Dance"}
GEN_ORG = {"Organic House", "Organic House / Downtempo", "Progressive House", "Afro House"}


def permitidos(generos: set, bpm: tuple, fuera: set, tope_mind: int) -> tuple[list, list]:
    """Elegibles del set y los mas parecidos al groove de Mindloop, en ese orden."""
    ok = [i for i in RANK_MIND
          if (POOL[i].get("genre") or "") in generos and bpm[0] <= POOL[i]["bpm"] <= bpm[1]
          and i not in fuera and i not in VETOS and gusto_ok(i)]
    return ok, ok[:tope_mind]


def noche_fuera(*nums: int) -> set:
    """Todo lo que ya suena esta noche, y cualquier otra version de esas canciones."""
    ids = {i for n in nums for i in ids_de(n)}
    bases = {base(POOL[i]) for i in ids if i in POOL}
    return ids | {i for i, t in POOL.items() if base(t) in bases}


def set_139() -> Path:
    fija = {k: buscar(*v) for k, v in {
        "imentet": ("Imentet", "Morttagua"), "opensea": ("Open Sea", "Cary Crank"),
        "sizer": ("Sizer", "Pietrocola"), "fragma": ("Fragma", "Kamilo"),
        "touch": ("Touch The Sky", "Marsh"), "olimpo": ("Olimpo", "Pavicich"),
        "boxer": ("I'm Lighter With You", "Boxer")}.items()}
    # el pool tiene que dar aire: con 212 candidatos y la apertura fija, el cierre
    # fijo y cuatro anclas, la busqueda se quedaba sin ramas validas
    elig, mind = permitidos(GEN_PROG, (121, 125), set(), 150)
    # el groove vive en energia media: sesgar el pool hacia el se lleva puesto el
    # material de pico. Con Fragma fijo al cierre (E7.5) y la regla de bajar 0.6
    # del pico, el set NECESITA un tema de 8.1+; quedaba uno solo y no habia
    # solucion. Se suman los mas parecidos al groove ENTRE los intensos.
    alta = [i for i in elig if E(i) >= 7.6][:40]
    perm = set(elig[:400]) | set(mind) | set(alta) | set(fija.values())
    cfg = json.loads((RAIZ / "data/set_configs/cumple_zorro.json").read_text(encoding="utf-8"))
    s = cfg["sets"][0]
    s["exclude_ids"] = sorted(i for i, t in POOL.items()
                              if (t.get("genre") or "") in GEN_PROG and i not in perm)
    s["prefer_ids"] = mind
    s["prefer_bonus"] = 1.0
    s["anclas"] = [fija["sizer"], fija["touch"], fija["olimpo"], fija["boxer"]]
    s["anclas_en"] = {fija["sizer"]: [0.55, 0.75], fija["olimpo"]: [0.70, 0.95]}
    s["inicio_fijo"] = [fija["imentet"], fija["opensea"]]
    s["cierre_fijo"] = [fija["fragma"]]
    s["_identidad"] = (s["_identidad"].split(" v5 (22/9)")[0] +
                       " v6 (22/9): mismo set con el groove de Mindloop en el relleno. Quedan fijos los "
                       "que el DJ llamo mi sonido: Imentet y Open Sea para abrir, Sizer en el pico, "
                       "Touch The Sky, Boxer, Olimpo y Fragma para cerrar.")
    return guardar("cumple_zorro.json", cfg)


def set_141() -> Path:
    fija = {k: buscar(*v) for k, v in {
        "jumbo": ("Jumbo", "Paul Thomas"), "haunted": ("Haunted", "Chelakhov"),
        "whiteroom": ("The Whiteroom", "Andy Moor")}.items()}
    fuera = noche_fuera(139) - set(fija.values())
    elig, mind = permitidos(GEN_HOUSE, (121, 126), fuera, 120)
    voz = [i for i in elig if re.search(r"feat\.?|ft\.|vocal|\bvox\b", POOL[i]["artist"] + " " + POOL[i]["title"], re.I)]
    perm = set(elig[:260]) | set(mind) | set(voz) | set(fija.values())
    cfg = json.loads((RAIZ / "data/set_configs/cumple_zorro_3a5.json").read_text(encoding="utf-8"))
    s = cfg["sets"][0]
    s["exclude_ids"] = sorted(i for i, t in POOL.items()
                              if (t.get("genre") or "") in GEN_HOUSE and i not in perm)
    s["prefer_ids"] = sorted(set(voz) | set(mind[:60]))
    s["prefer_bonus"] = 1.2
    s["anclas"] = [fija["jumbo"], fija["whiteroom"]]
    # The Whiteroom (E8.5) es la carta mas grande del set: sin ventana caia en el
    # tema 5 y el pico quedaba al 29%. Va junto a Jumbo, en el tramo heroico.
    s["anclas_en"] = {fija["jumbo"]: [0.70, 0.88], fija["whiteroom"]: [0.62, 0.90]}
    s["cierre_fijo"] = [fija["haunted"]]
    s["entrada_desde"] = ids_de(139)[-1]
    return guardar("cumple_zorro_3a5.json", cfg)


def set_140() -> Path:
    fav = [i for i, x in PERC.items() if x.get("favorito") and i in POOL and 117 <= POOL[i]["bpm"] <= 122]
    fuera = noche_fuera(139, 141) - set(fav)
    elig, mind = permitidos(GEN_ORG, (117, 122), fuera, 170)
    lentos = [i for i in elig if POOL[i]["bpm"] < 119.5]
    alta = [i for i in elig if E(i) >= 6.5][:30]
    perm = set(mind) | set(lentos) | set(alta) | {i for i in fav if i in elig}
    cfg = json.loads((RAIZ / "data/set_configs/cumple_zorro_warm.json").read_text(encoding="utf-8"))
    s = cfg["sets"][0]
    s["exclude_ids"] = sorted(i for i, t in POOL.items()
                              if (t.get("genre") or "") in GEN_ORG and i not in perm)
    s["prefer_ids"] = mind[:60]
    s["prefer_bonus"] = 1.2
    s["anclas"] = [i for i in fav if i in perm]
    s["salida_hacia"] = ids_de(139)[0]
    return guardar("cumple_zorro_warm.json", cfg)


if __name__ == "__main__":
    solo = "--solo-config" in sys.argv
    for nombre, hacer in (("139", set_139), ("141", set_141), ("140", set_140)):
        p = hacer()
        print(f"\n===== set {nombre}: {p.name}")
        if not solo:
            resolver(p)
