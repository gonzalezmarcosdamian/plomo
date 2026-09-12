"""Recalcula la energia de toda la biblioteca desde los cues YA guardados.

`backfill_energy.py` re-analiza el audio, que para 1883 tracks son horas. No hace
falta: los cues v8 que estan en `djmdCue` guardan exactamente los cuatro momentos
que la formula necesita — "Bass IN", "Breakdown", "DROP" y "Mix-OUT". Leerlos de
la base da el mismo resultado en segundos.

Se usa cuando cambia la FORMULA, no cuando falta el dato. Si un track no tiene
cues, este script lo saltea y lo reporta: ese es trabajo de backfill_energy.py.

Guarda el valor viejo en el comentario como `v1:X.X` para poder comparar y para
poder volver atras sin la base de backup.

Uso:
    python scripts/recalcular_energia.py --dry     # compara v1 contra v2
    python scripts/recalcular_energia.py
"""
from __future__ import annotations

import argparse
import re
import statistics as st
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
from plomo.energy import calculate_energy, energy_label  # noqa: E402

COMMIT_EVERY = 200
E_RE = re.compile(r"^E:\s*([\d.]+)")


def cues_por_track(con) -> dict[str, dict]:
    """{content_id: {bass_in, breakdown, drop, outro}} en milisegundos."""
    mapa: dict[str, dict] = {}
    campo = {"bass in": "bass_in", "breakdown": "breakdown",
             "drop": "drop", "mix-out": "outro"}
    for cid, com, ms in con.execute(
            "SELECT ContentID, Comment, InMsec FROM djmdCue WHERE rb_local_deleted=0"):
        k = campo.get((com or "").strip().lower())
        if k:
            mapa.setdefault(str(cid), {})[k] = int(ms)
    return mapa


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    con = sqlcipher3.connect(str(config.REKORDBOX_DB_PATH))
    con.execute("PRAGMA key = " + repr(config.SQLCIPHER_KEY))
    cues = cues_por_track(con)

    filas = con.execute("""
        SELECT c.ID, c.BPM, c.Length, c.Commnt, c.FileNameL
        FROM djmdContent c WHERE c.rb_local_deleted=0
    """).fetchall()

    cambios, sin_cues, pares = [], 0, []
    for cid, bpm100, length_s, commnt, fname in filas:
        c = cues.get(str(cid))
        if not c:
            sin_cues += 1
            continue
        bpm = (bpm100 or 12200) / 100.0
        nueva = calculate_energy(
            bpm, c.get("bass_in"), c.get("breakdown"), c.get("drop"),
            c.get("outro"), int((length_s or 0) * 1000))
        m = E_RE.match((commnt or "").strip())
        vieja = float(m.group(1)) if m else None
        if vieja is not None:
            pares.append((vieja, nueva, bpm))
        resto = (commnt or "")
        if m:
            resto = resto[m.end():].lstrip(" |").strip()
        resto = re.sub(r"\bv1:[\d.]+\s*\|?\s*", "", resto).strip()
        partes = [f"E:{nueva} [{energy_label(nueva)}]"]
        if vieja is not None:
            partes.append(f"v1:{vieja}")
        if resto:
            partes.append(resto)
        cambios.append((cid, " | ".join(partes)))

    print(f"tracks: {len(filas)} | con cues: {len(cambios)} | sin cues: {sin_cues}")
    if pares:
        v1 = [p[0] for p in pares]
        v2 = [p[1] for p in pares]
        print(f"\n                     v1        v2")
        print(f"  media           {st.mean(v1):6.2f}   {st.mean(v2):6.2f}")
        print(f"  mediana         {st.median(v1):6.2f}   {st.median(v2):6.2f}")
        print(f"  desvio          {st.pstdev(v1):6.2f}   {st.pstdev(v2):6.2f}")
        for u in (7.0, 7.5, 8.0):
            for etq, vals in (("v1", v1), ("v2", v2)):
                alto = [p for p in pares if (p[0] if etq == "v1" else p[1]) >= u]
                if not alto:
                    continue
                bajo = [p for p in alto if p[2] <= 122]
                print(f"  {etq} E>={u}: {len(alto):>4} tracks | "
                      f"con BPM<=122: {len(bajo):>3} ({len(bajo)/len(alto):.0%})")
        # el numero que decide si la fase sirvio
        a2 = [p for p in pares if p[1] >= 7.0]
        if a2:
            pct = sum(1 for p in a2 if p[2] <= 122) / len(a2)
            print(f"\n  CRITERIO DEL PLAN: tracks E>=7.0 con BPM<=122 pasa de 9% a "
                  f"{pct:.0%}  ({'OK' if pct >= 0.25 else 'NO ALCANZA'}, objetivo 25%)")

    if args.dry:
        print("\n[dry] no se escribio nada")
        return

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i, (cid, txt) in enumerate(cambios, 1):
        con.execute("UPDATE djmdContent SET Commnt=?, updated_at=? WHERE ID=?",
                    (txt, ts, cid))
        if i % COMMIT_EVERY == 0:
            con.commit()
    con.commit()
    print(f"\n{len(cambios)} tracks actualizados")
    print("integridad:", con.execute("PRAGMA integrity_check").fetchone()[0])


if __name__ == "__main__":
    main()
