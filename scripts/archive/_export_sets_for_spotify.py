"""Lee los tracks de los sets 41-45 (Para Probar) en orden desde el DB."""
import os, json
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

DB_PATH = os.environ['REKORDBOX_DB_PATH']
KEY = os.environ.get('SQLCIPHER_KEY')
PARA_PROBAR_ID = '1975667623'  # Sets Armados root

con = sqlcipher3.connect(DB_PATH)
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

# IDs directos de los sets 41-45
SET_IDS = [
    ('2826743819', '41. Dulce Progresivo — Loveland Style — 2026-06-13'),
    ('1524652779', '42. Emi & Kamilo — Colorido Progresivo — 2026-06-13'),
    ('3487987428', '43. Maze 28 + Cendryma — Nuevo Prog — 2026-06-13'),
    ('1811340937', '44. Dowden + Guy J — Progressive Profundo — 2026-06-13'),
    ('3007468625', '45. Tom Pavicich + Durante — Prog Argentino — 2026-06-13'),
]
playlists = [(id_, name, i) for i, (id_, name) in enumerate(SET_IDS)]

result = []
for pl_id, pl_name, seq in playlists:
    tracks = con.execute("""
        SELECT c.Title, a.Name, c.BPM, c.Commnt, sp.TrackNo
        FROM djmdSongPlaylist sp
        JOIN djmdContent c ON sp.ContentID = c.ID
        JOIN djmdArtist a ON c.ArtistID = a.ID
        WHERE sp.PlaylistID=? AND sp.rb_local_deleted=0 AND c.rb_local_deleted=0
        ORDER BY sp.TrackNo
    """, (pl_id,)).fetchall()

    entry = {
        "id": pl_id,
        "name": pl_name,
        "tracks": [{"title": t, "artist": a, "bpm": b} for t, a, b, _, _ in tracks]
    }
    result.append(entry)
    print(f"\n{pl_name} ({len(tracks)} tracks):")
    for i, (t, a, b, k, no) in enumerate(tracks, 1):
        print(f"  {i:2}. {a} - {t}")

con.close()

with open("data/sets_41_45_for_spotify.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("\nGuardado en data/sets_41_45_for_spotify.json")
