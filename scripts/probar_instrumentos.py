"""Carga el mismo clip en varias pistas, una por instrumento, para comparar.

Por que existe: probar presets de a uno es lento y engañoso. Entre que suena el
primero y suena el cuarto pasaron minutos, y el oido no compara contra un
recuerdo de hace tres minutos — compara contra lo que acaba de escuchar. Con
todos cargados al mismo tiempo, cambiar de uno a otro es un click y la
comparacion es real.

Deja todas las pistas muteadas menos la primera. Se pasa de una a otra con el
mute de Live, o con:

    python scripts/probar_instrumentos.py --solo 3

Uso:
    python scripts/probar_instrumentos.py postproduction/bocetos/x/04_detalle.mid \\
        "Soft Morning Keys" "Sencha Arp" "Lost in Plucks"
"""
from __future__ import annotations

import argparse
import sys
from math import ceil
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.live import Live, LiveNoResponde  # noqa: E402
from plomo.midi import leer  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("clip", nargs="?", type=Path, help="el .mid a repetir")
    ap.add_argument("instrumentos", nargs="*", help="nombres de preset")
    ap.add_argument("--categoria", default="instruments")
    ap.add_argument("--desde", type=int, help="primera pista del grupo (para --solo)")
    ap.add_argument("--solo", type=int,
                    help="deja sonando solo la enesima del grupo (1 = la primera)")
    args = ap.parse_args()

    try:
        if args.solo is not None:
            if args.desde is None:
                sys.exit("  --solo necesita --desde con la primera pista del grupo")
            with Live() as live:
                n = live.n_pistas()
                objetivo = args.desde + args.solo - 1
                for i in range(args.desde, n):
                    live.enviar("/live/track/set/mute", i, 0 if i == objetivo else 1)
                live.enviar("/live/scene/fire", 0)
                print(f"  sonando solo la pista {objetivo}")
            return

        if not args.clip or not args.instrumentos:
            sys.exit("  faltan el clip y al menos un instrumento")
        if not args.clip.exists():
            sys.exit(f"  no existe {args.clip}")

        nombre, bpm, notas = leer(args.clip)
        # el mismo largo que usa cargar_boceto: compases enteros, para que no se
        # desfase contra las pistas que ya estan sonando
        compases = max(4, ceil(ceil(max(n[0] for n in notas) / 4 + 1e-9) / 4) * 4)

        with Live() as live:
            primera = live.n_pistas()
            for i, preset in enumerate(args.instrumentos):
                pista = live.crear_pista_midi(f"{i + 1}. {preset}"[:30])
                live.cargar_midi(pista, 0, notas, largo_compases=compases)
                cargado = live.cargar_instrumento(pista, [preset], args.categoria)
                live.enviar("/live/track/set/mute", pista, 0 if i == 0 else 1)
                print(f"  pista {pista}: {cargado or 'NO ENCONTRADO: ' + preset}")
            live.enviar("/live/scene/fire", 0)

        print(f"\n  {len(args.instrumentos)} candidatos en las pistas "
              f"{primera}-{primera + len(args.instrumentos) - 1}, "
              f"suena el primero.")
        print(f"  para cambiar:  python scripts/probar_instrumentos.py "
              f"--desde {primera} --solo 2")
    except LiveNoResponde as e:
        sys.exit(f"\n{e}")


if __name__ == "__main__":
    main()
