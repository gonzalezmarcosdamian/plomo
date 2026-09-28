# -*- coding: utf-8 -*-
"""Renderiza la animacion del set cuadro por cuadro en la GPU y la junta con el master.

POR QUE
-------
Fuera de tiempo real: cada cuadro se dibuja con los rasgos de SU instante
(video_rasgos.py), asi que la sincronia es exacta y el video sale igual cada vez
que se corre. El shader es el look; los rasgos son la musica; el master es el
audio. Cambiar el look es cambiar un archivo .frag, no volver a medir.

TEXTO
-----
El nombre de cada tema aparece abajo a la izquierda unos segundos despues de la
mitad del blend, cuando el tema ya manda. En este nicho el tracklist es parte de
lo que se ofrece (docs/YOUTUBE_SERIE.md: "vendes lo contrario, decir todo").

USO
---
    # prototipo de 20 s en 1080p, con el titulo del tema visible
    python scripts/video_animar.py --nombre 2026-09-23 --master <wav> --desde 1370 --segundos 20
        --res 1920x1080 --mostrar-titulo --salida postproduction/video/prototipo.mp4
    # el video entero en 4K con el audio en PCM, para subir
    python scripts/video_animar.py --nombre 2026-09-23 --master <wav> --res 3840x2160
        --salida postproduction/video/2026-09-23_atardecer.mov
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import moderngl
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
RASGOS = ROOT / "data" / "video"
SHADERS = Path(__file__).resolve().parent / "shaders"
FUENTE = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
TITULO_DESDE_S = 4.0       # despues del inicio del capitulo
TITULO_DURA_S = 10.0
TITULO_FUNDIDO_S = 1.5
# el viento de cada tema: desplazamiento del dominio del ruido y direccion del flujo
VIENTOS = [((0.0, 0.0), 0.10), ((1.2, 0.4), -0.18), ((0.5, 1.3), 0.28), ((1.6, 1.1), -0.05)]

VERTEX = """
#version 330
in vec2 pos;
void main() { gl_Position = vec4(pos, 0.0, 1.0); }
"""


def texto_del_tema(w: int, h: int, n: int, total: int, artista: str, titulo: str) -> bytes:
    """Imagen RGBA del cartel del tema, del tamano del cuadro."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    grande = ImageFont.truetype(str(FUENTE), int(h * 0.036))
    grande.set_variation_by_name("SemiBold")
    chica = ImageFont.truetype(str(FUENTE), int(h * 0.026))
    chica.set_variation_by_name("Light")
    # en vertical (Shorts) el 20% de abajo lo tapa la interfaz de YouTube
    x, y = (int(w * 0.08), int(h * 0.62)) if h > w else (int(w * 0.055), int(h * 0.80))
    sombra = max(2, h // 540)
    renglones = [(artista, grande, (255, 255, 255, 235)), (titulo, chica, (255, 255, 255, 215))]
    if w > h:   # el "02 / 04" solo tiene sentido dentro del set entero, no en un Short suelto
        renglones.insert(0, (f"{n:02d} / {total:02d}", chica, (255, 255, 255, 150)))
    for texto, fuente, color in renglones:
        d.text((x + sombra, y + sombra), texto, font=fuente, fill=(0, 0, 0, 120))
        d.text((x, y), texto, font=fuente, fill=color)
        y += int(fuente.size * 1.25)
    return img.tobytes()


def alfa_del_titulo(t: float, inicio: float) -> float:
    a, b = inicio + TITULO_DESDE_S, inicio + TITULO_DESDE_S + TITULO_DURA_S
    if t < a or t > b:
        return 0.0
    return float(min(1.0, (t - a) / TITULO_FUNDIDO_S, (b - t) / TITULO_FUNDIDO_S))


def ffmpeg_salida(salida: Path, w: int, h: int, fps: int, master: Path, desde: float, segundos: float) -> list[str]:
    final = salida.suffix.lower() == ".mov"
    audio = ["-c:a", "pcm_s24le"] if final else ["-c:a", "aac", "-b:a", "320k"]
    return ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
            "-ss", f"{desde:.3f}", "-t", f"{segundos:.3f}", "-i", str(master),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "hevc_nvenc", "-preset", "p7", "-tune", "hq", "-rc", "vbr", "-cq", "17",
            "-b:v", "0", "-profile:v", "main", "-pix_fmt", "yuv420p", "-tag:v", "hvc1",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            *audio, "-shortest", str(salida)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--master", required=True)
    ap.add_argument("--shader", default="atardecer")
    ap.add_argument("--desde", type=float, default=0.0)
    ap.add_argument("--segundos", type=float, default=None)
    ap.add_argument("--res", default="3840x2160")
    ap.add_argument("--mostrar-titulo", action="store_true",
                    help="en un prototipo, muestra el cartel del tema que suena al principio del tramo")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()

    r = np.load(RASGOS / f"{a.nombre}_rasgos.npz")
    caps = json.loads((RASGOS / f"{a.nombre}_capitulos.json").read_text(encoding="utf-8"))["capitulos"]
    fps = int(r["fps"])
    n_total = len(r["cuerpo"])
    i0 = int(a.desde * fps)
    i1 = n_total if a.segundos is None else min(n_total, i0 + int(a.segundos * fps))
    w, h = (int(v) for v in a.res.split("x"))

    ctx = moderngl.create_standalone_context()
    frag = (SHADERS / f"{a.shader}.frag").read_text(encoding="utf-8")
    prog = ctx.program(vertex_shader=VERTEX, fragment_shader=frag)
    quad = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4").tobytes())
    vao = ctx.vertex_array(prog, [(quad, "2f", "pos")])
    fbo = ctx.simple_framebuffer((w, h), components=3)
    fbo.use()
    tex = ctx.texture((w, h), 4)
    tex.use(0)
    prog["uTexto"] = 0
    prog["uRes"] = (w, h)
    carteles = {k: texto_del_tema(w, h, k + 1, len(caps), c["artista"], c["titulo"]) for k, c in enumerate(caps)}
    inicios = [c["t"] for c in caps]
    if a.mostrar_titulo:
        k_actual = int(np.searchsorted(inicios, a.desde, side="right") - 1)
        inicios[k_actual] = a.desde - TITULO_DESDE_S + 1.0
    cartel_cargado = -1

    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(ffmpeg_salida(salida, w, h, fps, Path(a.master), i0 / fps, (i1 - i0) / fps),
                            stdin=subprocess.PIPE)
    t_arranque = time.time()
    for i in range(i0, i1):
        t = i / fps
        pal = r["paleta"][i]
        pesos = r["temas"][i]
        deriva = sum(p * np.array(v[0]) for p, v in zip(pesos, VIENTOS))
        angulo = sum(p * v[1] for p, v in zip(pesos, VIENTOS))
        k = int(np.searchsorted(inicios, t, side="right") - 1)
        alfa = alfa_del_titulo(t, inicios[k])
        if alfa > 0 and k != cartel_cargado:
            tex.write(carteles[k])
            cartel_cargado = k
        prog["uTime"] = t
        prog["uFondo"], prog["uCielo"], prog["uResplandor"], prog["uBrillo"] = (tuple(c) for c in pal)
        prog["uBombo"] = float(r["bombo"][i])
        prog["uBajo"] = float(r["bajo"][i])
        prog["uCuerpo"] = float(r["cuerpo"][i])
        prog["uAire"] = float(r["aire"][i])
        prog["uChispa"] = float(r["brillo"][i])
        prog["uNoche"] = float(1.0 - r["luz_cielo"][i])
        prog["uDeriva"] = tuple(float(v) for v in deriva)
        prog["uAngulo"] = float(angulo)
        prog["uTextoAlfa"] = alfa
        vao.render(moderngl.TRIANGLE_STRIP)
        proc.stdin.write(fbo.read(components=3))
        if (i - i0) % (fps * 30) == 0 and i > i0:
            hechos = i - i0
            ritmo = hechos / (time.time() - t_arranque)
            print(f"  {hechos / fps / 60:5.1f} min de {(i1 - i0) / fps / 60:.1f}  "
                  f"{ritmo:.1f} cuadros/s  faltan {(i1 - i) / ritmo / 60:.1f} min", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit("ffmpeg fallo")
    print(f"-> {salida}  ({(i1 - i0) / fps:.1f} s en {time.time() - t_arranque:.0f} s)")


if __name__ == "__main__":
    main()
