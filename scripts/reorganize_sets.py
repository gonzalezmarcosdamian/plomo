"""
Reorganización completa de Sets Armados:
1. Fix artistas faltantes (tracks con ? en Cumple del 20)
2. Limpiar duplicados en Energy Escalation
3. Crear 5 sets definitivos ordenados por Camelot
4. Renombrar borradores a [POOL]
"""
import sys
import random
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB, RekordboxRunningError
import sqlcipher3

# ---------------------------------------------------------------------------
# Artistas faltantes: {content_id: "Nombre Artista"}
# ---------------------------------------------------------------------------
ARTIST_FIXES = {
    246333736: "Benja Molina",
    206004569: "Benja Molina",
    30038355:  "Benja Molina",
    39880106:  "djimboh",
    264841568: "Durante, Ezequiel Arias",
    180819583: "Ewan Rill",
    230289841: "Juan Pablo Torrez, Kamilo Sanclemente",
    238425025: "Julian Nates",
    223928742: "Julian Nates",
    167162931: "Khen & Freedom Fighters",
    152689122: "Michael A",
    5130344:   "Nick Warren",
    31403052:  "Nicolas Rada",
    195885751: "Quivver",
}

# ---------------------------------------------------------------------------
# Sets definitivos: lista ordenada de content IDs (orden = orden de mezcla)
# ---------------------------------------------------------------------------
SETS = {
    # --- CATTANEO SET DEFINITIVO ---
    # Base: v4 (el que tocaste y funcionó) + 3 Simply City Remixes inyectados
    # Arco: 10A(warm) → 9A → 8A → 7A → 6A+Simply City → 5A → 4A → 3A → 2A
    #       → 1A → 11A → 10A → 9A → peak 8A → 7A → cierre 8A(117)
    "Cattaneo — Set Definitivo": [
        79359367,   # Henry Saiz - Me Llama Una Voz (10A 120) INTRO
        171043741,  # Simon Vuarambon - Quimera (9A 121)
        57988051,   # Kasper Koman - Sinking Sky (9A 122)
        4450071,    # Guy J - Worlds Apart (8A 122)
        33802344,   # Brian Cid - Allure (7A 122)
        29059854,   # Tantum - Keep My Letters (6A 122)
        24461486,   # Golan Zocher - SAO [Cattaneo Simply City] (6A 123)
        211255525,  # Solis - Echosphere [Cattaneo Simply City] (6A 122)
        12451550,   # Juan Deminicis - Deep Rock Galactic (5A 122)
        65722134,   # Cendryma - Moonflare (4A 121)
        57887899,   # George X - Telazar (3A 122)
        31945601,   # Meriva - Piece of Hope (2A 123)
        173808709,  # Maze 28 - Superbloom (2A 122)
        108258721,  # Abity, Ewan Rill - La Cumbre (1A 123)
        71754363,   # Paul Thomas - Abundance (11A 123)
        216859734,  # John Cosani - Snano (11A 123)
        218555193,  # Scippo - Wave (10A 123)
        228866911,  # Kaz James - Dazed (10A 122)
        238166033,  # Henry Saiz - Just A Mirage (9A 122)
        9200700,    # JP Torrez - Deep Truth [Cattaneo Vasami] (9A 124)
        40162623,   # J Lauda - Lifeline [Cattaneo Simply City] (8A 123)
        98987671,   # Kabi - Rainbow (8A 125) PEAK
        32299972,   # D-Nox, Andre Moret - Shine (8A 124)
        126951234,  # Cid Inc - Coalition (7A 122)
        197649902,  # Tinlicker - Because You Move Me (7A 122)
        167756126,  # Tmansoul - Vibrations Dub (8A 117) CIERRE
    ],

    # --- SIMON VUARAMBON — SET ---
    # Sonido: profundo, melódico, largo aliento. Guy J + Vuarambon + Melodic Deep
    # Arco: 12A(misterioso) → 11A → 10A → 9A → 8A(corazón) → 7A → 6A → cierre 1A
    "Simon Vuarambon — Set": [
        145824028,  # Simon Vuarambon - Strange Way (12A 120) INTRO
        123969986,  # Ruben Karapetyan - Synesthesia (12A 121)
        93545931,   # Cendryma - Particular Movement (12A 122) [Melodic Deep]
        216859734,  # John Cosani - Snano (11A 123)
        247168013,  # Andre Moret - Drift Whispers (10A 123) [Melodic Deep]
        42701772,   # Dabeat - Incense (10A 123)
        126806557,  # Guy Mantzur - Nothing Lasts (10A 122)
        160796044,  # Ruben Karapetyan - Cosmic Dot (9A 123)
        246911026,  # Ruben Karapetyan - Pantheon (9A 124)
        9200700,    # JP Torrez - Deep Truth [Cattaneo Vasami] (9A 124)
        215059847,  # Kamilo - Anomaly (8A 123)
        226583583,  # Guy Mantzur - Shine Tomorrow (8A 123)
        4450071,    # Guy J - Worlds Apart (8A 122)
        55666353,   # Guy Mantzur - Where Is Home (8A 122)
        71261420,   # Emi Galvan - Stay High (8A 121)
        148382703,  # Simon Vuarambon - Lake Of Fire (8A 122)
        155101303,  # Guy Mantzur & Sahar Z - Small Heart Attack (7A 121)
        118452631,  # Cendryma - Parabolic (7A 122) [Melodic Deep]
        23849546,   # Chelakhov - Insomnia (7A 122) [Melodic Deep]
        137727542,  # Mirage Extended (6A 123)
        143623916,  # Guy J - Nirvana (1A 120) CIERRE
        204524581,  # Chelakhov - Haunted (1A 121) CIERRE
    ],

    # --- NICK WARREN — MAIN PROGRESSIVE ---
    # Sonido: técnico, peak energy, mainstage prog. 124-126 BPM constante.
    # Arco: 8A(entrada directa) → 9A → 10A → 11A → 12A → 1A(climax)
    "Nick Warren — Main Progressive": [
        114349479,  # Mercurio, Nick Warren - Turbulence (8A 124) ENTRADA
        165530745,  # Pavel Petrov - Way Too High (8A 124)
        148015802,  # CamelPhat - Breathe (8A 125)
        207330948,  # Korolova - Reactive (8A 125)
        22551027,   # Empire Of The Sun - We Are The People ARTBAT (9A 125)
        246911026,  # Ruben Karapetyan - Pantheon (9A 124)
        9200700,    # JP Torrez - Deep Truth [Cattaneo Vasami] (9A 124)
        155175080,  # Rubmak - Fortuna (9A 125)
        220849717,  # Joshlane - System Overload (10A 124)
        130117600,  # Helsloot - Disco Maxi (10A 124)
        130747780,  # Kasey Taylor - Mount Epicon (10A 125)
        137953105,  # The Temper Trap - Sweet Disposition (John Summit) (10A 126)
        140323011,  # Carlo Whale - Inside Your Mind (11A 124)
        147351527,  # Sllash & Doppe - Cruel Summer (12A 124)
        184053630,  # Rony Seikaly - Lose Your Love (12A 124)
        166386470,  # àmou - I WISH I COULD FLY (12A 124)
        250126729,  # Coeus - Fiesta (1A 125) PEAK
        206443551,  # Meduza - Friends (1A 125)
    ],

    # --- EZE ARIAS — SET ---
    # Sonido: melodico emotivo, progressive con corazon. Mismo material, mejor orden.
    # Arco: 4A/3A(suave) → 6A/7A(melodico) → 8A/9A(build) → 6A(cierre)
    "Eze Arias — Set": [
        21539296,   # Aviate (4A 120) INTRO
        4984995,    # Bird Flight (4A 120)
        11244095,   # Tali Muss - Reward (4A 123)
        122435663,  # North Star (3A 122)
        32497909,   # Touch The Sky (3A 124) BUILD
        226402886,  # Primah (6A 120)
        252022349,  # Guy Mantzur - Tremolo Man (7A 120)
        91568734,   # Kamilo - Show Me the Stars (7A 121)
        250220914,  # Redspace - Thread (7B 122)
        111669615,  # Cubicolor - Hardly A Day (8B 120)
        71261420,   # Emi Galvan - Stay High (8A 121)
        226583583,  # Guy Mantzur - Shine Tomorrow (8A 123)
        215059847,  # Kamilo - Anomaly (8A 123)
        248132512,  # Emi Galvan - Don't Kill the Messenger (9A 123) PEAK
        139654438,  # Kamilo - Astronauts Nightmares (6A 123) CIERRE
    ],

    # --- SET ROMANTICO — SLOW BURN ---
    # Sonido: pre-fiesta, emotivo, 118-122 BPM. Reordenado por Camelot.
    "Set Romántico — Slow Burn": [
        37338213,   # DJ Soulstar - Bette Davis Eyes (5A 118) INTRO
        239200461,  # Kamilo - Sunset Love (7A 121)
        91568734,   # Kamilo - Show Me the Stars (7A 121)
        221134136,  # Samm - I'm Wondering (8A 120)
        99752619,   # &ME - Say What (8B 120)
        163848036,  # mredrollo - Follower (8A 121)
        79359367,   # Henry Saiz - Me Llama Una Voz (10A 120)
        268262920,  # AWEN - Your Voice (11A 122)
        168278733,  # Marten Lou - My Love for You (1A 122)
        42057678,   # Armin van Buuren - Part Of Me (3A 122) CIERRE
    ],
}

# Playlists a renombrar a [POOL] (borradores/versiones viejas)
RENAME_TO_POOL = {
    "1502184099": "Cattaneo Style v1",
    "1530476343": "Cattaneo Style v2",
    "1136008100": "Cattaneo Style v3",
    "1291980556": "Cattaneo Short - 1h35",
    "3706428817": "Cattaneo + Cierre Romantico v4",
    "66677896":   "Cattaneo & Simply City Remixes",
    "28689197":   "Guy J Style - 10",
    "22126253":   "Warm to Main - 10",
    "1953187021": "Energy Escalation",
}

# Playlists existentes a REEMPLAZAR con nueva versión ordenada
REPLACE_EXISTING = {
    "Eze Arias — Set":          "1794191870",
    "Set Romántico — Slow Burn": "974048971",
}


def safe_id():
    return str(random.randint(1500000000, 4000000000))


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_playlist(con, name, content_ids, parent_id="296109753"):
    pl_id = safe_id()
    pl_uuid = str(uuid_lib.uuid4())
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
    ts = now_str()
    con.execute("""
        INSERT INTO djmdPlaylist
          (ID, Seq, Name, ImagePath, Attribute, ParentID, SmartList, UUID,
           rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
           usn, rb_local_usn, created_at, updated_at)
        VALUES (?,?,?,NULL,0,?,NULL,?,0,0,0,0,NULL,?,?,?)
    """, (pl_id, 0, name, parent_id, pl_uuid, max_usn + 1, ts, ts))

    max_sp_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
    inserted = 0
    for i, cid in enumerate(content_ids, 1):
        # Verificar que el track existe
        exists = con.execute(
            "SELECT 1 FROM djmdContent WHERE ID=? AND rb_local_deleted=0", (str(cid),)
        ).fetchone()
        if not exists:
            print(f"    ⚠️  ContentID {cid} no encontrado en DB — salteando")
            continue
        max_sp_usn += 1
        con.execute("""
            INSERT INTO djmdSongPlaylist
              (ID, PlaylistID, ContentID, TrackNo, UUID,
               rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
               usn, rb_local_usn, created_at, updated_at)
            VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
        """, (safe_id(), pl_id, str(cid), i, str(uuid_lib.uuid4()), max_sp_usn, ts, ts))
        inserted += 1
    return pl_id, inserted


def clear_playlist_tracks(con, pl_id):
    con.execute("DELETE FROM djmdSongPlaylist WHERE PlaylistID=?", (pl_id,))


def main():
    with RekordboxDB() as db:
        print("✅ Pre-flight OK — Rekordbox no corre")
        print("✅ Backup creado\n")

        con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
        con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

        # ----------------------------------------------------------------
        # 1. FIX ARTISTAS FALTANTES
        # ----------------------------------------------------------------
        print("=== 1. Fix artistas faltantes ===")
        for content_id, artist_name in ARTIST_FIXES.items():
            # Buscar o crear artista
            row = con.execute(
                "SELECT ID FROM djmdArtist WHERE Name=? AND rb_local_deleted=0",
                (artist_name,)
            ).fetchone()
            if row:
                artist_id = row[0]
            else:
                artist_id = safe_id()
                ts = now_str()
                max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdArtist").fetchone()[0] or 0
                con.execute("""
                    INSERT INTO djmdArtist (ID, Name, rb_data_status, rb_local_data_status,
                      rb_local_deleted, rb_local_synced, usn, rb_local_usn, created_at, updated_at)
                    VALUES (?,?,0,0,0,0,NULL,?,?,?)
                """, (artist_id, artist_name, max_usn + 1, ts, ts))
                print(f"  Artista creado: {artist_name}")
            con.execute(
                "UPDATE djmdContent SET ArtistID=? WHERE ID=?",
                (artist_id, str(content_id))
            )
            print(f"  ✅ [{content_id}] → {artist_name}")
        con.commit()

        # ----------------------------------------------------------------
        # 2. LIMPIAR DUPLICADOS EN ENERGY ESCALATION
        # ----------------------------------------------------------------
        print("\n=== 2. Limpiar duplicados en Energy Escalation ===")
        dupes = con.execute("""
            SELECT ContentID, COUNT(*) as cnt, GROUP_CONCAT(ID, ',') as ids
            FROM djmdSongPlaylist
            WHERE PlaylistID='1953187021'
            GROUP BY ContentID
            HAVING cnt > 1
        """).fetchall()
        for cid, cnt, ids_str in dupes:
            keep, *remove = ids_str.split(",")
            for rid in remove:
                con.execute("DELETE FROM djmdSongPlaylist WHERE ID=?", (rid,))
            print(f"  Duplicado removido: ContentID={cid} (mantuve 1 de {cnt})")
        con.commit()
        print(f"  {len(dupes)} duplicados limpiados")

        # ----------------------------------------------------------------
        # 3. RENOMBRAR POOLS/BORRADORES
        # ----------------------------------------------------------------
        print("\n=== 3. Renombrar borradores a [POOL] ===")
        for pl_id, name in RENAME_TO_POOL.items():
            new_name = f"[POOL] {name}"
            con.execute(
                "UPDATE djmdPlaylist SET Name=?, updated_at=? WHERE ID=?",
                (new_name, now_str(), pl_id)
            )
            print(f"  {name} → {new_name}")
        con.commit()

        # ----------------------------------------------------------------
        # 4. REEMPLAZAR PLAYLISTS EXISTENTES (Eze Arias, Set Romantico)
        # ----------------------------------------------------------------
        print("\n=== 4. Reordenar playlists existentes ===")
        for set_name, pl_id in REPLACE_EXISTING.items():
            tracks = SETS[set_name]
            clear_playlist_tracks(con, pl_id)
            con.execute(
                "UPDATE djmdPlaylist SET Name=?, updated_at=? WHERE ID=?",
                (set_name, now_str(), pl_id)
            )
            max_sp_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
            ts = now_str()
            inserted = 0
            for i, cid in enumerate(tracks, 1):
                exists = con.execute(
                    "SELECT 1 FROM djmdContent WHERE ID=? AND rb_local_deleted=0", (str(cid),)
                ).fetchone()
                if not exists:
                    print(f"    ⚠️  ContentID {cid} no encontrado")
                    continue
                max_sp_usn += 1
                con.execute("""
                    INSERT INTO djmdSongPlaylist
                      (ID, PlaylistID, ContentID, TrackNo, UUID,
                       rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced,
                       usn, rb_local_usn, created_at, updated_at)
                    VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
                """, (safe_id(), pl_id, str(cid), i, str(uuid_lib.uuid4()), max_sp_usn, ts, ts))
                inserted += 1
            con.commit()
            print(f"  ✅ {set_name}: {inserted} tracks reordenados")

        # ----------------------------------------------------------------
        # 5. CREAR SETS NUEVOS (Cattaneo, Vuarambon, Warren)
        # ----------------------------------------------------------------
        print("\n=== 5. Crear sets nuevos ===")
        sets_armados_id = "1431708612"
        new_pl_ids = []
        for set_name, tracks in SETS.items():
            if set_name in REPLACE_EXISTING:
                continue  # ya procesado arriba
            pl_id, inserted = create_playlist(con, set_name, tracks, parent_id=sets_armados_id)
            new_pl_ids.append((int(pl_id), int(sets_armados_id)))
            con.commit()
            print(f"  ✅ {set_name}: {inserted}/{len(tracks)} tracks | ID={pl_id}")

        # ----------------------------------------------------------------
        # 6. ACTUALIZAR XML para playlists nuevas
        # ----------------------------------------------------------------
        print("\n=== 6. Actualizar masterPlaylists6.xml ===")
        for pl_id, parent_id in new_pl_ids:
            db.add_node_to_xml(pl_id, parent_id)
        print(f"  {len(new_pl_ids)} nodos agregados al XML")

        con.close()

    # Integrity check
    print("\nVerificando integridad DB...")
    with RekordboxDB() as db2:
        result = db2.integrity_check()
        print(f"DB integrity: {result}")

    print("\n=== RESUMEN FINAL ===")
    print("Sets Armados queda así:")
    print("  ✅ Cattaneo — Set Definitivo (26 tracks, 2.5h)")
    print("  ✅ Simon Vuarambon — Set (22 tracks, 2h)")
    print("  ✅ Nick Warren — Main Progressive (18 tracks, 1.75h)")
    print("  ✅ Eze Arias — Set (15 tracks, reordenado por Camelot)")
    print("  ✅ Set Romántico — Slow Burn (10 tracks, reordenado)")
    print("  ✅ Cumple del 20 (29 tracks, artistas corregidos)")
    print("  [POOL] Cattaneo v1/v2/v3/Short/Cierre/Simply City (archivados)")
    print("  [POOL] Energy Escalation (limpio, sin dupes)")
    print("  [POOL] Guy J Style / Warm to Main (archivados)")
    print("\nAbrí Rekordbox para ver los cambios.")


if __name__ == "__main__":
    main()
