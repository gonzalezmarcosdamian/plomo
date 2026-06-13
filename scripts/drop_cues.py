"""
DROP TABLE djmdCue y recrear vacia.
SQLite puede hacer DROP sin leer el contenido (solo borra la referencia).
Los track data, playlists y energia se conservan.
Los cue points se pierden pero se pueden reaplicar con post_import.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

# Obtener schema de djmdCue
print("Obteniendo schema de djmdCue...")
schema = con.execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name='djmdCue'"
).fetchone()

if not schema:
    print("ERROR: No se encontro djmdCue en sqlite_master")
    con.close()
    exit(1)

cue_schema = schema[0]
print(f"  Schema encontrado ({len(cue_schema)} chars)")

# Obtener indices de djmdCue
print("Obteniendo indices de djmdCue...")
idx_rows = con.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='djmdCue' AND sql IS NOT NULL"
).fetchall()
print(f"  {len(idx_rows)} indices encontrados")

# DROP TABLE (no necesita leer el contenido)
print("\nDropeando djmdCue...")
try:
    con.execute("DROP TABLE IF EXISTS djmdCue")
    con.commit()
    print("  DROP OK")
except Exception as e:
    print(f"  DROP error: {e}")
    con.close()
    exit(1)

# Recrear tabla vacia
print("Recreando djmdCue vacia...")
try:
    con.execute(cue_schema)
    con.commit()
    print("  CREATE TABLE OK")
except Exception as e:
    print(f"  CREATE error: {e}")

# Recrear indices
print("Recreando indices...")
for idx_name, idx_sql in idx_rows:
    try:
        con.execute(idx_sql)
        con.commit()
        print(f"  Index {idx_name}: OK")
    except Exception as e:
        print(f"  Index {idx_name}: {e}")

# Verificar
print("\nVerificando...")
try:
    count = con.execute("SELECT COUNT(*) FROM djmdCue").fetchone()[0]
    print(f"  djmdCue rows: {count} (debe ser 0)")
    tracks = con.execute("SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0").fetchone()[0]
    print(f"  Tracks activos: {tracks}")
    playlists = con.execute("SELECT COUNT(*) FROM djmdSongPlaylist WHERE rb_local_deleted=0").fetchone()[0]
    print(f"  Playlist entries: {playlists}")
except Exception as e:
    print(f"  Verify error: {e}")

con.close()
print("\nListo. Intentá abrir Rekordbox — deberia abrir sin crashear.")
print("Los cue points se reaplicaran con post_import.py despues.")
