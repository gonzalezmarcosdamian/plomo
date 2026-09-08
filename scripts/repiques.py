"""Saca los repiques de un tema: la percusion que NO es el patron base.

Por que existe: "me gustan los repiques que hace en el drop" es una observacion
precisa que no se puede copiar a ojo. Un repique es, por definicion, lo que
rompe el patron — si sonara todos los compases seria el patron y no un repique.

Asi que se separan por frecuencia de aparicion. Se transcribe la bateria del
fragmento y, para cada posicion de la grilla, se cuenta en cuantos compases
aparece:

  - en casi todos  -> es la base (bombo, clap, hat)
  - en unos pocos  -> es el repique
  - en uno solo    -> puede ser un repique o puede ser un falso positivo del
                      detector, asi que se marca aparte

Eso deja un clip con solo los adornos, que es lo que se queria agregar.

Uso:
    python scripts/repiques.py "<archivo.mp3>" --desde 256 --compases 8
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import librosa
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from copiar_tema import (BANDAS, MARGEN_S, SR, _afinar_bpm, _cuantizar,  # noqa: E402
                         _envolvente, _golpes, _grilla, separar)
from plomo.midi import Pista  # noqa: E402

# Un golpe que aparece en esta fraccion de los compases o mas es la base.
BASE = 0.75
# Debajo de esto es tan raro que puede ser el detector y no el tema.
DUDOSO = 2

# A que nota del drum rack va cada banda cuando es repique. No al mismo lugar
# que la base: un repique de la banda del clap es un tom o una percusion, no
# otro clap encima del clap.
NOTA_REPIQUE = {"kick": 41, "clap": 45, "hat": 51}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", type=Path)
    ap.add_argument("--desde", type=float, required=True)
    ap.add_argument("--compases", type=int, default=8)
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--salida", type=Path)
    args = ap.parse_args()

    if not args.archivo.exists():
        sys.exit(f"no existe {args.archivo}")

    bpm = args.bpm or 121.0
    dur = args.compases * 4 * 60.0 / bpm + 4.0
    rutas = separar(args.archivo, args.desde, dur)
    recorte = min(args.desde, MARGEN_S)
    drums, _ = librosa.load(rutas["drums"], sr=SR, offset=recorte, duration=dur)

    if args.bpm is None:
        crudo = float(np.atleast_1d(librosa.beat.beat_track(y=drums, sr=SR)[0])[0])
        while crudo < 100:
            crudo *= 2
        while crudo > 145:
            crudo /= 2
        bpm = _afinar_bpm(drums, SR, crudo)
    grilla = _grilla(drums, SR, bpm)
    semis = args.compases * 16
    print(f"  BPM {bpm:.1f}, {args.compases} compases desde {args.desde:.0f}s")

    base = Pista("Base", bpm, canal=9)
    repique = Pista("Repiques", bpm, canal=9)
    resumen = []
    for banda, (lo, hi, nota, vel) in BANDAS.items():
        golpes = sorted(x for x in _cuantizar(_golpes(_envolvente(drums, SR, lo, hi), SR),
                                              grilla) if 0 <= x < semis)
        # en cuantos compases distintos aparece cada posicion del compas
        compases_de = defaultdict(set)
        for i in golpes:
            compases_de[i % 16].add(i // 16)

        n_base = n_rep = n_dudoso = 0
        for i in golpes:
            veces = len(compases_de[i % 16])
            if veces >= BASE * args.compases:
                base.nota(i // 16, (i % 16) * 0.25, nota, 0.12, vel)
                n_base += 1
            elif veces < DUDOSO:
                n_dudoso += 1
            else:
                repique.nota(i // 16, (i % 16) * 0.25, NOTA_REPIQUE[banda], 0.10,
                             vel - 10)
                n_rep += 1
        resumen.append(f"  {banda:5} base {n_base:3d}   repique {n_rep:3d}   "
                       f"descartado por raro {n_dudoso:3d}")
    print("\n".join(resumen))

    n_rep_total = sum(1 for e in repique._eventos if e.datos[0] & 0xF0 == 0x90)
    if not n_rep_total:
        print("\n  no hay repiques: toda la percusion de este tramo es patron fijo")
        return

    salida = args.salida or (RAIZ / "postproduction" / "bocetos" /
                             ("repiques_" + "".join(c if c.isalnum() else "_"
                                                    for c in args.archivo.stem.lower())[:32]))
    salida.mkdir(parents=True, exist_ok=True)
    for viejo in salida.glob("*.mid"):
        viejo.unlink()
    for n, p in enumerate([base, repique], start=1):
        p.guardar(salida / f"{n:02d}_{p.nombre.lower()}.mid")
    print(f"\n  {n_rep_total} repiques = {n_rep_total / args.compases:.1f} por compas")
    print(f"  -> {salida}")


if __name__ == "__main__":
    main()
