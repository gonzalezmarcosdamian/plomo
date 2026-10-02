# -*- coding: utf-8 -*-
"""Renderiza un video largo en tramos que se pueden retomar, sin que la maquina se duerma.

POR QUE
-------
El 2026-10-02 el render de la Session 01 (89 min) murio en el minuto 25.5: la laptop
entro en reposo moderno por inactividad, al despertar el driver de NVIDIA reinicio el
dispositivo (evento nvlddmkm 153) y el codificador murio con el. El .mov a medias no
sirve —el indice va al final— y eran dos horas perdidas.

Dos cosas:
- Mientras corre, le pide a Windows que no suspenda el sistema ni apague la pantalla
  (SetThreadExecutionState), que es lo que hace un reproductor o un editor de video.
- Renderiza tramos de 10 minutos, cada uno su archivo. Un tramo que ya esta completo
  (duracion verificada con ffprobe) no se rehace; al final se unen con concat, sin
  recodificar. Si algo corta, se relanza el mismo comando y sigue donde estaba.

USO
---
    python scripts/video_por_trozos.py --nombre session_01 --master postproduction/mixes/148_mix.wav
        --res 2560x1440 --salida postproduction/video/session_01.mov
"""
from __future__ import annotations

import argparse
import ctypes
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TRAMO_S = 600
REINTENTOS = 3                  # un tramo que falla se rehace solo antes de rendirse
ESPERA_REINTENTO_S = 90         # tras un reinicio de la NVIDIA, el driver tarda en volver
ES_CONTINUOUS, ES_SYSTEM_REQUIRED, ES_DISPLAY_REQUIRED = 0x80000000, 0x00000001, 0x00000002


def mantener_despierta(si: bool) -> None:
    banderas = ES_CONTINUOUS | (ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED if si else 0)
    ctypes.windll.kernel32.SetThreadExecutionState(banderas)


def duracion(archivo: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(archivo)],
                       capture_output=True, text=True)
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--master", required=True)
    ap.add_argument("--res", default="2560x1440")
    ap.add_argument("--codificador", default="cpu")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()

    r = np.load(RAIZ / "data" / "video" / f"{a.nombre}_rasgos.npz")
    total = len(r["cuerpo"]) / int(r["fps"])
    salida = RAIZ / a.salida
    carpeta = salida.parent / f"{salida.stem}_tramos"
    carpeta.mkdir(parents=True, exist_ok=True)
    inicios = np.arange(0, total, TRAMO_S)
    mantener_despierta(True)
    try:
        for k, ini in enumerate(inicios):
            largo = min(TRAMO_S, total - ini)
            tramo = carpeta / f"{k:03d}.mov"
            if tramo.exists() and abs(duracion(tramo) - largo) < 0.2:
                print(f"tramo {k + 1}/{len(inicios)} ya estaba", flush=True)
                continue
            print(f"tramo {k + 1}/{len(inicios)}: {ini / 60:.0f}-{(ini + largo) / 60:.1f} min", flush=True)
            for intento in range(1, REINTENTOS + 1):
                r = subprocess.run([sys.executable, "-u", str(RAIZ / "scripts" / "video_animar.py"), "--nombre",
                                    a.nombre, "--master", a.master, "--res", a.res, "--desde", f"{ini:.3f}",
                                    "--segundos", f"{largo:.3f}", "--codificador", a.codificador,
                                    "--salida", str(tramo)], cwd=RAIZ)
                if r.returncode == 0 and abs(duracion(tramo) - largo) < 0.2:
                    break
                print(f"tramo {k + 1} fallo (intento {intento}/{REINTENTOS}, codigo {r.returncode})", flush=True)
                if intento < REINTENTOS:
                    time.sleep(ESPERA_REINTENTO_S)
            if abs(duracion(tramo) - largo) >= 0.2:
                sys.exit(f"el tramo {k} quedo de {duracion(tramo):.1f} s y tenia que durar {largo:.1f}")
        lista = carpeta / "lista.txt"
        lista.write_text("".join(f"file '{carpeta / f'{k:03d}.mov'}'\n".replace("\\", "/")
                                 for k in range(len(inicios))), encoding="utf-8")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(lista), "-c", "copy", str(salida)], check=True)
    finally:
        mantener_despierta(False)
    final = duracion(salida)
    if abs(final - total) > 1.0:
        sys.exit(f"el video unido dura {final:.1f} s y el mix {total:.1f}")
    print(f"-> {salida}  ({final / 60:.1f} min, {len(inicios)} tramos)", flush=True)


if __name__ == "__main__":
    main()
