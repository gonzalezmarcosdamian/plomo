"""Deshace una importacion accidental: saca de la biblioteca lo que entro de mas.

Caso que lo motivo: el 2026-09-07 Rekordbox analizo `Music/` entero en vez del
deposito, y se comio 301 archivos de `_Archivo/` (cuarentena y duplicados ya
removidos) y de las carpetas viejas. Eran exactamente la basura que la mudanza
del dia habia apartado.

Identifica por dos condiciones a la vez, y las dos tienen que dar:
  1. la fila se creo en la fecha indicada
  2. el archivo NO vive en `Music/Biblioteca/` — el deposito es lo unico legitimo

Un track que este en el deposito nunca se toca, aunque se haya creado ese dia.

Ademas de sacar las filas, mueve los archivos fuera del arbol de musica. Si no,
la proxima vez que Rekordbox mire la carpeta vuelve a importarlos: el problema
no era la importacion, era que esos archivos estuvieran ahi para importar.

Uso:
    python scripts/undo_import.py --fecha 2026-09-07
    python scripts/undo_import.py --fecha 2026-09-07 --si
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import psutil  # noqa: E402
import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

RAIZ = config.MUSIC_LIBRARY_ROOT
DEPOSITO = RAIZ / "Biblioteca"
# Fuera del arbol que Rekordbox mira. Es el punto: que no se pueda repetir.
BASURA = Path(r"C:\Users\gonza\Music\_plomo_fuera_de_biblioteca")


def rekordbox_corriendo() -> bool:
    return any(p.info["name"] and "rekordbox" in p.info["name"].lower()
               for p in psutil.process_iter(["name"]))


def _rb(p: Path) -> str:
    return str(p).replace("\\", "/")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fecha", required=True, help="AAAA-MM-DD de la importacion a deshacer")
    ap.add_argument("--si", action="store_true", help="ejecutar de verdad")
    ap.add_argument("--dejar-archivos", action="store_true",
                    help="saca las filas pero no mueve los archivos (no recomendado)")
    args = ap.parse_args()

    if rekordbox_corriendo():
        sys.exit("ABORTADO: rekordbox.exe esta corriendo. System Tray -> Quit "
                 "y volver a intentar.")

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

    filas = con.execute(
        """SELECT ID, FolderPath FROM djmdContent
           WHERE rb_local_deleted = 0 AND FolderPath IS NOT NULL
             AND created_at LIKE ?""", (f"{args.fecha}%",)).fetchall()
    # La segunda condicion es la que protege: lo que esta en el deposito se queda
    dep = _rb(DEPOSITO).lower()
    sobrantes = [(cid, ruta) for cid, ruta in filas if not ruta.lower().startswith(dep)]
    protegidos = len(filas) - len(sobrantes)

    print(f"modo: {'REAL' if args.si else 'DRY-RUN (no cambia nada)'}")
    print(f"\n  filas creadas el {args.fecha}: {len(filas)}")
    print(f"  de esas, en el deposito (NO se tocan): {protegidos}")
    print(f"  fuera del deposito, a sacar: {len(sobrantes)}")
    if not sobrantes:
        print("\n  nada que deshacer")
        return

    origen: Counter = Counter()
    for _, ruta in sobrantes:
        origen[ruta.split("/Music/")[-1].rsplit("/", 1)[0]] += 1
    print("\n  vienen de:")
    for k, v in origen.most_common(12):
        print(f"    {v:5d}  {k}")

    # cuantas estan en playlists: si alguna lo esta, hay que mirarla a mano
    ids = [str(c) for c, _ in sobrantes]
    marcas = ",".join("?" * len(ids))
    en_pl = con.execute(
        f"SELECT COUNT(*) FROM djmdSongPlaylist WHERE rb_local_deleted=0 "
        f"AND ContentID IN ({marcas})", ids).fetchone()[0]
    print(f"\n  de esas filas, en alguna playlist: {en_pl}"
          + ("  <-- REVISAR A MANO ANTES DE SEGUIR" if en_pl else ""))

    if not args.si:
        print("\n  Dry-run. Agregar --si para ejecutar.")
        con.close()
        return
    if en_pl:
        sys.exit("ABORTADO: hay filas en playlists. Sacalas de la playlist en "
                 "Rekordbox o revisalas antes de correr esto.")

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = config.BACKUP_FOLDER / f"master_pre_undo_{ts}.db"
    shutil.copy2(config.REKORDBOX_DB_PATH, backup)
    print(f"\n  backup -> {backup}")

    usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdContent").fetchone()[0] or 0
    sacadas = movidos = fallos = 0
    ahora = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for cid, ruta in sobrantes:
        try:
            usn += 1
            con.execute(
                "UPDATE djmdContent SET rb_local_deleted=1, rb_local_usn=?, "
                "updated_at=? WHERE ID=?", (usn, ahora, cid))
            con.commit()
            sacadas += 1
        except Exception as e:  # noqa: BLE001
            con.rollback()
            fallos += 1
            print(f"  [ERROR] {cid}: {e}")
            continue
        if args.dejar_archivos:
            continue
        p = Path(ruta.replace("/", "\\"))
        if not p.exists():
            continue
        destino = BASURA / p.parent.name / p.name
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not destino.exists():
            shutil.move(str(p), str(destino))
            movidos += 1

    integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
    vivos = con.execute(
        "SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0").fetchone()[0]
    con.close()
    print(f"\n  filas sacadas de la biblioteca: {sacadas}   fallos: {fallos}")
    print(f"  archivos movidos fuera del arbol: {movidos} -> {BASURA}")
    print(f"  tracks vivos ahora: {vivos}")
    print(f"  integrity_check: {integridad}")
    print("\n  Ahora: regenerar vistas con scripts/build_views.py y abrir "
          "Rekordbox para verificar el conteo.")


if __name__ == "__main__":
    main()
