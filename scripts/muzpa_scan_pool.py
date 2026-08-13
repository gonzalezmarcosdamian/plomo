"""Escanea Muzpa por artista conservando fecha, sello y genero.

`muzpa_download.search()` se queda solo con id/bpm/key y descarta `pubdate`,
`label` y `category_nm`, que son los campos que permiten validar si un track es
nuevo y de que palo es. Este scanner los conserva.

Filtra por BPM y descarta lo que ya esta en la biblioteca (match normalizado por
artista+titulo, no por substring del titulo como hace muzpa_artist_scan).

Uso:
    python scripts/muzpa_scan_pool.py --artists data/artistas_organico.txt \\
        --bpm-max 121 --out data/pool_apertura_crudo.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).parent.parent / ".env")

import sqlcipher3  # noqa: E402

from muzpa_download import MUZPA_API, get_session  # noqa: E402
from plomo import config  # noqa: E402


def norm(s: str) -> str:
    """Minusculas sin acentos ni puntuacion, para comparar titulos."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\((?:original|extended)[^)]*\)", "", s, flags=re.I)
    return re.sub(r"[^a-z0-9]", "", s.lower())


def buscar(s, query: str) -> list[dict]:
    """Busca en Muzpa conservando los campos de album (fecha, sello, genero)."""
    url = (
        f"{MUZPA_API}/a/ms/media/search?format=mp3&matchonly=true&page=0"
        f"&text={urllib.parse.quote_plus(query)}"
    )
    try:
        r = s.get(url, timeout=20)
    except Exception as e:
        print(f"  error de red: {e}")
        return []
    if r.status_code in (401, 403):
        print("  SESION EXPIRADA — renovar MUZPA_SESSION en .env")
        return None  # type: ignore[return-value]
    if r.status_code != 200:
        return []
    try:
        data = r.json() or {}
    except Exception:
        return []

    out = []
    for album in data.get("albums") or []:
        label = (album.get("label") or {}).get("nm") or ""
        pub = album.get("pubdate") or ""
        for t in album.get("tracks", []):
            if not t.get("satisfies"):
                continue
            out.append(
                {
                    "id": t["id"],
                    "fullname": re.sub(r"<[^>]+>", "", t.get("fullnm_html", "")),
                    "filename": t.get("filename", ""),
                    "bpm": t.get("bpm"),
                    "key": t.get("initial_key"),
                    "genero": t.get("category_nm") or album.get("category_nm") or "",
                    "sello": label,
                    "pubdate": t.get("pubdate") or pub,
                    "playtime": t.get("playtime"),
                }
            )
    return out


def cargar_biblioteca() -> set[str]:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    firmas = set()
    for artista, titulo in con.execute(
        "SELECT a.Name, c.Title FROM djmdContent c"
        " LEFT JOIN djmdArtist a ON a.ID = c.ArtistID"
        " WHERE c.rb_local_deleted = 0"
    ):
        firmas.add(norm(titulo))
        if artista:
            firmas.add(norm(artista) + norm(titulo))
    con.close()
    return firmas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artists", type=Path, required=True)
    ap.add_argument("--bpm-max", type=float, default=121)
    ap.add_argument("--bpm-min", type=float, default=105)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    artistas = [
        ln.strip()
        for ln in args.artists.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    biblioteca = cargar_biblioteca()
    print(f"{len(artistas)} artistas | {len(biblioteca)} firmas en biblioteca\n")

    s = get_session()
    if not s:
        return

    candidatos: dict[str, dict] = {}
    for i, artista in enumerate(artistas, 1):
        res = buscar(s, artista)
        if res is None:
            print("Abortado: sesion de Muzpa expirada.")
            break
        nuevos = 0
        for t in res:
            nombre = t["fullname"]
            if artista.lower().split()[0] not in nombre.lower():
                continue
            # separar "Artista - Titulo"
            partes = nombre.split(" - ", 1)
            titulo = partes[1] if len(partes) > 1 else nombre
            interpretes = partes[0] if len(partes) > 1 else artista
            if norm(titulo) in biblioteca:
                continue
            if norm(interpretes) + norm(titulo) in biblioteca:
                continue
            bpm = t.get("bpm")
            if bpm and not (args.bpm_min <= float(bpm) <= args.bpm_max):
                continue
            clave = norm(interpretes) + norm(titulo)
            if clave in candidatos:
                continue
            candidatos[clave] = {**t, "artista_buscado": artista,
                                 "interpretes": interpretes, "titulo": titulo}
            nuevos += 1
        print(f"  [{i:2d}/{len(artistas)}] {artista:<28} {nuevos:3d} candidatos")
        time.sleep(0.4)

    lista = list(candidatos.values())
    args.out.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(lista)} candidatos unicos -> {args.out}")


if __name__ == "__main__":
    main()
