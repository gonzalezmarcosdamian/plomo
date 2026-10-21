# -*- coding: utf-8 -*-
"""Lo que esta corriendo: cada proceso largo queda anotado, para retomarlo despues de un corte.

POR QUE
-------
El 2026-10-20 una sesion se corto con el render de la Session 04 a medias, y la siguiente tuvo que
reconstruir desde las conversaciones viejas que proceso era, que log escribia y que faltaba. Ese
mismo dia un reinicio de la PC corto una subida a YouTube y quedo un video roto en el canal que
nadie vio hasta que el DJ pregunto. `sin_ventana.py` anota aca cada trabajo al arrancar y al
terminar, y `scripts/en_curso.py` lo muestra: vivo, muerto o terminado, con la ultima linea del log.

Es estado de esta maquina, no del proyecto: data/en_curso.json no se versiona.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
REGISTRO = RAIZ / "data" / "en_curso.json"
GUARDAR_TERMINADOS = 30


def leer() -> list[dict]:
    try:
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _escribir(trabajos: list[dict]) -> None:
    corriendo = [t for t in trabajos if t["estado"] == "corriendo"]
    terminados = [t for t in trabajos if t["estado"] != "corriendo"][-GUARDAR_TERMINADOS:]
    tmp = REGISTRO.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(corriendo + terminados, ensure_ascii=False, indent=1), encoding="utf-8")
    for _ in range(5):                      # otra sesion puede estar escribiendo al mismo tiempo
        try:
            tmp.replace(REGISTRO)
            return
        except PermissionError:
            time.sleep(0.2)


def anotar(log: str, script: str, args: list[str]) -> str:
    ident = f"{datetime.now():%Y%m%d-%H%M%S}-{os.getpid()}"
    trabajos = leer()
    trabajos.append({"id": ident, "pid": os.getpid(), "script": script, "args": args, "log": log,
                     "desde": f"{datetime.now():%Y-%m-%d %H:%M:%S}", "estado": "corriendo"})
    _escribir(trabajos)
    return ident


def cerrar(ident: str, estado: str, codigo: int | str | None = None) -> None:
    trabajos = leer()
    for t in trabajos:
        if t["id"] == ident:
            t.update(estado=estado, codigo=codigo, hasta=f"{datetime.now():%Y-%m-%d %H:%M:%S}")
    _escribir(trabajos)


def vivo(pid: int) -> bool:
    try:
        import psutil
        return psutil.pid_exists(pid)
    except ImportError:
        return True
