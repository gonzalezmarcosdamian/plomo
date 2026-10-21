# -*- coding: utf-8 -*-
"""Camara lenta suave de un tramo de toma, inventando cuadros con RIFE en la placa de video.

POR QUE
-------
Las tomas del DJ vienen a 60 cuadros por segundo: bajadas a 30 ya dan una camara lenta x2 limpia.
Para ir mas lento (x4 en un gesto, en un break) hacen falta cuadros que no existen; RIFE los
calcula por flujo optico (rife-ncnn-vulkan, Vulkan sobre la RTX 4050, en
postproduction/herramientas/). Sin audio: la camara lenta va sobre la musica que el editor elija.

USO
---
    python scripts/camara_lenta.py grabaciones/video/IMG_2209.MOV --desde 230 --seg 3 --lento 4
        [--res 1920x1080] [--salida C:/Users/gonza/Videos/x.mp4]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RIFE = RAIZ / "postproduction" / "herramientas" / "rife-ncnn-vulkan-20221029-windows"
FPS_SALIDA = 30


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--desde", type=float, required=True)
    ap.add_argument("--seg", type=float, required=True)
    ap.add_argument("--lento", type=float, default=4.0, help="cuantas veces mas lento que la realidad")
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--salida")
    a = ap.parse_args()
    video = RAIZ / a.video
    w, h = a.res.split("x")
    salida = Path(a.salida) if a.salida else Path(r"C:\Users\gonza\Videos") / f"plomo_prueba_lenta_{video.stem}_{int(a.desde)}.mp4"
    with tempfile.TemporaryDirectory() as tmp:
        ent, sal = Path(tmp) / "entrada", Path(tmp) / "salida"
        ent.mkdir(), sal.mkdir()
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a.desde), "-t", str(a.seg), "-i", str(video),
                        "-vf", f"scale={w}:{h}:flags=lanczos", "-fps_mode", "passthrough", str(ent / "%08d.png")], check=True)
        n_in = len(list(ent.glob("*.png")))
        n_out = int(round(a.seg * a.lento * FPS_SALIDA))
        if n_out <= n_in:
            # alcanza con los cuadros que hay (60 fps a 30 = x2): se estiran los reales, no se inventa nada
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", f"{n_in / a.seg:.4f}", "-i", str(ent / "%08d.png"),
                            "-vf", f"setpts=PTS*{a.lento}", "-r", str(FPS_SALIDA), "-c:v", "libx264", "-crf", "16",
                            "-pix_fmt", "yuv420p", str(salida)], check=True)
        else:
            subprocess.run([str(RIFE / "rife-ncnn-vulkan.exe"), "-i", str(ent), "-o", str(sal), "-n", str(n_out),
                            "-m", str(RIFE / "rife-v4.6"), "-f", "%08d.png"], check=True, capture_output=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS_SALIDA), "-i", str(sal / "%08d.png"),
                            "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(salida)], check=True)
        print(f"-> {salida}  ({n_in} cuadros reales -> {n_out}, {a.seg * a.lento:.1f} s a x{a.lento:g})")


if __name__ == "__main__":
    main()
