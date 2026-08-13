"""Elimina entradas duplicadas de djmdSongPlaylist. Conserva la de menor ID."""
import os, sys, shutil
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

DB_PATH = os.environ['REKORDBOX_DB_PATH']
KEY = os.environ.get('SQLCIPHER_KEY')

# Backup
ts = datetime.now().strftime('%Y%m%d_%H%M')
bak = DB_PATH + f'.bak_{ts}'
shutil.copy2(DB_PATH, bak)
print(f"Backup: {bak}")

con = sqlcipher3.connect(DB_PATH)
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

# Encontrar IDs a eliminar (duplicados, conserva el menor ID por grupo)
to_delete = con.execute("""
    SELECT sp.ID, p.Name, c.Title
    FROM djmdSongPlaylist sp
    JOIN djmdPlaylist p ON sp.PlaylistID = p.ID
    JOIN djmdContent c ON sp.ContentID = c.ID
    WHERE sp.ID NOT IN (
        SELECT MIN(ID)
        FROM djmdSongPlaylist
        GROUP BY PlaylistID, ContentID
    )
    AND p.rb_local_deleted = 0
    AND c.rb_local_deleted = 0
    ORDER BY p.Name
""").fetchall()

print(f"\nEliminando {len(to_delete)} entradas duplicadas:")
for row_id, pl_name, title in to_delete:
    print(f"  [{pl_name}] {title[:55]}")
    con.execute("DELETE FROM djmdSongPlaylist WHERE ID=?", (row_id,))

con.commit()
print(f"\nOK — {len(to_delete)} duplicados eliminados.")

# Verificar
remaining = con.execute("""
    SELECT COUNT(*) FROM (
        SELECT PlaylistID, ContentID, COUNT(*) as cnt
        FROM djmdSongPlaylist
        GROUP BY PlaylistID, ContentID
        HAVING cnt > 1
    )
""").fetchone()[0]
print(f"Duplicados restantes: {remaining}")
con.close()
