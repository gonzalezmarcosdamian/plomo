"""Manda un boceto a Ableton Live, una pista por clip.

Es el reemplazo de `render_sketch.py` como forma de escuchar un boceto. La
sintesis propia llego a su techo: un pad hecho con sumas de senoides suena a eso,
y ningun parametro lo arregla. Live tiene instrumentos.

El render sintetico queda en el proyecto, pero para lo que sirve de verdad:
verificar que la forma del arreglo y el balance esten donde tienen que estar.
Para escuchar si el track existe, va esto.

Antes de la primera corrida, una sola vez:
    1. Abrir Live
    2. Preferences > Link/Tempo/MIDI > Control Surface -> "AbletonOSC"
    3. Live avisa "AbletonOSC: Listening for OSC on port 11000"

Uso:
    python scripts/a_live.py --test
    python scripts/a_live.py postproduction/bocetos/lo_tocado_6A
    python scripts/a_live.py <carpeta> --bpm 122
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.live import Live, LiveNoResponde, cargar_boceto  # noqa: E402

AYUDA = """
  Live no contesta. Lo mas probable, en orden:

    1. Live no esta abierto.
    2. El Control Surface no esta activado:
       Preferences > Link/Tempo/MIDI > Control Surface -> AbletonOSC
       Al activarlo Live muestra "Listening for OSC on port 11000".
    3. Live se abrio antes de que se instalara el script: cerralo y abrilo de
       nuevo para que lo vea.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta", nargs="?", type=Path,
                    help="carpeta del boceto con los .mid")
    ap.add_argument("--bpm", type=float, help="pisa el BPM del MIDI")
    ap.add_argument("--filtro", help="filtra el --browser por subcadena")
    ap.add_argument("--instrumento", nargs=2, metavar=("PISTA", "NOMBRE"),
                    help="cambia el instrumento de una pista, ej: --instrumento 7 'Vibes Mellow'")
    ap.add_argument("--categoria", default="instruments",
                    help="rama del browser para --instrumento (instruments, drums)")
    ap.add_argument("--sin-instrumentos", action="store_true",
                    help="deja las pistas vacias de dispositivo")
    ap.add_argument("--test", action="store_true",
                    help="solo verifica la conexion y muestra un cartel en Live")
    ap.add_argument("--browser", metavar="CATEGORIA", nargs="?", const="instruments",
                    help="lista que hay para cargar (instruments, drums, "
                         "audio_effects, sounds, packs, user_library)")
    args = ap.parse_args()

    try:
        if args.browser:
            with Live() as live:
                nombres = live.listar_browser(args.browser, args.filtro or "")
                print(f"  {args.browser}: {len(nombres)} cargables")
                for n in nombres:
                    print(f"    {n}")
            return
        if args.instrumento:
            pista, nombre = int(args.instrumento[0]), args.instrumento[1]
            with Live() as live:
                cargado = live.cambiar_instrumento(pista, [nombre], args.categoria)
            if cargado is None:
                sys.exit(f"  no se encontro '{nombre}' en {args.categoria}")
            print(f"  pista {pista}: {cargado}")
            return
        if args.test or not args.carpeta:
            with Live() as live:
                print(f"  conectado a Live {live.version()}")
                print(f"  tempo actual: {live.tempo():.0f} BPM")
                print(f"  pistas: {live.n_pistas()}")
                live.test()
                print("  (mira la pantalla de Live: tiene que aparecer un cartel)")
            return
        if not args.carpeta.exists():
            sys.exit(f"no existe {args.carpeta}")
        cargar_boceto(args.carpeta, args.bpm,
                      con_instrumentos=not args.sin_instrumentos)
        print()
        print("  Listo, dale play. El instrumento de cada pista es un punto")
        print("  de partida, no la eleccion final: cambialo escuchando.")
    except LiveNoResponde as e:
        print(f"\n{e}\n{AYUDA}")
        sys.exit(1)


if __name__ == "__main__":
    main()
