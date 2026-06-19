"""Muestra los 33 grupos restantes para entender por qué no se limpiaron."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

rows = con.execute("""
    SELECT sp.PlaylistID, p.Name, c.Title, c.ArtistID, a.Name,
           COUNT(DISTINCT sp.ContentID) as n,
           GROUP_CONCAT(sp.ContentID) as ids,
           p.rb_local_deleted as pl_del,
           c.rb_local_deleted as c_del
    FROM djmdSongPlaylist sp
    JOIN djmdPlaylist p ON sp.PlaylistID = p.ID
    JOIN djmdContent c ON sp.ContentID = c.ID
    JOIN djmdArtist a ON c.ArtistID = a.ID
    GROUP BY sp.PlaylistID, c.Title, c.ArtistID
    HAVING n > 1
    ORDER BY p.Name
""").fetchall()

print(f"Grupos restantes: {len(rows)}\n")
for pl_id, pl_name, title, art_id, artist, n, ids, pl_del, c_del in rows:
    flag = []
    if pl_del: flag.append("PL_DEL")
    if c_del:  flag.append("CT_DEL")
    print(f"  x{n} [{pl_name}] {artist} - {title[:45]}  {' '.join(flag) or 'ACTIVO'}  ids={ids}")

con.close()
