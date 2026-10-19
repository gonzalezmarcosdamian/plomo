# -*- coding: utf-8 -*-
"""Renderiza la animacion del set cuadro por cuadro en la GPU y la junta con el master.

POR QUE
-------
Fuera de tiempo real: cada cuadro se dibuja con los rasgos de SU instante
(video_rasgos.py), asi que la sincronia es exacta y el video sale igual cada vez
que se corre. El shader es el look; los rasgos son la musica; el master es el
audio. Cambiar el look es cambiar un archivo .frag, no volver a medir.

LOOKS
-----
Cada video de la serie tiene el suyo (`--shader`): `atardecer` es el cielo sobre la ciudad
con la paleta del telefono (el sunset del 23/09, la Session 01); `marea` es el mar de noche
con la luna saliendo naranja y subiendo plateada a lo largo del set (la Session 02).

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
# vuelo.frag: la hora del dia de cada tema, (cenit, horizonte, sol), en orden; ciclan.
# Son cielos que existen: "mas realismo, no solo las arenas" (el DJ, 2026-10-19).
PALETAS_VUELO = [
    ((0.10, 0.16, 0.30), (1.00, 0.55, 0.25), (1.00, 0.72, 0.42)),   # hora dorada: el naranja de la marca
    ((0.03, 0.06, 0.16), (0.55, 0.47, 0.72), (1.00, 0.66, 0.56)),   # hora azul
    ((0.08, 0.08, 0.22), (0.95, 0.46, 0.50), (1.00, 0.70, 0.60)),   # atardecer rosado
    ((0.01, 0.02, 0.05), (0.18, 0.26, 0.42), (0.75, 0.82, 1.00)),   # noche con luna
    ((0.18, 0.24, 0.40), (1.00, 0.76, 0.46), (1.00, 0.86, 0.62)),   # amanecer
    ((0.05, 0.03, 0.12), (0.70, 0.40, 0.80), (1.00, 0.62, 0.72)),   # violeta
]
BIOMAS_VUELO = 4   # montanas, costa, dunas, mar de nubes: el tema k va al paisaje k % 4
ADELANTO_DROP_S = 1.2    # la camara mira adelante: la picada empieza antes del drop y aterriza con el


def suavizar(x: np.ndarray, sigma_s: float, fps: int) -> np.ndarray:
    n = max(1, int(sigma_s * fps))
    k = np.exp(-0.5 * (np.arange(-3 * n, 3 * n + 1) / n) ** 2)
    return np.convolve(np.pad(x, 3 * n, mode="edge"), k / k.sum(), mode="valid")


def camara(r: dict, fps: int) -> dict[str, np.ndarray]:
    """La forma de cada tema para vuelo.frag, cuadro por cuadro, mirando adelante.

    El bombo no sirve para encontrar el drop: en Thrill entra 10 s despues que el bajo.
    Lo que cae a cero en el breakdown y vuelve de golpe en el drop es bajo + cuerpo."""
    seccion = np.clip(suavizar(np.clip((r["bajo"] + r["cuerpo"]) / 2, 0, 1), 1.0, fps) / 0.55, 0, 1)
    k = int(ADELANTO_DROP_S * fps)
    adelante = np.concatenate([seccion[k:], np.repeat(seccion[-1], k)])
    velocidad = 0.35 + 1.4 * suavizar(adelante, 0.6, fps) + 0.25 * r["bombo"]
    # el impacto es el salto de bajo+cuerpo en un segundo, que despues se apaga solo
    salto = np.clip(seccion - np.concatenate([np.repeat(seccion[0], fps), seccion[:-fps]]), 0, 1)
    impacto = np.empty_like(salto)
    caida, previo = np.exp(-1 / (2.5 * fps)), 0.0
    for i, s in enumerate(salto):
        previo = max(float(s), previo * caida)
        impacto[i] = previo
    paletas = np.array([PALETAS_VUELO[k % len(PALETAS_VUELO)] for k in range(r["temas"].shape[1])])
    # el paisaje: el de los dos temas que mas suenan; en el blend uno se funde en el otro.
    # Cuando el dominante cambia, A y B se dan vuelta con la mezcla en 0.5: no hay salto.
    # Cada tema vuela su propio paisaje desde que empieza a sonar: la distancia LOCAL queda
    # chica (en float32, a la hora y media de set el ruido se volvia escalones).
    distancia = np.cumsum(velocidad) / fps
    origen = distancia[np.argmax(r["temas"] > 1e-3, axis=0)]
    orden = np.argsort(-r["temas"], axis=1)[:, :2]
    filas = np.arange(len(orden))
    pa, pb = r["temas"][filas, orden[:, 0]], r["temas"][filas, orden[:, 1]]
    return {"altura": 1 - suavizar(adelante, 0.8, fps), "distancia": distancia,
            "impacto": impacto, "paleta": np.einsum("ft,tcd->fcd", r["temas"], paletas),
            "tema_a": orden[:, 0], "tema_b": orden[:, 1],
            "local_a": distancia - origen[orden[:, 0]], "local_b": distancia - origen[orden[:, 1]],
            "mezcla": pb / np.maximum(pa + pb, 1e-6)}

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


def poner(prog: moderngl.Program, nombre: str, valor: object) -> None:
    """Cada look usa los rasgos que quiere: marea.frag no lee la paleta del telefono y
    atardecer.frag no sabe en que parte del set esta. Un uniform que el shader no declara
    (o que el compilador saco por no usarse) no existe en el programa, y se saltea."""
    uniforme = prog.get(nombre, None)
    if uniforme is not None:
        uniforme.value = valor


def alfa_del_titulo(t: float, inicio: float) -> float:
    a, b = inicio + TITULO_DESDE_S, inicio + TITULO_DESDE_S + TITULO_DURA_S
    if t < a or t > b:
        return 0.0
    return float(min(1.0, (t - a) / TITULO_FUNDIDO_S, (b - t) / TITULO_FUNDIDO_S))


# El 2026-10-02 la NVIDIA se reinicio tres veces (nvlddmkm 153) y cada vez se llevo puesto al
# codificador NVENC, y despues CUDA no encontraba la placa. En la CPU el video no depende del
# driver: tarda mas, pero no se cae. NVENC queda para cuando la placa este estable.
# "faster" y no "medium": con medium ffmpeg ocupaba 10 de los 12 hilos y el cuello era el, con la
# GL esperando. YouTube recodifica igual; a crf 16 la diferencia de preset es tamano, no imagen.
# Todos los tramos de un video van con el mismo preset, o el concat sin recodificar no los une.
CODIFICADORES = {
    "cpu": ["-c:v", "libx264", "-preset", "faster", "-crf", "16", "-profile:v", "high",
            "-x264-params", "aq-mode=3"],
    "nvenc": ["-c:v", "hevc_nvenc", "-preset", "p7", "-tune", "hq", "-rc", "vbr", "-cq", "17",
              "-b:v", "0", "-profile:v", "main", "-tag:v", "hvc1"],
}


def ffmpeg_salida(salida: Path, w: int, h: int, fps: int, master: Path, desde: float, segundos: float,
                  codificador: str) -> list[str]:
    final = salida.suffix.lower() == ".mov"
    audio = ["-c:a", "pcm_s24le"] if final else ["-c:a", "aac", "-b:a", "320k"]
    return ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
            "-ss", f"{desde:.3f}", "-t", f"{segundos:.3f}", "-i", str(master),
            "-map", "0:v", "-map", "1:a",
            *CODIFICADORES[codificador], "-pix_fmt", "yuv420p",
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
    ap.add_argument("--codificador", choices=sorted(CODIFICADORES), default="cpu")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()

    # dict(): un .npz abierto vuelve a leer el arreglo entero del zip en cada r["..."], y
    # aca se piden ocho por cuadro (22 MB por cuadro en un set de 89 min)
    r = dict(np.load(RASGOS / f"{a.nombre}_rasgos.npz"))
    caps = json.loads((RASGOS / f"{a.nombre}_capitulos.json").read_text(encoding="utf-8"))["capitulos"]
    fps = int(r["fps"])
    n_total = len(r["cuerpo"])
    i0 = int(a.desde * fps)
    # round: 186.233 s * 30 da 5586.99..., y con int() el ultimo tramo perdia su ultimo cuadro
    i1 = n_total if a.segundos is None else min(n_total, i0 + round(a.segundos * fps))
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
    poner(prog, "uTexto", 0)
    poner(prog, "uRes", (w, h))
    cam = camara(r, fps) if prog.get("uAltura", None) is not None else None
    carteles = {k: texto_del_tema(w, h, k + 1, len(caps), c["artista"], c["titulo"]) for k, c in enumerate(caps)}
    inicios = [c["t"] for c in caps]
    if a.mostrar_titulo:
        k_actual = int(np.searchsorted(inicios, a.desde, side="right") - 1)
        inicios[k_actual] = a.desde - TITULO_DESDE_S + 1.0
    cartel_cargado = -1

    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(ffmpeg_salida(salida, w, h, fps, Path(a.master), i0 / fps, (i1 - i0) / fps,
                                          a.codificador), stdin=subprocess.PIPE)
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
        for nombre, valor in (
                ("uTime", t), ("uProgreso", i / n_total),
                ("uFondo", tuple(pal[0])), ("uCielo", tuple(pal[1])),
                ("uResplandor", tuple(pal[2])), ("uBrillo", tuple(pal[3])),
                ("uBombo", float(r["bombo"][i])), ("uBajo", float(r["bajo"][i])),
                ("uCuerpo", float(r["cuerpo"][i])), ("uAire", float(r["aire"][i])),
                ("uChispa", float(r["brillo"][i])), ("uNoche", float(1.0 - r["luz_cielo"][i])),
                ("uDeriva", tuple(float(v) for v in deriva)), ("uAngulo", float(angulo)),
                ("uTextoAlfa", alfa)):
            poner(prog, nombre, valor)
        if cam is not None:
            for nombre, valor in (("uAltura", float(cam["altura"][i])), ("uDistancia", float(cam["distancia"][i])),
                                  ("uImpacto", float(cam["impacto"][i])), ("uCieloAlto", tuple(cam["paleta"][i, 0])),
                                  ("uHorizonte", tuple(cam["paleta"][i, 1])), ("uAcento", tuple(cam["paleta"][i, 2])),
                                  ("uBiomaA", float(cam["tema_a"][i] % BIOMAS_VUELO)),
                                  ("uBiomaB", float(cam["tema_b"][i] % BIOMAS_VUELO)),
                                  ("uSemillaA", float(cam["tema_a"][i])), ("uSemillaB", float(cam["tema_b"][i])),
                                  ("uLocalA", float(cam["local_a"][i])), ("uLocalB", float(cam["local_b"][i])),
                                  ("uMezclaBioma", float(cam["mezcla"][i]))):
                poner(prog, nombre, valor)
        vao.render(moderngl.TRIANGLE_STRIP)
        try:
            proc.stdin.write(fbo.read(components=3))
        except OSError:
            # ffmpeg se cerro: que quede escrito con que codigo, para saber si fue un error
            # suyo, un crash o que alguien lo mato (2026-10-02 se cerro sin dejar nada)
            sys.exit(f"ffmpeg se cerro en el cuadro {i - i0} con codigo {proc.wait()}")
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
