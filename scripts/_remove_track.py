import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3
from datetime import datetime

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

# Find set 39
pl = con.execute(
    "SELECT ID, Name FROM djmdPlaylist WHERE Name LIKE '39.%' AND rb_local_deleted=0"
).fetchone()
print(f"Playlist: {pl[1]}")

# Find Max Cooper - Hope in the playlist
track = con.execute("""
    SELECT sp.ID, c.ID, a.Name, c.Title
    FROM djmdSongPlaylist sp
    JOIN djmdContent c ON c.ID=sp.ContentID
    LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
    WHERE sp.PlaylistID=? AND LOWER(c.Title) LIKE '%hope%'
    AND LOWER(COALESCE(a.Name,'')) LIKE '%cooper%'
""", (pl[0],)).fetchone()

if track:
    print(f"Removiendo: {track[2]} - {track[3]}")
    con.execute("DELETE FROM djmdSongPlaylist WHERE ID=?", (track[0],))
    con.commit()
    print("Listo.")
else:
    print("[warn] No encontrado en la playlist")

con.close()
