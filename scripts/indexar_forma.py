# -*- coding: utf-8 -*-
"""Indice de la FORMA de la biblioteca: la receta de cada tema, guardada por ID.

Los cues no alcanzan para medir forma: marcan el PRIMER breakdown, no el mas
grande (en Sizer marcan un respiro de 5 compases al 30% y no ven el breakdown de
20 compases al 60%). Lo que distingue a los favoritos del DJ es justamente la
forma —un breakdown unico y largo, un drop final largo—, asi que hace falta la
receta completa. Se calcula una vez y queda en data/recetas/lib/<id>.json.

Uso:
    python scripts/indexar_forma.py --genero "Progressive House" --bpm 121 125 --energia 5.5 8.8
    python scripts/indexar_forma.py ... --procesos 4
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(RAIZ / ".env")

import sqlcipher3  # noqa: E402
from plomo import config  # noqa: E402

DESTINO = RAIZ / "data" / "recetas" / "lib"
PY = str(RAIZ / ".venv" / "Scripts" / "python.exe")


def rutas(ids: list[str]) -> dict[str, str]:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    q = ",".join("?" * len(ids))
    return {r[0]: r[1] for r in con.execute(
        f"SELECT ID, FolderPath FROM djmdContent WHERE ID IN ({q})", ids)}


def una(cid: str, ruta: str) -> str:
    out = DESTINO / f"{cid}.json"
    if out.exists():
        return "ya"
    if not Path(ruta).exists():
        return "sin archivo"
    r = subprocess.run([PY, str(RAIZ / "scripts" / "reverse_engineer.py"), ruta,
                        "--json", str(out)], capture_output=True)
    return "ok" if r.returncode == 0 and out.exists() else "fallo"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--genero", action="append", required=True)
    ap.add_argument("--bpm", type=float, nargs=2, default=(118, 127))
    ap.add_argument("--energia", type=float, nargs=2, default=(0, 10))
    ap.add_argument("--procesos", type=int, default=4)
    a = ap.parse_args()
    pool = json.loads((RAIZ / "data" / "pool.json").read_text(encoding="utf-8"))
    ids = [t["id"] for t in pool
           if (t.get("genre") or "") in a.genero
           and a.bpm[0] <= t.get("bpm", 0) <= a.bpm[1]
           and t.get("energy") is not None and a.energia[0] <= t["energy"] <= a.energia[1]]
    DESTINO.mkdir(parents=True, exist_ok=True)
    rs = rutas(ids)
    print(f"{len(ids)} temas, {sum(1 for i in ids if (DESTINO / f'{i}.json').exists())} ya indexados")
    cuenta: dict[str, int] = {}
    with ThreadPoolExecutor(a.procesos) as ex:
        for i, res in enumerate(ex.map(lambda c: una(c, rs.get(c, "")), ids), 1):
            cuenta[res] = cuenta.get(res, 0) + 1
            if i % 50 == 0:
                print(f"  {i}/{len(ids)}  {cuenta}", flush=True)
    print("listo:", cuenta)


if __name__ == "__main__":
    main()
