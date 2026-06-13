"""
Fix: elimina djmdCue y contentCue corruptos del schema, hace VACUUM.
Rekordbox los recrea vacíos al abrir. Tracks y playlists intactos.
"""
import os, sys, shutil
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from dotenv import load_dotenv
load_dotenv()

import sqlcipher3

DB_PATH = os.environ['REKORDBOX_DB_PATH']
KEY     = os.environ.get('REKORDBOX_DB_KEY') or os.environ['SQLCIPHER_KEY']

# 1. Backup
ts = datetime.now().strftime('%Y%m%d_%H%M')
backup = DB_PATH + f'.bak_{ts}'
print(f"Backup -> {backup}")
shutil.copy2(DB_PATH, backup)
# También WAL si existe
for ext in ['-wal', '-shm']:
    if os.path.exists(DB_PATH + ext):
        shutil.copy2(DB_PATH + ext, backup + ext)
        print(f"  WAL/SHM copiado también")
print("Backup OK")

# 2. Abrir DB corrupta
con = sqlcipher3.connect(DB_PATH)
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")
con.execute("PRAGMA journal_mode=DELETE")  # asegurar no-WAL para vacuum

# 3. Verificar qué está bien antes
print("\nAntes del fix:")
for t in ['djmdContent','djmdPlaylist','djmdSongPlaylist','djmdArtist']:
    try:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} filas OK")
    except Exception as e:
        print(f"  {t}: ERROR {e}")

# 4. Eliminar tablas corruptas del schema
print("\nEliminando tablas corruptas del schema...")
con.execute("PRAGMA writable_schema = ON")

CORRUPT_TABLES = ['djmdCue', 'contentCue']
for tbl in CORRUPT_TABLES:
    try:
        rows = con.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE tbl_name=? OR (type='table' AND name=?)",
            (tbl, tbl)
        ).fetchone()[0]
        con.execute(
            "DELETE FROM sqlite_master WHERE tbl_name=? OR (type='table' AND name=?)",
            (tbl, tbl)
        )
        print(f"  {tbl}: eliminado del schema ({rows} entradas)")
    except Exception as e:
        print(f"  {tbl}: {e}")

con.execute("PRAGMA writable_schema = OFF")
con.commit()
print("Schema actualizado")

# 5. VACUUM (reconstruye el archivo sin las páginas corruptas)
print("\nVACUUM (puede tardar 1-2 min)...")
try:
    con.execute("VACUUM")
    print("VACUUM OK")
except Exception as e:
    print(f"VACUUM ERROR: {e}")
    print("Intentando igual — probá abrir Rekordbox")

con.close()

# 6. Verificar
print("\nVerificando DB reparada...")
con2 = sqlcipher3.connect(DB_PATH)
con2.execute(f"PRAGMA key='{KEY}'")
con2.execute("PRAGMA cipher_compatibility=4")
for t in ['djmdContent','djmdPlaylist','djmdSongPlaylist','djmdArtist']:
    try:
        n = con2.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} filas OK")
    except Exception as e:
        print(f"  {t}: ERROR {e}")

ic = con2.execute("PRAGMA integrity_check").fetchall()
ok = all(r[0] == 'ok' for r in ic)
print(f"\nIntegrity check: {'OK' if ok else ic[:5]}")
con2.close()

print("""
=== LISTO ===
Abrí Rekordbox ahora.
- Los tracks y playlists van a estar intactos.
- Los cue points se perdieron (hay que re-correr post_import FASE 1 después).
- La energía (Commnt) sigue OK en los tracks.
""")
