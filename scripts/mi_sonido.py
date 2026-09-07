"""Deriva "Mi Sonido" de lo que se toca, no de lo que uno cree que toca.

`docs/MI_SONIDO.md` es un documento escrito a mano en mayo de 2026 a partir de
UNA sesion con feedback. Vale mucho — de ahi salio la taxonomia entera — pero es
una foto vieja y una sola muestra. Esto mide lo mismo con todo el historial.

La pregunta que contesta no es "que track sono mas": eso premia a los artistas
de los que ya hay muchos tracks. La pregunta es **que esta sobrerrepresentado**
en lo tocado respecto de lo que hay en la biblioteca. Un sello con 109 tracks va
a sonar mas que uno con 5 aunque no guste mas; el lift corrige eso.

    lift = (share en lo tocado) / (share en la biblioteca)

Lift 1.0 = suena tanto como corresponde a su tamaño. Lift 3.0 = se elige tres
veces mas de lo que su presencia justifica. Eso ultimo es una preferencia real.

Uso:
    python scripts/mi_sonido.py
    python scripts/mi_sonido.py --json data/mi_sonido.json --batch
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_set import names  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
MIN_APARICIONES = 3     # debajo de esto el lift es ruido estadistico
# Y sobre todo: sin un piso de presencia en la biblioteca, el ranking lo ganan
# los artistas con UN solo track que sono mucho (10 reproducciones / 1 track =
# lift 18). Eso no es una preferencia, es una muestra de tamaño uno.
MIN_EN_BIBLIOTECA = 4
TOP = 20


def _con():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con


def _energia(txt: str | None) -> float | None:
    t = txt or ""
    if not t.startswith("E:"):
        return None
    try:
        return float(t[2:].split()[0].split("|")[0])
    except (ValueError, IndexError):
        return None


def cargar(con) -> tuple[list[dict], dict[str, int]]:
    """Biblioteca completa, y cuantas veces sono cada track.

    `DJPlayCount` y el conteo de `djmdSongHistory` son la MISMA cuenta: se
    verifico que coinciden en los 1816 tracks, 0 discrepancias. Sumarlas —como
    hacia esta funcion— duplicaba todo: las "1004 reproducciones" eran 502. Se
    nota a simple vista porque todos los conteos salian pares.

    Se toma el maximo de las dos por si alguna vez divergen, no la suma.
    """
    filas = con.execute(
        """SELECT c.ID, a.Name, c.Title, c.BPM/100.0, k.ScaleName, c.Commnt,
                  l.Name, g.Name, c.DJPlayCount, c.Length
           FROM djmdContent c
           LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
           LEFT JOIN djmdKey    k ON k.ID = c.KeyID
           LEFT JOIN djmdLabel  l ON l.ID = c.LabelID
           LEFT JOIN djmdGenre  g ON g.ID = c.GenreID
           WHERE c.rb_local_deleted = 0"""
    ).fetchall()

    historial: Counter = Counter()
    for cid, n in con.execute(
            """SELECT s.ContentID, COUNT(*) FROM djmdSongHistory s
               WHERE s.rb_local_deleted = 0 GROUP BY s.ContentID"""):
        historial[str(cid)] = n

    biblio = []
    for cid, artista, titulo, bpm, key, com, sello, genero, dj, largo in filas:
        try:
            reproducciones = int(dj or 0)
        except (TypeError, ValueError):
            reproducciones = 0
        biblio.append({
            "id": str(cid), "artist": artista or "?", "title": titulo or "?",
            "bpm": bpm or 0, "key": key or "?", "energy": _energia(com),
            "label": sello or "", "genre": genero or "",
            "dur_min": round((largo or 0) / 60, 1),
            "veces": max(reproducciones, historial.get(str(cid), 0)),
        })
    return biblio, historial


def _valores(t: dict, campo: str) -> set[str]:
    """Los valores de un track para ese campo.

    Para `artist` no alcanza el string crudo: "Cendryma", "Dimas Mixon,
    Cendryma" y "Muuk', Cendryma" son el mismo productor y el conteo los
    trataba como tres artistas distintos. `names()` los parte y ademas suma el
    remixer citado en el titulo, que es la regla del proyecto.
    """
    if campo == "artist":
        return names(t["artist"], t["title"])
    return {t[campo]} if t[campo] else set()


def _lift(campo: str, biblio: list[dict], tocados: list[dict]) -> list[dict]:
    """Sobrerrepresentacion de cada valor del campo en lo tocado."""
    en_bib: Counter = Counter()
    for t in biblio:
        en_bib.update(_valores(t, campo))
    en_toc: Counter = Counter()
    for t in tocados:
        for v in _valores(t, campo):
            en_toc[v] += t["veces"]
    n_bib, n_toc = sum(en_bib.values()), sum(en_toc.values())
    if not n_bib or not n_toc:
        return []

    out = []
    for valor, veces in en_toc.items():
        if veces < MIN_APARICIONES or en_bib[valor] < MIN_EN_BIBLIOTECA:
            continue
        share_toc = veces / n_toc
        share_bib = en_bib[valor] / n_bib
        out.append({
            "valor": valor, "veces": veces, "en_biblioteca": en_bib[valor],
            "lift": round(share_toc / share_bib, 2) if share_bib else 0.0,
        })
    return sorted(out, key=lambda x: -x["lift"])


def perfil(tocados: list[dict]) -> dict:
    """Banda de BPM, energia y keys de lo que suena, ponderado por veces."""
    def expandido(campo):
        return [t[campo] for t in tocados for _ in range(t["veces"])
                if t[campo] is not None and t[campo] != "?" and t[campo] != 0]

    bpms = expandido("bpm")
    ens = expandido("energy")
    keys = Counter(expandido("key"))
    return {
        "bpm_mediana": round(st.median(bpms), 1) if bpms else None,
        "bpm_p10_p90": ([round(sorted(bpms)[int(len(bpms) * .1)], 1),
                         round(sorted(bpms)[int(len(bpms) * .9)], 1)] if bpms else None),
        "energia_mediana": round(st.median(ens), 1) if ens else None,
        "energia_p10_p90": ([round(sorted(ens)[int(len(ens) * .1)], 1),
                             round(sorted(ens)[int(len(ens) * .9)], 1)] if ens else None),
        "keys_top": keys.most_common(8),
        "pct_menor": (round(sum(v for k, v in keys.items() if k.endswith("A"))
                            / sum(keys.values()) * 100) if keys else None),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=TOP)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--listar", type=int, default=25,
                    help="cuantos sin tocar mostrar con --batch (0 = todos)")
    ap.add_argument("--batch", action="store_true",
                    help="ademas, lista los tracks SIN TOCAR de los artistas y "
                         "sellos que mas se eligen")
    args = ap.parse_args()

    con = _con()
    biblio, historial = cargar(con)
    con.close()

    tocados = [t for t in biblio if t["veces"] > 0]
    total_repro = sum(t["veces"] for t in tocados)
    print(f"biblioteca: {len(biblio)} tracks | tocados alguna vez: {len(tocados)} "
          f"({len(tocados) / len(biblio):.0%}) | reproducciones: {total_repro}")

    print(f"\n{'=' * 74}\nLOS QUE MAS SUENAN")
    print(f"  {'veces':>5}  {'E':>4} {'BPM':>5} {'key':>4}  {'artista - titulo':<48} sello")
    for t in sorted(tocados, key=lambda x: -x["veces"])[:args.top]:
        e = f"{t['energy']:.1f}" if t["energy"] is not None else " -- "
        print(f"  {t['veces']:>5}  {e:>4} {t['bpm']:>5.0f} {t['key']:>4}  "
              f"{(t['artist'] + ' - ' + t['title'])[:48]:<48} {t['label'][:20]}")

    p = perfil(tocados)
    print(f"\n{'=' * 74}\nEL PERFIL, PONDERADO POR CUANTAS VECES SONO")
    print(f"  BPM       mediana {p['bpm_mediana']}   banda {p['bpm_p10_p90']}")
    print(f"  Energia   mediana {p['energia_mediana']}   banda {p['energia_p10_p90']}")
    print(f"  Keys      {p['pct_menor']}% en menor (zona A)   "
          + "  ".join(f"{k}:{v}" for k, v in p["keys_top"][:6]))

    secciones = [("artist", "ARTISTAS"), ("label", "SELLOS"), ("genre", "GENEROS")]
    lifts = {}
    for campo, titulo in secciones:
        datos = _lift(campo, biblio, tocados)
        lifts[campo] = datos
        print(f"\n{'=' * 74}\n{titulo} QUE MAS ELEGIS (lift = suena / lo que su tamaño justifica)")
        print(f"  {'lift':>5} {'suena':>6} {'tenes':>6}   nombre")
        for d in datos[:12]:
            print(f"  {d['lift']:>5.1f} {d['veces']:>6} {d['en_biblioteca']:>6}   {d['valor'][:44]}")

    if args.batch:
        artistas = {d["valor"] for d in lifts["artist"][:15]}
        sellos = {d["valor"] for d in lifts["label"][:12]}
        sin_tocar = [t for t in biblio if t["veces"] == 0
                     and (names(t["artist"], t["title"]) & artistas
                          or t["label"] in sellos)]
        sin_tocar.sort(key=lambda t: (-(t["energy"] or 0)))
        print(f"\n{'=' * 74}\nDE ESOS ARTISTAS Y SELLOS, SIN TOCAR NUNCA: {len(sin_tocar)} tracks")
        print("  (es material que ya compraste, del sonido que ya elegis, y no sono)")
        for t in (sin_tocar if args.listar == 0 else sin_tocar[:args.listar]):
            e = f"{t['energy']:.1f}" if t["energy"] is not None else " -- "
            print(f"  E{e:>4} {t['bpm']:>5.0f} {t['key']:>4}  "
                  f"{(t['artist'] + ' - ' + t['title'])[:50]:<50} {t['label'][:18]}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "n_biblioteca": len(biblio), "n_tocados": len(tocados),
            "reproducciones": total_repro, "perfil": p,
            "artistas": lifts["artist"][:30], "sellos": lifts["label"][:20],
            "generos": lifts["genre"][:15],
            "mas_sonados": sorted(tocados, key=lambda x: -x["veces"])[:50],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  -> {args.json}")


if __name__ == "__main__":
    main()
