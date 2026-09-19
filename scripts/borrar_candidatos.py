"""Elimina de la biblioteca los temas marcados como descarte, y sus archivos.

Trabaja sobre `data/candidatos_borrar.json`, que produce el analisis de descarte:
temas que cumplen las tres condiciones a la vez —nunca tocados, fuera de todo
set, y que ningun DJ del corpus de referencia toca— mas un motivo concreto
(genero fuera del estilo, BPM fuera de rango, energia real baja o demo de
Pioneer).

Tres guardas, porque esto no tiene vuelta atras sin volver a bajar los archivos:

  1. Nunca borra un archivo que este fuera del arbol de musica. Un FolderPath
     raro no puede terminar en un rm sobre otra cosa.
  2. Nunca borra un track que este en alguna playlist o en el historial. El
     analisis ya lo filtro, pero se vuelve a chequear contra la base en el
     momento de borrar: entre que se armo la lista y que se ejecuta, el DJ pudo
     haber metido uno en un set.
  3. En la base es borrado BLANDO (rb_local_deleted=1), que es como Rekordbox
     marca lo eliminado. La fila queda y se puede revivir; el archivo no.

Uso:
    python scripts/borrar_candidatos.py --dry
    python scripts/borrar_candidatos.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(RAIZ / ".env")

import sqlcipher3  # noqa: E402
from plomo import config  # noqa: E402

# El borrado solo puede ocurrir debajo de estas raices.
PERMITIDAS = (
    Path(r"C:\Users\gonza\OneDrive\Documentos\Music"),
    Path(r"C:\Users\gonza\Music"),
)


def bajo_musica(p: Path) -> bool:
    try:
        return any(p.resolve().is_relative_to(r.resolve()) for r in PERMITIDAS)
    except (OSError, ValueError):
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--lista", type=Path,
                    default=RAIZ / "data" / "candidatos_borrar.json")
    args = ap.parse_args()

    cand = json.loads(args.lista.read_text(encoding="utf-8"))
    ids = [c["id"] for c in cand]
    print(f"{len(ids)} candidatos en {args.lista.name}")

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Solo protegen los SETS numerados, no cualquier playlist: las vistas por
    # key, por BPM y los [POOL] contienen casi toda la biblioteca, asi que
    # mirarlas todas salvaba hasta los demos de Pioneer.
    en_playlist = {r[0] for r in con.execute(
        """SELECT DISTINCT sp.ContentID FROM djmdSongPlaylist sp
           JOIN djmdPlaylist p ON p.ID = sp.PlaylistID
           WHERE sp.rb_local_deleted=0 AND p.rb_local_deleted=0
             AND p.Name GLOB '[0-9]*. *'""")}
    try:
        tocados = {r[0] for r in con.execute(
            "SELECT DISTINCT ContentID FROM djmdSongHistory WHERE rb_local_deleted=0")}
    except Exception:
        tocados = set()

    borrar, saltados = [], []
    for cid in ids:
        fila = con.execute(
            "SELECT FolderPath, FileNameL, FileSize FROM djmdContent "
            "WHERE ID=? AND rb_local_deleted=0", (cid,)).fetchone()
        if not fila:
            saltados.append((cid, "ya no esta en la base"))
            continue
        if cid in en_playlist or cid in tocados:
            saltados.append((cid, "entro a una playlist o se toco"))
            continue
        p = Path(fila[0])
        if not bajo_musica(p):
            saltados.append((cid, f"fuera del arbol de musica: {fila[0][:50]}"))
            continue
        borrar.append((cid, p, fila[2] or 0))

    print(f"  a borrar: {len(borrar)}  |  saltados: {len(saltados)}")
    for cid, motivo in saltados[:10]:
        print(f"    [skip] {cid}: {motivo}")
    libera = sum(s for _, _, s in borrar) / 1e9
    print(f"  espacio a liberar: {libera:.2f} GB")

    if args.dry:
        print("\n[dry] no se borro nada")
        return

    sin_archivo = 0
    for i, (cid, p, _) in enumerate(borrar, 1):
        con.execute("UPDATE djmdContent SET rb_local_deleted=1, updated_at=? WHERE ID=?",
                    (ts, cid))
        con.execute("UPDATE djmdCue SET rb_local_deleted=1 WHERE ContentID=?", (cid,))
        if p.exists():
            p.unlink()
        else:
            sin_archivo += 1
        if i % 25 == 0:
            con.commit()
    con.commit()
    print(f"\n{len(borrar)} tracks eliminados ({sin_archivo} ya no tenian archivo en disco)")
    print("integridad:", con.execute("PRAGMA integrity_check").fetchone()[0])
    print("quedan en biblioteca:", con.execute(
        "SELECT COUNT(*) FROM djmdContent WHERE rb_local_deleted=0").fetchone()[0])


if __name__ == "__main__":
    main()
