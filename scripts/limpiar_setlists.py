"""Limpia restos de formato en los campos artista/titulo del corpus de setlists.

Los tracklists vienen de fuentes que los escriben de mil maneras y el parser se
fue arreglando sobre la marcha. Los setlists cargados ANTES de cada arreglo
quedaron con la basura adentro: "- 07:00: Nathan Fake" como nombre de artista,
titulos terminados en " /", numeraciones pegadas.

Reparsear todo no se puede: los archivos de origen se descartan despues de
cargar. Esto limpia en el lugar, es idempotente, y no toca la secuencia ni los
datos de key/BPM que costaron una pasada entera de Muzpa.

Uso:
    python scripts/limpiar_setlists.py --dry
    python scripts/limpiar_setlists.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent

# "- 07:00:", "[1:23:45]", "01.", "3)", "12," al principio del campo
BASURA = re.compile(
    r"^\s*(?:[-*•–—]\s*)*"          # bullets
    r"(?:\[?\d{1,2}[:.]\d{2}(?::\d{2})?\]?\s*:?\s*)*"  # timestamps, con o sin ':'
    r"(?:\d{1,3}[.),]\s*)*"                        # numeracion
)
COLA = re.compile(r"[\s/\-–—:]+$")


def limpiar(txt: str) -> str:
    t = BASURA.sub("", txt or "").strip()
    t = COLA.sub("", t).strip()
    return t or (txt or "").strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    tocados = cambios = 0
    for f in sorted((RAIZ / "data" / "setlists").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        n = 0
        for t in d.get("tracks", []):
            a, ti = limpiar(t.get("artist", "")), limpiar(t.get("title", ""))
            if a != t.get("artist") or ti != t.get("title"):
                if n < 3:
                    print(f"    {t.get('artist','')[:34]} | {t.get('title','')[:30]}")
                    print(f"      -> {a[:34]} | {ti[:30]}")
                t["artist"], t["title"] = a, ti
                n += 1
        if n:
            tocados += 1
            cambios += n
            print(f"  {f.name[:60]}: {n} campos")
            if not args.dry:
                f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{cambios} campos limpiados en {tocados} setlists"
          + ("  [dry]" if args.dry else ""))


if __name__ == "__main__":
    main()
