# -*- coding: utf-8 -*-
"""La variante HOUSERA de un set: mismo horario, mismo criterio, otro cuerpo.

POR QUE
-------
"Haceme una variante del set mas housera pero progresive" (el DJ, 2026-09-28).
Es hermana de la variante colorida de `armar_noche_zorro.py` y funciona igual:
no cambia el horario ni el arco, cambia QUE entra al pool y que se premia.

Housero no es un genero. Medido sobre los 1353 tracks del indice de groove, el
genero "House" tiene MENOS densidad que "Progressive House" (12.8 contra 14.1),
asi que pedir "mas housero" filtrando por genero devuelve lo contrario. Lo que
separa es el sonido, y esta en `rules/curaduria.json` -> `estilo.housero`:

    z(densidad) + z(sub) - 2 * (color_pct - 0.5)

o sea groove denso, bajo presente y poco protagonismo melodico: el eje opuesto
al del set colorido, con el mismo peso y el signo cambiado.

USO
---
    python scripts/variante_housera.py --base 139 --num 148 --dry
    python scripts/variante_housera.py --base 139 --num 148
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from plomo.rules import R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONFIGS = RAIZ / "data/set_configs"
POOL = {t["id"]: t for t in json.loads((RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
HOUSERO = R.get("estilo.housero") or {}


def indice() -> dict:
    """El mismo indice que usa el solver, para poder recortar el pool con el."""
    import select_set as S
    return S._HOUSERO


def spec_base(num: int) -> tuple[Path, dict, dict]:
    for f in sorted(CONFIGS.glob("*.json")):
        cfg = json.loads(f.read_text(encoding="utf-8"))
        for s in cfg.get("sets", []):
            if s.get("num") == num:
                return f, cfg, s
    sys.exit(f"no encontre el set {num} en data/set_configs/")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=int, required=True, help="set del que hereda horario y arco")
    ap.add_argument("--num", type=int, required=True)
    ap.add_argument("--nombre", default="")
    ap.add_argument("--top", type=int, default=260, help="cuantos temas del ranking entran al pool")
    ap.add_argument("--pico", type=float, default=0.75,
                    help="en que fraccion del set cae el pico")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    H = indice()
    f_base, cfg, base = spec_base(args.base)
    s = json.loads(json.dumps(base))          # copia, el base no se toca

    vetos = {k for k, v in json.loads(
        (RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8")).items()
        if v.get("veto")}

    generos = set(s.get("genres") or [])
    bl, bh = s.get("bpm", [119, 127])
    el, eh = s.get("e_pool", [0, 10])
    elegibles = [i for i, t in POOL.items()
                 if (t.get("genre") or "") in generos
                 and bl <= t["bpm"] <= bh
                 and el <= (t.get("energy") or 0) <= eh
                 and i not in vetos and i in H]
    ranking = sorted(elegibles, key=lambda i: H[i], reverse=True)
    perm = set(ranking[:args.top])
    # El pico vive aparte del groove: sin esto el set se queda sin cima, porque
    # los temas mas densos no son los mas altos de energia.
    # El umbral es 7.2 y no 7.6: con 7.6 entraban 40 temas altos pero casi
    # ninguno encadenaba en Camelot con el cuerpo del set, y el solver se quedaba
    # con un solo pico posible --Impending Storm, en 1A, lejos de todo-- que caia
    # a la mitad del set. Bajar el umbral es darle DONDE poner la cima.
    altos = [i for i in ranking if (POOL[i].get("energy") or 0) >= 7.2][:80]
    perm |= set(altos)

    s["num"] = args.num
    s["name"] = args.nombre or f"{args.num}. {s['name'].split('. ', 1)[1]}"
    s["grupo"] = s.get("grupo", "") + " housero"
    s["housero_peso"] = HOUSERO.get("peso", 1.5)
    s["color_peso"] = 0.0          # es el eje contrario: no se piden los dos
    s["mezcla_objetivo"] = HOUSERO.get("mezcla_objetivo", s.get("mezcla_objetivo"))
    # El pico va MAS TARDE que en el set base. Con el arco heredado (0.65) el
    # unico tema muy alto del pool housero caia a la mitad y despues el set
    # bajaba dos temas seguidos: el empuje sostenido necesita que la cima
    # llegue sobre el final, que es lo que el DJ viene pidiendo.
    arco = dict(s.get("arco") or {})
    arco["pico_en_pct"] = args.pico
    s["arco"] = arco
    s["_identidad"] = (
        "Variante HOUSERA del set " + str(args.base) + ". Mismo horario y mismo arco; "
        "cambia el cuerpo: groove denso, bajo presente y poca melodia al frente "
        "(estilo.housero). Sigue siendo progresivo -- la cuota deja Progressive House "
        "como mayoria -- pero el relleno lo elige el empuje y no el color.")
    s["exclude_ids"] = sorted(i for i in POOL if i not in perm)
    for k in ("prefer_ids", "anclas", "anclas_en", "inicio_fijo", "cierre_fijo"):
        s.pop(k, None)              # las anclas son del set base, no de la variante

    destino = CONFIGS / f"housero_{args.num}.json"
    salida = {k: v for k, v in cfg.items() if k != "sets"}
    salida["_comentario"] = (
        "Generado por scripts/variante_housera.py desde el set " + str(args.base) + ". "
        "No editar a mano: se regenera.")
    salida["sets"] = [s]
    ranking_top = [(H[i], i) for i in ranking[:12]]
    print(f"pool housero: {len(perm)} temas de {len(elegibles)} elegibles")
    print("los 12 que mas empujan:")
    for h, i in ranking_top:
        t = POOL[i]
        print(f"   {h:5.2f} E{t['energy']:.1f} {t['bpm']:.0f} {t['key']:>3s} "
              f"{t['artist'][:22]:22s} - {t['title'][:34]}")
    if args.dry:
        print("\n--dry: no se escribio el config")
        return
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {destino.relative_to(RAIZ)}")
    subprocess.run([sys.executable, str(RAIZ / "scripts/select_set.py"), str(destino)],
                   cwd=str(RAIZ))


if __name__ == "__main__":
    main()
