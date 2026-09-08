"""Convierte una frase hablada en una frase cantada, afinandola por palabra.

Por que existe: ningun TTS canta. Pero cantar, para lo que hace falta acá, es
que cada palabra caiga en una altura de la escala en vez de seguir la entonacion
del habla. Eso si se puede hacer despues: se parte la frase por los silencios,
se afina cada tramo a un grado del acorde y se vuelve a pegar.

El resultado no es una cantante. Es un vocal chop afinado, que es exactamente lo
que usa el genero — la voz entra como un instrumento mas, no como una interprete.

La linea sube. Una frase que sube es tension, y una que baja es cierre: si la
voz entra antes del drop tiene que estar subiendo.

Uso:
    python scripts/voz_cantada.py postproduction/audio/voz/voz_ava.wav --camelot 11A
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from plomo.midi import MENOR, tonica_de_camelot  # noqa: E402

USER_LIBRARY = Path("C:/Users/gonza/OneDrive/Documentos/Ableton/User Library/Samples/plomo")

# Grados de la escala para cada tramo, en orden. Sube: i - III - v - octava.
# Si hay mas tramos que grados se repite el ultimo, que deja la frase arriba.
CONTORNO = [0, 2, 4, 7]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", type=Path)
    ap.add_argument("--camelot", default="11A")
    ap.add_argument("--octava", type=int, default=4,
                    help="octava destino; 4 deja la voz donde la grabo el TTS")
    ap.add_argument("--salida", type=Path)
    args = ap.parse_args()

    if not args.archivo.exists():
        sys.exit(f"no existe {args.archivo}")

    y, sr = librosa.load(args.archivo, sr=44100)
    tramos = librosa.effects.split(y, top_db=32, frame_length=2048, hop_length=256)
    if len(tramos) < 2:
        sys.exit("  no se pudo partir la frase en palabras")

    f0, _, _ = librosa.pyin(y, sr=sr, fmin=80, fmax=400)
    validos = f0[~np.isnan(f0)]
    if not len(validos):
        sys.exit("  no se detecto altura en la voz")
    origen = float(librosa.hz_to_midi(np.median(validos)))

    tonica, menor = tonica_de_camelot(args.camelot)
    escala = MENOR if menor else [0, 2, 4, 5, 7, 9, 11]

    salida = np.zeros_like(y)
    print(f"  altura del habla: MIDI {origen:.1f}")
    for i, (a, b) in enumerate(tramos):
        g = CONTORNO[min(i, len(CONTORNO) - 1)]
        destino = 12 * args.octava + tonica + escala[g % len(escala)] + 12 * (g // len(escala))
        pasos = destino - origen
        # se afina el tramo, no la frase entera: afinar todo junto conserva la
        # entonacion del habla, que es justo lo que hay que sacar
        trozo = librosa.effects.pitch_shift(y[a:b], sr=sr, n_steps=pasos)
        n = min(len(trozo), len(salida) - a)
        salida[a:a + n] += trozo[:n]
        print(f"    tramo {i + 1}: {(b - a) / sr:.2f}s  ->  MIDI {destino}  "
              f"({pasos:+.1f} semitonos)")

    salida = salida / (np.abs(salida).max() or 1.0) * 0.89
    destino_wav = args.salida or args.archivo.with_name(args.archivo.stem + "_cantada.wav")
    sf.write(destino_wav, salida, sr)
    if USER_LIBRARY.exists():
        sf.write(USER_LIBRARY / destino_wav.name, salida, sr)
    print(f"\n  {destino_wav}")


if __name__ == "__main__":
    main()
