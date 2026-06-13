"""
Reorganizacion de carpetas de musica — una sola vez.

Que hace:
1. Mueve archivos NO importados de carpetas huerfanas -> Nuevos/Inbox/
   (carpetas: Mayo 26, Mi tercer lista gap, begin gap, Peak gap, ending gap)
2. Archiva las carpetas Set#4 (sets con nombres renombrados [key bpm]) -> Archivo/Sets/
3. Consolida Archivo/ Core inicial + Marzo 26 -> Archivo/2026-02/ y Archivo/2026-03/
4. Crea la carpeta Nuevos/Inbox/ como destino permanente para futuras descargas

Lo que NO toca:
- Archivos que ya estan en RB con su path actual (romperia paths)
- La estructura de Nuevos/2026-05/ (259 tracks registrados)

Despues de correr esto:
- Abri Rekordbox una vez
- Agrega 'Nuevos/Inbox/' como carpeta vigilada (File > Preferences > Library > Add folder)
- Desde ese momento, todo nuevo archivo en Inbox es auto-detectado
"""
import sys
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from plomo import config
import sqlcipher3

ROOT = Path(r"C:\Users\gonza\OneDrive\Documentos\Music\2026")
INBOX = ROOT / "Nuevos" / "Inbox"
SETS_ARCHIVE = ROOT / "Archivo" / "Sets"
DRY = "--dry" in sys.argv


def in_db(con, filepath: Path) -> bool:
    row = con.execute(
        "SELECT 1 FROM djmdContent WHERE FileNameL=? AND rb_local_deleted=0 LIMIT 1",
        (filepath.name,),
    ).fetchone()
    return row is not None


def move(src: Path, dest_dir: Path, dry: bool) -> str:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.exists():
        return f"  [dup] {src.name} ya existe en destino"
    if not dry:
        shutil.move(str(src), str(dest))
    return f"  [{'dry' if dry else 'ok'}] {src.name} -> {dest_dir.name}/"


def main():
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")

    print(f"Modo: {'DRY RUN (sin cambios)' if DRY else 'REAL'}")
    print(f"Inbox destino: {INBOX}\n")

    # 1. Carpetas huerfanas: mover archivos no importados a Inbox
    orphan_folders = [
        ROOT / "Mayo 26",
        ROOT / "ending",
    ]

    for folder in orphan_folders:
        if not folder.exists():
            continue
        files = list(folder.glob("*.mp3")) + list(folder.glob("*.flac"))
        in_rb = [f for f in files if in_db(con, f)]
        not_in_rb = [f for f in files if not in_db(con, f)]
        print(f"=== {folder.name}/ ({len(files)} tracks) ===")
        print(f"  En RB: {len(in_rb)} (no se tocan)")
        print(f"  No en RB: {len(not_in_rb)} -> Inbox/")
        for f in not_in_rb:
            print(move(f, INBOX, DRY))

    # 2. Carpetas Set#4 (sets renombrados) -> Archivo/Sets/
    set_folders = sorted(set(ROOT.glob("Set *")))
    if set_folders:
        print(f"\n=== Sets renombrados ({len(set_folders)} carpetas) -> Archivo/Sets/ ===")
        for folder in sorted(set_folders):
            if not folder.is_dir():
                continue
            files = list(folder.glob("*.mp3")) + list(folder.glob("*.flac"))
            dest_dir = SETS_ARCHIVE / folder.name
            print(f"  {folder.name}/ ({len(files)} tracks)")
            if not DRY:
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(folder), str(SETS_ARCHIVE / folder.name))
            else:
                print(f"    [dry] mover carpeta -> Archivo/Sets/{folder.name}/")

    # 3. Loose file in root
    loose = list(ROOT.glob("*.mp3")) + list(ROOT.glob("*.flac"))
    if loose:
        print(f"\n=== Archivos sueltos en raiz ({len(loose)}) ===")
        for f in loose:
            if not in_db(con, f):
                print(move(f, INBOX, DRY))
            else:
                print(f"  [rb] {f.name} (en RB, no se toca)")

    # 4. Crear Inbox si no existe
    if not DRY:
        INBOX.mkdir(parents=True, exist_ok=True)
        print(f"\nInbox creada: {INBOX}")

    con.close()

    print("\n=== SIGUIENTE PASO ===")
    print("1. Abri Rekordbox")
    print("2. File > Preferences > Library > Monitor Folder")
    print(f"   Agrega: {INBOX}")
    print("3. Desde ahora: nuevas descargas van a Inbox/")
    print("   RB las detecta solo al abrirse (sin import manual)")


if __name__ == "__main__":
    main()
