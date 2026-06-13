"""
Crea carpeta 'Para Probar' en Sets Armados y pre-crea playlists 41-45 dentro.
build_set.py las encontrara y las llenara con tracks.
"""
import sys, random, uuid as uuid_lib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, 'src')
from plomo import config
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3
from datetime import datetime

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
SETS_ARMADOS = "1975667623"

def safe_id():
    return str(random.randint(1500000000, 4000000000))

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

def make_folder(name, parent_id):
    existing = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND ParentID=? AND Attribute=1 AND rb_local_deleted=0",
        (name, parent_id)
    ).fetchone()
    if existing:
        print(f"  [ya existe] carpeta {name}: ID={existing[0]}")
        return existing[0]
    fid = safe_id()
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
    con.execute("""INSERT INTO djmdPlaylist
        (ID,Seq,Name,ImagePath,Attribute,ParentID,SmartList,UUID,
         rb_data_status,rb_local_data_status,rb_local_deleted,rb_local_synced,
         usn,rb_local_usn,created_at,updated_at)
        VALUES (?,0,?,NULL,1,?,NULL,?,0,0,0,0,NULL,?,?,?)""",
        (fid, name, parent_id, str(uuid_lib.uuid4()), max_usn+1, ts, ts))
    print(f"  [creada] carpeta {name}: ID={fid}")
    return fid

def make_playlist(name, parent_id):
    existing = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND rb_local_deleted=0",
        (name,)
    ).fetchone()
    if existing:
        # Move to Para Probar if not already there
        con.execute("UPDATE djmdPlaylist SET ParentID=?, updated_at=? WHERE ID=?",
                    (parent_id, ts, existing[0]))
        print(f"  [movida] {name}: ID={existing[0]}")
        return existing[0]
    pid = safe_id()
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
    con.execute("""INSERT INTO djmdPlaylist
        (ID,Seq,Name,ImagePath,Attribute,ParentID,SmartList,UUID,
         rb_data_status,rb_local_data_status,rb_local_deleted,rb_local_synced,
         usn,rb_local_usn,created_at,updated_at)
        VALUES (?,0,?,NULL,0,?,NULL,?,0,0,0,0,NULL,?,?,?)""",
        (pid, name, parent_id, str(uuid_lib.uuid4()), max_usn+1, ts, ts))
    print(f"  [creada] playlist {name}: ID={pid}")
    return pid

print("Creando 'Para Probar'...")
para_probar_id = make_folder("Para Probar", SETS_ARMADOS)

print("\nCreando playlists 41-45...")
sets = [
    (41, "41. Dulce Progresivo — Loveland Style — 2026-06-13"),
    (42, "42. Emi & Kamilo — Colorido Progresivo — 2026-06-13"),
    (43, "43. Maze 28 + Cendryma — Nuevo Prog — 2026-06-13"),
    (44, "44. Dowden + Guy J — Progressive Profundo — 2026-06-13"),
    (45, "45. Tom Pavicich + Durante — Prog Argentino — 2026-06-13"),
]

pl_ids = {}
for num, name in sets:
    pl_ids[num] = make_playlist(name, para_probar_id)

con.commit()

print("\nActualizando XML para Para Probar...")
with RekordboxDB() as db:
    db.add_node_to_xml(int(para_probar_id), int(SETS_ARMADOS))
    for num, name in sets:
        db.add_node_to_xml(int(pl_ids[num]), int(para_probar_id))

print("\nListo. Estructura creada:")
print("Sets Armados/")
print("  Para Probar/")
for num, name in sets:
    print(f"    {name}")
con.close()
