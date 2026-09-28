import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

pl = con.execute(
    "SELECT ID FROM djmdPlaylist WHERE Name LIKE '39.%' AND rb_local_deleted=0"
).fetchone()

row = con.execute("""
    SELECT sp.ID FROM djmdSongPlaylist sp
    JOIN djmdContent c ON c.ID=sp.ContentID
    WHERE sp.PlaylistID=? AND LOWER(c.Title) LIKE '%epika%'
""", (pl[0],)).fetchone()

if row:
    con.execute("DELETE FROM djmdSongPlaylist WHERE ID=?", (row[0],))
    con.commit()
    print("Epika removido del set 39. Set queda con 34 tracks.")
else:
    print("[warn] No encontrado")

con.close()
