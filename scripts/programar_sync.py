# -*- coding: utf-8 -*-
"""Programa el sync de Spotify para cuando vuelva la cuota.

POR QUE
-------
Spotify corta `/search` con 429 y un `retry-after` que puede ser de horas --el
2026-09-28 fueron casi diez--. Leer y escribir playlists sigue andando; lo unico
que no se puede es preguntar donde esta un tema, que es lo que hace falta para
publicar uno nuevo. Esperar despierto no tiene sentido y hacerlo a mano se
olvida, asi que se programa.

Usa el Programador de tareas de Windows y no un proceso dormido: sobrevive a
cerrar la terminal, a cerrar Claude y a reiniciar la maquina.

USO
---
    python scripts/programar_sync.py                 # lee el retry-after y programa
    python scripts/programar_sync.py --sets 148 901
    python scripts/programar_sync.py --cancelar
    python scripts/programar_sync.py --estado
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TAREA = "plomo-spotify-pendiente"
CMD = RAIZ / "scripts" / "sync_pendiente.cmd"
MARGEN_MIN = 10          # despues del retry-after, por las dudas


def cuanto_falta() -> int:
    """Segundos que faltan para que vuelva /search. 0 si ya esta disponible."""
    import requests
    import spotify_sync as S
    h = {"Authorization": f"Bearer {S.acceso()}"}
    r = requests.get(S.API + "/search", headers=h,
                     params={"q": "test", "type": "track", "limit": 1}, timeout=20)
    if r.status_code != 429:
        return 0
    return int(r.headers.get("retry-after", 3600))


def escribir_cmd(sets: list[int]) -> None:
    nums = " ".join(str(n) for n in sets)
    CMD.write_text(
        "@echo off" "\r\n"
        "REM Lo programa scripts/programar_sync.py. Se puede correr a mano.\r\n"
        f"cd /d {RAIZ}\r\n"
        "set LOG=data\sync_pendiente.log\r\n"
        "echo ================================= >> %LOG%\r\n"
        "echo %DATE% %TIME% >> %LOG%\r\n"
        f".venv\Scripts\python.exe scripts\spotify_sync.py {nums} >> %LOG% 2>&1\r\n"
        f".venv\Scripts\python.exe scripts\spotify_validar.py {nums} >> %LOG% 2>&1\r\n"
        "echo. >> %LOG%\r\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", type=int, nargs="*", default=[148, 901])
    ap.add_argument("--cancelar", action="store_true")
    ap.add_argument("--estado", action="store_true")
    args = ap.parse_args()

    if args.cancelar:
        subprocess.run(["schtasks", "/delete", "/tn", TAREA, "/f"])
        return
    if args.estado:
        subprocess.run(["schtasks", "/query", "/tn", TAREA, "/fo", "LIST"])
        log = RAIZ / "data" / "sync_pendiente.log"
        if log.exists():
            print("\nultimas lineas del log:")
            print("\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-12:]))
        return

    faltan = cuanto_falta()
    if faltan == 0:
        print("la cuota YA esta disponible: corriendo el sync ahora")
        subprocess.run([sys.executable, str(RAIZ / "scripts/spotify_sync.py"),
                        *[str(n) for n in args.sets]], cwd=str(RAIZ))
        return
    cuando = datetime.now() + timedelta(seconds=faltan, minutes=MARGEN_MIN)
    escribir_cmd(args.sets)
    # PowerShell y no `schtasks`, por UNA opcion que schtasks no expone:
    # StartWhenAvailable. El 2026-09-28 la tarea quedo para las 21:35, la
    # maquina estaba apagada a esa hora, y una tarea "once" NO se recupera: al
    # dia siguiente decia "Last Run Time: 11/30/1999" y "Next Run Time: N/A".
    # Con esto, si la hora pasa con la maquina apagada, corre apenas prende.
    ps = (
        f'$a = New-ScheduledTaskAction -Execute "{CMD}"; '
        f'$t = New-ScheduledTaskTrigger -Once -At "{cuando.strftime("%Y-%m-%dT%H:%M:%S")}"; '
        '$s = New-ScheduledTaskSettingsSet -StartWhenAvailable '
        '-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; '
        f'Register-ScheduledTask -TaskName "{TAREA}" -Action $a -Trigger $t '
        '-Settings $s -Force | Out-Null'
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    print(f"la cuota vuelve en {faltan / 3600:.1f} h")
    print(f"sets {args.sets} programados para el {cuando.strftime('%d/%m a las %H:%M')} "
          f"({MARGEN_MIN} min de margen)")
    print("  si la maquina esta apagada a esa hora, corre apenas prenda")
    print(f"  log -> data/sync_pendiente.log")
    print(f"  estado: python scripts/programar_sync.py --estado")


if __name__ == "__main__":
    main()
