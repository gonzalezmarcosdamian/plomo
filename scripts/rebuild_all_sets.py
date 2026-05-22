"""
1. Crea el 'Gina Set' de 2 horas con los tracks huérfanos + material complementario
2. Reconstruye todos los sets 01-13 con el nuevo algoritmo de movimientos
   (excepto Cattaneo que mantiene Camelot puro por diseño)
   Los sets 14-20 (DJ profesionales) no se tocan.
"""
import sys, random, uuid as uuid_lib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from plomo import config
from plomo.rekordbox_db import RekordboxDB
from plomo.set_builder import SetConfig, Movement, build_set, load_feedback
from plomo.camelot import distance as camelot_dist
import sqlcipher3

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def safe_id(): return str(random.randint(1500000000, 4000000000))


def get_tracks(con, pl_id: str) -> list[dict]:
    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.BPM, k.ScaleName, c.Commnt
        FROM djmdSongPlaylist sp JOIN djmdContent c ON c.ID=sp.ContentID
        LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
        LEFT JOIN djmdKey k ON k.ID=c.KeyID
        WHERE sp.PlaylistID=? AND c.rb_local_deleted=0 ORDER BY sp.TrackNo
    """, (pl_id,)).fetchall()
    result = []
    for cid, artist, title, bpm, key, commnt in rows:
        e = 5.0
        if commnt and "E:" in commnt:
            try: e = float(commnt.split("|")[0].replace("E:", "").strip())
            except: pass
        result.append({"id": str(cid), "artist": artist or "?",
                        "title": title, "bpm": (bpm or 12200)/100,
                        "key": key or "?", "energy": e})
    return result


def save_and_print(con, pl_id: str, name: str, tracks: list[dict]) -> None:
    con.execute("DELETE FROM djmdSongPlaylist WHERE PlaylistID=?", (pl_id,))
    max_sp = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
    print(f"\n{name} ({len(tracks)} tracks):")
    for i, t in enumerate(tracks, 1):
        max_sp += 1
        con.execute("""INSERT INTO djmdSongPlaylist
            (ID,PlaylistID,ContentID,TrackNo,UUID,rb_data_status,rb_local_data_status,
             rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at)
            VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)""",
            (safe_id(), pl_id, t["id"], i, str(uuid_lib.uuid4()), max_sp, ts, ts))
        print(f"  {i:>2}. E:{t['energy']:.1f} {t['bpm']:.0f} {t['key']:4} | "
              f"{t['artist'][:18]:18} — {t['title'][:38]}")


def create_playlist(con, name: str, tracks: list[dict], db) -> str:
    pl_id = safe_id()
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
    con.execute("""INSERT INTO djmdPlaylist
        (ID,Seq,Name,ImagePath,Attribute,ParentID,SmartList,UUID,
         rb_data_status,rb_local_data_status,rb_local_deleted,rb_local_synced,
         usn,rb_local_usn,created_at,updated_at)
        VALUES (?,0,?,NULL,0,'1431708612',NULL,?,0,0,0,0,NULL,?,?,?)""",
        (pl_id, name, str(uuid_lib.uuid4()), max_usn + 1, ts, ts))
    save_and_print(con, pl_id, name, tracks)
    db.add_node_to_xml(int(pl_id), 1431708612)
    return pl_id


def main():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    with RekordboxDB() as db:

        # ═══════════════════════════════════════════════════════════
        # GINA SET — 2 horas
        # Core: 7 tracks huérfanos + complementarios de librería
        # ═══════════════════════════════════════════════════════════
        print("=" * 60)
        print("GINA SET — 2 horas")

        # IDs huérfanos
        orphan_ids = [
            "147188154",  # Tunnel - Alex O'Rion       7A 122 E:5.2
            "190251324",  # Aer8 - Maze 28             10B 122 E:5.6  (nuevo)
            "115910688",  # Phaxon - Sasha              8A 125 E:7.0
            "222144888",  # Twenty Miami's - Blake Jar  6A 122 E:5.5
            "48899177",   # Deceptions - Maze 28        12A 122 E:6.2
            "206614040",  # Mirage - Kamilo/Maze 28     6A 123 E:6.8  (nuevo)
            "146334410",  # Lost in My Head - COQUEIT   5A 122 E:5.8
        ]

        # Complementarios: ~15 tracks del estilo (progressive 120-125, no en Gina aún)
        comp_ids = [
            "32706259",   # Maze 28 - Aer8 JP Torrez     D 122
            "57121373",   # Rockka - Operator Maze28     5A 122
            "246690426",  # Maze 28 - Leave World Behind 6A 122
            "200354003",  # Dmitry Molosh - Ambition      2A 121
            "160824916",  # Massano - Function            4A 122
            "124747526",  # Paul Thomas, Maze 28 Abundance 11A 123
            "32706259",   # Maze 28 Aer8 JP Torrez
            "57043826",   # Breakdown (Anderson)          8A 123
            "111302352",  # Chelakhov - Insomnia          7A 122
            "139458182",  # Glasgow (Nicolas Rada)       10A 122
            "88670086",   # K Loveski Check-a-Change      9A 122
            "178522502",  # Dee Montero - Shadows         9B 120
            "62244875",   # Powel - Johannesburg          8B 120
            "108442112",  # LUCH - Shepard's Tone         4A 123
            "190330726",  # Nicolas Viana - Endgame       2A 124
        ]

        # Construir pool sin duplicados
        seen = set()
        pool_ids = []
        for cid in orphan_ids + comp_ids:
            if cid not in seen:
                seen.add(cid)
                pool_ids.append(cid)

        # Leer tracks
        gina_pool = []
        for cid in pool_ids:
            row = con.execute("""
                SELECT c.ID, a.Name, c.Title, c.BPM, k.ScaleName, c.Commnt
                FROM djmdContent c LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
                LEFT JOIN djmdKey k ON k.ID=c.KeyID WHERE c.ID=?
            """, (cid,)).fetchone()
            if not row: continue
            cid_r, artist, title, bpm, key, commnt = row
            e = 5.0
            if commnt and "E:" in commnt:
                try: e = float(commnt.split("|")[0].replace("E:","").strip())
                except: pass
            gina_pool.append({"id": str(cid_r), "artist": artist or "?",
                               "title": title, "bpm": (bpm or 12200)/100,
                               "key": key or "?", "energy": e})

        # Config: 2h, 3 movimientos, anclas en los peaks
        gina_config = SetConfig(
            name="21. Gina Set — 2h — 2026-05-21",
            movements=[
                Movement("Entrada",  3.0, 6.0, 4.5, 0.30),
                Movement("Cuerpo",   5.0, 7.0, 5.5, 0.50, anchor_ids=["206614040", "115910688"]),
                Movement("Cierre",   5.0, 6.5, 4.5, 0.20),
            ],
            anchor_ids=["206614040", "115910688"],
        )

        gina_ordered = build_set(gina_pool, gina_config)
        create_playlist(con, gina_config.name, gina_ordered, db)

        # ═══════════════════════════════════════════════════════════
        # RECONSTRUIR SETS 01-13 con nuevo algoritmo
        # 01 (Cattaneo) se salta — Camelot puro por diseño
        # ═══════════════════════════════════════════════════════════
        print("\n" + "=" * 60)
        print("RECONSTRUYENDO SETS 02-13")

        SETS_TO_REBUILD = [
            ("3799821444", "02. Progressive Deep — 2h — Vuarambon Style",
             SetConfig.progressive_3h("02. Progressive Deep — 2h — Vuarambon Style")),
            ("3806493069", "03. Progressive Peak — 1.75h — Warren Style",
             SetConfig("03. Progressive Peak — 1.75h — Warren Style", movements=[
                 Movement("Entrada", 4.0, 7.0, 5.5, 0.30),
                 Movement("Peak",    6.5, 9.0, 7.0, 0.55),
                 Movement("Cierre",  6.0, 7.5, 5.5, 0.15),
             ])),
            ("1794191870", "04. Progressive Melodic — 1.5h — Eze Arias Style",
             SetConfig("04. Progressive Melodic — 1.5h — Eze Arias Style", movements=[
                 Movement("Entrada",  2.5, 5.5, 3.5, 0.35),
                 Movement("Cuerpo",   4.5, 7.0, 5.5, 0.45),
                 Movement("Cierre",   4.0, 5.5, 3.5, 0.20),
             ])),
            ("2176642189", "06. Cena & Progressive — 3h — 2026-05-13",
             SetConfig("06. Cena & Progressive — 3h — 2026-05-13", movements=[
                 Movement("Cena",     1.5, 4.5, 3.0, 0.40),
                 Movement("Prog",     3.5, 7.5, 5.5, 0.45),
                 Movement("Cierre",   5.0, 7.0, 4.5, 0.15),
             ])),
            ("2144500797", "07. Progressive — 2h — 2026-05-16",
             SetConfig.progressive_3h("07. Progressive — 2h — 2026-05-16")),
            ("3445647640", "08. Progressive — 2h — 2026-05-16 v2",
             SetConfig.progressive_3h("08. Progressive — 2h — 2026-05-16 v2")),
            ("3284983581", "09. Progressive Dark — 3h — Sonido Plomo — 2026-05-21",
             SetConfig("09. Progressive Dark — 3h — Sonido Plomo — 2026-05-21", movements=[
                 Movement("Entrada",  2.0, 5.5, 3.5, 0.28),
                 Movement("Meseta",   4.5, 7.5, 6.0, 0.47,
                           anchor_ids=["9200700", "32299972"]),
                 Movement("Cierre",   5.5, 7.0, 4.5, 0.25,
                           anchor_ids=["9168971"]),
             ])),
            ("2000435540", "12. Progressive — Nuevo Material — 2026-05-21",
             SetConfig.progressive_3h("12. Progressive — Nuevo Material — 2026-05-21")),
            ("210233332", "Melodic Deep 09-05",
             SetConfig("Melodic Deep 09-05", movements=[
                 Movement("Cuerpo", 3.5, 7.5, 5.5, 0.75),
                 Movement("Cierre", 5.0, 7.0, 5.0, 0.25),
             ])),
        ]

        for pl_id, name, set_config in SETS_TO_REBUILD:
            tracks = get_tracks(con, pl_id)
            if not tracks:
                print(f"  SKIP {name} (sin tracks)")
                continue
            set_config.name = name
            ordered = build_set(tracks, set_config)
            save_and_print(con, pl_id, name, ordered)

        con.commit()
        con.close()

    with RekordboxDB() as db2:
        print(f"\nDB integrity: {db2.integrity_check()}")
    print("\nListo. Abrí Rekordbox y hacé sync.")


if __name__ == "__main__":
    main()
