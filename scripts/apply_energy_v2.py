"""
Aplica energy score v2 a toda la librería:
- v1.1: bass_in=0 penalizado
- v1.2: BPM peso reducido
- v1.3: groove_ratio desde audio
Preserva overrides manuales (M:X en Comment).
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB
from plomo.energy_v2 import calculate_energy_v2, compute_groove_ratio
import sqlcipher3


def get_cue_timings(con, cid):
    cues = con.execute(
        "SELECT Comment, InMsec FROM djmdCue WHERE ContentID=? AND rb_local_deleted=0",
        (str(cid),)
    ).fetchall()
    r = {}
    for c, ms in cues:
        if c in ("Mix-IN First Beat", "M-First Beat"):
            r["first_beat"] = ms
        elif c in ("Bass IN", "M-Bass IN"):
            r["bass_in"] = ms
        elif c in ("Breakdown", "M-Breakdown"):
            r["breakdown"] = ms
        elif c in ("DROP", "M-DROP"):
            r["drop"] = ms
        elif c == "Mix-OUT":
            r["outro"] = ms
    return r


def set_score(commnt: str, new_score: float) -> str:
    """Actualiza E: preservando M: y notas del DJ."""
    if commnt and "| M:" in commnt:
        idx = commnt.index("| M:")
        return f"E:{new_score}" + commnt[idx:]
    return f"E:{new_score}"


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with RekordboxDB() as db:
        con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
        con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

        tracks = con.execute("""
            SELECT c.ID, c.BPM, c.FolderPath, c.Commnt, c.Length
            FROM djmdContent c
            WHERE c.rb_local_deleted=0 AND c.BPM > 0
        """).fetchall()

        print(f"Procesando {len(tracks)} tracks con energy v2...")

        updated = 0
        skipped_manual = 0
        no_audio = 0

        for cid, bpm_raw, path, commnt, length_ms in tracks:
            bpm = (bpm_raw or 12200) / 100

            # Respetar override manual
            if commnt and "| M:" in commnt:
                skipped_manual += 1
                continue

            timings = get_cue_timings(con, str(cid))
            if not timings:
                continue

            # Groove ratio
            gr = None
            if path and Path(path).exists():
                try:
                    gr = compute_groove_ratio(path, bpm)
                except Exception:
                    gr = None
            else:
                no_audio += 1

            score = calculate_energy_v2(
                bpm=bpm,
                bass_in_ms=timings.get("bass_in"),
                breakdown_ms=timings.get("breakdown"),
                drop_ms=timings.get("drop"),
                outro_ms=timings.get("outro"),
                track_length_ms=length_ms,
                groove_ratio=gr,
            )

            new_commnt = set_score(commnt or "", score)
            con.execute(
                "UPDATE djmdContent SET Commnt=?, updated_at=? WHERE ID=?",
                (new_commnt, ts, str(cid))
            )
            updated += 1

            if updated % 50 == 0:
                con.commit()
                print(f"  {updated}/{len(tracks)} procesados...")

        con.commit()
        con.close()

    with RekordboxDB() as db2:
        print(f"\nDB integrity: {db2.integrity_check()}")

    print(f"\n=== Energy v2 aplicado ===")
    print(f"  Actualizados:        {updated}")
    print(f"  Sin audio (skipped): {no_audio}")
    print(f"  Overrides manuales:  {skipped_manual} (preservados)")


if __name__ == "__main__":
    main()
