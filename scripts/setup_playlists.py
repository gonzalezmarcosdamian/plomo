"""Crea la estructura de carpetas y playlists para todos los sets."""
import sys, random, uuid, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
import sqlcipher3
from datetime import datetime

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_id():
    return str(random.randint(1500000000, 4000000000))

def get_or_create_folder(name, parent_id):
    row = con.execute("SELECT ID FROM djmdPlaylist WHERE Name=? AND Attribute=1 AND rb_local_deleted=0 LIMIT 1", (name,)).fetchone()
    if row:
        return row[0]
    pid = safe_id()
    con.execute("INSERT INTO djmdPlaylist (ID,Name,Attribute,ParentID,UUID,rb_data_status,rb_local_data_status,rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at) VALUES (?,?,1,?,?,0,0,0,0,NULL,1,?,?)",
                (pid, name, parent_id, str(uuid.uuid4()), ts, ts))
    print(f"  Creada carpeta: {name}")
    return pid

# Estructura raiz
root = con.execute("SELECT ID FROM djmdPlaylist WHERE Name='Pro DJ Library' AND rb_local_deleted=0 LIMIT 1").fetchone()
if root:
    root_id = root[0]
    print(f"Pro DJ Library encontrada: {root_id}")
else:
    root_id = get_or_create_folder("Pro DJ Library", None)

sets_folder_id = get_or_create_folder("Sets Armados", root_id)
get_or_create_folder("Por Posicion de Set", root_id)
get_or_create_folder("Por Estilo", root_id)

# Crear playlists para todos los targets
targets = sorted(Path("data/set_targets").glob("set_*.json"))
created = 0
for t in targets:
    num = int(t.stem.replace("set_", ""))
    data = json.loads(t.read_text(encoding="utf-8"))
    name = data["name"]
    exists = con.execute("SELECT ID FROM djmdPlaylist WHERE Name LIKE ? AND rb_local_deleted=0", (f"{num}.%",)).fetchone()
    if not exists:
        pid = safe_id()
        con.execute("INSERT INTO djmdPlaylist (ID,Name,Attribute,ParentID,UUID,rb_data_status,rb_local_data_status,rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at) VALUES (?,?,0,?,?,0,0,0,0,NULL,1,?,?)",
                    (pid, name, sets_folder_id, str(uuid.uuid4()), ts, ts))
        created += 1
        print(f"  Set {num}: {name[:50]}")

con.commit()
con.close()
print(f"\nPlaylists creadas: {created}/{len(targets)}")
