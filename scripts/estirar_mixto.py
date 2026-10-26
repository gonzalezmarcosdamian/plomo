# -*- coding: utf-8 -*-
"""Estirado mixto de un timelapse con camara quieta: RIFE en el cielo, cuadros reales en lo quieto.

POR QUE
-------
Para que un timelapse corto llene su plano de la Session 04 se estiraba con RIFE (rife-ncnn-vulkan,
en postproduction/herramientas). En el plano 111 la roca de abajo quedo con la mitad del detalle
de la toma y una textura ondulada a 1:1 (el revisor, 2026-10-25). Lo que no se mueve no necesita
cuadros inventados: alcanza fundir los dos cuadros reales vecinos, y asi no pierde nada. El cielo
si se mueve, y ahi sigue RIFE. La mascara se arma una vez con la textura de la toma: de la cresta
para abajo, con borde suave.

USO
---
    python scripts/estirar_mixto.py <fuente_limpia.mp4> <estirado_rife.mp4> <p/q> <salida.mp4>
        [--mascara=png] [--bajar=60] [--suave=16] [--cresta=npy]
    fuente_limpia: los cuadros reales, a 2560x1440 y con el fps de la toma.
    estirado_rife: la misma toma estirada con RIFE por el mismo factor p/q.
    Lo armo el editor para el plano 111; sirve para cualquier timelapse de camara quieta.
"""
from __future__ import annotations

import subprocess
import sys
from fractions import Fraction

import cv2
import numpy as np

pos = [a for a in sys.argv[1:] if not a.startswith("--")]
fuente, rife, factor, salida = pos[0], pos[1], Fraction(pos[2]), pos[3]
opt = {a.split("=")[0][2:]: a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--") and "=" in a}
BAJAR = int(opt.get("bajar", 60))
SUAVE = float(opt.get("suave", 16))
W, H = 2560, 1440
TAM = W * H * 3 * 2


def leer(ruta: str):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", ruta, "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=rgb48le",
                          "-f", "rawvideo", "-pix_fmt", "rgb48le", "-"], stdout=subprocess.PIPE, bufsize=TAM)
    while True:
        b = p.stdout.read(TAM)
        if len(b) < TAM:
            return
        yield np.frombuffer(b, np.uint16).reshape(H, W, 3)


# 1) la cresta, con 25 cuadros repartidos: la roca tiene textura en todos los cuadros, el cielo y las nubes no
N = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", fuente], capture_output=True, text=True).stdout.strip())
paso_m = max(1, N // 25)
tex = []
for k, r in enumerate(leer(fuente)):
    if k % paso_m == 0:
        g = cv2.cvtColor((r >> 8).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
        tex.append(cv2.blur(np.abs(cv2.Laplacian(g, cv2.CV_32F)), (21, 21)))
tmin = np.percentile(np.stack(tex), 20, axis=0)
del tex
roca = (tmin > 4.5).astype(np.uint8)
roca = cv2.morphologyEx(roca, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
roca = cv2.morphologyEx(roca, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
frac = np.cumsum(roca[::-1].astype(np.float32), axis=0)[::-1] / np.arange(H, 0, -1)[:, None]
cresta = np.full(W, H, np.float32)
for x in range(W):
    ys = np.where(frac[:, x] > 0.9)[0]
    if len(ys):
        cresta[x] = ys[0]
cresta = np.array([np.median(cresta[max(0, x - 8):x + 9]) for x in range(W)])
print("cuadros reales", N, flush=True)
if "cresta" in opt:
    cresta = np.load(opt["cresta"]).astype(np.float32)
yy = np.arange(H)[:, None]
masc = np.clip((yy - (cresta[None, :] + BAJAR)) / SUAVE, 0, 1).astype(np.float32)
if "mascara" in opt:
    cv2.imwrite(opt["mascara"], (masc * 255).astype(np.uint8))
print("cresta: min", int(cresta.min()), "mediana", int(np.median(cresta)), "max", int(cresta.max()), flush=True)
m3 = masc[..., None]

# 2) mezclar
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{W}x{H}", "-r", "30",
                        "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p10le",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p10le",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
                        salida], stdin=subprocess.PIPE)
gen = leer(fuente)
cache = {}
sig = 0
def real(j: int):
    global sig
    while sig <= j:
        try:
            cache[sig] = next(gen).astype(np.float32)
        except StopIteration:
            break
        sig += 1
        for viejo in [k for k in cache if k < sig - 3]:
            del cache[viejo]
    return cache[min(j, max(cache))]
n = 0
for i, rf in enumerate(leer(rife)):
    s = i / float(factor)
    a = min(int(s), N - 1)
    b = min(a + 1, N - 1)
    f = s - int(s)
    fundido = (1 - f) * real(a) + f * real(b)
    out = m3 * fundido + (1 - m3) * rf.astype(np.float32)
    enc.stdin.write(np.clip(out, 0, 65535).astype(np.uint16).tobytes())
    n += 1
enc.stdin.close()
enc.wait()
print(salida, n, "cuadros", flush=True)
