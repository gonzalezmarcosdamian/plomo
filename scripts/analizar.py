"""Analiza un tema o un grupo de temas y devuelve sus IDEAS, no sus estadisticas.

Por que existe: las herramientas anteriores devuelven medianas —densidad, color,
continuidad— y componer desde medianas ya se probo y no funciona. El promedio de
muchos temas buenos no es un tema bueno.

Esto contesta otras preguntas, que son las que un musico usa:

  - En que grados esta la progresion, relativa a la tonica. "Am - Dm" no sirve
    para escribir en F#m; "i - iv" si.
  - Cual es la celula ritmica del bajo, y **cuales de sus semicorcheas son ancla**
    —estan en todos los compases— y cuales varian. Esa distincion es la
    diferencia entre una frase y un compas repetido, y no la daba ninguna
    herramienta.
  - Donde cae el bajo respecto del bombo. Encima es una marcha; en el hueco
    empuja.
  - Cuanto sostiene cada capa y cuanto ataca.

Y cuando se le pasan varios temas NO promedia: reporta que se repite y que varia.
Lo que aparece en todos es la regla del grupo; lo disperso es decision de cada
tema y no hay que copiarlo.

Uso:
    python scripts/analizar.py "<mp3>"
    python scripts/analizar.py --sello "Lost & Found" --cuantos 6
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from color_melodico import _color  # noqa: E402
from continuidad import continuidad_audio  # noqa: E402
from copiar_tema import (BANDAS, MARGEN_S, NOMBRES, SR, TRIADAS,  # noqa: E402
                         _afinar_bpm, _bajo, _cuantizar, _envolvente, _golpes,
                         _grilla)
from medir_arreglos import _mejor_momento  # noqa: E402
from plomo import config  # noqa: E402
from plomo.midi import MENOR, TICKS_POR_NEGRA  # noqa: E402
from separar import separar  # noqa: E402

COMPASES = 8
# Grados en semitonos sobre la tonica, con su nombre romano en modo menor.
ROMANOS = {0: "i", 2: "II", 3: "III", 5: "iv", 7: "v", 8: "VI", 10: "VII",
           1: "bII", 4: "iii", 6: "bV", 9: "VI#", 11: "vii"}


def _tonica(elegidos: list[str]) -> int | None:
    """La tonica es la raiz mas repetida entre los acordes del fragmento.

    No se usa la tonalidad del nombre del archivo: se quiere lo que suena en
    ESTE tramo, que puede estar en el relativo o en un grado prestado.
    """
    reales = [a for a in elegidos if a != "-"]
    if not reales:
        return None
    raiz = Counter(a.rstrip("m") for a in reales).most_common(1)[0][0]
    return NOMBRES.index(raiz)


def _en_grados(elegidos: list[str], tonica: int) -> list[str]:
    fuera = []
    for a in elegidos:
        if a == "-":
            fuera.append("-")
            continue
        pc = NOMBRES.index(a.rstrip("m"))
        fuera.append(ROMANOS.get((pc - tonica) % 12, "?"))
    return fuera


def _celula(pista, compases: int) -> tuple[list[list[int]], list[int], list[int]]:
    """Devuelve (compas por compas, anclas, variables) en semicorcheas."""
    por_compas: list[list[int]] = [[] for _ in range(compases)]
    for e in pista._eventos:
        if e.datos[0] & 0xF0 != 0x90 or e.datos[2] == 0:
            continue
        semi = int(round(e.tick / (TICKS_POR_NEGRA / 4)))
        c = semi // 16
        if 0 <= c < compases:
            por_compas[c].append(semi % 16)
    por_compas = [sorted(set(x)) for x in por_compas]
    con_notas = [x for x in por_compas if x]
    if not con_notas:
        return por_compas, [], []
    cuenta = Counter(k for fila in con_notas for k in fila)
    anclas = sorted(k for k, v in cuenta.items() if v >= len(con_notas) * 0.8)
    variables = sorted(k for k, v in cuenta.items() if v < len(con_notas) * 0.8)
    return por_compas, anclas, variables


def _contra_el_bombo(bajo, drums, sr, grilla, semis) -> float:
    """Fraccion de notas de bajo que caen encima de un bombo."""
    kicks = _cuantizar(_golpes(_envolvente(drums, sr, *BANDAS["kick"][:2]), sr), grilla)
    kicks = {k for k in kicks if 0 <= k < semis}
    notas = {int(round(e.tick / (TICKS_POR_NEGRA / 4)))
             for e in bajo._eventos if e.datos[0] & 0xF0 == 0x90}
    if not notas:
        return 0.0
    return len(notas & kicks) / len(notas)


def analizar(archivo: Path, desde: float | None = None) -> dict | None:
    from copiar_tema import _armonia
    desde = _mejor_momento(archivo) if desde is None else desde
    dur = COMPASES * 4 * 60.0 / 121.0 + 4.0
    rutas = separar(archivo, desde, dur)
    recorte = min(desde, MARGEN_S)
    st = {n: librosa.load(p, sr=SR, offset=recorte, duration=dur)[0]
          for n, p in rutas.items()}

    crudo = float(np.atleast_1d(librosa.beat.beat_track(y=st["drums"], sr=SR)[0])[0])
    while crudo < 100:
        crudo *= 2
    while crudo > 145:
        crudo /= 2
    bpm = _afinar_bpm(st["drums"], SR, crudo)
    grilla = _grilla(st["drums"], SR, bpm)
    semis = COMPASES * 16

    kicks = _golpes(_envolvente(st["drums"], SR, *BANDAS["kick"][:2]), SR)
    enganche = float((np.abs(kicks[:, None] - grilla[None, :]).min(axis=1) < 0.020).mean())
    n_kick = len({k for k in _cuantizar(kicks, grilla) if 0 <= k < semis}) / COMPASES
    if enganche < 0.70 or not 3.0 <= n_kick <= 4.6:
        return {"archivo": archivo.stem, "descartado":
                f"bombo {n_kick:.1f}/compas, enganche {enganche:.0%}"}

    acordes, elegidos = _armonia(st["other"], SR, grilla, semis, bpm)
    tonica = _tonica(elegidos)
    grados = _en_grados(elegidos, tonica) if tonica is not None else []

    bajo = _bajo(st["bass"], SR, grilla, semis, bpm)
    por_compas, anclas, variables = _celula(bajo, COMPASES)
    col = _color(rutas["other"])

    return {
        "archivo": archivo.stem, "bpm": round(bpm, 1), "desde_s": round(desde),
        "tonica": NOMBRES[tonica] if tonica is not None else "?",
        "grados": grados,
        "progresion": " ".join(dict.fromkeys(g for g in grados if g != "-")),
        "bajo_compases": por_compas,
        "bajo_anclas": anclas, "bajo_variables": variables,
        "bajo_notas_x_compas": round(sum(len(x) for x in por_compas) / COMPASES, 2),
        "bajo_sobre_bombo": round(_contra_el_bombo(bajo, st["drums"], SR, grilla, semis), 2),
        "centroide": round(col["centroide"]), "rolloff85": round(col["rolloff85"]),
        "planitud": round(col["planitud"], 4),
        "cont_armonia": round(continuidad_audio(rutas["other"]) or 0, 2),
        "cont_bajo": round(continuidad_audio(rutas["bass"]) or 0, 2),
    }


def _mostrar(d: dict) -> None:
    if "descartado" in d:
        print(f"  {d['archivo'][:52]:52}  DESCARTADO: {d['descartado']}")
        return
    print(f"\n  {d['archivo'][:66]}")
    print(f"    {d['bpm']:.0f} BPM · tonica {d['tonica']} · desde {d['desde_s']}s")
    print(f"    progresion:  {d['progresion']}   ({' '.join(d['grados'])})")
    print(f"    bajo:  {d['bajo_notas_x_compas']}/compas · "
          f"{d['bajo_sobre_bombo']:.0%} encima del bombo · "
          f"anclas en {d['bajo_anclas']}")
    for i, fila in enumerate(d["bajo_compases"][:4]):
        print(f"      c{i+1}  " + "".join(
            ("A" if k in d["bajo_anclas"] else "x") if k in fila else "." for k in range(16)))
    print(f"    color: centroide {d['centroide']}Hz · rolloff {d['rolloff85']}Hz · "
          f"planitud {d['planitud']}")
    print(f"    sostiene: armonia {d['cont_armonia']:.0%} · bajo {d['cont_bajo']:.0%}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", nargs="?", type=Path)
    ap.add_argument("--sello", help="analiza los temas de un sello")
    ap.add_argument("--cuantos", type=int, default=6)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    archivos: list[Path] = []
    if args.archivo:
        archivos = [args.archivo]
    elif args.sello:
        dep = config.MUSIC_LIBRARY_ROOT / "Biblioteca"
        clave = args.sello.lower().replace(" ", "").replace("&", "")
        for p in sorted(dep.rglob("*.mp3")):
            if clave in p.stem.lower().replace(" ", "").replace("&", ""):
                archivos.append(p)
        print(f"  {len(archivos)} temas del sello, analizo {args.cuantos}")
        archivos = archivos[:args.cuantos]
    else:
        sys.exit("  pasá un archivo o --sello")

    filas = [d for d in (analizar(f) for f in archivos) if d]
    for d in filas:
        _mostrar(d)

    buenos = [d for d in filas if "descartado" not in d]
    if len(buenos) < 2:
        return

    # NO se promedia: se reporta que se repite y que varia. Lo que aparece en
    # todos es la regla del grupo; lo disperso es decision de cada tema.
    print(f"\n  === {len(buenos)} temas: que se repite ===")
    prog = Counter(d["progresion"] for d in buenos)
    for p, n in prog.most_common(4):
        print(f"    progresion {p:22} en {n} de {len(buenos)}")
    grados = Counter(g for d in buenos for g in d["grados"] if g != "-")
    print(f"    grados usados: " + " ".join(f"{g}×{n}" for g, n in grados.most_common()))
    anclas = Counter(k for d in buenos for k in d["bajo_anclas"])
    comunes = [k for k, n in anclas.items() if n >= len(buenos) * 0.6]
    print(f"    semicorcheas ancla del bajo en la mayoria: {sorted(comunes)}")

    print(f"\n  === que varia (min - mediana - max) ===")
    for k, etq in (("bpm", "BPM"), ("bajo_notas_x_compas", "bajo/compas"),
                   ("bajo_sobre_bombo", "bajo sobre bombo"), ("centroide", "centroide"),
                   ("rolloff85", "rolloff85"), ("cont_bajo", "sostiene el bajo")):
        v = [d[k] for d in buenos]
        print(f"    {etq:18} {min(v):8.2f} - {statistics.median(v):8.2f} - {max(v):8.2f}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(filas, indent=2, ensure_ascii=False),
                             encoding="utf-8")
        print(f"\n  {args.json}")


if __name__ == "__main__":
    main()
