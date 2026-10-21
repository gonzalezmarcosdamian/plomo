# -*- coding: utf-8 -*-
"""Corre un script del proyecto sin consola, con la salida a un log.

POR QUE
-------
El 2026-10-02 se murieron dos procesos largos lanzados por WMI: una cadena que esperaba
para mezclar y la subida de la Session 02 al 32% (el log termina en "^C"). Esos procesos
abren una ventana de consola, y una ventana que se cierra o un Ctrl+C se los lleva. Con
pythonw no hay consola: no hay ventana que cerrar ni Ctrl+C que recibir.

USO
---
    pythonw scripts/sin_ventana.py <log> <script> [args...]
    # por WMI, para que ademas sobreviva a que se cierre la sesion que lo lanzo:
    Invoke-CimMethod Win32_Process Create -Arguments @{CommandLine =
        '<venv>\\pythonw.exe scripts\\sin_ventana.py postproduction\\video\\x.log scripts\\youtube_publicar.py subir ...'}

Cada trabajo queda anotado en data/en_curso.json al arrancar y al terminar (`plomo.en_curso`):
`python scripts/en_curso.py` muestra que esta corriendo, que murio y que termino.
"""
from __future__ import annotations

import runpy
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from plomo import en_curso  # noqa: E402


def main() -> None:
    log, script, *args = sys.argv[1:]
    salida = open(log, "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = salida
    sys.argv = [script, *args]
    ident = en_curso.anotar(log, script, args)
    try:
        runpy.run_path(script, run_name="__main__")
        en_curso.cerrar(ident, "termino", 0)
    except SystemExit as e:
        if e.code not in (None, 0):
            print(f"salio con {e.code}")
            en_curso.cerrar(ident, "fallo", e.code)
            raise
        en_curso.cerrar(ident, "termino", 0)
    except BaseException:
        traceback.print_exc()
        en_curso.cerrar(ident, "fallo", "excepcion")
        raise


if __name__ == "__main__":
    main()
