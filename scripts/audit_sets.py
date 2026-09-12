"""Audita los sets activos: arco de energia, saltos Camelot y BPM."""
import re
import sys

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import sqlcipher3

from plomo import config
from plomo.rules import R

# Los umbrales salen de rules/curaduria.json, no de numeros sueltos aca. Antes
# esta herramienta usaba 1.2 para el escalon de energia y 0.55 para la posicion
# del pico, mientras la regla decia 1.3 y 0.82: auditar un set daba resultados
# distintos que medirlo, y las dos cosas se hacen en el mismo proyecto.
MAX_ESCALON = R.get("energia.max_escalon")
PICO_PCT = R.get("energia.pico_en_pct")
EPS = 1e-9

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


def _metricas_de_set(filas: list[tuple]) -> None:
    """Lo que no se ve mirando las transiciones de a una.

    Un set puede tener cero transiciones flojas y aun asi no ir a ningun lado:
    todas las mezclas legales y la misma tonalidad de punta a punta. Estas
    metricas miran el SET, no el par.
    """
    keys = [camelot(f[3] or "") for f in filas]
    pasos = []
    for a, b in zip(keys, keys[1:]):
        if a and b:
            d = (b[0] - a[0]) % 12
            pasos.append(d if d <= 6 else d - 12)
    if pasos:
        quietos = sum(1 for p in pasos if p == 0) / len(pasos)
        corrida = mejor = 1
        for x, y in zip(pasos, pasos[1:]):
            corrida = corrida + 1 if (x == y and x != 0) else 1
            mejor = max(mejor, corrida)
        aviso = ""
        if quietos > 0.35:
            aviso = "  <-- se queda clavado (real: 23%, referencia: 14%)"
        elif mejor >= 4:
            aviso = "  <-- escalera monotona"
        print(f"  >> movimiento: {quietos:.0%} sin mover la rueda, "
              f"corrida monotona mas larga {mejor}{aviso}")

    sellos = [(i, (f[5] or "").strip()) for i, f in enumerate(filas)]
    pegados = [(a[1], b[0] + 1, a[0] + 1) for a, b in zip(sellos, sellos[1:])
               if a[1] and a[1] == b[1]]
    if pegados:
        print(f"  >> AVISO: sello repetido en posiciones seguidas: "
              + ", ".join(f"{s} (#{i}-#{j})" for s, j, i in pegados[:4]))

    bs, es = [], []
    for f in filas:
        m = re.match(r"E:(\d+(?:\.\d+)?)", f[4] or "")
        if f[2] and m:
            bs.append(f[2])
            es.append(float(m.group(1)))
    if len(bs) == len(es) and len(bs) >= 6:
        mb, me = sum(bs) / len(bs), sum(es) / len(es)
        num = sum((x - mb) * (y - me) for x, y in zip(bs, es))
        den = (sum((x - mb) ** 2 for x in bs) * sum((y - me) ** 2 for y in es)) ** 0.5
        if den:
            r = num / den
            extra = "  <-- la energia la esta poniendo el tempo" if r > 0.75 else ""
            print(f"  >> corr(BPM, energia): {r:+.2f}   "
                  f"BPM {min(bs):.0f}-{max(bs):.0f} (recorrido {max(bs)-min(bs):.0f}){extra}")


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
        SELECT ar.Name, c.Title, c.BPM/100.0, k.ScaleName, c.Commnt, lb.Name
        FROM djmdSongPlaylist sp
        JOIN djmdContent c ON c.ID = sp.ContentID
        LEFT JOIN djmdArtist ar ON ar.ID = c.ArtistID
        LEFT JOIN djmdKey k ON k.ID = c.KeyID
        LEFT JOIN djmdLabel lb ON lb.ID = c.LabelID
        WHERE sp.PlaylistID = ? AND sp.rb_local_deleted = 0
        ORDER BY sp.TrackNo
        """,
        (row[0],),
    ).fetchall()

    print(f"\n{'='*70}\n{row[1]}")
    issues = []
    prev = None
    for i, (artist, title, bpm, key, commnt, _label) in enumerate(tracks, 1):
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
            if pe and e and e - pe > MAX_ESCALON + EPS:
                flags.append(f"ENERGIA salto +{e-pe:.1f}")
            if pe and e and pe - e > MAX_ESCALON + EPS and i < len(tracks) - 1:
                flags.append(f"ENERGIA bajon -{pe-e:.1f}")
        mark = "  <-- " + " | ".join(flags) if flags else ""
        if flags:
            issues.append((i, flags))
        es = f"E{e:.1f}" if e else "E?  "
        print(f"  {i:2d}. {es} {bpm:5.1f} {key or '?':>4} | {artist} - {title}"[:98] + mark)
        prev = (e, bpm, key)

    energies = [
        float(re.match(r"E:(\d+(?:\.\d+)?)", c or "").group(1))
        for _a, _t, _b, _k, c, _l in tracks
        if re.match(r"E:(\d+(?:\.\d+)?)", c or "")
    ]
    if energies:
        peak_at = energies.index(max(energies)) + 1
        pct = peak_at / len(tracks)
        print(
            f"  >> arco: {energies[0]:.1f} -> pico {max(energies):.1f} (#{peak_at}, {pct:.0%}) -> {energies[-1]:.1f}"
        )
        if pct < PICO_PCT - 0.27:
            print("  >> AVISO: el pico llega temprano (<55% del set)")
    print(f"  >> {len(issues)} transiciones flojas")
    _metricas_de_set(tracks)

con.close()
