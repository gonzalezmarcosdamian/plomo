"""Audita los sets activos: arco de energia, saltos Camelot y BPM."""
import re
import sys

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import sqlcipher3

from plomo import config

SETS = [int(a) for a in sys.argv[1:]] or [65, 66, 67, 68, 69, 70]


def camelot(key: str) -> tuple[int, str] | None:
    m = re.match(r"^(\d{1,2})([AB])$", (key or "").strip())
    return (int(m.group(1)), m.group(2)) if m else None


def cam_distance(a: str, b: str) -> int | None:
    """Distancia armonica: 0 = perfecto, 1 = vecino, >=2 = salto."""
    ca, cb = camelot(a), camelot(b)
    if not ca or not cb:
        return None
    num_a, let_a = ca
    num_b, let_b = cb
    ring = min((num_a - num_b) % 12, (num_b - num_a) % 12)
    if let_a == let_b:
        return ring
    return 0 if ring == 0 else ring + 1


con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

for num in SETS:
    row = con.execute(
        "SELECT ID, Name FROM djmdPlaylist WHERE rb_local_deleted=0 AND Name LIKE ?",
        (f"{num}. %",),
    ).fetchone()
    if not row:
        print(f"\nSet {num}: NO EXISTE")
        continue
    tracks = con.execute(
        """
        SELECT ar.Name, c.Title, c.BPM/100.0, k.ScaleName, c.Commnt
        FROM djmdSongPlaylist sp
        JOIN djmdContent c ON c.ID = sp.ContentID
        LEFT JOIN djmdArtist ar ON ar.ID = c.ArtistID
        LEFT JOIN djmdKey k ON k.ID = c.KeyID
        WHERE sp.PlaylistID = ? AND sp.rb_local_deleted = 0
        ORDER BY sp.TrackNo
        """,
        (row[0],),
    ).fetchall()

    print(f"\n{'='*70}\n{row[1]}")
    issues = []
    prev = None
    for i, (artist, title, bpm, key, commnt) in enumerate(tracks, 1):
        m = re.match(r"E:(\d+(?:\.\d+)?)", commnt or "")
        e = float(m.group(1)) if m else None
        flags = []
        if prev:
            pe, pbpm, pkey = prev
            d = cam_distance(pkey, key)
            if d is not None and d >= 2:
                flags.append(f"CAMELOT {pkey}->{key} (salto {d})")
            if pbpm and bpm and abs(bpm - pbpm) > 2:
                flags.append(f"BPM {pbpm:.0f}->{bpm:.0f} (+{abs(bpm-pbpm):.0f})")
            if pe and e and e - pe > 1.2:
                flags.append(f"ENERGIA salto +{e-pe:.1f}")
            if pe and e and pe - e > 1.2 and i < len(tracks) - 1:
                flags.append(f"ENERGIA bajon -{pe-e:.1f}")
        mark = "  <-- " + " | ".join(flags) if flags else ""
        if flags:
            issues.append((i, flags))
        es = f"E{e:.1f}" if e else "E?  "
        print(f"  {i:2d}. {es} {bpm:5.1f} {key or '?':>4} | {artist} - {title}"[:98] + mark)
        prev = (e, bpm, key)

    energies = [
        float(re.match(r"E:(\d+(?:\.\d+)?)", c or "").group(1))
        for *_, c in tracks
        if re.match(r"E:(\d+(?:\.\d+)?)", c or "")
    ]
    if energies:
        peak_at = energies.index(max(energies)) + 1
        pct = peak_at / len(tracks)
        print(
            f"  >> arco: {energies[0]:.1f} -> pico {max(energies):.1f} (#{peak_at}, {pct:.0%}) -> {energies[-1]:.1f}"
        )
        if pct < 0.55:
            print("  >> AVISO: el pico llega temprano (<55% del set)")
    print(f"  >> {len(issues)} transiciones flojas")

con.close()
