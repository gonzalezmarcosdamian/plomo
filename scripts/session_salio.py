# -*- coding: utf-8 -*-
"""Cuando una Session programada ya es publica, la pone de destacada del canal y en la web.

POR QUE
-------
La Session 02 sale el domingo 2026-10-04 a las 9:00: el DJ toca ese set el sabado a la
noche ("ponela programada domingo 9 am"). YouTube la abre sola a esa hora, pero el video
destacado y la web no se pueden cambiar antes sin apuntar a un video privado. El
Programador de tareas de Windows corre esto despues de la hora; si la maquina estaba
apagada, cuando vuelva. Espera a que el video sea publico y recien ahi hace los pasos.

USO
---
    python scripts/session_salio.py data/youtube/session_02.json
    # sin consola, con log (lo que corre la tarea programada):
    pythonw scripts/sin_ventana.py postproduction/video/session_02_salio.log
        scripts/session_salio.py data/youtube/session_02.json
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from plomo.youtube import cliente  # noqa: E402

ESPERA_MAX_S = 3 * 3600
CADA_S = 300
SIN_VENTANA = 0x08000000   # CREATE_NO_WINDOW: desde pythonw, cada hijo de consola abriria una ventana


def correr(cmd: list[str], cwd: Path = RAIZ) -> None:
    print(f"$ {' '.join(cmd)}", flush=True)
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=SIN_VENTANA)
    print((r.stdout + r.stderr).strip()[-1500:], flush=True)
    if r.returncode != 0:
        sys.exit(f"fallo con {r.returncode}: {' '.join(cmd)}")


def esperar_publico(yt, vid: str) -> None:
    limite = time.time() + ESPERA_MAX_S
    while True:
        items = yt.videos().list(part="status", id=vid).execute()["items"]
        estado = items[0]["status"]["privacyStatus"] if items else "no existe"
        print(f"{datetime.now():%H:%M} {vid}: {estado}", flush=True)
        if estado == "public":
            return
        if estado == "no existe" or time.time() > limite:
            sys.exit(f"{vid} no esta publico ({estado}): no se toca el canal ni la web")
        time.sleep(CADA_S)


def main() -> None:
    paquete = sys.argv[1]
    p = json.loads((RAIZ / paquete).read_text(encoding="utf-8"))
    vid = json.loads((RAIZ / "data" / "youtube" / f"{p['nombre']}_publicado.json").read_text(encoding="utf-8"))["id"]
    esperar_publico(cliente(), vid)

    py = sys.executable.replace("pythonw.exe", "python.exe")
    correr([py, "scripts/youtube_canal.py", "--trailer", vid])
    correr([py, "scripts/web_sessions.py"])
    vercel = shutil.which("vercel") or str(Path.home() / "AppData" / "Roaming" / "npm" / "vercel.cmd")
    correr(["cmd", "/c", vercel, "deploy", "--prod", "--yes", "--scope", "gonzalezmarcosdamians-projects"],
           cwd=RAIZ / "web" / "plomo")
    imagen = f"web/plomo/img/{p['nombre'].replace('_', '-')}.jpg"
    archivos = ["data/youtube/canal.json", "web/plomo/index.html", imagen]
    cambios = subprocess.run(["git", "status", "--porcelain", "--", *archivos], cwd=RAIZ, capture_output=True,
                             text=True, creationflags=SIN_VENTANA).stdout.strip()
    if cambios:
        correr(["git", "add", *archivos])
        correr(["git", "commit", "-m", f"feat: {p['nombre']} salio, destacada en el canal y en la web", "--", *archivos])
    print(f"listo: https://youtu.be/{vid} destacado y en https://plomo.marcosdamiangonzalez.ar", flush=True)


if __name__ == "__main__":
    main()
