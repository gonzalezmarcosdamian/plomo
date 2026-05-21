"""
Nullea AnalysisDataPath de los tracks nuevos (Cumple del 20).
Con NULL, Rekordbox está forzado a generar los ANLZ frescos desde el audio
en lugar de buscar un UUID que no existe en el pen.
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3

# Todos los tracks del Cumple del 20 (pool de 29)
CUMPLE_IDS = [
    37723737, 205665671, 246333736, 206004569, 30038355, 88367438,
    191335971, 121667930, 39880106, 264841568, 180819583, 79146277,
    173432985, 24461486, 40162623, 230289841, 238425025, 223928742,
    167162931, 14192861, 227818551, 152689122, 5130344, 31403052,
    221819672, 62725563, 195885751, 250281940, 211255525
]

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with RekordboxDB() as db:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    fixed = 0
    for cid in CUMPLE_IDS:
        row = con.execute(
            "SELECT AnalysisDataPath FROM djmdContent WHERE ID=?", (str(cid),)
        ).fetchone()
        if not row:
            continue

        old_path = row[0]
        con.execute(
            "UPDATE djmdContent SET AnalysisDataPath=NULL, updated_at=? WHERE ID=?",
            (ts, str(cid))
        )
        fixed += 1
        print(f"  [{cid}] NULL ← {old_path}")

    con.commit()
    con.close()
    print(f"\nAnalysisDataPath nulleado en {fixed} tracks")

with RekordboxDB() as db2:
    print(f"DB integrity: {db2.integrity_check()}")

print("\nAhora:")
print("  1. Abrí Rekordbox (CON el pen conectado)")
print("  2. Abrí la playlist 'Cumple del 20 - Set'")
print("  3. Ctrl+A → click derecho → Analyze Track")
print("  4. Esperá que termine (genera ANLZ frescos en el pen)")
print("  5. Sync / Export de nuevo")
