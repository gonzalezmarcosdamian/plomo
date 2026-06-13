import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3
con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

# Get all playlists with parent name
rows = con.execute("""
    SELECT p.ID, p.Name, p.ParentID, p.Attribute,
           COALESCE(par.Name, 'root') as ParentName
    FROM djmdPlaylist p
    LEFT JOIN djmdPlaylist par ON par.ID = p.ParentID
    WHERE p.rb_local_deleted=0
    ORDER BY p.ParentID, p.Name
""").fetchall()

for r in rows:
    attr = "FOLDER" if r[3] == 1 else "playlist"
    print(f"[{attr}] parent={r[4]:<20} | {r[1]}")
con.close()
