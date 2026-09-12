"""Mide las reglas de curaduria contra evidencia en vez de contra el criterio.

Cada regla dura de `rules/curaduria.json` se traduce a una pregunta medible:
"que porcentaje de transiciones la viola". Se mide sobre tres corpus, que valen
cosas distintas:

  PROPIO      - los sets armados (data/set_targets/). Los produjo el solver, que
                impone las reglas: medirlas ahi es circular y no prueba nada.
  TOCADO      - el historial real de Rekordbox (data/tocados/), via
                scripts/ingest_history.py. No lo produjo el solver: es donde uno
                se desvia del plan arriba del escenario. Muestra si la regla
                describe la practica propia.
  REFERENCIA  - setlists de otros DJs (data/setlists/), via
                scripts/ingest_setlist.py. Es el unico que puede refutar: si
                Digweed viola la regla seguido y sus sets funcionan, la regla es
                una restriccion autoimpuesta y no una ley de la musica.

Uso:
    python scripts/backtest_rules.py                # todo lo que haya
    python scripts/backtest_rules.py --solo-propio
    python scripts/backtest_rules.py --json informe.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.camelot import distance as cam_dist, from_musical  # noqa: E402
from plomo.matching import clave as _clave  # noqa: E402
from plomo.rules import R  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
_COBERTURA = [0, 0, 0]
COBERTURA_MINIMA = 0.80  # debajo de esto el veredicto no vale
UMBRAL_REFUTACION = 0.15  # >15% de violaciones en sets reales refuta una regla dura
# Piso de muestra para animarse a refutar. Sin esto el backtest daba REFUTADA la
# regla de energia con n=9: nueve transiciones no refutan nada, y un veredicto
# falso es peor que ninguno porque despues se usa para cambiar una regla.
N_MINIMO_PARA_REFUTAR = 40


# -- carga de corpus --------------------------------------------------------
def _pool_indices() -> tuple[dict[str, dict], dict[str, dict]]:
    """Pool indexado por ContentID y por artista+titulo.

    El indice por nombre no es un lujo: los ContentID de Rekordbox CAMBIAN
    cuando se reconstruye la biblioteca, y este proyecto la reconstruyo despues
    de la corrupcion de junio. Los `set_targets` guardan los IDs viejos, asi que
    matchear solo por ID descarta el 68% de los tracks — y lo que queda no es
    una muestra al azar, son los sets armados despues de la reconstruccion.
    """
    p = RAIZ / "data" / "pool.json"
    if not p.exists():
        return {}, {}
    pool = json.loads(p.read_text(encoding="utf-8"))
    return ({t["id"]: t for t in pool},
            {_clave(t["artist"], t["title"]): t for t in pool})


def corpus_propio(incluir_pools: bool = False) -> list[dict]:
    """Sets propios: data/set_targets/set_*.json + datos del pool.

    Los `[POOL]` se excluyen: son material de referencia sin orden de ejecucion,
    y medirles transiciones inventa violaciones que nadie va a tocar nunca.
    """
    por_id, por_nombre = _pool_indices()
    sets = []
    global _COBERTURA
    _COBERTURA = [0, 0, 0]  # [total, por id, por nombre]
    for f in sorted((RAIZ / "data" / "set_targets").glob("set_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if not incluir_pools and str(d.get("name", "")).strip().startswith("[POOL]"):
            continue
        tracks = []
        for t in d.get("tracks", []):
            m = por_id.get(str(t.get("content_id")))
            _COBERTURA[0] += 1
            if m:
                _COBERTURA[1] += 1
            else:
                m = por_nombre.get(_clave(t.get("artist", ""), t.get("title", "")))
                if m:
                    _COBERTURA[2] += 1
            tracks.append({
                "artist": t.get("artist", ""), "title": t.get("title", ""),
                "key": m["key"] if m else None,
                "bpm": m["bpm"] if m else None,
                "energy": m["energy"] if m else None,
                "label": (m or {}).get("label", ""),
            })
        if tracks:
            sets.append({"nombre": d.get("name", f.stem), "origen": f.name,
                         "tracks": tracks})
    return sets


def corpus_tocado() -> list[dict]:
    """Sets que Gonzalo toco de verdad, del historial de Rekordbox.

    Es el corpus que rompe la circularidad sin depender de nadie: los
    `set_targets` los produjo el solver, que impone las reglas, asi que medirlas
    ahi siempre da que se cumplen. Lo tocado es donde se desvio del plan arriba
    del escenario, con key y BPM que salen de la misma DB — cobertura 100%, sin
    matcheo por nombre.

    Lo genera scripts/ingest_history.py.
    """
    sets = []
    for f in sorted((RAIZ / "data" / "tocados").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        tracks = [{
            "artist": t.get("artist", ""), "title": t.get("title", ""),
            "key": t.get("key"), "bpm": t.get("bpm"), "energy": t.get("energy"),
            "label": t.get("label", ""),
        } for t in d.get("tracks", [])]
        if tracks:
            sets.append({"nombre": d.get("evento", f.stem), "origen": f.name,
                         "tracks": tracks})
    return sets


def corpus_referencia() -> list[dict]:
    """Setlists de otros DJs cargados con ingest_setlist.py."""
    sets = []
    for f in sorted((RAIZ / "data" / "setlists").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if not d.get("orden_confiable", True):
            continue
        tracks = [{
            "artist": t.get("artist", ""), "title": t.get("title", ""),
            "key": from_musical(t["key"]) if t.get("key") else None,
            "bpm": t.get("bpm"), "energy": t.get("energy"),
            "label": t.get("label", ""),
        } for t in d.get("tracks", [])]
        if tracks:
            sets.append({
                "nombre": f"{d.get('dj')} - {d.get('evento', '')}".strip(" -"),
                "origen": f.name, "tracks": tracks})
    return sets


# -- metricas ---------------------------------------------------------------
def _pares(sets: list[dict], campo: str):
    """Transiciones consecutivas donde ambos tracks tienen el campo cargado."""
    for s in sets:
        ts = s["tracks"]
        for a, b in zip(ts, ts[1:]):
            if a.get(campo) is not None and b.get(campo) is not None:
                yield s, a, b


def medir(sets: list[dict]) -> dict:
    if not sets:
        return {"n_sets": 0}
    out: dict = {"n_sets": len(sets),
                 "n_tracks": sum(len(s["tracks"]) for s in sets)}

    ds = [cam_dist(a["key"], b["key"]) for _, a, b in _pares(sets, "key")]
    ds = [d for d in ds if d < 99]
    if ds:
        out["camelot"] = {
            "n": len(ds),
            "dist": dict(sorted(Counter(ds).items())),
            "viol_pct": sum(d > R.get("armonia.max_camelot_dist") for d in ds) / len(ds),
            "media": round(statistics.mean(ds), 2),
        }

    js = [abs(b["bpm"] - a["bpm"]) for _, a, b in _pares(sets, "bpm")]
    if js:
        out["bpm"] = {
            "n": len(js),
            "viol_pct": sum(j > R.get("bpm.max_salto") for j in js) / len(js),
            "media": round(statistics.mean(js), 2),
            "p90": round(sorted(js)[int(len(js) * 0.9)], 2),
            "max": round(max(js), 2),
        }

    es = [abs(b["energy"] - a["energy"]) for _, a, b in _pares(sets, "energy")]
    if es:
        out["escalon_energia"] = {
            "n": len(es),
            "viol_pct": sum(e > R.get("energia.max_escalon") for e in es) / len(es),
            "media": round(statistics.mean(es), 2),
            "p90": round(sorted(es)[int(len(es) * 0.9)], 2),
        }

    # forma del set: donde cae el pico y como cierra
    picos, cierres_arriba, n_forma = [], 0, 0
    for s in sets:
        ens = [t["energy"] for t in s["tracks"] if t.get("energy") is not None]
        if len(ens) < 5:
            continue
        n_forma += 1
        picos.append(ens.index(max(ens)) / (len(ens) - 1))
        if ens[-1] > max(ens) - R.get("energia.baja_minima_al_cierre"):
            cierres_arriba += 1
    if n_forma:
        out["forma"] = {
            "n_sets": n_forma,
            "pico_pct_medio": round(statistics.mean(picos), 3),
            "pico_pct_mediana": round(statistics.median(picos), 3),
            "cierra_arriba_pct": cierres_arriba / n_forma,
        }

    por_artista, por_sello = [], []
    for s in sets:
        c = Counter(t["artist"].split(",")[0].strip().lower()
                    for t in s["tracks"] if t["artist"])
        if c:
            por_artista.append(max(c.values()))
        cl = Counter((t.get("label") or "").strip().lower()
                     for t in s["tracks"] if t.get("label"))
        if cl:
            por_sello.append(max(cl.values()))
    if por_artista:
        out["repeticion"] = {
            "max_artista_observado": max(por_artista),
            "media_max_artista": round(statistics.mean(por_artista), 2),
            "max_sello_observado": max(por_sello) if por_sello else None,
        }
    return out


# -- veredictos -------------------------------------------------------------
def veredictos(prop: dict, ref: dict, toc: dict | None = None) -> list[dict]:
    """Confronta cada regla dura con lo que hacen los sets reales."""
    pruebas = [
        ("armonia.max_camelot_dist", "camelot", "salta la rueda mas de {v}"),
        ("bpm.max_salto", "bpm", "salta mas de {v} BPM"),
        ("energia.max_escalon", "escalon_energia", "escalon de energia mayor a {v}"),
    ]
    out = []
    for ruta, metrica, texto in pruebas:
        v = R.get(ruta)
        m_ref, m_pro = ref.get(metrica), prop.get(metrica)
        item = {
            "regla": ruta, "valor": v, "dura": R.es_dura(ruta),
            "porque": R.porque(ruta),
            "propio_viol_pct": m_pro["viol_pct"] if m_pro else None,
            "tocado_viol_pct": (toc or {}).get(metrica, {}).get("viol_pct"),
            "referencia_viol_pct": m_ref["viol_pct"] if m_ref else None,
            "n_referencia": m_ref["n"] if m_ref else 0,
        }
        m_toc = (toc or {}).get(metrica)
        if not m_ref and m_toc:
            # Lo tocado no es circular — no lo produjo el solver — pero es la
            # practica propia, no la de un DJ de referencia. Puede mostrar que
            # la regla no describe lo que uno hace; no puede probar que la regla
            # este mal. Por eso matiza y nunca refuta.
            item["veredicto"] = ("CONTRADICHA POR LO TOCADO"
                                 if m_toc["viol_pct"] > UMBRAL_REFUTACION
                                 else "COMPATIBLE CON LO TOCADO")
            item["detalle"] = (
                f"sin setlists de referencia todavia. En los sets que SI se "
                f"tocaron, el {m_toc['viol_pct']:.0%} de las transiciones "
                + texto.format(v=v) + f" (n={m_toc['n']}, cobertura 100%). "
                "Eso dice que la regla no describe la practica propia — no que "
                "la regla este mal. Para eso hacen falta setlists de otros DJs.")
        elif not m_ref:
            item["veredicto"] = "SIN DATOS"
            item["detalle"] = (
                "no hay setlists de referencia ni historial con este campo. "
                "Cargar con scripts/ingest_setlist.py o scripts/ingest_history.py")
        elif m_ref["n"] < N_MINIMO_PARA_REFUTAR:
            item["veredicto"] = "MUESTRA INSUFICIENTE"
            item["detalle"] = (
                f"solo {m_ref['n']} transiciones de referencia con este dato "
                f"(hacen falta {N_MINIMO_PARA_REFUTAR}). Se viola el "
                f"{m_ref['viol_pct']:.0%} pero con esa n no se decide nada. "
                "Cargar mas setlists con scripts/buscar_setlists.py.")
        elif m_ref["viol_pct"] > UMBRAL_REFUTACION:
            item["veredicto"] = "REFUTADA"
            item["detalle"] = (
                f"en sets reales el {m_ref['viol_pct']:.0%} de las transiciones "
                + texto.format(v=v)
                + f" (n={m_ref['n']}). Si esos sets funcionan, la regla dura sobra: "
                  "deberia pasar a penalizacion con peso, no a filtro.")
        elif m_ref["viol_pct"] > 0.05:
            item["veredicto"] = "MATIZADA"
            item["detalle"] = (
                f"se viola el {m_ref['viol_pct']:.0%} de las veces en sets reales "
                f"(n={m_ref['n']}): es una regla con excepciones, no absoluta. "
                "Vale como default con escape explicito.")
        else:
            item["veredicto"] = "SOSTENIDA"
            item["detalle"] = (f"los sets reales tambien la cumplen "
                               f"({m_ref['viol_pct']:.0%} de violaciones, "
                               f"n={m_ref['n']}).")
        out.append(item)

    fuente = ref if ref.get("forma") else (toc or {})
    etiqueta = "sets de referencia" if ref.get("forma") else "los sets tocados"
    if fuente.get("forma"):
        obs = fuente["forma"]["pico_pct_mediana"]
        decl = R.get("energia.pico_en_pct")
        out.append({
            "regla": "energia.pico_en_pct", "valor": decl, "dura": False,
            "porque": R.porque("energia.pico_en_pct"),
            "veredicto": "AJUSTAR" if abs(obs - decl) > 0.08 else "SOSTENIDA",
            "detalle": (f"en {etiqueta} el pico cae a la mediana del {obs:.0%} "
                        f"del set; la regla dice {decl:.0%}."),
            "n_referencia": fuente["forma"]["n_sets"],
        })
        cierra = fuente["forma"]["cierra_arriba_pct"]
        out.append({
            "regla": "energia.baja_minima_al_cierre",
            "valor": R.get("energia.baja_minima_al_cierre"), "dura": True,
            "porque": R.porque("energia.baja_minima_al_cierre"),
            "veredicto": "CONTRADICHA POR LO TOCADO" if cierra > UMBRAL_REFUTACION
                         else "COMPATIBLE CON LO TOCADO",
            "detalle": (f"el {cierra:.0%} de {etiqueta} termina arriba, sin bajar "
                        f"los {R.get('energia.baja_minima_al_cierre')} del pico."),
            "n_referencia": fuente["forma"]["n_sets"],
        })
    return out


# -- salida -----------------------------------------------------------------
def imprimir(nombre: str, m: dict) -> None:
    print(f"\n{'=' * 72}\nCORPUS {nombre}")
    if not m.get("n_sets"):
        print("  vacio")
        return
    print(f"  {m['n_sets']} sets, {m['n_tracks']} tracks")
    if m.get("cobertura"):
        c = m["cobertura"]
        marca = "" if c["pct"] >= COBERTURA_MINIMA else "   <-- MUESTRA INSUFICIENTE"
        print(f"  cobertura {c['pct']:.0%}  ({c['por_id']} por ContentID + "
              f"{c['por_nombre']} por nombre de {c['total']}){marca}")
    if "camelot" in m:
        c = m["camelot"]
        print(f"  Camelot   n={c['n']:4d}  viola>{R.get('armonia.max_camelot_dist')}: "
              f"{c['viol_pct']:6.1%}  media={c['media']}  dist={c['dist']}")
    if "bpm" in m:
        b = m["bpm"]
        print(f"  BPM       n={b['n']:4d}  viola>{R.get('bpm.max_salto')}: "
              f"{b['viol_pct']:6.1%}  media={b['media']}  p90={b['p90']}  max={b['max']}")
    if "escalon_energia" in m:
        e = m["escalon_energia"]
        print(f"  Energia   n={e['n']:4d}  viola>{R.get('energia.max_escalon')}: "
              f"{e['viol_pct']:6.1%}  media={e['media']}  p90={e['p90']}")
    if "forma" in m:
        f = m["forma"]
        print(f"  Forma     {f['n_sets']} sets  pico mediana={f['pico_pct_mediana']:.0%}  "
              f"cierran arriba={f['cierra_arriba_pct']:.0%}")
    if "repeticion" in m:
        r = m["repeticion"]
        print(f"  Repeticion  max artista en un set={r['max_artista_observado']}  "
              f"media={r['media_max_artista']}  max sello={r['max_sello_observado']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-propio", action="store_true")
    ap.add_argument("--incluir-pools", action="store_true",
                    help="mide tambien los [POOL], que no tienen orden de ejecucion")
    ap.add_argument("--json", type=Path, help="guarda el informe completo")
    args = ap.parse_args()

    print(f"reglas v{R.version}  -  umbral de refutacion {UMBRAL_REFUTACION:.0%}")
    sets_propios = corpus_propio(args.incluir_pools)
    prop = medir(sets_propios)
    total, por_id, por_nombre = _COBERTURA
    if total:
        prop["cobertura"] = {"total": total, "por_id": por_id,
                             "por_nombre": por_nombre,
                             "pct": (por_id + por_nombre) / total}
    toc = medir(corpus_tocado())
    ref = {} if args.solo_propio else medir(corpus_referencia())
    imprimir("PROPIO — armado por el solver (data/set_targets)", prop)
    imprimir("TOCADO — historial real de Rekordbox (data/tocados)", toc)
    imprimir("REFERENCIA — otros DJs (data/setlists)", ref)

    print(f"\n{'=' * 72}\nVEREDICTOS")
    vs = veredictos(prop, ref, toc)
    for v in vs:
        print(f"\n  [{v['veredicto']}] {v['regla']} = {v['valor']}")
        print(f"    {v['detalle']}")

    print(f"\n{'=' * 72}\nHIGIENE DE LAS REGLAS")
    for ruta, msg in R.conflictos():
        print(f"  [CONFLICTO] {ruta}: {msg}")
    sin = R.sin_evidencia()
    if sin:
        print(f"  [SIN EVIDENCIA] reglas duras que nadie midio: {', '.join(sin)}")

    if args.json:
        args.json.write_text(json.dumps(
            {"version_reglas": R.version, "propio": prop, "referencia": ref,
             "tocado": toc, "veredictos": vs, "conflictos": R.conflictos()},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  informe -> {args.json}")


if __name__ == "__main__":
    main()
