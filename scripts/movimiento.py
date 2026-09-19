"""Prende el LFO libre del Auto Filter en las capas melodicas.

Por que existe. `variacion por compas` medía 0.64 contra 0.85-2.50 de las
referencias, y la vuelta anterior —huecos de fin de frase en la bateria— la
subio a 0.84. Falta un centesimo, y el mecanismo que falta no es MIDI.

De `data/vocabulario/videos.json`, y es el consenso mas fuerte que encontro la
investigacion —tres videos independientes del nicho lo dicen con las mismas
palabras—:

    "LFO con RE-TRIGGER APAGADO, a una tasa que no coincida con el compas
     (media medida, o free rate), ruteado a cutoff [...]. Amount bajo."

El porque es mecanico y explica el numero exacto que medimos. Con re-trigger
prendido cada nota recibe la misma forma de modulacion desde cero, asi que el
compas 2 es bit a bit el compas 1. Apagado, el LFO corre libre contra la grilla
y cada repeticion cae en otra fase: las mismas notas, otro timbre.

Y estaba todo ahi y apagado. Las cinco pistas melodicas ya tienen un Auto
Filter, su `LFO T Mode` ya esta en "Rate" —que es Hz libre, o sea que no
re-dispara nunca, que es justo lo que pide la regla— y `LFO Amount` esta en
0.0%. El movimiento no habia que construirlo: habia que prenderlo.

Las tasas. Un compas a 123 BPM dura 1.951 s. Cada pista lleva una tasa distinta
y ninguna cae en un numero entero de compases:

    Atmosfera  0.13 Hz = 3.94 compases
    Acordes    0.19 Hz = 2.70
    Gancho     0.23 Hz = 2.23
    Anchos     0.29 Hz = 1.77
    Abiertos   0.31 Hz = 1.65

Distintas entre si a proposito. Con la misma tasa en las cinco, el oido no
escucha cinco capas moviendose: escucha UN barrido de filtro sobre la mezcla,
que es un efecto y no el movimiento interno que se busca.

Uso:
    python scripts/movimiento.py
    python scripts/movimiento.py --amount 0       # para apagarlo y comparar
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from plomo.live import Live  # noqa: E402

# (pista, nombre, Hz). El Hz se busca por biseccion sobre el valor mostrado
# porque el parametro esta normalizado 0..1 y la curva no es lineal.
CAPAS = [
    (4,  "Atmosfera", 0.13),
    (5,  "Acordes",   0.19),
    (8,  "Gancho",    0.23),
    (11, "Anchos",    0.29),
    (19, "Abiertos",  0.31),
]

AMOUNT = 12.0   # "amount bajo" en POR CIENTO: movimiento, no wobble


def _indice(nombres: list[str], clave: str) -> int | None:
    return next((i for i, n in enumerate(nombres) if n == clave), None)


def _a_valor(l: Live, t: int, d: int, i: int, objetivo: float) -> str:
    """Biseccion sobre el normalizado hasta que el DISPLAY diga el objetivo.

    Hace falta porque los dos parametros que toca este script estan
    normalizados 0..1 y ninguno es lineal. Poner `LFO Amount` en 0.12 crudo da
    1.4% mostrado, no 12%: un factor 8.5. Al Hz le pasa lo mismo con otra
    curva. Se busca contra lo que el device dice, que es el unico numero que
    significa algo.
    """
    lo, hi = 0.0, 1.0
    for _ in range(18):
        med = (lo + hi) / 2
        l.set_parametro(t, d, i, med)
        time.sleep(0.04)
        txt = l.valor_mostrado(t, d, i)
        try:
            v = float(txt.split()[0])
        except (ValueError, IndexError):
            return txt
        if v < objetivo:
            lo = med
        else:
            hi = med
    return l.valor_mostrado(t, d, i)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--amount", type=float, default=AMOUNT,
                    help="en por ciento, como lo muestra el device")
    args = ap.parse_args()

    with Live(timeout=30.0) as l:
        print(f"\n  LFO libre al {args.amount:.0f}% · una tasa distinta por capa")
        for t, nombre, hz in CAPAS:
            ds = l.dispositivos(t)
            if "Auto Filter" not in ds:
                print(f"  ->{nombre:<11} sin Auto Filter, se saltea")
                continue
            d = ds.index("Auto Filter")
            ns = l.parametros(t, d)
            i_modo = _indice(ns, "LFO T Mode")
            i_hz = _indice(ns, "LFO Freq")
            i_amt = _indice(ns, "LFO Amount")
            if None in (i_modo, i_hz, i_amt):
                print(f"  ->{nombre:<11} le faltan parametros del LFO")
                continue
            # "Rate" es el modo de Hz libre: no se sincroniza al tempo y por lo
            # tanto no re-dispara. Es el valor 0 del enum.
            l.set_parametro(t, d, i_modo, 0.0)
            time.sleep(0.05)
            dice = _a_valor(l, t, d, i_hz, hz)
            amt = _a_valor(l, t, d, i_amt, args.amount)
            compases = (1.0 / hz) / (4 * 60.0 / 123.0)
            print(f"    {nombre:<11} {dice:>10}  = {compases:.2f} compases  "
                  f"amount {amt}")
        print("\n  ahora: python scripts/render.py v4 --desde 159 --compases 16")


if __name__ == "__main__":
    main()
