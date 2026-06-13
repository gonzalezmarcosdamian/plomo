"""
Planifica el armado de un set:
1. Lee data/set_targets/setXX.json con la tracklist objetivo
2. Verifica que tracks existen en la libreria (DB)
3. Para los que faltan: chequea disponibilidad en Muzpa
4. Para los no disponibles: busca reemplazos automaticamente
5. Imprime el plan completo y genera batch file para descarga

Uso:
  python scripts/plan_set.py 16              # plan del set 16
  python scripts/plan_set.py 16 --batch      # plan + genera data/batch_set16.txt
  python scripts/plan_set.py --list          # lista todos los targets disponibles
"""
import sys
import json
import re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from plomo import config
import sqlcipher3

# Importar funciones de Muzpa sin ejecutar main
sys.path.insert(0, str(Path(__file__).parent))
from muzpa_download import get_session, search

TARGETS_DIR = Path(__file__).parent.parent / "data" / "set_targets"
TARGETS_DIR.mkdir(parents=True, exist_ok=True)


# ─── DB helpers ──────────────────────────────────────────────────────────────

def db_connect():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
    return con


def find_playlist(con, set_num: int) -> tuple[str, str] | None:
    """Encuentra un playlist por numero de set (busca '16.' en el nombre)."""
    rows = con.execute(
        "SELECT ID, Name FROM djmdPlaylist WHERE Name LIKE ? AND rb_local_deleted=0",
        (f"{set_num}.%",)
    ).fetchall()
    if not rows:
        return None
    return rows[0][0], rows[0][1]


def get_playlist_tracks(con, playlist_id: str) -> list[dict]:
    """Retorna tracks actuales de un playlist."""
    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.BPM, c.Commnt, c.FileNameL
        FROM djmdSongPlaylist sp
        JOIN djmdContent c ON c.ID = sp.ContentID
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE sp.PlaylistID = ? AND c.rb_local_deleted = 0
        ORDER BY sp.TrackNo
    """, (playlist_id,)).fetchall()

    result = []
    for cid, artist, title, bpm, commnt, fname in rows:
        energy = 5.0
        if commnt and "E:" in commnt:
            try:
                energy = float(commnt.split("|")[0].replace("E:", "").strip())
            except ValueError:
                pass
        result.append({
            "content_id": str(cid),
            "artist": artist or "?",
            "title": title or "",
            "bpm": (bpm or 12200) / 100,
            "energy": energy,
            "filename": fname or "",
        })
    return result


def find_in_library(con, artist: str, title: str) -> str | None:
    """Busca un track en djmdContent por artist + title (fuzzy)."""
    # Busqueda exacta primero
    rows = con.execute("""
        SELECT c.ID FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE c.rb_local_deleted = 0
          AND LOWER(c.Title) LIKE LOWER(?)
          AND LOWER(COALESCE(a.Name, '')) LIKE LOWER(?)
    """, (f"%{title}%", f"%{artist.split()[0]}%")).fetchall()

    if rows:
        return str(rows[0][0])

    # Fallback: solo titulo
    rows = con.execute("""
        SELECT c.ID FROM djmdContent c
        WHERE c.rb_local_deleted = 0 AND LOWER(c.Title) LIKE LOWER(?)
    """, (f"%{title}%",)).fetchall()

    return str(rows[0][0]) if rows else None


# ─── Muzpa helpers ────────────────────────────────────────────────────────────

def check_muzpa(session, artist: str, title: str, remix: str = "") -> dict | None:
    """Busca un track en Muzpa. Retorna el primer resultado o None."""
    query = f"{artist} {title}"
    if remix:
        query += f" {remix}"
    results = search(session, query)
    if not results:
        return None
    # Filtrar por coincidencia minima de titulo
    title_lower = title.lower().split("(")[0].strip()
    for r in results:
        fname = r.get("fullname", "").lower()
        if title_lower in fname or title_lower[:15] in fname:
            return r
    return results[0]


def search_replacement(session, replacement_query: str, bpm_range: list[int],
                        exclude_names: set[str]) -> list[dict]:
    """Busca reemplazos en Muzpa para un track no disponible."""
    results = search(session, replacement_query)
    candidates = []
    for r in results:
        bpm = r.get("bpm")
        fname = r.get("fullname", "")
        if fname.lower() in exclude_names:
            continue
        if bpm and bpm_range[0] <= bpm <= bpm_range[1]:
            candidates.append(r)
    return candidates[:3]


# ─── Target JSON ──────────────────────────────────────────────────────────────

def load_target(set_num: int) -> dict | None:
    path = TARGETS_DIR / f"set_{set_num:02d}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_target(set_num: int, data: dict) -> None:
    path = TARGETS_DIR / f"set_{set_num:02d}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─── Plan ─────────────────────────────────────────────────────────────────────

def run_plan(set_num: int, write_batch: bool = False) -> None:
    target = load_target(set_num)
    if not target:
        print(f"ERROR: No existe data/set_targets/set_{set_num:02d}.json")
        print("Crea el archivo con la lista de tracks objetivo primero.")
        return

    con = db_connect()

    # Buscar playlist
    playlist = find_playlist(con, set_num)
    if playlist:
        pl_id, pl_name = playlist
        # Guardar playlist_id en target si no estaba
        if not target.get("playlist_id"):
            target["playlist_id"] = pl_id
            target["name"] = pl_name
            save_target(set_num, target)
        current_tracks = get_playlist_tracks(con, pl_id)
    else:
        pl_name = target.get("name", f"Set {set_num}")
        current_tracks = []
        print(f"  [warn] Playlist '{set_num}.' no encontrada en DB")

    bpm_range = target.get("bpm_range", [118, 127])
    target_count = target.get("target_track_count", 20)
    replacement_query = target.get("replacement_query", "progressive")

    print(f"\n{'='*60}")
    print(f"SET {set_num}: {pl_name}")
    print(f"  Tracks actuales: {len(current_tracks)}")
    print(f"  Tracks objetivo: {target_count}")
    print(f"  BPM range: {bpm_range[0]}-{bpm_range[1]}")
    print(f"{'='*60}")

    # Muzpa session
    session = get_session()

    in_library = []
    to_download = []
    not_available = []
    replacements = []
    already_excluded = set()

    print(f"\n{'─'*60}")
    print("CHECKING TRACKS OBJETIVO:")
    print(f"{'─'*60}")

    for track in target.get("tracks", []):
        artist = track.get("artist", "")
        title = track.get("title", "")
        remix = track.get("remix", "")
        energy = track.get("energy", 5.0)

        # Buscar en libreria
        cid = find_in_library(con, artist, title)
        if cid:
            in_library.append({**track, "content_id": cid})
            print(f"  [LIB ] {artist} - {title}")
            already_excluded.add(title.lower())
            continue

        # Buscar en Muzpa
        if session:
            result = check_muzpa(session, artist, title, remix)
            if result:
                to_download.append({
                    **track,
                    "muzpa_id": result["id"],
                    "muzpa_name": result["fullname"],
                    "muzpa_bpm": result.get("bpm"),
                })
                print(f"  [MUZPA] {result['fullname']} (BPM={result.get('bpm')})")
                already_excluded.add(title.lower())
            else:
                not_available.append(track)
                print(f"  [MISS ] {artist} - {title}  <- buscar reemplazo")
        else:
            not_available.append(track)

    # Buscar reemplazos para los no disponibles
    if not_available and session:
        print(f"\n{'─'*60}")
        print("BUSCANDO REEMPLAZOS:")
        print(f"{'─'*60}")
        for track in not_available:
            candidates = search_replacement(
                session, replacement_query, bpm_range, already_excluded
            )
            if candidates:
                best = candidates[0]
                replacements.append({
                    "original": track,
                    "replacement": best,
                    "muzpa_id": best["id"],
                    "muzpa_name": best["fullname"],
                    "muzpa_bpm": best.get("bpm"),
                    "energy": track.get("energy", 5.0),
                })
                already_excluded.add(best["fullname"].lower())
                print(f"  [ORIG] {track['artist']} - {track['title']}")
                print(f"  [REMP] {best['fullname']} (BPM={best.get('bpm')})")
            else:
                print(f"  [NADA] Sin reemplazo para {track['artist']} - {track['title']}")

    # Calcular cuantos tracks tendriamos
    total_available = len(in_library) + len(to_download) + len(replacements)
    gap = target_count - total_available

    print(f"\n{'='*60}")
    print(f"RESUMEN SET {set_num}:")
    print(f"  En libreria:    {len(in_library):>3} tracks")
    print(f"  En Muzpa:       {len(to_download):>3} tracks  <- descargar")
    print(f"  Reemplazos:     {len(replacements):>3} tracks  <- descargar")
    print(f"  No disponible:  {len(not_available) - len(replacements):>3} tracks")
    print(f"  {'─'*30}")
    print(f"  TOTAL posible:  {total_available:>3} / {target_count} objetivo")
    if gap > 0:
        print(f"  FALTAN:         {gap:>3} tracks para completar el set")
    elif gap <= 0:
        print(f"  OK: set completo ({total_available} tracks >= {target_count} objetivo)")
    print(f"{'='*60}")

    con.close()

    if write_batch:
        batch_path = Path(__file__).parent.parent / "data" / f"batch_set{set_num:02d}.txt"
        lines = []
        for t in to_download:
            artist = t["original"]["artist"] if "original" in t else t["artist"]
            title_full = t["muzpa_name"]
            # Usar formato Artist - Title para el batch
            lines.append(f"# {artist} - {t.get('title', '')}")
            lines.append(title_full)

        for r in replacements:
            lines.append(f"# REEMPLAZO de: {r['original']['artist']} - {r['original']['title']}")
            lines.append(r["muzpa_name"])

        # Formatear como "Artist - Title" usando el nombre completo de Muzpa
        batch_lines = []
        for t in to_download:
            batch_lines.append(t["muzpa_name"])
        for r in replacements:
            batch_lines.append(r["muzpa_name"])

        with open(batch_path, "w", encoding="utf-8") as f:
            for line in batch_lines:
                f.write(line + "\n")

        print(f"\nBatch file generado: {batch_path}")
        print(f"Correr: python scripts/muzpa_download.py --batch {batch_path}")


def cmd_list() -> None:
    """Lista todos los targets disponibles."""
    files = sorted(TARGETS_DIR.glob("set_*.json"))
    if not files:
        print("No hay targets en data/set_targets/")
        return
    print(f"\nTargets disponibles ({len(files)}):")
    for f in files:
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        name = data.get("name", f.stem)
        count = len(data.get("tracks", []))
        target_n = data.get("target_track_count", "?")
        print(f"  {f.name}: {name} — {count} tracks definidos / {target_n} objetivo")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] == "--help":
        print(__doc__)
        return

    if sys.argv[1] == "--list":
        cmd_list()
        return

    try:
        set_num = int(sys.argv[1])
    except ValueError:
        print(f"ERROR: '{sys.argv[1]}' no es un numero de set valido")
        return

    write_batch = "--batch" in sys.argv
    run_plan(set_num, write_batch=write_batch)


if __name__ == "__main__":
    main()
