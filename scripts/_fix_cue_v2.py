"""
Fix v2: no cambia journal_mode antes del fix (evita checkpoint del WAL corrupto).
"""
import os, sys, shutil
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

DB_PATH = os.environ['REKORDBOX_DB_PATH']
KEY = os.environ.get('REKORDBOX_DB_KEY') or os.environ['SQLCIPHER_KEY']

# Backup
ts = datetime.now().strftime('%Y%m%d_%H%M')
backup = DB_PATH + f'.bak_{ts}'
shutil.copy2(DB_PATH, backup)
for ext in ['-wal', '-shm']:
    if os.path.exists(DB_PATH + ext):
        shutil.copy2(DB_PATH + ext, backup + ext)
print(f"Backup: {backup}")

con = sqlcipher3.connect(DB_PATH)
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")
# NO cambiamos journal_mode — dejamos WAL como está

# Verificar tablas importantes primero
for t in ['djmdContent', 'djmdPlaylist', 'djmdSongPlaylist']:
    try:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} OK")
    except Exception as e:
        print(f"  {t}: ERROR {e}")

# Eliminar tablas corruptas del schema
print("\nEliminando cue tables del schema...")
con.execute("PRAGMA writable_schema = ON")
for tbl in ['djmdCue', 'contentCue']:
    try:
        con.execute("DELETE FROM sqlite_master WHERE tbl_name=? OR (type='table' AND name=?)", (tbl, tbl))
        print(f"  {tbl}: eliminado")
    except Exception as e:
        print(f"  {tbl}: {e}")

con.execute("PRAGMA writable_schema = OFF")
con.commit()
print("Commit OK")

# VACUUM sin haber cambiado journal_mode
print("\nVACUUM...")
try:
    con.execute("VACUUM")
    print("VACUUM OK")
except Exception as e:
    print(f"VACUUM: {e} (puede ser OK igual)")

con.close()

# Verificar con nueva conexion
print("\nVerificando...")
con2 = sqlcipher3.connect(DB_PATH)
con2.execute(f"PRAGMA key='{KEY}'")
con2.execute("PRAGMA cipher_compatibility=4")
for t in ['djmdContent', 'djmdPlaylist', 'djmdSongPlaylist']:
    try:
        n = con2.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} OK")
    except Exception as e:
        print(f"  {t}: ERROR {e}")

ic = con2.execute("PRAGMA integrity_check").fetchall()
ok = all(r[0] == 'ok' for r in ic)
print(f"\nIntegrity: {'OK' if ok else 'FALLO — ver abajo'}")
if not ok:
    for r in ic[:10]:
        print(f"  {r[0]}")
con2.close()
