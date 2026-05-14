"""
Deduplicate tracks by filename: keep one canonical copy, apply cues v8 if missing.
Priority order: Nuevos/2026-05 > Archivo > sets folders (begin/Peak/ending/Mi tercer lista)
"""
import sys
import random
import uuid as uuid_lib
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB
from plomo.cue_engine import analyze_track, apply_cues_v8
import sqlcipher3

SET_FOLDERS = {"begin", "Peak", "ending", "Mi tercer lista"}

def folder_priority(path: str) -> int:
    """Lower = higher priority (keep this one)."""
    p = Path(path)
    parts = p.parts
    for part in parts:
        if "2026-05" in part or "2026-04" in part or "2026-03" in part:
            return 0  # Newest Nuevos subfolder
        if part in SET_FOLDERS:
            return 10  # Set folders, lowest priority
    if "Archivo" in path:
        return 5
    return 3

with RekordboxDB() as db:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    # Find filename duplicates
    dupes = con.execute("""
        SELECT FileNameL, COUNT(*) as cnt, GROUP_CONCAT(ID, ',') as ids,
               GROUP_CONCAT(FolderPath, '|') as paths
        FROM djmdContent
        WHERE rb_local_deleted=0
        GROUP BY FileNameL
        HAVING cnt > 1
    """).fetchall()

    print(f"Grupos duplicados: {len(dupes)}")
    deleted = 0

    for filename, cnt, ids_str, paths_str in dupes:
        ids = ids_str.split(",")
        paths = paths_str.split("|")

        # Get cue counts and priorities
        candidates = []
        for id_, path in zip(ids, paths):
            cues = con.execute(
                "SELECT COUNT(*) FROM djmdCue WHERE ContentID=?", (id_,)
            ).fetchone()[0]
            prio = folder_priority(path)
            candidates.append((prio, -cues, id_, path))

        candidates.sort()  # best = lowest priority number, most cues
        keep_id, keep_path = candidates[0][2], candidates[0][3]

        for _, _, id_, path in candidates[1:]:
            con.execute(
                "UPDATE djmdContent SET rb_local_deleted=1 WHERE ID=?", (id_,)
            )
            deleted += 1
            print(f"  DEL [{Path(path).parent.name}] {filename}")

        print(f"  KEEP [{Path(keep_path).parent.name}] {filename} (ID={keep_id})")

    con.commit()

    # Now find tracks with 0 or <7 cues and apply v8
    print(f"\n=== Aplicando cues v8 a tracks sin cues ===")
    tracks_no_cues = con.execute("""
        SELECT c.ID, c.FolderPath, c.BPM
        FROM djmdContent c
        WHERE c.rb_local_deleted=0
        AND (
            SELECT COUNT(*) FROM djmdCue WHERE ContentID=c.ID
        ) < 7
        AND c.FolderPath != ''
        ORDER BY c.FolderPath
    """).fetchall()

    print(f"Tracks sin cues completos: {len(tracks_no_cues)}")
    con.close()

    cueed = 0
    skipped = 0
    for content_id, path, bpm_raw in tracks_no_cues:
        # Normalize path separators
        path = path.replace("\\", "/")
        if not Path(path).exists():
            skipped += 1
            continue

        bpm = (bpm_raw or 12200) / 100.0

        print(f"  Analizando: {Path(path).name} (BPM={bpm:.0f})")
        cues = analyze_track(path, known_bpm=bpm)
        if cues is None:
            print(f"    -> Track muy corto, salteando")
            skipped += 1
            continue

        n = apply_cues_v8(db.db, content_id, cues)
        print(f"    -> {n} markers insertados")
        cueed += 1

    print(f"\nResumen:")
    print(f"  Duplicados eliminados: {deleted}")
    print(f"  Tracks cueados: {cueed}")
    print(f"  Salteados (archivo no encontrado): {skipped}")
    print(f"  DB integrity: {db.integrity_check()}")
