import sys; sys.path.insert(0,'src')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from plomo import config
import sqlcipher3
DEAD = config.REKORDBOX_DB_PATH.parent / "master.dead.db"
con = sqlcipher3.connect(str(DEAD))
con.execute('PRAGMA key = ' + repr(config.SQLCIPHER_KEY))
rows = con.execute("SELECT ID, Name, Attribute FROM djmdPlaylist WHERE rb_local_deleted=0 ORDER BY Name").fetchall()
print("TODAS las playlists en master.dead.db:")
for r in rows:
    print(f"  {'FOLDER' if r[2]==1 else 'list  '} | {r[1]}")
con.close()
