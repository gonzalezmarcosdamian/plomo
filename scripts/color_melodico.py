"""Mide el color de la capa melodica de un grupo de temas.

Por que existe: elegir el instrumento de un boceto por nombre de preset es
adivinar. "Vibes Mellow" sonaba a ringtone y no habia forma de saberlo antes de
cargarlo — hasta que se midio: la capa melodica de los temas que se tocan tiene
el centroide espectral en 1224 Hz y planitud 0.0012, o sea oscura y puramente
armonica, mientras que vibes, campanas y marimba viven en 3-6 kHz con parciales
inarmonicos. La familia estaba mal, no el preset.

Esto permite hacer la misma pregunta por productor: "que color tiene el lead de
Digweed" o "el de Eze Arias" pasa a ser un numero en vez de una impresion.

Mide sobre el stem `other` de Demucs, que es donde quedan pad, arpegio y lead
despues de sacar bateria y bajo.

Lo que NO resuelve: no dice que preset cargar. Descarta familias enteras, que es
la mitad del trabajo; elegir adentro de la familia que queda sigue siendo
criterio, porque para medirlo habria que renderizar cada preset a audio y la
Trial de Live no exporta.

Uso:
    python scripts/color_melodico.py --patron "ezequiel arias" --cuantos 3
    python scripts/color_melodico.py --patron digweed --patron bedrock
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

from plomo import config  # noqa: E402
from separar import MARGEN_S, separar  # noqa: E402

DEPOSITO = config.MUSIC_LIBRARY_ROOT / "Biblioteca"
SR = 22050
SEGUNDOS = 20.0


def _color(stem: Path) -> dict | None:
    y, _ = librosa.load(stem, sr=SR, offset=min(MARGEN_S, 5.0), duration=SEGUNDOS)
    if np.abs(y).max() < 1e-3:
        return None
    env = librosa.onset.onset_strength(y=y, sr=SR)
    # el reparto de energia por octavas dice mas que el centroide solo: dos
    # sonidos con el mismo centroide pueden tener uno el peso abajo y otro
    # repartido, y eso se escucha como sonidos distintos
    stft = np.abs(librosa.stft(y, n_fft=4096))
    frecs = librosa.fft_frequencies(sr=SR, n_fft=4096)
    total = stft.sum() or 1.0
    bandas = {f"{lo}-{hi}Hz": float(stft[(frecs >= lo) & (frecs < hi)].sum() / total)
              for lo, hi in ((0, 500), (500, 2000), (2000, 6000), (6000, 11025))}
    return {
        "centroide": float(np.median(librosa.feature.spectral_centroid(y=y, sr=SR))),
        "planitud": float(np.median(librosa.feature.spectral_flatness(y=y))),
        "rolloff85": float(np.median(librosa.feature.spectral_rolloff(y=y, sr=SR,
                                                                     roll_percent=0.85))),
        "ataque": float(np.percentile(env, 95) / (np.median(env) + 1e-9)),
        **bandas,
    }


def _mejor_momento(archivo: Path) -> float:
    y, sr = librosa.load(archivo, sr=8000, mono=True)
    rms = librosa.feature.rms(y=y, hop_length=1024)[0]
    veces = librosa.times_like(rms, sr=sr, hop_length=1024)
    medio = (veces > veces[-1] * 0.25) & (veces < veces[-1] * 0.80)
    if not medio.any():
        return max(0.0, veces[-1] / 2)
    return float(veces[medio][int(np.argmax(rms[medio]))])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patron", action="append", required=True,
                    help="subcadena del nombre de archivo; se puede repetir")
    ap.add_argument("--cuantos", type=int, default=3)
    ap.add_argument("--etiqueta", default="")
    args = ap.parse_args()

    archivos: list[Path] = []
    for p in args.patron:
        for f in sorted(DEPOSITO.rglob("*.mp3")):
            if p.lower() in f.stem.lower() and f not in archivos:
                archivos.append(f)
    archivos = archivos[:args.cuantos]
    if not archivos:
        sys.exit(f"  ningun archivo para {args.patron}")

    etiqueta = args.etiqueta or "+".join(args.patron)
    filas = []
    for f in archivos:
        desde = _mejor_momento(f)
        rutas = separar(f, desde, SEGUNDOS + 4)
        c = _color(rutas["other"])
        if c is None:
            print(f"  - sin senial: {f.stem[:50]}")
            continue
        filas.append(c)
        print(f"  {f.stem[:44]:<44} {c['centroide']:6.0f}Hz  "
              f"planitud {c['planitud']:.4f}  ataque {c['ataque']:4.1f}")

    if not filas:
        sys.exit("  nada medible")
    print(f"\n  === {etiqueta} ({len(filas)} temas) ===")
    for k in filas[0]:
        v = np.median([f[k] for f in filas])
        if k.endswith("Hz") and "-" in k:
            print(f"    {k:12} {v:6.1%} de la energia")
        else:
            print(f"    {k:12} {v:8.4f}" if k == "planitud" else f"    {k:12} {v:8.1f}")


if __name__ == "__main__":
    main()
