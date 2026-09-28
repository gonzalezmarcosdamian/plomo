"""ONE-OFF DE LA CORRUPCION DE JUNIO 2026. NO CORRER. Archivado el 2026-09-27.

Borra cues por rowid: `DELETE FROM djmdCue WHERE rowid > 50000`, y si eso falla
reintenta con 40000, 30000, 20000 y 10000 — o sea que el ultimo intento borra la
tabla entera.

El 50000 se calibro cuando la biblioteca era un tercio de la de hoy. Medido
contra la base actual: `djmdCue` tiene 124.995 filas y el corte de 50000
borraria 102.388, el 81.9% de los cues de la coleccion. Los fallbacks llegan
al 100%.

Y no hay forma de mirar antes lo que va a hacer: no tiene `--dry`, no tiene
argparse y no tiene `if __name__ == "__main__"`. La conexion y el DELETE estan a
nivel de modulo, asi que IMPORTARLO alcanza para que borre.

Queda archivado y no borrado porque es el registro de como se salio de esa
corrupcion. Para diagnosticar la base estan `check_db.py` y `db_audit.py`; para
repararla, `repair_db.py`, `recover_db.py`, `fix_db_wal.py` y `vacuum_db.py`, que
son las cuatro estrategias que documenta el agente `tecnico`.
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
