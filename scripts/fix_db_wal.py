"""Consolida el WAL en el DB principal y verifica integridad."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

print("Checkpointing WAL...")
result = con.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
print(f"  WAL checkpoint: busy={result[0]}, log={result[1]}, checkpointed={result[2]}")

print("Verificando integridad...")
result = con.execute("PRAGMA integrity_check").fetchone()
print(f"  Integridad: {result[0]}")

total = con.execute("SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0").fetchone()[0]
print(f"  Tracks activos: {total}")

con.close()
print("Listo.")
