"""Restaura el original de Ambition en las playlists donde estaba el duplicado."""
import os, sys, uuid, random
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
con = sqlcipher3.connect(os.environ['REKORDBOX_DB_PATH'])
con.execute("PRAGMA key='" + KEY + "'")
con.execute("PRAGMA cipher_compatibility=4")

original_id = '57277028'
dup_playlists = ['3510738544', '2039131269', '3887003823', '2058305450', '3864232730']

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0

added = 0
for i, pl_id in enumerate(dup_playlists):
    pl_name = con.execute("SELECT Name FROM djmdPlaylist WHERE ID=?", (pl_id,)).fetchone()
    name = pl_name[0] if pl_name else pl_id

    # Verificar que no este ya
    exists = con.execute(
        "SELECT COUNT(*) FROM djmdSongPlaylist WHERE PlaylistID=? AND ContentID=?",
        (pl_id, original_id)
    ).fetchone()[0]
    if exists:
        print(f"  [skip] ya esta: {name}")
        continue

    # Obtener TrackNo apropiado (al final de la playlist)
    max_track = con.execute(
        "SELECT MAX(TrackNo) FROM djmdSongPlaylist WHERE PlaylistID=?", (pl_id,)
    ).fetchone()[0] or 0

    new_id = str(random.randint(1500000000, 4000000000))
    con.execute("""
        INSERT INTO djmdSongPlaylist
        (ID, PlaylistID, ContentID, TrackNo, UUID,
         rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
         usn, rb_local_usn, created_at, updated_at)
        VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
    """, (new_id, pl_id, original_id, max_track + 1,
          str(uuid.uuid4()), max_usn + added + 1, ts, ts))
    added += 1
    print(f"  [OK] restaurado en: {name}")

con.commit()
con.close()
print(f"\n{added} playlists restauradas.")
