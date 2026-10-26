"""Lee el export.pdb del pen drive para encontrar el set Pocho."""
import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

# El .pdb de Pioneer usa su propio formato binario
# Intentamos leer como SQLite sin clave
import sqlite3

pen_db = Path("D:/PIONEER/rekordbox/exportLibrary.db")

try:
    con = sqlite3.connect(str(pen_db))
    r = con.execute("PRAGMA integrity_check").fetchone()
    print("Integridad:", r[0])
    playlists = con.execute("SELECT ID, Name, ParentID FROM djmdPlaylist ORDER BY Name").fetchall()
    print(f"Playlists en pen: {len(playlists)}")
    for p in playlists:
        print(f"  {p[1][:60]}")
    con.close()
except Exception as e:
    print(f"Error sqlite3: {e}")

# Intentar export.pdb
try:
    pdb = Path("D:/PIONEER/rekordbox/export.pdb")
    print(f"\nexport.pdb: {pdb.stat().st_size} bytes")
    # Leer primeros bytes para identificar formato
    with open(pdb, 'rb') as f:
        header = f.read(16)
    print(f"Header hex: {header.hex()}")
except Exception as e:
    print(f"pdb error: {e}")
