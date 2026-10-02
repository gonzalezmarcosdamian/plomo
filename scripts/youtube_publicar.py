# -*- coding: utf-8 -*-
"""Sube un video al canal del DJ con su paquete de publicacion, y lo publica SOLO cuando se pide.

POR QUE
-------
El paquete (titulo, descripcion con capitulos, tags, miniatura) lo arma el agente
`video` en data/youtube/<nombre>.json. Cargarlo a mano en Studio es copiar y
pegar cinco campos sin equivocarse; esto lo hace igual cada vez.

Publicar es una accion hacia afuera y la decide el DJ: `subir` deja el video en
PRIVADO. Asi aparecen primero los reclamos de Content ID (el paso "Comprobaciones"
de Studio), y recien despues `publicar` lo abre.

LA RESTRICCION QUE HAY QUE PROBAR ANTES
---------------------------------------
Google documenta que lo que sube por `videos.insert` un proyecto de API no
auditado queda trabado en privado. `prueba` sube diez segundos, intenta pasarlos
a no listado, dice que paso y los borra. Si queda trabado, el camino es subir el
archivo a mano en Studio y correr `actualizar --id <id>`, que carga todo lo demas
sobre ese video (editar no es subir).

USO
---
    python scripts/youtube_publicar.py prueba
    python scripts/youtube_publicar.py subir data/youtube/2026-09-23_atardecer.json
    python scripts/youtube_publicar.py actualizar data/youtube/2026-09-23_atardecer.json --id <id>
    python scripts/youtube_publicar.py estado data/youtube/2026-09-23_atardecer.json
    python scripts/youtube_publicar.py publicar data/youtube/2026-09-23_atardecer.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from plomo.youtube import cliente  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BLOQUE_SUBIDA = 64 * 1024 * 1024
REINTENTOS_BLOQUE = 8


def leer(paquete: Path) -> dict:
    return json.loads(paquete.read_text(encoding="utf-8"))


def registro(p: dict) -> Path:
    return RAIZ / "data" / "youtube" / f"{p['nombre']}_publicado.json"


def snippet(p: dict) -> dict:
    return {"title": p["titulo"], "description": p["descripcion"], "tags": p["tags"],
            "categoryId": p["categoria"], "defaultLanguage": p["idioma"]}


def subir_archivo(yt, archivo: Path, cuerpo: dict) -> str:
    media = MediaFileUpload(str(archivo), chunksize=BLOQUE_SUBIDA, resumable=True)
    pedido = yt.videos().insert(part="snippet,status", body=cuerpo, media_body=media)
    respuesta = None
    while respuesta is None:
        # un video de una hora y media son mas de cien bloques: un corte de red no puede tirar la subida
        estado, respuesta = pedido.next_chunk(num_retries=REINTENTOS_BLOQUE)
        if estado:
            print(f"  subido {estado.progress() * 100:5.1f}%", flush=True)
    return respuesta["id"]


def estado_de(yt, video_id: str) -> dict:
    items = yt.videos().list(part="status,processingDetails,contentDetails", id=video_id).execute()["items"]
    return items[0] if items else {}


def cmd_prueba(yt) -> None:
    """Diez segundos privados -> intenta no listado -> informa -> borra."""
    with tempfile.TemporaryDirectory() as tmp:
        clip = Path(tmp) / "prueba.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                        "color=c=0x1b2a38:s=1280x720:d=10", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                        "-t", "10", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(clip)], check=True)
        vid = subir_archivo(yt, clip, {"snippet": {"title": "prueba plomo (se borra sola)", "categoryId": "10"},
                                      "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}})
    print(f"subido {vid}")
    try:
        yt.videos().update(part="status", body={"id": vid, "status": {
            "privacyStatus": "unlisted", "selfDeclaredMadeForKids": False}}).execute()
        quedo = estado_de(yt, vid).get("status", {}).get("privacyStatus")
        print(f"pedido: no listado -> quedo: {quedo}")
        print("SUBIR POR API ANDA" if quedo == "unlisted"
              else "TRABADO EN PRIVADO: subir a mano en Studio y usar `actualizar --id`")
    except HttpError as e:
        print(f"el cambio de privacidad fallo: {e.status_code} {e.reason}")
    finally:
        yt.videos().delete(id=vid).execute()
        print(f"prueba {vid} borrada")


def cmd_subir(yt, p: dict) -> None:
    archivo = RAIZ / p["video"]
    if not archivo.exists():
        sys.exit(f"no existe {archivo}")
    print(f"subiendo {archivo.name} ({archivo.stat().st_size / 1e9:.2f} GB) como PRIVADO")
    vid = subir_archivo(yt, archivo, {"snippet": snippet(p), "status": {
        "privacyStatus": "private", "selfDeclaredMadeForKids": False, "embeddable": True}})
    registro(p).write_text(json.dumps({"id": vid, "url": f"https://youtu.be/{vid}"}, indent=2), encoding="utf-8")
    print(f"-> https://youtu.be/{vid}  (privado)")
    poner_miniatura(yt, p, vid)


def poner_miniatura(yt, p: dict, vid: str) -> None:
    try:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(RAIZ / p["miniatura"]))).execute()
        print("miniatura puesta")
    except HttpError as e:
        print(f"miniatura NO puesta ({e.status_code}): la cuenta tiene que estar verificada, youtube.com/verify")


def cmd_actualizar(yt, p: dict, vid: str) -> None:
    yt.videos().update(part="snippet", body={"id": vid, "snippet": snippet(p)}).execute()
    registro(p).write_text(json.dumps({"id": vid, "url": f"https://youtu.be/{vid}"}, indent=2), encoding="utf-8")
    print(f"titulo, descripcion y tags cargados en {vid}")
    poner_miniatura(yt, p, vid)


def cmd_estado(yt, p: dict) -> None:
    vid = json.loads(registro(p).read_text(encoding="utf-8"))["id"]
    e = estado_de(yt, vid)
    st, pr = e.get("status", {}), e.get("processingDetails", {})
    print(f"{vid}: privacidad {st.get('privacyStatus')}, subida {st.get('uploadStatus')}, "
          f"procesado {pr.get('processingStatus')}, contenido con licencia {e.get('contentDetails', {}).get('licensedContent')}")
    for k in ("rejectionReason", "failureReason"):
        if st.get(k):
            print(f"  {k}: {st[k]}")


def cmd_publicar(yt, p: dict) -> None:
    vid = json.loads(registro(p).read_text(encoding="utf-8"))["id"]
    yt.videos().update(part="status", body={"id": vid, "status": {
        "privacyStatus": "public", "selfDeclaredMadeForKids": False, "embeddable": True}}).execute()
    print(f"PUBLICO: https://youtu.be/{vid}  (estado real: {estado_de(yt, vid)['status']['privacyStatus']})")


def cmd_borrar(yt, vid: str) -> None:
    """Borra un video del canal. No tiene vuelta atras: dice cual es antes de borrarlo."""
    items = yt.videos().list(part="snippet,status", id=vid).execute()["items"]
    if not items:
        sys.exit(f"{vid} no esta en el canal")
    print(f"borrando {vid}: {items[0]['snippet']['title']} ({items[0]['status']['privacyStatus']})")
    yt.videos().delete(id=vid).execute()
    quedo = yt.videos().list(part="id", id=vid).execute()["items"]
    print("borrado" if not quedo else f"{vid} SIGUE en el canal")


def cmd_programar(yt, p: dict, cuando: str) -> None:
    """Deja el video privado con fecha de publicacion: YouTube lo abre solo a esa hora."""
    from datetime import datetime, timezone
    momento = datetime.fromisoformat(cuando)
    if momento.tzinfo is None:
        sys.exit("la hora necesita zona: por ejemplo 2026-09-28T19:00-03:00")
    if momento <= datetime.now(timezone.utc):
        sys.exit(f"{cuando} ya paso")
    vid = json.loads(registro(p).read_text(encoding="utf-8"))["id"]
    utc = momento.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    yt.videos().update(part="status", body={"id": vid, "status": {
        "privacyStatus": "private", "publishAt": utc, "selfDeclaredMadeForKids": False, "embeddable": True}}).execute()
    st = estado_de(yt, vid)["status"]
    print(f"programado: {vid} sale {cuando} (UTC {st.get('publishAt')}), hasta entonces {st['privacyStatus']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["prueba", "subir", "actualizar", "estado", "programar", "publicar", "borrar"])
    ap.add_argument("paquete", nargs="?")
    ap.add_argument("--id")
    ap.add_argument("--cuando", help="programar: fecha con zona, ej. 2026-09-28T19:00-03:00")
    a = ap.parse_args()
    yt = cliente()
    if a.accion == "prueba":
        return cmd_prueba(yt)
    if a.accion == "borrar":
        if not a.id:
            sys.exit("borrar necesita --id")
        return cmd_borrar(yt, a.id)
    if not a.paquete:
        sys.exit("falta el paquete: data/youtube/<nombre>.json")
    p = leer(RAIZ / a.paquete)
    if a.accion == "actualizar":
        if not a.id:
            sys.exit("actualizar necesita --id del video subido a mano")
        return cmd_actualizar(yt, p, a.id)
    if a.accion == "programar":
        if not a.cuando:
            sys.exit("programar necesita --cuando, ej. 2026-09-28T19:00-03:00")
        return cmd_programar(yt, p, a.cuando)
    {"subir": cmd_subir, "estado": cmd_estado, "publicar": cmd_publicar}[a.accion](yt, p)


if __name__ == "__main__":
    main()
