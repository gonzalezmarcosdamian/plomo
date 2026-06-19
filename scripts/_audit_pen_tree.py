"""Muestra cuantas playlists tiene cada track y cuales son las mas repetidas."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

# Estructura del arbol de playlists (carpetas y listas)
print("=== ARBOL DE PLAYLISTS ===\n")
folders = con.execute("""
    SELECT p.ID, p.Name, p.ParentID, p.Attribute,
           (SELECT COUNT(*) FROM djmdSongPlaylist sp WHERE sp.PlaylistID = p.ID) as tracks
    FROM djmdPlaylist p
    WHERE p.rb_local_deleted = 0
    ORDER BY p.ParentID, p.Seq
""").fetchall()

# Construir arbol
id_to = {r[0]: r for r in folders}
def print_tree(parent_id, indent=0):
    children = [r for r in folders if r[2] == parent_id]
    for r in children:
        pl_id, name, par, attr, tracks = r
        tag = '[F]' if attr == 1 else f'[{tracks}]'
        print(f"{'  ' * indent}{tag} {name}")
        print_tree(pl_id, indent + 1)

print_tree('root')

# Tracks que aparecen en mas playlists
print("\n\n=== TOP 20 TRACKS MAS REPETIDOS EN EL ARBOL ===\n")
rows = con.execute("""
    SELECT c.Title, a.Name, COUNT(DISTINCT sp.PlaylistID) as n_playlists,
           GROUP_CONCAT(p.Name, ' | ') as playlists
    FROM djmdSongPlaylist sp
    JOIN djmdContent c ON sp.ContentID = c.ID
    JOIN djmdArtist a ON c.ArtistID = a.ID
    JOIN djmdPlaylist p ON sp.PlaylistID = p.ID
    WHERE c.rb_local_deleted = 0 AND p.rb_local_deleted = 0
    GROUP BY sp.ContentID
    HAVING n_playlists > 3
    ORDER BY n_playlists DESC
    LIMIT 20
""").fetchall()

for title, artist, n, pls in rows:
    print(f"x{n}  {artist} - {title[:50]}")
    for pl in pls.split(' | ')[:6]:
        print(f"     · {pl[:60]}")
    print()

con.close()
