# -*- coding: utf-8 -*-
"""Importar musica nueva de punta a punta, sin tocar Rekordbox a mano.

    python scripts/importar.py                    # Descargas -> biblioteca
    python scripts/importar.py --batch data/x.txt # baja de Muzpa primero
    python scripts/importar.py --abrir            # deja Rekordbox abierto al final
    python scripts/importar.py --dry              # muestra que haria y sale
    python scripts/importar.py --cerrar           # si Rekordbox esta abierto, lo cierra

Hace en orden lo que antes eran cinco pasos y dos clicks:
  0. (con --batch) muzpa_download.py --batch
  1. si Rekordbox esta abierto, para; con --cerrar lo cierra (ordenado, nunca lo mata)
  2. backup verificado de la base               (backup.py)
  3. Descargas -> Inbox, sin repetidos          (import_all.py)
  4. abre Rekordbox, cierra los carteles, importa el Inbox con Ctrl+O,
     espera el analisis y lo cierra             (plomo.rekordbox_app)
  5. cues v8 + energia                          (post_import.py)
  6. vacia el Inbox a Nuevos/AAAA-MM            (import_all.py --archive)

POR QUE ASI
Rekordbox no tiene carpeta vigilada (ni la 6 ni la 7.2, verificado 2026-10-19) y
el import lo tiene que hacer el mismo: pyrekordbox add_content deja tracks que el
export al pen rechaza. Lo unico automatizable era el click, y eso hace el paso 4.
Los demas pasos son los scripts de siempre, corridos como procesos aparte: cada
uno sigue sirviendo solo, y si uno falla, el ciclo para ahi y dice cual.

Lo que no termina de analizarse a tiempo se lista al final. Ya tiene fila, asi
que no se vuelve a importar: hay que abrir Rekordbox, dejar que termine y correr
post_import.py.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import traceback
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from import_all import rutas_por_nombre, ya_en_biblioteca  # noqa: E402
from plomo import config, rekordbox_app as rb  # noqa: E402

# Lo mismo que mueve y archiva import_all: un .wav que entrara aca se importaria
# y despues quedaria en el Inbox para siempre, porque --archive no lo ve.
AUDIO = {".mp3", ".flac"}


def correr(*args: str) -> None:
    """Corre un script del proyecto con el mismo Python. Si falla, para todo."""
    print(f"\n$ {' '.join(args)}", flush=True)
    resultado = subprocess.run([sys.executable, *args], cwd=RAIZ)
    if resultado.returncode != 0:
        raise SystemExit(f"Fallo: {' '.join(args)} (codigo {resultado.returncode}). El ciclo para aca.")


def inbox() -> tuple[list[Path], list[Path]]:
    """Archivos del Inbox: (sin fila en Rekordbox, con fila).

    Los "con fila" son restos de una corrida cortada despues del import: les
    falta post_import y el archivado, y la corrida siguiente los termina.
    """
    carpeta = config.MUSIC_NEW_FOLDER
    if not carpeta.is_dir():
        return [], []
    archivos = sorted(p for p in carpeta.iterdir() if p.suffix.lower() in AUDIO)
    filas = rb.leer_analisis(config.REKORDBOX_DB_PATH, config.SQLCIPHER_KEY, str(carpeta))
    sin_fila = [p for p in archivos if rb.clave_ruta(p) not in filas]
    return sin_fila, [p for p in archivos if p not in sin_fila]


def pendientes_inbox() -> list[Path]:
    return inbox()[0]


def descargas() -> list[Path]:
    """Lo de Descargas que import_all va a mover: mp3/flac que no estan ya en la biblioteca."""
    en_biblioteca = rutas_por_nombre()
    return sorted(p for p in config.DOWNLOADS_FOLDER.glob("*")
                  if p.suffix.lower() in {".mp3", ".flac"}
                  and not ya_en_biblioteca(p.name, en_biblioteca))


def cerrar_rekordbox(permitido: bool) -> None:
    """Rekordbox tiene que estar cerrado para escribir la base. Abierto, puede
    estar en medio de un sync al pen: se cierra solo si el DJ lo pidio."""
    if not rb.esta_abierto():
        return
    if not permitido:
        raise SystemExit("Rekordbox esta abierto. Cerralo, o corre con --cerrar para que lo cierre "
                         "yo (no lo uses si esta sincronizando el pen).")
    print("\nRekordbox esta abierto: lo cierro (ordenado, puede tardar ~40 s)...", flush=True)
    if not rb.cerrar():
        raise SystemExit("Rekordbox no se cerro solo. Cerralo a mano y volve a correr esto.")


def importar_en_rekordbox(archivos: list[Path]) -> list[Path]:
    """Paso 4. Devuelve lo que no llego a analizarse."""
    print(f"\nAbriendo Rekordbox para importar {len(archivos)} tema(s)...", flush=True)
    rb.abrir()
    try:
        rb.esperar_lista()
        rb.importar(config.MUSIC_NEW_FOLDER, [p.name for p in archivos])
        faltan = rb.esperar_analisis(archivos, config.REKORDBOX_DB_PATH,
                                     config.SQLCIPHER_KEY, config.MUSIC_NEW_FOLDER)
    except BaseException:
        # El error se muestra ANTES de cerrar: si el cierre tambien falla, su
        # SystemExit taparia la causa real.
        traceback.print_exc()
        print("\nCerrando Rekordbox...", flush=True)
        if not rb.cerrar():
            print("Rekordbox no se cerro solo: cerralo a mano antes de seguir.")
        raise
    # Rekordbox no puede quedar abierto: los pasos que siguen escriben la base.
    print("\nCerrando Rekordbox...", flush=True)
    if not rb.cerrar():
        raise SystemExit("Rekordbox no se cerro solo. Cerralo a mano y corre "
                         "post_import.py y import_all.py --archive.")
    return faltan


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--batch", help="lista para muzpa_download.py --batch, se baja primero")
    ap.add_argument("--abrir", action="store_true", help="dejar Rekordbox abierto al final")
    ap.add_argument("--dry", action="store_true", help="mostrar que haria y salir")
    ap.add_argument("--cerrar", action="store_true",
                    help="si Rekordbox esta abierto, cerrarlo (si no, se corta)")
    args = ap.parse_args()

    if args.dry:
        print(f"Descargas ({config.DOWNLOADS_FOLDER}): {len(descargas())} para mover")
        for p in descargas():
            print(f"  {p.name}")
        pend, a_medias = inbox()
        print(f"Inbox ({config.MUSIC_NEW_FOLDER}): {len(pend)} sin importar, "
              f"{len(a_medias)} importados sin archivar")
        for p in pend:
            print(f"  {p.name}")
        print(f"Rekordbox: {'abierto' if rb.esta_abierto() else 'cerrado'}")
        return

    if args.batch:
        correr("scripts/muzpa_download.py", "--batch", args.batch)

    pend, a_medias = inbox()
    if not descargas() and not pend and not a_medias:
        print("\nNada nuevo en Descargas ni en el Inbox.")
        return
    cerrar_rekordbox(args.cerrar)

    correr("scripts/backup.py", "antes_importar")
    if descargas():
        correr("scripts/import_all.py")

    nuevos = pendientes_inbox()
    faltan: list[Path] = []
    if nuevos:
        faltan = importar_en_rekordbox(nuevos)
    else:
        print("\nEl Inbox no tiene nada sin importar.")

    correr("scripts/post_import.py")
    correr("scripts/import_all.py", "--archive")

    print("\n=== IMPORTACION TERMINADA ===")
    print(f"  importados y analizados: {len(nuevos) - len(faltan)}")
    if faltan:
        print(f"  sin terminar de analizar ({len(faltan)}), quedan en el Inbox para la proxima:")
        for p in faltan:
            print(f"    {p.name}")

    if args.abrir:
        rb.abrir()
        rb.esperar_lista()
        print("\nRekordbox abierto: listo para el sync al pen.")


if __name__ == "__main__":
    main()
