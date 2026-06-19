"""Encuentra tracks duplicados DENTRO de la misma playlist, incluso si son ContentIDs distintos (mismo archivo importado 2 veces)."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

# Caso 1: mismo ContentID aparece 2+ veces en la misma playlist
print("=== CASO 1: mismo ContentID, misma playlist ===")
rows = con.execute("""
    SELECT sp.PlaylistID, p.Name, sp.ContentID, c.Title, COUNT(*) as cnt
    FROM djmdSongPlaylist sp
    JOIN djmdPlaylist p ON sp.PlaylistID = p.ID
    JOIN djmdContent c ON sp.ContentID = c.ID
    WHERE p.rb_local_deleted=0 AND c.rb_local_deleted=0
    GROUP BY sp.PlaylistID, sp.ContentID
    HAVING cnt > 1
    ORDER BY p.Name
""").fetchall()
print(f"  {len(rows)} casos")
for pl_id, pl_name, ct_id, title, cnt in rows[:20]:
    print(f"  x{cnt} [{pl_name}] {title[:55]}")

# Caso 2: mismo titulo+artista (distinto ContentID) en la misma playlist
print("\n=== CASO 2: mismo titulo+artista con distinto ContentID en misma playlist ===")
rows2 = con.execute("""
    SELECT sp.PlaylistID, p.Name, c.Title, a.Name as artist,
           COUNT(DISTINCT sp.ContentID) as n_ids,
           GROUP_CONCAT(sp.ContentID) as ids
    FROM djmdSongPlaylist sp
    JOIN djmdPlaylist p ON sp.PlaylistID = p.ID
    JOIN djmdContent c ON sp.ContentID = c.ID
    JOIN djmdArtist a ON c.ArtistID = a.ID
    WHERE p.rb_local_deleted=0 AND c.rb_local_deleted=0
    GROUP BY sp.PlaylistID, c.Title, a.Name
    HAVING n_ids > 1
    ORDER BY p.Name
""").fetchall()
print(f"  {len(rows2)} casos")
for pl_id, pl_name, title, artist, n, ids in rows2[:30]:
    print(f"  x{n} [{pl_name}] {artist} - {title[:45]}  IDs:{ids}")

# Caso 3: tracks con mismo FolderPath (archivo duplicado en disco)
print("\n=== CASO 3: archivos duplicados en disco (mismo FolderPath) ===")
rows3 = con.execute("""
    SELECT c.FolderPath, c.Title, COUNT(*) as cnt,
           GROUP_CONCAT(c.ID) as ids
    FROM djmdContent c
    WHERE c.rb_local_deleted=0 AND c.FolderPath IS NOT NULL
    GROUP BY c.FolderPath
    HAVING cnt > 1
    LIMIT 20
""").fetchall()
print(f"  {len(rows3)} archivos duplicados")
for path, title, cnt, ids in rows3[:10]:
    print(f"  x{cnt} {title[:55]}  path:{path[-60:]}")

con.close()
