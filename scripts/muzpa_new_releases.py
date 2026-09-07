"""
Radar de nuevos lanzamientos en Muzpa.

Escanea Muzpa por artistas y sellos de la biblioteca (ordenado por fecha),
filtra por fecha de publicacion y descarta lo que ya esta en Rekordbox.

Uso:
  python scripts/muzpa_new_releases.py                      # ultimos 90 dias
  python scripts/muzpa_new_releases.py --days 30
  python scripts/muzpa_new_releases.py --since 2026-06-01
  python scripts/muzpa_new_releases.py --top-artists 40 --top-labels 25
  python scripts/muzpa_new_releases.py --terms data/radar_extra.txt

Salida:
  data/nuevos_<since>.json   reporte completo
  data/batch_nuevos_<since>.txt   listo para: muzpa_download.py --batch
"""
from __future__ import annotations

import argparse
import json
import re
from urllib.parse import quote_plus
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import sqlcipher3  # noqa: E402
from plomo import config  # noqa: E402

from muzpa_download import MUZPA_API, get_session  # noqa: E402

DEFAULT_DAYS = 90
MAX_PAGES = 12
DATA_DIR = ROOT / "data"

# El sonido del proyecto: progressive 118-126 BPM (ver docs/MI_SONIDO.md).
DEFAULT_CATEGORIES = ("Progressive", "Melodic House/Techno", "Organic House / Downtempo")
DEFAULT_BPM_MIN = 118
DEFAULT_BPM_MAX = 126

# Sellos genericos: aparecen en la biblioteca pero no definen el estilo.
LABEL_BLACKLIST = {
    "white label",
    "armada music",
    "toolroom",
    "drumcode",
    "spinnin' records",
    "unknown",
}

# Compilados de Beatport: sirven para descubrir, pero se marcan aparte.
CHART_PATTERN = re.compile(r"^(bp\s*-|top\s*100|.*\bchart\b)", re.IGNORECASE)


@dataclass(frozen=True)
class Candidate:
    """Un track nuevo encontrado en Muzpa."""

    track_id: int
    pubdate: str
    artist: str
    title: str
    subtitle: str
    fullname: str
    label: str
    category: str
    bpm: int | None
    key: str | None
    playtime: str
    from_chart: bool = False
    matched_terms: tuple[str, ...] = field(default=())

    @property
    def titulo_completo(self) -> str:
        """Titulo tal como se va a pedir, con el remix incluido."""
        return f"{self.title} ({self.subtitle})" if self.subtitle else self.title

    @property
    def batch_line(self) -> str:
        return f"{self.artist} - {self.titulo_completo}"


# ---------------------------------------------------------------- biblioteca


def open_library() -> sqlcipher3.Connection:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con


def top_artists(con: sqlcipher3.Connection, limit: int) -> list[str]:
    rows = con.execute(
        """
        SELECT a.Name FROM djmdContent c
        JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE c.rb_local_deleted = 0 AND a.Name IS NOT NULL AND a.Name != ''
        GROUP BY a.Name ORDER BY COUNT(*) DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    # Los nombres compuestos ("Rockka, Maze 28") ya estan cubiertos por cada parte.
    return [r[0] for r in rows if "," not in r[0]]


def top_labels(con: sqlcipher3.Connection, limit: int) -> list[str]:
    rows = con.execute(
        """
        SELECT l.Name FROM djmdContent c
        JOIN djmdLabel l ON l.ID = c.LabelID
        WHERE c.rb_local_deleted = 0 AND l.Name IS NOT NULL AND l.Name != ''
        GROUP BY l.Name ORDER BY COUNT(*) DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [r[0] for r in rows if r[0].lower() not in LABEL_BLACKLIST]


def library_index(con: sqlcipher3.Connection) -> set[str]:
    """Set de claves normalizadas 'artista|titulo' de toda la biblioteca."""
    rows = con.execute(
        """
        SELECT COALESCE(a.Name, ''), COALESCE(c.Title, '')
        FROM djmdContent c LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE c.rb_local_deleted = 0
        """
    ).fetchall()
    return {norm_key(artist, title) for artist, title in rows}


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def norm_key(artist: str, title: str) -> str:
    """Clave de dedup: primer artista + titulo sin sufijos de mix."""
    first = re.split(r"[,&]| feat| ft\.", artist, maxsplit=1)[0]
    clean = re.sub(r"\((original|extended)[^)]*\)", "", title, flags=re.IGNORECASE)
    return f"{norm(first)}|{norm(clean)}"


# -------------------------------------------------------------------- muzpa


def search_page(session, term: str, page: int) -> dict:
    """Busqueda ordenada por fecha (sin popularorder)."""
    url = (
        f"{MUZPA_API}/a/ms/media/search"
        # quote_plus y no replace(' ', '+'): un termino con "&" ("Lost & Found")
        # cortaba el querystring y la busqueda se volvia text=Lost+, devolviendo
        # cero. Es el mismo bug que ya se habia arreglado en muzpa_download.py.
        f"?format=mp3&matchonly=true&page={page}&text={quote_plus(term)}"
    )
    try:
        response = session.get(url, timeout=25)
    except Exception as exc:  # red inestable: no romper el scan completo
        print(f"    error de red: {exc}")
        return {}
    if response.status_code in (401, 403):
        raise PermissionError("Sesion Muzpa expirada — renovar MUZPA_SESSION en .env")
    if response.status_code != 200:
        return {}
    try:
        return response.json() or {}
    except ValueError:
        return {}


def matches(term: str, kind: str, fullname: str, label: str) -> bool:
    """Un artista matchea por nombre del track; un sello, solo por su campo label.

    Sin esta distincion, sellos de nombre generico ("Moments", "UV", "Sprout")
    matchean cualquier titulo que contenga esa palabra.
    """
    if kind == "sello":
        return norm(term) == norm(label)
    return term.lower() in fullname.lower()


def scan_term(session, term: str, kind: str, since: str) -> tuple[list[Candidate], int]:
    """Recorre paginas por fecha hasta pasar el corte. Devuelve (candidatos, charts)."""
    found: list[Candidate] = []
    charts = 0

    for page in range(MAX_PAGES):
        data = search_page(session, term, page)
        albums = data.get("albums") or []
        if not albums:
            break

        stop = True
        for album in albums:
            if (album.get("pubdate") or "") >= since:
                stop = False
            is_chart = bool(CHART_PATTERN.match(album.get("nm") or ""))
            for track in album.get("tracks") or []:
                if not track.get("satisfies"):
                    continue
                pubdate = track.get("pubdate") or album.get("pubdate") or ""
                if pubdate < since:
                    continue
                label = (track.get("label") or {}).get("nm") or ""
                fullname = track.get("fullnm_html") or ""
                if not matches(term, kind, fullname, label):
                    continue
                if is_chart:
                    charts += 1
                found.append(
                    Candidate(
                        track_id=track["id"],
                        pubdate=pubdate,
                        artist=track.get("artist") or "",
                        title=track.get("title") or "",
                        subtitle=track.get("subtitle") or "",
                        fullname=fullname,
                        label=label,
                        category=track.get("category_nm") or "",
                        bpm=track.get("bpm"),
                        key=track.get("initial_key"),
                        playtime=track.get("playtime") or "",
                        from_chart=is_chart,
                        matched_terms=(term,),
                    )
                )
        if stop:
            break

    return found, charts


# ------------------------------------------------------------------- reporte


def dedupe(candidates: list[Candidate]) -> list[Candidate]:
    """Colapsa el mismo track hallado por varios terminos."""
    by_key: dict[str, Candidate] = {}
    for cand in candidates:
        key = norm(cand.fullname) or str(cand.track_id)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = cand
        else:
            merged = tuple(dict.fromkeys(existing.matched_terms + cand.matched_terms))
            # Si el track aparece en un release real y ademas en un chart, gana el release.
            base = existing if not existing.from_chart else cand
            by_key[key] = Candidate(
                **{
                    **base.__dict__,
                    "matched_terms": merged,
                    "from_chart": existing.from_chart and cand.from_chart,
                }
            )
    return sorted(by_key.values(), key=lambda c: c.pubdate, reverse=True)


def write_outputs(candidates: list[Candidate], since: str) -> tuple[Path, Path]:
    DATA_DIR.mkdir(exist_ok=True)
    json_path = DATA_DIR / f"nuevos_{since}.json"
    batch_path = DATA_DIR / f"batch_nuevos_{since}.txt"

    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(
            [c.__dict__ | {"matched_terms": list(c.matched_terms)} for c in candidates],
            handle,
            ensure_ascii=False,
            indent=2,
        )

    with open(batch_path, "w", encoding="utf-8") as handle:
        handle.write(f"# Nuevos lanzamientos en Muzpa desde {since}\n")
        handle.write("# Revisar y borrar las lineas que no quieras antes de descargar\n\n")
        for cand in candidates:
            meta = f"BPM={cand.bpm or '?'} Key={cand.key or '?'} {cand.pubdate} [{cand.label}]"
            handle.write(f"# {meta}\n{cand.batch_line}\n")

    return json_path, batch_path


def print_report(candidates: list[Candidate], since: str) -> None:
    by_term: dict[str, list[Candidate]] = {}
    for cand in candidates:
        by_term.setdefault(cand.matched_terms[0] if cand.matched_terms else "?", []).append(cand)

    print(f"\n{'=' * 78}")
    print(f"NUEVOS LANZAMIENTOS DESDE {since} — {len(candidates)} tracks")
    print("=" * 78)
    for term, tracks in sorted(by_term.items(), key=lambda kv: -len(kv[1])):
        print(f"\n--- {term} ({len(tracks)}) ---")
        for cand in sorted(tracks, key=lambda c: c.pubdate, reverse=True):
            bpm = str(cand.bpm or "?")
            key = str(cand.key or "?")
            print(
                f"  {cand.pubdate}  BPM={bpm:>3} {key:<4} {cand.playtime:>5} "
                f"| {cand.fullname[:66]} [{cand.label}]"
            )


# ---------------------------------------------------------------------- main


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Radar de nuevos lanzamientos en Muzpa")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--since", help="Fecha de corte YYYY-MM-DD (pisa --days)")
    parser.add_argument("--top-artists", type=int, default=35)
    parser.add_argument("--top-labels", type=int, default=22)
    parser.add_argument("--terms", help="Archivo con terminos extra, uno por linea")
    parser.add_argument(
        "--include-charts",
        action="store_true",
        help="Incluir tracks que solo aparecen en compilados/charts de Beatport",
    )
    parser.add_argument("--bpm-min", type=int, default=DEFAULT_BPM_MIN)
    parser.add_argument("--bpm-max", type=int, default=DEFAULT_BPM_MAX)
    parser.add_argument(
        "--categories",
        default=",".join(DEFAULT_CATEGORIES),
        help="Generos separados por coma. Vacio ('') desactiva el filtro.",
    )
    return parser.parse_args()


def fits_style(cand: Candidate, categories: set[str], bpm_min: int, bpm_max: int) -> bool:
    if categories and cand.category not in categories:
        return False
    if cand.bpm is None:
        return True
    return bpm_min <= cand.bpm <= bpm_max


def load_extra_terms(path: str | None) -> list[str]:
    if not path:
        return []
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def main() -> None:
    args = parse_args()
    since = args.since or (date.today() - timedelta(days=args.days)).isoformat()

    con = open_library()
    artists = top_artists(con, args.top_artists)
    labels = top_labels(con, args.top_labels)
    known = library_index(con)
    con.close()

    terms = list(dict.fromkeys(artists + labels + load_extra_terms(args.terms)))
    print(f"Corte: {since} | {len(artists)} artistas + {len(labels)} sellos")
    print(f"Biblioteca: {len(known)} tracks conocidos\n")

    session = get_session()
    if session is None:
        return

    label_set = set(labels)
    raw: list[Candidate] = []
    for index, term in enumerate(terms, 1):
        kind = "sello" if term in label_set else "artista"
        try:
            found, charts = scan_term(session, term, kind, since)
        except PermissionError as exc:
            print(f"\n{exc}")
            return
        note = f" ({charts} en charts)" if charts else ""
        print(f"[{index:>2}/{len(terms)}] {term:<28} {kind:<7} {len(found):>3} nuevos{note}")
        raw.extend(found)

    candidates = dedupe(raw)
    # El dedup tiene que usar el MISMO string que se va a proponer. Con
    # `c.title` pelado, "Gaxyda" no matcheaba "Gaxyda (D-Nox & Beckers Remix)"
    # de la biblioteca, asi que todo remix se re-proponia: 24 de 270 en la
    # ultima corrida ya estaban descargados.
    fresh = [c for c in candidates
             if norm_key(c.artist, c.titulo_completo) not in known]
    in_library = len(candidates) - len(fresh)

    if not args.include_charts:
        only_charts = [c for c in fresh if c.from_chart]
        fresh = [c for c in fresh if not c.from_chart]
        if only_charts:
            print(f"\nOmitidos (solo en charts, usar --include-charts): {len(only_charts)}")

    categories = {c.strip() for c in args.categories.split(",") if c.strip()}
    on_style = [c for c in fresh if fits_style(c, categories, args.bpm_min, args.bpm_max)]
    off_style = len(fresh) - len(on_style)
    fresh = on_style

    print(f"\nEncontrados: {len(candidates)} | Ya en biblioteca: {in_library}")
    print(f"Fuera de estilo (genero/BPM): {off_style}")

    print_report(fresh, since)
    json_path, batch_path = write_outputs(fresh, since)
    print(f"\nReporte: {json_path}")
    print(f"Batch:   {batch_path}")
    print(f"Descargar: python scripts/muzpa_download.py --batch {batch_path}")


if __name__ == "__main__":
    main()
