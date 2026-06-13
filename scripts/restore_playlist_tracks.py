"""
Restaura los tracks de cada playlist mapeando ContentIDs por FolderPath.
Los IDs cambiaron cuando RB recreó la librería, pero los paths son los mismos.
"""
import sys, random, uuid as uuid_lib
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3
from datetime import datetime

DEAD_DB = config.REKORDBOX_DB_PATH.parent / "master.dead.db"
LIVE_DB = config.REKORDBOX_DB_PATH

def connect(path):
    con = sqlcipher3.connect(str(path))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con

def safe_id():
    return str(random.randint(1500000000, 4000000000))

dead = connect(DEAD_DB)
live = connect(LIVE_DB)
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("Construyendo mapa de ContentIDs (old -> new) por FolderPath...")
# Cargar todos los tracks del live DB indexados por FolderPath normalizado
live_tracks = {}
for cid, fpath in live.execute("SELECT ID, FolderPath FROM djmdContent WHERE rb_local_deleted=0 AND FolderPath IS NOT NULL").fetchall():
    if fpath:
        key = fpath.lower().replace("\\", "/").strip()
        live_tracks[key] = str(cid)

print(f"  {len(live_tracks)} tracks en live DB")

# Leer tracks del dead DB y construir mapa
dead_to_live = {}
dead_tracks = dead.execute("SELECT ID, FolderPath FROM djmdContent WHERE rb_local_deleted=0 AND FolderPath IS NOT NULL").fetchall()
matched = 0
for old_cid, fpath in dead_tracks:
    if not fpath:
        continue
    key = fpath.lower().replace("\\", "/").strip()
    if key in live_tracks:
        dead_to_live[str(old_cid)] = live_tracks[key]
        matched += 1

print(f"  {matched}/{len(dead_tracks)} tracks mapeados")

# Mapeo de playlist IDs (dead -> live) por nombre
print("\nMapeando playlists...")
pl_map = {}
for old_id, name in dead.execute("SELECT ID, Name FROM djmdPlaylist WHERE rb_local_deleted=0").fetchall():
    row = live.execute("SELECT ID FROM djmdPlaylist WHERE Name=? AND rb_local_deleted=0 LIMIT 1", (name,)).fetchone()
    if row:
        pl_map[str(old_id)] = row[0]

print(f"  {len(pl_map)} playlists mapeadas")

# Restaurar tracks en cada playlist
print("\nRestaurando tracks...")
total_added = 0
max_usn = live.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0

playlists = dead.execute(
    "SELECT ID, Name FROM djmdPlaylist WHERE rb_local_deleted=0 AND Attribute=0"
).fetchall()

for old_pl_id, pl_name in playlists:
    new_pl_id = pl_map.get(str(old_pl_id))
    if not new_pl_id:
        continue

    # Skip si ya tiene tracks
    existing = live.execute(
        "SELECT COUNT(*) FROM djmdSongPlaylist WHERE PlaylistID=? AND rb_local_deleted=0",
        (new_pl_id,)
    ).fetchone()[0]
    if existing > 0:
        continue

    # Obtener tracks del dead DB
    try:
        tracks = dead.execute(
            "SELECT ContentID, TrackNo FROM djmdSongPlaylist WHERE PlaylistID=? AND rb_local_deleted=0 ORDER BY TrackNo",
            (old_pl_id,)
        ).fetchall()
    except Exception:
        continue

    added = 0
    for old_cid, track_no in tracks:
        new_cid = dead_to_live.get(str(old_cid))
        if not new_cid:
            continue
        max_usn += 1
        live.execute("""INSERT INTO djmdSongPlaylist
            (ID,PlaylistID,ContentID,TrackNo,UUID,rb_data_status,rb_local_data_status,
             rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at)
            VALUES(?,?,?,?,?,0,0,0,0,NULL,?,?,?)""",
            (safe_id(), new_pl_id, new_cid, track_no, str(uuid_lib.uuid4()), max_usn, ts, ts))
        added += 1

    if added > 0:
        total_added += added
        print(f"  {pl_name[:50]}: {added}/{len(tracks)} tracks")

live.commit()
dead.close()
live.close()

print(f"\nTotal tracks restaurados en playlists: {total_added}")
print("Cerrá y reabri RekordBox.")
