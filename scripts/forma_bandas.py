"""La forma de un tema leida por nivel de bandas, compas por compas.

Por que existe. `estructura.py` clasifica por umbrales relativos y se EQUIVOCA
en las partes fuertes: el detector de bombo se satura y marca "BAJADA" donde hay
drop. Sobre Interlocutor dio 40 compases de bajada en el medio del tema, y el
nivel de graves mostraba que ahi habia pleno.

El nivel de graves no se equivoca. Un tema de este genero tiene dos estados
claros y separados por diez o mas dB: con bombo y bajo (-9 a -12 dBFS en
30-200 Hz) y sin ellos (-16 a -29). La frontera es inequivoca y no hay que
calibrar nada.

Ademas de la forma imprime los MEDIOS y los AGUDOS de cada bloque, que es lo que
permitio descubrir que en un breakdown los medios SUBEN. Sin esas dos columnas
la forma sola no dice que hacer adentro de cada seccion.

Uso:
    python scripts/forma_bandas.py "<mp3>"
    python scripts/forma_bandas.py --lista postproduction/refs_prog.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from copiar_tema import _banda  # noqa: E402

SR = 22050
BANDAS = {"graves": (30, 200), "medios": (200, 3000), "agudos": (3000, 11000)}
# Un bloque nuevo empieza cuando los graves cambian mas que esto. 6 dB separa
# "entro el bajo" de "el compas sono un poco mas fuerte".
SALTO_DB = 6.0
MINIMO = 4          # una seccion dura al menos una frase


def _db(y: np.ndarray) -> float:
    return float(20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-9))


def forma(archivo: Path, bpm: float | None = None) -> list[tuple]:
    y, _ = librosa.load(archivo, sr=SR)
    if bpm is None:
        crudo = float(np.atleast_1d(librosa.beat.beat_track(y=y, sr=SR)[0])[0])
        while crudo < 100:
            crudo *= 2
        while crudo > 145:
            crudo /= 2
        bpm = crudo
    x = int(round(SR * 4 * 60.0 / bpm))
    b = {n: _banda(y, SR, lo, hi) for n, (lo, hi) in BANDAS.items()}
    n = len(y) // x
    filas = [(i, _db(y[i * x:(i + 1) * x]),
              *[_db(b[k][i * x:(i + 1) * x]) for k in BANDAS]) for i in range(n)]

    # bloques: se corta donde los graves saltan mas de SALTO_DB
    bloques, ini = [], 0
    for i in range(1, n):
        if abs(filas[i][2] - filas[ini][2]) > SALTO_DB and i - ini >= MINIMO:
            bloques.append((ini, i))
            ini = i
    bloques.append((ini, n))
    fuera = []
    for a, z in bloques:
        if z - a < MINIMO and fuera:          # pegar los restos al anterior
            a0, z0, *_ = fuera[-1]
            fuera[-1] = (a0, z, *[float(np.mean([f[k] for f in filas[a0:z]]))
                                  for k in range(1, 5)])
            continue
        fuera.append((a, z, *[float(np.mean([f[k] for f in filas[a:z]]))
                              for k in range(1, 5)]))
    return [(bpm, n)] + fuera


def mostrar(archivo: Path) -> None:
    r = forma(archivo)
    bpm, total = r[0]
    print(f"\n  {archivo.stem[:70]}")
    print(f"  {bpm:.0f} BPM · {total} compases · {total * 4 * 60 / bpm / 60:.1f} min\n")
    print(f"   {'compases':>11} {'largo':>5} {'total':>7} {'graves':>7} {'medios':>7} {'agudos':>7}   estado")
    for a, z, tot, gr, me, ag in r[1:]:
        # el estado sale del grave: es lo unico que separa los dos modos
        estado = "PLENO" if gr > -14 else ("bajon" if gr > -19 else "SIN GRAVES")
        print(f"   {a + 1:>5}-{z:<5} {z - a:>5} {tot:7.1f} {gr:7.1f} {me:7.1f} {ag:7.1f}   {estado}")
    # lo que se usa para escribir: los medios del breakdown contra los del drop
    plenos = [x for x in r[1:] if x[3] > -14]
    vacios = [x for x in r[1:] if x[3] <= -19 and x[1] - x[0] >= 8]
    if plenos and vacios:
        pd = max(plenos, key=lambda x: x[1] - x[0])
        bd = max(vacios, key=lambda x: x[1] - x[0])
        print(f"\n   drop mas largo      {pd[0]+1:>4}-{pd[1]:<4} medios {pd[4]:6.1f}  agudos {pd[5]:6.1f}")
        print(f"   breakdown mas largo {bd[0]+1:>4}-{bd[1]:<4} medios {bd[4]:6.1f}  agudos {bd[5]:6.1f}")
        print(f"   -> en el breakdown los medios van {bd[4] - pd[4]:+.1f} dB y los agudos {bd[5] - pd[5]:+.1f} dB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", type=Path, nargs="?")
    ap.add_argument("--lista", type=Path)
    args = ap.parse_args()
    objetivos = ([args.archivo] if args.archivo else
                 [Path(l.strip()) for l in args.lista.read_text(encoding="utf-8").splitlines()
                  if l.strip()] if args.lista else [])
    if not objetivos:
        sys.exit("dame un archivo o --lista")
    for f in objetivos:
        try:
            mostrar(f)
        except Exception as e:                      # noqa: BLE001
            print(f"  - {f.stem[:50]}: {e}")


if __name__ == "__main__":
    main()
