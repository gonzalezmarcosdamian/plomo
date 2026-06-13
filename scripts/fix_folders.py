import sys; sys.path.insert(0,'src')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from plomo import config
import sqlcipher3
con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute('PRAGMA key = ' + repr(config.SQLCIPHER_KEY))

root_row = con.execute("SELECT ID FROM djmdPlaylist WHERE Name='Pro DJ Library' AND rb_local_deleted=0 LIMIT 1").fetchone()
if not root_row:
    print("Pro DJ Library not found")
    con.close()
    exit()

root_id = root_row[0]
print("Pro DJ Library ID:", root_id)

folders = con.execute("SELECT ID, Name, ParentID FROM djmdPlaylist WHERE Name IN ('Por Estilo','Por Posicion de Set') AND rb_local_deleted=0").fetchall()
for fid, fname, parent in folders:
    print(fname, "-> current parent:", parent)
    if parent != root_id:
        con.execute("UPDATE djmdPlaylist SET ParentID=? WHERE ID=?", (root_id, fid))
        print("  Fixed -> Pro DJ Library")

con.commit()
con.close()
print("Done")
