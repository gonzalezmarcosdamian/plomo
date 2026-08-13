"""
Elimina entradas duplicadas de djmdSongPlaylist donde el mismo titulo+artista
aparece con distintos ContentIDs en la misma playlist.
Conserva el ContentID mas alto (importacion mas reciente).
"""
import os, sys, shutil
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

DB_PATH = os.environ['REKORDBOX_DB_PATH']
KEY = os.environ.get('SQLCIPHER_KEY')

ts = datetime.now().strftime('%Y%m%d_%H%M')
bak = DB_PATH + f'.bak_{ts}'
shutil.copy2(DB_PATH, bak)
print(f"Backup: {bak}\n")

con = sqlcipher3.connect(DB_PATH)
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

# Encontrar grupos duplicados: misma playlist + mismo titulo + mismo artista
grupos = con.execute("""
    SELECT sp.PlaylistID, p.Name, c.Title, c.ArtistID, a.Name as artist,
           COUNT(DISTINCT sp.ContentID) as n,
           GROUP_CONCAT(sp.ContentID ORDER BY sp.ContentID DESC) as ids_desc
    FROM djmdSongPlaylist sp
    JOIN djmdPlaylist p ON sp.PlaylistID = p.ID
    JOIN djmdContent c ON sp.ContentID = c.ID
    JOIN djmdArtist a ON c.ArtistID = a.ID
    WHERE p.rb_local_deleted=0 AND c.rb_local_deleted=0
    GROUP BY sp.PlaylistID, c.Title, c.ArtistID
    HAVING n > 1
    ORDER BY p.Name, a.Name, c.Title
""").fetchall()

print(f"Grupos con duplicados: {len(grupos)}")
total_removed = 0

for pl_id, pl_name, title, artist_id, artist, n, ids_desc in grupos:
    ids = [int(x) for x in ids_desc.split(',')]
    keep = ids[0]   # el mas alto = importacion mas reciente
    remove = ids[1:]

    print(f"  [{pl_name}] {artist} - {title[:45]}")
    print(f"    keep={keep}  remove={remove}")

    for cid in remove:
        con.execute(
            "DELETE FROM djmdSongPlaylist WHERE PlaylistID=? AND ContentID=?",
            (pl_id, cid)
        )
    total_removed += len(remove)

con.commit()
print(f"\nTotal eliminados: {total_removed} entradas")

# Verificar que no queden duplicados
restantes = con.execute("""
    SELECT COUNT(*) FROM (
        SELECT sp.PlaylistID, c.Title, c.ArtistID, COUNT(DISTINCT sp.ContentID) as n
        FROM djmdSongPlaylist sp
        JOIN djmdContent c ON sp.ContentID = c.ID
        GROUP BY sp.PlaylistID, c.Title, c.ArtistID
        HAVING n > 1
    )
""").fetchone()[0]
print(f"Grupos duplicados restantes: {restantes}")
con.close()
