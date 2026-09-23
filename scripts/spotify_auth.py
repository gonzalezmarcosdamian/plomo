# -*- coding: utf-8 -*-
"""Permiso de usuario de Spotify, una sola vez, para poder ESCRIBIR listas.

POR QUE HACE FALTA
------------------
Las credenciales que el proyecto ya usaba (client credentials) sirven para
buscar, que es lo que hace spotify_radio.py. Crear o editar una playlist es una
accion sobre la cuenta del DJ, y para eso Spotify pide que el DUENO de la cuenta
autorice a la app. Sin eso no hay forma, ni con la API key.

COMO FUNCIONA
-------------
Abre el navegador en la pantalla de permisos de Spotify, levanta un servidor
local en el redirect que ya esta configurado (localhost:8888/callback), y cuando
el DJ toca "Aceptar" recibe el codigo por ahi mismo. Nadie copia y pega nada.

El resultado es un refresh token que queda en data/spotify_token.json, fuera de
git. Con eso, de aca en mas los scripts se autentican solos y no hay que volver
a pasar por el navegador.

PERMISOS QUE PIDE
-----------------
playlist-modify-private y playlist-modify-public: crear y editar listas.
playlist-read-private: encontrar una lista que ya existe en vez de duplicarla.
No pide acceso a la biblioteca ni a la reproduccion.

USO
---
    python scripts/spotify_auth.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DESTINO = RAIZ / "data" / "spotify_token.json"
SCOPES = "playlist-modify-private playlist-modify-public playlist-read-private"

_codigo: dict[str, str] = {}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        q = parse_qs(urlparse(self.path).query)
        _codigo.update({k: v[0] for k, v in q.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        ok = "code" in q
        self.wfile.write(
            ("<h2>" + ("Listo, ya podes cerrar esta pestana."
                       if ok else "No se pudo: " + q.get("error", ["?"])[0])
             + "</h2>").encode("utf-8"))

    def log_message(self, *a):  # silencio
        pass


def main() -> None:
    cid = os.environ["SPOTIFY_CLIENT_ID"]
    secret = os.environ["SPOTIFY_CLIENT_SECRET"]
    redirect = os.environ["SPOTIFY_REDIRECT_URI"]
    puerto = urlparse(redirect).port or 8888

    url = "https://accounts.spotify.com/authorize?" + urlencode({
        "client_id": cid, "response_type": "code",
        "redirect_uri": redirect, "scope": SCOPES})

    servidor = HTTPServer(("localhost", puerto), Handler)
    threading.Thread(target=servidor.handle_request, daemon=True).start()
    print("Se abre el navegador para que autorices la app.")
    print("Si no se abre solo, entra a:\n  " + url + "\n")
    webbrowser.open(url)
    servidor.socket.settimeout(180)
    for _ in range(180):
        if _codigo:
            break
        import time
        time.sleep(1)
    if "code" not in _codigo:
        sys.exit("no llego el permiso (pasaron 3 minutos o lo cancelaste)")

    b = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    r = requests.post("https://accounts.spotify.com/api/token",
                      data={"grant_type": "authorization_code",
                            "code": _codigo["code"], "redirect_uri": redirect},
                      headers={"Authorization": f"Basic {b}"}, timeout=20)
    r.raise_for_status()
    tok = r.json()
    if "refresh_token" not in tok:
        sys.exit("Spotify no devolvio refresh_token")
    DESTINO.write_text(json.dumps({"refresh_token": tok["refresh_token"]}, indent=1),
                       encoding="utf-8")
    perfil = requests.get("https://api.spotify.com/v1/me",
                          headers={"Authorization": f"Bearer {tok['access_token']}"},
                          timeout=20).json()
    print(f"permiso guardado en {DESTINO.relative_to(RAIZ)}")
    print(f"cuenta: {perfil.get('display_name')} ({perfil.get('id')})")
    print("\nYa se pueden crear y editar listas: python scripts/spotify_sync.py 143")


if __name__ == "__main__":
    main()
