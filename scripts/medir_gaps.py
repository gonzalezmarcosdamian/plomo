"""Mide en que se diferencia un set armado por el solver de uno real.

No mide reglas (eso es `backtest_rules.py`): mide DIMENSIONES QUE EL SOLVER NI
MIRA — forma de la curva de energia, duracion de los tracks, variedad de sellos
y artistas, repeticion de tonalidad, y con que energia se arranca y se termina
en proporcion al pico.

Tres corpus, y valen cosas distintas (igual que en el backtest):

  PROPIO      data/set_targets/  - lo armo el solver. Medirle las reglas es
                                   circular; medirle lo que el solver NO mira
                                   no lo es, porque ahi el numero sale del azar
                                   de la biblioteca, no de una restriccion.
  TOCADO      data/tocados/      - lo que se toco de verdad. Matiza, no refuta.
  REFERENCIA  data/setlists/     - otros DJs. El unico que puede refutar.

Uso:
    python scripts/medir_gaps.py
    python scripts/medir_gaps.py --json informe.json
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.matching import clave as _clave  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent

# -- umbrales, nombrados para no esconder magia en los numeros ---------------
PASO_PLANO = 0.3        # |delta energia| <= esto: la rueda no se movio
MESETA_BANDA = 0.5      # tramo dentro de esta banda = meseta
MESETA_MIN = 3          # cuantos tracks seguidos hacen una meseta
MIN_PUNTOS_FORMA = 8    # puntos de energia para animarse a ajustar una recta
N_MINIMO = 40           # piso de muestra para concluir (igual que el backtest)
CORTE_TANDA_MIN = 20.0  # hueco mayor a esto = pausa, no duracion de track


# -- carga -------------------------------------------------------------------
def _indice_biblioteca() -> tuple[dict, dict]:
    """ContentID -> datos y clave(artista,titulo) -> datos.

    La energia y el sello salen de `data/pool.json`; la duracion y el anio de
    edicion salen de la DB de Rekordbox (solo lectura, sin tocar nada). Se
    indexa tambien por nombre porque los ContentID cambiaron al reconstruir la
    biblioteca: cruzar solo por ID descarta la mayoria de los sets viejos.
    """
    por_id: dict[str, dict] = {}
    pool = RAIZ / "data" / "pool.json"
    if pool.exists():
        for t in json.loads(pool.read_text(encoding="utf-8")):
            por_id[str(t["id"])] = {
                "artist": t.get("artist", ""), "title": t.get("title", ""),
                "key": t.get("key"), "bpm": t.get("bpm"),
                "energy": t.get("energy"), "label": t.get("label") or "",
                "dur_seg": t.get("dur_seg"), "anio": None,
            }
    _anios_y_duracion(por_id)
    por_nombre = {_clave(v["artist"], v["title"]): v for v in por_id.values()}
    return por_id, por_nombre


def _anios_y_duracion(por_id: dict[str, dict]) -> None:
    """Completa anio de edicion y duracion desde djmdContent (solo lectura)."""
    try:
        import sqlcipher3
        from plomo import config
        con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
        cur = con.cursor()
        cur.execute("PRAGMA key='%s'" % config.SQLCIPHER_KEY)
        cur.execute("""select c.ID, a.Name, c.Title, c.ReleaseYear, c.Length
                       from djmdContent c
                       left join djmdArtist a on a.ID = c.ArtistID""")
        filas = cur.fetchall()
        con.close()
    except Exception as e:  # DB ocupada o Rekordbox abierto: se sigue sin anio
        print(f"[aviso] sin anio/duracion de la DB: {e}", file=sys.stderr)
        return
    por_nombre = {}
    for cid, art, tit, anio, largo in filas:
        d = {"anio": anio if anio and anio > 1990 else None,
             "dur_seg": largo if largo and largo > 60 else None}
        por_nombre[_clave(art or "", tit or "")] = d
        if str(cid) in por_id:
            por_id[str(cid)].update({k: v for k, v in d.items() if v is not None})
    for v in por_id.values():
        if v["anio"] is None:
            m = por_nombre.get(_clave(v["artist"], v["title"]))
            if m:
                v["anio"] = m["anio"]
                v["dur_seg"] = v["dur_seg"] or m["dur_seg"]


def _enriquecer(t: dict, por_id: dict, por_nombre: dict) -> dict:
    m = por_id.get(str(t.get("content_id"))) or \
        por_nombre.get(_clave(t.get("artist", ""), t.get("title", "")))
    out = {
        "artist": t.get("artist", ""), "title": t.get("title", ""),
        "key": t.get("key"), "bpm": t.get("bpm"), "energy": t.get("energy"),
        "label": t.get("label") or "", "dur_seg": None, "anio": None,
        "hora": t.get("hora"),
    }
    if m:
        for c in ("key", "bpm", "energy", "label", "dur_seg", "anio"):
            if out.get(c) in (None, ""):
                out[c] = m.get(c)
    return out


def cargar(carpeta: str, por_id: dict, por_nombre: dict,
           excluir_pool: bool = False) -> list[dict]:
    sets = []
    for f in sorted((RAIZ / "data" / carpeta).glob("*.json")):
        if f.name == "set_990.json":      # copia de trabajo del 106: duplicaria
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        nombre = str(d.get("name") or d.get("evento") or f.stem)
        if excluir_pool and nombre.strip().startswith("[POOL]"):
            continue
        if d.get("orden_confiable") is False:
            continue
        ts = d.get("tracks") or []
        if not (isinstance(ts, list) and ts and isinstance(ts[0], dict)):
            continue
        sets.append({
            "nombre": nombre, "archivo": f.name, "dj": d.get("dj", "propio"),
            "tracks": [_enriquecer(t, por_id, por_nombre) for t in ts],
        })
    return sets


# -- utilidades ---------------------------------------------------------------
def _num(v):
    return v if isinstance(v, (int, float)) else None


def _serie(tracks, campo):
    """[(posicion_0based, valor)] para los tracks que tienen el campo."""
    return [(i, _num(t.get(campo))) for i, t in enumerate(tracks)
            if _num(t.get(campo)) is not None]


def _r2(puntos) -> float | None:
    """R2 de la recta ajustada: cuanto de rampa lineal tiene la curva."""
    if len(puntos) < MIN_PUNTOS_FORMA:
        return None
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return (sxy ** 2) / (sxx * syy)


def _res(vals, etiqueta, unidad="", dec=2):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"etiqueta": etiqueta, "n": 0}
    vals_o = sorted(vals)
    return {
        "etiqueta": etiqueta, "n": len(vals),
        "mediana": round(st.median(vals_o), dec),
        "media": round(st.mean(vals_o), dec),
        "p10": round(vals_o[max(0, len(vals_o) // 10)], dec),
        "p90": round(vals_o[min(len(vals_o) - 1, -max(1, len(vals_o) // 10))], dec),
        "unidad": unidad,
    }


ARTISTA_SEP = re.compile(r"\s*(?:,|&| x | X |/| feat\.? | ft\.? | vs\.? |\+)\s*", re.I)


def _artista_principal(a: str) -> str:
    a = (a or "").strip()
    if not a:
        return ""
    return ARTISTA_SEP.split(a)[0].strip().lower()


# -- 1. forma de la curva de energia ------------------------------------------
def forma(sets: list[dict]) -> dict:
    r2s, planos, meseta_larga, giros = [], [], [], []
    pasos_planos = pasos_tot = 0
    autocorr = []
    for s in sets:
        pts = _serie(s["tracks"], "energy")
        r = _r2(pts)
        if r is not None:
            r2s.append(r)
        # pares ADYACENTES (posiciones consecutivas), unicos que dicen algo de
        # la transicion; con datos salteados no se puede hablar de escalon
        ady = [(a[1], b[1]) for a, b in zip(pts, pts[1:]) if b[0] - a[0] == 1]
        if len(ady) >= 4:
            d = [b - a for a, b in ady]
            pl = sum(1 for x in d if abs(x) <= PASO_PLANO)
            pasos_planos += pl
            pasos_tot += len(d)
            planos.append(pl / len(d))
            giros.append(sum(1 for x, y in zip(d, d[1:])
                             if x * y < 0) / max(1, len(d) - 1))
            if len(d) >= 6:
                md = st.mean(d)
                num = sum((x - md) * (y - md) for x, y in zip(d, d[1:]))
                den = sum((x - md) ** 2 for x in d)
                if den:
                    autocorr.append(num / den)
        # meseta: tramo consecutivo dentro de una banda estrecha
        mejor = 0
        run = []
        for i, t in enumerate(s["tracks"]):
            e = _num(t.get("energy"))
            if e is None:
                run = []
                continue
            if run and (i - run[-1][0]) != 1:
                run = []
            run.append((i, e))
            while len(run) > 1 and (max(v for _, v in run) - min(v for _, v in run)) > MESETA_BANDA:
                run.pop(0)
            mejor = max(mejor, len(run))
        if mejor:
            meseta_larga.append(mejor)
    return {
        "r2_recta": _res(r2s, "R2 del ajuste lineal energia~posicion"),
        "frac_pasos_planos": _res(planos, "fraccion de pasos planos por set"),
        "pasos_planos_global": {"n": pasos_tot,
                                "pct": round(100 * pasos_planos / pasos_tot, 1) if pasos_tot else None},
        "meseta_mas_larga": _res(meseta_larga, "tracks seguidos dentro de +-%.1f" % MESETA_BANDA, dec=1),
        "tasa_giro": _res(giros, "fraccion de cambios de direccion"),
        "autocorr_delta": _res(autocorr, "autocorrelacion lag-1 de los saltos"),
        "sets_con_ajuste": len(r2s),
    }


# -- 2. duracion de los tracks -------------------------------------------------
def duracion(sets: list[dict]) -> dict:
    todos, ini, med, fin = [], [], [], []
    pico_dur, resto_dur = [], []
    corr = []
    for s in sets:
        ts = s["tracks"]
        n = len(ts)
        ds = [(i, _num(t.get("dur_seg"))) for i, t in enumerate(ts)
              if _num(t.get("dur_seg"))]
        if not ds:
            continue
        todos += [d for _, d in ds]
        for i, d in ds:
            p = i / max(1, n - 1)
            (ini if p <= 0.33 else med if p <= 0.66 else fin).append(d)
        es = _serie(ts, "energy")
        if len(es) >= 6:
            top = {i for i, _ in sorted(es, key=lambda p: -p[1])[:max(1, len(es) // 5)]}
            for i, d in ds:
                (pico_dur if i in top else resto_dur).append(d)
        if len(ds) >= MIN_PUNTOS_FORMA:
            r = _r2(ds)
            xs = [i for i, _ in ds]
            ys = [d for _, d in ds]
            mx, my = st.mean(xs), st.mean(ys)
            sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            if r is not None:
                corr.append(math.copysign(math.sqrt(r), sxy))
    return {
        "dur_todos_seg": _res(todos, "duracion de track (seg)", dec=0),
        "dur_primer_tercio": _res(ini, "duracion en el primer tercio (seg)", dec=0),
        "dur_tercio_medio": _res(med, "duracion en el tercio medio (seg)", dec=0),
        "dur_ultimo_tercio": _res(fin, "duracion en el ultimo tercio (seg)", dec=0),
        "dur_en_pico": _res(pico_dur, "duracion del 20% mas energetico (seg)", dec=0),
        "dur_fuera_pico": _res(resto_dur, "duracion del resto (seg)", dec=0),
        "corr_pos_duracion": _res(corr, "correlacion posicion~duracion por set"),
    }


def duracion_real_tocado(sets: list[dict]) -> dict:
    """Cuanto sono cada track de verdad, del reloj del historial."""
    mins, ratios = [], []
    for s in sets:
        ts = s["tracks"]
        horas = []
        for t in ts:
            h = t.get("hora")
            horas.append(h)
        for (a, ta), (b, tb) in zip(zip(horas, ts), zip(horas[1:], ts[1:])):
            if not a or not b:
                continue
            try:
                from datetime import datetime
                d = (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 60
            except Exception:
                continue
            if 0 < d <= CORTE_TANDA_MIN:
                mins.append(d)
                dur = _num(ta.get("dur_seg"))
                if dur:
                    ratios.append(d * 60 / dur)
    return {"minutos_por_track": _res(mins, "minutos reales por track", dec=1),
            "frac_del_track_usada": _res(ratios, "fraccion del track que suena")}


# -- 3. variedad ---------------------------------------------------------------
def variedad(sets: list[dict]) -> dict:
    sellos, artistas, max_art, max_sello = [], [], [], []
    cob_sello, anios_share, edad = [], [], []
    for s in sets:
        ts = s["tracks"]
        n = len(ts)
        if n < 6:
            continue
        arts = [_artista_principal(t["artist"]) for t in ts if t.get("artist")]
        if arts:
            c = Counter(arts)
            artistas.append(len(c) / len(arts))
            max_art.append(max(c.values()))
        ls = [t["label"].strip().lower() for t in ts if (t.get("label") or "").strip()]
        cob_sello.append(len(ls) / n)
        if len(ls) >= 6:
            c = Counter(ls)
            sellos.append(len(c) / len(ls))
            max_sello.append(max(c.values()) / len(ls))
        ys = [t["anio"] for t in ts if t.get("anio")]
        if len(ys) >= 6:
            reciente = max(ys)
            anios_share.append(sum(1 for y in ys if y >= reciente - 1) / len(ys))
            edad.append(st.median([reciente - y for y in ys]))
    return {
        "artistas_distintos_frac": _res(artistas, "artistas distintos / tracks"),
        "max_tracks_mismo_artista": _res(max_art, "tope de un mismo artista", dec=1),
        "sellos_distintos_frac": _res(sellos, "sellos distintos / tracks con sello"),
        "max_share_un_sello": _res(max_sello, "share del sello mas repetido"),
        "cobertura_sello": _res(cob_sello, "cobertura del dato de sello"),
        "frac_ultimos_2_anios": _res(anios_share, "share de temas de los 2 ultimos anios"),
        "antiguedad_mediana_anios": _res(edad, "anios entre el tema mas nuevo y la mediana", dec=1),
    }


# -- 4. tonalidad ---------------------------------------------------------------
def tonalidad(sets: list[dict], submuestra: float | None = None,
              semilla: int = 7) -> dict:
    rnd = random.Random(semilla)
    distintas, max_rep, repes_seguidas = [], [], []
    pares_rep = pares_tot = 0
    for s in sets:
        ks = [t["key"] for t in s["tracks"] if t.get("key")]
        if submuestra:
            ks = [k for k in ks if rnd.random() < submuestra]
        if len(ks) >= 6:
            c = Counter(ks)
            distintas.append(len(c) / len(ks))
            max_rep.append(max(c.values()) / len(ks))
        ady = [(a["key"], b["key"]) for a, b in zip(s["tracks"], s["tracks"][1:])
               if a.get("key") and b.get("key")]
        if ady:
            pares_tot += len(ady)
            pares_rep += sum(1 for a, b in ady if a == b)
    return {
        "keys_distintas_frac": _res(distintas, "keys distintas / tracks con key"),
        "max_share_una_key": _res(max_rep, "share de la key mas repetida"),
        "pares_misma_key": {"n": pares_tot,
                            "pct": round(100 * pares_rep / pares_tot, 1) if pares_tot else None},
    }


# -- 5. arranque y cierre --------------------------------------------------------
def bordes(sets: list[dict]) -> dict:
    ini_r, fin_r, ini_a, fin_a, caida = [], [], [], [], []
    pico_pos = []
    for s in sets:
        pts = _serie(s["tracks"], "energy")
        n = len(s["tracks"])
        if len(pts) < 5:
            continue
        pico = max(v for _, v in pts)
        if pico <= 0:
            continue
        pini = [v for i, v in pts if i <= max(1, int(0.15 * n))]
        pfin = [v for i, v in pts if i >= n - 1 - max(1, int(0.15 * n))]
        if pini:
            ini_a.append(st.mean(pini))
            ini_r.append(st.mean(pini) / pico)
        if pfin:
            fin_a.append(st.mean(pfin))
            fin_r.append(st.mean(pfin) / pico)
            caida.append(pico - st.mean(pfin))
        ipico = max(pts, key=lambda p: p[1])[0]
        pico_pos.append(ipico / max(1, n - 1))
    return {
        "energia_inicio": _res(ini_a, "energia media del 15% inicial", dec=2),
        "energia_cierre": _res(fin_a, "energia media del 15% final", dec=2),
        "inicio_sobre_pico": _res(ini_r, "inicio / pico"),
        "cierre_sobre_pico": _res(fin_r, "cierre / pico"),
        "caida_desde_pico": _res(caida, "puntos de energia del pico al cierre"),
        "pos_pico": _res(pico_pos, "posicion relativa del pico"),
    }


# -- salida ----------------------------------------------------------------------
def _fmt(d: dict) -> str:
    if not d or d.get("n", 0) == 0:
        return "sin datos"
    if "pct" in d:
        return f"{d['pct']}%  (n={d['n']})"
    return (f"mediana={d['mediana']:>7}  media={d['media']:>7}  "
            f"p10={d['p10']:>7}  p90={d['p90']:>7}  n={d['n']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    por_id, por_nombre = _indice_biblioteca()
    corpus = {
        "PROPIO": cargar("set_targets", por_id, por_nombre, excluir_pool=True),
        "TOCADO": cargar("tocados", por_id, por_nombre),
        "REFERENCIA": cargar("setlists", por_id, por_nombre),
    }
    informe: dict = {"corpus": {}}
    for nombre, sets in corpus.items():
        tracks = sum(len(s["tracks"]) for s in sets)
        informe["corpus"][nombre] = {"sets": len(sets), "tracks": tracks}
        print(f"\n{'=' * 78}\n{nombre}: {len(sets)} sets, {tracks} tracks\n{'=' * 78}")
        bloques = {
            "1. FORMA DE LA CURVA": forma(sets),
            "2. DURACION DE TRACKS": duracion(sets),
            "3. VARIEDAD": variedad(sets),
            "4. TONALIDAD": tonalidad(sets),
            "5. ARRANQUE Y CIERRE": bordes(sets),
        }
        if nombre == "TOCADO":
            bloques["2b. DURACION REAL (reloj)"] = duracion_real_tocado(sets)
        if nombre == "PROPIO":
            bloques["4b. TONALIDAD submuestreada al 55%"] = tonalidad(sets, 0.55)
        for titulo, b in bloques.items():
            print(f"\n  {titulo}")
            for k, v in b.items():
                if isinstance(v, dict):
                    print(f"    {k:28} {_fmt(v)}")
                else:
                    print(f"    {k:28} {v}")
            informe.setdefault(nombre, {})[titulo] = b
    if a.json:
        a.json.write_text(json.dumps(informe, ensure_ascii=False, indent=1),
                          encoding="utf-8")
        print(f"\n-> {a.json}")


if __name__ == "__main__":
    main()
