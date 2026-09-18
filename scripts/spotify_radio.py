"""La "radio" de un tema en Spotify, traida como lista de compras.

Por que existe: hasta ahora el descubrimiento salia de dos lados — el radar de
sellos (lo que SALE) y los setlists de referencia (lo que se TOCA). Falta el
tercero, que es el que usa cualquiera cuando encuentra un tema que le pega: darle
play a la radio del tema y ver a donde lleva. Eso es una fuente distinta, porque
no depende de que el track haya salido en un sello que seguimos ni de que lo haya
tocado un DJ que miramos.

Spotify dio de baja /recommendations y /related-artists para apps nuevas, asi que
la radio se arma a mano y el script avisa cual de los dos caminos pudo usar:

  1. related-artists + top-tracks  (si la app tiene acceso al endpoint viejo)
  2. los artistas que comparten album/EP con el seed, mas sus top-tracks

Lo que devuelve se cruza contra la biblioteca y sale en formato batch, listo para
muzpa_download.py. Spotify sirve para DESCUBRIR; el archivo se baja de Muzpa.

Uso:
    python scripts/spotify_radio.py "Nanda Dilby"
    python scripts/spotify_radio.py "Nanda Dilby" --artistas 12 --por-artista 5
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(RAIZ / ".env")

import os  # noqa: E402
from plomo.matching import clave  # noqa: E402

API = "https://api.spotify.com/v1"
_N = re.compile(r"[^a-z0-9]")


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()


def token() -> str:
    cid = os.getenv("SPOTIFY_CLIENT_ID")
    sec = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not cid or not sec:
        sys.exit("faltan SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET en .env")
    b = base64.b64encode(f"{cid}:{sec}".encode()).decode()
    r = requests.post("https://accounts.spotify.com/api/token",
                      data={"grant_type": "client_credentials"},
                      headers={"Authorization": f"Basic {b}"}, timeout=20)
    if r.status_code != 200:
        sys.exit(f"Spotify no dio token ({r.status_code}): {r.text[:160]}")
    return r.json()["access_token"]


class Spotify:
    def __init__(self, tok: str) -> None:
        self.h = {"Authorization": f"Bearer {tok}"}

    def get(self, ruta: str, **params):
        r = requests.get(f"{API}/{ruta}", headers=self.h, params=params, timeout=25)
        if r.status_code == 200:
            return r.json()
        return {"_error": r.status_code, "_texto": r.text[:120]}


def semilla(sp: Spotify, consulta: str) -> dict | None:
    d = sp.get("search", q=consulta, type="track", limit=1)
    items = (d.get("tracks") or {}).get("items") or []
    return items[0] if items else None


def radio(sp: Spotify, track: dict, n_art: int, por_art: int) -> tuple[list[dict], str]:
    """(tracks candidatos, que camino se uso)."""
    art_ids = [a["id"] for a in track["artists"]]
    vecinos: dict[str, str] = {}
    camino = "related-artists"

    for aid in art_ids:
        d = sp.get(f"artists/{aid}/related-artists")
        for a in d.get("artists", [])[:n_art]:
            vecinos[a["id"]] = a["name"]

    if not vecinos:
        return _por_playlists(sp, track, n_art * por_art), "co-ocurrencia en playlists"

    for aid in art_ids:
        vecinos.pop(aid, None)

    salida, vistos = [], set()
    for aid, nombre in list(vecinos.items())[:n_art * 2]:
        d = sp.get(f"artists/{aid}/top-tracks", market="AR")
        for t in d.get("tracks", [])[:por_art]:
            k = (t["name"].lower(), t["artists"][0]["name"].lower())
            if k in vistos:
                continue
            vistos.add(k)
            salida.append({
                "artist": ", ".join(a["name"] for a in t["artists"]),
                "title": t["name"],
                "popularidad": t.get("popularity", 0),
                "vecino": nombre,
            })
    return salida, camino


def _por_playlists(sp: Spotify, track: dict, tope: int) -> list[dict]:
    """La radio, reconstruida a mano: que mas aparece junto al tema.

    Spotify cerro /related-artists y /recommendations para las apps nuevas, que
    es justo lo que hacia falta. Pero "parecido" no es un dato secreto de
    Spotify: es co-ocurrencia. Si mil personas armaron playlists donde Nanda
    convive con otro tema, ese otro tema ES la radio de Nanda.

    Se buscan playlists por nombre del tema y del artista, se conservan las que
    REALMENTE lo contienen, y se cuenta que mas aparece adentro. Un tema que
    aparece en ocho de esas playlists pesa mas que uno que aparece en una.
    """
    seed_id = track["id"]
    seed_art = {a["id"] for a in track["artists"]}
    nombre = track["name"]
    a0 = track["artists"][0]["name"]

    ids: list[str] = []
    for q in (f"{a0} {nombre}", nombre, a0):
        d = sp.get("search", q=q, type="playlist", limit=20)
        for p in ((d.get("playlists") or {}).get("items") or []):
            if p and p.get("id") and p["id"] not in ids:
                ids.append(p["id"])

    cuenta: dict[tuple, dict] = {}
    con_semilla = 0
    for pid in ids[:40]:
        d = sp.get(f"playlists/{pid}/tracks", limit=100,
                   fields="items(track(id,name,popularity,artists(id,name)))")
        items = [i.get("track") for i in d.get("items", []) if i.get("track")]
        if not any(t.get("id") == seed_id for t in items):
            continue          # la playlist no tiene el tema: no dice nada de el
        con_semilla += 1
        for t in items:
            if t.get("id") == seed_id or not t.get("name"):
                continue
            # los temas del propio artista no son descubrimiento
            if {a["id"] for a in t.get("artists", [])} & seed_art:
                continue
            k = (t["name"].lower(), (t["artists"][0]["name"] if t.get("artists") else "").lower())
            e = cuenta.setdefault(k, {
                "artist": ", ".join(a["name"] for a in t.get("artists", [])),
                "title": t["name"], "popularidad": t.get("popularity", 0), "veces": 0})
            e["veces"] += 1

    print(f"  playlists revisadas: {len(ids[:40])}, con el tema adentro: {con_semilla}")
    out = sorted(cuenta.values(), key=lambda e: (-e["veces"], -e["popularidad"]))
    for e in out:
        e["vecino"] = f"{e['veces']} playlists"
    return out[:tope]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("consulta", nargs="+", help='ej: "Nanda Dilby"')
    ap.add_argument("--artistas", type=int, default=10)
    ap.add_argument("--por-artista", type=int, default=4)
    ap.add_argument("--salida", type=Path)
    args = ap.parse_args()

    sp = Spotify(token())
    q = " ".join(args.consulta)
    s = semilla(sp, q)
    if not s:
        sys.exit(f"Spotify no encontro '{q}'")
    print(f"semilla: {', '.join(a['name'] for a in s['artists'])} - {s['name']}")

    cands, camino = radio(sp, s, args.artistas, args.por_artista)
    print(f"camino usado: {camino}  |  {len(cands)} candidatos\n")
    if not cands:
        sys.exit("la radio vino vacia — revisar permisos de la app en Spotify")

    pool = json.loads((RAIZ / "data" / "pool.json").read_text(encoding="utf-8"))
    tengo = {clave(t["artist"], t["title"]) for t in pool}
    nuevos = [c for c in cands if clave(c["artist"], c["title"]) not in tengo]
    print(f"ya en la biblioteca: {len(cands) - len(nuevos)}  |  nuevos: {len(nuevos)}")

    nuevos.sort(key=lambda c: -c["popularidad"])
    for c in nuevos[:20]:
        print(f"  pop{c['popularidad']:>3} | {c['artist'][:30]:30} - {c['title'][:40]}"
              f"   (via {c['vecino'][:18]})")

    dest = args.salida or RAIZ / "data" / f"batch_radio_{date.today()}.txt"
    L = [f"# Radio de Spotify a partir de: {s['artists'][0]['name']} - {s['name']}",
         f"# camino: {camino} | {len(nuevos)} temas que no estan en la biblioteca",
         "# Spotify sirve para descubrir; el archivo se baja de Muzpa.", ""]
    L += [f"{c['artist']} - {c['title']}   # pop{c['popularidad']} via {c['vecino']}"
          for c in nuevos]
    dest.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\n-> {dest.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
