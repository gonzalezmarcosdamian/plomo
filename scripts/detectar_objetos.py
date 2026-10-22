# -*- coding: utf-8 -*-
"""Busca personas, barcos, vehiculos y objetos en un clip de stock antes de usarlo en un video de naturaleza.

POR QUE
-------
El video de la Session 04 tiene que ser "todo naturaleza" (el DJ, 2026-10-21). El agente editor lo
armo para la prueba de 3 minutos: en un clip de costa aparecieron casas y una escalera al pie del
acantilado, y en otro gente en la arena, cosas que en la miniatura no se ven.

Revisa cada PASO segundos el cuadro 4K en mosaicos de 3x3 con solape, porque una persona chica en
4K no se ve en un cuadro achicado. Usa MediaPipe ObjectDetector con EfficientDet-Lite2 (las clases de
COCO). Deja una hoja con el recorte de cada hallazgo en postproduction/stock/detecciones/det_<id>.jpg.
Un ave suelta no cuenta.

USO
---
    python scripts/detectar_objetos.py <id> [desde hasta]
"""
import sys, subprocess
from pathlib import Path
import numpy as np
import mediapipe as mp
from PIL import Image
RAIZ = Path(__file__).resolve().parents[1]
MODELO = RAIZ / "postproduction" / "modelos" / "efficientdet_lite2.tflite"
NAT = RAIZ / "postproduction" / "stock" / "detecciones"
NAT.mkdir(parents=True, exist_ok=True)
S = Path(r"C:\Users\gonza\Documents\plomo\postproduction\stock\pixabay")
PASO = 1.0
UMBRAL = 0.22
NATURAL = {"bird"}            # un ave suelta pasa
i = sys.argv[1]
src = S / f"{i}.mp4"
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                           capture_output=True, text=True).stdout)
t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
t1 = float(sys.argv[3]) if len(sys.argv) > 3 else dur - 0.2
W, H = 1920, 1080
crudo = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.2f}", "-t", f"{t1 - t0:.2f}", "-i", str(src),
                        "-vf", f"fps=1/{PASO},scale={W*2}:{H*2}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True).stdout
fr = np.frombuffer(crudo, np.uint8).reshape(-1, H * 2, W * 2, 3)
op = mp.tasks.vision.ObjectDetectorOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(MODELO)),
                                           score_threshold=UMBRAL, max_results=10)
salida = NAT / f"det_{i}"; salida.mkdir(exist_ok=True)
hallazgos = 0
grupos = {}   # celda de 240 px -> [n, mejor puntaje, categorias, recorte del mejor, t]
with mp.tasks.vision.ObjectDetector.create_from_options(op) as det:
    for k, f in enumerate(fr):
        t = t0 + k * PASO
        # mosaicos 3x3 con solape: cada uno ~1600x900 del cuadro 3840x2160
        for ty in range(3):
            for tx in range(3):
                x0 = int(tx * (W * 2 - 1600) / 2); y0 = int(ty * (H * 2 - 900) / 2)
                tile = np.ascontiguousarray(f[y0:y0 + 900, x0:x0 + 1600])
                r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=tile))
                for d in r.detections:
                    c = d.categories[0]
                    if c.category_name in NATURAL:
                        continue
                    b = d.bounding_box
                    X, Y = x0 + b.origin_x, y0 + b.origin_y
                    hallazgos += 1
                    cel = ((X + b.width // 2) // 240, (Y + b.height // 2) // 240)
                    g = grupos.setdefault(cel, [0, 0.0, set(), None, t])
                    g[0] += 1; g[2].add(c.category_name)
                    if c.score > g[1]:
                        pad = 100
                        g[1] = c.score; g[4] = t
                        g[3] = Image.fromarray(f[max(0, Y - pad):Y + b.height + pad, max(0, X - pad):X + b.width + pad])
orden = sorted(grupos.items(), key=lambda kv: -kv[1][1])[:24]
from PIL import ImageDraw
lado = 300
hoja = Image.new("RGB", (6 * lado, ((len(orden) + 5) // 6 or 1) * (lado + 30)), "black")
dib = ImageDraw.Draw(hoja)
for k, ((cx, cy), (n, sc, cats, im, tt)) in enumerate(orden):
    im = im.copy(); im.thumbnail((lado, lado))
    x, y = (k % 6) * lado, (k // 6) * (lado + 30)
    hoja.paste(im, (x, y + 30))
    dib.text((x + 4, y + 4), f"{'/'.join(sorted(cats))[:22]} {sc:.2f} n={n} t={tt:.0f} ({cx*240},{cy*240})", fill="white")
    print(f"  grupo x~{cx*240} y~{cy*240}: n={n} max={sc:.2f} {sorted(cats)} t={tt:.0f}")
hoja.save(NAT / f"det_{i}.jpg", quality=90)
print(f"{i}: {len(fr)} cuadros revisados ({t0:.0f}-{t1:.0f}s), {hallazgos} hallazgos")
