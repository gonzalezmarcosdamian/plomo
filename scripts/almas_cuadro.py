# -*- coding: utf-8 -*-
"""Un cuadro de scripts/shaders/almas.frag, para elegir el look antes de hacer video.

"Trabajemos en una idea nueva de maqueta de video, la idea es que sea una historia de amor
abstracta" (el DJ, 2026-10-27), y de los tres looks: "mostrame las 3". Un cuadro por look en el
mismo momento de la historia cuesta segundos; el video entero se hace recien con el look elegido.

Uso:
    python scripts/almas_cuadro.py --salida C:/Users/gonza/Pictures/plomo_almas_looks.jpg
"""
from __future__ import annotations

import argparse
from pathlib import Path

import moderngl
import numpy as np
from PIL import Image, ImageDraw

SHADER = Path(__file__).resolve().parent / "shaders" / "almas.frag"
VERTICES = """#version 330
in vec2 pos;
void main() { gl_Position = vec4(pos, 0.0, 1.0); }
"""
LOOKS = ["Dos luces sobre el mar", "Dos luces en el cielo", "Particulas en negro"]
# "vuelan juntas": cerca, las dos plenas, subiendo hacia la derecha
JUNTAS = {"uPosA": (-0.05, 0.10), "uPosB": (0.04, 0.13), "uVelA": (0.18, 0.05), "uVelB": (0.18, 0.06),
          "uLuzA": 1.0, "uLuzB": 1.0, "uTime": 12.0}


def cuadro(look: int, ancho: int, alto: int, uniformes: dict) -> Image.Image:
    ctx = moderngl.create_standalone_context()
    prog = ctx.program(vertex_shader=VERTICES, fragment_shader=SHADER.read_text(encoding="utf-8"))
    for nombre, valor in {**uniformes, "uRes": (ancho, alto), "uLook": look}.items():
        if nombre in prog:
            prog[nombre].value = valor
    vbo = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4").tobytes())
    vao = ctx.vertex_array(prog, [(vbo, "2f", "pos")])
    fbo = ctx.simple_framebuffer((ancho, alto))
    fbo.use()
    vao.render(moderngl.TRIANGLE_STRIP)
    im = Image.frombytes("RGB", (ancho, alto), fbo.read(components=3)).transpose(Image.FLIP_TOP_BOTTOM)
    ctx.release()
    return im


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ancho", type=int, default=960)
    a = ap.parse_args()
    alto = a.ancho * 9 // 16
    hoja = Image.new("RGB", (a.ancho, (alto + 34) * len(LOOKS)), (14, 14, 16))
    dib = ImageDraw.Draw(hoja)
    for k, nombre in enumerate(LOOKS):
        hoja.paste(cuadro(k, a.ancho, alto, JUNTAS), (0, k * (alto + 34) + 34))
        dib.text((10, k * (alto + 34) + 10), f"{k + 1}. {nombre} - vuelan juntas", fill=(243, 235, 221))
    hoja.save(a.salida, quality=88)
    print(a.salida)


if __name__ == "__main__":
    main()
