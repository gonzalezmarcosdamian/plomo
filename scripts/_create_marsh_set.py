"""
Set estilo Marsh × Ferry Corsten — driving emotional progressive, 2h constante.
Arco: GMJ school → Marsh builds → doble climax Attraction + Whiteroom → bajada clásica.
"""
import os, sys, uuid, random
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dotenv import load_dotenv; load_dotenv()
import sqlcipher3

KEY = os.environ.get('SQLCIPHER_KEY')
DB = os.environ['REKORDBOX_DB_PATH']

SETS_PARENT = "1975667623"  # Sets Armados
PLAYLIST_NAME = "marsh"

# Tracklist con content_ids directos — sin ambigüedad
TRACKS = [
    # INTRO — establecer el registro: prog driving, Nick Warren school
    ("112197003",  "GMJ, Matter",              "Cryo"),
    ("241228611",  "Marcelo Vasami",            "Shades Of Blue"),
    ("145878175",  "X-Press 2",                "Ac/DC (Guy J Remix)"),
    ("130441327",  "Sébastien Léger",           "Forbidden Garden (Tim Green Remix)"),
    # MARSH ENTRA
    ("137466154",  "Marsh",                    "Little Darling"),
    ("87765340",   "Analog Trip",              "Cold Heart"),
    ("175806155",  "Marsh, Simon Doty",        "Touch The Sky"),
    ("161840112",  "Marsh",                    "Free"),
    ("80576548",   "Analog Trip",              "Red Clouds"),
    # FERRY BUILD
    ("132623275",  "Ferry Corsten",            "Reborn (Jonas Saalbach Remix)"),
    ("160052137",  "Ferry Corsten, Dirty South","Carte Blanche"),
    ("238643661",  "Sasha",                    "Phaxon (Einmusik Remix)"),
    # DOBLE CLIMAX — the reason for the set
    ("220272481",  "Ferry Corsten, Marsh",     "Attraction (Marsh's Extended Mix)"),
    ("162072169",  "Andy Moor & Adam White",   "The Whiteroom (Marsh Extended Mix)"),
    ("69857507",   "Ferry Corsten, Marsh",     "Attraction (Ferry's Extended Mix)"),
    # POST-PEAK — todavía alto
    ("7092958",    "N'to",                     "Trauma (Worakls Remix)"),
    ("188863500",  "Sasha",                    "Singularity (Fur Coat Remix)"),
    # DESCENSO CLÁSICO
    ("204313298",  "Guy J",                    "Dizzy Moments"),
    ("93960449",   "Dosem",                    "Chosen"),
    ("27307122",   "Yotto",                    "Radiate"),
    ("112295588",  "Nick Warren",              "Freebird (Emi Galvan Remix)"),
    ("41326127",   "MXV & Jody Wisternoff & James Grant", "Pursuit Of Happiness"),
    ("135098098",  "Guy J",                    "Silver Lake"),
]


def main():
    con = sqlcipher3.connect(DB)
    con.execute("PRAGMA key='" + KEY + "'")
    con.execute("PRAGMA cipher_compatibility=4")

    existing = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND rb_local_deleted=0",
        (PLAYLIST_NAME,)
    ).fetchone()

    if existing:
        pl_id = existing[0]
        print(f"Playlist '{PLAYLIST_NAME}' ya existe (ID={pl_id}), reconstruyendo")
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
        """, (pl_id, PLAYLIST_NAME, SETS_PARENT, str(uuid.uuid4()), max_usn + 1,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        print(f"Playlist '{PLAYLIST_NAME}' creada (ID={pl_id})")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
    added = 0

    print(f"\nTracklist {PLAYLIST_NAME}:")
    for i, (cid, artist, title) in enumerate(TRACKS):
        row = con.execute("""
            SELECT a.Name, c.Title, c.BPM, c.Commnt
            FROM djmdContent c LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
            WHERE c.ID=? AND c.rb_local_deleted=0
        """, (cid,)).fetchone()

        if not row:
            print(f"  {i+1:>2}. [WARN] ID {cid} no encontrado: {artist} - {title}")
            continue

        db_artist, db_title, bpm, commnt = row
        bpm_str = f"{bpm//100}bpm" if bpm else "?"
        energy = commnt.replace("E:", "E:") if commnt and commnt.startswith("E:") else "E:?"
        print(f"  {i+1:>2}. {energy}  {bpm_str}  | {db_artist} — {db_title}")

        con.execute("""
            INSERT INTO djmdSongPlaylist
            (ID, PlaylistID, ContentID, TrackNo, UUID,
             rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
             usn, rb_local_usn, created_at, updated_at)
            VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
        """, (str(random.randint(1500000000, 4000000000)), pl_id, cid,
              added, str(uuid.uuid4()), max_usn + added + 1, ts, ts))
        added += 1

    con.commit()

    # Registrar en XML
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent / "src"))
    from plomo.rekordbox_db import RekordboxDB
    with RekordboxDB() as db:
        db.add_node_to_xml(int(pl_id), int(SETS_PARENT))

    con.close()
    print(f"\n{added}/23 tracks en '{PLAYLIST_NAME}'. Sync al pen.")


if __name__ == "__main__":
    main()
