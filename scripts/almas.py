# -*- coding: utf-8 -*-
"""Maqueta de 1 minuto de la historia de las almas (scripts/shaders/almas.frag, look cielo).

"Hace solo una maqueta de 1 minuto con todo" (el DJ, 2026-10-27): la historia entera en un
minuto, sobre el set 159. Se conocen, vuelan juntas, se separan, una se apaga y se aleja, vuelve y
la otra la cura (en el drop de The Captain), vuelan otra vez, se alejan, y al final se separan
brillando las dos. El cielo pasa detras (uCam) para que se sienta el vuelo sin perderlas de cuadro.

Uso:
    python scripts/almas.py --salida C:/Users/gonza/Videos/plomo_prueba_almas.mp4
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import moderngl
import numpy as np
import soundfile as sf
from PIL import Image
from scipy.signal import butter, sosfilt

RAIZ = Path(__file__).resolve().parents[1]
SHADER = RAIZ / "scripts" / "shaders" / "almas.frag"
MIX = RAIZ / "postproduction" / "mixes" / "159_mix"
VERTICES = "#version 330\nin vec2 pos;\nvoid main() { gl_Position = vec4(pos, 0.0, 1.0); }\n"
FPS, LARGO, DROP_EN = 30, 60.0, 36.0     # el drop cae en el segundo 36: la cura
TEMA_DROP = "The Captain"
# (segundo, alma A, alma B, luz A, luz B, cielo): A es la calida, B la fria
CLAVES = [
    (0, (-0.75, 0.05), (0.75, 0.15), 0.45, 0.45, (0.0, 0.0)),     # aparecen lejos
    (5, (-0.10, 0.08), (0.08, 0.10), 0.90, 0.90, (0.02, 0.0)),    # se conocen
    (7, (-0.03, 0.09), (0.03, 0.11), 1.0, 1.0, (0.10, 0.02)),
    (14, (-0.04, 0.12), (0.04, 0.15), 1.0, 1.0, (1.40, 0.30)),    # vuelan juntas
    (20, (-0.30, 0.05), (0.30, 0.18), 1.0, 1.0, (1.80, 0.38)),    # se separan
    (27, (-0.25, 0.02), (0.62, 0.25), 1.0, 0.12, (1.90, 0.40)),   # B se apaga y se aleja
    (31, (-0.05, 0.06), (0.30, 0.15), 1.0, 0.15, (1.92, 0.40)),   # B vuelve, A va a buscarla
    (35, (0.10, 0.10), (0.14, 0.11), 0.85, 0.20, (1.93, 0.40)),
    (36, (0.10, 0.10), (0.14, 0.11), 0.80, 0.35, (1.93, 0.40)),   # el drop: A le pasa la luz
    (38, (0.09, 0.11), (0.15, 0.12), 1.0, 1.0, (1.95, 0.40)),     # curada
    (44, (-0.03, 0.13), (0.03, 0.15), 1.0, 1.0, (3.20, 0.62)),    # vuelan otra vez
    (48, (-0.28, 0.05), (0.30, 0.16), 1.0, 1.0, (3.50, 0.66)),    # se alejan
    (52, (-0.05, 0.10), (0.05, 0.12), 1.0, 1.0, (3.90, 0.70)),    # se vuelven a acercar
    (60, (-0.70, 0.02), (0.70, 0.22), 1.0, 1.0, (4.10, 0.72)),    # se separan brillando
]


def catmull(t: float, ts: np.ndarray, vs: np.ndarray) -> np.ndarray:
    """Interpolacion suave que pasa por cada clave sin frenar en ellas."""
    i = int(np.clip(np.searchsorted(ts, t) - 1, 0, len(ts) - 2))
    p0, p1, p2, p3 = vs[max(i - 1, 0)], vs[i], vs[i + 1], vs[min(i + 2, len(ts) - 1)]
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    return 0.5 * (2 * p1 + (p2 - p0) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2 + (3 * p1 - p0 - 3 * p2 + p3) * u ** 3)


def estado(t: float) -> dict:
    ts = np.array([c[0] for c in CLAVES], float)
    vs = np.array([[*c[1], *c[2], c[3], c[4], *c[5]] for c in CLAVES], float)
    v = catmull(t, ts, vs)
    a, b, cam = v[0:2].copy(), v[2:4].copy(), v[6:8]
    # la cura: A gira alrededor de B en los segundos antes del drop
    giro = np.clip((t - 31) / 3, 0, 1) * (1 - np.clip((t - 36.5) / 1.5, 0, 1))
    a += giro * 0.035 * np.array([np.cos(1.6 * t), 0.6 * np.sin(1.6 * t)])
    # que respiren: un vaiven chico, distinto para cada una
    a += 0.006 * np.array([np.sin(0.7 * t), np.sin(0.9 * t + 1.0)])
    b += 0.006 * np.array([np.sin(0.8 * t + 2.0), np.sin(0.6 * t + 0.5)])
    return {"a": a, "b": b, "luz_a": float(np.clip(v[4], 0, 1)), "luz_b": float(np.clip(v[5], 0, 1)), "cam": cam}


def pulso(audio: np.ndarray, sr: int, n: int) -> np.ndarray:
    """El grave del mix por cuadro, 0 a 1: la luz late apenas con el bombo."""
    grave = sosfilt(butter(4, 120, "lowpass", fs=sr, output="sos"), audio.mean(1))
    por = len(grave) // n
    e = np.sqrt(np.mean(grave[: por * n].reshape(n, por) ** 2, axis=1))
    return np.clip(e / (np.percentile(e, 95) + 1e-9), 0, 1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", required=True)
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--muestras", help="ademas, una hoja con 6 cuadros")
    a = ap.parse_args()
    ancho, alto = map(int, a.res.split("x"))
    mix = json.loads(MIX.with_suffix(".json").read_text(encoding="utf-8"))
    k = next(i for i, t in enumerate(mix["plan"]) if TEMA_DROP in t["tema"])
    drop = mix["plan"][k]["desde"] + mix["estructura"][k]["medido"]["drop"] * 4 * 60 / mix["tempo"]
    desde = drop - DROP_EN
    sr = sf.info(str(MIX.with_suffix(".wav"))).samplerate
    audio, _ = sf.read(str(MIX.with_suffix(".wav")), start=int(desde * sr), stop=int((desde + LARGO) * sr), dtype="float32")
    n = int(LARGO * FPS)
    late = pulso(audio, sr, n)

    ctx = moderngl.create_standalone_context()
    prog = ctx.program(vertex_shader=VERTICES, fragment_shader=SHADER.read_text(encoding="utf-8"))
    vbo = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4").tobytes())
    vao = ctx.vertex_array(prog, [(vbo, "2f", "pos")])
    fbo = ctx.simple_framebuffer((ancho, alto))
    fbo.use()
    prog["uRes"].value = (ancho, alto)
    prog["uLook"].value = 1
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ancho}x{alto}", "-r", str(FPS),
         "-i", "-", "-ss", f"{desde:.3f}", "-t", str(LARGO), "-i", str(MIX.with_suffix(".wav")),
         "-vf", f"vflip,fade=in:0:45,fade=out:{n - 60}:60", "-af", f"afade=in:d=1.5,afade=out:st={LARGO - 2}:d=2",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-shortest", a.salida],
        stdin=subprocess.PIPE)
    dt = 1 / FPS
    muestras = {int(s * FPS): s for s in (3, 10, 24, 36.7, 46, 58)}
    hoja = []
    for f in range(n):
        t = f * dt
        e, e2 = estado(t), estado(t + dt)
        vcam = (e2["cam"] - e["cam"]) / dt
        brillo = 0.94 + 0.06 * late[f]
        valores = {"uTime": t, "uPosA": tuple(e["a"]), "uPosB": tuple(e["b"]), "uCam": tuple(e["cam"]),
                   "uVelA": tuple((e2["a"] - e["a"]) / dt + vcam), "uVelB": tuple((e2["b"] - e["b"]) / dt + vcam),
                   "uLuzA": e["luz_a"] * brillo, "uLuzB": e["luz_b"] * brillo}
        for nombre, valor in valores.items():
            prog[nombre].value = valor
        vao.render(moderngl.TRIANGLE_STRIP)
        crudo = fbo.read(components=3)
        ff.stdin.write(crudo)
        if f in muestras:
            hoja.append(Image.frombytes("RGB", (ancho, alto), crudo).transpose(Image.FLIP_TOP_BOTTOM).resize((480, 270)))
    ff.stdin.close()
    ff.wait()
    if a.muestras and hoja:
        lienzo = Image.new("RGB", (960, 270 * 3))
        for i, im in enumerate(hoja):
            lienzo.paste(im, ((i % 2) * 480, (i // 2) * 270))
        lienzo.save(a.muestras, quality=85)
    print(f"{a.salida}  ({LARGO:.0f} s, desde {int(desde // 60)}:{desde % 60:04.1f} del mix, drop de {TEMA_DROP} en el s {DROP_EN:.0f})")


if __name__ == "__main__":
    main()
