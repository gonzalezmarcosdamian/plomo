# -*- coding: utf-8 -*-
"""Backup de master.db a mano, con el motivo en el nombre.

POR QUE EXISTE SI YA HAY BACKUP AUTOMATICO
`RekordboxDB` hace una copia cada vez que se abre, con nombre
`master.db.backup-<timestamp>`. Eso cubre los accidentes pero no sirve para
volver a un estado: el nombre no dice a que estado se vuelve. Con 271 archivos
acumulados, "restaurar el backup" obliga a adivinar por fecha.

Aca el motivo es OBLIGATORIO y va en el nombre, que es la convencion que el
proyecto ya tenia escrita y nunca tuvo script:

    master_YYYYMMDD_HHMMSS_<motivo>.db

LA COPIA SE VERIFICA, NO SE DA POR HECHA
Un archivo de 105 MB que no abre no es un backup. Despues de copiar, esto abre
la copia con la clave, le corre quick_check y le cuenta los tracks y las
playlists. Si no da, lo dice y sale con error: es el unico momento en que
enterarse sirve de algo.

TAMBIEN SE COPIAN -wal, -shm Y EL XML
El -wal puede tener transacciones que todavia no estan en el .db. Copiar solo el
.db cuando hay WAL pendiente guarda un estado anterior al que uno cree. En
2026-06-04 la corrupcion de djmdCue vino justamente de no chequear el WAL.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(RAIZ / "src"))

import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

DIAS_RETENCION = 60
MINIMO_A_CONSERVAR = 10
SUFIJOS = ("-wal", "-shm")


def rekordbox_abierto() -> bool:
    import subprocess
    try:
        out = subprocess.run(["tasklist"], capture_output=True, text=True,
                             timeout=30).stdout.lower()
    except Exception:
        return False
    return "rekordbox.exe" in out


def verificar(copia: Path) -> tuple[bool, str]:
    """Abre la COPIA y se asegura de que sea una base usable, no un archivo."""
    try:
        con = sqlcipher3.connect(f"file:{copia}?mode=ro", uri=True)
        con.execute(f"PRAGMA key='{config.SQLCIPHER_KEY}'")
        con.execute("PRAGMA cipher_compatibility=4")
        chk = con.execute("PRAGMA quick_check").fetchone()[0]
        tracks = con.execute(
            "SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0").fetchone()[0]
        listas = con.execute(
            "SELECT COUNT(*) FROM djmdPlaylist WHERE rb_local_deleted=0").fetchone()[0]
        cues = con.execute(
            "SELECT COUNT(*) FROM djmdCue WHERE rb_local_deleted=0").fetchone()[0]
        con.close()
    except Exception as e:                                  # noqa: BLE001
        return False, f"la copia no se pudo abrir: {e}"
    if chk != "ok":
        return False, f"quick_check dio {chk!r}"
    return True, f"quick_check ok · {tracks} tracks · {listas} listas · {cues} cues"


def retencion(carpeta: Path, aplicar: bool) -> None:
    hoy = dt.datetime.now()
    todos = sorted((p for p in carpeta.glob("*") if p.is_file()),
                   key=lambda p: p.stat().st_mtime)
    peso = sum(p.stat().st_size for p in todos) / 1024 ** 3
    viejos = [p for p in todos
              if (hoy - dt.datetime.fromtimestamp(p.stat().st_mtime)).days > DIAS_RETENCION]
    print(f"\n  retencion: {len(todos)} archivos, {peso:.2f} GB")
    if len(todos) <= MINIMO_A_CONSERVAR or not viejos:
        print(f"  nada que limpiar (la regla borra los de mas de {DIAS_RETENCION} dias "
              f"solo si hay mas de {MINIMO_A_CONSERVAR} acumulados)")
        return
    # Nunca se toca el mas nuevo de cada motivo: es el unico al que alguien
    # podria querer volver. Y nunca se toca nada que no sea un backup.
    por_motivo: dict[str, Path] = {}
    for p in todos:
        m = re.match(r"master_\d{8}_\d{6}_(.+?)\.db", p.name)
        if m:
            por_motivo[m.group(1)] = p                      # el ultimo gana
    intocables = set(por_motivo.values()) | set(todos[-MINIMO_A_CONSERVAR:])
    a_borrar = [p for p in viejos if p not in intocables]
    libera = sum(p.stat().st_size for p in a_borrar) / 1024 ** 3
    print(f"  {len(a_borrar)} de mas de {DIAS_RETENCION} dias se pueden borrar "
          f"({libera:.2f} GB). Se conservan los {MINIMO_A_CONSERVAR} mas nuevos y "
          f"el ultimo de cada motivo.")
    if not aplicar:
        print("  (corre con --limpiar para borrarlos)")
        return
    for p in a_borrar:
        p.unlink()
    print(f"  borrados. quedan {len(todos) - len(a_borrar)} archivos")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("motivo", help="a que estado se vuelve si se restaura, en una palabra "
                                   "o dos con guion bajo: pre_gig, antes_dedup, pre_sync_pen")
    ap.add_argument("--limpiar", action="store_true",
                    help="aplica la retencion de 60 dias despues de copiar")
    a = ap.parse_args()

    motivo = re.sub(r"[^a-z0-9_]+", "_", a.motivo.lower()).strip("_")
    if not motivo:
        sys.exit("el motivo no puede quedar vacio")
    if rekordbox_abierto():
        sys.exit("rekordbox.exe esta abierto. Cerralo: con la DB abierta la copia puede "
                 "salir con transacciones a medias y el backup no serviria.")

    db = config.REKORDBOX_DB_PATH
    destino = config.BACKUP_FOLDER
    destino.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    copia = destino / f"master_{ts}_{motivo}.db"

    print(f"  {db}  ->  {copia.name}")
    shutil.copy2(db, copia)
    for suf in SUFIJOS:
        src = Path(str(db) + suf)
        if src.exists():
            shutil.copy2(src, Path(str(copia) + suf))
            print(f"  + {suf}  ({src.stat().st_size / 1024:.0f} KB)")
    if config.REKORDBOX_XML_PATH.exists():
        xml = destino / f"masterPlaylists6_{ts}_{motivo}.xml"
        shutil.copy2(config.REKORDBOX_XML_PATH, xml)
        print(f"  + {xml.name}")

    ok, detalle = verificar(copia)
    print(f"\n  {'VERIFICADA' if ok else 'FALLO'}: {detalle}")
    if not ok:
        copia.unlink(missing_ok=True)
        sys.exit("la copia no sirve y se borro para no dejar un backup falso. "
                 "Revisar espacio en disco y la clave de sqlcipher.")
    print(f"  {copia.stat().st_size / 1024 ** 2:.1f} MB en {destino}")
    retencion(destino, a.limpiar)


if __name__ == "__main__":
    main()
