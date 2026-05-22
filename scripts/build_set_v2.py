"""
Build Set v2 — usa el nuevo SetBuilder con movimientos, anclas y feedback.

Uso:
  python scripts/build_set_v2.py                    # demo con set de 3h
  python scripts/build_set_v2.py --feedback          # registrar feedback de transiciones

Ejemplos de registro de feedback (desde la sesión 2026-05-16):
  record_transition("93753672", "57043826", -1, "Lifeline→Breakdown: choca color")
  record_transition("50268841", "57043826", -2, "Breakdown→Undertow: intro muy silenciosa")
  record_transition("50268841", "213870089", +1, "Undertow→Sonoma: fluye bien")
"""
import sys, random, uuid as uuid_lib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB
from plomo.set_builder import (
    SetConfig, Movement, build_set,
    record_transition, load_feedback,
)
import sqlcipher3

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def safe_id(): return str(random.randint(1500000000, 4000000000))


def get_tracks_from_playlist(con: sqlcipher3.Connection, pl_id: str) -> list[dict]:
    rows = con.execute("""
        SELECT c.ID, a.Name, c.Title, c.BPM, k.ScaleName, c.Commnt
        FROM djmdSongPlaylist sp JOIN djmdContent c ON c.ID=sp.ContentID
        LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
        LEFT JOIN djmdKey k ON k.ID=c.KeyID
        WHERE sp.PlaylistID=? AND c.rb_local_deleted=0
        ORDER BY sp.TrackNo
    """, (pl_id,)).fetchall()
    result = []
    for cid, artist, title, bpm, key, commnt in rows:
        e = 5.0
        if commnt and "E:" in commnt:
            try:
                e = float(commnt.split("|")[0].replace("E:", "").strip())
            except ValueError:
                pass
        result.append({
            "id": str(cid), "artist": artist or "?",
            "title": title, "bpm": (bpm or 12200) / 100,
            "key": key or "?", "energy": e,
        })
    return result


def save_playlist(con, pl_name: str, tracks: list[dict], parent_id: str = "1431708612") -> str:
    from plomo.rekordbox_db import RekordboxDB
    pl_id = safe_id()
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdPlaylist").fetchone()[0] or 0
    con.execute("""INSERT INTO djmdPlaylist
        (ID,Seq,Name,ImagePath,Attribute,ParentID,SmartList,UUID,
         rb_data_status,rb_local_data_status,rb_local_deleted,rb_local_synced,
         usn,rb_local_usn,created_at,updated_at)
        VALUES (?,0,?,NULL,0,?,NULL,?,0,0,0,0,NULL,?,?,?)""",
        (pl_id, pl_name, parent_id, str(uuid_lib.uuid4()), max_usn + 1, ts, ts))
    max_sp = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
    for i, t in enumerate(tracks, 1):
        max_sp += 1
        con.execute("""INSERT INTO djmdSongPlaylist
            (ID,PlaylistID,ContentID,TrackNo,UUID,rb_data_status,rb_local_data_status,
             rb_local_deleted,rb_local_synced,usn,rb_local_usn,created_at,updated_at)
            VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)""",
            (safe_id(), pl_id, t["id"], i, str(uuid_lib.uuid4()), max_sp, ts, ts))
    return pl_id


def register_session_feedback() -> None:
    """Registra el feedback de la sesión 2026-05-16."""
    # Malas transiciones confirmadas en vivo
    record_transition("93753672", "57043826", -1, "Lifeline→Breakdown: color melódico→oscuro")
    record_transition("50268841", "57043826", -2, "Breakdown→Undertow: groove→silencio abrupto")
    record_transition("139458182", "128016078", -1, "Glasgow→Im Lighter: dulce→comprimido")
    record_transition("128016078", "135496627", -1, "Im Lighter→Trigger: energía cae bruscamente")
    # Buenas transiciones confirmadas
    record_transition("50268841", "213870089", +1, "Undertow→Sonoma: constructor→emotivo fluye")
    record_transition("135496627", "253892170", +1, "Trigger→Astrea: oscuro continúa bien")
    record_transition("253892170", "194246173", +1, "Astrea→Jumbo: oscuro→heroico 1 hop")
    print("Feedback de sesión 2026-05-16 registrado.")


def demo_build() -> None:
    """Demo: construye el set 09 Progressive Dark con el nuevo builder."""
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    # Leer pool del set existente
    tracks = get_tracks_from_playlist(con, "3284983581")
    print(f"Pool: {len(tracks)} tracks del set 09")

    # Configuración con movimientos — marcar Deep Truth y D-Nox Shine como anclas
    deep_truth_id = "9200700"
    shine_id = "32299972"
    moments_id = "9168971"

    set_config = SetConfig(
        name="09v2. Progressive Dark — 3h — Movimientos — 2026-05-21",
        movements=[
            Movement("Entrada",  2.0, 5.5, 3.5, 0.30),
            Movement("Meseta",   4.5, 7.5, 6.0, 0.45, anchor_ids=[deep_truth_id, shine_id]),
            Movement("Cierre",   5.5, 7.0, 4.5, 0.25, anchor_ids=[moments_id]),
        ],
        anchor_ids=[deep_truth_id, shine_id, moments_id],
    )

    with RekordboxDB() as db:
        ordered = build_set(tracks, set_config)

        print(f"\n{set_config.name} ({len(ordered)} tracks):")
        feedback = load_feedback()
        for i, t in enumerate(ordered, 1):
            marker = " ⭐ ANCLA" if t["id"] in set_config.anchor_ids else ""
            prev_id = ordered[i - 2]["id"] if i > 1 else None
            warn = ""
            if prev_id:
                key = f"{prev_id}→{t['id']}"
                if key in feedback and feedback[key].get("score", 0) < 0:
                    warn = f" ⚠️  {feedback[key].get('note','')}"
            print(f"  {i:>2}. E:{t['energy']:.1f} {t['bpm']:.0f} {t['key']:4} | "
                  f"{t['artist'][:18]:18} — {t['title'][:35]}{marker}{warn}")

        pl_id = save_playlist(con, set_config.name, ordered)
        con.commit()
        db.add_node_to_xml(int(pl_id), 1431708612)
        print(f"\nPlaylist creada: {pl_id}")

    con.close()
    from plomo.rekordbox_db import RekordboxDB as RDB
    with RDB() as db2:
        print(f"DB integrity: {db2.integrity_check()}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--feedback":
        register_session_feedback()
    else:
        register_session_feedback()
        demo_build()
