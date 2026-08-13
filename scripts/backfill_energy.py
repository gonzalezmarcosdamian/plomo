"""Backfill de cues + energia para tracks que quedaron fuera del pipeline.

`post_import.py` elige que procesar por CARPETA (`FolderPath LIKE '%Inbox%'`),
asi que todo lo que entro a la biblioteca antes de que existiera el pipeline
nunca fue candidato. Resultado: 477 tracks (29%) invisibles para `select_set.py`,
incluida una carpeta entera llamada "Peak".

Este script elige por ESTADO: procesa lo que no tiene energia, venga de donde
venga. Es idempotente y reanudable — si se corta, volves a correrlo y sigue.

Preserva el comentario original: guarda `E:5.4 | /* 2025 / Love It */` en vez de
pisarlo. Los 8 scripts que parsean energia usan `split("|")[0]`, asi que el
formato es compatible con todos.

Uso:
    python scripts/backfill_energy.py --dry          # que haria, sin escribir
    python scripts/backfill_energy.py --limit 10     # probar con pocos
    python scripts/backfill_energy.py                # todo
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import sqlcipher3  # noqa: E402

from plomo import config  # noqa: E402
from plomo.cue_engine import analyze_track, apply_cues_v8_direct  # noqa: E402
from plomo.energy import calculate_energy, energy_label  # noqa: E402

COMMIT_EVERY = 10


def pending(con) -> list[tuple]:
    """Tracks sin energia, ordenados por carpeta para que el log sea legible."""
    return con.execute(
        """
        SELECT c.ID, c.FileNameL, c.FolderPath, c.BPM, c.Commnt
        FROM djmdContent c
        WHERE c.rb_local_deleted = 0
          AND (c.Commnt IS NULL OR c.Commnt NOT LIKE 'E:%')
        ORDER BY c.FolderPath
        """
    ).fetchall()


def build_comment(score: float, previo: str | None) -> str:
    """Antepone la energia conservando lo que hubiera antes."""
    previo = (previo or "").strip()
    return f"E:{score} | {previo}" if previo else f"E:{score}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="no escribe en la DB")
    ap.add_argument("--limit", type=int, default=0, help="procesar solo N tracks")
    args = ap.parse_args()

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))

    tracks = pending(con)
    if args.limit:
        tracks = tracks[: args.limit]

    print(f"Tracks sin energia: {len(tracks)}")
    if args.dry:
        from collections import Counter

        car = Counter()
        for _, _, fpath, _, _ in tracks:
            p = Path(fpath or "?")
            car[str(p.parent.name)] += 1
        for c, n in car.most_common(20):
            print(f"  {n:4d}  {c}")
        con.close()
        return

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = fallo = sin_archivo = 0
    t0 = time.time()

    for i, (cid, fname, fpath, bpm_raw, previo) in enumerate(tracks, 1):
        nombre = (fname or str(cid))[:52]
        if not fpath or not Path(fpath).exists():
            sin_archivo += 1
            print(f"  [{i}/{len(tracks)}] SIN ARCHIVO | {nombre}")
            continue

        bpm = (bpm_raw or 12200) / 100
        try:
            cues = analyze_track(fpath, known_bpm=bpm)
        except Exception as e:  # el analisis de audio falla en archivos raros
            fallo += 1
            print(f"  [{i}/{len(tracks)}] ERROR analisis | {nombre}: {e}")
            continue

        if not cues:
            fallo += 1
            print(f"  [{i}/{len(tracks)}] sin cues | {nombre}")
            continue

        try:
            n_markers = apply_cues_v8_direct(con, int(cid), cues)
            score = calculate_energy(
                bpm=bpm,
                bass_in_ms=int(cues.bass_in * 1000) if cues.bass_in else None,
                breakdown_ms=int(cues.breakdown * 1000) if cues.breakdown else None,
                drop_ms=int(cues.drop * 1000) if cues.drop else None,
                outro_ms=int(cues.outro * 1000) if cues.outro else None,
                track_length_ms=None,
            )
            con.execute(
                "UPDATE djmdContent SET Commnt=?, updated_at=? WHERE ID=?",
                (build_comment(score, previo), ts, str(cid)),
            )
        except Exception as e:
            fallo += 1
            print(f"  [{i}/{len(tracks)}] ERROR escritura | {nombre}: {e}")
            continue

        ok += 1
        conservado = " +previo" if (previo or "").strip() else ""
        print(
            f"  [{i}/{len(tracks)}] E:{score} [{energy_label(score):7}] "
            f"{n_markers}m{conservado} | {nombre}"
        )

        if ok % COMMIT_EVERY == 0:
            con.commit()
            transcurrido = time.time() - t0
            resta = (len(tracks) - i) * (transcurrido / i)
            print(f"      ... commit. quedan ~{resta/60:.0f} min")

    con.commit()
    print(
        f"\n=== RESUMEN ===\n"
        f"  Procesados OK:      {ok}\n"
        f"  Sin archivo:        {sin_archivo}\n"
        f"  Fallaron:           {fallo}\n"
        f"  Tiempo:             {(time.time()-t0)/60:.1f} min"
    )
    print("Integridad:", con.execute("PRAGMA integrity_check").fetchone()[0])
    con.close()


if __name__ == "__main__":
    main()
