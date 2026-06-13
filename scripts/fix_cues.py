"""
Elimina los cues corruptos (rowid > 50000) del djmdCue directamente.
Esto permite que RB abra sin crashear al leer cues invalidos.
Los tracks nuevos pierden sus cue points pero los viejos los conservan.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

# Contar cues actuales (puede fallar en rango corrupto - OK)
print("Intentando contar cues actuales...")
try:
    total = con.execute("SELECT COUNT(*) FROM djmdCue LIMIT 1 OFFSET 50000").fetchone()
    print(f"  Cues hasta row 50000+: {total}")
except Exception as e:
    print(f"  Count error (esperado): {e}")

# Eliminar cues por rowid > 50000 (los corruptos son de pyrekordbox esta sesion)
print("\nEliminando cues corruptos (rowid > 50000)...")
try:
    con.execute("DELETE FROM djmdCue WHERE rowid > 50000")
    con.commit()
    print("  DELETE OK")
except Exception as e:
    print(f"  DELETE error: {e}")
    # Intentar con rowid mas bajo
    for cutoff in [40000, 30000, 20000, 10000]:
        try:
            print(f"  Intentando rowid > {cutoff}...")
            con.execute(f"DELETE FROM djmdCue WHERE rowid > {cutoff}")
            con.commit()
            print(f"  DELETE OK con cutoff {cutoff}")
            break
        except Exception as e2:
            print(f"  Error: {e2}")

# Contar lo que queda
print("\nContando cues restantes...")
try:
    remaining = con.execute("SELECT COUNT(*) FROM djmdCue WHERE rb_local_deleted=0").fetchone()[0]
    print(f"  Cues activos restantes: {remaining}")
except Exception as e:
    print(f"  Count error: {e}")

con.close()
print("\nListo. Intentá abrir Rekordbox.")
