# -*- coding: utf-8 -*-
"""Vuelve a poner los cues de los temas de un set con la estructura de la mezcla.

"1 como el que mezcla que lo veo joya cada vez que escucho / armalo" (el DJ, 2026-10-27). Los cues
salen de plomo.cues_mezcla (la misma medicion que mezclar.py, sobre la grilla de Rekordbox) con el
mismo layout de siempre. Un tema con cues puestos a mano no se toca: se informa.

Uso:
    python scripts/recuear.py 159 --dry     # compara, en compases, los cues de hoy con los nuevos
    python scripts/recuear.py 159           # backup y escribe (Rekordbox cerrado)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAMPOS = [("mix_in", "first_beat"), ("bass_in", "bass_in"), ("breakdown", "breakdown"), ("drop", "drop"),
          ("mix_out", "outro")]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("set", help="el numero de la playlist, ej. 159")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    from plomo.cue_engine import apply_cues_v8_direct
    from plomo.cues_mezcla import analizar, cues_a_mano
    from plomo.mezcla import _abrir_db, en_compases, leer_set
    from plomo.rekordbox_app import esta_abierto

    if not a.dry and esta_abierto():
        raise SystemExit("Rekordbox esta abierto: cerralo y volve a correr.")
    temas = leer_set(a.set)
    ro = _abrir_db()
    nuevos, saltear = {}, {}
    print(f"{'tema':38s} " + " ".join(f"{c:>13s}" for c, _ in CAMPOS) + "   (compases: hoy -> nuevo)")
    for t in temas:
        a_mano = cues_a_mano(ro, t.content_id)
        try:
            c = analizar(t)
        except (ValueError, IndexError) as err:
            saltear[t.content_id] = f"no se pudo medir: {err}"
            print(f"{t.titulo[:38]:38s} NO SE PUDO MEDIR: {err}")
            continue
        if a_mano:
            saltear[t.content_id] = "cues a mano: " + ", ".join(a_mano)
        nuevos[t.content_id] = c
        celdas = []
        for viejo, nuevo in CAMPOS:
            v, n = t.cues.get(viejo), getattr(c, nuevo)
            fv = f"{en_compases(t, v):.0f}" if v is not None else "-"
            fn = f"{en_compases(t, n):.0f}" if n is not None else "-"
            celdas.append(f"{fv:>5s} -> {fn:<4s}")
        print(f"{t.titulo[:38]:38s} " + " ".join(celdas) + ("   A MANO" if a_mano else ""))
    ro.close()
    for cid, motivo in saltear.items():
        print(f"  no se toca {cid}: {motivo}")
    if a.dry:
        print(f"--dry: {len(nuevos) - len([c for c in saltear if c in nuevos])} temas se escribirian")
        return

    subprocess.run([sys.executable, str(RAIZ / "scripts" / "backup.py"), f"antes_recuear_{a.set}"], check=True)
    from build_set import db_connect
    con = db_connect()
    escritos = 0
    for cid, c in nuevos.items():
        if cid in saltear:
            continue
        escritos += 1 if apply_cues_v8_direct(con, int(cid), c) else 0
    con.commit()
    print(f"{escritos} temas con cues nuevos | integridad: {con.execute('PRAGMA quick_check').fetchone()[0]}")
    con.close()


if __name__ == "__main__":
    main()
