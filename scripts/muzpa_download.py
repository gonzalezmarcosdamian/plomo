"""
Downloader de Muzpa via API directa.

Uso:
  python scripts/muzpa_download.py "Guy J" "Sirens"
  python scripts/muzpa_download.py --search "Guy J"
  python scripts/muzpa_download.py --batch tracks.txt

tracks.txt formato (una por linea):
  Guy J — Sirens
  Massano — Ten Minutes
  Cid Inc. — Remnants

Session cookie:
  El SESS cookie dura ~30 días. Si el login automático falla, renovalo:
    1. Abrí muzpa.com en Chrome → DevTools (F12) → Network
    2. Hacé cualquier request → copiá el valor de la cookie "SESS"
    3. Pegalo en .env: MUZPA_SESSION=<valor>
"""
import sys
import os
import re
import urllib.parse
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from plomo import config

MUZPA_API = "https://srv.muzpa.com"
DOWNLOADS = config.DOWNLOADS_FOLDER


def _session_from_env() -> requests.Session | None:
    """Build a session using the MUZPA_SESSION cookie from .env."""
    sess_cookie = os.getenv("MUZPA_SESSION")
    if not sess_cookie:
        return None
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"{MUZPA_API}/",
        "Accept": "application/json",
        "Cookie": f"SESS={sess_cookie}",
    })
    return s


def _session_from_login() -> requests.Session | None:
    """Login via API credentials from .env."""
    user = os.getenv("MUZPA_USER")
    pwd = os.getenv("MUZPA_PASS")
    if not user or not pwd:
        return None

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"{MUZPA_API}/",
        "Accept": "application/json",
    })

    try:
        r = s.post("https://muzpa.com/api/account/login",
                   json={"login": user, "password": pwd}, timeout=10)
    except requests.RequestException as e:
        print(f"  Login request error: {e}")
        return None

    if r.status_code != 200:
        return None

    sess = s.cookies.get("SESS") or r.json().get("sess")
    if sess:
        s.headers["Cookie"] = f"SESS={sess}"
        print(f"  Login OK, SESS={sess[:20]}...")
    return s


def get_session() -> requests.Session | None:
    """
    Return an authenticated session.

    Priority:
      1. Login with MUZPA_USER + MUZPA_PASS
      2. Fallback to MUZPA_SESSION cookie (in case login endpoint is down or
         credentials are not set but a valid cookie was manually saved)

    If the session cookie is expired (HTTP 401/403 on first real request), the
    caller should remove MUZPA_SESSION from .env, re-obtain it from DevTools,
    and paste it back.
    """
    s = _session_from_login()
    if s:
        return s

    s = _session_from_env()
    if s:
        print("  Usando MUZPA_SESSION del .env (login no disponible)")
        return s

    print("ERROR: No hay sesión disponible.")
    print("  Opciones:")
    print("    a) Agrega MUZPA_USER + MUZPA_PASS al .env")
    print("    b) Obtené la cookie de DevTools y agrega MUZPA_SESSION=<valor> al .env")
    return None


def _is_session_valid(s: requests.Session) -> bool:
    """Quick check: ping the search endpoint with a trivial query."""
    try:
        r = s.get(f"{MUZPA_API}/a/ms/media/search?format=mp3&page=0&text=test", timeout=10)
        return r.status_code == 200
    except requests.RequestException:
        return False


def search(s: requests.Session, query: str) -> list[dict]:
    """
    Search Muzpa by free-text query.

    Returns list of result dicts with keys: id, filename, fullname, bpm, key.
    """
    encoded = query.replace(" ", "+")
    url = f"{MUZPA_API}/a/ms/media/search?format=mp3&matchonly=true&page=0&popularorder=true&text={encoded}"
    try:
        r = s.get(url, timeout=15)
    except requests.RequestException as e:
        print(f"  Search error: {e}")
        return []

    if r.status_code == 401 or r.status_code == 403:
        print(f"  Sesión expirada (HTTP {r.status_code}).")
        print("  Renovar: obtené el cookie SESS de DevTools y actualizá MUZPA_SESSION en .env")
        return []

    if r.status_code != 200:
        return []

    try:
        data = r.json()
    except Exception:
        return []

    if not data:
        return []

    results = []
    for album in (data.get("albums") or []):
        for track in album.get("tracks", []):
            if not track.get("satisfies"):
                continue
            results.append({
                "id": track["id"],
                "filename": track.get("filename", ""),
                "fullname": track.get("fullnm_html", ""),
                "bpm": track.get("bpm"),
                "key": track.get("initial_key"),
            })
    return results


def search_artist_title(s: requests.Session, artist: str, title: str) -> list[dict]:
    """Search and filter results to match artist + title."""
    results = search(s, f"{artist} {title}")
    filtered = []
    for t in results:
        fname = t.get("fullname", "").lower()
        if artist.lower() in fname and title.lower() in fname:
            filtered.append(t)
    # Fall back to unfiltered if nothing matched exactly
    return filtered if filtered else results


def download_track(s: requests.Session, track_id: int, filename: str) -> tuple[Path, float] | None:
    """Download a track by ID. Returns (dest_path, size_mb) or None on failure."""
    url = f"{MUZPA_API}/dwnld/track/{track_id}.mp3"
    try:
        r = s.get(url, timeout=60, stream=True)
    except requests.RequestException as e:
        print(f"  Download error: {e}")
        return None

    if r.status_code == 401 or r.status_code == 403:
        print(f"  Sesión expirada al descargar (HTTP {r.status_code}). Renovar MUZPA_SESSION.")
        return None

    if r.status_code != 200:
        print(f"  Error {r.status_code}: {r.text[:100]}")
        return None

    # Nombre desde Content-Disposition o filename del track
    cd = r.headers.get("content-disposition", "")
    fname_match = re.search(r"filename\*?=(?:UTF-8'')?([^;]+)", cd)
    if fname_match:
        fname = urllib.parse.unquote(fname_match.group(1).strip().strip('"'))
    else:
        fname = re.sub(r'[<>:"/\\|?*]', '', filename.replace(".aiff", ".mp3").replace(".aif", ".mp3"))
        if not fname.endswith(".mp3"):
            fname += ".mp3"

    dest = DOWNLOADS / fname
    with open(dest, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

    size_mb = dest.stat().st_size / 1024 / 1024
    return dest, size_mb


def process(artist: str, title: str, s: requests.Session | None = None) -> bool:
    """Search and download a single track. Returns True on success."""
    if s is None:
        s = get_session()
    if s is None:
        return False

    print(f"Buscando: {artist} — {title}")
    results = search_artist_title(s, artist, title)

    if not results:
        print("  No encontrado en Muzpa")
        return False

    track = results[0]
    print(f"  Encontrado: {track['fullname']} (BPM={track['bpm']}, Key={track['key']})")

    result = download_track(s, track["id"], track["filename"])
    if result:
        dest, size_mb = result
        print(f"  OK {dest.name} ({size_mb:.1f} MB)")
        return True
    return False


def cmd_search(query: str) -> None:
    """Print search results without downloading."""
    s = get_session()
    if s is None:
        return

    print(f"Buscando: {query}")
    results = search(s, query)

    if not results:
        print("  Sin resultados.")
        return

    print(f"  {len(results)} resultado(s):")
    for t in results:
        bpm = t.get("bpm") or "?"
        key = t.get("key") or "?"
        print(f"  [{t['id']}] {t['fullname']}  BPM={bpm}  Key={key}")


def cmd_batch(path: str) -> None:
    """Download all tracks listed in a file (one per line: Artist — Title)."""
    s = get_session()
    if s is None:
        return

    with open(path) as f:
        lines = [l.strip() for l in f if " — " in l or " - " in l]

    print(f"Procesando {len(lines)} tracks...")
    ok = 0
    for line in lines:
        sep = " — " if " — " in line else " - "
        parts = line.split(sep, 1)
        if len(parts) == 2:
            if process(parts[0].strip(), parts[1].strip(), s):
                ok += 1
    print(f"\nDescargados: {ok}/{len(lines)}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return

    if sys.argv[1] == "--search":
        if len(sys.argv) < 3:
            print("Uso: muzpa_download.py --search 'query'")
            return
        cmd_search(sys.argv[2])

    elif sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("Uso: muzpa_download.py --batch tracks.txt")
            return
        cmd_batch(sys.argv[2])

    else:
        artist = sys.argv[1]
        title = sys.argv[2] if len(sys.argv) > 2 else ""
        process(artist, title)


if __name__ == "__main__":
    main()
