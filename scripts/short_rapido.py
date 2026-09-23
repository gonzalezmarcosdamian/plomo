# -*- coding: utf-8 -*-
"""Convierte un video largo de set en un short mudo de N segundos.

POR QUE
-------
"Quiero un video sin audio de todo el video pero rapido que dure 20 seg, le voy
a poner un tema de IG arriba" (el DJ, 2026-09-23). El recorrido entero de la
noche en veinte segundos, sin sonido, para que la musica la ponga la app.

EL TRUCO QUE IMPORTA
--------------------
Comprimir 26 minutos a 20 segundos es 77x. Hecho con `setpts=PTS/77`, ffmpeg
DECODIFICA los 93.000 cuadros del 4K60 para quedarse con 600: son cuarenta
minutos de CPU. Con `-skip_frame nokey` decodifica SOLO los keyframes —que en un
video de iPhone caen cada uno o dos segundos, o sea mas de los 600 que hacen
falta— y tarda ONCE SEGUNDOS. Mismo resultado visual.

La diferencia entre once segundos y cuarenta minutos es elegir que se decodifica,
no que tan rapido se decodifica.

USO
---
    python scripts/short_rapido.py <video> --segundos 20
    python scripts/short_rapido.py <video> --horizontal
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FPS = 30


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--segundos", type=int, default=20)
    ap.add_argument("--horizontal", action="store_true",
                    help="16:9 en vez del 9:16 que pide Instagram")
    ap.add_argument("--salida")
    args = ap.parse_args()

    entrada = Path(args.video)
    forma = ("scale=1920:1080:flags=lanczos"
             if args.horizontal else
             "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920")
    salida = Path(args.salida) if args.salida else entrada.with_name(
        f"{args.segundos}s_{'horizontal' if args.horizontal else 'vertical'}_IG.mp4")

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-skip_frame", "nokey", "-i", str(entrada),
        "-an", "-vsync", "0",
        "-vf", f"{forma},fps={FPS}",
        "-frames:v", str(args.segundos * FPS),
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(salida),
    ]
    subprocess.run(cmd, check=True)
    mb = salida.stat().st_size / 1e6
    print(f"{salida.name}  {args.segundos}s  {args.segundos * FPS} cuadros  {mb:.1f} MB")
    print("sin audio: la musica se pone en la app")


if __name__ == "__main__":
    main()
