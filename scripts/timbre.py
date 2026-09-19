"""Mide el SONIDO de cada bus, no el arreglo. La dimension que faltaba.

Por que existe. `iterar.py` compara veinte dimensiones y todas contestan la
misma clase de pregunta: cuantas veces pasa algo y cuan fuerte suena. Ninguna
contesta QUE ES el sonido. Y el juicio del DJ —"parece un ringtone", "horrible
aunque mejores efectos"— es exactamente sobre eso. Por eso se podian mover las
veinte sin mover el juicio.

La medicion que lo separa es la CRESTA ESPECTRAL: pico sobre media del espectro
promedio, en dB. Alta significa tres parciales limpios y nada en el medio; baja
significa un espectro lleno. Medido sobre el bus de bateria en cuatro
referencias del genero da 17.4, 17.7, 17.7 y 18.8 dB — un span de 1.4 dB, el
invariante mas apretado que encontro el proyecto. El boceto daba 26-27.

Y la OCUPACION: que fraccion de la banda esta a menos de 40 dB del pico. En el
bus melodico las referencias dan 44 a 100%; el boceto daba 4 a 18%. O sea que
el 96% de su banda estaba practicamente vacia. Eso es "ringtone de 2009"
escrito en numeros, y no se arregla con ningun efecto: es la fuente.

Dos avisos que costaron encontrarse:

**La flatness NO sirve para comparar entre caminos distintos.** Sobre el mismo
material da 0.0028 via Demucs y 0.0199 sobre el render directo — un factor 7.
La cresta espectral si es robusta: 27.0 contra 25.8 por los dos caminos.

**El instrumento discrimina.** El bus de BAJO propio mide igual que el de
Tunnel (ancho de banda 709 contra 716 Hz, centroide 279 contra 254). No esta
marcando "propio = distinto" por default: el bajo esta bien y lo melodico no.

Uso:
    python scripts/timbre.py postproduction/render/v3_159-174.wav
    python scripts/timbre.py "<referencia.mp3>" --desde 388 --separar
    python scripts/timbre.py --comparar propio.wav "<ref.mp3>" --desde 388
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

SR = 22050

# La banda donde vive el cuerpo de cada bus. No arranca en cero a proposito: el
# sub de un bajo y el golpe de un bombo dominan el espectro y taparian la
# pregunta, que es si ENTRE medio hay algo.
BUSES = {
    "bateria":  ("drums", 150, 11000),
    "bajo":     ("bass",   40, 1200),
    "melodico": ("other", 150, 8000),
}

# Objetivos medidos en Alex O'Rion "Tunnel", Jeremy Olander "Panorama",
# Khen "Closing Doors" e Interlocutor (Kebin Van Reeken).
OBJETIVO = {
    "bateria":  {"cresta": (17.4, 18.8), "ocupacion": (1.00, 1.00), "centroide": (3518, 4414)},
    "melodico": {"cresta": (18.5, 28.7), "ocupacion": (0.44, 1.00), "centroide": (1210, 1992)},
    "bajo":     {"cresta": (15.0, 19.0), "ocupacion": (0.50, 1.00), "centroide": (200, 400)},
}


def _espectro(y: np.ndarray, lo: float, hi: float) -> tuple[np.ndarray, np.ndarray]:
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=1024))
    f = librosa.fft_frequencies(sr=SR, n_fft=4096)
    m = (f >= lo) & (f < hi)
    return f[m], S[m].mean(axis=1)


def medir(y: np.ndarray, lo: float, hi: float, piso_db: float = -40.0) -> dict:
    f, e = _espectro(y, lo, hi)
    if not e.size or e.max() <= 0:
        return {}
    pico = e.max()
    cresta = 20 * np.log10(pico / max(e.mean(), 1e-12))
    ocupacion = float((20 * np.log10(e / pico + 1e-12) > piso_db).mean())
    centroide = float((f * e).sum() / e.sum())
    # ancho de banda: desviacion del espectro respecto de su centroide
    ancho = float(np.sqrt(((f - centroide) ** 2 * e).sum() / e.sum()))
    return {"cresta": float(cresta), "ocupacion": ocupacion,
            "centroide": centroide, "ancho": ancho}


def _cargar(archivo: Path, desde: float | None, separar_: bool) -> dict[str, np.ndarray]:
    """Devuelve {bus: senial}. De un WAV propio por bandas; de un mp3 por stems."""
    if not separar_:
        y, _ = librosa.load(archivo, sr=SR, mono=True)
        return {"mezcla": y}
    from separar import MARGEN_S, separar
    dur = 32.0
    rutas = separar(archivo, desde or 180.0, dur)
    recorte = min(desde or 180.0, MARGEN_S)
    return {n: librosa.load(p, sr=SR, mono=True, offset=recorte, duration=dur)[0]
            for n, p in rutas.items()}


def mostrar(archivo: Path, desde: float | None, separar_: bool) -> dict:
    piezas = _cargar(archivo, desde, separar_)
    print(f"\n  {archivo.stem[:66]}")
    print(f"   {'bus':<10} {'cresta':>8} {'ocupa':>7} {'centro':>8} {'ancho':>8}   objetivo del genero")
    fuera = {}
    for bus, (stem, lo, hi) in BUSES.items():
        y = piezas.get(stem if separar_ else "mezcla")
        if y is None:
            continue
        m = medir(y, lo, hi)
        if not m:
            continue
        fuera[bus] = m
        o = OBJETIVO[bus]
        marca = "  " if o["cresta"][0] - 2 <= m["cresta"] <= o["cresta"][1] + 2 else "->"
        print(f"  {marca}{bus:<10} {m['cresta']:7.1f}dB {m['ocupacion']:6.0%} "
              f"{m['centroide']:7.0f}Hz {m['ancho']:7.0f}Hz   "
              f"cresta {o['cresta'][0]:.0f}-{o['cresta'][1]:.0f} · "
              f"ocupa {o['ocupacion'][0]:.0%}-{o['ocupacion'][1]:.0%} · "
              f"centro {o['centroide'][0]:.0f}-{o['centroide'][1]:.0f}")
    print("\n   cresta alta = tres parciales limpios y nada en el medio (suena a sinte barato)")
    print("   cresta baja = espectro lleno. Es lo que separa una produccion de un boceto.")
    print("   La flatness NO se reporta: varia x7 entre medir por Demucs y por render directo.")
    return fuera


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", type=Path, nargs="?")
    ap.add_argument("--desde", type=float)
    ap.add_argument("--separar", action="store_true",
                    help="separar en stems con Demucs (para referencias en mp3)")
    ap.add_argument("--solo", type=Path,
                    help="un WAV de un bus grabado solo: se mide como ese bus")
    ap.add_argument("--bus", default="melodico", choices=list(BUSES))
    args = ap.parse_args()

    if args.solo:
        y, _ = librosa.load(args.solo, sr=SR, mono=True)
        lo, hi = BUSES[args.bus][1:]
        m = medir(y, lo, hi)
        o = OBJETIVO[args.bus]
        print(f"\n  {args.solo.stem} como bus '{args.bus}':")
        print(f"   cresta {m['cresta']:.1f} dB (objetivo {o['cresta'][0]:.0f}-{o['cresta'][1]:.0f})")
        print(f"   ocupacion {m['ocupacion']:.0%} (objetivo {o['ocupacion'][0]:.0%}-{o['ocupacion'][1]:.0%})")
        print(f"   centroide {m['centroide']:.0f} Hz (objetivo {o['centroide'][0]:.0f}-{o['centroide'][1]:.0f})")
        return
    if not args.archivo:
        sys.exit("dame un archivo, o --solo <wav> --bus <bus>")
    mostrar(args.archivo, args.desde, args.separar)


if __name__ == "__main__":
    main()
