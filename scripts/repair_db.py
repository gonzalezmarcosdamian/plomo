"""Intenta reparar el DB reconstruyendo los indices corruptos."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
con.execute("PRAGMA journal_mode=WAL")

print("Reconstruyendo indices (REINDEX)...")
try:
    con.execute("REINDEX djmdCue")
    print("  djmdCue: OK")
except Exception as e:
    print(f"  djmdCue error: {e}")

try:
    con.execute("REINDEX")
    print("  REINDEX global: OK")
except Exception as e:
    print(f"  REINDEX global error: {e}")

print("\nVerificando integridad post-repair...")
results = con.execute("PRAGMA integrity_check").fetchall()
if len(results) == 1 and results[0][0] == 'ok':
    print("  Integridad: OK")
else:
    print(f"  Errores: {len(results)}")
    for r in results[:5]:
        print(f"    {r[0]}")

total = con.execute("SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0").fetchone()[0]
cues = con.execute("SELECT COUNT(*) FROM djmdCue WHERE rb_local_deleted=0").fetchone()[0]
print(f"\n  Tracks: {total} | Cues: {cues}")

con.close()
print("Listo.")
