"""Mide el arco de un set largo directamente del audio, sin necesitar tracklist.

POR QUE EXISTE
--------------
La evidencia de referencia del proyecto son setlists: nombres de temas en orden,
de los que sacamos energia, key y BPM buscando cada track en la biblioteca. Eso
tiene dos problemas. Uno, la mayoria de los sets buenos no publican tracklist (el
de Maze 28 en La Biblioteca no lo tiene y nadie lo contesta en los comentarios).
Dos, cuando lo publican, la energia que le atribuimos sale de NUESTRO calculo
sobre NUESTRA copia del track, no de lo que sono esa noche.

El audio del set no tiene ninguno de los dos problemas. Un video de YouTube de
tres horas es el set entero, en orden, con las mezclas reales y con lo que el DJ
efectivamente hizo con el EQ. Lo que se pierde es la identidad de los temas; lo
que se gana es el arco.

QUE MIDE, Y QUE NO
------------------
Por bloque de 60 s: BPM, densidad de onsets, balance espectral (sub / bajo /
medio / aire) y RMS.

El RMS de un set subido a YouTube esta casi plano: la plataforma normaliza y el
sistema del club comprime. NO usarlo como energia. La energia percibida en una
mezcla larga vive en el brillo (aire), en la densidad ritmica y en el tempo, que
sobreviven a la normalizacion. Por eso la curva de energia de aca es un indice
compuesto de esos tres, y se reporta en z (desvios respecto del promedio del
propio set), no en la escala E1-E10 de la biblioteca: son unidades distintas y
mezclarlas daria una comparacion falsa.

El BPM por bloque se estima con autocorrelacion y puede caer en el doble o la
mitad (60 vs 120). El script pliega todo a [95, 145].

USO
---
    python scripts/arco_de_audio.py <archivo.wav> --nombre maze_biblioteca
    -> data/arcos/<nombre>.json  +  una curva en texto por pantalla
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BLOQUE_SEG = 60
SR = 22050
BANDAS = {"sub": (20, 120), "bajo": (120, 500), "medio": (500, 4000), "aire": (4000, 11000)}
BPM_MIN, BPM_MAX = 95.0, 145.0
DEST = Path("data/arcos")


def _plegar_bpm(bpm: float) -> float:
    """Lleva una estimacion al rango de la pista de baile duplicando o partiendo."""
    if bpm <= 0 or not np.isfinite(bpm):
        return float("nan")
    while bpm < BPM_MIN:
        bpm *= 2
    while bpm > BPM_MAX:
        bpm /= 2
    return float(bpm)


def _bandas(y: np.ndarray) -> dict[str, float]:
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=1024))
    freqs = librosa.fft_frequencies(sr=SR, n_fft=2048)
    total = float(S.sum()) or 1.0
    out = {}
    for nombre, (lo, hi) in BANDAS.items():
        m = (freqs >= lo) & (freqs < hi)
        out[nombre] = float(S[m].sum() / total)
    return out


def medir(path: Path) -> list[dict]:
    info = sf.info(str(path))
    assert info.samplerate == SR, f"esperaba {SR} Hz, vino {info.samplerate}"
    n_bloques = int(info.frames // (SR * BLOQUE_SEG))
    bloques = []
    with sf.SoundFile(str(path)) as f:
        for i in range(n_bloques):
            y = f.read(SR * BLOQUE_SEG, dtype="float32")
            if y.ndim > 1:
                y = y.mean(axis=1)
            env = librosa.onset.onset_strength(y=y, sr=SR)
            onsets = librosa.onset.onset_detect(onset_envelope=env, sr=SR)
            tempo = librosa.feature.tempo(onset_envelope=env, sr=SR, aggregate=None)
            b = _bandas(y)
            bloques.append({
                "min": i * BLOQUE_SEG // 60,
                "bpm": _plegar_bpm(float(np.median(tempo))),
                "onsets_seg": len(onsets) / BLOQUE_SEG,
                "rms_db": float(20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-9)),
                **{k: round(v, 4) for k, v in b.items()},
            })
            if i % 20 == 0:
                print(f"  bloque {i}/{n_bloques}", flush=True)
    return bloques


def _z(xs: list[float]) -> np.ndarray:
    a = np.asarray(xs, dtype=float)
    s = a.std() or 1.0
    return (a - a.mean()) / s


def energia(bloques: list[dict]) -> np.ndarray:
    """Indice compuesto: brillo + densidad ritmica + tempo, cada uno en z.

    Sin el RMS, que en un set normalizado no dice nada (ver docstring).
    """
    return (_z([b["aire"] for b in bloques])
            + _z([b["onsets_seg"] for b in bloques])
            + _z([b["bpm"] for b in bloques])) / 3.0


def suavizar(a: np.ndarray, ventana: int = 5) -> np.ndarray:
    k = np.ones(ventana) / ventana
    return np.convolve(a, k, mode="same")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--nombre", required=True)
    args = ap.parse_args()

    bloques = medir(Path(args.audio))
    e = suavizar(energia(bloques))
    for b, v in zip(bloques, e):
        b["energia_z"] = round(float(v), 3)

    n = len(bloques)
    pico = int(np.argmax(e))
    doc = {
        "nombre": args.nombre,
        "duracion_min": n,
        "bloques": bloques,
        "pico_en_min": pico,
        "pico_en_pct": round(pico / n, 3),
        "bpm_inicio": round(float(np.median([b["bpm"] for b in bloques[:10]])), 1),
        "bpm_pico": round(float(np.median([b["bpm"] for b in bloques[max(0, pico - 5):pico + 5]])), 1),
        "bpm_cierre": round(float(np.median([b["bpm"] for b in bloques[-10:]])), 1),
        "rango_bpm": round(max(b["bpm"] for b in bloques) - min(b["bpm"] for b in bloques), 1),
        "caida_post_pico_z": round(float(e[pico] - np.median(e[pico:])), 2),
    }
    DEST.mkdir(parents=True, exist_ok=True)
    out = DEST / f"{args.nombre}.json"
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{args.nombre} — {n} min, pico al {doc['pico_en_pct']:.0%}")
    print(f"BPM: arranca {doc['bpm_inicio']}, pico {doc['bpm_pico']}, cierra {doc['bpm_cierre']}\n")
    lo, hi = float(e.min()), float(e.max())
    for i in range(0, n, 5):
        pos = int((e[i] - lo) / ((hi - lo) or 1) * 40)
        print(f"{i:4d}m {bloques[i]['bpm']:5.1f} |{'.' * pos}{chr(9608)}")
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
