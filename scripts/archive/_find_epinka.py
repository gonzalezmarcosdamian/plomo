import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

pl = con.execute(
    "SELECT ID, Name FROM djmdPlaylist WHERE Name LIKE '39.%' AND rb_local_deleted=0"
).fetchone()
print(f"Playlist: {pl[1]}\n")

# Buscar en set 39 con variantes de "epinka"
print("--- Tracks en set 39 con 'pink' en titulo o artista ---")
results = con.execute("""
    SELECT sp.ID, sp.TrackNo, COALESCE(a.Name,'?'), c.Title
    FROM djmdSongPlaylist sp
    JOIN djmdContent c ON c.ID=sp.ContentID
    LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
    WHERE sp.PlaylistID=?
    AND (LOWER(c.Title) LIKE '%pink%' OR LOWER(a.Name) LIKE '%pink%'
         OR LOWER(c.Title) LIKE '%epink%' OR LOWER(a.Name) LIKE '%epink%')
    ORDER BY sp.TrackNo
""", (pl[0],)).fetchall()

if results:
    for r in results:
        print(f"  [{r[0]}] #{r[1]} {r[2]} - {r[3]}")
else:
    print("  Ninguno encontrado con 'pink'")

# Lista completa para ayudar al usuario a identificar
print("\n--- TODOS los tracks del set 39 ---")
all_tracks = con.execute("""
    SELECT sp.ID, sp.TrackNo, COALESCE(a.Name,'?'), c.Title
    FROM djmdSongPlaylist sp
    JOIN djmdContent c ON c.ID=sp.ContentID
    LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
    WHERE sp.PlaylistID=?
    ORDER BY sp.TrackNo
""", (pl[0],)).fetchall()

for r in all_tracks:
    print(f"  #{r[1]:02d} {r[2]} - {r[3]}")

con.close()
