import sys; sys.path.insert(0,'src')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from plomo import config
import sqlcipher3
con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute('PRAGMA key = ' + repr(config.SQLCIPHER_KEY))
rows = con.execute("SELECT ID, Name, Attribute, ParentID FROM djmdPlaylist WHERE rb_local_deleted=0 ORDER BY Name LIMIT 30").fetchall()
for r in rows:
    typ = "FOLDER" if r[2]==1 else "playlist"
    print(f"  [{r[2]}] {r[1][:50]} | parent={r[3]}")
con.close()
