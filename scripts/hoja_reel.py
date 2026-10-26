# -*- coding: utf-8 -*-
"""La hoja de recorrido del Reel en doble exposicion (scripts/reel_doble.py), antes del render.

POR QUE
-------
"Para proximas hace hoja de recorrido y asi sabemos como va" (el DJ, 2026-10-22). La idea del Reel es
nueva, asi que la hoja va antes del render: el audio elegido, los cortes, el pulso y los destellos, los
tramos de su toma y los paisajes, y cuadros reales ya compuestos a 1080x1920 al lado de su toma tal cual.

USO
---
    python scripts/hoja_reel.py --cuadros 1.0 8.15 13.5 27 --carpeta <dir de cuadros>
        [--salida C:/Users/gonza/Pictures/plomo_reel_session04_recorrido.jpg]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reel_doble as rd  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ANCHO = 2600
FONDO = (21, 18, 16)
CREMA = (243, 235, 221)
GRIS = (165, 155, 142)
NARANJA = (240, 140, 50)
COLOR_MODO = {"paisaje": (120, 95, 70), "fusion": (190, 130, 60), "drop": (240, 140, 50)}
SALIDA = Path(r"C:\Users\gonza\Pictures\plomo_reel_session04_recorrido.jpg")
FASE = {118: "B", 120: "B", 125: "C", 123: "C", 126: "C", 127: "C", 136: "E"}
NOMBRE_PAISAJE = {118: "niebla dorada y cerro", 120: "nubes doradas", 125: "el sol sobre los Alpes",
                  123: "mar de nubes naranja", 126: "el sol entre cumbres", 127: "Alpes y cielo naranja",
                  136: "arrebol sobre la nieve"}


def fuente(tam: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(rd.FUENTE), tam)


def coma(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def minuto(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}".replace(".", ",")


def segundo_de_toma(r: rd.Reel, tau: float) -> float:
    p = r.plano(tau)
    return p["toma"] + (r.inicio + tau - (r.drop + p["desde"] * r.beat)) / p["lento"]


def toma_real(r: rd.Reel, tau: float, alto: int) -> Image.Image:
    """El recorte 9:16 de su toma en ese instante, sin tocar: para comparar lado a lado."""
    p = r.plano(tau)
    toma = rd.RAIZ / r.plan["toma"]
    x0 = rd.centrar(toma, p["toma"], (p["hasta"] - p["desde"]) * r.beat / p["lento"])
    f = rd.leer_toma(toma, segundo_de_toma(r, tau), 0.05, x0, 2)[0]
    return Image.fromarray(f).resize((round(alto * 9 / 16), alto), Image.LANCZOS)


def onda(r: rd.Reel, ancho: int, alto: int) -> np.ndarray:
    """El nivel de la mezcla en el tramo del Reel, una columna por pixel."""
    ruta = rd.RAIZ / r.plan["mezcla"]
    sr = sf.info(str(ruta)).samplerate
    x, _ = sf.read(str(ruta), start=int(r.inicio * sr), stop=int((r.inicio + r.duracion) * sr), dtype="float32")
    m = x.mean(1)
    cols = np.array_split(m, ancho)
    rms = np.array([np.sqrt((c ** 2).mean()) for c in cols])
    db = 20 * np.log10(rms + 1e-6)
    return np.clip((db + 42) / 36, 0.02, 1) * alto


def banda_audio(d: ImageDraw.ImageDraw, r: rd.Reel, x0: int, y0: int, ancho: int) -> int:
    alto = 170
    px = lambda t: x0 + int(t / r.duracion * ancho)
    h = onda(r, ancho, alto)
    for i, v in enumerate(h):
        d.line([(x0 + i, y0 + alto - v), (x0 + i, y0 + alto)], fill=(95, 82, 70))
    t_drop = r.drop - r.inicio
    d.line([(px(t_drop), y0 - 10), (px(t_drop), y0 + alto + 10)], fill=NARANJA, width=4)
    d.text((px(t_drop) + 30, y0 - 6), f"DROP  {minuto(r.drop)} de la Session", font=fuente(30), fill=NARANJA)
    # pulso: cada bombo medido despues del drop
    for b in r.bombos:
        if b - r.inicio < r.duracion:
            d.line([(px(b - r.inicio), y0 + alto + 14), (px(b - r.inicio), y0 + alto + 26)], fill=CREMA, width=2)
    # destellos: el golpe del drop y el uno de cada frase de cuatro compases
    for k in (0, 1, 2):
        t = t_drop + k * 16 * r.beat
        xx, yy, rr = px(t), y0 + 18, (16 if k == 0 else 10)
        d.polygon([(xx, yy - rr), (xx + rr // 3, yy - rr // 3), (xx + rr, yy), (xx + rr // 3, yy + rr // 3),
                   (xx, yy + rr), (xx - rr // 3, yy + rr // 3), (xx - rr, yy), (xx - rr // 3, yy - rr // 3)],
                  fill=(255, 225, 160))
    # los planos: un bloque por corte, del color de su modo
    yb = y0 + alto + 36
    for p in r.plan["planos"]:
        a = px(r.drop + p["desde"] * r.beat - r.inicio)
        z = min(px(r.drop + p["hasta"] * r.beat - r.inicio), x0 + ancho)
        d.rectangle([a + 1, yb, z - 1, yb + 58], fill=COLOR_MODO[p["modo"]])
        if z - a > 60:
            d.text((a + 8, yb + 4), f"{p['paisaje']}", font=fuente(24), fill=FONDO)
            d.text((a + 8, yb + 30), f"{p['toma']:.0f} s" + (" x2" if p["lento"] == 2 else ""), font=fuente(20),
                   fill=FONDO)
    for s in range(0, int(r.duracion) + 1, 5):
        d.text((px(s) - 8, yb + 66), f"{s}", font=fuente(22), fill=GRIS)
    yl = yb + 100
    d.text((x0, yl), "armado: 4 compases, 0:00 a 0:07,8 (69:05,7 a 69:13,5)   ·   drop: 11 compases, 0:07,8 a 0:29,4 "
           "(69:13,5 a 69:35,1)   ·   estado de los dos: en armado", font=fuente(26), fill=CREMA)
    leyenda = [("paisaje", "en transparencia"), ("fusion", "más presente"), ("drop", "la silueta llena")]
    xl = x0
    for modo, txt in leyenda:
        d.rectangle([xl, yl + 44, xl + 30, yl + 66], fill=COLOR_MODO[modo])
        d.text((xl + 40, yl + 40), txt, font=fuente(24), fill=GRIS)
        xl += 300
    d.text((xl + 20, yl + 40), "rayitas: el pulso en cada bombo   ·   estrellas: los destellos   ·   en cada bloque, "
           "el paisaje y el segundo de tu toma", font=fuente(24), fill=GRIS)
    return yl + 90


def pegar_cuadros(lienzo: Image.Image, d: ImageDraw.ImageDraw, r: rd.Reel, cuadros: list[tuple[float, Path, str]],
                  y0: int) -> int:
    alto, alto_real = 800, 280
    x = 60
    for tau, ruta, leyenda in cuadros:
        img = Image.open(ruta).convert("RGB").resize((450, alto), Image.LANCZOS)
        lienzo.paste(img, (x, y0))
        real = toma_real(r, tau, alto_real)
        lienzo.paste(real, (x + 462, y0 + alto - alto_real))
        d.text((x + 462, y0 + alto - alto_real - 34), "tu toma tal cual", font=fuente(22), fill=GRIS)
        d.text((x, y0 + alto + 12), f"{minuto(tau)} del Reel", font=fuente(30), fill=NARANJA)
        for k, renglon in enumerate(leyenda.split("\n")):
            d.text((x, y0 + alto + 52 + k * 32), renglon, font=fuente(26), fill=CREMA)
        x += 630
    return y0 + alto + 130


def tira_tomas(lienzo: Image.Image, d: ImageDraw.ImageDraw, r: rd.Reel, y0: int) -> int:
    d.text((60, y0), "Tus tomas (IMG_2209): un tramo por corte. x2 = cámara lenta con los cuadros reales de 60 por "
           "segundo. El puño arriba del drop es 369,9 a 373,9 s.", font=fuente(28), fill=CREMA)
    alto = 300
    x = 60
    for p in r.plan["planos"]:
        tau = r.drop + (p["desde"] + p["hasta"]) / 2 * r.beat - r.inicio
        img = toma_real(r, tau, alto)
        lienzo.paste(img, (x, y0 + 44))
        d.text((x, y0 + 44 + alto + 6), f"{coma(p['toma'])} s" + (" x2" if p["lento"] == 2 else ""), font=fuente(22),
               fill=COLOR_MODO[p["modo"]] if p["modo"] != "paisaje" else GRIS)
        x += 192
    return y0 + 44 + alto + 50


def tira_paisajes(lienzo: Image.Image, d: ImageDraw.ImageDraw, r: rd.Reel, y0: int) -> int:
    d.text((60, y0), "Los paisajes: solo planos aprobados de la Session 04, ya revisados. La luz va de la dorada [B] a "
           "la naranja [C] y al arrebol [E], sin volver.", font=fuente(28), fill=CREMA)
    vistos, x, alto = [], 60, 300
    for p in r.plan["planos"]:
        n = p["paisaje"]
        if n in vistos:
            continue
        vistos.append(n)
        cu = rd.leer_paisaje(n, p["paisaje_desde"], 0.05, p["paisaje_x"], p.get("paisaje_y", 0.0),
                             p.get("paisaje_alto", rd.H))[0].astype(np.float32) / 65535
        img = Image.fromarray((np.clip(rd.grado_marca(cu), 0, 1) * 255).astype(np.uint8))
        lienzo.paste(img.resize((round(alto * 9 / 16), alto), Image.LANCZOS), (x, y0 + 44))
        d.text((x, y0 + 44 + alto + 6), f"{n} [{FASE.get(n, '?')}]", font=fuente(24), fill=NARANJA)
        d.text((x, y0 + 44 + alto + 36), NOMBRE_PAISAJE.get(n, ""), font=fuente(20), fill=GRIS)
        x += 230
    xt = x + 40
    notas = ["Cómo está hecha la doble exposición:",
             "vos y el paisaje sumados como dos exposiciones de una",
             "misma foto. En lo oscuro de la campera aparece el",
             "paisaje; en lo blanco quedás vos. La cara, la gorra",
             "y las manos van opacas y sin tocar; el borde se funde",
             "sin aro ni gris de cortina. La consola es la toma real.",
             "",
             "Texto: solo el nombre del tema, chico, arriba a la",
             "izquierda (abajo lo tapa Instagram), los primeros 7 s."]
    for k, renglon in enumerate(notas):
        d.text((xt, y0 + 50 + k * 34), renglon, font=fuente(26), fill=CREMA if k == 0 else GRIS)
    return y0 + 44 + alto + 80


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cuadros", type=float, nargs="+", required=True)
    ap.add_argument("--leyendas", nargs="+", required=True, help="una por cuadro; \\n separa renglones")
    ap.add_argument("--carpeta", required=True, help="donde estan (o van) los cuadros compuestos")
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args()
    if len(a.leyendas) != len(a.cuadros):
        sys.exit("hace falta una leyenda por cuadro")
    r = rd.cargar()
    carpeta = Path(a.carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ps = rd.particulas()
    cuadros = []
    for tau, ley in zip(a.cuadros, a.leyendas):
        ruta = carpeta / f"cuadro_{tau:05.2f}.png"
        if not ruta.exists():
            cv2.imwrite(str(ruta), cv2.cvtColor(rd.cuadro(r, tau, ps), cv2.COLOR_RGB2BGR))
        cuadros.append((tau, ruta, ley.replace("\\n", "\n")))

    lienzo = Image.new("RGB", (ANCHO, 3000), FONDO)
    d = ImageDraw.Draw(lienzo)
    d.text((60, 40), "Reel · Session 04 · doble exposición", font=fuente(64), fill=CREMA)
    d.text((60, 122), f"Hoja de recorrido · 26/10/2026 · 9:16, {coma(r.duracion)} s · estado: EN ARMADO, espera tu OK antes del "
           "render entero", font=fuente(32), fill=NARANJA)
    d.text((60, 176), f"Audio: la mezcla del 157, {minuto(r.inicio)} a {minuto(r.inicio + r.duracion)} de la Session. "
           "Stamina (Simon Vuarambon): 4 compases del break y 11 del drop, el más fuerte del set (sube 13 dB; "
           "el de Fog Machine, 7).", font=fuente(28), fill=CREMA)
    d.text((60, 214), "Cortes en el golpe: cada compás, después cada dos beats y cada beat antes del drop; en el drop, "
           "cada 2 compases. Pulso: un zoom de 1,4 % en cada bombo.", font=fuente(28), fill=GRIS)
    d.text((60, 252), "Destellos: un trazo de luz por el sol en el golpe del drop y más suave en el uno de cada frase; "
           "polvo de luz desde el drop.", font=fuente(28), fill=GRIS)
    y = banda_audio(d, r, 60, 340, ANCHO - 120)
    y = pegar_cuadros(lienzo, d, r, cuadros, y + 30)
    y = tira_tomas(lienzo, d, r, y + 10)
    y = tira_paisajes(lienzo, d, r, y + 10)
    lienzo = lienzo.crop((0, 0, ANCHO, y + 20))
    salida = Path(a.salida)
    lienzo.save(salida, quality=92)
    print(f"-> {salida} ({lienzo.size[0]}x{lienzo.size[1]})", flush=True)


if __name__ == "__main__":
    main()
