# -*- coding: utf-8 -*-
"""Aplica la identidad del canal de YouTube desde data/youtube/canal.json.

POR QUE
-------
El nombre artistico es "Marcos Damian" (el DJ, 2026-09-28: "quiero que sea mi
nombre artistico, hace todo despues en base a eso"). Nombre, descripcion,
palabras clave, pais, banner y marca de agua salen de un archivo, igual que el
paquete de cada video: se cambia el JSON y se vuelve a correr.

OJO CON LA API
--------------
`channels.update` con `brandingSettings` REEMPLAZA el objeto entero: lo que no
se manda, se borra. Por eso se manda siempre todo junto, banner incluido.

El NOMBRE del canal tampoco se cambia por API, aunque la API acepte el campo sin
error: se mando "Marcos Damian" y se leyo de vuelta "Marcos Damian Gonzalez"
(2026-09-28). Nombre, foto de perfil y handle (@...) van a mano en Studio,
Personalizacion -> Perfil. El titulo se sigue mandando para que coincida cuando
YouTube lo acepte, y el script avisa si no coincide.

`watermarks.set` responde 204 sin cuerpo y httplib2 0.32 se cae al descomprimir
un cuerpo vacio ("range() arg 3 must not be zero"). El pedido ya se proceso; no
hay forma de leer la marca de agua por API, asi que se verifica en Studio.

USO
---
    python scripts/youtube_canal.py            # muestra lo que haria
    python scripts/youtube_canal.py --aplicar
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from googleapiclient.http import MediaFileUpload

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from plomo.youtube import cliente  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CONFIG = RAIZ / "data" / "youtube" / "canal.json"
# la marca de agua aparece los ultimos 15 s de cada video: al final molesta menos
MARCA_TIMING = {"type": "offsetFromEnd", "offsetMs": 15000, "durationMs": 15000}


def cambiar_trailer(yt, video_id: str, c: dict) -> None:
    """Cada Session nueva pasa a ser el destacado. brandingSettings se reemplaza entero al
    actualizarlo, asi que se manda de vuelta lo que YouTube tiene (con lo que el DJ haya
    tocado en Studio) cambiando solo el trailer."""
    actual = yt.channels().list(part="brandingSettings", mine=True).execute()["items"][0]
    branding = actual["brandingSettings"]
    antes = branding.get("channel", {}).get("unsubscribedTrailer")
    branding.setdefault("channel", {})["unsubscribedTrailer"] = video_id
    yt.channels().update(part="brandingSettings", body={"id": actual["id"], "brandingSettings": branding}).execute()
    leido = yt.channels().list(part="brandingSettings", mine=True).execute()["items"][0]["brandingSettings"]
    quedo = leido.get("channel", {}).get("unsubscribedTrailer")
    # la lectura inmediata suele devolver el valor viejo: YouTube tarda unos segundos en reflejarlo
    print(f"trailer: {antes} -> {quedo}" + ("" if quedo == video_id else
                                             f"  (todavia figura el viejo: releer en un minuto, pedido {video_id})"))
    CONFIG.write_text(json.dumps({**c, "trailer": video_id}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--pisar", action="store_true", help="reemplazar una descripcion escrita a mano en Studio")
    ap.add_argument("--trailer", metavar="ID", help="cambiar SOLO el video destacado, sin tocar nada mas")
    a = ap.parse_args()
    c = json.loads(CONFIG.read_text(encoding="utf-8"))
    yt = cliente()
    if a.trailer:
        return cambiar_trailer(yt, a.trailer, c)
    actual = yt.channels().list(part="snippet,brandingSettings", mine=True).execute()["items"][0]
    print(f"ahora:  {actual['snippet']['title']}  |  {actual['snippet'].get('description', '')!r}")
    print(f"queda:  {c['titulo']}  |  {c['descripcion']!r}  |  {', '.join(c['palabras_clave'])}  |  {c['pais']}")
    if not a.aplicar:
        print("(no se aplico nada: correr con --aplicar)")
        return
    # el DJ edita en Studio en paralelo: el 2026-09-28 escribio "Jugando" y este script lo piso.
    # Si la descripcion del canal no es la del JSON, la cambio el: no se toca sin --pisar.
    en_canal = actual["snippet"].get("description", "")
    if en_canal and en_canal != c["descripcion"] and not a.pisar:
        sys.exit(f"la descripcion del canal es {en_canal!r} y no la escribio este script: "
                 "copiarla a canal.json, o correr con --pisar si de verdad hay que reemplazarla")

    banner = yt.channelBanners().insert(media_body=MediaFileUpload(str(RAIZ / c["banner"]))).execute()["url"]
    palabras = " ".join(f'"{p}"' if " " in p else p for p in c["palabras_clave"])
    cuerpo = {"id": actual["id"], "brandingSettings": {
        "channel": {"title": c["titulo"], "description": c["descripcion"], "keywords": palabras,
                    "country": c["pais"], "defaultLanguage": "es",
                    # el video destacado para quien entra sin estar suscripto
                    **({"unsubscribedTrailer": c["trailer"]} if c.get("trailer") else {})},
        "image": {"bannerExternalUrl": banner},
    }}
    yt.channels().update(part="brandingSettings", body=cuerpo).execute()
    try:
        yt.watermarks().set(channelId=actual["id"], media_body=MediaFileUpload(str(RAIZ / c["marca_de_agua"])),
                            body={"timing": MARCA_TIMING, "position": {"type": "corner", "cornerPosition": "topRight"}}
                            ).execute()
        print("marca de agua puesta")
    except ValueError as e:
        if "must not be zero" not in str(e):
            raise
        print("marca de agua enviada (respuesta vacia; verificar en Studio -> Personalizacion -> Marca)")

    leido = yt.channels().list(part="snippet,brandingSettings", mine=True).execute()["items"][0]
    b = leido["brandingSettings"]
    print(f"leido de YouTube: titulo {leido['snippet']['title']!r} (branding {b['channel'].get('title')!r}), "
          f"descripcion {b['channel'].get('description')!r}, banner {'si' if b.get('image') else 'NO'}")
    if leido["snippet"]["title"] != c["titulo"]:
        print("el titulo visible todavia no cambio: YouTube puede tardar unos minutos en propagarlo")


if __name__ == "__main__":
    main()
