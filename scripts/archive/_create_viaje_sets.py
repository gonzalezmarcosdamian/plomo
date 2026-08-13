"""
Crea los 8 sets del viaje 47 dias (Sets 47-54) usando los tracks del Inbox sin asignar.
Ordena por energy (warmup -> peak -> cierre).
"""
import sys, random, uuid as uuid_lib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from plomo import config
import sqlcipher3

DRY = "--dry" in sys.argv
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_id():
    return str(random.randint(1500000000, 4000000000))

# Sets: (nombre, lista de (artista_fragment, titulo_fragment))
# Se busca por LIKE para tolerar variaciones menores
SETS = [
    (
        "47. Colyn x Mind Against — Afterlife Dark — Viaje 2026",
        [
            ("Colyn", "Signs of Change"),
            ("Mind Against", "Walking Away"),
            ("RÜFÜS DU SOL", "On My Knees"),
            ("Colyn", "Bridges In The Sky"),
            ("Mind Against", "Isolate"),
            ("RÜFÜS DU SOL", "Wildfire"),
            ("Colyn", "Caroussel"),
            ("KAS:ST", "Who's to Say What's Real"),
            ("Colyn", "Unstable Gravity Alert"),
            ("Colyn", "Jatayu"),
            ("Mind Against", "Bloom"),
            ("Colyn", "Oxygen Levels Low"),
            ("Colyn", "It's All Over"),
            ("Mind Against", "Prophet"),
            ("Colyn", "The Future Is the Past"),
        ]
    ),
    (
        "48. Rauschhaus x Tali Muss — Mango Alley x Univack — Viaje 2026",
        [
            ("Tali Muss", "Istanbul"),
            ("Rauschhaus", "Tapestry of Perception"),
            ("Rauschhaus", "Panaji"),
            ("Rauschhaus", "What We Expected"),
            ("Tali Muss", "Interlocutor"),
            ("Rauschhaus", "Canacona"),
            ("Rauschhaus", "Mesopotamia"),
            ("Tali Muss", "Mesafeler"),
            ("Rauschhaus", "If I Had Wings"),
            ("Rauschhaus", "Painting in the Sky"),
            ("Rauschhaus", "Morning Walks"),
            ("Tali Muss", "Dimension Of Space"),
            ("Tali Muss", "Garip"),
            ("Peer Kusiv", "Nightdrive"),
            ("Tali Muss", "Solar Focus"),
            ("Rauschhaus", "Waiting For The Birds"),
            ("Rauschhaus", "Galapagos"),
            ("Tali Muss", "Azal"),
        ]
    ),
    (
        "49. Kasper Koman x Kebin van Reeken x Gai Barone — Anjunadeep x Univack — Viaje 2026",
        [
            ("Kasper Koman", "Wilder (Extended"),
            ("Kebin Van Reeken", "Endurance"),
            ("Kasper Koman", "In Circles"),
            ("Kebin Van Reeken", "Mystic"),
            ("Gai Barone", "Fractals"),
            ("Kasper Koman", "The Observer"),
            ("Gai Barone", "Bedrocking"),
            ("Around Us", "Deep Down"),
            ("Kasper Koman", "Islander"),
            ("Kebin Van Reeken", "Hypnotize"),
            ("DJ Zombi", "Sparkling in the Shadow"),
            ("Gai Barone", "Black Hearts"),
            ("Kebin Van Reeken", "Mycelium"),
            ("Gai Barone", "Low Era"),
            ("Kasper Koman", "Fruit"),
            ("Kasper Koman", "Wilder (Alex O'Rion"),
            ("Serious Dancers", "Echo"),
            ("ECHO DAFT", "Years of Ascent"),
        ]
    ),
    (
        "50. Ric Niels x Jonas Saalbach — Driving Progressive — Viaje 2026",
        [
            ("Ric Niels", "Morning Dew"),
            ("Ric Niels", "Lose to Win"),
            ("Ric Niels & Mango", "Trip To South"),
            ("Dowden", "Coil"),
            ("Ric Niels", "Osmio"),
            ("Jonas Saalbach", "Faint"),
            ("Ric Niels & Juan Buitrago", "Glide"),
            ("Florian Kruse", "Falling"),
            ("Einmusik", "Lagoon"),
            ("Jonas Saalbach", "Vanishing Point"),
            ("Kabi (AR)", "Mutant"),
            ("Jonas Saalbach", "Second Surface"),
            ("Kabi (AR)", "Kimica"),
            ("Ric Niels", "Phantom"),
            ("Jonas Saalbach", "Midnight Sky"),
            ("Ric Niels", "Invasion"),
            ("Jonas Saalbach", "Keep Spirit High"),
            ("Guy J", "Catfish"),
        ]
    ),
    (
        "51. Guy J x Roy Rosenfeld x Simon Vuarambon — Hipnotico Progresivo — Viaje 2026",
        [
            ("Simon Vuarambon", "Diafana"),
            ("Simon Vuarambon", "Afrika"),
            ("Roy Rosenfeld", "Toco"),
            ("Roy Rosenfeld", "Halomot"),
            ("Way Out West", "Tuesday Maybe"),
            ("Guy J", "Airborne"),
            ("Roy Rosenfeld", "The Biggest Heart"),
            ("MOSHIC", "Love Made Me Do It"),
            ("Guy J", "Day Of Light"),
            ("Guy J", "Metal Dreams"),
            ("X-Press 2", "AC"),
            ("Guy J", "River"),
            ("Eitan Reiter", "Fade Away"),
        ]
    ),
    (
        "52. Spencer Brown x Rodriguez Jr. — Bedrock Driving — Viaje 2026",
        [
            ("Darque", "Yonke"),
            ("Nu, Jo.Ke", "Who Loves The Sun"),
            ("Rodriguez Jr.", "Alraegadir"),
            ("Fingerprint", "Santorini"),
            ("Ezequiel Arias", "SF to Cordoba"),
            ("Jeremy Olander", "Andköln"),
            ("Jeremy Olander", "Passagen"),
            ("Spencer Brown", "Thanks, Guy"),
            ("Rodriguez Jr.", "Ocean Drive"),
            ("Spencer Brown", "Blue Magic"),
            ("Rodriguez Jr.", "Kilian"),
            ("8Kays", "Waves"),
            ("Nick Muir, John Digweed, Spencer Brown", "Relentless"),
            ("Spencer Brown", "Offsides"),
        ]
    ),
    (
        "53. Lane 8 x Vocal Progressive — Anjunadeep — Viaje 2026",
        [
            ("Lane 8", "Matcha Mistake"),
            ("Nils Hoffmann", "9 Days"),
            ("Ben Böhmer", "Breathing"),
            ("Massane", "Horizon"),
            ("Braxton", "Taking Form"),
            ("Lane 8", "I / Y"),
            ("Massane", "Wild"),
            ("Lane 8", "Buggy"),
            ("Of Norway", "I Miss You"),
            ("Braxton", "Torn"),
            ("RUFUS", "Innerbloom"),
            ("Lane 8", "Oh, Miles"),
            ("Lane 8", "Little Mushroom"),
            ("Massane", "Promise You"),
            ("Lane 8", "Is This Our Earth"),
            ("Jody Wisternoff", "Mui"),
        ]
    ),
    (
        "54. Gorje Hewek x Sebastien Leger — All Day I Dream — Viaje 2026",
        [
            ("Gorje Hewek", "Otoko"),
            ("Gorje Hewek", "Full of Wonder"),
            ("Gorje Hewek", "Endless History"),
            ("Gorje Hewek", "U & Eyeye"),
            ("Sebastien Leger", "Panko Day"),
            ("Gorje Hewek", "Altitude"),
            ("Gorje Hewek", "Solovey"),
            ("Sebastien Leger", "Lanarka"),
            ("Gorje Hewek", "Life It Is"),
            ("Sebastien Leger", "Lava"),
            ("Gorje Hewek", "Never Been"),
            ("Sebastien Leger", "Feel"),
            ("Sebastien Leger", "Ariana"),
            ("Gorje Hewek", "Changes"),
            ("Gorje Hewek", "Margaret"),
            ("Gorje Hewek", "Earth"),
            ("Sebastien Leger", "Mistily"),
            ("Hernan Cattaneo", "Kaleidoscope"),
            ("Gorje Hewek", "Aya"),
        ]
    ),
]


def find_track(con, artist_frag, title_frag):
    """Busca un track por fragmento de artista y titulo."""
    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.Commnt
        FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
        WHERE c.rb_local_deleted=0
          AND a.Name LIKE ?
          AND c.Title LIKE ?
        ORDER BY c.ID DESC
        LIMIT 3
    """, (f"%{artist_frag}%", f"%{title_frag}%")).fetchall()
    return rows


def get_or_create_playlist(con, name):
    row = con.execute(
        "SELECT ID FROM djmdPlaylist WHERE Name=? AND rb_local_deleted=0", (name,)
    ).fetchone()
    if row:
        return row[0]
    pl_id = safe_id()
    con.execute("""
        INSERT INTO djmdPlaylist (ID, Name, ImagePath, Attribute, ParentID, Seq, UUID,
            rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
            usn, rb_local_usn, created_at, updated_at)
        VALUES (?, ?, NULL, 0, 'root', 0, ?, 0, 0, 0, 0, NULL, NULL, ?, ?)
    """, (pl_id, name, str(uuid_lib.uuid4()), ts, ts))
    return pl_id


def main():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    mode = "[DRY]" if DRY else "[WRITE]"
    print(f"Creando 8 sets del viaje {mode}\n")

    for set_name, tracklist in SETS:
        print(f"\n{'='*60}")
        print(f"{set_name}")
        print(f"{'='*60}")

        found_tracks = []
        not_found = []

        for artist_frag, title_frag in tracklist:
            results = find_track(con, artist_frag, title_frag)
            if results:
                cid, artist, title, commnt = results[0]
                energy = commnt or "?"
                print(f"  ✓ [{cid}] {artist} — {title} | {energy}")
                found_tracks.append((cid, artist, title))
            else:
                print(f"  ✗ NOT FOUND: {artist_frag} — {title_frag}")
                not_found.append((artist_frag, title_frag))

        print(f"\n  {len(found_tracks)} encontrados, {len(not_found)} no encontrados")

        if not DRY and found_tracks:
            pl_id = get_or_create_playlist(con, set_name)
            max_sp = con.execute(
                "SELECT MAX(rb_local_usn) FROM djmdSongPlaylist"
            ).fetchone()[0] or 0

            for i, (cid, artist, title) in enumerate(found_tracks):
                exists = con.execute(
                    "SELECT 1 FROM djmdSongPlaylist WHERE PlaylistID=? AND ContentID=? AND rb_local_deleted=0",
                    (pl_id, str(cid))
                ).fetchone()
                if not exists:
                    max_sp += 1
                    con.execute("""
                        INSERT INTO djmdSongPlaylist
                          (ID, PlaylistID, ContentID, TrackNo, UUID,
                           rb_data_status, rb_local_data_status, rb_local_deleted,
                           rb_local_synced, usn, rb_local_usn, created_at, updated_at)
                        VALUES (?,?,?,?,?, 0,0,0,0,NULL,?,?,?)
                    """, (safe_id(), pl_id, str(cid), i + 1,
                          str(uuid_lib.uuid4()), max_sp, ts, ts))

            print(f"  → Playlist '{set_name}' creada con {len(found_tracks)} tracks (ID={pl_id})")

    if not DRY:
        con.commit()
        result = con.execute("PRAGMA integrity_check(5)").fetchone()[0]
        print(f"\nIntegridad DB: {result}")
        print("\nListo. Abri Rekordbox y hace sync al pen.")
    else:
        print("\n[DRY] No se modifico nada.")

    con.close()


if __name__ == "__main__":
    main()
