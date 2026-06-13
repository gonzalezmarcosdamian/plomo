"""
Busca tracks con archivo faltante y actualiza FolderPath si el archivo
se encuentra en Inbox u otras carpetas conocidas.
"""
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from plomo import config
import sqlcipher3

DRY = "--dry" in sys.argv

SEARCH_ROOTS = [
    Path(r"C:\Users\gonza\OneDrive\Documentos\Music\2026\Nuevos\Inbox"),
    Path(r"C:\Users\gonza\OneDrive\Documentos\Music\2026\Nuevos\2026-05"),
    Path(r"C:\Users\gonza\OneDrive\Documentos\Music\2026\Nuevos"),
    Path(r"C:\Users\gonza\OneDrive\Documentos\Music\2026"),
]


def db_connect():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con


def find_file(filename: str) -> Path | None:
    for root in SEARCH_ROOTS:
        candidate = root / filename
        if candidate.exists():
            return candidate
    # Busqueda recursiva en Inbox como fallback
    inbox = SEARCH_ROOTS[0]
    if inbox.exists():
        matches = list(inbox.rglob(filename))
        if matches:
            return matches[0]
    return None


def main():
    mode = "DRY RUN" if DRY else "WRITE MODE"
    print(f"Fix Missing Paths — {mode}")

    con = db_connect()

    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.FolderPath
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE c.rb_local_deleted = 0
          AND c.FolderPath IS NOT NULL
    """).fetchall()

    fixed = 0
    missing = 0

    for cid, artist, title, fpath in rows:
        if not fpath:
            continue
        local_path = Path(fpath.replace("/", os.sep))
        if local_path.exists():
            continue

        filename = local_path.name
        found = find_file(filename)

        if found:
            new_path = found.as_posix()
            print(f"FIX [{cid}] {artist or '?'} - {title}")
            print(f"     OLD: {fpath}")
            print(f"     NEW: {new_path}")
            if not DRY:
                con.execute(
                    "UPDATE djmdContent SET FolderPath=? WHERE ID=?",
                    (new_path, str(cid))
                )
            fixed += 1
        else:
            print(f"NOT FOUND [{cid}] {artist or '?'} - {title}")
            print(f"     {fpath}")
            missing += 1

    print(f"\nRutas corregidas: {fixed}")
    print(f"Archivos no encontrados: {missing}")

    if not DRY and fixed:
        con.commit()
        print("DB actualizada.")

    con.close()


if __name__ == "__main__":
    main()
