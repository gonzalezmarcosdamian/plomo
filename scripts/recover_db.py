"""
Recupera el DB copiando todas las tablas a un nuevo archivo limpio,
saltando los cues corruptos del rango alto de rowid.
"""
import sys, shutil, random, uuid as uuid_lib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3
from pathlib import Path
from datetime import datetime

src_path = config.REKORDBOX_DB_PATH
dst_path = src_path.parent / "master.recovered.db"

print(f"Fuente: {src_path}")
print(f"Destino: {dst_path}")

if dst_path.exists():
    dst_path.unlink()

src = sqlcipher3.connect(str(src_path))
src.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
src.execute("PRAGMA journal_mode=WAL")

dst = sqlcipher3.connect(str(dst_path))
dst.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
dst.execute("PRAGMA journal_mode=WAL")

# Copiar schema
print("\nCopiando schema...")
schema_rows = src.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL ORDER BY rootpage"
).fetchall()

for name, sql in schema_rows:
    try:
        dst.execute(sql)
        print(f"  Table: {name}")
    except Exception as e:
        print(f"  Skip {name}: {e}")

# Copiar índices
idx_rows = src.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
).fetchall()
for name, sql in idx_rows:
    try:
        dst.execute(sql)
    except Exception:
        pass

dst.commit()

# Tablas a copiar (todas menos djmdCue que la copiamos con cuidado)
TABLES = [
    "djmdContent", "djmdArtist", "djmdAlbum", "djmdGenre", "djmdKey",
    "djmdLabel", "djmdColor", "djmdPlaylist", "djmdSongPlaylist",
    "djmdMixerParam", "djmdRelatedTracks", "djmdSongHistory",
    "djmdHotCueBanklist", "djmdHotCueBanklistEntry",
    "djmdProperty", "djmdSampler", "djmdSamplerTrack",
    "djmdSort", "djmdTagList",
]

print("\nCopiando tablas principales...")
for table in TABLES:
    try:
        rows = src.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print(f"  {table}: vacia")
            continue
        cols = len(rows[0])
        placeholders = ",".join(["?"] * cols)
        dst.executemany(f"INSERT OR IGNORE INTO {table} VALUES ({placeholders})", rows)
        dst.commit()
        print(f"  {table}: {len(rows)} filas")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")

# djmdCue: copiar solo hasta rowid ~50000 (antes del rango corrupto)
print("\nCopiando djmdCue (evitando rango corrupto)...")
cues_ok = 0
cues_skip = 0
try:
    # Intentar leer por lotes pequenos, parar al llegar a paginas corruptas
    batch_size = 500
    offset = 0
    while True:
        try:
            rows = src.execute(
                f"SELECT * FROM djmdCue WHERE rb_local_deleted=0 LIMIT {batch_size} OFFSET {offset}"
            ).fetchall()
            if not rows:
                break
            cols = len(rows[0])
            placeholders = ",".join(["?"] * cols)
            dst.executemany(f"INSERT OR IGNORE INTO djmdCue VALUES ({placeholders})", rows)
            dst.commit()
            cues_ok += len(rows)
            offset += batch_size
            if offset % 5000 == 0:
                print(f"    ...{offset} cues copiados")
        except Exception as e:
            print(f"    Parado en offset {offset}: {e}")
            cues_skip = offset
            break
except Exception as e:
    print(f"  djmdCue error: {e}")

print(f"  djmdCue: {cues_ok} OK, {cues_skip} saltados")

src.close()

# Verificar
print("\nVerificando DB recuperado...")
check = sqlcipher3.connect(str(dst_path))
check.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
result = check.execute("PRAGMA integrity_check").fetchone()
tracks = check.execute("SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0").fetchone()[0]
playlists = check.execute("SELECT COUNT(*) FROM djmdPlaylist WHERE rb_local_deleted=0 AND Attribute=0").fetchone()[0]
cues_total = check.execute("SELECT COUNT(*) FROM djmdCue WHERE rb_local_deleted=0").fetchone()[0]
check.close()

print(f"  Integridad: {result[0]}")
print(f"  Tracks: {tracks} | Playlists: {playlists} | Cues: {cues_total}")

if result[0] == 'ok':
    backup_orig = src_path.parent / "master.before_recovery.db"
    shutil.copy2(src_path, backup_orig)
    shutil.copy2(dst_path, src_path)
    dst_path.unlink()
    print(f"\nDB recuperado instalado como master.db")
    print(f"Original guardado en: master.before_recovery.db")
else:
    print(f"\nDB recuperado guardado en: {dst_path.name}")
    print("Revisar antes de instalar.")
