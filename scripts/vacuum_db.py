"""Crea una copia limpia del DB via VACUUM INTO."""
import sys, shutil
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3

db_path = config.REKORDBOX_DB_PATH
clean_path = db_path.parent / "master.clean.db"

print(f"DB origen: {db_path}")
print(f"DB destino: {clean_path}")

con = sqlcipher3.connect(str(db_path))
con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
con.execute("PRAGMA journal_mode=WAL")

print("Ejecutando VACUUM INTO...")
try:
    con.execute(f"VACUUM INTO '{clean_path}'")
    print("  OK — copia limpia creada")

    # Verificar la copia
    con2 = sqlcipher3.connect(str(clean_path))
    con2.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    result = con2.execute("PRAGMA integrity_check").fetchone()
    tracks = con2.execute("SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0").fetchone()[0]
    print(f"  Integridad copia: {result[0]}")
    print(f"  Tracks en copia: {tracks}")
    con2.close()

    if result[0] == 'ok':
        # Backup del corrupto y reemplazar
        corrupt_backup = db_path.parent / "master.corrupt.db"
        shutil.copy2(db_path, corrupt_backup)
        shutil.copy2(clean_path, db_path)
        clean_path.unlink()
        print(f"\n  DB corrupto guardado en: master.corrupt.db")
        print(f"  DB limpio instalado como master.db")
    else:
        print("  La copia tampoco es perfecta pero puede ser usable")

except Exception as e:
    print(f"  VACUUM INTO error: {e}")

con.close()
print("Listo.")
