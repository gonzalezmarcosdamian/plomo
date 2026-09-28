"""Encuentra y reporta tracks duplicados en playlists (djmdSongPlaylist)."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

# Duplicados en djmdSongPlaylist: mismo ContentID en mismo PlaylistID mas de una vez
rows = con.execute("""
    SELECT sp.PlaylistID, p.Name, sp.ContentID, c.Title, a.Name as Artist,
           COUNT(*) as cnt
    FROM djmdSongPlaylist sp
    JOIN djmdPlaylist p ON sp.PlaylistID = p.ID
    JOIN djmdContent c ON sp.ContentID = c.ID
    JOIN djmdArtist a ON c.ArtistID = a.ID
    WHERE p.rb_local_deleted = 0 AND c.rb_local_deleted = 0
    GROUP BY sp.PlaylistID, sp.ContentID
    HAVING COUNT(*) > 1
    ORDER BY p.Name, a.Name, c.Title
""").fetchall()

total_extra = sum(r[5] - 1 for r in rows)
print(f"Playlists con duplicados: {len(set(r[0] for r in rows))}")
print(f"Tracks duplicados: {len(rows)} ({total_extra} entradas de mas)\n")

current_pl = None
for pl_id, pl_name, ct_id, title, artist, cnt in rows:
    if pl_id != current_pl:
        print(f"\n[{pl_name}]")
        current_pl = pl_id
    print(f"  x{cnt}  {artist} - {title[:55]}")

con.close()
