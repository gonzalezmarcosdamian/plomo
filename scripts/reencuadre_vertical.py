# -*- coding: utf-8 -*-
"""Pasa una toma horizontal a vertical 9:16 siguiendo al DJ, como un camarografo con buen pulso.

POR QUE
-------
Para los Reels, TikTok y Shorts con sus tomas reales (ver .claude/agents/redes.md). Un recorte fijo
al centro lo pierde si se corre; uno que lo sigue cuadro por cuadro marea. Aca el centro del cuerpo
sale de `momentos.py` (MediaPipe Pose, 6 muestras por segundo), se suaviza sin retraso y la camara
no se mueve mientras el siga dentro de la zona del medio: solo acompana cuando se va de ahi.

La imagen sale sin corregir: el color lo pone el editor (`--filtro` agrega lo que se le pase a ffmpeg).

USO
---
    python scripts/momentos.py grabaciones/video/IMG_2209.MOV          # una vez, deja el centro
    python scripts/reencuadre_vertical.py grabaciones/video/IMG_2209.MOV --desde 368 --seg 15
        [--filtro "..."] [--salida C:/Users/gonza/Videos/x.mp4]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FPS = 30
SUAVE_S = 1.5          # sigma del suavizado: el pulso de la camara
ZONA = 0.10            # mientras el centro del cuerpo no se aleje mas que esto del centro del cuadro, quieta


def recorrido(centro: list, muestras_por_s: int, desde: float, seg: float, ancho_src: int, ancho_crop: int) -> np.ndarray:
    c = np.array([np.nan if v is None else v for v in centro], np.float64)
    ok = ~np.isnan(c)
    t_m = np.arange(len(c)) / muestras_por_s
    c = np.interp(t_m, t_m[ok], c[ok])                              # huecos sin persona: el ultimo lugar visto
    t = desde + np.arange(int(round(seg * FPS))) / FPS
    x = np.interp(t, t_m, c) * ancho_src
    # suavizado gaussiano de ida y vuelta: no atrasa al DJ
    k = int(3 * SUAVE_S * FPS)
    nucleo = np.exp(-0.5 * (np.arange(-k, k + 1) / (SUAVE_S * FPS)) ** 2)
    x = np.convolve(np.pad(x, k, mode="edge"), nucleo / nucleo.sum(), mode="valid")
    # zona muerta: la camara sostiene hasta que el DJ se va del medio
    camara = np.empty_like(x)
    actual = x[0]
    for i, v in enumerate(x):
        if abs(v - actual) > ZONA * ancho_crop:
            actual += (v - actual) - np.sign(v - actual) * ZONA * ancho_crop
        camara[i] = actual
    return np.clip(camara - ancho_crop / 2, 0, ancho_src - ancho_crop)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--desde", type=float, required=True)
    ap.add_argument("--seg", type=float, required=True)
    ap.add_argument("--filtro", default="")
    ap.add_argument("--salida")
    a = ap.parse_args()
    video = RAIZ / a.video
    m = json.loads((RAIZ / "data" / "video" / f"{video.stem}_momentos.json").read_text(encoding="utf-8"))
    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                                    "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout.strip().split(",")[:2])
    ancho_crop = int(round(h * 9 / 16 / 2) * 2)
    xs = recorrido(m["centro_x"], m["muestras_por_s"], a.desde, a.seg, w, ancho_crop)
    comandos = "".join(f"{k / FPS:.4f} crop x {int(x)};\n" for k, x in enumerate(xs))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(comandos)
        archivo = Path(f.name)
    salida = Path(a.salida) if a.salida else Path(r"C:\Users\gonza\Videos") / f"plomo_prueba_vertical_{video.stem}_{int(a.desde)}.mp4"
    ruta = archivo.as_posix().replace(":", "\\:")
    vf = f"fps={FPS},sendcmd=f='{ruta}',crop={ancho_crop}:{h}:{int(xs[0])}:0,scale=1080:1920:flags=lanczos"
    if a.filtro:
        vf += "," + a.filtro
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.desde), "-t", str(a.seg), "-i", str(video), "-map", "0:v",
                    "-map", "0:a:0", "-vf", vf, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-b:a", "256k", "-movflags", "+faststart", str(salida)], check=True)
    archivo.unlink()
    print(f"-> {salida}  (la camara se movio {xs.max() - xs.min():.0f} px de {w})")


if __name__ == "__main__":
    main()
