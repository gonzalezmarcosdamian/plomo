"""
Elimina todos los loops de la biblioteca de Rekordbox.

Un loop es un cue con OutMsec > 0 (tiene punto de salida) o con BeatLoopSize.
Los borra de djmdCue y ademas los saca del JSON de ContentCue.Cues, que es lo
que Rekordbox lee para dibujar los markers — si solo se borra djmdCue, los loops
siguen apareciendo.

Los cues normales (Mix-IN, Bass IN, Breakdown, DROP, Mix-OUT) no se tocan.

Uso:
  python scripts/remove_loops.py --dry    # reporta, no modifica
  python scripts/remove_loops.py          # elimina

Rekordbox debe estar cerrado (System Tray -> Quit).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import sqlcipher3  # noqa: E402
from plomo import config  # noqa: E402

DRY = "--dry" in sys.argv


def db_connect() -> sqlcipher3.Connection:
    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute(f"PRAGMA key = '{config.SQLCIPHER_KEY}'")
    return con


def is_loop(cue: dict) -> bool:
    """Un cue es loop si tiene punto de salida o tamano de beatloop."""
    out_msec = cue.get("OutMsec")
    if out_msec is not None and out_msec > 0:
        return True
    return cue.get("BeatLoopSize") is not None


def report(con: sqlcipher3.Connection) -> int:
    rows = con.execute(
        """
        SELECT COALESCE(Comment, '(sin comment)'), COUNT(*), COUNT(DISTINCT ContentID)
        FROM djmdCue
        WHERE rb_local_deleted = 0
          AND ((OutMsec IS NOT NULL AND OutMsec > 0) OR BeatLoopSize IS NOT NULL)
        GROUP BY Comment ORDER BY COUNT(*) DESC
        """
    ).fetchall()

    total = sum(r[1] for r in rows)
    print("=== LOOPS ENCONTRADOS ===")
    for comment, count, tracks in rows:
        print(f"  {count:>6} cues en {tracks:>5} tracks | {comment}")
    print(f"  {'-' * 50}\n  {total} loops en total")

    active = con.execute(
        "SELECT COUNT(*) FROM djmdCue WHERE rb_local_deleted=0 AND ActiveLoop=1"
    ).fetchone()[0]
    print(f"  de los cuales auto-activados (ActiveLoop=1): {active}")
    return total


def clean_content_cue_json(con: sqlcipher3.Connection, ts: str) -> int:
    """Saca los loops del JSON de ContentCue.Cues. Devuelve filas actualizadas."""
    rows = con.execute(
        "SELECT ID, Cues FROM ContentCue WHERE rb_local_deleted = 0 AND Cues IS NOT NULL"
    ).fetchall()

    updated = 0
    for cc_id, cues_json in rows:
        try:
            cues = json.loads(cues_json)
        except (ValueError, TypeError):
            continue
        if not isinstance(cues, list):
            continue

        kept = [c for c in cues if isinstance(c, dict) and not is_loop(c)]
        if len(kept) == len(cues):
            continue

        if not DRY:
            con.execute(
                "UPDATE ContentCue SET Cues=?, updated_at=? WHERE ID=?",
                (json.dumps(kept), ts, cc_id),
            )
        updated += 1

    return updated


def delete_loop_cues(con: sqlcipher3.Connection, ts: str) -> int:
    """
    Borrado FISICO, no logico.

    El borrado logico (rb_local_deleted=1) es lo que usa el resto del proyecto,
    pero para los loops no alcanza: la fila sigue en la tabla y Rekordbox no
    filtra esa columna en todos los caminos de codigo — sobre todo al exportar
    los cues al USB. Resultado: los loops seguian apareciendo en el CDJ despues
    de "borrarlos". Con DELETE no queda dato que se pueda leer.
    """
    cur = con.execute(
        """
        DELETE FROM djmdCue
        WHERE (OutMsec IS NOT NULL AND OutMsec > 0) OR BeatLoopSize IS NOT NULL
        """
    )
    return cur.rowcount


def main() -> None:
    if DRY:
        print("DRY RUN — no se modifica nada\n")

    con = db_connect()
    total = report(con)

    if total == 0:
        print("\nNo hay loops que eliminar.")
        con.close()
        return

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json_updated = clean_content_cue_json(con, ts)
    deleted = 0 if DRY else delete_loop_cues(con, ts)

    print("\n=== RESUMEN ===")
    print(f"  Cues de loop eliminados:        {deleted if not DRY else total}")
    print(f"  Tracks con ContentCue limpiado: {json_updated}")

    if DRY:
        con.close()
        print("\n[DRY RUN] No se modifico nada.")
        return

    con.commit()
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    con.close()
    print(f"\nIntegridad SQLite: {integrity}")
    print("Abri Rekordbox y hace sync al pen.")


if __name__ == "__main__":
    main()
