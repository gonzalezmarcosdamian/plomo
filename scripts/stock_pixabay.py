# -*- coding: utf-8 -*-
"""Busca y baja clips reales de Pixabay para el video de una Session.

POR QUE
-------
"El video el concepto esta bueno pero podes usar imagenes reales? clips?" (el DJ, 2026-10-20,
sobre la fiesta dibujada de la Session 04), y de las cinco formas eligio la 2: clips de fiestas
reales de un banco gratis. Pexels pauso las claves nuevas de su API y Mixkit gratis llega a 720p
(el 1080p es pago, por Envato), asi que la fuente es Pixabay: 1080p para todos los videos, 4K para
muchos, y una licencia que permite editarlos dentro de un video propio sin atribucion (no se
venden sueltos, no se usan marcas reconocibles para vender, nada enganoso con la gente que sale).

QUE HACE
--------
    buscar   corre las busquedas y guarda lo que vuelve en postproduction/stock/candidatos.json
             (la API pide guardar las respuestas 24 h en vez de repetirlas), mas una hoja de
             miniaturas por busqueda para elegir mirando.
    bajar    baja los ids elegidos a postproduction/stock/pixabay/<id>.mp4 en la mejor
             resolucion hasta 4K, de a uno: la API no permite descargas masivas sistematicas.

La clave va en .env como PIXABAY_API_KEY.

USO
---
    python scripts/stock_pixabay.py buscar "beach party sunset" "festival crowd night" ...
    python scripts/stock_pixabay.py bajar 12345 67890 ...
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API = "https://pixabay.com/api/videos/"
DEST = RAIZ / "postproduction" / "stock"
CANDIDATOS = DEST / "candidatos.json"
MIN_ANCHO = 1920
PAUSA_S = 2.0          # 100 pedidos por minuto por clave, y nada de descargas masivas: de a uno y espaciado
POR_BUSQUEDA = 40
MINI = (240, 135)


def clave() -> str:
    k = os.getenv("PIXABAY_API_KEY")
    if not k:
        sys.exit("falta PIXABAY_API_KEY en .env")
    return k


def leer_candidatos() -> dict:
    return json.loads(CANDIDATOS.read_text(encoding="utf-8")) if CANDIDATOS.exists() else {}


def resumen(h: dict, busqueda: str) -> dict:
    v = h["videos"]
    mejor = next(t for t in ("large", "medium") if v.get(t, {}).get("url"))
    return {"id": h["id"], "busqueda": busqueda, "tags": h["tags"], "duracion": h["duration"],
            "pagina": h["pageURL"], "autor": h["user"], "vistas": h["views"],
            "mejor": {"url": v[mejor]["url"], "ancho": v[mejor]["width"], "alto": v[mejor]["height"]},
            "miniatura": v["tiny"].get("thumbnail") or v["small"].get("thumbnail")}


def hoja(cli: httpx.Client, items: list[dict], salida: Path) -> None:
    """Miniaturas en grilla con el id y la duracion encima, para elegir mirando."""
    cols = 6
    filas = (len(items) + cols - 1) // cols
    lienzo = Image.new("RGB", (cols * MINI[0], filas * (MINI[1] + 18)), "black")
    dib = ImageDraw.Draw(lienzo)
    for k, it in enumerate(items):
        x, y = (k % cols) * MINI[0], (k // cols) * (MINI[1] + 18)
        try:
            im = Image.open(io.BytesIO(cli.get(it["miniatura"]).content)).convert("RGB")
            lienzo.paste(im.resize(MINI), (x, y + 18))
        except (httpx.HTTPError, OSError):
            pass
        dib.text((x + 4, y + 3), f"{it['id']}  {it['duracion']}s  {it['mejor']['alto']}p", fill="white")
    lienzo.save(salida, quality=85)


def buscar(busquedas: list[str]) -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    cand = leer_candidatos()
    with httpx.Client(timeout=30) as cli:
        for q in busquedas:
            r = cli.get(API, params={"key": clave(), "q": q, "video_type": "film", "min_width": MIN_ANCHO,
                                     "per_page": POR_BUSQUEDA, "safesearch": "true"})
            r.raise_for_status()
            items = [resumen(h, q) for h in r.json()["hits"]]
            for it in items:
                cand.setdefault(str(it["id"]), it)
            hoja(cli, items, DEST / f"hoja_{q.replace(' ', '_')}.jpg")
            print(f"{q!r}: {len(items)} clips")
            time.sleep(PAUSA_S)
    CANDIDATOS.write_text(json.dumps(cand, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(cand)} candidatos -> {CANDIDATOS}")


def bajar(ids: list[str]) -> None:
    cand = leer_candidatos()
    carpeta = DEST / "pixabay"
    carpeta.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120, follow_redirects=True) as cli:
        for i in ids:
            it = cand.get(str(i))
            if not it:
                print(f"{i}: no esta en candidatos.json, buscarlo primero")
                continue
            destino = carpeta / f"{i}.mp4"
            if destino.exists():
                print(f"{i}: ya estaba")
                continue
            with cli.stream("GET", it["mejor"]["url"]) as r:
                r.raise_for_status()
                with open(destino, "wb") as f:
                    for trozo in r.iter_bytes(1 << 20):
                        f.write(trozo)
            print(f"{i}: {destino.stat().st_size / 1e6:.0f} MB, {it['mejor']['alto']}p  {it['pagina']}")
            time.sleep(PAUSA_S)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["buscar", "bajar"])
    ap.add_argument("args", nargs="+")
    a = ap.parse_args()
    buscar(a.args) if a.accion == "buscar" else bajar(a.args)


if __name__ == "__main__":
    main()
