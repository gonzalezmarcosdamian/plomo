"""Completa key y BPM de un setlist de referencia cruzando contra Muzpa.

`ingest_setlist.py` enriquece contra la biblioteca propia, y ahi esta el techo:
un setlist de otro DJ se solapa con la coleccion propia en un 6-30%, muy por
debajo del 80% que `backtest_rules.py` exige para dar un veredicto. Sin key ni
BPM el corpus de referencia existe pero no mide nada, y la circularidad que
denuncia docs/APRENDIZAJES.md sigue sin resolverse.

Muzpa tiene key y BPM de casi todo el catalogo progresivo, incluso de lo que no
tenemos. Este script los trae. La energia NO: esa la calcula el pipeline propio
sobre el archivo, asi que las reglas de energia siguen sin evidencia externa.

El cruce NO usa el artista como parte de la clave: las fuentes lo escriben
distinto ("D-Shift & Drunken Kong" vs "Drunken Kong, D-SHIFT") y por ese lado se
pierde la mitad de los matches. Se cruza por titulo + remixer, y el artista se
usa despues como confirmacion.

Uso:
    python scripts/enrich_setlist.py data/setlists/*.json
    python scripts/enrich_setlist.py data/setlists/x.json --dry
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(RAIZ / ".env")

from plomo.matching import GENERICOS  # noqa: E402
from muzpa_download import get_session, search  # noqa: E402

_NO_ALNUM = re.compile(r"[^a-z0-9]")
_PARENTESIS = re.compile(r"[(\[]([^)\]]*)[)\]]")


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()


def clave_titulo(titulo: str) -> str:
    """Titulo + nombre del remixer, sin el artista. 'Mantra (Extended Mix)' -> mantra."""
    manos = []
    for tramo in _PARENTESIS.findall(titulo or ""):
        manos += [p for p in _NO_ALNUM.sub(" ", _ascii(tramo).lower()).split()
                  if p and p not in GENERICOS]
    base = _PARENTESIS.sub("", titulo or "")
    return _NO_ALNUM.sub("", _ascii(base).lower()) + "".join(sorted(set(manos)))


def tokens(s: str) -> set[str]:
    return {p for p in _NO_ALNUM.sub(" ", _ascii(s).lower()).split() if len(p) > 2}


def partir(fullname: str) -> tuple[str, str]:
    art, _, tit = (fullname or "").partition(" - ")
    return art.strip(), tit.strip()


def _substring_confiable(a: str, b: str) -> bool:
    """Uno contiene al otro y son parecidos de largo.

    Sin el piso de largo, "Asia" entra en "Anastasia" y "Go" en cualquier cosa.
    """
    if not (a in b or b in a):
        return False
    corto, largo = sorted((a, b), key=len)
    return len(corto) >= 6 and len(corto) / len(largo) >= 0.6


def elegir(cands: list[dict], artist: str, title: str) -> dict | None:
    """Mejor candidato de Muzpa, o None si ninguno da confianza suficiente."""
    objetivo = clave_titulo(title)
    # Un titulo "ID" es un hueco, no un titulo: "id" es substring de medio
    # catalogo ("Same Idea", "Identity") y matchea cualquier cosa del artista.
    if not objetivo or objetivo == "id":
        return None
    art_tok = tokens(artist)
    mejor, mejor_score = None, 0.0
    for c in cands:
        c_art, c_tit = partir(c.get("fullname", ""))
        k = clave_titulo(c_tit)
        if k == objetivo:
            score = 2.0
        elif _substring_confiable(objetivo, k):
            score = 1.0
        else:
            continue
        # el artista confirma, no identifica: sumar si algun token coincide
        if art_tok & tokens(c_art):
            score += 1.0
        if c.get("bpm"):
            score += 0.1
        if c.get("key"):
            score += 0.1
        if score > mejor_score:
            mejor, mejor_score = c, score
    # titulo exacto solo no alcanza si el artista no confirma y el titulo es corto
    return mejor if mejor_score >= 2.0 else None


def _orientacion_invertida(doc: dict, s, muestra: int = 10) -> bool:
    """True si el tracklist viene como 'Titulo - Artista' en vez de 'Artista - Titulo'.

    Pasa seguido: varios canales publican el tracklist al reves. Cargado asi el
    setlist entra al corpus con 0% de cobertura y no mide nada, pero ocupa lugar
    y ensucia el conteo de artistas de la lista de compras.

    Se prueban las dos orientaciones sobre una muestra y gana la que matchea mas.
    """
    nombrados = [t for t in doc["tracks"]
                 if not t.get("es_id") and (t.get("title") or "").strip().lower() != "id"]
    if len(nombrados) < 6:
        return False
    paso = max(1, len(nombrados) // muestra)
    derecho = invertido = 0
    for t in nombrados[::paso][:muestra]:
        cands = search(s, f"{t['artist']} {t['title']}") or []
        if elegir(cands, t["artist"], t["title"]):
            derecho += 1
        cands2 = search(s, f"{t['title']} {t['artist']}") or []
        if elegir(cands2, t["title"], t["artist"]):
            invertido += 1
    return invertido >= 3 and invertido >= derecho * 2


def enriquecer(doc: dict, s) -> tuple[int, int, list[str]]:
    faltan = [t for t in doc["tracks"]
              if not t.get("es_id") and (t.get("key") is None or t.get("bpm") is None)]
    ok, log = 0, []
    for t in faltan:
        cands = search(s, f"{t['artist']} {t['title']}") or []
        if not cands:
            cands = search(s, t["title"]) or []
        m = elegir(cands, t["artist"], t["title"])
        if not m:
            log.append(f"    [--] {t['artist']} - {t['title']}")
            continue
        if t.get("key") is None and m.get("key"):
            t["key"] = m["key"]
        if t.get("bpm") is None and m.get("bpm"):
            t["bpm"] = float(m["bpm"])
        if t.get("key") is None and t.get("bpm") is None:
            log.append(f"    [--] {t['artist']} - {t['title']} (match sin key ni bpm)")
            continue
        t["fuente_datos"] = t.get("fuente_datos") or "muzpa"
        t["muzpa_fullname"] = m.get("fullname", "")
        ok += 1
        log.append(f"    [OK] {t['artist']} - {t['title']}  ->  {m.get('fullname','')[:60]} "
                   f"| {m.get('bpm')} BPM | {m.get('key')}")
    return ok, len(faltan), log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivos", nargs="+", type=Path)
    ap.add_argument("--dry", action="store_true", help="no escribe, solo reporta")
    args = ap.parse_args()

    s = get_session()
    if not s:
        sys.exit("sin sesion de Muzpa")

    for f in args.archivos:
        doc = json.loads(f.read_text(encoding="utf-8"))
        if not doc.get("orden_campos_revisado"):
            if _orientacion_invertida(doc, s):
                for t in doc["tracks"]:
                    t["artist"], t["title"] = t["title"], t["artist"]
                doc["orden_invertido_corregido"] = True
                print(f"  {f.name}: venia como 'Titulo - Artista', se dio vuelta")
            doc["orden_campos_revisado"] = True
        ok, total, log = enriquecer(doc, s)
        nombrados = doc.get("n_identificados") or sum(
            1 for t in doc["tracks"] if not t.get("es_id"))
        con_key = sum(1 for t in doc["tracks"] if not t.get("es_id") and t.get("key"))
        con_bpm = sum(1 for t in doc["tracks"] if not t.get("es_id") and t.get("bpm"))
        print(f"\n{f.name}")
        for l in log:
            print(l)
        print(f"  resueltos {ok}/{total} | key {con_key}/{nombrados} "
              f"({con_key/nombrados:.0%}) | bpm {con_bpm}/{nombrados} "
              f"({con_bpm/nombrados:.0%})")
        doc["cobertura_key"] = round(con_key / nombrados, 3) if nombrados else 0.0
        doc["cobertura_bpm"] = round(con_bpm / nombrados, 3) if nombrados else 0.0
        if not args.dry:
            f.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
