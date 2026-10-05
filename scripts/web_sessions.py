# -*- coding: utf-8 -*-
"""Pone en la web todas las Sessions publicadas: miniatura, enlace, fecha y tracklist.

POR QUE
-------
"En la web, deja todas las sessions" (el DJ, 2026-10-05). Antes la web mostraba solo el
ultimo set y cada Session nueva pisaba a la anterior. Ahora la seccion se arma entera
desde los paquetes (data/youtube/session_NN.json) que tienen video subido, la mas nueva
arriba, cada una con su tracklist desplegable. Solo entran las que YouTube dice que son
publicas: una programada no aparece hasta que sale. La fecha es la de publicacion en
YouTube, no la del dia en que se corre esto (la Session 02 habia quedado con la del lunes).

USO
---
    python scripts/web_sessions.py
    cd web/plomo && vercel deploy --prod --yes --scope gonzalezmarcosdamians-projects
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from plomo.youtube import cliente  # noqa: E402

WEB = RAIZ / "web" / "plomo"
PAQUETES = RAIZ / "data" / "youtube"
TAMANO_IMAGEN = (1280, 720)
HORA_LOCAL = timezone(timedelta(hours=-3))
LINEA_TEMA = re.compile(r"^(\d+(?::\d\d){1,2}) (.+?)(?: \[(.+)\])?$")
SECCION = re.compile(r"  <section[^>]*>\n    <h2>(?:Último set|Sessions)</h2>\n.*?\n  </section>", re.S)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def temas(descripcion: str) -> list[tuple[str, str, str]]:
    """(minuto, artista – titulo, sello) de cada renglon del tracklist."""
    salida = []
    for renglon in descripcion.splitlines():
        m = LINEA_TEMA.match(renglon.strip())
        if m:
            salida.append((m.group(1), m.group(2).replace(" - ", " – ", 1), m.group(3) or ""))
    return salida


def publicadas() -> list[dict]:
    """Las Sessions con video subido que YouTube tiene publicas, la mas nueva primero."""
    subidas = {}
    for paquete in sorted(PAQUETES.glob("session_[0-9][0-9].json")):
        p = json.loads(paquete.read_text(encoding="utf-8"))
        registro = PAQUETES / f"{p['nombre']}_publicado.json"
        if registro.exists():
            subidas[json.loads(registro.read_text(encoding="utf-8"))["id"]] = p
    if not subidas:
        return []
    videos = cliente().videos().list(part="status,snippet", id=",".join(subidas)).execute()["items"]
    salida = []
    for v in videos:
        if v["status"]["privacyStatus"] != "public":
            continue
        cuando = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00")).astimezone(HORA_LOCAL)
        salida.append({**subidas[v["id"]], "id": v["id"], "fecha": cuando})
    return sorted(salida, key=lambda s: s["nombre"], reverse=True)


def imagen(p: dict) -> str:
    nombre = f"{p['nombre'].replace('_', '-')}.jpg"
    Image.open(RAIZ / p["miniatura"]).convert("RGB").resize(TAMANO_IMAGEN, Image.LANCZOS).save(
        WEB / "img" / nombre, quality=88)
    return nombre


def articulo(p: dict, abierta: bool) -> str:
    serie = p["titulo"].split("·")[-1].strip()
    lista = temas(p["descripcion"])
    lis = "\n".join(f"          <li><span>{t}</span> {html.escape(tema)}"
                    + (f" <em>{html.escape(s)}</em>" if s else "") + "</li>" for t, tema, s in lista)
    w, h = TAMANO_IMAGEN
    return (f'    <article class="session">\n'
            f'      <a class="set" href="https://youtu.be/{p["id"]}">\n'
            f'        <img src="/img/{imagen(p)}" alt="{html.escape(p["titulo"])}" width="{w}" height="{h}">\n'
            f'      </a>\n'
            f'      <p class="suave">{html.escape(serie)} · {p["fecha"]:%d.%m.%Y}</p>\n'
            f'      <details{" open" if abierta else ""}>\n'
            f'        <summary>Tracklist · {len(lista)} temas</summary>\n'
            f'        <ol class="tracklist">\n{lis}\n        </ol>\n'
            f'      </details>\n'
            f'    </article>')


def main() -> None:
    sesiones = publicadas()
    if not sesiones:
        sys.exit("no hay ninguna Session publica")
    for s in sesiones:
        if not temas(s["descripcion"]):
            sys.exit(f"{s['nombre']}: la descripcion del paquete no tiene tracklist")
    cuerpo = "\n".join(articulo(s, k == 0) for k, s in enumerate(sesiones))
    seccion = f'  <section class="sessions">\n    <h2>Sessions</h2>\n{cuerpo}\n  </section>'

    indice = WEB / "index.html"
    texto = indice.read_text(encoding="utf-8")
    nuevo, n = SECCION.subn(lambda _: seccion, texto)
    if n != 1:
        sys.exit("no encontre la seccion de sets en index.html")
    indice.write_text(nuevo, encoding="utf-8")
    for s in sesiones:
        print(f"web: {s['nombre']} {s['fecha']:%d.%m.%Y} -> https://youtu.be/{s['id']}, {len(temas(s['descripcion']))} temas")


if __name__ == "__main__":
    main()
