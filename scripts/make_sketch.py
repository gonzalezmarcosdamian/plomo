"""Genera un boceto de track: clips MIDI + plano de arreglo, listos para Ableton.

No compone: arma el esqueleto. Progresion, bajo rodante, arpegio, bateria y una
linea de melodia en la tonalidad y el BPM que se le pidan, mas un plano de
arreglo con los compases reales derivados de un corpus medido
(`scripts/derive_template.py`).

La musica la hace uno; esto ahorra los cuarenta minutos de poner la grilla,
elegir la tonalidad y decidir en que compas va el breakdown.

Los clips son loops de 8 compases pero NO son ocho compases iguales: el bajo
cambia cada cuatro, el arpegio se abre en la segunda mitad, la bateria tiene
fills, y todo lleva swing y variacion de velocidad. Ocho compases identicos
suenan a maquina; ese es el defecto que mas rapido delata a un boceto.

Uso:
    python scripts/make_sketch.py --camelot 4A --bpm 123
    python scripts/make_sketch.py --camelot 8A --registro oscuro
    python scripts/make_sketch.py --camelot 4A --registro heroico --swing 0.10
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.midi import (  # noqa: E402
    MAYOR, MENOR, Pista, grado, nombre_tonalidad, tonica_de_camelot, triada,
)

RAIZ = Path(__file__).resolve().parent.parent
COMPASES_LOOP = 8

# Progresiones por registro, en grados de la escala (0 = tonica).
# Dos compases por acorde: ocho compases de loop.
PROGRESIONES = {
    "luminoso": ([0, 5, 2, 6], "i - VI - III - VII. La progresion del progressive "
                               "melodico: melancolica pero que empuja hacia arriba."),
    "oscuro":   ([0, 6, 5, 6], "i - VII - VI - VII. No resuelve nunca. Es la que "
                               "sostiene una meseta hipnotica sin cansar."),
    "suspendido": ([0, 4, 5, 2], "i - v - VI - III. El v menor en vez de mayor deja "
                                 "todo en suspenso: sirve para breakdowns largos."),
    "heroico":  ([5, 6, 0, 6], "VI - VII - i - VII. La cadencia que aterriza en la "
                               "tonica y vuelve a empujar. Es la progresion de los "
                               "momentos de aplauso, y no hay que tenerle verguenza."),
}

# Notas del drum rack de Ableton.
KICK, CLAP, CHH, OHH, RIDE, SHAKER = 36, 39, 42, 46, 51, 70

# Cuanto se corre la contratiempo de semicorchea. 0 = cuantizado duro.
SWING = 0.07
# Variacion de velocidad y de microtiming. Sin esto ocho compases suenan iguales
# porque LO SON.
JITTER_VEL = 9
JITTER_TIEMPO = 0.012


class Humano:
    """Aplica microtiming y variacion de velocidad con semilla fija.

    Semilla fija a proposito: dos corridas del mismo boceto tienen que dar el
    mismo archivo, si no no se pueden comparar dos versiones.
    """

    def __init__(self, semilla: int = 12, swing: float = SWING) -> None:
        self.rng = random.Random(semilla)
        self.swing = swing

    def pulso(self, p: float) -> float:
        """Swing sobre las semicorcheas impares, mas un jitter chico."""
        if abs((p * 4) % 2 - 1) < 1e-6:      # cae en semicorchea impar
            p += self.swing * 0.25
        return max(0.0, p + self.rng.uniform(-JITTER_TIEMPO, JITTER_TIEMPO))

    def vel(self, v: int) -> int:
        return max(1, min(127, v + self.rng.randint(-JITTER_VEL, JITTER_VEL)))


def _acordes(bpm: float, tonica: int, escala: list[int], grados: list[int],
             h: Humano) -> Pista:
    """Pad sostenido + stabs en contratiempo + una voz superior que se mueve.

    El pad solo, plano dos compases, es lo que hace que un boceto suene a
    plantilla. Los stabs y la voz que camina le dan direccion adentro del acorde.
    """
    p = Pista("Acordes", bpm, canal=0)
    for i, g in enumerate(grados):
        # Triada sin novena y con la septima solo en el primer compas. La
        # septima MAS la novena sostenidas ocho tiempos con ataque lento y
        # reverb larga es literalmente un organo de iglesia: el apilado suena
        # a himno antes de que entre nada mas.
        base = triada(tonica, escala, g, octava=3, septima=False)
        color = triada(tonica, escala, g, octava=3, septima=True)
        c0 = i * 2
        # el colchon deja un hueco al final de cada compas en vez de tapar todo
        p.acorde(compas=c0, pulso=0, alturas=base, duracion=3.4, velocidad=62)
        p.acorde(compas=c0 + 1, pulso=0, alturas=color, duracion=3.4, velocidad=58)
        # stabs en el contratiempo: es donde el pad respira contra el kick
        for c in (c0, c0 + 1):
            for pulso in (1.5, 3.5):
                p.acorde(c, h.pulso(pulso), base[1:], duracion=0.30,
                         velocidad=h.vel(78 if pulso == 1.5 else 66))
    return p


def _bajo(bpm: float, tonica: int, escala: list[int], grados: list[int],
          h: Humano) -> Pista:
    """Bajo rodante: nada en el pulso, todo en el contratiempo.

    Es lo que hace que un progressive respire en vez de marchar. El kick ocupa
    el pulso, el bajo ocupa el hueco. Cada cuatro compases cambia el patron:
    ocho compases del mismo bajo es la definicion de rigido.
    """
    p = Pista("Bajo", bpm, canal=0)
    for i, g in enumerate(grados):
        raiz = grado(tonica, escala, g, octava=1)
        quinta = grado(tonica, escala, g + 4, octava=1)
        for c in (i * 2, i * 2 + 1):
            segunda_mitad = c >= 4
            roll = c == 7   # solo al cerrar el loop, no cada cuatro
            for pulso in (0.5, 1.5, 2.5, 3.5):
                # Casi siempre la fundamental. Un bajo hipnotico no cuenta una
                # melodia: ancla. La quinta aparece una vez cada ocho compases,
                # no una vez por compas.
                alt = raiz
                if segunda_mitad and c == 6 and pulso == 2.5:
                    alt = quinta
                # si viene el roll, esta nota se acorta para no pisarlo: dos
                # notas del mismo tono superpuestas se pierden al leer el MIDI
                dur = 0.16 if (roll and pulso == 3.5) else 0.30
                p.nota(c, h.pulso(pulso), alt, duracion=dur,
                       velocidad=h.vel(106 if pulso == 0.5 else 88))
            if roll:
                p.nota(c, h.pulso(3.75), raiz, 0.18, h.vel(98))
    return p


def _arpegio(bpm: float, tonica: int, escala: list[int], grados: list[int],
             h: Humano) -> Pista:
    """Semicorcheas sobre las notas del acorde, con swing.

    Primera mitad cerrada, segunda mitad una octava arriba y con otro contorno:
    el arpegio es el que mas rapido cansa si no se mueve.
    """
    p = Pista("Arpegio", bpm, canal=0)
    for i, g in enumerate(grados):
        n = triada(tonica, escala, g, octava=4, septima=True)
        cerrado = [n[0], n[1], n[2], n[3], n[2], n[1], n[2], n[0] + 12]
        abierto = [n[0], n[2], n[3], n[2] + 12, n[3], n[2], n[1], n[0] + 12]
        for c in (i * 2, i * 2 + 1):
            patron = abierto if c >= 4 else cerrado
            desplazamiento = 12 if c >= 4 else 0
            for k in range(16):
                if c >= 4 and k % 8 == 7:
                    continue             # un hueco por compas: deja respirar
                p.nota(c, h.pulso(k * 0.25), patron[k % len(patron)] + desplazamiento,
                       duracion=0.22,
                       velocidad=h.vel(92 if k % 4 == 0 else (74 if k % 2 == 0 else 60)))
    return p


def _bateria(bpm: float, h: Humano) -> Pista:
    """Kick en negras, clap en 2 y 4, hats con acentos, y fills cada 4 compases.

    Los fills y el kick que falta antes del compas 1 son lo que convierte ocho
    compases en una frase de ocho compases.
    """
    p = Pista("Bateria", bpm, canal=9)
    for c in range(COMPASES_LOOP):
        for pulso in range(4):
            # el ultimo kick del loop no suena: el hueco anticipa la vuelta
            if c == COMPASES_LOOP - 1 and pulso == 3:
                continue
            p.nota(c, pulso, KICK, 0.25, h.vel(110))
        for pulso in (1, 3):
            p.nota(c, h.pulso(pulso), CLAP, 0.25, h.vel(96))
        # Hat abierto en dos contratiempos, no en cuatro: cuatro por compas
        # satura y es lo que hace sonar arenoso al conjunto.
        for pulso in (0.5, 2.5):
            p.nota(c, h.pulso(pulso), OHH, 0.3, h.vel(70))
        # El movimiento de semicorcheas lo lleva el shaker, no el hat cerrado.
        # Es lo que hace la percusion del palo Cattaneo / Vuarambon: se siente
        # antes de escucharse.
        for k in range(16):
            if k % 4 == 0:
                continue                 # el pulso es del kick
            p.nota(c, h.pulso(k * 0.25), SHAKER, 0.10,
                   h.vel(52 if k % 2 == 0 else 42))
        # el hat cerrado queda como detalle, no como base
        for pulso in (1.75, 3.75):
            p.nota(c, h.pulso(pulso), CHH, 0.10, h.vel(52))
        # ride en la segunda mitad: sube la sensacion sin sumar volumen
        if c >= 4:
            for k in range(4):
                p.nota(c, h.pulso(k + 0.5), RIDE, 0.2, h.vel(52))
        # fills: chico en el compas 4, grande en el 8
        if c == 3:
            for k in (3.5, 3.75):
                p.nota(c, h.pulso(k), CLAP, 0.15, h.vel(80))
        if c == COMPASES_LOOP - 1:
            for k in (3.0, 3.25, 3.5, 3.75):
                p.nota(c, h.pulso(k), CLAP, 0.15, h.vel(70 + int((k - 3) * 60)))
            p.nota(c, 3.5, OHH, 0.4, h.vel(100))
    return p


# Celula ritmica de 2 compases (8 pulsos): (pulso, offset de grado, duracion).
# Notas cortas y sincopadas en vez de notas largas sostenidas. Una linea de
# blancas apiladas sobre acordes con septima y novena suena a himno; lo que hace
# moderno a un gancho de progressive es el ritmo, no la nota.
CELULA = [
    (0.0, 0, 0.45), (0.75, 0, 0.20), (1.5, -2, 0.45), (2.5, 0, 0.70),
    (4.0, 1, 0.45), (4.75, 0, 0.20), (6.0, -2, 1.10),
]
# Grado base de cada repeticion de 2 compases. La tercera sube a la tonica una
# octava arriba: ahi cae el pico, sin sostenerla cuatro tiempos.
BASES = [4, 5, 7, 4]


def _melodia(bpm: float, tonica: int, escala: list[int], h: Humano) -> Pista:
    """Gancho de 8 compases: una celula ritmica que se repite y transpone.

    Sin doblaje de octava: el doblaje es lo que engorda la linea y la vuelve
    coral. El ancho lo pone el delay en la mezcla, no una segunda voz.
    """
    p = Pista("Melodia", bpm, canal=0)
    for r, base in enumerate(BASES):
        for pulso_abs, offset, dur in CELULA:
            c, pulso = divmod(r * 8 + pulso_abs, 4)
            alt = grado(tonica, escala, base + offset, octava=5)
            # la nota larga de cada celula acentua; las cortas empujan
            p.nota(int(c), h.pulso(pulso), alt, dur,
                   h.vel(96 if dur > 0.6 else 78))
    return p


def _plano(plantilla: dict | None, camelot: str, bpm: float, registro: str,
           progresion_texto: str) -> str:
    """Plano de arreglo, con compases reales si hay plantilla medida."""
    if plantilla and plantilla.get("linea_tiempo"):
        total = int(plantilla["compases"])
        fuente = (f"derivado de {plantilla['n_tracks']} tracks medidos "
                  f"({plantilla.get('nombre', '?')})")
        objetivo = (f"{plantilla['lufs']} LUFS, rango {plantilla['rango_dinamico_db']} dB, "
                    f"{plantilla['duracion_min']} min")
        balance = "  ".join(f"{k} {v:.1f}%" for k, v in plantilla["balance"].items())
        ancho = "  ".join(f"{k} {v:.2f}" for k, v in plantilla["ancho"].items())
        filas = []
        for t in plantilla["linea_tiempo"]:
            desde = int(t["desde_pct"] / 100 * total) + 1
            hasta = int(t["hasta_pct"] / 100 * total)
            filas.append(f"| {t['tipo']:<11} | {desde:>3} - {hasta:<3} | "
                         f"{hasta - desde + 1:>5} | {t['acuerdo_pct']:>3}% |")
        cuerpo = "\n".join(filas)
    else:
        total, fuente = 200, "valores por defecto — sin plantilla medida"
        objetivo = "sin referencia"
        balance = ancho = "sin referencia"
        cuerpo = ("| intro       |   1 - 16  |    16 | n/a |\n"
                  "| groove      |  17 - 112 |    96 | n/a |\n"
                  "| breakdown   | 113 - 136 |    24 | n/a |\n"
                  "| drop        | 137 - 192 |    56 | n/a |\n"
                  "| outro       | 193 - 200 |     8 | n/a |")

    return f"""# Boceto — {nombre_tonalidad(camelot)} ({camelot}) a {bpm:.0f} BPM

Registro **{registro}**. {progresion_texto}

Plano {fuente}.

## Arreglo

Largo objetivo: **{total} compases** ({total * 4 / bpm:.1f} min a {bpm:.0f} BPM).

La forma sale de votar posicion a posicion sobre el corpus: cada track se
normaliza y cada compas vota que tipo de seccion es. La columna *acuerdo* dice
que porcentaje del corpus vota lo mismo — abajo del 50% la seccion es una
tendencia, no una regla.

| seccion | compases | largo | acuerdo |
|---|---|---|---|
{cuerpo}

## Objetivo de mezcla

- **{objetivo}**
- balance espectral: {balance}
- ancho estereo (1.00 = mono): {ancho}

El sub tiene que quedar en mono. Si baja de 0.85 se cancela en un sistema grande.

## Los clips

Loops de 8 compases — pero no ocho compases iguales. El bajo cambia en la
segunda mitad, el arpegio sube una octava y se abre, la bateria tiene fills en
el 4 y en el 8, y el ultimo kick del loop no suena para anticipar la vuelta.
Todo lleva swing y variacion de velocidad.

| archivo | que es | como usarlo |
|---|---|---|
| `01_acordes.mid` | pad sostenido + stabs en contratiempo + voz superior que camina | el color del track — filtrarlo en la intro y abrirlo en el drop |
| `02_bajo.mid` | bajo rodante en contratiempo, quinta en la segunda mitad, octava al cerrar | no toca el pulso: ese lugar es del kick |
| `03_arpegio.mid` | semicorcheas con swing; segunda mitad una octava arriba y con huecos | entra despues del primer breakdown, si no gasta el recurso |
| `04_bateria.mid` | kick, clap en 2 y 4, shaker en semicorcheas, hat abierto en dos contratiempos, ride en la segunda mitad, fills | drum rack: 36 kick, 39 clap, 42 hat cerrado, 46 abierto, 51 ride, 70 shaker |
| `05_melodia.mid` | frase de 8 compases doblada en octava, con el pico en el compas 5 | es el gancho: va en el breakdown y vuelve en el drop |

## Como se importa a Ableton

1. Abrir Live, poner el proyecto a **{bpm:.0f} BPM**.
2. Arrastrar cada `.mid` a una pista MIDI vacia. Live respeta el tempo del archivo.
3. Los clips quedan de 8 compases: duplicarlos siguiendo el plano de arriba.

## Lo que esto NO hace

Elegir los sonidos, que es donde se decide si el track existe. El esqueleto es
correcto y generico: el caracter sale del pad, del kick y de lo que se le haga a
la mezcla.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camelot", default="4A", help="tonalidad, ej 4A")
    ap.add_argument("--bpm", type=float, default=123.0)
    ap.add_argument("--registro", choices=sorted(PROGRESIONES), default="luminoso")
    ap.add_argument("--swing", type=float, default=SWING,
                    help="0 = cuantizado duro; 0.07 default; arriba de 0.15 ya es shuffle")
    ap.add_argument("--semilla", type=int, default=12)
    ap.add_argument("--plantilla", type=Path,
                    default=RAIZ / "data" / "plantillas" / "eze_arias.json")
    ap.add_argument("--nombre", default="")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    tonica, menor = tonica_de_camelot(args.camelot)
    escala = MENOR if menor else MAYOR
    grados, texto = PROGRESIONES[args.registro]
    h = Humano(args.semilla, args.swing)

    plantilla = None
    if args.plantilla and args.plantilla.exists():
        plantilla = json.loads(args.plantilla.read_text(encoding="utf-8"))

    nombre = args.nombre or f"{nombre_tonalidad(args.camelot)}_{args.registro}"
    destino = args.out or (RAIZ / "postproduction" / "bocetos" / nombre)
    destino.mkdir(parents=True, exist_ok=True)

    pistas = [
        ("01_acordes.mid", _acordes(args.bpm, tonica, escala, grados, h)),
        ("02_bajo.mid", _bajo(args.bpm, tonica, escala, grados, h)),
        ("03_arpegio.mid", _arpegio(args.bpm, tonica, escala, grados, h)),
        ("04_bateria.mid", _bateria(args.bpm, h)),
        ("05_melodia.mid", _melodia(args.bpm, tonica, escala, h)),
    ]
    for archivo, pista in pistas:
        pista.guardar(destino / archivo)

    (destino / "ARREGLO.md").write_text(
        _plano(plantilla, args.camelot, args.bpm, args.registro, texto),
        encoding="utf-8")

    print(f"\nBoceto {nombre_tonalidad(args.camelot)} ({args.camelot}) "
          f"a {args.bpm:.0f} BPM — registro {args.registro}, swing {args.swing}")
    print(f"{texto}\n")
    for archivo, _ in pistas:
        print(f"  {archivo}")
    print("  ARREGLO.md")
    print(f"\n-> {destino}")
    if not plantilla:
        print("\nSin plantilla medida: el plano usa valores por defecto. "
              "Correr scripts/derive_template.py para derivarla del corpus real.")


if __name__ == "__main__":
    main()
