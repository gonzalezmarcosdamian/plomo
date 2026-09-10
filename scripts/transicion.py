"""Como cruza un tema de un drop a una bajada: la forma del corte, en compases.

Por que existe. El DJ escucho la entrada a la bajada y dijo "es re brusco, es
silencio y viene de una conga linda". Medido en MIDI era 1933 -> 154 de impacto
en un compas, de doce capas a cuatro. La pregunta correcta no es cuanto bajar
la caida sino como la hacen los temas que a el le gustan: cuantos compases
tarda, que se va primero, que se queda.

Se toma cada frontera DROP -> BAJADA que encuentra `estructura.py` y se imprime,
compas por compas alrededor de ella, el nivel total y tres bandas: graves (el
bombo y el bajo), medios (percusion y armonia) y agudos (hats y aire). Con eso
se lee que capa se cae en que compas. Sin Demucs: es nivel por banda sobre la
mezcla, alcanza para la forma y corre en segundos.

Uso:
    python scripts/transicion.py "<mp3>"
    python scripts/transicion.py --tocados 4
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from copiar_tema import _banda  # noqa: E402
from estructura import SR, medir  # noqa: E402

BANDAS = {"graves": (30, 200), "medios": (200, 3000), "agudos": (3000, 11000)}
ANTES, DESPUES = 4, 8


def _db(y: np.ndarray) -> float:
    return float(20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-9))


def fronteras(d: dict) -> list[int]:
    """Compases (0-based) donde un DROP termina y empieza una BAJADA."""
    bl = [b for b in d["bloques"] if b[1] - b[0] >= 4]
    fuera = []
    for (a0, a1, ea), (b0, b1, eb) in zip(bl, bl[1:]):
        if ea == "DROP" and eb == "BAJADA" and a1 == b0:
            fuera.append(b0)
    return fuera


def transicion(archivo: Path) -> None:
    d = medir(archivo)
    y, _ = librosa.load(archivo, sr=SR)
    x_compas = int(round(SR * 4 * 60.0 / d["bpm"]))
    bandas = {n: _banda(y, SR, lo, hi) for n, (lo, hi) in BANDAS.items()}
    print(f"\n  {archivo.stem[:66]}")
    fr = fronteras(d)
    if not fr:
        print("  sin frontera DROP -> BAJADA clara")
        return
    for f in fr[:2]:
        print(f"  frontera en el compas {f + 1}   (nivel en dBFS; 0 = el compas de la caida)")
        print(f"   {'compas':>7} {'total':>7} {'graves':>7} {'medios':>7} {'agudos':>7}")
        for c in range(f - ANTES, f + DESPUES):
            if c < 0 or (c + 1) * x_compas > len(y):
                continue
            seg = slice(c * x_compas, (c + 1) * x_compas)
            fila = [_db(y[seg])] + [_db(bandas[n][seg]) for n in BANDAS]
            marca = "<-" if c == f else "  "
            print(f"   {c + 1:>5}{marca} " + " ".join(f"{v:7.1f}" for v in fila))
        # la caida, resumida: cuanto baja cada banda del compas anterior al de
        # la frontera, y cuantos compases tarda en bajar 6 dB desde el drop
        ant = slice((f - 1) * x_compas, f * x_compas)
        for n in BANDAS:
            ref = _db(bandas[n][ant])
            tarda = next((k for k in range(0, DESPUES)
                          if _db(bandas[n][(f + k) * x_compas:(f + k + 1) * x_compas]) < ref - 6), None)
            print(f"   {n:<7} cae {ref - _db(bandas[n][f * x_compas:(f + 1) * x_compas]):5.1f} dB en el primer compas · "
                  f"-6 dB {'nunca' if tarda is None else 'en el compas ' + str(tarda)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", type=Path, nargs="?")
    ap.add_argument("--tocados", type=int)
    args = ap.parse_args()
    objetivos: list[Path] = []
    if args.archivo:
        objetivos = [args.archivo]
    elif args.tocados:
        from medir_arreglos import DEPOSITO, _buscar, _partir
        from plomo.matching import clave
        mas = json.loads((RAIZ / "data" / "mi_sonido.json").read_text(encoding="utf-8"))
        indice = {clave(*_partir(p.stem)): p for p in DEPOSITO.rglob("*.mp3")}
        for t in mas["mas_sonados"]:
            if len(objetivos) >= args.tocados:
                break
            f = _buscar(t["artist"], t["title"], indice)
            if f:
                objetivos.append(f)
    else:
        sys.exit("dame un archivo o --tocados N")
    for f in objetivos:
        try:
            transicion(f)
        except Exception as e:  # noqa: BLE001
            print(f"  - {f.stem[:50]}: {e}")


if __name__ == "__main__":
    main()
