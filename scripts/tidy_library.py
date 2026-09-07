"""Consolida el deposito de musica: una carpeta por mes de ingreso, y nada mas.

La doctrina es "deposito inmutable, vistas descartables". El deposito es
`Music/Biblioteca/AAAA-MM/`: un archivo entra una vez y no se mueve nunca mas.
Toda la forma de navegar la coleccion vive en `scripts/build_views.py`, que se
borra y se regenera sin consecuencias.

Este script hace la mudanza inicial, en dos fases separadas por su riesgo:

  FASE A  basura que no es musica (backups del pen, carpetas de duplicados
          removidos). No toca la DB. Riesgo cero.
  FASE B  consolidar el audio al deposito. Cada archivo que se mueve se
          relinkea en `djmdContent.FolderPath` en la misma operacion: primero
          el UPDATE, despues el archivo, y commit solo si las dos cosas
          salieron. Los archivos sin fila en la DB no entran al deposito — van
          a cuarentena en `_Archivo/`, porque una carpeta que por doctrina no se
          revisa nunca no es lugar para basura.

Nada corre en real sin `--si`. La fase B ademas requiere `--con-relink`, para
que mover archivos de la biblioteca sea siempre una decision explicita.

Uso:
    python scripts/tidy_library.py                       # dry-run de todo
    python scripts/tidy_library.py --fase a --si         # solo la basura
    python scripts/tidy_library.py --fase b --con-relink # dry-run detallado
    python scripts/tidy_library.py --fase b --con-relink --si
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import psutil  # noqa: E402
import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

RAIZ = config.MUSIC_LIBRARY_ROOT
DEPOSITO = RAIZ / "Biblioteca"
ARCHIVO = RAIZ / "_Archivo"
AUDIO = {".mp3", ".flac", ".wav", ".aiff", ".aif", ".m4a", ".ogg"}
MES_RE = re.compile(r"^(20\d{2})-(0[1-9]|1[0-2])$")

# Carpetas que no se tocan nunca.
INTOCABLES = {
    RAIZ / "2026" / "Nuevos" / "Inbox",   # carpeta vigilada por Rekordbox
    DEPOSITO,
    ARCHIVO,
}

# Basura que no es musica y ensucia la raiz.
PATRONES_BASURA = ["_pen*_USBANLZ_backup_*", "**/_dups_removidos_*"]


def rekordbox_corriendo() -> bool:
    return any(p.info["name"] and "rekordbox" in p.info["name"].lower()
               for p in psutil.process_iter(["name"]))


def _conectar():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con


def _rb(p: Path) -> str:
    """Formato de path que usa Rekordbox: barras normales."""
    return str(p).replace("\\", "/")


# -- FASE A -----------------------------------------------------------------
def fase_a(ejecutar: bool) -> None:
    print(f"\n{'=' * 70}\nFASE A — basura fuera del arbol de musica")
    encontrados: list[Path] = []
    for patron in PATRONES_BASURA:
        encontrados += [p for p in RAIZ.glob(patron) if p.is_dir()]
    if not encontrados:
        print("  nada que mover")
        return

    con = _conectar()
    for d in sorted(set(encontrados)):
        n = con.execute(
            "SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0 "
            "AND FolderPath LIKE ?", (_rb(d) + "/%",)).fetchone()[0]
        archivos = sum(1 for _ in d.rglob("*") if _.is_file())
        if n:
            print(f"  [SALTEA] {d.name} — tiene {n} tracks vivos en la DB, "
                  "no es basura")
            continue
        destino = ARCHIVO / d.name
        print(f"  [{'ok' if ejecutar else 'dry'}] {d.relative_to(RAIZ)} "
              f"({archivos} archivos) -> _Archivo/")
        if ejecutar:
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(d), str(destino))
    con.close()


# -- FASE B -----------------------------------------------------------------
def destino_de(p: Path) -> str:
    """Carpeta del deposito para un archivo, por orden de confianza.

    1. La carpeta origen ya se llama AAAA-MM: esa es la respuesta, no se adivina.
    2. La ruta tiene una carpeta de año (2024, 2025, ...): se usa el año solo,
       sin mes. Inventar un mes seria peor que no tenerlo.
    3. Ninguna de las dos: mtime del archivo.

    El mtime NO se usa cuando la ruta dice el año, porque OneDrive toco los
    archivos viejos al sincronizar y su mtime es de 2026 aunque sean de 2024.
    """
    if MES_RE.match(p.parent.name):
        return p.parent.name
    for parte in p.parts:
        if re.fullmatch(r"20\d{2}", parte):
            return parte
    return dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m")


def _plan() -> tuple[list[tuple[Path, Path, int]], list[Path], Counter]:
    """(mudanzas con ContentID, archivos sin DB, resumen por destino)."""
    con = _conectar()
    en_db = {r[0].replace("/", "\\").lower(): r[1]
             for r in con.execute(
                 "SELECT FolderPath, ID FROM djmdContent "
                 "WHERE rb_local_deleted=0 AND FolderPath IS NOT NULL")}
    con.close()

    mudanzas: list[tuple[Path, Path, int]] = []
    huerfanos: list[Path] = []
    resumen: Counter = Counter()

    basura = {d.resolve() for patron in PATRONES_BASURA
              for d in RAIZ.glob(patron) if d.is_dir()}
    saltar = [str(t).lower() for t in INTOCABLES] + [str(b).lower() for b in basura]
    for p in RAIZ.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in AUDIO:
            continue
        # lo que la fase A se lleva a _Archivo no es material del deposito
        if any(str(p).lower().startswith(s0) for s0 in saltar):
            continue
        mes = destino_de(p)
        destino = DEPOSITO / mes / p.name
        if destino == p:
            continue
        cid = en_db.get(str(p).lower())
        if cid is None:
            huerfanos.append(p)
        else:
            mudanzas.append((p, destino, cid))
        resumen[mes] += 1
    return mudanzas, huerfanos, resumen


def fase_b(ejecutar: bool, con_relink: bool) -> None:
    print(f"\n{'=' * 70}\nFASE B — consolidar el audio en Biblioteca/AAAA-MM")
    mudanzas, huerfanos, resumen = _plan()

    if not mudanzas and not huerfanos:
        print("  el deposito ya esta consolidado")
        return

    print(f"\n  {len(mudanzas)} archivos en la DB (necesitan relink)")
    print(f"  {len(huerfanos)} archivos sueltos sin fila en la DB "
          f"-> a _Archivo/huerfanos_<fecha>/, NO al deposito")
    print("\n  destino          archivos")
    for mes, n in sorted(resumen.items()):
        print(f"    Biblioteca/{mes:<8} {n:5d}")

    origenes: dict[str, int] = defaultdict(int)
    for p, _, _ in mudanzas:
        origenes[str(p.parent.relative_to(RAIZ))] += 1
    print("\n  desde")
    for o, n in sorted(origenes.items(), key=lambda x: -x[1])[:15]:
        print(f"    {n:5d}  {o}")

    if not con_relink:
        print("\n  Falta --con-relink. Sin eso no se mueve ningun archivo que "
              "este en la DB:\n  mover sin relinkear lo hace desaparecer de "
              "Rekordbox.")
        return
    if not ejecutar:
        print("\n  Dry-run. Agregar --si para ejecutar.")
        return

    if rekordbox_corriendo():
        sys.exit("ABORTADO: rekordbox.exe esta corriendo. System Tray -> Quit "
                 "y volver a intentar.")

    backup = config.BACKUP_FOLDER / (
        "master_pre_tidy_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S") + ".db")
    shutil.copy2(config.REKORDBOX_DB_PATH, backup)
    print(f"\n  backup -> {backup}")

    con = _conectar()
    usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdContent").fetchone()[0] or 0
    movidos = fallos = saltados = 0
    for origen, destino, cid in mudanzas:
        if destino.exists():
            saltados += 1
            print(f"  [dup] ya existe en destino, no se mueve: {destino.name}")
            continue
        # El UPDATE va PRIMERO y se confirma solo si el archivo llego. Al reves
        # —mover y despues escribir— un fallo del UPDATE deja el archivo en otro
        # lado con la DB apuntando al viejo: el track desaparece de Rekordbox.
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            usn += 1
            con.execute(
                "UPDATE djmdContent SET FolderPath=?, rb_local_usn=? WHERE ID=?",
                (_rb(destino), usn, cid))
            shutil.move(str(origen), str(destino))
            con.commit()
            movidos += 1
        except Exception as e:  # noqa: BLE001 — un fallo no puede abortar la tanda
            con.rollback()
            fallos += 1
            print(f"  [ERROR] {origen.name}: {e}")

    # Los huerfanos NO van al deposito. Son archivos sin fila en la DB: exports
    # de sets renombrados y copias byte-identicas de tracks vivos. Meterlos en
    # una carpeta que por doctrina no se revisa nunca mas es enterrar basura
    # donde nadie la va a encontrar.
    cuarentena = ARCHIVO / f"huerfanos_{dt.date.today():%Y-%m-%d}"
    # La cuarentena es plana y los exports de sets repiten nombres entre
    # versiones. Antes, en colision, el archivo se quedaba donde estaba EN
    # SILENCIO y el resumen igual imprimia `len(huerfanos)`: reportaba 246
    # movidos cuando habia movido 196. Ahora se desambigua con sufijo y se
    # cuentan los movidos de verdad.
    en_cuarentena = 0
    for p in huerfanos:
        destino = cuarentena / p.name
        destino.parent.mkdir(parents=True, exist_ok=True)
        k = 2
        while destino.exists():
            destino = cuarentena / f"{p.stem}~{k}{p.suffix}"
            k += 1
        shutil.move(str(p), str(destino))
        en_cuarentena += 1

    integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
    con.close()
    print(f"\n  movidos y relinkeados: {movidos}   fallos: {fallos}   "
          f"saltados por duplicado: {saltados}")
    print(f"  huerfanos a cuarentena: {en_cuarentena} de {len(huerfanos)} "
          f"-> {cuarentena.name}/")
    print(f"  integrity_check: {integridad}")
    print("\n  Ahora: regenerar las vistas con "
          "scripts/build_views.py, y abrir Rekordbox para verificar.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fase", choices=["a", "b", "todo"], default="todo")
    ap.add_argument("--si", action="store_true", help="ejecutar de verdad")
    ap.add_argument("--con-relink", action="store_true",
                    help="permite mover archivos que estan en la DB, actualizando FolderPath")
    args = ap.parse_args()

    print(f"raiz: {RAIZ}")
    print(f"modo: {'REAL' if args.si else 'DRY-RUN (no cambia nada)'}")
    if args.fase in ("a", "todo"):
        fase_a(args.si)
    if args.fase in ("b", "todo"):
        fase_b(args.si, args.con_relink)


if __name__ == "__main__":
    main()
