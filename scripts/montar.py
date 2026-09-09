"""Monta el tema entero en el arreglo de Ableton Live.

Por que existe: `idea.py --tema` escribe nueve carpetas de MIDI, una por parte, y
cada una arranca en su propio compas 0. Alguien tiene que ponerlas en el compas
que les toca del arreglo, en la pista que les toca, y eso a mano son ochenta
clips que hay que arrastrar sin equivocarse ni uno.

Lo primero que hace es BORRAR el arreglo de cada pista, y eso no es una
precaucion sino una correccion. `duplicate_clip_to_arrangement` reemplaza lo que
pisa, asi que si la version anterior tenia un clip en el compas 65 y la nueva no
pone nada ahi, el clip viejo sobrevive y suena. El sintoma es un tema que suena
bien la primera vez y raro la segunda, con capas que aparecen donde no se
escribio nada — y como el MIDI en disco esta bien, se busca el error en el
generador, que es donde no esta.

No hay handler de borrado en AbletonOSC, asi que el borrado se hace poniendo un
clip vacio del largo del tema entero: pisa todo y no suena nada.

Uso:
    python scripts/idea.py --nombre v1 --tema
    python scripts/montar.py v1
    python scripts/montar.py v1 --desde 160     # y arranca a sonar ahi
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from idea import FORMA  # noqa: E402
from plomo.live import Live  # noqa: E402
from plomo.midi import leer  # noqa: E402

# Que archivo va en que pista de Live. El numero del nombre es el orden de la
# capa, no la pista: las pistas 0 a 3 son las que trae el set vacio.
PISTAS = {
    "01_atmosfera.mid": 4,  "02_acordes.mid": 5,   "03_bajo.mid": 6,
    "04_bateria.mid": 7,    "05_gancho.mid": 8,    "06_arpegio.mid": 9,
    "07_cierre.mid": 10,    "08_anchos.mid": 11,   "09_sub.mid": 12,
    "10_repiques.mid": 13,  "11_splash.mid": 14,   "12_reversa.mid": 15,
    "13_lead.mid": 16,   "14_riser.mid": 17,
    # Las capas de espesor van a las pistas que la v2 dejaba vacias. No hay
    # conflicto con la v1 porque cada version usa su propia receta de set y
    # ninguna de las dos usa los dos juegos a la vez.
    "15_bajo2.mid": 9,   "16_textura.mid": 10,
    "17_subkick.mid": 11, "18_metales.mid": 16,
}

# El gancho se escribe en la octava 4 y suena una octava mas abajo. Es del
# pedido "la melodia bajale una octava" y vive aca, en el montaje, para que el
# MIDI en disco siga siendo el que escribio el generador.
TRANSPONE = {"05_gancho.mid": -12}


def montar(carpeta: Path, live: Live) -> int:
    total = max(c + l for _, c, l in FORMA)

    usadas = sorted({PISTAS[f.name]
                     for nom, _, _ in FORMA
                     for f in (carpeta / nom).glob("*.mid")
                     if f.name in PISTAS})
    print(f"  borrando el arreglo de {len(usadas)} pistas")
    for t in usadas:
        live.cargar_midi(t, 0, [], largo_compases=total)
        time.sleep(0.25)
        live.preguntar("/live/arrangement/duplicate", t, 0, 0.0)
        time.sleep(0.25)

    for nombre, compas, largo in FORMA:
        d = carpeta / nombre
        capas = []
        for f in sorted(d.glob("*.mid")):
            if f.name not in PISTAS:
                print(f"    ? {f.name} no tiene pista asignada")
                continue
            _, _, notas = leer(f)
            salto = TRANSPONE.get(f.name, 0)
            if salto:
                notas = [(i, du, a + salto, v) for i, du, a, v in notas]
            live.cargar_midi(PISTAS[f.name], 0, notas, largo_compases=largo)
            time.sleep(0.28)
            live.preguntar("/live/arrangement/duplicate",
                           PISTAS[f.name], 0, float(compas))
            time.sleep(0.24)
            capas.append(f.stem[3:])
        print(f"  {compas + 1:>4}-{compas + largo:<5} {nombre:<11} "
              f"{len(capas):>2}  {', '.join(capas)}", flush=True)
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("nombre", help="carpeta bajo postproduction/bocetos")
    ap.add_argument("--desde", type=int, default=1,
                    help="compas donde arrancar a sonar")
    args = ap.parse_args()

    carpeta = RAIZ / "postproduction" / "bocetos" / args.nombre
    if not carpeta.exists():
        sys.exit(f"no existe {carpeta}")

    with Live(timeout=45.0) as live:
        total = montar(carpeta, live)
        # El loop cubre el tema entero. Sin esto el cabezal se va mas alla del
        # final y el sintoma es "no suena", que manda a revisar el audio cuando
        # el problema es donde esta parado el cabezal.
        live.enviar("/live/song/set/loop_start", 0.0)
        live.enviar("/live/song/set/loop_length", float(total * 4))
        live.enviar("/live/song/set/loop", 1)
        # Primero se arranca el transporte y DESPUES se mueve el cabezal.
        #
        # El orden importa y es al reves de lo que parece. Medido sobre el set:
        #
        #     posicion -> start_playing       queda en el compas 2
        #     posicion -> continue_playing    a veces anda, a veces no
        #     start_playing -> posicion       anda siempre
        #
        # `start_playing` arranca desde el marcador de inicio y pisa cualquier
        # posicion escrita antes; `continue_playing` retoma desde donde se paro,
        # que tampoco es donde uno la puso. Con el transporte ya andando, escribir
        # `current_song_time` es un salto y se respeta.
        #
        # El sintoma de tenerlo al reves es "no suena": suena, pero en el compas 2
        # de una intro que son treinta y dos compases de groove, asi que durante
        # un minuto no pasa nada de lo que se queria escuchar.
        live.enviar("/live/song/start_playing")
        time.sleep(0.6)
        live.enviar("/live/song/set/current_song_time", float((args.desde - 1) * 4))
        time.sleep(1.2)
        print(f"\n  {total} compases · sonando desde el {args.desde}")


if __name__ == "__main__":
    main()
