"""Acceso autenticado al canal de YouTube del DJ.

La credencial de la app (`data/youtube_client_secret.json`) se baja una vez de la
consola de Google, proyecto `plomo-youtube`. El permiso del DJ
(`data/youtube_token.json`) lo genera `scripts/youtube_auth.py`. Los dos estan
fuera de git: con cualquiera de ellos se opera el canal.
"""
from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

RAIZ = Path(__file__).resolve().parents[2]
CLIENTE = RAIZ / "data" / "youtube_client_secret.json"
TOKEN = RAIZ / "data" / "youtube_token.json"
# subir, editar videos/miniaturas/listas, y comentar (el comentario fijado)
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def credenciales() -> Credentials:
    if not TOKEN.exists():
        raise SystemExit("falta el permiso del DJ: correr scripts/youtube_auth.py")
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds.valid:
        if not (creds.expired and creds.refresh_token):
            raise SystemExit("el permiso no se puede renovar: volver a correr scripts/youtube_auth.py")
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return creds


def cliente():
    return build("youtube", "v3", credentials=credenciales(), cache_discovery=False)
