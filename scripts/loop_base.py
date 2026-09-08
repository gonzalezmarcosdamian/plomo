"""Loop minimo de progressive house: bombo, bajo y pad. Nada mas.

Por que existe: `make_sketch.py` genera cinco capas que suenan las ocho compases
enteras — 44 notas por compas, 2.8 por semicorchea. Eso no se escucha como una
idea musical, se escucha como una maquina. El arpegio solo mete 15 notas por
compas sin un hueco.

Este script es el contraejemplo. Tres capas, todo en la grilla, sin jitter ni
swing, y el pad se mueve una sola vez en ocho compases. Si esto suena bien y el
boceto de cinco capas suena mal, el problema nunca fue la cadena ni los
instrumentos: es que la composicion no deja aire.

Esta en F# menor a 121 BPM a proposito, que es la tonalidad y el tempo de
`Simon Vuarambon - Afrika`. Asi se puede poner el tema al lado y comparar.

Uso:
    python scripts/loop_base.py
    python scripts/loop_base.py --bpm 123 --camelot 6A
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.midi import Pista, tonica_de_camelot  # noqa: E402

COMPASES = 8
KICK, CLAP, CHH, OHH, SHAKER = 36, 39, 42, 46, 70

# Progresion: cuatro compases por acorde. Dos acordes en ocho compases parece
# poco escrito hasta que se escucha al lado de uno que cambia cada dos: el que
# cambia poco deja que la atencion vaya al groove, que es donde vive el genero.
# i -> VI en menor (con tonica F#: F#m -> D), el movimiento mas usado
# del progressive.
GRADOS = [0, 5]          # semitonos sobre la tonica: i y VI


def _bateria(bpm: float) -> Pista:
    """Cuatro por cuatro. La variacion es por ausencia, no por agregado."""
    p = Pista("Bateria", bpm, canal=9)
    for c in range(COMPASES):
        for pulso in range(4):
            # el ultimo bombo del loop no suena: el hueco anuncia la vuelta
            if c == COMPASES - 1 and pulso == 3:
                continue
            p.nota(c, pulso, KICK, 0.25, 108)
        for pulso in (1, 3):
            p.nota(c, pulso, CLAP, 0.25, 92)
        # Hat abierto en los cuatro contratiempos: es el pulso de arriba contra
        # el bombo. Va solo, sin hat cerrado encima — dos capas de hat es lo que
        # empieza a sonar a arena.
        for pulso in (0.5, 1.5, 2.5, 3.5):
            p.nota(c, pulso, OHH, 0.22, 64)
        # El shaker entra recien en la segunda mitad. Ocho compases iguales no
        # son una frase; que aparezca un elemento en el cinco si lo es.
        if c >= 4:
            for k in (0.75, 1.75, 2.75, 3.75):
                p.nota(c, k, SHAKER, 0.10, 46)
    return p


def _bajo(bpm: float, tonica: int) -> Pista:
    """Raiz en los contratiempos, corta.

    El bajo no toca donde toca el bombo. Ese entrelazado es lo que hace que el
    groove empuje sin que nada suba de volumen — es la razon por la que en este
    genero el bajo se siente y no se escucha. Tocarlo encima del bombo es el
    error mas comun y suena a una sola cosa gorda en vez de a dos.
    """
    p = Pista("Bajo", bpm, canal=1)
    for c in range(COMPASES):
        raiz = 37 + tonica + GRADOS[c // 4]         # segunda octava
        for pulso in (0.5, 1.5, 2.5, 3.5):
            p.nota(c, pulso, raiz, 0.30, 100)
        # una quinta al final de cada frase de cuatro, para tirar hacia el que sigue
        if c % 4 == 3:
            p.nota(c, 3.75, raiz + 7, 0.20, 88)
    return p


def _pad(bpm: float, tonica: int) -> Pista:
    """Un acorde por frase de cuatro compases, sostenido.

    Sin septima ni novena: la triada sola deja lugar. La septima sostenida ocho
    tiempos con reverb larga es lo que hace que un pad suene a organo de iglesia.
    """
    p = Pista("Acordes", bpm, canal=0)
    for frase, grado in enumerate(GRADOS):
        raiz = 61 + tonica + grado                  # cuarta octava
        # menor para el i, mayor para el VI: es lo que da la escala
        tercera = 3 if grado == 0 else 4
        p.acorde(compas=frase * 4, pulso=0,
                 alturas=[raiz, raiz + tercera, raiz + 7],
                 duracion=15.5, velocidad=58)
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bpm", type=float, default=121.0)
    ap.add_argument("--camelot", default="11A", help="tonalidad (11A = F# menor)")
    ap.add_argument("--salida", type=Path,
                    default=Path("postproduction/bocetos/loop_base"))
    args = ap.parse_args()

    tonica, _ = tonica_de_camelot(args.camelot)
    print(f"  {args.bpm:.0f} BPM, {args.camelot}, {COMPASES} compases")

    args.salida.mkdir(parents=True, exist_ok=True)
    for viejo in args.salida.glob("*.mid"):
        viejo.unlink()
    for n, p in enumerate([_pad(args.bpm, tonica), _bajo(args.bpm, tonica),
                           _bateria(args.bpm)], start=1):
        destino = args.salida / f"{n:02d}_{p.nombre.lower()}.mid"
        p.guardar(destino)
        print(f"  {destino.name:16} {len(p._eventos) // 2:3d} notas = "
              f"{len(p._eventos) // 2 / COMPASES:4.1f} por compas")
    print(f"\n  python scripts/a_live.py {args.salida}")


if __name__ == "__main__":
    main()
