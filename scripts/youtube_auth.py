# -*- coding: utf-8 -*-
"""Permiso del DJ sobre su canal de YouTube, una sola vez.

POR QUE HACE FALTA
------------------
Subir un video, cambiarle el titulo o ponerle miniatura son acciones sobre la
cuenta del DJ, y YouTube pide que el DUENO del canal autorice a la app. Igual que
con Spotify (scripts/spotify_auth.py): se autoriza una vez y de ahi en mas los
scripts se autentican solos con el refresh token.

COMO FUNCIONA
-------------
Abre el navegador en la pantalla de permisos de Google y levanta un servidor
local para recibir la respuesta. Como la app es propia y no esta verificada por
Google, aparece "Google no verifico esta app": Configuracion avanzada -> Ir a
Plomo. El permiso queda en data/youtube_token.json, fuera de git.

Al final lee el canal y dice si ya acepta videos de mas de 15 minutos
(`longUploadsStatus`): sin verificar la cuenta en youtube.com/verify, no.

USO
---
    python scripts/youtube_auth.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from plomo.youtube import CLIENTE, SCOPES, TOKEN, cliente  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    if not CLIENTE.exists():
        sys.exit(f"falta {CLIENTE}: se baja de la consola de Google, proyecto plomo-youtube, "
                 "Clientes -> App de escritorio -> Descargar JSON")
    flujo = InstalledAppFlow.from_client_secrets_file(str(CLIENTE), SCOPES)
    creds = flujo.run_local_server(port=0, prompt="consent", access_type="offline",
                                   authorization_prompt_message="Abriendo el navegador para el permiso de YouTube...",
                                   success_message="Listo, ya podes cerrar esta pestana.")
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    print(f"permiso guardado en {TOKEN}")

    canales = cliente().channels().list(part="snippet,status,statistics", mine=True).execute().get("items", [])
    if not canales:
        sys.exit("la cuenta que dio el permiso no tiene canal de YouTube")
    for c in canales:
        largos = c["status"].get("longUploadsStatus", "?")
        print(f"canal: {c['snippet']['title']}  ({c['statistics'].get('videoCount', '?')} videos)")
        print(f"videos de mas de 15 min: {largos}"
              + ("" if largos == "allowed" else "  -> verificar la cuenta en https://www.youtube.com/verify"))


if __name__ == "__main__":
    main()
