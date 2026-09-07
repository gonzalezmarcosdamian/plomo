"""Repara tracks cuyo archivo no esta donde dice la DB.

Es la herramienta de emergencia del proyecto: cuando `db_audit.py` reporta
"archivos faltantes", esto los vuelve a enganchar. `build_views.py` la recomienda
por nombre en su salida.

Tres cosas de esta version que no estaban antes, y las tres importan:

1. **Busca en el deposito.** Los `SEARCH_ROOTS` apuntaban al arbol viejo
   (`2026/Nuevos/...`) y quedaron ciegos el dia que la biblioteca se mudo a
   `Music/Biblioteca/`. La herramienta de reparar paths sin el lugar donde
   viven los archivos.
2. **Nunca busca en `_Archivo/`.** Ahi vive la cuarentena y los duplicados.
   Relinkear una fila viva a una copia de cuarentena deja el track sonando pero
   fuera de la biblioteca, que es peor que tenerlo roto: no se nota.
3. **No escribe sin `--si`.** Antes el default era escribir y `--dry` era el
   flag: correrlo sin argumentos modificaba la DB sin backup y sin verificar que
   Rekordbox estuviera cerrado.

Uso:
    python scripts/fix_missing_paths.py          # dry-run
    python scripts/fix_missing_paths.py --si
"""
from __future__ import annotations

import datetime as dt
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import psutil  # noqa: E402
import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402

EJECUTAR = "--si" in sys.argv

RAIZ = config.MUSIC_LIBRARY_ROOT
DEPOSITO = RAIZ / "Biblioteca"
# Orden de confianza: primero el deposito, que es donde vive todo; despues la
# carpeta vigilada, unico lugar con audio recien llegado.
SEARCH_ROOTS = [DEPOSITO, config.MUSIC_NEW_FOLDER]
# Cuarentena y basura. Un track relinkeado aca queda fuera de la biblioteca
# pero suena, asi que el error no se nota hasta que es tarde.
PROHIBIDO = (RAIZ / "_Archivo",)


def rekordbox_corriendo() -> bool:
    return any(p.info["name"] and "rekordbox" in p.info["name"].lower()
               for p in psutil.process_iter(["name"]))


def db_connect():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    return con


def find_file(filename: str) -> Path | None:
    """Match directo primero, recursivo despues. Si es ambiguo, no se toca."""
    for root in SEARCH_ROOTS:
        directo = root / filename
        if directo.is_file():
            return directo
    hits = [
        p for root in SEARCH_ROOTS if root.exists()
        for p in root.rglob(filename)
        if p.is_file() and not any(
            str(p).lower().startswith(str(x).lower()) for x in PROHIBIDO)
    ]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        # Dos copias del mismo nombre: elegir una al azar es como relinkear a
        # ciegas. Se reporta y lo mira una persona.
        print(f"  AMBIGUO ({len(hits)}) {filename} — no se toca")
        for h in hits[:4]:
            print(f"      {h}")
    return None


def main() -> None:
    print(f"Fix Missing Paths — {'REAL' if EJECUTAR else 'DRY-RUN (no cambia nada)'}")
    print(f"  busca en: {', '.join(str(r) for r in SEARCH_ROOTS)}")
    print(f"  nunca en: {', '.join(str(r) for r in PROHIBIDO)}\n")

    if EJECUTAR and rekordbox_corriendo():
        sys.exit("ABORTADO: rekordbox.exe esta corriendo. System Tray -> Quit "
                 "y volver a intentar.")

    con = db_connect()
    rows = con.execute(
        """SELECT c.ID, a.Name, c.Title, c.FolderPath
           FROM djmdContent c
           LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
           WHERE c.rb_local_deleted = 0 AND c.FolderPath IS NOT NULL"""
    ).fetchall()

    rotos = [(cid, ar, ti, fp) for cid, ar, ti, fp in rows
             if fp and not Path(fp.replace("/", os.sep)).exists()]
    print(f"  {len(rows)} tracks, {len(rotos)} con archivo faltante\n")
    if not rotos:
        print("  nada que reparar")
        con.close()
        return

    plan = []
    sin_encontrar = 0
    for cid, artista, titulo, fpath in rotos:
        found = find_file(Path(fpath.replace("/", os.sep)).name)
        if found:
            plan.append((cid, found.as_posix(), fpath))
            print(f"  FIX [{cid}] {artista or '?'} - {titulo}")
            print(f"       {fpath}\n    -> {found.as_posix()}")
        else:
            sin_encontrar += 1
            print(f"  SIN ENCONTRAR [{cid}] {artista or '?'} - {titulo}")

    print(f"\n  reparables: {len(plan)}   sin encontrar: {sin_encontrar}")
    if not EJECUTAR:
        print("\n  Dry-run. Agregar --si para ejecutar.")
        con.close()
        return
    if not plan:
        con.close()
        return

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = config.BACKUP_FOLDER / f"master_pre_fixpaths_{ts}.db"
    shutil.copy2(config.REKORDBOX_DB_PATH, backup)
    print(f"\n  backup -> {backup}")

    # El USN se actualiza junto con el path: escribir uno sin el otro deja la
    # fila inconsistente para el sync, que es como quedo la mudanza de hoy.
    usn = con.execute("SELECT MAX(rb_local_usn) FROM djmdContent").fetchone()[0] or 0
    ahora = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = fallos = 0
    for cid, nuevo, _ in plan:
        try:
            usn += 1
            con.execute(
                "UPDATE djmdContent SET FolderPath=?, rb_local_usn=?, updated_at=? "
                "WHERE ID=?", (nuevo, usn, ahora, str(cid)))
            con.commit()
            ok += 1
        except Exception as e:  # noqa: BLE001 — un fallo no aborta la tanda
            con.rollback()
            fallos += 1
            print(f"  [ERROR] {cid}: {e}")

    integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
    con.close()
    print(f"\n  rutas corregidas: {ok}   fallos: {fallos}")
    print(f"  integrity_check: {integridad}")


if __name__ == "__main__":
    main()
