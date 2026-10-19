# -*- coding: utf-8 -*-
"""Las historias de Instagram de una Session: portada y tracklist, 1080x1920, listas para subir.

POR QUE
-------
"Haceme la historia para compartir" (el DJ, 2026-10-19, con la Session 03 recien publicada).
El fondo sale de la animacion misma, no de una foto aparte: se renderiza un cuadro en 4K del
look del video y se recorta una franja vertical centrada en lo mas brillante del cielo (el
cohete en ascenso, la luna en marea). El texto es el de la miniatura: Bahnschrift condensada,
crema y naranja. La portada deja libre el tercio de abajo para el sticker de enlace, que se pone
en Instagram: una imagen con un sticker dibujado no lleva a ningun lado.

Los textos van en la voz del DJ y cortos (feedback_voz_del_dj): nada de explicar la tecnica.

USO
---
    python scripts/historia_session.py --paquete data/youtube/session_03.json --mix postproduction/mixes/153_mix.wav
        --shader ascenso --t 4944.8
    -> C:/Users/gonza/Pictures/plomo_historia_session_03_portada.png  y  ..._tracklist.png
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
FUENTE = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
CREMA, NARANJA, SUAVE = (243, 235, 221), (232, 150, 74), (201, 193, 180)
ANCHO, ALTO = 1080, 1920
MARGEN = 88
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def fuente(tam: int, variacion: str) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FUENTE), tam)
    f.set_variation_by_name(variacion)
    return f


def fondo(nombre: str, mix: str, shader: str, t: float) -> Image.Image:
    """Un cuadro en 4K del look del video, recortado en vertical alrededor de lo mas brillante."""
    with tempfile.TemporaryDirectory() as tmp:
        clip, png = Path(tmp) / "c.mp4", Path(tmp) / "c.png"
        subprocess.run([sys.executable, str(RAIZ / "scripts" / "video_animar.py"), "--nombre", nombre, "--master", mix,
                        "--shader", shader, "--desde", f"{t:.2f}", "--segundos", "0.4", "--res", "3840x2160",
                        "--supermuestreo", "1.5", "--salida", str(clip)], check=True, capture_output=True, cwd=RAIZ)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-frames:v", "1", str(png)], check=True)
        cuadro = Image.open(png).convert("RGB")
    w, h = cuadro.size
    cielo = np.asarray(cuadro.convert("L"), dtype=np.float32)[: int(h * 0.7)]
    cx = int(np.unravel_index(np.argmax(cielo), cielo.shape)[1])
    ancho = round(h * ANCHO / ALTO)
    # lo brillante al 70% del ancho: centrado quedaba detras del "03" de la portada
    x0 = min(max(cx - int(ancho * 0.70), 0), w - ancho)
    return cuadro.crop((x0, 0, x0 + ancho, h)).resize((ANCHO, ALTO), Image.LANCZOS)


def con_sombra(img: Image.Image, dibujar) -> Image.Image:
    """Texto con una sombra suave abajo, para que se lea sobre el agua y el cielo."""
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dibujar(ImageDraw.Draw(capa), (0, 0, 0, 150), (3, 4))
    sombra = capa.filter(ImageFilter.GaussianBlur(10))
    letras = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dibujar(ImageDraw.Draw(letras), None, (0, 0))
    return Image.alpha_composite(Image.alpha_composite(img.convert("RGBA"), sombra), letras)


def portada(base: Image.Image, numero: int) -> Image.Image:
    grande, chica, linea = fuente(210, "Bold Condensed"), fuente(56, "SemiBold Condensed"), fuente(50, "SemiBold")

    def dibujar(d: ImageDraw.ImageDraw, sombra, corrido) -> None:
        dx, dy = corrido
        col = (lambda c: sombra or c)
        d.text((MARGEN + dx, 280 + dy), "SESSION", font=grande, fill=col(CREMA))
        d.text((MARGEN + dx, 470 + dy), f"{numero:02d}", font=grande, fill=col(NARANJA))
        d.text((MARGEN + 6 + dx, 700 + dy), "MARCOS DAMIAN", font=chica, fill=col(CREMA))
        d.text((ANCHO // 2 + dx, 1290 + dy), "Ya está en YouTube", font=linea, fill=col(CREMA), anchor="mm")

    return con_sombra(base, dibujar).convert("RGB")


def tracklist(base: Image.Image, numero: int, descripcion: str) -> Image.Image:
    oscuro = Image.blend(base, Image.new("RGB", base.size, (8, 11, 15)), 0.78)
    temas = []
    for renglon in descripcion.splitlines():
        m = re.match(r"^\d+(?::\d\d){1,2} (.+?) - (.+?)(?: \[.+\])?$", renglon.strip())
        if m:
            titulo = re.sub(r"\s*\((Original|Extended)(?: Mix)?\)", "", m.group(2))
            temas.append((m.group(1), titulo.replace(" Extended Remix", " Remix")))
    titulo_f, sub_f = fuente(118, "Bold Condensed"), fuente(40, "Regular")
    num_f = fuente(38, "SemiBold Condensed")
    alto_renglon = min(64, (1500 - 520) // max(len(temas), 1))

    def dibujar(d: ImageDraw.ImageDraw, sombra, corrido) -> None:
        dx, dy = corrido
        col = (lambda c: sombra or c)
        d.text((MARGEN + dx, 270 + dy), "SESSION", font=titulo_f, fill=col(CREMA))
        d.text((MARGEN + 400 + dx, 270 + dy), f"{numero:02d}", font=titulo_f, fill=col(NARANJA))
        d.text((MARGEN + dx, 420 + dy), f"Los {len(temas)} temas, en orden", font=sub_f, fill=col(SUAVE))
        y = 520
        for k, (artista, titulo) in enumerate(temas, 1):
            d.text((MARGEN + dx, y + dy), f"{k:02d}", font=num_f, fill=col(NARANJA))
            # un renglon que no entra se achica entero, artista y titulo juntos, hasta que entre
            tam = 38
            while tam > 26 and (d.textlength(artista + "  ", font=fuente(tam, "SemiBold Condensed"))
                                + d.textlength(titulo, font=fuente(tam, "Light Condensed"))) > ANCHO - 2 * MARGEN - 70:
                tam -= 1
            fa, ft = fuente(tam, "SemiBold Condensed"), fuente(tam, "Light Condensed")
            d.text((MARGEN + 70 + dx, y + dy + (38 - tam)), artista, font=fa, fill=col(CREMA))
            ancho_art = d.textlength(artista + "  ", font=fa)
            d.text((MARGEN + 70 + ancho_art + dx, y + dy + (38 - tam)), titulo, font=ft, fill=col(SUAVE))
            y += alto_renglon

    return con_sombra(oscuro, dibujar).convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paquete", required=True)
    ap.add_argument("--mix", required=True)
    ap.add_argument("--shader", required=True)
    ap.add_argument("--t", type=float, required=True, help="el segundo del video que va de fondo")
    ap.add_argument("--salida", default=str(Path.home() / "Pictures"))
    a = ap.parse_args()
    p = json.loads((RAIZ / a.paquete).read_text(encoding="utf-8"))
    numero = int(p["nombre"].split("_")[-1])
    base = fondo(p["nombre"], a.mix, a.shader, a.t)
    destino = Path(a.salida)
    destino.mkdir(parents=True, exist_ok=True)
    for cual, img in (("portada", portada(base, numero)), ("tracklist", tracklist(base, numero, p["descripcion"]))):
        archivo = destino / f"plomo_historia_{p['nombre']}_{cual}.png"
        img.save(archivo)
        print(f"-> {archivo}")


if __name__ == "__main__":
    main()
