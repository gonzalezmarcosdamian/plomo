# -*- coding: utf-8 -*-
"""Cuanta voz tiene un tema, medido, no adivinado por el titulo.

POR QUE
El DJ pidio "vocales" y el proyecto no tenia ningun dato de voz: se elegia por
el nombre del tema o por si el artista figura con un cantante al lado, que falla
en las dos direcciones --"Never B Alone" puede ser instrumental y un tema sin
pista en el titulo puede tener una voz entera--.

Demucs ya separa `vocals.wav` en cada corrida; `separar()` devolvia solo tres
stems y ese cuarto quedaba tirado en la carpeta. Aca se usa.

QUE MIDE
  presencia: que fraccion del fragmento tiene voz audible. Separa "tema cantado"
             de "tema con un sample suelto", que es la distincion que importa
             cuando el DJ dice que le faltan vocales.
  peso:      cuanta energia de la mezcla es voz. Dice si la voz es protagonista
             o esta de fondo.

LO QUE NO RESUELVE
Demucs mete en `vocals` cualquier cosa con formantes: un pad con voz sampleada y
procesada cuenta como voz. Para "me falta algo de vocales" eso esta bien --suena
a voz-- pero no sirve para buscar un tema con letra.
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

SR = 22050
SEGUNDOS = 30.0


def _voz(stem_voz: Path, mezcla: Path) -> dict | None:
    """Compara la voz contra la SUMA DE LOS STEMS, no contra el archivo original.

    El bug que esto arregla: el stem de voz sale del 45% del tema --donde Demucs
    corto-- y la mezcla se cargaba del archivo entero con offset 5s, o sea de la
    intro. Comparar el estribillo contra la intro daba pesos imposibles: Satori
    midio 343.9%, y un ratio no puede pasar de 100%. Todos los pesos anteriores
    al 2026-10-01 estan mal por esto; la presencia tambien, porque su umbral
    sale del maximo de la mezcla.

    Los cuatro stems son del MISMO fragmento, asi que sumarlos reconstruye esa
    porcion de la mezcla y el ratio vuelve a significar algo.
    """
    y, _ = librosa.load(stem_voz, sr=SR, offset=min(MARGEN_S, 5.0), duration=SEGUNDOS)
    partes = []
    for nom in ("drums", "bass", "other", "vocals"):
        f = stem_voz.parent / f"{nom}.wav"
        if f.exists():
            a, _ = librosa.load(f, sr=SR, offset=min(MARGEN_S, 5.0), duration=SEGUNDOS)
            partes.append(a)
    if partes:
        n = min(len(a) for a in partes)
        m = sum(a[:n] for a in partes)
    else:
        m, _ = librosa.load(mezcla, sr=SR, offset=min(MARGEN_S, 5.0), duration=SEGUNDOS)
    if len(y) == 0 or len(m) == 0:
        return None
    rv = librosa.feature.rms(y=y, hop_length=512)[0]
    rm = librosa.feature.rms(y=m, hop_length=512)[0]
    n = min(len(rv), len(rm))
    rv, rm = rv[:n], rm[:n]
    piso = max(rm.max() * 0.02, 1e-5)      # -34 dB de la mezcla: audible
    return {
        "presencia": float((rv > piso).mean()),
        "peso": float(rv.sum() / (rm.sum() + 1e-9)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patron", action="append", required=True)
    args = ap.parse_args()
    archivos = [p for p in config.MUSIC_LIBRARY_ROOT.rglob("*")
                if p.suffix.lower() in (".mp3", ".flac", ".wav", ".aiff")]
    for pat in args.patron:
        hit = next((p for p in archivos if pat.lower() in p.name.lower()), None)
        if not hit:
            print(f"  ningun archivo para {pat!r}")
            continue
        dur = librosa.get_duration(path=str(hit))
        stems = separar(hit, dur * 0.45, SEGUNDOS)
        voz = stems["other"].parent / "vocals.wav"
        if not voz.exists():
            print(f"  {hit.stem[:44]:<44}  sin stem de voz")
            continue
        r = _voz(voz, hit)
        if not r:
            print(f"  {hit.stem[:44]:<44}  no se pudo medir")
            continue
        etiqueta = ("CANTADO" if r["presencia"] > 0.60 and r["peso"] > 0.08
                    else "algo de voz" if r["presencia"] > 0.30
                    else "instrumental")
        print(f"  {hit.stem[:44]:<44}  presencia {r['presencia']:.0%}  "
              f"peso {r['peso']:.1%}  -> {etiqueta}")


if __name__ == "__main__":
    main()
