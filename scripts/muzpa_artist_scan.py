"""
Busca todos los tracks disponibles en Muzpa por artista.
Filtra los que ya estan en la libreria.

Uso:
  python scripts/muzpa_artist_scan.py "Gai Barone" "Cary Crank" ...
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from plomo import config
import sqlcipher3

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from muzpa_download import get_session, search
from plomo.matching import clave


def indice_biblioteca(con) -> set[str]:
    """Claves artista+titulo de todo lo que ya esta en la biblioteca.

    Antes esto era un LIKE de los primeros 20 caracteres del `filename` de
    Muzpa contra `djmdContent.Title`. El filename trae "Artista - Titulo" y el
    Title guarda solo el titulo, asi que "Cendryma - Typical U" no matcheaba
    nunca con "Typical Use (Original Mix)": el scan reportaba como nuevos
    tracks con 10 reproducciones. Ahora se cruza con la misma clave que usa el
    resto del proyecto, que ademas conserva el remixer.
    """
    return {
        clave(a or "", t or "")
        for a, t in con.execute(
            """SELECT COALESCE(ar.Name, ''), COALESCE(c.Title, '')
               FROM djmdContent c LEFT JOIN djmdArtist ar ON ar.ID = c.ArtistID
               WHERE c.rb_local_deleted = 0""")
    }


def _partes(fullname: str) -> tuple[str, str]:
    """Separa 'Artista - Titulo' como lo entrega Muzpa."""
    if " - " in fullname:
        a, t = fullname.split(" - ", 1)
        return a.strip(), t.strip()
    return "", fullname.strip()


def main():
    artists = sys.argv[1:]
    if not artists:
        print("Uso: muzpa_artist_scan.py 'Artista 1' 'Artista 2' ...")
        return

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

    s = get_session()
    if not s:
        return

    biblioteca = indice_biblioteca(con)
    all_available = []

    for artist in artists:
        results = search(s, artist)
        if not results:
            print(f"\n{artist}: no encontrado en Muzpa")
            continue

        new_tracks = []
        for t in results:
            fname = t.get("fullname", "")
            title = t.get("filename", "").replace(".mp3", "")
            bpm = t.get("bpm") or "?"
            key = t.get("key") or "?"

            if artist.lower() not in fname.lower():
                continue

            ar, ti = _partes(fname or title)
            if clave(ar, ti) in biblioteca:
                continue

            new_tracks.append(t)
            all_available.append({"artist": artist, "track": t})

        if new_tracks:
            print(f"\n{artist} — {len(new_tracks)} nuevos en Muzpa:")
            for t in new_tracks:
                print(f"  BPM={str(t.get('bpm') or '?'):>4} Key={str(t.get('key') or '?'):<6} | {t['fullname'][:70]}")
        else:
            print(f"\n{artist}: sin tracks nuevos en Muzpa")

    con.close()
    print(f"\nTotal disponibles: {len(all_available)}")


if __name__ == "__main__":
    main()
