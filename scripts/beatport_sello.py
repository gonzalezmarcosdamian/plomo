# -*- coding: utf-8 -*-
"""Lee el catalogo de un SELLO en Beatport, con BPM y key Camelot oficiales.

POR QUE
-------
Muzpa busca por tema y por artista, nunca por sello. Esta escrito en
`muzpa_new_releases.py`: pasarle sellos como terminos devuelve falsos positivos
--buscar "Early Morning" trae temas con esas palabras en el titulo-- y para
cubrir un sello hay que escanear a sus artistas uno por uno, cosa que no se
puede hacer si no sabes quienes son.

Medido el 2026-09-28, los sellos que definen el sonido del DJ estaban flacos y
nadie sabia por que: Selador 6 temas, Narratives 1, Natura Sonoris 2, Replug 14
con CERO de 2025 en adelante, All Day I Dream 53 pero solo el 15% reciente. No
era criterio: era que el radar no los podia ver.

Beatport si publica el catalogo por sello, y trae mas que Muzpa: fecha exacta de
release, BPM y la key ya en Camelot. La pagina responde 403 a un fetch normal y
200 a curl con User-Agent de browser; los datos estan en el JSON que Next.js
deja embebido en `__NEXT_DATA__`.

ESTO NO DESCARGA NADA. Dice QUE existe y que falta; bajarlo sigue siendo trabajo
de `muzpa_scan.py` y `muzpa_download.py`.

USO
---
    python scripts/beatport_sello.py --buscar selador
    python scripts/beatport_sello.py --sello selador:30570 --desde 2025-01-01
    python scripts/beatport_sello.py --sellos rules/sellos_radar.txt
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
NEXT = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)


def traer(url: str) -> dict | None:
    """El JSON embebido de una pagina de Beatport, vía curl.

    Con `requests` y el mismo User-Agent igual devuelve 403; con curl, 200.
    """
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        destino = Path(tmp.name)
    try:
        subprocess.run(["curl", "-s", "-H", f"User-Agent: {UA}", url, "-o", str(destino)],
                       check=True, timeout=60)
        html = destino.read_text(encoding="utf-8", errors="replace")
    finally:
        destino.unlink(missing_ok=True)
    m = NEXT.search(html)
    return json.loads(m.group(1)) if m else None


def _hojas(o, prof: int = 0):
    """Cada lista `results` del JSON, que es donde Next mete los datos."""
    if prof > 10:
        return
    if isinstance(o, dict):
        r = o.get("results")
        if isinstance(r, list) and r and isinstance(r[0], dict):
            yield r
        for v in o.values():
            yield from _hojas(v, prof + 1)
    elif isinstance(o, list):
        for v in o[:10]:
            yield from _hojas(v, prof + 1)


def temas_de(slug: str, sello_id: str, paginas: int = 3) -> list[dict]:
    salida: list[dict] = []
    vistos: set = set()
    for pag in range(1, paginas + 1):
        d = traer(f"https://www.beatport.com/label/{slug}/{sello_id}/tracks"
                  f"?page={pag}&per_page=50")
        if not d:
            break
        filas = next((r for r in _hojas(d) if "mix_name" in r[0]), [])
        nuevos = 0
        for t in filas:
            if t.get("id") in vistos:
                continue
            vistos.add(t.get("id"))
            nuevos += 1
            k = t.get("key") or {}
            salida.append({
                "artista": ", ".join(a.get("name", "") for a in t.get("artists", [])),
                "titulo": t.get("name", ""),
                "version": t.get("mix_name") or "",
                "sello": ((t.get("release") or {}).get("label") or {}).get("name", slug),
                "fecha": str(t.get("new_release_date") or t.get("publish_date") or "")[:10],
                "bpm": t.get("bpm"),
                "camelot": f"{k.get('camelot_number', '')}{k.get('camelot_letter', '')}",
                "largo_seg": round((t.get("length_ms") or 0) / 1000) or None,
            })
        if nuevos == 0:
            break
    return salida


def buscar_sello(nombre: str) -> list[tuple[str, str, str]]:
    """Resuelve nombre -> (nombre, id, slug). Los sellos viven en un lugar fijo.

    La busqueda de Beatport devuelve `tracks / artists / charts / labels /
    releases` bajo `dehydratedState.queries[0].state.data`, y cada sello trae
    `label_name` y `label_id` pero NO trae slug: la URL lo acepta igual con el
    nombre pasado a guiones, porque lo que identifica es el id.
    """
    d = traer("https://www.beatport.com/search?q=" + nombre.replace(" ", "+"))
    if not d:
        return []
    try:
        data = d["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]
        filas = (data.get("labels") or {}).get("data") or []
    except (KeyError, IndexError, TypeError):
        return []
    fuera = []
    for x in filas[:8]:
        nom = x.get("label_name") or x.get("name") or ""
        ident = x.get("label_id") or x.get("id")
        if nom and ident:
            slug = x.get("label_slug") or re.sub(r"[^a-z0-9]+", "-", nom.lower()).strip("-")
            fuera.append((nom, str(ident), slug))
    return fuera


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--buscar", help="resolver el ID de un sello por nombre")
    ap.add_argument("--sello", action="append", default=[], help="slug:id, repetible")
    ap.add_argument("--sellos", type=Path, help="archivo con un slug:id por linea")
    ap.add_argument("--desde", default="2025-01-01")
    ap.add_argument("--bpm", nargs=2, type=float, default=[117.0, 128.0])
    ap.add_argument("--paginas", type=int, default=3)
    ap.add_argument("--salida", type=Path, default=RAIZ / "data/beatport_sellos.json")
    args = ap.parse_args()

    if args.buscar:
        for nom, ident, slug in buscar_sello(args.buscar):
            print(f"  {nom:38s} {slug}:{ident}")
        return

    objetivos = list(args.sello)
    if args.sellos:
        objetivos += [x.strip() for x in args.sellos.read_text(encoding="utf-8").splitlines()
                      if x.strip() and not x.startswith("#")]
    if not objetivos:
        ap.error("pasa --sello slug:id o --sellos archivo")

    from plomo.matching import clave
    POOL = json.loads((RAIZ / "data/pool.json").read_text(encoding="utf-8"))
    tengo = {clave(t["artist"], t["title"]) for t in POOL}
    nucleos = {(t["title"].split("(")[0].strip().lower(),
                t["artist"].split(",")[0].strip().lower()) for t in POOL}
    vetos = {v.get("title", "").lower() for v in json.loads(
        (RAIZ / "data/energia_percibida.json").read_text(encoding="utf-8")).values()
        if v.get("veto")}

    faltan: list[dict] = []
    for obj in objetivos:
        slug, _, sid = obj.partition(":")
        if not sid:
            print(f"{obj}: falta el id (usa --buscar)")
            continue
        temas = temas_de(slug, sid, args.paginas)
        recientes = [t for t in temas if t["fecha"] >= args.desde]
        nuevos = 0
        for t in recientes:
            if t["bpm"] and not (args.bpm[0] <= t["bpm"] <= args.bpm[1]):
                continue
            if t["titulo"].lower() in vetos:
                continue
            full = f"{t['titulo']} ({t['version']})" if t["version"] else t["titulo"]
            nuc = (t["titulo"].split("(")[0].strip().lower(),
                   t["artista"].split(",")[0].strip().lower())
            if clave(t["artista"], full) in tengo or nuc in nucleos:
                continue
            faltan.append(t)
            nuevos += 1
        print(f"{slug:26s} {len(temas):4d} en catalogo | {len(recientes):3d} desde "
              f"{args.desde} | {nuevos:3d} que NO tenes")

    args.salida.write_text(json.dumps(
        {"generado": date.today().isoformat(), "desde": args.desde,
         "sellos": objetivos, "faltan": faltan}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    batch = RAIZ / f"data/batch_sellos_{date.today().isoformat()}.txt"
    with batch.open("w", encoding="utf-8") as f:
        for t in faltan:
            extra = ""
            if t["version"] and t["version"].lower() != "original mix":
                extra = f" ({t['version']})"
            f.write(f"{t['artista']} - {t['titulo']}{extra}\n")
    print(f"\n{len(faltan)} temas que no tenes")
    # relative_to() explota si --salida vino relativa: no es un error del
    # scraper y no tiene que tirar la corrida despues de escribir el archivo.
    try:
        print(f"  -> {args.salida.resolve().relative_to(RAIZ)}")
    except ValueError:
        print(f"  -> {args.salida}")
    print(f"  -> {batch.relative_to(RAIZ)}  (para muzpa_scan.py)")


if __name__ == "__main__":
    main()
