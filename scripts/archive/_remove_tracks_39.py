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

# --- Sacar de la playlist ---
fragments = ["balance perc tool", "epink"]

for frag in fragments:
    track = con.execute("""
        SELECT sp.ID, COALESCE(a.Name,'?'), c.Title
        FROM djmdSongPlaylist sp
        JOIN djmdContent c ON c.ID=sp.ContentID
        LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
        WHERE sp.PlaylistID=? AND LOWER(c.Title) LIKE ?
    """, (pl[0], f"%{frag}%")).fetchone()

    if track:
        print(f"[SET] Removiendo: {track[1]} - {track[2]}")
        con.execute("DELETE FROM djmdSongPlaylist WHERE ID=?", (track[0],))
    else:
        print(f"[SET] No encontrado en playlist: '{frag}'")

con.commit()

# --- Buscar Circle of Lights en libreria ---
print("\n--- Buscando Circle of Lights de Ignacio Hernandez ---")
results = con.execute("""
    SELECT c.ID, COALESCE(a.Name,'?') as artist, c.Title, c.BPM
    FROM djmdContent c
    LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
    WHERE LOWER(c.Title) LIKE '%circle%light%'
    AND c.rb_local_deleted=0
""").fetchall()

if results:
    for r in results:
        bpm = r[3]/100 if r[3] else 0
        print(f"  [{r[0]}] {r[1]} - {r[2]} ({bpm:.1f} BPM)")
else:
    print("  No encontrado en libreria")
    # Try broader search
    results2 = con.execute("""
        SELECT c.ID, COALESCE(a.Name,'?'), c.Title
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
        WHERE LOWER(a.Name) LIKE '%hernandez%' AND c.rb_local_deleted=0
    """).fetchall()
    if results2:
        print("  Tracks de Hernandez en libreria:")
        for r in results2:
            print(f"    {r[1]} - {r[2]}")
    else:
        print("  Ignacio Hernandez tampoco esta en la libreria")

# --- Listar tracks actuales en set 39 ---
print("\n--- Set 39 actualizado ---")
tracks = con.execute("""
    SELECT sp.TrackNo, COALESCE(a.Name,'?'), c.Title
    FROM djmdSongPlaylist sp
    JOIN djmdContent c ON c.ID=sp.ContentID
    LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
    WHERE sp.PlaylistID=?
    ORDER BY sp.TrackNo
""", (pl[0],)).fetchall()
print(f"  Total: {len(tracks)} tracks")

con.close()
