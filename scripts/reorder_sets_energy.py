"""
1. Calcula energy score para todos los tracks con cues
2. Guarda en djmdContent.Commnt como "E:7.5 | <comment anterior>"
3. Reordena todos los sets usando energía + Camelot
"""
import sys
import uuid as uuid_lib
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.rekordbox_db import RekordboxDB
from plomo.energy import calculate_energy, energy_label, reorder_by_energy_and_camelot
import sqlcipher3

SETS_TO_REORDER = {
    "Cattaneo — Set Definitivo":  "1648651516",
    "Simon Vuarambon — Set":      "3799821444",
    "Nick Warren — Main Progressive": "3806493069",
    "Eze Arias — Set":            "1794191870",
    "Set Romántico — Slow Burn":  "974048971",
    "Cumple del 20 — Set":        "2144500797",
    "Cena & Progressive — 2h":    "2176642189",
    "Melodic Deep 09-05":         "210233332",
}

def safe_id(): return str(random.randint(1500000000, 4000000000))
def now_str(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_cue_timings(con, content_id: str) -> dict:
    cues = con.execute(
        "SELECT Comment, InMsec FROM djmdCue WHERE ContentID=? AND rb_local_deleted=0",
        (content_id,)
    ).fetchall()
    result = {}
    for comment, in_msec in cues:
        if comment in ("Mix-IN First Beat", "M-First Beat"):
            result["first_beat"] = in_msec
        elif comment in ("Bass IN", "M-Bass IN"):
            result["bass_in"] = in_msec
        elif comment in ("Breakdown", "M-Breakdown"):
            result["breakdown"] = in_msec
        elif comment in ("DROP", "M-DROP"):
            result["drop"] = in_msec
        elif comment == "Mix-OUT":
            result["outro"] = in_msec
    return result


def main():
    with RekordboxDB() as db:
        con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
        con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

        # ── 1. Calcular energy score para todos los tracks con cues ──
        print("=== 1. Calculando energy scores ===")

        tracks_raw = con.execute("""
            SELECT c.ID, c.BPM, c.Length, k.ScaleName, c.Commnt
            FROM djmdContent c
            LEFT JOIN djmdKey k ON k.ID=c.KeyID
            WHERE c.rb_local_deleted=0 AND c.BPM > 0
        """).fetchall()

        scored = 0
        ts = now_str()
        for cid, bpm_raw, length_ms, key, commnt in tracks_raw:
            bpm = (bpm_raw or 12200) / 100
            timings = get_cue_timings(con, str(cid))

            if not timings:
                continue

            score = calculate_energy(
                bpm=bpm,
                bass_in_ms=timings.get("bass_in"),
                breakdown_ms=timings.get("breakdown"),
                drop_ms=timings.get("drop"),
                outro_ms=timings.get("outro"),
                track_length_ms=length_ms,
            )

            # Guardar en Commnt preservando contenido previo (sin E: prefix)
            prev = (commnt or "").strip()
            if prev.startswith("E:"):
                # reemplazar score anterior
                parts = prev.split("|", 1)
                prev = parts[1].strip() if len(parts) > 1 else ""

            new_commnt = f"E:{score}" + (f" | {prev}" if prev else "")
            con.execute(
                "UPDATE djmdContent SET Commnt=?, updated_at=? WHERE ID=?",
                (new_commnt, ts, str(cid))
            )
            scored += 1

        con.commit()
        print(f"  Energy scores calculados: {scored} tracks")

        # ── 2. Reordenar cada set ──
        print("\n=== 2. Reordenando sets ===")

        for set_name, pl_id in SETS_TO_REORDER.items():
            # Leer tracks actuales con su data
            rows = con.execute("""
                SELECT c.ID, a.Name, c.Title, c.BPM, k.ScaleName, c.Commnt
                FROM djmdSongPlaylist sp
                JOIN djmdContent c ON c.ID=sp.ContentID
                LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
                LEFT JOIN djmdKey k ON k.ID=c.KeyID
                WHERE sp.PlaylistID=? AND c.rb_local_deleted=0
                ORDER BY sp.TrackNo
            """, (pl_id,)).fetchall()

            if not rows:
                print(f"  ⚠️  {set_name}: sin tracks")
                continue

            tracks = []
            for cid, artist, title, bpm_raw, key, commnt in rows:
                bpm = (bpm_raw or 12200) / 100
                # Leer energy score del Commnt
                energy = 5.0
                if commnt and commnt.startswith("E:"):
                    try:
                        energy = float(commnt.split("|")[0].replace("E:", "").strip())
                    except ValueError:
                        pass
                tracks.append({
                    "id": str(cid),
                    "artist": artist or "?",
                    "title": title,
                    "bpm": bpm,
                    "key": key or "?",
                    "energy": energy,
                })

            # Reordenar
            reordered = reorder_by_energy_and_camelot(tracks)

            # Borrar entradas actuales y reescribir en nuevo orden
            con.execute("DELETE FROM djmdSongPlaylist WHERE PlaylistID=?", (pl_id,))

            max_sp = con.execute("SELECT MAX(rb_local_usn) FROM djmdSongPlaylist").fetchone()[0] or 0
            for i, t in enumerate(reordered, 1):
                max_sp += 1
                con.execute("""
                    INSERT INTO djmdSongPlaylist
                      (ID,PlaylistID,ContentID,TrackNo,UUID,
                       rb_data_status,rb_local_data_status,rb_local_deleted,rb_local_synced,
                       usn,rb_local_usn,created_at,updated_at)
                    VALUES (?,?,?,?,?,0,0,0,0,NULL,?,?,?)
                """, (safe_id(), pl_id, t["id"], i,
                      str(uuid_lib.uuid4()), max_sp, ts, ts))

            con.commit()

            # Print nuevo orden
            print(f"\n  {set_name} ({len(reordered)} tracks):")
            for i, t in enumerate(reordered, 1):
                label = energy_label(t["energy"])
                print(f"    {i:>2}. {t['bpm']:.0f} {t['key']:4} E:{t['energy']:.1f} [{label:7}] {t['artist']} — {t['title'][:45]}")

        con.close()

    with RekordboxDB() as db2:
        print(f"\nDB integrity: {db2.integrity_check()}")
        print("Listo. Abrí Rekordbox y hacé sync.")


if __name__ == "__main__":
    main()
