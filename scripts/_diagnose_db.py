"""Diagnóstico rápido: qué tablas están OK y cuál es Tree 29."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from dotenv import load_dotenv
load_dotenv()

import sqlcipher3
import struct

DB_PATH = os.environ['REKORDBOX_DB_PATH']
DB_KEY  = os.environ.get('REKORDBOX_DB_KEY') or os.environ.get('SQLCIPHER_KEY')

con = sqlcipher3.connect(DB_PATH)
con.execute(f"PRAGMA key='{DB_KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

# Identificar Tree 29 (root page)
print("=== sqlite_master B-trees (rootpage) ===")
try:
    rows = con.execute(
        "SELECT type, name, rootpage FROM sqlite_master ORDER BY rootpage"
    ).fetchall()
    for r in rows:
        marker = " *** TREE 29 ***" if r[2] == 29 else ""
        print(f"  rootpage={r[2]:4d}  {r[0]:6s}  {r[1]}{marker}")
except Exception as e:
    print(f"  ERROR sqlite_master: {e}")

# Chequear tablas críticas
tables = [
    ("djmdContent",      "SELECT COUNT(*) FROM djmdContent"),
    ("djmdCue",          "SELECT COUNT(*) FROM djmdCue"),
    ("djmdPlaylist",     "SELECT COUNT(*) FROM djmdPlaylist"),
    ("djmdSongPlaylist", "SELECT COUNT(*) FROM djmdSongPlaylist"),
    ("djmdArtist",       "SELECT COUNT(*) FROM djmdArtist"),
]
print("\n=== Conteo de filas por tabla ===")
for name, sql in tables:
    try:
        n = con.execute(sql).fetchone()[0]
        print(f"  {name:25s} {n:6d} filas  OK")
    except Exception as e:
        print(f"  {name:25s} ERROR: {e}")

# Ver si los cues son legibles
print("\n=== Muestra djmdCue (primeros 5) ===")
try:
    rows = con.execute(
        "SELECT ID, ContentID, Kind, Seq FROM djmdCue LIMIT 5"
    ).fetchall()
    for r in rows:
        print(f"  {r}")
except Exception as e:
    print(f"  ERROR: {e}")

con.close()
print("\nDiagnóstico completo.")
