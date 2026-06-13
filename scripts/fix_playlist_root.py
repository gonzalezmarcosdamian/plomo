"""Corrige ParentID de carpetas raiz para que RB las muestre."""
import sys; sys.path.insert(0,'src')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from plomo import config
import sqlcipher3
con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute('PRAGMA key = ' + repr(config.SQLCIPHER_KEY))

# RekordBox usa 'root' como ParentID para carpetas de primer nivel
rows = con.execute("SELECT ID, Name, ParentID FROM djmdPlaylist WHERE rb_local_deleted=0 AND (ParentID IS NULL OR ParentID='None')").fetchall()
print(f"Playlists con ParentID null: {len(rows)}")
for r in rows:
    print(f"  {r[1][:50]} | parent={r[2]}")

# Las carpetas de primer nivel (Pro DJ Library) deben tener ParentID='root'
# Las playlists/carpetas dentro de Pro DJ Library ya tienen el ID correcto
pro_dj = con.execute("SELECT ID FROM djmdPlaylist WHERE Name='Pro DJ Library' AND rb_local_deleted=0 LIMIT 1").fetchone()
if pro_dj:
    con.execute("UPDATE djmdPlaylist SET ParentID='root' WHERE ID=?", (pro_dj[0],))
    print(f"\nPro DJ Library actualizado -> ParentID='root'")

# Sets que pueden estar sueltos a nivel raiz
con.execute("UPDATE djmdPlaylist SET ParentID='root' WHERE (ParentID IS NULL OR ParentID='None') AND rb_local_deleted=0 AND Name != 'Pro DJ Library'")

con.commit()

# Verificar
rows2 = con.execute("SELECT ID, Name, ParentID FROM djmdPlaylist WHERE rb_local_deleted=0 AND ParentID='root'").fetchall()
print(f"\nPlaylists con ParentID='root': {len(rows2)}")
for r in rows2:
    print(f"  {r[1][:50]}")

con.close()
print("\nListo. Reabri RekordBox.")
