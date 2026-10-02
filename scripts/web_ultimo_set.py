# -*- coding: utf-8 -*-
"""Pone en la web el set recien publicado: miniatura, enlace y tracklist, desde su paquete.

POR QUE
-------
La seccion "Ultimo set" de web/plomo/index.html tiene que coincidir con lo que dice el
video en YouTube. Copiarla a mano es donde se cuela un horario corrido o un tema de menos;
el paquete (data/youtube/<nombre>.json) ya tiene el tracklist que se subio.

USO
---
    python scripts/web_ultimo_set.py data/youtube/session_01.json --id <video_id> --fecha 2026-10-02
    cd web/plomo && vercel deploy --prod --yes --scope gonzalezmarcosdamians-projects
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
WEB = RAIZ / "web" / "plomo"
TAMANO_IMAGEN = (1280, 720)
LINEA_TEMA = re.compile(r"^(\d+(?::\d\d){1,2}) (.+?)(?: \[(.+)\])?$")
SECCION = re.compile(r"(<h2>Último set</h2>\n).*?(\n  </section>)", re.S)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def temas(descripcion: str) -> list[tuple[str, str, str]]:
    """(minuto, artista – titulo, sello) de cada renglon del tracklist."""
    salida = []
    for renglon in descripcion.splitlines():
        m = LINEA_TEMA.match(renglon.strip())
        if m:
            salida.append((m.group(1), m.group(2).replace(" - ", " – ", 1), m.group(3) or ""))
    return salida


def seccion(p: dict, vid: str, imagen: str, fecha: date) -> str:
    serie = p["titulo"].split("·")[-1].strip()
    lis = "\n".join(f"      <li><span>{t}</span> {html.escape(tema)}" + (f" <em>{html.escape(s)}</em>" if s else "")
                    + "</li>" for t, tema, s in temas(p["descripcion"]))
    w, h = TAMANO_IMAGEN
    return (f'    <a class="set" href="https://youtu.be/{vid}">\n'
            f'      <img src="/img/{imagen}" alt="{html.escape(p["titulo"])}" width="{w}" height="{h}">\n'
            f'    </a>\n'
            f'    <p class="suave">{html.escape(serie)} · {fecha:%d.%m.%Y}</p>\n'
            f'    <ol class="tracklist">\n{lis}\n    </ol>')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paquete")
    ap.add_argument("--id", required=True, help="id del video en YouTube")
    ap.add_argument("--fecha", type=date.fromisoformat, default=date.today())
    a = ap.parse_args()

    p = json.loads((RAIZ / a.paquete).read_text(encoding="utf-8"))
    if not temas(p["descripcion"]):
        sys.exit("la descripcion del paquete no tiene tracklist")
    imagen = f"{p['nombre'].replace('_', '-')}.jpg"
    Image.open(RAIZ / p["miniatura"]).convert("RGB").resize(TAMANO_IMAGEN, Image.LANCZOS).save(
        WEB / "img" / imagen, quality=88)

    indice = WEB / "index.html"
    texto = indice.read_text(encoding="utf-8")
    nuevo, n = SECCION.subn(lambda m: m.group(1) + seccion(p, a.id, imagen, a.fecha) + m.group(2), texto)
    if n != 1:
        sys.exit("no encontre la seccion 'Último set' en index.html")
    indice.write_text(nuevo, encoding="utf-8")
    print(f"web: {p['titulo']} -> https://youtu.be/{a.id}, {len(temas(p['descripcion']))} temas, img/{imagen}")


if __name__ == "__main__":
    main()
