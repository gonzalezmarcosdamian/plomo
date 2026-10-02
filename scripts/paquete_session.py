# -*- coding: utf-8 -*-
"""Arma el paquete de publicacion de una Session desde el plan del mix, y su miniatura.

POR QUE
-------
"Inventemos un session 1, session 2" (el DJ, 2026-10-02). Cada Session es un mix
armado con `mezclar.py`; su tracklist sale del mismo plan que lo mezclo, asi que
los capitulos caen donde de verdad cambia el tema (el cambio de bajos).

La descripcion es la que dicto el DJ: el tracklist y "Gracias por escuchar."
Nada mas — ni presentacion, ni explicar la imagen, ni "compralo" (ver
`feedback_voz_del_dj`).

USO
---
    python scripts/paquete_session.py --mix postproduction/mixes/148_mix.json --numero 1
        --artistas "Hernan Cattaneo, Maze 28, Paul Thomas, Marsh" --cuadro <png de la animacion>
    -> data/youtube/session_01.json  y  data/youtube/session_01_miniatura.jpg
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FUENTE = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
CREMA, NARANJA = (243, 235, 221), (232, 150, 74)
MAX_TAGS_CHARS = 480


def _clave(texto: str) -> str:
    return re.sub(r"[^a-z0-9]", "", texto.lower().split(" (")[0])


def sellos() -> dict[tuple[str, str], str]:
    pool = json.loads((RAIZ / "data" / "pool.json").read_text(encoding="utf-8"))
    return {(_clave(t["artist"]), _clave(t["title"])): t.get("label") or "" for t in pool}


def mmss(s: float) -> str:
    s = int(round(s))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def miniatura(cuadro: Path, numero: int, salida: Path) -> None:
    img = Image.open(cuadro).convert("RGB").resize((1280, 720), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    grande = ImageFont.truetype(str(FUENTE), 150)
    grande.set_variation_by_name("Bold Condensed")
    chica = ImageFont.truetype(str(FUENTE), 46)
    chica.set_variation_by_name("SemiBold Condensed")
    d.text((70, 70), "SESSION", font=grande, fill=CREMA)
    d.text((70, 230), f"{numero:02d}", font=grande, fill=NARANJA)
    d.text((76, 400), "MARCOS DAMIAN", font=chica, fill=CREMA)
    img.save(salida, quality=92)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mix", required=True, help="el JSON que escribe mezclar.py")
    ap.add_argument("--numero", type=int, required=True)
    ap.add_argument("--artistas", required=True, help="los 3-4 nombres que van en el titulo (lo que se busca)")
    ap.add_argument("--video", help="el render final (por defecto postproduction/video/session_NN.mov)")
    ap.add_argument("--cuadro", help="un cuadro de la animacion para la miniatura")
    a = ap.parse_args()

    mix = json.loads(Path(a.mix).read_text(encoding="utf-8"))
    nombre = f"session_{a.numero:02d}"
    por_tema = sellos()
    lineas, artistas, labels = [], [], []
    for k, c in enumerate(mix["plan"]):
        artista, _, titulo = c["tema"].partition(" - ")
        sello = por_tema.get((_clave(artista), _clave(titulo)), "")
        t = 0.0 if k == 0 else c["cambio_in"]
        lineas.append(f"{mmss(t)} {artista} - {titulo}" + (f" [{sello}]" if sello else ""))
        artistas += [x.strip() for x in re.split(r",|&| x ", artista) if x.strip()]
        if sello:
            labels.append(sello)
    descripcion = "\n".join(lineas) + "\n\nGracias por escuchar."
    tags, largo = [], 0
    for tag in dict.fromkeys(["Marcos Damian", *artistas, *labels, "progressive house", "progressive house mix",
                              "dj mix", "melodic progressive", f"session {a.numero:02d}"]):
        if largo + len(tag) + 3 > MAX_TAGS_CHARS:
            break
        tags.append(tag)
        largo += len(tag) + 3
    titulo = f"{a.artistas} | Progressive House Mix · Session {a.numero:02d}"
    paquete = {"nombre": nombre, "titulo": titulo, "descripcion": descripcion, "tags": tags, "categoria": "10",
               "idioma": "es", "video": a.video or f"postproduction/video/{nombre}.mov",
               "miniatura": f"data/youtube/{nombre}_miniatura.jpg", "mix": a.mix, "set": mix["set"]}
    if len(titulo) > 100:
        sys.exit(f"el titulo tiene {len(titulo)} caracteres; YouTube corta en 100")
    salida = RAIZ / "data" / "youtube" / f"{nombre}.json"
    salida.write_text(json.dumps(paquete, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.cuadro:
        miniatura(Path(a.cuadro), a.numero, RAIZ / paquete["miniatura"])
    print(titulo, f"({len(titulo)} caracteres)")
    print(descripcion)
    print(f"{len(tags)} tags, {largo} caracteres\n-> {salida}")


if __name__ == "__main__":
    main()
