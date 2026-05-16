"""Fix Loop Outro de Sonoma: 8 bars al final del track, fuera del breakdown largo."""
import sys, random, uuid as uuid_lib
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3

# Posiciones calculadas desde análisis de audio de Sonoma (124 BPM, 232.2s)
# Breakdown largo: 131.6s - 197.4s
# Ultimo groove: 197.4s - 224.5s
# 8 bars a 124 BPM = 15.5s
BAR_S = 4 * 60 / 124
LOOP_8BAR_MS  = int(216.7 * 1000)   # 8 bars antes del fin — en groove final
MIX_OUT_MS    = int(224.5 * 1000)   # fin del último kick detectable
LOOP_DURATION = int(BAR_S * 8 * 1000)  # duración del loop en ms

def ms_to_frame(ms): return round(ms / 1000 * 150)

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with RekordboxDB() as db:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    row = con.execute(
        "SELECT ID FROM djmdContent WHERE Title='Sonoma' AND rb_local_deleted=0"
    ).fetchone()
    cid = str(row[0])
    print(f"Sonoma ID: {cid}")

    # Borrar Loop Outro y Mix-OUT actuales
    con.execute(
        "DELETE FROM djmdCue WHERE ContentID=? AND Comment IN ('Loop Outro 16b ACTIVE','Mix-OUT')",
        (cid,)
    )
    print("Loop Outro 16b y Mix-OUT anteriores borrados")

    max_sp = con.execute("SELECT MAX(rb_local_usn) FROM djmdCue").fetchone()[0] or 0

    def insert_cue(comment, in_ms, out_ms, kind, color, active_loop, beat_loop_size=None):
        global max_sp
        max_sp += 1
        con.execute("""
            INSERT INTO djmdCue
              (ID, ContentID, InMsec, InFrame, InMpegFrame, InMpegAbs,
               OutMsec, OutFrame, OutMpegFrame, OutMpegAbs,
               Kind, Color, ColorTableIndex, ActiveLoop, Comment,
               BeatLoopSize, CueMicrosec, InPointSeekInfo, OutPointSeekInfo,
               ContentUUID, UUID, rb_data_status, rb_local_data_status,
               rb_local_deleted, rb_local_synced, usn, rb_local_usn,
               created_at, updated_at)
            VALUES (?,?,?,?,0,0,?,?,0,0,?,?,NULL,?,?,?,NULL,NULL,NULL,
                    (SELECT UUID FROM djmdContent WHERE ID=?),?,
                    0,0,0,0,NULL,?,?,?)
        """, (
            str(random.randint(1500000000, 4000000000)),
            cid, in_ms, ms_to_frame(in_ms),
            out_ms, ms_to_frame(out_ms),
            kind, color, active_loop, comment,
            beat_loop_size,
            cid,
            str(uuid_lib.uuid4()),
            max_sp, ts, ts
        ))

    # Loop Outro 8 bars ACTIVE al final
    insert_cue("Loop Outro 8b ACTIVE", LOOP_8BAR_MS,
               LOOP_8BAR_MS + LOOP_DURATION, 0, -1, 1, beat_loop_size=8)

    # Mix-OUT al fin del último kick
    insert_cue("Mix-OUT", MIX_OUT_MS, -1, 5, 13, None)

    con.commit()
    con.close()
    print(f"Loop Outro 8b → {LOOP_8BAR_MS/1000:.1f}s (groove final, fuera del breakdown)")
    print(f"Mix-OUT       → {MIX_OUT_MS/1000:.1f}s")

with RekordboxDB() as db2:
    print(f"DB integrity: {db2.integrity_check()}")
