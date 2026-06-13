"""
Extrae playlists y sus tracks del DB viejo (master.dead.db)
y los recrea en el DB actual (master.db).
Solo copia lo que no existe ya.
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

def safe_id():
    return str(random.randint(1500000000, 4000000000))

def connect(path):
    con = sqlcipher3.connect(str(path))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con

dead = connect(DEAD_DB)
live = connect(LIVE_DB)
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Leer toda la estructura de playlists del DB muerto
print("Leyendo estructura del DB viejo...")
dead_playlists = dead.execute(
    "SELECT ID, Name, Attribute, ParentID, Seq FROM djmdPlaylist WHERE rb_local_deleted=0 ORDER BY Seq"
).fetchall()
print(f"  {len(dead_playlists)} playlists/carpetas encontradas")

# Mapeo de IDs viejos -> IDs nuevos
id_map = {}

# Ver qué ya existe en el live DB
live_names = set(r[0] for r in live.execute(
    "SELECT Name FROM djmdPlaylist WHERE rb_local_deleted=0"
).fetchall())

# Mapear IDs que ya existen (por nombre)
for old_id, name, attr, parent_id, seq in dead_playlists:
    existing = live.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND rb_local_deleted=0 LIMIT 1", (name,)
    ).fetchone()
    if existing:
        id_map[old_id] = existing[0]

# Insertar los que no existen, respetando la jerarquia
# Primera pasada: carpetas
created_folders = 0
created_playlists = 0

def resolve_parent(old_parent):
    if old_parent is None or old_parent == 'root':
        return old_parent
    return id_map.get(old_parent, old_parent)

# Procesar en orden para que los padres existan antes que los hijos
for old_id, name, attr, parent_id, seq in dead_playlists:
    if old_id in id_map:
        continue  # Ya existe

    new_parent = resolve_parent(parent_id)
    new_id = safe_id()
    id_map[old_id] = new_id

    live.execute("""INSERT INTO djmdPlaylist
        (ID,Name,Attribute,ParentID,Seq,UUID,rb_data_status,rb_local_data_status,
         rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at)
        VALUES(?,?,?,?,?,?,0,0,0,0,NULL,1,?,?)""",
        (new_id, name, attr, new_parent, seq or 0, str(uuid_lib.uuid4()), ts, ts))

    if attr == 1:
        created_folders += 1
        print(f"  [FOLDER] {name}")
    else:
        created_playlists += 1
        print(f"  [LIST]   {name[:60]}")

live.commit()
print(f"\nCarpetas creadas: {created_folders} | Playlists creadas: {created_playlists}")

# Ahora copiar los tracks de cada playlist
print("\nCopiando tracks de playlists...")
total_tracks = 0
skipped_playlists = 0

for old_id, name, attr, parent_id, seq in dead_playlists:
    if attr == 1:  # Skip folders
        continue

    new_pl_id = id_map.get(old_id)
    if not new_pl_id:
        continue

    # Obtener tracks de esta playlist del DB muerto
    try:
        tracks = dead.execute(
            "SELECT ContentID, TrackNo FROM djmdSongPlaylist WHERE PlaylistID=? AND rb_local_deleted=0 ORDER BY TrackNo",
            (old_id,)
        ).fetchall()
    except Exception as e:
        skipped_playlists += 1
        continue

    if not tracks:
        continue

    # Verificar que la playlist en el live DB no tiene ya tracks
    existing_tracks = live.execute(
        "SELECT COUNT(*) FROM djmdSongPlaylist WHERE PlaylistID=? AND rb_local_deleted=0",
        (new_pl_id,)
    ).fetchone()[0]

    if existing_tracks > 0:
        continue  # Ya tiene tracks, no sobreescribir

    # Verificar que los ContentIDs existen en el live DB
    max_usn = live.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
    added = 0
    for content_id, track_no in tracks:
        exists = live.execute(
            "SELECT 1 FROM djmdContent WHERE ID=? AND rb_local_deleted=0", (str(content_id),)
        ).fetchone()
        if exists:
            max_usn += 1
            live.execute("""INSERT INTO djmdSongPlaylist
                (ID,PlaylistID,ContentID,TrackNo,UUID,rb_data_status,rb_local_data_status,
                 rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at)
                VALUES(?,?,?,?,?,0,0,0,0,NULL,?,?,?)""",
                (safe_id(), new_pl_id, content_id, track_no,
                 str(uuid_lib.uuid4()), max_usn, ts, ts))
            added += 1

    if added > 0:
        live.commit()
        total_tracks += added
        print(f"  {name[:50]}: {added}/{len(tracks)} tracks")

dead.close()
live.close()
print(f"\nTotal tracks restaurados: {total_tracks}")
print("Listo. Reabri RekordBox.")
