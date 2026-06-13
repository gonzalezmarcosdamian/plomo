"""
Completa los sets de DJ profesionales (23-26) con tracks de la libreria
que mantienen la misma idea/vibe de cada set.

Estrategia:
- Set 23 (Cattaneo): preserva orden original, intercala 6 tracks nuevos
- Sets 24-26 (Vuarambon/Digweed): ordena todos por energia, construye el arco
"""
import sys
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from plomo import config
import sqlcipher3

PLAYLIST_IDS = {
    23: "3539144677",   # Cattaneo Sunsetstrip Dia 2 BA 2026
    24: "1575045446",   # Vuarambon Stereo Montreal 2024-09-21
    25: "1756510163",   # Vuarambon Palacio Alsina BA 01.08.2025
    26: "3509983334",   # Digweed Forja Cordoba 18.04.2026
}

# Tracks existentes en cada set (content_id, energy)
EXISTING = {
    23: [
        (255475076, 6.0), (23437412, 5.7), (122024647, 5.6), (140593804, 6.4),
        (228547036, 3.9), (103030336, 6.7), (125227708, 5.5), (256470506, 4.9),
        (239731330, 6.1), (163058093, 5.8), (194717318, 5.1), (188218036, 5.4),
        (226402886, 4.4), (179975804, 2.9), (99927362, 4.0), (112000976, 4.0),
        (31090483, 5.7), (138831144, 4.7), (139819355, 6.1),
        # 59367602 = duplicado de Primah, se omite
    ],
    24: [
        (252219168, 1.5), (159250758, 6.7), (224698070, 5.3), (172986670, 5.6),
        (165662271, 5.4), (247190064, 4.0), (155831368, 5.4), (130144289, 5.3),
        (147392799, 5.0), (237884335, 4.3),
    ],
    25: [
        (232615393, 6.0), (70886512, 7.0), (5752103, 6.7), (164137848, 4.9),
        (148382703, 6.2), (48668279, 4.9), (103071288, 5.0),
    ],
    26: [
        (240856742, 1.0), (50324199, 6.3), (70779655, 6.9), (45455289, 6.1),
    ],
}

# Tracks nuevos a agregar (content_id, energy)
NEW_TRACKS = {
    23: [
        # 6 tracks para completar el Cattaneo (faltan picos E:7+)
        (10564061,  7.3),   # NOIYSE PROJECT, HC, Jamie Stevens - Remember Me
        (189889458, 7.0),   # Maze 28 - Leave the World Behind
        (183539189, 7.3),   # Einmusik, Dirty Doering - Centaurio
        (32299972,  7.4),   # D-Nox, Andre Moret - Shine
        (115910688, 7.0),   # Sasha & Jody Barr - Phaxon (Einmusik Remix)
        (139458182, 4.4),   # Nicolas Rada - Glasgow
    ],
    24: [
        # 12 tracks Vuarambon deep progressive style
        (123443538, 1.4),   # Gai Barone et al - All I Need (HC Remix)
        (184665629, 1.8),   # Cid Inc & Dmitry Molosh - Impending Storm
        (161923357, 1.8),   # Antrim & Juan Fernandez - Hide and Seek (Ric Niels)
        (99179089,  2.2),   # Hobin Rude - Seraph (Liam Garcia Remix)
        (74746061,  2.5),   # Maze 28 - This Is Just a Dream (HC & Vasami)
        (183627124, 2.5),   # Hermanez - Eight Years
        (19936591,  2.5),   # Joe Miller - The Last of the Great Days (Jamie Stevens)
        (216859734, 2.9),   # John Cosani - Snano
        (255101144, 2.9),   # Benja Molina - Aura
        (27040370,  3.5),   # Mike Rish - Tu Attair
        (252022349, 4.0),   # Guy Mantzur - Tremolo Man
        (141582909, 4.3),   # Simon Vuarambon & Sidartha Siliceo - Liberation
    ],
    25: [
        # 10 tracks Vuarambon Palacio Alsina style
        (17135379,  2.9),   # Golan Zocher - SAO (HC & Simply City)
        (114349479, 2.7),   # Mercurio, Nick Warren - Turbulence
        (134780496, 4.2),   # Tantum - Out Of Nowhere
        (18205051,  4.5),   # KYOTTO - Trigger
        (228325573, 4.9),   # Togni, Rodrives - Existence
        (126547672, 4.9),   # D-Nox, Andre Moret - Six
        (12451550,  4.9),   # Juan Deminicis - Deep Rock Galactic
        (93753672,  4.8),   # J Lauda - Lifeline (HC & Simply City)
        (139654438, 7.1),   # Kamilo Sanclemente - Astronauts Nightmares
        (83457678,  7.0),   # Ezequiel Arias - Passenger
    ],
    26: [
        # 30 tracks Digweed deep progressive 4h style
        (123443538, 1.4),   # Gai Barone et al - All I Need (HC Remix)
        (184665629, 1.8),   # Cid Inc & Dmitry Molosh - Impending Storm
        (161923357, 1.8),   # Antrim & Juan Fernandez - Hide and Seek (Ric Niels)
        (111669615, 1.8),   # Cubicolor - Hardly A Day Hardly A Night
        (172863178, 1.8),   # Panorama Channel - Kinly Estellar
        (50579825,  2.1),   # Juan Deminicis - Under Control
        (172367436, 2.1),   # Sandhog - Accent (Renato Cohen Remix)
        (99179089,  2.2),   # Hobin Rude - Seraph (Liam Garcia Remix)
        (32732043,  2.5),   # Nicholas Van Orton - Dark and Housey
        (183627124, 2.5),   # Hermanez - Eight Years
        (216859734, 2.9),   # John Cosani - Snano
        (255101144, 2.9),   # Benja Molina - Aura
        (17135379,  2.9),   # Golan Zocher - SAO (HC & Simply City)
        (245772299, 3.0),   # Cornucopia - Early Morning
        (45722094,  3.1),   # Michael A - Hunting Flowers
        (27040370,  3.5),   # Mike Rish - Tu Attair
        (252022349, 4.0),   # Guy Mantzur - Tremolo Man
        (44139624,  4.1),   # D-Nox, Stereo Underground - Dolby
        (134780496, 4.2),   # Tantum - Out Of Nowhere
        (59483047,  4.4),   # Chris Isaak - Wicked Game (Mass Digital Remix)
        (250639861, 4.4),   # Fer Torti - Star Trip
        (139458182, 4.4),   # Nicolas Rada - Glasgow
        (266175194, 4.4),   # Ismail M & Redspace - Jamevu
        (47108213,  4.5),   # Sebastian Sellares - Limbo
        (27375648,  4.5),   # Ewan Rill - Jacaranda on Jupiter
        (49117490,  4.5),   # Dmitry Molosh - Bird Flight
        (18205051,  4.5),   # KYOTTO - Trigger
        (211930560, 4.6),   # Julian Nates - Good Company Good Memories
        (114349479, 2.7),   # Mercurio, Nick Warren - Turbulence
        (183539189, 7.3),   # Einmusik, Dirty Doering - Centaurio (peak closer)
    ],
}


def safe_id() -> int:
    return random.randint(1, 2**31 - 1)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def insert_by_energy(existing: list, new_tracks: list) -> list:
    """
    Para Set 23: inserta cada track nuevo en la posicion que minimiza
    la diferencia de energia con sus vecinos (preserva el orden original
    de los existentes).
    """
    result = list(existing)
    for new_cid, new_e in sorted(new_tracks, key=lambda x: x[1]):
        best_pos = len(result)
        best_score = float("inf")
        for i in range(len(result) + 1):
            prev_e = result[i - 1][1] if i > 0 else new_e
            next_e = result[i][1] if i < len(result) else new_e
            score = abs(new_e - prev_e) + abs(new_e - next_e)
            if score < best_score:
                best_score = score
                best_pos = i
        result.insert(best_pos, (new_cid, new_e))
    return result


def sort_by_energy(existing: list, new_tracks: list) -> list:
    """
    Para Sets 24-26: mezcla todos y ordena por energia (arco progresivo).
    """
    all_tracks = existing + new_tracks
    return sorted(all_tracks, key=lambda x: x[1])


def validate_track_ids(con, track_ids: list[int]) -> set[int]:
    """Verifica que los IDs existan en djmdContent."""
    valid = set()
    for cid in track_ids:
        row = con.execute(
            "SELECT ID FROM djmdContent WHERE ID=? AND rb_local_deleted=0",
            (str(cid),),
        ).fetchone()
        if row:
            valid.add(cid)
        else:
            print(f"  [warn] ID {cid} no encontrado en DB, se omite")
    return valid


def rebuild_playlist(con, playlist_id: str, ordered_tracks: list, ts: str) -> int:
    """Elimina entradas existentes y reconstruye con el nuevo orden."""
    import uuid as uuid_lib
    con.execute("DELETE FROM djmdSongPlaylist WHERE PlaylistID=?", (playlist_id,))
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0

    inserted = 0
    for i, (cid, _) in enumerate(ordered_tracks, 1):
        max_usn += 1
        con.execute(
            """INSERT INTO djmdSongPlaylist
               (ID, PlaylistID, ContentID, TrackNo, UUID,
                rb_data_status, rb_local_data_status, rb_local_deleted,
                rb_local_synced, usn, rb_local_usn, created_at, updated_at)
               VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)""",
            (safe_id(), playlist_id, str(cid), i, str(uuid_lib.uuid4()), max_usn, ts, ts),
        )
        inserted += 1
    return inserted


def main() -> None:
    ts = now_str()
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    for set_num, playlist_id in PLAYLIST_IDS.items():
        existing = EXISTING[set_num]
        new_tracks = NEW_TRACKS[set_num]

        # Validar IDs nuevos
        all_new_ids = [cid for cid, _ in new_tracks]
        valid_ids = validate_track_ids(con, all_new_ids)
        new_tracks_valid = [(cid, e) for cid, e in new_tracks if cid in valid_ids]

        skipped = len(new_tracks) - len(new_tracks_valid)
        if skipped:
            print(f"\nSet {set_num}: {skipped} tracks omitidos (no en DB)")

        if set_num == 23:
            # Preserva orden original de Cattaneo, inserta nuevos por energia
            ordered = insert_by_energy(existing, new_tracks_valid)
        else:
            # Ordena todo por energia (arco progresivo)
            ordered = sort_by_energy(existing, new_tracks_valid)

        total = rebuild_playlist(con, playlist_id, ordered, ts)
        print(f"Set {set_num}: {total} tracks ({len(existing)} orig + {len(new_tracks_valid)} nuevos)")

    con.commit()
    con.close()
    print("\nListo. Abri Rekordbox y hace sync al pen.")


if __name__ == "__main__":
    main()
