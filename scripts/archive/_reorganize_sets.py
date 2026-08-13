"""
Reorganiza Sets Armados en dos niveles:
  Sets Armados/
    Para Tocar/       -> sets 35-41 (activos, listos para tocar)
    Mis Sets/         -> 01-34 (archivo propio)
    Referencia Pro/   -> 16-20 fechados + 23-26 (sets de DJs externos)
    [POOL]/           -> pools + Cumple

Tambien: marca Monolink - Swallow (Oliver Koletzki Remix) en Core (Tracks Pilares)
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

# ── 1. MARK TRACK ──────────────────────────────────────────────────────────
print("Buscando Monolink - Swallow (Oliver Koletzki Remix)...")
track = con.execute("""
    SELECT c.ID FROM djmdContent c
    LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
    WHERE LOWER(c.Title) LIKE '%swallow%' AND LOWER(c.Title) LIKE '%koletzki%'
    AND c.rb_local_deleted=0
""").fetchone()

if track:
    track_id = track[0]
    # Find Core (Tracks Pilares) playlist
    core_pl = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name='Core (Tracks Pilares)' AND rb_local_deleted=0"
    ).fetchone()
    if core_pl:
        core_id = core_pl[0]
        already = con.execute(
            "SELECT ID FROM djmdSongPlaylist WHERE PlaylistID=? AND ContentID=?",
            (core_id, track_id)
        ).fetchone()
        if not already:
            max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
            max_no = con.execute("SELECT MAX(TrackNo) FROM djmdSongPlaylist WHERE PlaylistID=?", (core_id,)).fetchone()[0] or 0
            con.execute("""
                INSERT INTO djmdSongPlaylist
                (ID,PlaylistID,ContentID,TrackNo,UUID,rb_data_status,rb_local_data_status,
                 rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at)
                VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
            """, (safe_id(), core_id, track_id, max_no+1, str(uuid_lib.uuid4()), max_usn+1, ts, ts))
            print(f"  -> Agregado a 'Core (Tracks Pilares)': Swallow (Oliver Koletzki Remix)")
        else:
            print(f"  -> Ya estaba en Core (Tracks Pilares)")
    # Set color (ColorID=1 = pink/red en RB = destacado)
    con.execute("UPDATE djmdContent SET ColorID=1, updated_at=? WHERE ID=?", (ts, track_id))
    print(f"  -> Color destacado aplicado (ID={track_id})")
else:
    print("  [warn] Track no encontrado en DB — importalo primero")

# ── 2. CREAR SUBCARPETAS EN SETS ARMADOS ────────────────────────────────────
print("\nCreando subcarpetas en Sets Armados...")

def make_folder(name, parent_id):
    existing = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND ParentID=? AND rb_local_deleted=0",
        (name, parent_id)
    ).fetchone()
    if existing:
        print(f"  [ya existe] {name}")
        return existing[0]
    fid = safe_id()
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
    con.execute("""INSERT INTO djmdPlaylist
        (ID,Seq,Name,ImagePath,Attribute,ParentID,SmartList,UUID,
         rb_data_status,rb_local_data_status,rb_local_deleted,rb_local_synced,
         usn,rb_local_usn,created_at,updated_at)
        VALUES (?,0,?,NULL,1,?,NULL,?,0,0,0,0,NULL,?,?,?)""",
        (fid, name, parent_id, str(uuid_lib.uuid4()), max_usn+1, ts, ts))
    print(f"  [creada] {name} (ID={fid})")
    return fid

para_tocar_id = make_folder("Para Tocar", SETS_ARMADOS)
mis_sets_id   = make_folder("Mis Sets", SETS_ARMADOS)
referencia_id = make_folder("Referencia Pro", SETS_ARMADOS)
pool_id       = make_folder("[POOL]", SETS_ARMADOS)

# ── 3. CLASIFICAR Y MOVER PLAYLISTS ─────────────────────────────────────────
print("\nMoviendo playlists...")

all_playlists = con.execute("""
    SELECT ID, Name FROM djmdPlaylist
    WHERE ParentID=? AND rb_local_deleted=0 AND Attribute=0
    ORDER BY Name
""", (SETS_ARMADOS,)).fetchall()

# Also grab the ones at root that are numbered sets (23-26)
root_sets = con.execute("""
    SELECT ID, Name FROM djmdPlaylist
    WHERE ParentID IS NULL AND rb_local_deleted=0 AND Attribute=0
    AND (Name LIKE '23.%' OR Name LIKE '24.%' OR Name LIKE '25.%' OR Name LIKE '26.%')
""").fetchall()

def move_playlist(pl_id, dest_id, name):
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
    con.execute("""UPDATE djmdPlaylist SET ParentID=?, rb_local_usn=?, updated_at=?
                   WHERE ID=?""", (dest_id, max_usn+1, ts, pl_id))
    print(f"  -> {name}")

def get_set_number(name):
    try:
        n = name.split(".")[0].strip()
        return int(n)
    except:
        return None

# Rules:
# [POOL] or Cumple -> pool_id
# "Style" sets (16-20 Style versions) -> mis_sets_id (user's approximations)
# Dated pro sets (16-20 dated + 23-26) -> referencia_id
# Sets 35-41 -> para_tocar_id
# Sets 01-34 (own) -> mis_sets_id
# Sunset Trip (14-15) -> mis_sets_id (user's gig)
# Especiales: Romantico (5,10), Gina(21) -> mis_sets_id

PRO_DJ_KEYWORDS = ["Balance Croatia", "Lollapalooza", "Transitions 2025",
                   "We Are Lost", "Forja 2025", "Flowing 058",
                   "Sunsetstrip", "Stereo Montreal", "Palacio Alsina", "Forja Cordoba"]

for pl_id, name in all_playlists:
    if name.startswith("[POOL]") or name == "Cumple del 20":
        move_playlist(pl_id, pool_id, name)
    elif any(kw in name for kw in PRO_DJ_KEYWORDS):
        move_playlist(pl_id, referencia_id, name)
    else:
        num = get_set_number(name)
        if num is not None and num >= 35:
            move_playlist(pl_id, para_tocar_id, name)
        else:
            move_playlist(pl_id, mis_sets_id, name)

# Move root sets 23-26 to referencia
print("\nMoviendo sets 23-26 de root a Referencia Pro...")
for pl_id, name in root_sets:
    move_playlist(pl_id, referencia_id, name)

con.commit()

# ── 4. ACTUALIZAR XML ───────────────────────────────────────────────────────
print("\nActualizando XML...")
with RekordboxDB() as db:
    for fid in [para_tocar_id, mis_sets_id, referencia_id, pool_id]:
        db.add_node_to_xml(int(fid), int(SETS_ARMADOS))

print("\nListo. Estructura:")
print("Sets Armados/")
for name, fid in [("Para Tocar", para_tocar_id), ("Mis Sets", mis_sets_id),
                   ("Referencia Pro", referencia_id), ("[POOL]", pool_id)]:
    rows = con.execute(
        "SELECT Name FROM djmdPlaylist WHERE ParentID=? AND rb_local_deleted=0 ORDER BY Name",
        (fid,)
    ).fetchall()
    print(f"  {name}/ ({len(rows)} items)")
    for r in rows:
        print(f"    {r[0]}")

con.close()
