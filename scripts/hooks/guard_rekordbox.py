"""Hook PreToolUse: bloquea escrituras a master.db con Rekordbox abierto.

Rekordbox carga master.db en memoria al abrir y la vuelca al cerrar. Cualquier
cambio externo hecho mientras corre se pierde en silencio — o peor, deja la DB
inconsistente. Este proyecto ya perdio una biblioteca entera asi.

El hook lee la llamada a Bash, ve si invoca un script que escribe en la DB, y si
`rekordbox.exe` esta corriendo la corta antes de que pase nada.

Se instala en `.claude/settings.json` como hook PreToolUse sobre Bash.
Salir con codigo 2 bloquea la llamada y le muestra el mensaje al modelo.
"""
from __future__ import annotations

import json
import re
import sys

# Scripts que escriben en master.db. Si agregas uno nuevo que escriba, sumalo
# aca: la lista es la unica cosa que separa un descuido de perder la biblioteca.
ESCRIBEN = {
    "post_import.py", "build_set.py", "build_set_v2.py", "backfill_energy.py",
    "apply_energy_v2.py", "rebuild_all_sets.py", "reorder_sets_energy.py",
    "build_setlist_sets.py", "setup_playlists.py", "create_folder.py",
    "build_collection.py", "build_pools.py", "import_all.py",
    "remove_loops.py", "drop_cues.py", "fix_cues.py", "fix_folders.py",
    "fix_missing_paths.py", "fix_playlist_root.py", "fix_db_wal.py",
    "restore_playlist_tracks.py", "restore_playlists_from_dead.py",
    "repair_db.py", "recover_db.py", "vacuum_db.py", "reorganize_library.py",
    "tidy_library.py", "strip_anlz_loops.py",
    # db_audit hace soft-delete de tracks, reasigna entradas de playlist y mueve
    # archivos. Sin --dry escribe, y se habia colado fuera de esta lista.
    "db_audit.py", "undo_import.py",
}
# Flags que hacen que un script en dry-run pase a escribir de verdad.
SOLO_LECTURA = ("--dry", "--dry-run", "--check")


def main() -> None:
    try:
        evento = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # sin evento parseable, no es asunto del hook

    cmd = (evento.get("tool_input") or {}).get("command", "")
    if not cmd:
        sys.exit(0)

    # Solo cuenta si el script se EJECUTA, no si se lo nombra. Antes bastaba
    # con que el nombre apareciera en cualquier parte del comando, asi que un
    # `sed -n 12,22p scripts/fix_missing_paths.py` —leer el archivo— quedaba
    # bloqueado. Un guardarrail que corta operaciones inofensivas se termina
    # desactivando, y ahi deja de proteger de lo que importa.
    invocados = [
        s for s in ESCRIBEN
        if re.search(r"(?:python[\w.]*[\"']?\s+(?:-[^\s]+\s+)*[\"']?[^\s\"';|&]*"
                     + re.escape(s) + r"|(?:^|[;|&]\s*)\./?[^\s\"';|&]*"
                     + re.escape(s) + r")", cmd)
    ]
    if not invocados:
        sys.exit(0)
    # tidy_library solo escribe con --si; los demas dry-run son inofensivos
    if any(f in cmd for f in SOLO_LECTURA) and "--si" not in cmd:
        sys.exit(0)

    try:
        import psutil
        corriendo = any(
            p.info["name"] and "rekordbox" in p.info["name"].lower()
            for p in psutil.process_iter(["name"]))
    except Exception:
        sys.exit(0)  # sin psutil no bloqueamos: peor seria trabar todo

    if corriendo:
        print(
            f"BLOQUEADO: {', '.join(invocados)} escribe en master.db y "
            "rekordbox.exe esta corriendo.\n"
            "Rekordbox tiene la DB en memoria y sobrescribe todo cambio "
            "externo al cerrar.\n"
            "Cerrar Rekordbox desde System Tray -> Quit (no con la X) y "
            "volver a intentar.",
            file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
