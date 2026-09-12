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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.camelot import distance as _cam_dist_canonico  # noqa: E402
from plomo.rules import R  # noqa: E402

# Los numeros no viven aca: viven en rules/curaduria.json con su porque y su
# evidencia, para que el agente analista pueda medirlos y discutirlos.
BEAM = R.get("solver.beam")
MIN_GAP = R.get("repeticion.separacion_minima_codigo", 3)  # separacion entre temas del mismo productor
MAX_E_STEP = R.get("energia.max_escalon")
MAX_CAM = R.get("armonia.max_camelot_dist")
MAX_RETROCESO = R.get("energia.max_retroceso_en_subida")
PICO_PCT = R.get("energia.pico_en_pct")
CAIDA_PCT = R.get("energia.caida_post_pico_pct")
BAJA_CIERRE = R.get("energia.baja_minima_al_cierre")
PESO_ARCO = R.get("energia.peso_desvio_arco")
PESO_CAM = R.get("armonia.peso_salto_camelot")
PENAL_MISMA_KEY_DESDE = R.get("armonia.penal_misma_key_desde")
PESO_MISMA_KEY = R.get("armonia.penal_misma_key_desde_peso", 1.2)
PESO_QUIETO = R.get("armonia.penal_quedarse_en_la_rueda", 0.8)
MONOTONIA_DESDE = R.get("armonia.monotonia_desde", 2)
PESO_MONOTONIA = R.get("armonia.monotonia_desde_peso", 0.5)
SPLIT = (",", "&", " feat", " ft", " vs", " x ")
# Margen para las comparaciones contra los topes. abs(7.0 - 8.3) da
# 1.3000000000000007 en punto flotante, asi que un escalon que es exactamente
# el limite se rechazaba: se perdian vecinos musicalmente legales y el solver
# terminaba pidiendo relajar una regla que no hacia falta tocar.
EPS = 1e-9


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
# Apodo entre comillas dentro del nombre del remixer: "Jonathan Kaspar
# 'Midnight' Remix" y "... 'Sunrise' Remix" son la misma mano, y sin sacarlo el
# dedup los tomaba por dos productores distintos y metia las dos versiones del
# mismo tema en el mismo set.
APODO_RE = re.compile(r"\s*['‘’\"][^'‘’\"]{2,}['‘’\"]\s*")


def _clean(name: str) -> str:
    """Normaliza un nombre de productor quitando sufijos de version."""
    n = APODO_RE.sub(" ", name).strip().lower()
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


# Habia DOS definiciones de distancia Camelot en el repo: esta, que daba 0 al
# cambio de relativa (8A -> 8B), y la de src/plomo/camelot.py, que le da 1. El
# solver optimizaba con una y el auditor y el backtest median con la otra. El
# impacto medido es chico —ese caso aparece en el 0% de las transiciones de
# referencia y el 3% de las tocadas— pero no se pueden discutir los pesos con
# dos varas distintas. Queda la de plomo.camelot, que es la que usa todo lo demas.
cam_dist = _cam_dist_canonico


def _paso_firmado(ca, cb):
    """Cuanto y hacia donde se movio en la rueda: -6..+6, 0 = se quedo.

    Trabaja sobre el numero de rueda solamente. El cambio de modo (A<->B) ya lo
    cobra cam_dist; aca interesa si el set avanza o se queda clavado.
    """
    if not ca or not cb:
        return 0
    d = (cb[0] - ca[0]) % 12
    return d if d <= 6 else d - 12


def arc_target(i, n, lo, hi, hi_at=PICO_PCT):
    t = i / (n - 1)
    if t <= hi_at:
        return lo + (hi - lo) * (t / hi_at)
    return hi - (hi - lo) * CAIDA_PCT * ((t - hi_at) / (1 - hi_at))


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
                    if d > MAX_CAM:
                        continue
                    if abs(t["bpm"] - prev["bpm"]) > max_bpm_jump + EPS:
                        continue
                    # no retroceder energia durante la subida
                    if (i / (n - 1) <= PICO_PCT
                            and t["energy"] < prev["energy"] - MAX_RETROCESO - EPS):
                        continue
                    # ningun escalon brusco: el crowd tiene que no notar el cambio
                    if abs(t["energy"] - prev["energy"]) > MAX_E_STEP + EPS:
                        continue
                    # el cierre siempre baja del pico — nunca terminar arriba
                    if i == n - 1 and t["energy"] > max(x["energy"] for x in seq) - BAJA_CIERRE:
                        continue
                    # quedarse clavado en la misma key aburre: penalizar la
                    # tercera repeticion en adelante, premiar el movimiento
                    same = 0
                    for prv in reversed(seq):
                        if prv["_cam"][0] == t["_cam"][0]:
                            same += 1
                        else:
                            break
                    step = d * PESO_CAM + max(0, same - PENAL_MISMA_KEY_DESDE + 1) * PESO_MISMA_KEY
                    # Quedarse en la misma rueda costaba CERO, y por eso pasaba
                    # el 38% de las veces contra el 23% de lo que el DJ toca de
                    # verdad y el 14% de los sets de referencia. El set no sonaba
                    # mal transicion por transicion: sonaba igual de punta a punta.
                    paso = _paso_firmado(prev["_cam"], t["_cam"])
                    if paso == 0:
                        step += PESO_QUIETO
                    else:
                        # Subir siempre un paso hacia el mismo lado aburre igual
                        # que no moverse. Se penaliza desde la tercera seguida.
                        corrida = 0
                        ant = prev
                        for prv in reversed(seq[:-1]):
                            if _paso_firmado(prv["_cam"], ant["_cam"]) == paso:
                                corrida += 1
                                ant = prv
                            else:
                                break
                        if corrida >= MONOTONIA_DESDE:
                            step += (corrida - MONOTONIA_DESDE + 1) * PESO_MONOTONIA
                else:
                    step = 0.0
                c = cost + abs(t["energy"] - tgt) * PESO_ARCO + step
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
