"""
Post-import: aplica cues v8, energy score y restaura playlists
para tracks recien importados por Rekordbox desde Nuevos/2026-05.

Usa sqlcipher3 directamente para todos los writes — nunca pyrekordbox.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import json
import random
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.cue_engine import analyze_track, apply_cues_v8_direct
from plomo.energy import calculate_energy, energy_label
import sqlcipher3

MAPPING_FILE = Path(__file__).parent.parent / "data" / "track_playlist_mapping.json"
PEN_SHARE = Path(r"C:\Users\gonza\AppData\Roaming\Pioneer\rekordbox\share")
PEN_ROOT = Path("D:/")


def safe_id():
    return str(random.randint(1500000000, 4000000000))


def copy_anlz_to_pen(con, content_id, title):
    row = con.execute(
        "SELECT AnalysisDataPath FROM djmdContent WHERE ID=?", (str(content_id),)
    ).fetchone()
    if not row or not row[0]:
        return
    import os, shutil
    rel = row[0].lstrip("/")
    local_src = PEN_SHARE / rel
    pen_dst = PEN_ROOT / rel.replace("/", "\\")
    if not local_src.exists() or pen_dst.exists():
        return
    pen_dst.parent.mkdir(parents=True, exist_ok=True)
    for f in local_src.parent.iterdir():
        shutil.copy2(f, pen_dst.parent / f.name)


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(MAPPING_FILE) as f:
        mapping = json.load(f)

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    new_tracks = con.execute("""
        SELECT c.ID, c.FileNameL, c.FolderPath, c.BPM
        FROM djmdContent c
        WHERE (c.FolderPath LIKE '%Nuevos%' OR c.FolderPath LIKE '%Inbox%')
          AND c.rb_local_deleted=0
    """).fetchall()

    print(f"Procesando {len(new_tracks)} tracks...\n")

    for cid, fname, fpath, bpm_raw in new_tracks:
        bpm = (bpm_raw or 12200) / 100
        fpath_fixed = fpath.replace("\\", "/") if fpath else fpath

        # Fix DeliveryControl + FolderPath
        con.execute(
            "UPDATE djmdContent SET DeliveryControl='on', FolderPath=?, updated_at=? WHERE ID=?",
            (fpath_fixed, ts, str(cid))
        )

        # Cues v8 via sqlcipher3 (nunca pyrekordbox)
        cues = None
        if fpath and Path(fpath).exists():
            try:
                cues = analyze_track(fpath, known_bpm=bpm)
                if cues:
                    n = apply_cues_v8_direct(con, int(cid), cues)
                    print(f"  cues [{cid}] {n} markers | {fname[:45]}")
            except Exception as e:
                print(f"  [WARN] cues [{cid}] {fname[:30]}: {e}")

        # Energy score
        if cues:
            score = calculate_energy(
                bpm=bpm,
                bass_in_ms=int(cues.bass_in * 1000) if cues.bass_in else None,
                breakdown_ms=int(cues.breakdown * 1000) if cues.breakdown else None,
                drop_ms=int(cues.drop * 1000) if cues.drop else None,
                outro_ms=int(cues.outro * 1000) if cues.outro else None,
                track_length_ms=None,
            )
            label = energy_label(score)
            con.execute(
                "UPDATE djmdContent SET Commnt=?, updated_at=? WHERE ID=?",
                (f"E:{score}", ts, str(cid))
            )
            print(f"  meta [{cid}] E:{score} [{label:7}] | {fname[:45]}")

        # Restaurar playlists
        if fname in mapping:
            max_sp = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
            added = 0
            for pl_id, track_no in mapping[fname]["playlists"]:
                exists = con.execute(
                    "SELECT 1 FROM djmdSongPlaylist WHERE PlaylistID=? AND ContentID=? AND rb_local_deleted=0",
                    (pl_id, str(cid))
                ).fetchone()
                if not exists:
                    max_sp += 1
                    con.execute("""
                        INSERT INTO djmdSongPlaylist
                          (ID,PlaylistID,ContentID,TrackNo,UUID,
                           rb_data_status,rb_local_data_status,rb_local_deleted,
                           rb_local_synced,usn,rb_local_usn,created_at,updated_at)
                        VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
                    """, (safe_id(), pl_id, str(cid), track_no,
                          str(uuid_lib.uuid4()), max_sp, ts, ts))
                    added += 1
            if added:
                print(f"         -> {added} playlists")

    con.commit()

    # Copiar ANLZ al pen
    if (PEN_ROOT / "PIONEER").exists():
        print("\nCopiando ANLZ al pen...")
        for cid, fname, fpath, _ in new_tracks:
            copy_anlz_to_pen(con, str(cid), fname)

    # Verificacion final de integridad
    result = con.execute("PRAGMA integrity_check(5)").fetchone()[0]
    print(f"\nIntegridad DB: {result}")

    con.close()
    print("\nListo. Abri Rekordbox y hace sync al pen.")


if __name__ == "__main__":
    main()
