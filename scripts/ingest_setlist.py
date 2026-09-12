"""Convierte un tracklist pegado en texto a un setlist medible en data/setlists/.

El backtest necesita setlists REALES y EN ORDEN. Los datos que hay en
`data/setlists_muzpa.json` son repertorio por DJ, no secuencias: sirven para
medir paleta (BPM, keys, sellos) pero no transiciones. Este script produce lo
otro: la secuencia, con key/BPM/energia enriquecidos desde la biblioteca propia
cuando el track existe.

Uso:
    python scripts/ingest_setlist.py --dj "John Digweed" --evento "Transitions 1050" \
        --fecha 2026-01-10 --fuente https://... < tracklist.txt

Formato de entrada (una linea por track, se ignoran vacias y encabezados):
    01. Artista - Titulo (Remix)
    Artista - Titulo
    [00:12:30] Artista - Titulo
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.camelot import from_musical  # noqa: E402
from plomo.matching import clave  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DEST = RAIZ / "data" / "setlists"
POOL = RAIZ / "data" / "pool.json"

LINEA = re.compile(
    r"^\s*(?:\[?\d{1,2}[:.]\d{2}(?::\d{2})?\]?)?\s*"   # timestamp opcional
    r"(?:[-*•–—]\s+)?"                          # bullet al principio de la linea
    r"(?:\d{1,3}[.),]\s*|\d{1,3}\s+)?"                  # numeracion: "3." "3)" "3," o "3 "
    r"(?P<artist>.+?)\s+[-–—]\s+(?P<title>.+?)\s*$"
)
RUIDO = re.compile(r"^(tracklist|setlist|w/|\s*$)", re.I)
# Timestamp al FINAL del titulo: "Artista - Titulo (1:23:45)". Si no se saca,
# el titulo nunca matchea contra el pool.
COLA_TS = re.compile(r"\s*[(\[]\d{1,2}[:.]\d{2}(?::\d{2})?[)\]]\s*$")
ES_ID = re.compile(r"^id$", re.I)


def _sin_columnas(linea: str) -> str:
    """Deja solo la columna que tiene el 'Artista - Titulo'.

    Varios tracklists vienen en columnas separadas por tab:
    "01<TAB>0:05:27<TAB>Fran Garay - Illusion<TAB>Mango Alley". Sin esto el
    sello se pega al titulo y el track no matchea nunca contra el pool.
    """
    if "\t" not in linea:
        return linea
    campos = [c.strip() for c in linea.split("\t") if c.strip()]
    con_guion = [c for c in campos if re.search(r"\s[-–—]\s", c)]
    return con_guion[0] if con_guion else linea.replace("\t", " ")


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def cargar_indice() -> dict[str, dict]:
    if not POOL.exists():
        return {}
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    return {clave(t["artist"], t["title"]): t for t in pool}


def parsear(lineas: list[str]) -> list[dict]:
    out: list[dict] = []
    for ln in lineas:
        if RUIDO.match(ln):
            continue
        ln = _sin_columnas(ln)
        m = LINEA.match(ln.strip())
        if not m:
            continue
        artist = m.group("artist").strip()
        title = COLA_TS.sub("", m.group("title").strip()).strip()
        # Varios tracklists cierran el titulo con " /" o " -" de separador.
        title = title.rstrip(" /-–—").strip()
        artist = artist.lstrip("-*• ").strip()
        # Los "ID - ID" NO se descartan: se guardan como hueco. Si se borraran,
        # dos tracks que estaban a cinco minutos uno del otro quedarian
        # consecutivos y el backtest mediria una transicion que nunca existio.
        out.append({
            "pos": len(out) + 1,
            "artist": artist,
            "title": title,
            "es_id": bool(ES_ID.match(artist) and ES_ID.match(title)),
        })
    return out


def enriquecer(tracks: list[dict], indice: dict[str, dict]) -> tuple[list[dict], int]:
    hits = 0
    for t in tracks:
        m = None if t.get("es_id") else indice.get(clave(t["artist"], t["title"]))
        if m:
            hits += 1
            t.update(key=m["key"], bpm=m["bpm"], energy=m["energy"],
                     label=m.get("label", ""), fuente_datos="biblioteca")
        else:
            t.setdefault("key", None)
            t.setdefault("bpm", None)
            t.setdefault("energy", None)
            t["fuente_datos"] = None
    return tracks, hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dj", required=True)
    ap.add_argument("--evento", default="")
    ap.add_argument("--fecha", default="")
    ap.add_argument("--fuente", default="")
    ap.add_argument("--archivo", type=Path, help="si no se pasa, lee de stdin")
    ap.add_argument("--orden-dudoso", action="store_true",
                    help="marcar cuando el orden de la fuente no es confiable")
    args = ap.parse_args()

    crudo = (args.archivo.read_text(encoding="utf-8") if args.archivo
             else sys.stdin.read())
    tracks = parsear(crudo.splitlines())
    if not tracks:
        sys.exit("no se parseo ningun track — revisa el formato 'Artista - Titulo'")

    tracks, hits = enriquecer(tracks, cargar_indice())
    ids = sum(1 for t in tracks if t.get("es_id"))
    nombrados = len(tracks) - ids
    doc = {
        "dj": args.dj,
        "evento": args.evento,
        "fecha": args.fecha,
        "fuente": args.fuente,
        "orden_confiable": not args.orden_dudoso,
        "n": len(tracks),
        "n_identificados": nombrados,
        "n_huecos_id": ids,
        "cobertura_datos": round(hits / nombrados, 3) if nombrados else 0.0,
        "tracks": tracks,
    }
    DEST.mkdir(parents=True, exist_ok=True)
    nombre = "_".join(x for x in [slug(args.dj), slug(args.evento or ""), args.fecha] if x)
    out = DEST / f"{nombre}.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(tracks)} posiciones ({nombrados} con nombre, {ids} huecos ID) "
          f"-> {out.relative_to(RAIZ)}")
    print(f"con key/BPM/energia desde la biblioteca: {hits}/{nombrados} "
          f"({doc['cobertura_datos']:.0%})")
    if hits < nombrados:
        print("Los que no matchearon quedan con key/bpm en null: el backtest "
              "los saltea. Para medir transiciones hace falta completar key y BPM.")


if __name__ == "__main__":
    main()
