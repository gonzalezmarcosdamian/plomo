# -*- coding: utf-8 -*-
"""Publica un set en Spotify, en orden, y lo vuelve a sincronizar en cada vuelta.

POR QUE
-------
"Haceme las listas en el orden en Spotify, las podes editar en cada iteracion?"
Si: la lista se busca por nombre y se REEMPLAZA su contenido, asi que conserva
la misma URL, el mismo lugar en la carpeta y lo que el DJ le haya puesto de
portada o descripcion. Cada iteracion del set es un `spotify_sync.py NNN` mas,
no una lista nueva.

QUE NO PUEDE
------------
Poner un tema que no esta en Spotify. La biblioteca es de Extended Mixes de
sellos chicos y una parte no llega al streaming; el script dice cuales faltaron
en vez de poner cualquier otra version. Un tema que no aparece no se reemplaza
por el radio edit ni por otro remix: seria una lista que suena distinto de lo
que el DJ va a tocar.

LOS ENDPOINTS VIEJOS DEVUELVEN 403, Y PARECE OTRA COSA
------------------------------------------------------
Spotify deprecó `/users/{id}/playlists` y `/playlists/{id}/tracks`, y en vez de
404 o de un mensaje que lo diga, devuelve **403 Forbidden** con el cuerpo vacio.
Eso se lee como "no tenes permiso" y manda a buscar el problema donde no esta:
scopes, cuenta, modo desarrollo, Extended Quota. Perdi una tarde en eso.

Los que andan son los nuevos:

    POST /me/playlists                 crear          -> 201
    POST /playlists/{id}/items         agregar        -> 201
    PUT  /playlists/{id}/items         reemplazar     -> 200
    GET  /playlists/{id}/items         leer           -> 200

Regla para la proxima: un 403 sin cuerpo en una API que uno cree conocer es
sospechoso de endpoint viejo antes que de permisos. Se descarta probando la
version nueva del mismo endpoint.

COMO BUSCA
----------
Primero `artist:"X" track:"Y"` con el titulo limpio de "(Extended Mix)" y
parecidos; si no hay, busca el titulo con el remixer, que es lo que distingue
dos versiones del mismo tema; si tampoco, titulo y artista sueltos. Se queda con
el candidato cuyo titulo y artista se parecen mas, y nunca con uno que apenas
comparta una palabra.

USO
---
    python scripts/spotify_auth.py            # una sola vez
    python scripts/spotify_sync.py 143
    python scripts/spotify_sync.py 139 140 141 142 143 144 145
"""
from __future__ import annotations

import argparse
import base64
import difflib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOKEN_F = RAIZ / "data" / "spotify_token.json"
API = "https://api.spotify.com/v1"
RUIDO = re.compile(r"\s*[\(\[](original|extended|radio|club|vocal|instrumental)[^\)\]]*[\)\]]",
                   re.I)
# Un remix DE VERDAD, o sea con alguien acreditado. "(Original Mix)" y
# "(Extended Mix)" contienen la palabra "mix" y no son remixes: tratarlos como
# tales hacia que el buscador castigara al candidato correcto por no decir
# "mix" en el titulo, y Juri de Parra for Cuva caia de 0.63 a 0.48 y quedaba
# como "no esta en Spotify" estando.
PARENTESIS = re.compile(r"[\(\[][^\)\]]*[\)\]]")
REMIX = re.compile(
    r"[\(\[]\s*(?!(?:original|extended|radio|club|vocal|instrumental))"
    r"([^\)\]]*(?:remix|rework|edit|mix)[^\)\]]*)[\)\]]", re.I)


def limpiar(s: str) -> str:
    return RUIDO.sub("", s or "").strip(" -")


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s or "")
                if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def parecido(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def acceso() -> str:
    if not TOKEN_F.exists():
        sys.exit("falta el permiso de usuario: corre primero python scripts/spotify_auth.py")
    ref = json.loads(TOKEN_F.read_text(encoding="utf-8"))["refresh_token"]
    b = base64.b64encode(
        f"{os.environ['SPOTIFY_CLIENT_ID']}:{os.environ['SPOTIFY_CLIENT_SECRET']}".encode()).decode()
    r = requests.post("https://accounts.spotify.com/api/token",
                      data={"grant_type": "refresh_token", "refresh_token": ref},
                      headers={"Authorization": f"Basic {b}"}, timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]


class Spotify:
    def __init__(self, tok: str):
        self.h = {"Authorization": f"Bearer {tok}"}
        self.yo = self.get("/me")["id"]

    def get(self, ruta, **params):
        r = requests.get(API + ruta, headers=self.h, params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    def post(self, ruta, payload):
        r = requests.post(API + ruta, headers=self.h, json=payload, timeout=20)
        r.raise_for_status()
        return r.json()

    def put(self, ruta, payload):
        r = requests.put(API + ruta, headers=self.h, json=payload, timeout=20)
        r.raise_for_status()
        return r.json() if r.text else {}

    def buscar(self, artista: str, titulo: str) -> tuple[str | None, str]:
        t, a = limpiar(titulo), artista.split(",")[0].strip()
        remix = REMIX.search(titulo)
        # El NUCLEO del titulo, sin ningun parentesis. Spotify publica el remix
        # con guion y otras palabras --"Un Mundo En Paz - Serious Dancers
        # Remix"-- asi que buscar track:"Un Mundo En Paz (Serious Dancers
        # Extended Remix)" da CERO resultados, y buscar solo "Un Mundo En Paz"
        # lo encuentra con 0.93. El parentesis, que para nosotros es
        # informacion, para el buscador es ruido.
        nucleo = PARENTESIS.sub("", titulo).strip(" -")
        intentos = [f'artist:"{a}" track:"{t}"']
        if nucleo != t:
            intentos.append(f'artist:"{a}" track:"{nucleo}"')
        if remix:
            intentos.append(f'{nucleo} {remix.group(1)}')
        intentos += [f"{a} {t}", f"{a} {nucleo}", nucleo]
        for q in intentos:
            try:
                res = self.get("/search", q=q, type="track", limit=10)["tracks"]["items"]
            except requests.HTTPError:
                continue
            mejor, punt = None, 0.0
            for it in res:
                # se compara el titulo CON y SIN el sufijo: Spotify publica
                # "Juri" y la biblioteca lo tiene como "Juri (Original Mix)",
                # y comparar solo la forma larga lo dejaba en 0.47 y afuera
                pt = max(parecido(titulo, it["name"]), parecido(t, it["name"]),
                         parecido(nucleo, it["name"]))
                p = pt * 0.6 + max(parecido(artista, ar["name"]) for ar in it["artists"]) * 0.4
                # una version distinta del mismo tema no sirve: si el titulo
                # original dice remix, el candidato tiene que decir algo parecido
                if remix and "remix" not in it["name"].lower() and "mix" not in it["name"].lower():
                    p -= 0.15
                if p > punt:
                    mejor, punt = it, p
            if mejor and punt >= 0.62:
                return mejor["uri"], f"{mejor['artists'][0]['name']} - {mejor['name']}"
        return None, ""

    def playlist_por_nombre(self, nombre: str) -> str | None:
        off = 0
        while True:
            r = self.get("/me/playlists", limit=50, offset=off)
            for pl in r["items"]:
                if pl["name"] == nombre and pl["owner"]["id"] == self.yo:
                    return pl["id"]
            if not r.get("next"):
                return None
            off += 50


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("nums", type=int, nargs="+")
    ap.add_argument("--prefijo", default="", help="texto delante del nombre de la lista")
    ap.add_argument("--archivo", action="store_true",
                    help="no escribe en Spotify: deja los links en data/spotify/ para pegar a mano")
    args = ap.parse_args()

    # Spotify bloquea TODA escritura para apps en modo desarrollo: crear una
    # lista, guardar un tema y hasta seguir a un artista dan 403 con los scopes
    # otorgados y la cuenta habilitada. Lo unico que destraba eso es el Extended
    # Quota Mode, que se pide y puede no salir. Mientras tanto, --archivo deja
    # los links en orden y la app de escritorio los pega de una: se seleccionan
    # todas las lineas, se copian, y se pegan adentro de la lista.
    sp = Spotify(acceso())
    cache_f = RAIZ / "data" / "spotify_matches.json"
    cache = json.loads(cache_f.read_text(encoding="utf-8")) if cache_f.exists() else {}

    for num in args.nums:
        f = RAIZ / "data" / "set_targets" / f"set_{num}.json"
        if not f.exists():
            print(f"set {num}: no hay target JSON")
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        nombre = args.prefijo + doc["name"]
        uris, faltan = [], []
        for t in doc["tracks"]:
            cid = t["content_id"]
            if cid in cache:
                uri, nom = cache[cid]["uri"], cache[cid]["nombre"]
            else:
                uri, nom = sp.buscar(t["artist"], t["title"])
                cache[cid] = {"uri": uri, "nombre": nom}
            if uri:
                uris.append(uri)
            else:
                faltan.append(f"{t['artist']} - {t['title']}")
        if args.archivo:
            dest = RAIZ / "data" / "spotify"
            dest.mkdir(parents=True, exist_ok=True)
            f_out = dest / f"set_{num}.txt"
            links = [u.replace("spotify:track:", "https://open.spotify.com/track/")
                     for u in uris]
            f_out.write_text("\n".join(links), encoding="utf-8")
            print(f"{nombre}")
            print(f"  {len(uris)}/{len(doc['tracks'])} temas -> {f_out.relative_to(RAIZ)}")
            for x in faltan:
                print(f"    no esta en Spotify: {x[:66]}")
            continue
        pid = sp.playlist_por_nombre(nombre)
        if pid is None:
            pid = sp.post("/me/playlists",
                          {"name": nombre, "public": False,
                           "description": "Set armado con plomo. Se re-sincroniza en cada iteracion."})["id"]
            estado = "creada"
        else:
            estado = "actualizada"
        sp.put(f"/playlists/{pid}/items", {"uris": uris[:100]})
        for i in range(100, len(uris), 100):
            sp.post(f"/playlists/{pid}/items", {"uris": uris[i:i + 100]})
        print(f"{nombre}")
        print(f"  {estado}: {len(uris)}/{len(doc['tracks'])} temas   "
              f"https://open.spotify.com/playlist/{pid}")
        for x in faltan:
            print(f"    no esta en Spotify: {x[:66]}")
    cache_f.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
