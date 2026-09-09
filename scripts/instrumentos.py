"""Desarma un tema instrumento por instrumento: patron, feel y dinamica.

Por que existe: `analizar.py` devuelve las ideas del tema —progresion, celula
del bajo, color— pero trata a la bateria como un bloque. Y la diferencia entre
dos temas del mismo genero casi nunca esta en que notas tocan: esta en COMO las
tocan.

Tres cosas por instrumento, y la segunda es la que no se habia medido nunca:

**El patron.** En que semicorcheas cae, cuales son ancla —estan en todos los
compases— y cuales varian. Es lo mismo que ya se hacia con el bajo, aplicado a
cada pieza de la bateria por separado.

**El feel.** Cuantos milisegundos adelante o atras del pulso vive cada capa.
`src/plomo/humano.py` afirma que el clap va +10 ms atras y el bajo -4 ms
adelante, y esos numeros los invento alguien mirando el techo. Aca se miden, y
el resultado se puede pegar directo como un `Perfil`.

**La dinamica.** Cuanto varia el golpe entre repeticiones. Una capa con todos
los golpes iguales suena programada por mas que este bien colocada.

Un aviso sobre el feel, porque decide como se lee todo lo demas: el detector de
ataques tiene su propia latencia, asi que los milisegundos ABSOLUTOS no
significan nada. Lo que si significa es la diferencia ENTRE capas, porque todas
se miden con el mismo detector contra la misma grilla. La grilla sale del bombo,
asi que el bombo da cero por construccion — y esta bien, porque el bombo es el
reloj contra el que se mide todo lo demas.

Uso:
    python scripts/instrumentos.py "<mp3>"
    python scripts/instrumentos.py "<mp3>" --desde 180 --perfil
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from copiar_tema import (MARGEN_S, SR, _afinar_bpm, _banda,  # noqa: E402
                         _envolvente, _golpes, _grilla)
from medir_arreglos import _mejor_momento  # noqa: E402
from separar import separar  # noqa: E402

COMPASES = 8

# Cada pieza con su banda y el stem donde vive. Son anchas a proposito: no se
# busca aislar el instrumento sino saber cuando pega algo en ese registro.
PIEZAS: dict[str, tuple[str, float, float]] = {
    "bombo":     ("drums", 30, 120),
    "clap":      ("drums", 200, 1400),
    "hat":       ("drums", 6000, 11000),
    "percusion": ("drums", 1400, 4000),
    "bajo":      ("bass", 35, 260),
    "melodia":   ("other", 300, 4000),
}

# Piezas cuyo FEEL medido es confiable.
#
# El detector marca el ataque donde la envolvente crece, no donde empieza la
# nota. En una pieza percusiva el transiente es instantaneo y las dos cosas
# coinciden; en un bajo o un pad el ataque tarda 10 a 30 ms en subir, asi que el
# desvio medido mezcla el FEEL con el TIEMPO DE ATAQUE del sonido y no se pueden
# separar.
#
# Moonflare da +9.7 ms para el bajo y +15.9 para la melodia. Puede ser que
# toquen atras, puede ser que su bajo tenga ataque lento, y esta medicion no
# distingue. Entre piezas percusivas si: todas comparten detector y transiente.
FEEL_CONFIABLE = {"bombo", "clap", "hat", "percusion"}


def _ataques(y: np.ndarray, lo: float, hi: float) -> tuple[np.ndarray, np.ndarray]:
    """Tiempos de ataque en esa banda, y la altura del pico de cada uno."""
    env = _envolvente(y, SR, lo, hi)
    tiempos = _golpes(env, SR)
    if not len(tiempos):
        return tiempos, np.array([])
    veces = librosa.times_like(env, sr=SR, hop_length=256)
    picos = np.array([env[np.argmin(np.abs(veces - t))] for t in tiempos])
    return tiempos, picos


def _feel(tiempos: np.ndarray, grilla: np.ndarray, bpm: float) -> tuple[float, float]:
    """Desvio mediano contra la grilla y su dispersion, en milisegundos.

    Positivo = atras del pulso. Se descartan los ataques a mas de media
    semicorchea: a esa distancia ya no se sabe contra que golpe medir, y meterlos
    ensucia la mediana con ruido del detector.
    """
    if not len(tiempos):
        return 0.0, 0.0
    limite = (60.0 / bpm / 4) / 2
    desvios = []
    for t in tiempos:
        d = t - grilla[np.argmin(np.abs(grilla - t))]
        if abs(d) < limite:
            desvios.append(d * 1000.0)
    if not desvios:
        return 0.0, 0.0
    return float(np.median(desvios)), float(np.std(desvios))


def _patron(tiempos: np.ndarray, grilla: np.ndarray,
            compases: int) -> tuple[list[int], list[int], float]:
    """Anclas, variables, y golpes por compas."""
    posiciones: list[int] = []
    for t in tiempos:
        k = int(np.argmin(np.abs(grilla - t)))
        if k < compases * 16:
            posiciones.append(k)
    if not posiciones:
        return [], [], 0.0
    por_compas: dict[int, set[int]] = {}
    for k in posiciones:
        por_compas.setdefault(k // 16, set()).add(k % 16)
    con_notas = [v for v in por_compas.values() if v]
    cuenta = Counter(p for fila in con_notas for p in fila)
    anclas = sorted(p for p, n in cuenta.items() if n >= len(con_notas) * 0.8)
    variables = sorted(p for p, n in cuenta.items() if n < len(con_notas) * 0.8)
    return anclas, variables, len(posiciones) / compases


def _dinamica(picos: np.ndarray) -> float:
    """Cuanto varia el golpe, de 0 a 1. Todos iguales da 0."""
    if len(picos) < 3 or picos.max() <= 0:
        return 0.0
    return float(np.std(picos) / picos.max())


def _dibujo(anclas: list[int], variables: list[int], por_compas: dict) -> str:
    linea = []
    for k in range(16):
        if k in anclas:
            linea.append("A")
        elif k in variables:
            linea.append("x")
        else:
            linea.append(".")
    return "".join(linea)


def analizar(archivo: Path, desde: float | None = None) -> dict:
    desde = _mejor_momento(archivo) if desde is None else desde
    dur = COMPASES * 4 * 60.0 / 121.0 + 4.0
    rutas = separar(archivo, desde, dur)
    recorte = min(desde, MARGEN_S)
    stems = {n: librosa.load(p, sr=SR, offset=recorte, duration=dur)[0]
             for n, p in rutas.items()}

    crudo = float(np.atleast_1d(librosa.beat.beat_track(y=stems["drums"], sr=SR)[0])[0])
    while crudo < 100:
        crudo *= 2
    while crudo > 145:
        crudo /= 2
    bpm = _afinar_bpm(stems["drums"], SR, crudo)
    grilla = _grilla(stems["drums"], SR, bpm)

    fuera = {"archivo": archivo.stem, "bpm": bpm, "desde": desde, "piezas": {}}
    for pieza, (stem, lo, hi) in PIEZAS.items():
        if stem not in stems:
            continue
        tiempos, picos = _ataques(stems[stem], lo, hi)
        anclas, variables, por_compas = _patron(tiempos, grilla, COMPASES)
        desvio, disp = _feel(tiempos, grilla, bpm)
        fuera["piezas"][pieza] = {
            "por_compas": por_compas, "anclas": anclas, "variables": variables,
            "desvio_ms": desvio, "dispersion_ms": disp,
            "dinamica": _dinamica(picos), "n": len(tiempos),
        }
    return fuera


def _mostrar(d: dict) -> None:
    print(f"\n  {d['archivo'][:66]}")
    print(f"  {d['bpm']:.1f} BPM · fragmento desde {d['desde']:.0f}s\n")
    print(f"  {'pieza':<11} {'x compas':>9} {'feel':>9} {'disp':>7} {'dinamica':>9}"
          f"   patron (A = ancla, x = varia)")
    base = d["piezas"].get("bombo", {}).get("desvio_ms", 0.0)
    for pieza, v in d["piezas"].items():
        if not v["n"]:
            continue
        # el feel es RELATIVO al bombo: los milisegundos absolutos son latencia
        # del detector y no significan nada
        rel = v["desvio_ms"] - base
        dib = _dibujo(v["anclas"], v["variables"], {})
        marca = " " if pieza in FEEL_CONFIABLE else "?"
        print(f"  {pieza:<11} {v['por_compas']:9.2f} {rel:+7.1f}ms{marca} "
              f"{v['dispersion_ms']:6.1f}ms {v['dinamica']:9.2f}   {dib}")
    print("\n  feel: positivo = atras del pulso. El bombo es la referencia y da 0")
    print("  por construccion, porque la grilla sale de el.")
    print()
    print("  El '?' marca donde el feel NO es confiable: el detector marca donde")
    print("  la envolvente crece, y en un bajo o un pad eso tarda 10 a 30 ms.")


def _perfil(d: dict) -> None:
    """Escupe los perfiles listos para pegar en src/plomo/humano.py."""
    equivalencias = {"bombo": "kick", "clap": "clap", "hat": "hat",
                     "percusion": "percusion", "bajo": "bajo", "melodia": "gancho"}
    base = d["piezas"].get("bombo", {}).get("desvio_ms", 0.0)
    print(f"\n  # medido sobre {d['archivo'][:50]}")
    print(f"  PERFILES = {{")
    for pieza, v in d["piezas"].items():
        if not v["n"] or pieza not in equivalencias:
            continue
        if pieza not in FEEL_CONFIABLE:
            print(f'      # "{equivalencias[pieza]}": sin dato. El feel de esta pieza')
            print("      #   mezcla el toque con el tiempo de ataque del sonido")
            print("      #   y esta medicion no los separa.")
            continue
        rel = (v["desvio_ms"] - base) / 1000.0 * (d["bpm"] / 60.0)
        disp = v["dispersion_ms"] / 1000.0 * (d["bpm"] / 60.0)
        din = int(round(v["dinamica"] * 40))
        print(f'      "{equivalencias[pieza]}": Perfil({rel / (1/488):.1f} * MS, '
              f'{disp / (1/488):.1f} * MS, dinamica={din}),')
    print("  }")
    print("\n  Ojo: la dispersion medida incluye el error del detector, asi que es")
    print("  un TECHO. Copiarla entera hace sonar mas sucio que la referencia.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", type=Path)
    ap.add_argument("--desde", type=float)
    ap.add_argument("--perfil", action="store_true",
                    help="imprime los perfiles de humanizacion listos para pegar")
    args = ap.parse_args()

    if not args.archivo.exists():
        sys.exit(f"no existe {args.archivo}")
    d = analizar(args.archivo, args.desde)
    _mostrar(d)
    if args.perfil:
        _perfil(d)
    print()


if __name__ == "__main__":
    main()
