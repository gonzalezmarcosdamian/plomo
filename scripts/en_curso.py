# -*- coding: utf-8 -*-
"""Que esta corriendo, que murio sin terminar y que termino, con la ultima linea de cada log.

POR QUE
-------
Para retomar despues de un corte de sesion o un reinicio sin reconstruir la historia desde las
conversaciones (ver `plomo.en_curso`). Un trabajo "corriendo" cuyo proceso ya no existe murio sin
cerrar: un reinicio, la PC apagada. Ahi se mira el log antes de relanzar. Una subida a YouTube
cortada deja ademas un video roto en el canal.

USO
---
    python scripts/en_curso.py           # lo corriendo y lo de las ultimas 24 h
    python scripts/en_curso.py --todo    # tambien lo viejo
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from plomo import en_curso  # noqa: E402


def ultima_linea(log: str) -> str:
    try:
        lineas = [x.strip() for x in (RAIZ / log).read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
        return lineas[-1][:110] if lineas else "(log vacio)"
    except FileNotFoundError:
        return "(sin log)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--todo", action="store_true")
    a = ap.parse_args()
    desde = datetime.now() - timedelta(hours=24)
    trabajos = en_curso.leer()
    if not trabajos:
        print("nada anotado")
        return
    for t in trabajos:
        cuando = datetime.strptime(t["desde"], "%Y-%m-%d %H:%M:%S")
        if t["estado"] != "corriendo" and cuando < desde and not a.todo:
            continue
        estado = t["estado"]
        if estado == "corriendo" and not en_curso.vivo(t["pid"]):
            estado = "MURIO SIN TERMINAR"
        print(f"{estado:20} {t['desde']}  {Path(t['script']).name} {' '.join(t['args'])[:60]}")
        print(f"{'':20} log {t['log']}: {ultima_linea(t['log'])}")


if __name__ == "__main__":
    main()
