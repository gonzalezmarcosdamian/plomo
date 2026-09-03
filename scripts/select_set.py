"""Selecciona un set desde un pool respetando escalera Camelot + arco de energia.

A diferencia de reordenar (que trabaja con una seleccion ya fija), aca se ELIGE
que tracks entran. Es la unica forma de que key y energia no se contradigan.

Beam search: en cada posicion se prueba cada candidato cuyo key este a distancia
<=1 del anterior, penalizando el desvio del arco. Se conservan los mejores K.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BEAM = 400
MIN_GAP = 3      # tracks minimos entre dos temas del mismo productor
MAX_E_STEP = 1.3 # escalon maximo de energia entre tracks consecutivos
SPLIT = (",", "&", " feat", " ft", " vs", " x ")


REMIX_RE = re.compile(
    r"[(\[]([^)\]]*?)\s+(?:Remix|Mix|Edit|Version|Reinterpretation|Rework|Re-?shape|Dub)[)\]]",
    re.I,
)
NOISE = {"original", "extended", "club", "dub", "instrumental", "radio", "vocal",
         "re-shape", "the", "a", "feat", "ft"}
# Sufijos que ensucian el nombre del remixer: "Marsh Extended" / "Marsh's" no
# matcheaban con "marsh", asi que el solver metia dos temas del mismo productor.
QUALIFIERS = ("extended", "original", "club", "radio", "vocal", "instrumental",
              "dub", "long", "short", "re-shape", "reshape", "12\"", "'s")


def _clean(name: str) -> str:
    """Normaliza un nombre de productor quitando sufijos de version."""
    n = name.strip().lower()
    changed = True
    while changed:
        changed = False
        for q in QUALIFIERS:
            if q == "'s":
                if n.endswith("'s") or n.endswith("’s"):
                    n, changed = n[:-2].strip(), True
            elif n.endswith(" " + q):
                n, changed = n[: -len(q) - 1].strip(), True
            elif n.startswith(q + " "):
                n, changed = n[len(q) + 1:].strip(), True
    return n


def names(artist, title=""):
    """Nombres involucrados: campo artista + remixer citado en el titulo.

    El remixer cuenta como artista — 'Kyotto - Trigger' y 'Cary Crank - Inner
    Atlas (Kyotto Remix)' son el mismo productor dos veces en el set.
    Los sufijos de version se limpian: "Marsh's Extended Mix" -> "marsh".
    """
    raw = [artist]
    for m in REMIX_RE.finditer(title or ""):
        raw.append(m.group(1))
    parts = raw
    for sep in SPLIT:
        parts = [p for chunk in parts for p in chunk.split(sep)]
    out = set()
    for p in parts:
        p = _clean(p)
        if p and p not in NOISE:
            out.add(p)
    return out


def camelot(key):
    m = re.match(r"^(\d{1,2})([AB])$", (key or "").strip())
    return (int(m.group(1)), m.group(2)) if m else None


def cam_dist(a, b):
    ca, cb = camelot(a), camelot(b)
    if not ca or not cb:
        return 99
    ring = min((ca[0] - cb[0]) % 12, (cb[0] - ca[0]) % 12)
    return ring if ca[1] == cb[1] else (0 if ring == 0 else ring + 1)


def arc_target(i, n, lo, hi, hi_at=0.82):
    t = i / (n - 1)
    if t <= hi_at:
        return lo + (hi - lo) * (t / hi_at)
    return hi - (hi - lo) * 0.30 * ((t - hi_at) / (1 - hi_at))


def select(pool, n, e_lo, e_hi, max_bpm_jump=2.0, prefer=(), bonus=6.0,
           max_per_artist=1, beam=BEAM):
    """Devuelve la mejor secuencia de n tracks, o None.

    `prefer` son ids con descuento en el costo — sirve para forzar que el set
    estrene material nuevo sin romper las restricciones duras.
    """
    prefer = set(prefer)
    # names() y camelot() dependen solo del track: calcularlos una vez evita
    # millones de regex dentro del doble loop (beam x candidatos x posiciones).
    for t in pool:
        if "_names" not in t:
            t["_names"] = names(t["artist"], t["title"])
            t["_cam"] = camelot(t["key"])
    beams = [(0.0, [], set(), {})]  # (costo, tracks, ids, {artista: [posiciones]})
    for i in range(n):
        tgt = arc_target(i, n, e_lo, e_hi)
        nxt = []
        for cost, seq, ids, arts in beams:
            prev = seq[-1] if seq else None
            for t in pool:
                if t["id"] in ids:
                    continue
                na = t["_names"]
                # tope por productor + separacion minima: un showcase se banca
                # repetir artista, pero no dos seguidos ni tres en cinco tracks
                if any(len(arts.get(a, ())) >= max_per_artist for a in na):
                    continue
                if any(i - p < MIN_GAP for a in na for p in arts.get(a, ())):
                    continue
                if prev:
                    d = cam_dist(prev["key"], t["key"])
                    if d > 1:
                        continue
                    if abs(t["bpm"] - prev["bpm"]) > max_bpm_jump:
                        continue
                    # no retroceder energia durante la subida
                    if i / (n - 1) <= 0.82 and t["energy"] < prev["energy"] - 0.4:
                        continue
                    # ningun escalon brusco: el crowd tiene que no notar el cambio
                    if abs(t["energy"] - prev["energy"]) > MAX_E_STEP:
                        continue
                    # el cierre siempre baja del pico — nunca terminar arriba
                    if i == n - 1 and t["energy"] > max(x["energy"] for x in seq) - 0.6:
                        continue
                    # quedarse clavado en la misma key aburre: penalizar la
                    # tercera repeticion en adelante, premiar el movimiento
                    same = 0
                    for prv in reversed(seq):
                        if prv["_cam"][0] == t["_cam"][0]:
                            same += 1
                        else:
                            break
                    step = d * 0.5 + max(0, same - 1) * 1.2
                else:
                    step = 0.0
                c = cost + abs(t["energy"] - tgt) * 3.0 + step
                if t["id"] in prefer:
                    c -= bonus
                na_pos = {a: arts.get(a, ()) + (i,) for a in na}
                nxt.append((c, seq + [t], ids | {t["id"]}, {**arts, **na_pos}))
        if not nxt:
            return None
        nxt.sort(key=lambda x: x[0])
        beams = nxt[:beam]
    return beams[0]


def show(seq, prefer=()):
    prev = None
    for i, t in enumerate(seq, 1):
        flag = "  [NUEVO]" if t["id"] in set(prefer) else ""
        if prev:
            d = cam_dist(prev["key"], t["key"])
            if d >= 2:
                flag += f"  <-- CAMELOT {d}"
            if abs(t["bpm"] - prev["bpm"]) > 2:
                flag += f"  <-- BPM +{abs(t['bpm']-prev['bpm']):.0f}"
        print(
            f"  {i:2d}. E{t['energy']:.1f} {t['bpm']:5.1f} {t['key']:>4} {t['label'][:15]:15} | "
            f"{t['artist']} - {t['title']}"[:112] + flag
        )
        prev = t


if __name__ == "__main__":
    RAIZ = Path(__file__).parent.parent

    def ruta(p: str) -> Path:
        """Las rutas del config son relativas a la raiz del repo."""
        q = Path(p)
        return q if q.is_absolute() else RAIZ / q

    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    pool_all = json.loads(ruta(cfg["pool"]).read_text(encoding="utf-8"))
    # artistas ya comprometidos en otros sets — cada set mantiene identidad propia
    taken = {a.lower() for a in cfg.get("exclude_artists", [])}
    # Cuantas veces puede aparecer un mismo track en toda la tanda. Sin tope, con
    # paletas parecidas el optimizador converge al mismo optimo y salen sets
    # identicos con nombres distintos.
    tope = cfg.get("max_apariciones_por_track", 0)
    usos: dict[str, int] = {}
    for spec in cfg["sets"]:
        artistas = spec.get("artists") or ["*"]
        e_pool = spec.get("e_pool")  # [min, max] — acota el pool por energia
        generos = [g.lower() for g in spec.get("genres", [])]
        excluidos = set(spec.get("exclude_ids", []))
        if tope:
            excluidos |= {i for i, c in usos.items() if c >= tope}
        pool = [
            t for t in pool_all
            if (artistas == ["*"]
                or any(a.lower() in t["artist"].lower() for a in artistas))
            and spec["bpm"][0] <= t["bpm"] <= spec["bpm"][1]
            and (not e_pool or e_pool[0] <= t["energy"] <= e_pool[1])
            and (not generos or (t.get("genre", "") or "").lower() in generos)
            and (not spec.get("solo_sin_usar") or not t.get("usado"))
            and (not spec.get("keys") or t["key"] in spec["keys"])
            and camelot(t["key"])
            and not (names(t["artist"], t["title"]) & taken)
            and t["id"] not in excluidos
        ]
        best = select(
            pool, spec["n"], spec["e_lo"], spec["e_hi"],
            max_bpm_jump=spec.get("max_bpm_jump", 2.0),
            prefer=set(spec.get("prefer_ids", [])),
            bonus=spec.get("prefer_bonus", 6.0),
            max_per_artist=spec.get("max_per_artist", 1),
            beam=spec.get("beam", BEAM),
        )
        print(f"\n{'='*72}\n{spec['name']}  (pool {len(pool)})")
        if not best:
            print("  SIN SOLUCION — relajar restricciones")
            continue
        show(best[1], spec.get("prefer_ids", []))
        target = {
            "name": spec["name"],
            # carpeta destino en Rekordbox; build_set la resuelve por nombre
            **({"carpeta": spec["carpeta"]} if spec.get("carpeta") else {}),
            "duration_h": spec["duration_h"],
            "bpm_range": spec["bpm"],
            "max_per_artist": spec.get("max_per_artist", 1),
            "keep_order": True,
            "tracks": [
                {"artist": t["artist"], "title": t["title"], "content_id": t["id"]}
                for t in best[1]
            ],
        }
        out = ruta(cfg["targets_dir"]) / f"set_{spec['num']}.json"
        out.write_text(json.dumps(target, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  -> {out.name}")
        # Por defecto cada set del config estrena artistas: se acumulan para que
        # el siguiente no los repita. Una serie de videos independientes puede
        # querer lo contrario — cada uno lleva lo mejor de su concepto.
        for t in best[1]:
            usos[t["id"]] = usos.get(t["id"], 0) + 1
        if not cfg.get("permitir_repetir_entre_sets"):
            for t in best[1]:
                taken |= names(t["artist"], t["title"])
