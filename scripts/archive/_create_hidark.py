"""
Crea la playlist "hidark" en Rekordbox DB.
Organico colorido, 2h directo al grano, antes del set Maze 28.
"""
import os, sys, uuid, random
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
DB = os.environ['REKORDBOX_DB_PATH']

SETS_PARENT = "1975667623"  # Sets Armados
PLAYLIST_NAME = "hidark"

# Tracklist curada — directo al grano, organico colorido
# (artist, title) para matching fuzzy
TRACKS = [
    # ATAQUE — directo, organico, punch desde el primer track
    ("Hermanez",             "Other Side"),
    ("Gorje Hewek",          "Aya"),
    ("Tinlicker",            "Because You Move Me"),
    ("Gorje Hewek",          "Forest Song in the Night"),
    ("Makebo",               "Back To The Roots"),
    # BUILD COLOR
    ("Jan Blomqvist",        "Deeper Grounds"),
    ("Gorje Hewek",          "Children"),
    ("NOIYSE PROJECT",       "Remember Me"),
    ("RUFUS DU SOL",         "In the Moment"),
    ("Hana",                 "Elysia"),
    # PEAK — sorpresa
    ("Adriatique",           "Mystery"),
    ("Emi Galvan",           "Free Your Mind"),
    ("MXV",                  "Pursuit Of Happiness"),
    ("Tinlicker",            "Voodoo"),
    # COLOR DOWN
    ("N'to",                 "Alter Ego"),
    ("Gorje Hewek",          "Fluminnese"),
    ("Black Coffee",         "Wish You Were Here"),
    ("Hermanez",             "Gamma Ray"),
    ("Simon Doty",           "Sonoma"),
    # BRIDGE TO MAZE 28
    ("Fur Coat",             "Hurricane"),
    ("Lee Burridge",         "Forget"),
    ("Guy Mantzur",          "Hidden Karisma"),
    ("Stephan Bodzin",       "Earth"),
]

def find_track(con, artist, title):
    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.BPM, c.Commnt
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE c.rb_local_deleted=0
          AND LOWER(c.Title) LIKE LOWER(?)
          AND LOWER(COALESCE(a.Name,'')) LIKE LOWER(?)
    """, (f"%{title}%", f"%{artist.split()[0]}%")).fetchall()

    if not rows:
        rows = con.execute("""
            SELECT c.ID, a.Name, c.Title, c.BPM, c.Commnt
            FROM djmdContent c
            LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
            WHERE c.rb_local_deleted=0 AND LOWER(c.Title) LIKE LOWER(?)
        """, (f"%{title}%",)).fetchall()

    return rows[0] if rows else None


def main():
    con = sqlcipher3.connect(DB)
    con.execute(f"PRAGMA key='{KEY}'")
    con.execute("PRAGMA cipher_compatibility=4")

    # Verificar si ya existe
    existing = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND rb_local_deleted=0",
        (PLAYLIST_NAME,)
    ).fetchone()

    if existing:
        pl_id = existing[0]
        print(f"Playlist '{PLAYLIST_NAME}' ya existe (ID={pl_id}), la reemplaza")
        con.execute("DELETE FROM djmdSongPlaylist WHERE PlaylistID=?", (pl_id,))
    else:
        pl_id = str(random.randint(1500000000, 4000000000))
        max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        con.execute("""
            INSERT INTO djmdPlaylist
            (ID, Seq, Name, ImagePath, Attribute, ParentID, SmartList, UUID,
             rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
             usn, rb_local_usn, created_at, updated_at)
            VALUES (?,0,?,NULL,0,?,NULL,?,0,0,0,0,NULL,?,?,?)
        """, (pl_id, PLAYLIST_NAME, SETS_PARENT, str(uuid.uuid4()), max_usn + 1, ts, ts))
        print(f"Playlist '{PLAYLIST_NAME}' creada (ID={pl_id})")

    # Resolver y agregar tracks
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
    added = 0
    seen_ids = set()

    print(f"\nTracklist {PLAYLIST_NAME}:")
    for i, (artist, title) in enumerate(TRACKS):
        row = find_track(con, artist, title)
        if not row:
            print(f"  {i+1:>2}. [WARN] No encontrado: {artist} - {title}")
            continue

        cid, db_artist, db_title, bpm, commnt = row
        if cid in seen_ids:
            print(f"  {i+1:>2}. [DUP]  {db_artist} - {db_title}")
            continue
        seen_ids.add(cid)

        bpm_str = f"{bpm/100:.0f}bpm" if bpm else "?"
        energy = commnt.replace("E:", "") if commnt and commnt.startswith("E:") else "?"
        print(f"  {i+1:>2}. E:{energy}  {bpm_str}  | {db_artist} — {db_title}")

        con.execute("""
            INSERT INTO djmdSongPlaylist
            (ID, PlaylistID, ContentID, TrackNo, UUID,
             rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
             usn, rb_local_usn, created_at, updated_at)
            VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
        """, (str(random.randint(1500000000, 4000000000)), pl_id, str(cid),
              added, str(uuid.uuid4()), max_usn + added + 1, ts, ts))
        added += 1

    con.commit()
    con.close()
    print(f"\n{added} tracks en '{PLAYLIST_NAME}'. Sync al pen cuando quieras.")


if __name__ == "__main__":
    main()
