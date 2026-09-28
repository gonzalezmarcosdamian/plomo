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

class CuotaAgotada(RuntimeError):
    """Spotify devolvio 429. NO es que el tema no exista."""


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
# "Cosita - Mixed" es el corte de una compilacion mezclada, no el tema.
MIXED = re.compile(r"(?:^|[-(\[ ])mixed\b", re.I)
# "Muse feat. Kate Morgan" es "Muse": el invitado va acreditado aparte en
# Spotify, y dejarlo adentro del titulo hundia el parecido de 0.9 a 0.5.
FEAT = re.compile(r"\s*[(\[]?\b(feat|ft|featuring)\b[.]?[^)\]]*[)\]]?", re.I)
# palabras que NO son el nombre del remixer dentro del parentesis
VERSIONES = re.compile(r"\b(extended|original|radio|club|vocal|instrumental|remix|rework|edit|mix|version|feat|ft|featuring)\b", re.I)
REMIX = re.compile(
    r"[\(\[]\s*(?!(?:original|extended|radio|club|vocal|instrumental))"
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

    def buscar(self, artista: str, titulo: str,
               dur_seg: int | None = None) -> tuple[str | None, str]:
        """El tema que el DJ va a tocar, no otro con el mismo nombre.

        Tres cosas hunden a un candidato, y las tres aparecieron el 2026-09-27
        mirando la lista del 143 contra Rekordbox:

        1. EL REMIXER. La biblioteca tenia "Muse (L.GU. Extended Mix)" y en la
           lista habia quedado el "Roman Extended Mix". Los dos existen, los dos
           dicen "mix", y el puntaje anterior solo pedia que el candidato dijera
           "mix" en alguna parte: no comparaba QUIEN lo remezclo.
        2. LAS VERSIONES "Mixed". Spotify publica los temas de las
           compilaciones mezcladas con el sufijo "- Mixed", y son el corte de
           la mezcla continua, no el tema. Tres habian entrado asi.
        3. EL LARGO. Un extended de ocho minutos contra un edit de cuatro es el
           mismo titulo y otro tema. `dur_seg` viene de Rekordbox, que es la
           duracion del archivo que va a sonar, y es la senal mas barata y mas
           dura de todas: Portal Six entro en 4:00 contra 7:22 del archivo.
        """
        t, a = limpiar(titulo), artista.split(",")[0].strip()
        remix = REMIX.search(titulo)
        # El NUCLEO del titulo, sin ningun parentesis. Spotify publica el remix
        # con guion y otras palabras --"Un Mundo En Paz - Serious Dancers
        # Remix"-- asi que buscar track:"Un Mundo En Paz (Serious Dancers
        # Extended Remix)" da CERO resultados, y buscar solo "Un Mundo En Paz"
        # lo encuentra con 0.93. El parentesis, que para nosotros es
        # informacion, para el buscador es ruido.
        nucleo = PARENTESIS.sub("", titulo).strip(" -")
        corto = FEAT.sub("", nucleo).strip(" -") or nucleo
        # quien remezclo, sin las palabras de version: de "L.GU. Extended Mix"
        # queda "l gu", que es lo que tiene que aparecer en el candidato.
        quien = ""
        if remix:
            quien = norm(VERSIONES.sub("", remix.group(1)))
        intentos = [f'artist:"{a}" track:"{t}"']
        if nucleo != t:
            intentos.append(f'artist:"{a}" track:"{nucleo}"')
        if remix:
            intentos.append(f"{nucleo} {remix.group(1)}")
        intentos += [f"{a} {t}", f"{a} {nucleo}", nucleo]
        for q in intentos:
            try:
                res = self.get("/search", q=q, type="track", limit=10)["tracks"]["items"]
            except requests.HTTPError as e:
                # 429 no significa "no esta": significa que no pude preguntar.
                # Tratarlo como ausencia escribe una conclusion falsa en el
                # informe Y la deja cacheada, que es peor: el tema queda
                # marcado como inexistente para siempre.
                if e.response is not None and e.response.status_code == 429:
                    espera = e.response.headers.get("retry-after", "?")
                    raise CuotaAgotada(
                        f"Spotify corto por cuota; vuelve en {espera} segundos") from e
                continue
            mejor, punt, pa_mejor = None, 0.0, 0.0
            for it in res:
                # se compara el titulo CON y SIN el sufijo: Spotify publica
                # "Juri" y la biblioteca lo tiene como "Juri (Original Mix)",
                # y comparar solo la forma larga lo dejaba en 0.47 y afuera
                pt = max(parecido(titulo, it["name"]), parecido(t, it["name"]),
                         parecido(nucleo, it["name"]), parecido(corto, it["name"]))
                pa = max(parecido(artista, ar["name"]) for ar in it["artists"])
                pa = max(pa, max(parecido(artista.split(",")[0].strip(), ar["name"])
                                 for ar in it["artists"]))
                p = pt * 0.6 + pa * 0.4
                nom = norm(it["name"])
                gente = norm(" ".join(ar["name"] for ar in it["artists"]))
                if remix:
                    if "remix" not in nom and "mix" not in nom:
                        p -= 0.15
                    # el remixer TIENE que estar, en el titulo o acreditado
                    if quien:
                        p += 0.15 if (quien in nom or quien in gente) else -0.40
                # El largo y el "- Mixed" ORDENAN, no descartan. Un radio edit
                # del mismo mix sigue siendo el tema, y la lista existe para que
                # el DJ la escuche en el auto: mejor el edit que un hueco. Lo
                # que SI descarta es el remixer equivocado, que es otro tema con
                # el mismo nombre. Puesto en -0.30 dejaba siete afuera diciendo
                # "no esta en Spotify" con la version buena a la vista.
                if MIXED.search(it["name"]) and not MIXED.search(titulo):
                    p -= 0.10
                if dur_seg and it.get("duration_ms"):
                    rel = abs(it["duration_ms"] / 1000 - dur_seg) / dur_seg
                    if rel > 0.25:
                        p -= 0.12
                    elif rel > 0.12:
                        p -= 0.05
                    elif rel < 0.04:
                        p += 0.08
                if p > punt:
                    mejor, punt, pa_mejor = it, p, pa
            # PISO al parecido de artista. "Confusion" de Dilby & Amine K
            # engancho el "Confusion" de Adam Sellouk & Glowal: titulo 1.00,
            # artista 0.38, y el promedio ponderado daba 0.75. Con un titulo
            # generico el titulo no identifica nada, y el artista es lo unico
            # que queda. El piso es 0.40: los matches buenos verificados van
            # de 0.53 para arriba (Rockka contra Rockka+Fuenka 0.63, Andy Moor
            # & Adam White contra su version con Whiteroom 0.71).
            if pa_mejor < 0.40:
                mejor, punt = None, 0.0
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

    # ESTE COMENTARIO DECIA que Spotify bloquea toda escritura para apps en modo
    # desarrollo y que hacia falta Extended Quota Mode. Era falso: los 403 venian
    # de endpoints deprecados, y con los nuevos las listas se crean y se
    # reemplazan sin ningun permiso especial (ver el encabezado del archivo).
    # Queda escrito porque una conclusion negativa equivocada no se revisa sola:
    # si manana algo vuelve a dar 403, el primer sospechoso es el endpoint.
    #
    # `--archivo` sobrevive por otro motivo: deja los links en orden en un .txt
    # para pegar a mano, que sirve cuando no hay permiso de usuario a mano.
    sp = Spotify(acceso())
    # La duracion del archivo de Rekordbox es la senal que separa el extended
    # del radio edit y de las versiones "- Mixed" de las compilaciones.
    POOL = {t["id"]: t for t in json.loads(
        (RAIZ / "data/pool.json").read_text(encoding="utf-8"))}
    cache_f = RAIZ / "data" / "spotify_matches.json"
    cache = json.loads(cache_f.read_text(encoding="utf-8")) if cache_f.exists() else {}

    for num in args.nums:
        f = RAIZ / "data" / "set_targets" / f"set_{num}.json"
        if not f.exists():
            print(f"set {num}: no hay target JSON")
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        nombre = args.prefijo + doc["name"]
        uris, faltan, sin_preguntar = [], [], []
        cortado = ""
        for t in doc["tracks"]:
            cid = t["content_id"]
            if cid in cache:
                uri, nom = cache[cid]["uri"], cache[cid]["nombre"]
            else:
                try:
                    uri, nom = sp.buscar(t["artist"], t["title"],
                                         (POOL.get(cid) or {}).get("dur_seg"))
                except CuotaAgotada as e:
                    # no es ausencia: es que no pude preguntar. Se publica lo que
                    # hay y se avisa, en vez de tirar la corrida entera.
                    sin_preguntar.append(f"{t['artist']} - {t['title']}")
                    cortado = str(e)
                    continue
                cache[cid] = {"uri": uri, "nombre": nom} if uri else None
                if cache[cid] is None:
                    # no se cachea el fracaso: la proxima corrida vuelve a
                    # intentar en vez de heredar un "no existe" que quiza
                    # solo fue un mal dia de la API.
                    del cache[cid]
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
        if sin_preguntar:
            print(f"    {len(sin_preguntar)} temas SIN PREGUNTAR: {cortado}")
            for x in sin_preguntar[:5]:
                print(f"      {x[:66]}")
            print("    la lista quedo incompleta; re-correr cuando vuelva la cuota")
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
