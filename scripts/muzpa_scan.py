"""
Escanea Muzpa para un listado de artista+titulo y reporta disponibilidad.
Util para planificar descargas antes de bajar nada.

Uso:
  python scripts/muzpa_scan.py scan_targets.txt
"""
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from plomo import config
import sqlcipher3

# Import muzpa functions
sys.path.insert(0, str(Path(__file__).parent))
from muzpa_download import get_session, search_artist_title


def in_library(con, artist: str, title: str) -> bool:
    rows = con.execute("""
        SELECT COUNT(*) FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE c.rb_local_deleted = 0
          AND LOWER(c.Title) LIKE LOWER(?)
          AND LOWER(COALESCE(a.Name,'')) LIKE LOWER(?)
    """, (f"%{title[:15]}%", f"%{artist.split()[0]}%")).fetchone()
    return rows[0] > 0


def main():
    targets_file = sys.argv[1] if len(sys.argv) > 1 else None
    if not targets_file:
        print("Uso: muzpa_scan.py targets.txt")
        return

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

    s = get_session()
    if not s:
        return

    with open(targets_file, encoding="utf-8") as f:
        lines = [l.strip() for l in f
                 if (" - " in l or " — " in l) and not l.strip().startswith("#")]

    found = []
    not_found = []
    already_have = []

    for line in lines:
        sep = " — " if " — " in line else " - "
        parts = line.split(sep, 1)
        if len(parts) != 2:
            continue
        artist, title = parts[0].strip(), parts[1].strip()

        if in_library(con, artist, title):
            already_have.append(f"{artist} - {title}")
            print(f"  [LIB] {artist} - {title}")
            continue

        results = search_artist_title(s, artist, title)
        if results:
            t = results[0]
            bpm = t.get("bpm") or "?"
            key = t.get("key") or "?"
            found.append({"artist": artist, "title": title,
                          "fullname": t["fullname"], "bpm": bpm, "key": key})
            print(f"  [OK ] BPM={bpm:>4} Key={key:<5} | {t['fullname'][:60]}")
        else:
            not_found.append(f"{artist} - {title}")
            print(f"  [NO ] {artist} - {title}")

    con.close()

    print(f"\n=== RESUMEN ===")
    print(f"  En Muzpa:       {len(found)}")
    print(f"  Ya en libreria: {len(already_have)}")
    print(f"  No encontrado:  {len(not_found)}")

    # Guardar resultado
    out = Path(targets_file).stem + "_scan_result.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"found": found, "not_found": not_found, "already_have": already_have}, f, ensure_ascii=False, indent=2)
    print(f"\nResultado guardado: {out}")


if __name__ == "__main__":
    main()
