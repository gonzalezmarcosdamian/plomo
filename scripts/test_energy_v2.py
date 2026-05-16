"""Comparativa Energy v1 vs v2 para el set Cumple del 20 v2."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
from plomo.energy_v2 import calculate_energy_v2, compute_groove_ratio
import sqlcipher3

TRACK_IDS = [
    17135379, 124672768, 48428996, 152277273, 132240681,
    111302352, 57043826, 93753672, 50268841, 213870089,
    139458182, 128016078, 135496627, 253892170, 194246173,
    28669810, 9168971, 3854653
]

# Veredictos esperados del feedback de sesión
EXPECTED = {
    'Long Time':   ('bajar', lambda d: d < 0),
    'Echosphere':  ('ok',    lambda d: True),
    'Breakdown':   ('mantener', lambda d: abs(d) < 1.5),
    'Lifeline':    ('bajar', lambda d: d < 0),
    'Undertow':    ('bajar', lambda d: d < 0),
    'Insomnia':    ('ok',    lambda d: True),
    'Haunted':     ('ok',    lambda d: True),
}


def get_cue_timings(con, cid):
    cues = con.execute(
        'SELECT Comment, InMsec FROM djmdCue WHERE ContentID=? AND rb_local_deleted=0',
        (str(cid),)
    ).fetchall()
    r = {}
    for c, ms in cues:
        if c in ('Mix-IN First Beat', 'M-First Beat'):
            r['first_beat'] = ms
        elif c in ('Bass IN', 'M-Bass IN'):
            r['bass_in'] = ms
        elif c in ('Breakdown', 'M-Breakdown'):
            r['breakdown'] = ms
        elif c in ('DROP', 'M-DROP'):
            r['drop'] = ms
        elif c == 'Mix-OUT':
            r['outro'] = ms
    return r


def main():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    header = f"{'#':>2}  {'Track':<36} {'Key':4} {'BPM':>3}  {'v1':>4}  {'GR':>5}  {'v2':>4}  {'Δ':>5}  Veredicto"
    print(header)
    print('-' * len(header))

    oks = 0
    total_check = 0

    for i, cid in enumerate(TRACK_IDS, 1):
        row = con.execute("""
            SELECT a.Name, c.Title, c.BPM, k.ScaleName,
                   c.FolderPath, c.Commnt, c.Length
            FROM djmdContent c
            LEFT JOIN djmdArtist a ON a.ID=c.ArtistID
            LEFT JOIN djmdKey k ON k.ID=c.KeyID
            WHERE c.ID=?
        """, (str(cid),)).fetchone()
        artist, title, bpm_raw, key, path, commnt, length_ms = row
        bpm = (bpm_raw or 12200) / 100

        e_v1 = 0.0
        if commnt and 'E:' in commnt:
            try:
                e_v1 = float(commnt.split('|')[0].replace('E:', '').strip())
            except ValueError:
                pass

        timings = get_cue_timings(con, cid)

        gr = None
        if path and Path(path).exists():
            try:
                gr = compute_groove_ratio(path, bpm)
            except Exception:
                gr = None

        e_v2 = calculate_energy_v2(
            bpm=bpm,
            bass_in_ms=timings.get('bass_in'),
            breakdown_ms=timings.get('breakdown'),
            drop_ms=timings.get('drop'),
            outro_ms=timings.get('outro'),
            track_length_ms=length_ms,
            groove_ratio=gr,
        )

        delta = e_v2 - e_v1
        gr_str = f"{gr:.2f}" if gr is not None else "  ?"
        delta_str = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"

        label = f"{artist or '?'[:14]} — {title}"
        short = label[:36]

        verdict = ""
        for keyword, (desc, check) in EXPECTED.items():
            if keyword in title:
                total_check += 1
                if check(delta):
                    verdict = f"OK ({desc})"
                    oks += 1
                else:
                    verdict = f"REVISAR (esperado: {desc})"
                break

        print(f"{i:>2}. {short:<36} {key or '?':4} {bpm:>3.0f}  "
              f"{e_v1:>4.1f}  {gr_str:>5}  {e_v2:>4.1f}  {delta_str:>5}  {verdict}")

    con.close()

    print()
    print(f"Validaciones: {oks}/{total_check} correctas")
    print()
    print("Interpretacion groove_ratio:")
    print("  > 0.70 = anclado oscuro (Breakdown, Shine)")
    print("  0.55-0.70 = mid groove")
    print("  < 0.55 = flotante (Long Time, Sonoma)")


if __name__ == "__main__":
    main()
