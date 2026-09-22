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
# Tambien los dos umbrales que definen una transicion floja. Estaban escritos
# a mano (rueda >= 2, BPM > 2) aunque el encabezado dijera lo contrario, y al
# calibrar la armonia contra los pros el 2026-09-21 el auditor siguio marcando
# como "flojos" los pasos que los profesionales hacen todo el tiempo.
MAX_CAM = R.get("armonia.max_camelot_dist")
MAX_BPM = R.get("bpm.max_salto")
# La energia que el DJ escucho pisa la del comentario, igual que en el solver.
# Sin esto el auditor marcaba como "bajon -1.9" la entrada de Sizer al pico del
# set 139: medido 5.2 calculado, y el DJ lo escucha 7.7.
import json as _json
from pathlib import Path as _Path
_PERC_F = _Path(__file__).resolve().parent.parent / "data" / "energia_percibida.json"
def _rueda_pros() -> tuple[float, int, int]:
    """Cuanto se quedan quietos en la rueda los DJ de referencia, set por set
    (p90), y su escalera mas larga. Se mide en vivo: el aviso citaba un "14%"
    viejo cuando los pros, medidos, dan 29% de mediana."""
    import glob
    fr, esc = [], [1]
    for f in glob.glob(str(_Path(__file__).resolve().parent.parent / "data" / "setlists" / "*.json")):
        d = _json.loads(_Path(f).read_text(encoding="utf-8"))
        if not d.get("orden_confiable", True):
            continue
        ts = [t for t in d["tracks"] if camelot(t.get("key") or "")]
        ps = []
        for a, b in zip(ts, ts[1:]):
            if b["pos"] != a["pos"] + 1:
                continue
            na, nb = camelot(a["key"])[0], camelot(b["key"])[0]
            x = (nb - na) % 12
            ps.append(x if x <= 6 else x - 12)
        if len(ps) >= 5:
            fr.append(sum(1 for x in ps if x == 0) / len(ps))
            c = 1
            for x, y in zip(ps, ps[1:]):
                c = c + 1 if (x == y and x != 0) else 1
                esc.append(c)
    fr.sort()
    return (fr[int(len(fr) * 0.9)] if fr else 0.35), max(esc), len(fr)


PERCIBIDA = ({k: v["E"] for k, v in _json.loads(_PERC_F.read_text(encoding="utf-8")).items()
              if "E" in v} if _PERC_F.exists() else {})
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
        p90_quieto, esc_max, n_pros = _rueda_pros()
        if quietos > p90_quieto:
            aviso = f"  <-- mas quieto que el 90% de los pros (p90 {p90_quieto:.0%})"
        elif mejor > esc_max:
            aviso = f"  <-- escalera mas larga que la de los pros (max {esc_max} en {n_pros} sets: muestra chica)"
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
        SELECT ar.Name, c.Title, c.BPM/100.0, k.ScaleName, c.Commnt, lb.Name, c.ID
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
    tracks = [(a, t, b, k, (f"E:{PERCIBIDA[str(cid)]}" if str(cid) in PERCIBIDA else cm), lb)
              for a, t, b, k, cm, lb, cid in tracks]

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
            if d is not None and d > MAX_CAM:
                flags.append(f"CAMELOT {pkey}->{key} (salto {d})")
            if pbpm and bpm and abs(bpm - pbpm) > MAX_BPM + EPS:
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
