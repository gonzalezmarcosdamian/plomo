"""Construye sets en orden original del setlist para Sunset Trip, Eze Arias, Digweed, Vuarambon, Emi Galvan."""
import sys, random, uuid as uuid_lib
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from plomo import config
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def safe_id(): return str(random.randint(1500000000, 4000000000))


def find_id(con, title_kw, artist_kw=None):
    rows = con.execute("""
        SELECT c.ID, a.Name FROM djmdContent c
        LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
        WHERE c.rb_local_deleted=0 AND c.Title LIKE ?
        ORDER BY c.created_at DESC LIMIT 5
    """, (f"%{title_kw}%",)).fetchall()
    if artist_kw:
        for cid, aname in rows:
            if artist_kw.lower() in (aname or "").lower():
                return str(cid)
    return str(rows[0][0]) if rows else None


SETS = {
    "14. Sunset Trip — Dia 1 — 11.04.2026": [
        ("Kinly Estellar", "Panorama"),
        ("Check-a-Change", "Loveski"),
        ("Roots", "Abity"),
        ("Parallel Moon", "Kamilo"),
        ("Shepard", "Luch"),
        ("Piece of Hope", "Meriva"),
        ("Paradise Lost", "Freedo"),
        ("Soul Drive", "Dilby"),
        ("Song of Life", "Leftfield"),
        ("From Here to Eternity", "Moroder"),
        ("Le Souffle", "Fuscarini"),
        ("Control Is an Illusion", "Ezequiel"),
        ("Static Storm", "Griego"),
    ],
    "15. Sunset Trip — Dia 2 — 12.04.2026": [
        ("Eolomea", "Powel"),
        ("Shadows", "Dee Montero"),
        ("Kaskazi", "Vuarambon"),
        ("Blind Navigator", "Kasper"),
        ("Johannesburg", "Powel"),
        ("Forbidden Garden", "Leger"),
        ("Piece of Hope", "Meriva"),
        ("Le Souffle", "Fuscarini"),
        ("Parallel Moon", "Kamilo"),
        ("Control Is an Illusion", "Ezequiel"),
        ("Static Storm", "Griego"),
    ],
    "16. Eze Arias — Balance Croatia 021 — 2025": [
        ("Trigger", "Kyotto"),
        ("Existence", "Togni"),
        ("Hippias", "Paul Thomas"),
        ("Amnesia", "Rockka"),
        ("Endgame", "Nicolas Viana"),
        ("Deflator", "Dowden"),
        ("Raven", "Cendryma"),
        ("Reaching", "Durante"),
    ],
    "17. Eze Arias — Lollapalooza / Rosario — 2025": [
        ("Trigger", "Kyotto"),
        ("Existence", "Togni"),
        ("Raven", "Cendryma"),
        ("Endgame", "Nicolas Viana"),
        ("Deflator", "Dowden"),
        ("Reaching", "Durante"),
        ("Amnesia", "Rockka"),
        ("Hippias", "Paul Thomas"),
        ("Parallel Moon", "Kamilo"),
        ("Control Is an Illusion", "Ezequiel"),
    ],
    "18. Digweed — Transitions 2025 Selection": [
        ("Shine Tomorrow", "Guy Mantzur"),
        ("Nothing Lasts", "Guy Mantzur"),
        ("Silver Lake", "Guy J"),
        ("Everyday", "Guy J"),
        ("Reaching", "Durante"),
        ("Shadows", "Dee Montero"),
        ("Eolomea", "Powel"),
        ("Johannesburg", "Powel"),
        ("Forbidden Garden", "Leger"),
        ("Kaskazi", "Vuarambon"),
    ],
    "19. Vuarambon — We Are Lost / Forja 2025": [
        ("Eolomea", "Powel"),
        ("Johannesburg", "Powel"),
        ("Shadows", "Dee Montero"),
        ("Kaskazi", "Vuarambon"),
        ("Blind Navigator", "Kasper"),
        ("Forbidden Garden", "Leger"),
        ("Shine Tomorrow", "Guy Mantzur"),
        ("Nothing Lasts", "Guy Mantzur"),
        ("Silver Lake", "Guy J"),
        ("Everyday", "Guy J"),
    ],
    "20. Emi Galvan — Flowing 058 / Balance 2026": [
        ("Nothing Less", "Emi Galvan"),
        ("Everlong", "Emi Galvan"),
        ("Shadows", "Dee Montero"),
        ("Raven", "Cendryma"),
        ("Reaching", "Durante"),
        ("Deflator", "Dowden"),
        ("Parallel Moon", "Kamilo"),
        ("Kaskazi", "Vuarambon"),
    ],
}

con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

with RekordboxDB() as db:
    for set_name, track_queries in SETS.items():
        track_ids = []
        for title_kw, artist_kw in track_queries:
            tid = find_id(con, title_kw, artist_kw)
            if tid:
                track_ids.append(tid)

        # Dedup preservando orden
        seen = set()
        unique_ids = []
        for tid in track_ids:
            if tid not in seen:
                seen.add(tid)
                unique_ids.append(tid)

        if not unique_ids:
            print(f"SKIP {set_name}")
            continue

        pl_id = safe_id()
        max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
        con.execute("""INSERT INTO djmdPlaylist
            (ID,Seq,Name,ImagePath,Attribute,ParentID,SmartList,UUID,
             rb_data_status,rb_local_data_status,rb_local_deleted,rb_local_synced,
             usn,rb_local_usn,created_at,updated_at)
            VALUES (?,0,?,NULL,0,'1431708612',NULL,?,0,0,0,0,NULL,?,?,?)""",
            (pl_id, set_name, str(uuid_lib.uuid4()), max_usn + 1, ts, ts))

        max_sp = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
        print(f"\n{set_name} ({len(unique_ids)} tracks):")
        for i, cid in enumerate(unique_ids, 1):
            row = con.execute("""
                SELECT a.Name, c.Title, c.BPM, k.ScaleName
                FROM djmdContent c LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
                LEFT JOIN djmdKey k ON k.ID=c.KeyID WHERE c.ID=?
            """, (cid,)).fetchone()
            if not row:
                continue
            artist, title, bpm, key = row
            max_sp += 1
            con.execute("""INSERT INTO djmdSongPlaylist
                (ID,PlaylistID,ContentID,TrackNo,UUID,rb_data_status,rb_local_data_status,
                 rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at)
                VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)""",
                (safe_id(), pl_id, cid, i, str(uuid_lib.uuid4()), max_sp, ts, ts))
            print(f"  {i:>2}. {(bpm or 0)/100:.0f} {key or '?':4} | {(artist or '?')[:20]} — {title[:38]}")

        con.commit()
        db.add_node_to_xml(int(pl_id), 1431708612)

con.close()
with RekordboxDB() as db2:
    print(f"\nDB integrity: {db2.integrity_check()}")
