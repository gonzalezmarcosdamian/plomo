"""
Fix completo del Cumple del 20 — Set:
1. Loop Outro Sonoma → 8 bars al final (fuera del breakdown largo)
2. Loop Outro Jumbo → 8 bars al final (fuera del drop largo)
3. Beat grid snap en Glasgow, Trigger, Astrea (hot cues al golpe)
4. Rediseño del orden del set (distribuir Cattaneo, fix arco narrativo)
"""
import sys, random, uuid as uuid_lib, librosa, numpy as np
from scipy.signal import butter, filtfilt
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from plomo import config
from plomo.rekordbox_db import RekordboxDB
import sqlcipher3

SET_ID = "2144500797"  # Cumple del 20 — Set
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def safe_id(): return str(random.randint(1500000000, 4000000000))
def ms_to_frame(ms): return round(ms / 1000 * 150)
def snap_to_beat(time_s, bpm, ref_s):
    beat = 60.0 / bpm
    return ref_s + round((time_s - ref_s) / beat) * beat


def find_last_kick_end(path, bpm):
    y, sr = librosa.load(path, sr=None, mono=True)
    dur = len(y) / sr
    hop = 512
    bar_s = 4 * 60 / bpm
    b, a = butter(4, [60/(sr/2), 200/(sr/2)], btype='band')
    y_kick = filtfilt(b, a, y)
    kick_rms = librosa.feature.rms(y=y_kick, hop_length=hop)[0]
    bar_frames = int(bar_s * sr / hop)
    n = len(kick_rms) // bar_frames
    kpb = [kick_rms[i*bar_frames:(i+1)*bar_frames].mean() for i in range(n)]
    threshold = np.percentile(kpb, 40)
    last_kick_bar = max((i for i, k in enumerate(kpb) if k > threshold), default=n-1)
    return dur, last_kick_bar * bar_s


def fix_loop_outro(con, cid, path, bpm, n_bars=8):
    dur, last_kick_s = find_last_kick_end(path, bpm)
    bar_s = 4 * 60 / bpm
    loop_ms = int(max(0, last_kick_s - n_bars * bar_s) * 1000)
    mixout_ms = int(last_kick_s * 1000)

    # Borrar Loop Outro y Mix-OUT actuales
    con.execute(
        "DELETE FROM djmdCue WHERE ContentID=? AND Comment IN "
        "('Loop Outro 16b ACTIVE','Loop Outro 8b ACTIVE','Mix-OUT')",
        (str(cid),)
    )
    content_uuid = con.execute("SELECT UUID FROM djmdContent WHERE ID=?", (str(cid),)).fetchone()[0]
    max_usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdCue").fetchone()[0] or 0

    for comment, in_ms, out_ms, kind, color, active, loop_size in [
        ("Loop Outro 8b ACTIVE", loop_ms, loop_ms + int(n_bars * bar_s * 1000), 0, -1, 1, 8),
        ("Mix-OUT", mixout_ms, -1, 5, 13, None, None),
    ]:
        max_usn += 1
        con.execute("""
            INSERT INTO djmdCue
              (ID,ContentID,InMsec,InFrame,InMpegFrame,InMpegAbs,
               OutMsec,OutFrame,OutMpegFrame,OutMpegAbs,
               Kind,Color,ColorTableIndex,ActiveLoop,Comment,
               BeatLoopSize,CueMicrosec,InPointSeekInfo,OutPointSeekInfo,
               ContentUUID,UUID,rb_data_status,rb_local_data_status,
               rb_local_deleted,rb_local_synced,usn,rb_local_usn,
               created_at,updated_at)
            VALUES (?,?,?,?,0,0,?,?,0,0,?,?,NULL,?,?,?,NULL,NULL,NULL,?,?,
                    0,0,0,0,NULL,?,?,?)
        """, (safe_id(), str(cid), in_ms, ms_to_frame(in_ms),
              out_ms, ms_to_frame(max(0, out_ms)),
              kind, color, active, comment, loop_size,
              content_uuid, str(uuid_lib.uuid4()), max_usn, ts, ts))

    return loop_ms / 1000, mixout_ms / 1000


def snap_cues_to_grid(con, cid, bpm):
    """Snap todas las cues al beat más cercano usando el first_beat como referencia."""
    cues = con.execute(
        "SELECT ID, Comment, InMsec FROM djmdCue WHERE ContentID=? AND rb_local_deleted=0",
        (str(cid),)
    ).fetchall()

    # Encontrar first_beat
    ref_ms = None
    for cue_id, comment, in_ms in cues:
        if comment in ("Mix-IN First Beat", "M-First Beat") and in_ms > 0:
            ref_ms = in_ms
            break
    if ref_ms is None:
        return 0

    ref_s = ref_ms / 1000
    beat_dur = 60.0 / bpm
    snapped = 0

    for cue_id, comment, in_ms in cues:
        if comment in ("Mix-IN First Beat", "M-First Beat", "Loop Outro 8b ACTIVE",
                       "Loop Outro 16b ACTIVE", "Mix-OUT"):
            continue  # no snap a estos
        if in_ms <= 0:
            continue
        orig_s = in_ms / 1000
        new_s = snap_to_beat(orig_s, bpm, ref_s)
        new_ms = int(new_s * 1000)
        if abs(new_ms - in_ms) > 5:  # solo si hay diferencia real
            con.execute(
                "UPDATE djmdCue SET InMsec=?, InFrame=?, updated_at=? WHERE ID=?",
                (new_ms, ms_to_frame(new_ms), ts, str(cue_id))
            )
            snapped += 1
    return snapped


# Nuevo orden del set — arco narrativo corregido
NEW_ORDER = [
    # ENTRADA warmup (6A, 122-124 BPM)
    17135379,   # SAO Cattaneo Simply City     6A 123 ← opener Cattaneo temprano
    124672768,  # Levantine                    6A 122
    48428996,   # Echosphere Cattaneo Simply   6A 122 ← 2do Cattaneo, no en masa
    152277273,  # Long Time                    6A 124 ← sube BPM
    # BUILD
    132240681,  # Unknown Destination          7A 124 ← 6A→7A
    # MESETA OSCURA (referencia)
    57043826,   # Breakdown                    8A 123 ← CAPTURA ⭐
    93753672,   # Lifeline Cattaneo Simply     8A 123 ← respiro, intro larga como puente
    # EMOTIVO
    50268841,   # Undertow                     9A 122 ← constructor
    213870089,  # Sonoma                      10A 124 ← alma ⭐
    # MESETA BAILABLE
    139458182,  # Glasgow                     10A 122 ← dulce hypnótico ⭐
    # HEROICO → BUILD → PEAK → CIERRE
    128016078,  # I'm Lighter With You         1A 123 ← HEROICO ⭐
    135496627,  # Trigger                      2A 122 ← build post-heroico
    253892170,  # Astrea                       3A 122 ← oscuro con alma
    194246173,  # Jumbo                        4A 124 ← heroico 2 ⭐
    28669810,   # Cosmos                       4A 123 ← funcional puente
    9168971,    # Moments                      4A 125 ← CIERRE ⭐
]

TRACKS_TO_FIX_LOOP = {
    "Sonoma":  (213870089, "C:/Users/gonza/OneDrive/Documentos/Music/2026/Nuevos/2026-05/Simon Doty - Sonoma [Anjunadeep].mp3", 124),
    "Jumbo":   (194246173, "C:/Users/gonza/OneDrive/Documentos/Music/2026/Nuevos/2026-05/Paul Thomas - Jumbo (Jamie Stevens Remix) [UV].mp3", 124),
}

TRACKS_TO_SNAP = {
    "Glasgow": (139458182, 122),
    "Trigger": (135496627, 122),
    "Astrea":  (253892170, 122),
    "Breakdown": (57043826, 123),
}


def main():
    with RekordboxDB() as db:
        con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
        con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

        # 1. Fix Loop Outro Sonoma y Jumbo
        print("=== 1. Fix Loop Outro (8 bars al final) ===")
        for name, (cid, path, bpm) in TRACKS_TO_FIX_LOOP.items():
            loop_s, mixout_s = fix_loop_outro(con, cid, path, bpm)
            print(f"  {name}: Loop8b={loop_s:.1f}s | Mix-OUT={mixout_s:.1f}s")

        con.commit()

        # 2. Beat grid snap
        print("\n=== 2. Beat grid snap ===")
        for name, (cid, bpm) in TRACKS_TO_SNAP.items():
            n = snap_cues_to_grid(con, cid, bpm)
            print(f"  {name}: {n} cues alineados al grid")

        con.commit()

        # 3. Rediseño del orden del set
        print("\n=== 3. Rediseño del set ===")
        con.execute("DELETE FROM djmdSongPlaylist WHERE PlaylistID=?", (SET_ID,))
        max_sp = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0

        for i, cid in enumerate(NEW_ORDER, 1):
            row = con.execute(
                "SELECT a.Name, c.Title, c.BPM, k.ScaleName FROM djmdContent c "
                "LEFT JOIN djmdArtist a ON a.ID=c.ArtistID "
                "LEFT JOIN djmdKey k ON k.ID=c.KeyID "
                "WHERE c.ID=?", (str(cid),)
            ).fetchone()
            artist, title, bpm_raw, key = row
            bpm_f = (bpm_raw or 0)/100
            max_sp += 1
            con.execute("""
                INSERT INTO djmdSongPlaylist
                  (ID,PlaylistID,ContentID,TrackNo,UUID,
                   rb_data_status,rb_local_data_status,rb_local_deleted,
                   rb_local_synced,usn,rb_local_usn,created_at,updated_at)
                VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
            """, (safe_id(), SET_ID, str(cid), i,
                  str(uuid_lib.uuid4()), max_sp, ts, ts))
            print(f"  {i:>2}. {bpm_f:.0f} {key or '?':4} | {artist or '?'[:20]} — {title[:40]}")

        con.commit()
        con.close()

    with RekordboxDB() as db2:
        print(f"\nDB integrity: {db2.integrity_check()}")
    print("\nListo. Abrí Rekordbox, analizá los tracks y hacé sync al pen.")


if __name__ == "__main__":
    main()
