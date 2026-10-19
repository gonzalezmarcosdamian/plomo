"""
Pipeline de importación — Fase 1 (pre-Rekordbox).

Qué hace:
1. Mueve archivos de Downloads → Music/YYYY-MM
2. Para tracks que YA EXISTEN en la DB: fija FolderPath (forward slashes)
   y DeliveryControl='on' para que el export USB funcione sin error [2]

Qué NO hace:
- NO importa tracks a la DB (Rekordbox lo hace él mismo al abrirse)
- NO aplica cues ni energy — eso es post_import.py

Flujo correcto — desde 2026-10-19 lo corre entero `python scripts/importar.py`:
  1. python scripts/import_all.py     ← este script
  2. Rekordbox importa el Inbox y lo analiza (BPM + key + waveform). Rekordbox
     no tiene carpeta vigilada, ni la 6 ni la 7.2: importar.py abre Rekordbox y
     hace el Ctrl+O por el DJ (ver src/plomo/rekordbox_app.py).
  3. Cerrar Rekordbox (importar.py lo cierra ordenado y espera que salga)
  4. python scripts/post_import.py            ← cues v8 + energy + playlists
  5. python scripts/import_all.py --archive   ← vacia el Inbox

Lo que ya esta en la biblioteca no entra al Inbox: con el import automatico,
lo que entra se importa sin que nadie lo mire, y un tema bajado dos veces
quedaria duplicado. Se deja en Descargas y se avisa.

El paso 5 no es opcional: Rekordbox reescanea la carpeta monitoreada ENTERA en
cada apertura, no solo lo nuevo. Si el Inbox crece sin limite, cada apertura
reprocesa todo, y cualquier archivo cuya fila se haya borrado vuelve a entrar
como track nuevo -> duplicado. Vaciando el Inbox, Rekordbox solo ve lo que
falta importar.
"""
import os
import sys
import shutil
import unicodedata
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plomo import config
import sqlcipher3

DOWNLOADS = config.DOWNLOADS_FOLDER
DEST = config.MUSIC_NEW_FOLDER


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clave_nombre(nombre: str) -> str:
    """Nombre de archivo comparable: mismos acentos (NFC) y sin mayusculas."""
    return unicodedata.normalize("NFC", nombre).casefold()


def ya_en_biblioteca(nombre: str, rutas_por_nombre: Mapping[str, list[str]],
                     existe: Callable[[str], bool] = os.path.exists) -> str | None:
    """La ruta de la biblioteca si ese archivo ya esta importado y en disco.

    Se compara por nombre de archivo y no por contenido: Rekordbox reescribe los
    tags del que importo, asi que la descarga repetida tiene otro hash (medido con
    Maze 28 - Constant Daydream, 2026-10-19). Si la fila existe pero su archivo se
    perdio, la descarga es el reemplazo y entra. Con varias filas del mismo
    nombre alcanza con que una tenga el archivo.
    """
    return next((r for r in rutas_por_nombre.get(clave_nombre(nombre), []) if existe(r)), None)


def rutas_por_nombre() -> dict[str, list[str]]:
    """clave_nombre(FileNameL) -> FolderPaths de las filas activas, en solo lectura."""
    con = sqlcipher3.connect(f"file:{config.REKORDBOX_DB_PATH}?mode=ro", uri=True)
    try:
        con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
        filas = con.execute(
            "SELECT FileNameL, FolderPath FROM djmdContent "
            "WHERE rb_local_deleted=0 AND FileNameL IS NOT NULL").fetchall()
    finally:
        con.close()
    indice: dict[str, list[str]] = {}
    for nombre, ruta in filas:
        indice.setdefault(clave_nombre(nombre), []).append(ruta)
    return indice


def fix_existing_tracks(moved: list[Path]) -> None:
    """Fix FolderPath + DeliveryControl for tracks that already exist in the DB."""
    if not moved:
        return

    ts = now_str()
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    fixed = 0
    for dest_file in moved:
        folder = str(dest_file).replace("\\", "/")
        row = con.execute(
            "SELECT ID FROM djmdContent WHERE FileNameL=? AND rb_local_deleted=0",
            (dest_file.name,),
        ).fetchone()
        if row:
            con.execute(
                "UPDATE djmdContent SET FolderPath=?, DeliveryControl='on', updated_at=? WHERE ID=?",
                (folder, ts, row[0]),
            )
            fixed += 1

    con.commit()
    con.close()

    if fixed:
        print(f"\n  Fix metadata: {fixed} tracks existentes actualizados (FolderPath + DeliveryControl)")


def archive_imported(con_path: Path) -> None:
    """
    Saca del Inbox los archivos que Rekordbox ya importo, a Nuevos/YYYY-MM.

    Por que: Rekordbox reescanea la carpeta monitoreada ENTERA en cada apertura,
    no solo lo nuevo. Con el Inbox creciendo sin limite (llego a 975 archivos)
    cada apertura reprocesa todo, y cualquier archivo cuya fila se haya borrado
    vuelve a entrar como track nuevo -> duplicado. Vaciando el Inbox despues de
    cada importacion, Rekordbox solo ve lo que falta importar.

    Solo mueve archivos que YA tienen fila activa apuntando a su ruta actual:
    lo que todavia no importo Rekordbox se queda donde esta.
    """
    files = sorted(DEST.glob("*.mp3")) + sorted(DEST.glob("*.flac"))
    if not files:
        return

    con = sqlcipher3.connect(str(con_path))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
    # ruta -> ID. Se actualiza por ID y no por "WHERE LOWER(FolderPath)=?":
    # el LOWER() de SQLite solo baja ASCII, asi que "RÜFÜS" nunca matchea
    # contra el .lower() de Python y la fila queda apuntando al archivo viejo.
    # Solo lo analizado (BPM > 0): un tema que Rekordbox importo pero no termino
    # de analizar se queda en el Inbox, a la vista, hasta que tenga BPM.
    known = {r[1].lower(): str(r[0]) for r in con.execute(
        "SELECT ID, FolderPath FROM djmdContent WHERE rb_local_deleted=0 "
        "AND FolderPath IS NOT NULL AND COALESCE(BPM, 0) > 0")}

    ts = now_str()
    moved = 0
    pending = 0
    fallidos = 0
    for src in files:
        current = str(src).replace("\\", "/")
        if current.lower() not in known:
            pending += 1
            continue  # Rekordbox todavia no lo importo

        month = datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m")
        dest_dir = DEST.parent / month
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / src.name
        if dest_file.exists():
            pending += 1
            continue

        # La fila se actualiza PRIMERO y se confirma solo si el archivo llego.
        # Al reves —mover y despues escribir, con un unico commit al final— un
        # corte a mitad de la tanda deja los archivos movidos y ninguna fila
        # actualizada: todos los tracks pasan a "archivo faltante" de una vez.
        # Commit por track, como manda la regla del proyecto.
        try:
            con.execute(
                "UPDATE djmdContent SET FolderPath=?, updated_at=? WHERE ID=?",
                (str(dest_file).replace("\\", "/"), ts, known[current.lower()]),
            )
            shutil.move(str(src), str(dest_file))
            con.commit()
            moved += 1
        except Exception as e:  # noqa: BLE001 — un fallo no aborta la tanda
            con.rollback()
            fallidos += 1
            print(f"  [ERROR] {src.name}: {e}")

    con.close()
    print(f"\n  Inbox archivado: {moved} movidos a Nuevos/YYYY-MM, "
          f"{pending} siguen en Inbox, {fallidos} fallidos")


def main() -> None:
    if "--archive" in sys.argv:
        # Se corre DESPUES de que Rekordbox importo. Vacia el Inbox.
        print(f"Archivando lo ya importado desde {DEST}")
        archive_imported(config.REKORDBOX_DB_PATH)
        return

    tracks = sorted(list(DOWNLOADS.glob("*.mp3")) + list(DOWNLOADS.glob("*.flac")))
    print(f"Tracks en Downloads: {len(tracks)}")
    for t in tracks:
        print(f"  {t.name}")

    if not tracks:
        print("Nada que procesar.")
        return

    DEST.mkdir(parents=True, exist_ok=True)
    try:
        en_biblioteca = rutas_por_nombre()
    except Exception as e:  # noqa: BLE001 — sin base no se puede chequear: se corta
        print(f"  No pude leer la base de Rekordbox ({e}). No muevo nada.")
        sys.exit(1)

    moved: list[Path] = []
    repetidos: list[tuple[str, str]] = []

    for i, src in enumerate(tracks, 1):
        dest_file = DEST / src.name
        print(f"[{i}/{len(tracks)}] {src.name}")

        ya = ya_en_biblioteca(src.name, en_biblioteca)
        if ya:
            # No se borra: el archivo es distinto byte a byte y quien decide si
            # sobra es el DJ. Se deja en Descargas, fuera del camino del import.
            repetidos.append((src.name, ya))
            print(f"  [ya esta] {ya}")
            continue

        if dest_file.exists():
            # Archivo ya en destino — eliminar duplicado de Downloads
            if src.exists():
                src.unlink()
            print(f"  [dup] Ya existia en destino, removido de Downloads")
        else:
            shutil.move(str(src), str(dest_file))
            print(f"  [ok] Movido a {DEST.name}/")

        moved.append(dest_file)

    print(f"\n{len(moved)} archivos movidos a {DEST}")

    # Fix metadata sólo para los que ya estaban en la DB antes de que RB los importe.
    # Los nuevos los fijará post_import.py después del análisis de Rekordbox.
    try:
        fix_existing_tracks(moved)
    except Exception as e:
        print(f"  Advertencia: no se pudo conectar a la DB ({e})")
        print("  Rekordbox no debe estar corriendo — cerralo primero.")

    if repetidos:
        print(f"\n{len(repetidos)} ya estaban en la biblioteca y quedaron en Descargas "
              "(borralos si sobran):")
        for nombre, ruta in repetidos:
            print(f"  {nombre}\n    -> {ruta}")

    print("\n=== LISTO ===")
    print(f"Tracks movidos a: {DEST}")
    print("")
    # Rekordbox no importa solo, ni la 6 ni la 7.2: no tiene carpeta vigilada.
    # Este mensaje decia una vez lo contrario y costo una sesion entera
    # esperando un analisis que nunca iba a arrancar. Ahora el resto lo hace
    # importar.py, que corre este script como primer paso.
    print("Rekordbox no importa solo. Para el resto del ciclo:")
    print("  python scripts/importar.py   (abre Rekordbox, importa, analiza, cues, archiva)")


if __name__ == "__main__":
    main()
