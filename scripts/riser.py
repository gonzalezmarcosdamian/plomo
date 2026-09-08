"""Genera el riser: el ruido que sube y anuncia que algo va a cambiar.

Por que existe: la tension de un tema no la da la armonia sino los avisos. Cada
vez que algo esta por cambiar, dos compases antes empieza a subir algo — y el
oido lo lee como "se viene". Sin eso, ocho compases y otros ocho suenan a dos
bloques pegados en vez de a un tema que va a algun lado.

Se sintetiza y no se baja de un pack a proposito: son cuatro lineas de ruido
filtrado, el pack tendria licencia y ademas el largo tiene que dar exacto con el
tempo del tema. Un riser que dura 3.8 segundos en un tema de 123 BPM entra tarde.

Uso:
    python scripts/riser.py --bpm 123 --compases 2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.midi import MAYOR, MENOR, tonica_de_camelot  # noqa: E402

SR = 44100
USER_LIBRARY = Path("C:/Users/gonza/OneDrive/Documentos/Ableton/User Library/Samples/plomo")


def riser(segundos: float, desde_hz: float = 300.0, hasta_hz: float = 9000.0,
          tono: float = 0.18, pico: float = 0.85) -> np.ndarray:
    """Ruido con un pasabanda que sube, mas una sinusoide que lo acompania."""
    n = int(segundos * SR)
    t = np.arange(n) / SR
    avance = (t / segundos) ** 1.7        # curva: casi todo el movimiento al final

    # el filtro se mueve por bloques: un pasabanda variable de verdad es caro y
    # a 64 bloques el barrido ya no se escucha escalonado
    ruido = np.random.default_rng(7).standard_normal(n) * 0.35
    salida = np.zeros(n)
    bloques = 64
    paso = n // bloques
    for b in range(bloques):
        a, z = b * paso, min((b + 1) * paso + 256, n)
        centro = desde_hz + (hasta_hz - desde_hz) * avance[min(a, n - 1)]
        lo = max(40.0, centro * 0.6) / (SR / 2)
        hi = min(centro * 1.6, SR / 2 - 100) / (SR / 2)
        sos = butter(2, [lo, hi], btype="band", output="sos")
        salida[a:z] += sosfilt(sos, ruido[a:z])

    # Una sinusoide que sube: le da altura al ruido, que solo suena a viento.
    # Es la parte que mas rapido se vuelve obvia — con `tono` bajo el riser
    # empuja sin anunciarse, que es lo que se quiere cuando aparece siete veces
    # en dos minutos. Fuerte esta bien una vez; siete veces cansa.
    freq = 220.0 * 2 ** (avance * 1.5)
    salida += tono * np.sin(2 * np.pi * np.cumsum(freq) / SR)

    salida *= avance ** 0.8                       # entra de la nada
    salida[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))   # corte limpio
    return salida / (np.abs(salida).max() or 1.0) * pico


def swell(segundos: float, tonica: int, escala: list[int]) -> np.ndarray:
    """Acorde reversado: crece de la nada y corta en seco al llegar al golpe.

    Otro mecanismo, no otra version del mismo. El riser de ruido anuncia con
    aire y brillo; esto anuncia con armonia — es el mismo acorde del tema
    llegando al compas siguiente. Al ser tonal se funde con lo que suena en vez
    de superponerse, que es la razon por la que un barrido de ruido se escucha
    como un efecto pegado encima.

    Se sintetiza decayendo y despues se da vuelta el buffer entero. Ese es el
    truco: la cola de un decaimiento natural, leida al reves, da un crecimiento
    que ningun envelope dibujado a mano imita bien.
    """
    n = int(segundos * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(11)

    # triada menor mas la octava, en dos registros
    grados = [0, 3, 7, 12, 19]
    y = np.zeros(n)
    for i, g in enumerate(grados):
        f = 110.0 * 2 ** ((tonica + g) / 12.0)
        for armonico, peso in ((1, 1.0), (2, 0.35), (3, 0.16)):
            desafine = 1.0 + rng.uniform(-0.0016, 0.0016)
            y += peso / (i + 1.6) * np.sin(2 * np.pi * f * armonico * desafine * t)

    # decaimiento natural; al reversar queda el crecimiento
    y *= np.exp(-t * 2.6)
    # un hilo de aire que acompania, muy abajo
    y += 0.06 * rng.standard_normal(n) * np.exp(-t * 3.2)
    y = y[::-1].copy()

    y[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    y[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))   # corte seco
    return y / (np.abs(y).max() or 1.0) * 0.62


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bpm", type=float, default=123.0)
    ap.add_argument("--compases", type=float, default=2.0)
    ap.add_argument("--tipo", choices=("aire", "acorde"), default="aire",
                    help="aire = ruido que sube; acorde = swell tonal reversado")
    ap.add_argument("--camelot", default="11A", help="tonalidad del swell")
    ap.add_argument("--tono", type=float, default=0.18,
                    help="cuanta sinusoide encima del ruido; 0 = solo aire")
    ap.add_argument("--hasta", type=float, default=9000.0,
                    help="hasta donde sube el filtro, en Hz")
    ap.add_argument("--pico", type=float, default=0.85,
                    help="nivel maximo del sample")
    ap.add_argument("--salida", type=Path,
                    default=Path("postproduction/audio/riser.wav"))
    args = ap.parse_args()

    segundos = args.compases * 4 * 60.0 / args.bpm
    if args.tipo == "acorde":
        tonica, menor = tonica_de_camelot(args.camelot)
        y = swell(segundos, tonica, MENOR if menor else MAYOR)
    else:
        y = riser(segundos, hasta_hz=args.hasta, tono=args.tono, pico=args.pico)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    sf.write(args.salida, y, SR)
    if USER_LIBRARY.exists():
        # Se copia con el nombre del archivo de salida, no con uno fijo: si Live
        # tiene el sample cargado en un Simpler lo tiene abierto, y sobrescribirlo
        # falla con un error de sistema que no dice eso. Con nombre nuevo entra
        # siempre, y la version vieja queda por si habia que volver.
        destino = USER_LIBRARY / args.salida.name
        try:
            sf.write(destino, y, SR)
            print(f"  en la User Library: {destino.name}")
        except Exception as e:
            print(f"  no se pudo copiar a la User Library ({e.__class__.__name__}): "
                  f"probablemente Live tiene abierto {destino.name}")
    print(f"  {args.compases:.0f} compases a {args.bpm:.0f} BPM = {segundos:.2f}s")
    print(f"  {args.salida}")


if __name__ == "__main__":
    main()
