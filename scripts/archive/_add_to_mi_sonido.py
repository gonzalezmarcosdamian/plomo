"""Crea [POOL] Mi Sonido si no existe y agrega tracks."""
import os, sys, random
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

DB_PATH = os.environ['REKORDBOX_DB_PATH']
KEY = os.environ.get('SQLCIPHER_KEY')
POOL_PARENT = '1520268261'  # [POOL] folder
NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

con = sqlcipher3.connect(DB_PATH)
con.execute(f"PRAGMA key='{KEY}'")
con.execute("PRAGMA cipher_compatibility=4")

# Buscar o crear playlist
row = con.execute(
    "SELECT ID FROM djmdPlaylist WHERE Name='[POOL] Mi Sonido' AND Attribute=0"
).fetchone()

if row:
    pl_id = row[0]
    print(f"Playlist existente ID={pl_id}")
else:
    pl_id = str(random.randint(1000000000, 3999999999))
    seq = (con.execute("SELECT MAX(Seq) FROM djmdPlaylist WHERE ParentID=?", (POOL_PARENT,)).fetchone()[0] or 0) + 1
    con.execute("""
        INSERT INTO djmdPlaylist (ID, Name, Attribute, ParentID, Seq, rb_local_deleted, created_at, updated_at)
        VALUES (?, '[POOL] Mi Sonido', 0, ?, ?, 0, ?, ?)
    """, (pl_id, POOL_PARENT, seq, NOW, NOW))
    con.commit()
    print(f"Playlist creada: [POOL] Mi Sonido ID={pl_id}")

# Tracks a agregar
tracks = [
    ("Emi Galvan", "Around the World"),
    ("Emi Galvan", "Trust"),
    ("Emi Galvan", "No Regrets"),
]

for artist, title in tracks:
    row = con.execute("""
        SELECT c.ID, c.Title, a.Name FROM djmdContent c
        JOIN djmdArtist a ON c.ArtistID = a.ID
        WHERE LOWER(c.Title) LIKE ? AND LOWER(a.Name) LIKE ?
        AND c.rb_local_deleted=0 LIMIT 1
    """, (f"%{title.lower()}%", f"%{artist.lower()}%")).fetchone()

    if not row:
        print(f"  NO ENCONTRADO: {artist} - {title}"); continue

    cid, ctitle, cartist = row
    exists = con.execute(
        "SELECT COUNT(*) FROM djmdSongPlaylist WHERE PlaylistID=? AND ContentID=?",
        (pl_id, cid)
    ).fetchone()[0]
    if exists:
        print(f"  YA EXISTE: {cartist} - {ctitle}"); continue

    tno = (con.execute("SELECT MAX(TrackNo) FROM djmdSongPlaylist WHERE PlaylistID=?", (pl_id,)).fetchone()[0] or 0) + 1
    con.execute(
        "INSERT INTO djmdSongPlaylist (ID, PlaylistID, ContentID, TrackNo, rb_local_deleted, created_at, updated_at) VALUES (?,?,?,?,0,?,?)",
        (random.randint(100000000, 999999999), pl_id, cid, tno, NOW, NOW)
    )
    con.commit()
    print(f"  AGREGADO #{tno}: {cartist} - {ctitle}")

con.close()
print("\nListo.")
