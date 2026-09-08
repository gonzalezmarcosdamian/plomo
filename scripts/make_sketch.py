"""Genera un boceto de track: clips MIDI + plano de arreglo, listos para Ableton.

No compone: arma el esqueleto. Armonia, bajo rodante, bateria y un gancho corto
en la tonalidad y el BPM que se le pidan, mas un plano de arreglo con los
compases reales derivados de un corpus medido (`scripts/derive_template.py`).

La musica la hace uno; esto ahorra los cuarenta minutos de poner la grilla,
elegir la tonalidad y decidir en que compas va el breakdown.

La densidad no es una opinion: sale de `scripts/medir_arreglos.py`, que separa
en stems y transcribe los temas mas tocados de la propia historia de Rekordbox.
La mediana de esos temas es 17.7 notas por compas. La version anterior de este
script escribia 44 repartidas en cinco capas que sonaban las ocho compases
enteras — un arpegio de semicorcheas que no paraba nunca, un pad con septima
sostenido, una melodia y stabs, todo a la vez. Eso no se escucha como una idea
musical: se escucha como una maquina, y no era el timing sino la falta de aire.

Cuatro capas, y no todas suenan todo el tiempo. Al final imprime la densidad
generada al lado de la medida, que es el numero que costo dos iteraciones ver.

Uso:
    python scripts/make_sketch.py --camelot 4A --bpm 123
    python scripts/make_sketch.py --camelot 8A --registro oscuro
    python scripts/make_sketch.py --camelot 4A --registro heroico
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
# Se usan los tres primeros grados: 4 compases el primero, 2 y 2 los otros. Son
# dos cambios cada ocho compases, que es la mediana medida.
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
KICK, CLAP, CHH, OHH, RIDE, SHAKER, RIM = 36, 39, 42, 46, 51, 70, 37

# Cuanto se corre la contratiempo de semicorchea. 0 = cuantizado duro, y es el
# default: el swing nunca fue el problema —el jitter maximo son 6 ms— pero
# tampoco hay nada medido que lo justifique, y todo lo que no esta medido y no
# se escucha no deberia estar prendido.
SWING = 0.0
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


def _objetivos() -> dict | None:
    """Las medianas medidas sobre los temas mas tocados, si existen."""
    ruta = RAIZ / "data" / "arreglos_medidos.json"
    if not ruta.exists():
        return None
    return json.loads(ruta.read_text(encoding="utf-8")).get("mediana")


def _acordes(bpm: float, tonica: int, escala: list[int], grados: list[int],
             h: Humano) -> Pista:
    """Tres acordes en ocho compases —4 + 2 + 2— pero pulsando, no sostenidos.

    La armonia sigue siendo la misma; lo que cambia es que no se mantiene. Una
    triada sostenida cuatro compases con reverb larga suena a organo de iglesia,
    y no es la septima ni el registro: es la duracion. El mismo acorde en golpes
    cortos suena a progressive.

    Queda una nota larga por acorde —la fundamental sola, abajo— para que el
    fondo no se corte entre golpe y golpe. Una nota no arma un acorde, asi que
    no reconstruye el problema.
    """
    p = Pista("Acordes", bpm, canal=0)
    for compas, largo, g in ((0, 4, grados[0]), (4, 2, grados[1]), (6, 2, grados[2])):
        notas = triada(tonica, escala, g, octava=3, septima=False)
        p.nota(compas, 0, notas[0], duracion=largo * 4 - 0.5, velocidad=44)
        # golpes en el contratiempo, solo tercera y quinta: la fundamental ya
        # esta sonando abajo y repetirla engorda el golpe sin sumar nada
        for c in range(compas, compas + largo):
            for pulso in (1.5, 3.5):
                p.acorde(c, pulso, notas[1:], duracion=0.30,
                         velocidad=h.vel(66 if pulso == 1.5 else 58))
    return p


# Celula de bajo de 2 compases: (pulso absoluto sobre 8, offset de altura).
#
# Las posiciones salen de la medicion, no del gusto. Sobre los seis temas
# medidos con bajo audible: 10% de las notas cae en el pulso, 35% en el
# contratiempo de corchea y el 55% restante en semicorcheas. Esta celula da
# 14 / 29 / 57, que es lo mas cerca que se llega con siete notas.
#
# La version anterior ponia las cuatro notas en el contratiempo y nada mas:
# 0% en el pulso y 100% en contratiempo. Sonaba a marcha porque lo era — el
# bajo real rueda, no marca.
CELULA_BAJO = [
    (0.00, 0), (0.75, 0), (1.50, 0), (2.75, 7),
    (4.75, 0), (5.50, 0), (7.25, 12),
]


def _bajo(bpm: float, tonica: int, escala: list[int], grados: list[int],
          h: Humano) -> Pista:
    """Bajo rodante, 3.5 notas por compas.

    Tres alturas distintas: fundamental, quinta y octava. La mediana medida es
    3.5 alturas distintas — un bajo hipnotico ancla, pero no repite una sola
    nota durante ocho compases.
    """
    p = Pista("Bajo", bpm, canal=0)
    for repeticion, g in enumerate((grados[0], grados[0], grados[1], grados[2])):
        raiz = grado(tonica, escala, g, octava=1)
        for k, (pulso_abs, offset) in enumerate(CELULA_BAJO):
            c, pulso = divmod(repeticion * 8 + pulso_abs, 4)
            # La duracion sale del hueco hasta la nota siguiente, no de una
            # constante. Con 0.30 fijo el bajo cubria el 28% del tiempo y los
            # temas de referencia cubren el 71% (medido con
            # `scripts/continuidad.py` sobre los stems): eso es lo que se
            # escuchaba como cortado. Con el 78% del hueco las notas casi se
            # tocan sin llegar a pisarse, y el bajo pasa a ser una linea en vez
            # de una serie de golpes.
            siguiente = (CELULA_BAJO[k + 1][0] if k + 1 < len(CELULA_BAJO)
                         else CELULA_BAJO[0][0] + 8)
            dur = max(0.25, (siguiente - pulso_abs) * 0.66)
            vel = 104 if pulso == 0 else (86 if pulso % 1 == 0.5 else 78)
            p.nota(int(c), pulso, raiz + offset, duracion=dur, velocidad=h.vel(vel))
    return p


def _bateria(bpm: float, h: Humano) -> Pista:
    """Cuatro por cuatro, con unas diez notas agudas por compas.

    La mediana medida de elementos arriba de 6 kHz —hats, shaker, ride juntos—
    es 10.1 por compas. Ni cuatro ni dieciseis: el hat cerrado en semicorcheas
    constantes da 16 y es lo que se escucha como arena.

    El bombo NO lleva jitter. La variacion va por ausencia: el ultimo bombo del
    loop no suena, y ese hueco es lo que anuncia la vuelta.
    """
    p = Pista("Bateria", bpm, canal=9)
    for c in range(COMPASES_LOOP):
        for pulso in range(4):
            if c == COMPASES_LOOP - 1 and pulso == 3:
                continue
            p.nota(c, pulso, KICK, 0.25, 108)
        for pulso in (1, 3):
            p.nota(c, pulso, CLAP, 0.25, h.vel(92))
        # El abierto SOLO en dos contratiempos, no en cuatro. Es el elemento mas
        # brillante de la bateria: cuatro por compas es lo que empuja la energia
        # arriba de 6 kHz, y medido sobre los stems de Ezequiel Arias ahi vive
        # apenas el 3.8% de su energia. Con dos se mantiene el contratiempo y se
        # baja el brillo a la mitad.
        for pulso in (0.5, 2.5):
            p.nota(c, h.pulso(pulso), OHH, 0.20, h.vel(58))
        # El cerrado lleva el movimiento, que es lo que el abierto dejo de hacer.
        # Total: 8 agudos por compas, que es la mediana medida de Eze Arias
        # (8.05 sobre tres temas). La mediana general del repertorio es 10.12 —
        # se va a la de el a proposito, porque es el sonido que se pidio.
        cerrados = [0.25, 0.75, 1.75, 2.25, 2.75, 3.75]
        for pulso in cerrados:
            p.nota(c, h.pulso(pulso), CHH, 0.10, h.vel(48 if c < 4 else 54))
    return p


# Motivo corto: (pulso absoluto sobre 8, grado relativo, duracion).
# Siete notas en cuatro compases. Reemplaza al arpegio de semicorcheas, que
# metia 15 notas por compas sin un hueco y era la mayor fuente de ruido del
# boceto: un arpegio de septima que no para nunca no es un gancho, es un zumbido.
MOTIVO = [
    (0.0, 4, 0.70), (1.5, 2, 0.35), (2.5, 4, 0.90),
    (4.0, 5, 0.70), (5.5, 4, 0.35), (6.5, 2, 1.20),
]


def _detalle(bpm: float, tonica: int, escala: list[int], h: Humano) -> Pista:
    """Gancho de dos notas por compas, y solo en la segunda mitad del loop.

    Entra en el compas 5. Que aparezca un elemento a mitad de camino es lo que
    convierte ocho compases en una frase; ocho compases con los mismos cinco
    elementos sonando es lo que se escucha como una maquina.
    """
    p = Pista("Detalle", bpm, canal=0)
    for repeticion in range(2):
        for pulso_abs, g, dur in MOTIVO:
            # Cada nota del motivo abre un gesto de tres, separadas por corchea
            # con puntillo (0.75 de pulso = 3/16). Las alturas de la melodia son
            # las mismas —lo que gustaba se conserva— pero suenan arpegiadas en
            # vez de sostenidas: una nota larga se percibe como atmosfera, tres
            # cortas como melodia.
            #
            # El 3/16 no es arbitrario: es la misma division del delay del
            # gancho, asi que el arpegio y sus repeticiones se entrelazan en vez
            # de embarrarse.
            for k, salto in enumerate((0, 2, 4) if dur > 0.6 else (0, 2)):
                # 16 y no 4: `pulso_abs` viene en PULSOS, asi que sumar 4
                # corria el motivo un compas en vez de cuatro. El gancho decia
                # entrar en el compas 5 y entraba en el 2, reventaba en el 3 y
                # callaba en 6-7-8 — justo al reves de lo que dice el docstring,
                # y con las dos repeticiones pisandose entre si.
                arranque = 16 + repeticion * 16 + pulso_abs + k * 0.75
                c, pulso = divmod(arranque, 4)
                if c >= COMPASES_LOOP:
                    continue
                # 0.34 y no 0.18: a 123 BPM una nota de 0.18 pulsos dura 88 ms
                # y eso es un click, no una nota. Con 0.34 las tres del gesto se
                # encadenan y suena a arpegio en vez de a tres golpes sueltos.
                p.nota(int(c), h.pulso(pulso),
                       grado(tonica, escala, g + salto, octava=4),
                       0.34, h.vel(86 - k * 12))
    return p


def _atmosfera(bpm: float, tonica: int, escala: list[int],
               grados: list[int], h: Humano) -> Pista:
    """Pedal grave sostenido: raiz y quinta, sin tercera.

    Es la capa que hace que un tema no tenga huecos. En progressive casi siempre
    hay algo sonando abajo aunque no se lo escuche como un instrumento — se nota
    cuando falta, no cuando esta. Sin tercera a proposito: la tercera define el
    acorde y pelearia con el pad; la quinta no dice nada armonico y solo llena.

    Velocidad baja: esto no se escucha, se apoya.
    """
    p = Pista("Atmosfera", bpm, canal=0)
    for compas, largo, g in ((0, 4, grados[0]), (4, 2, grados[1]), (6, 2, grados[2])):
        raiz = grado(tonica, escala, g, octava=2)
        p.acorde(compas=compas, pulso=0, alturas=[raiz, raiz + 7],
                 duracion=largo * 4 - 0.25, velocidad=42)
    return p


def _percusion(bpm: float, h: Humano) -> Pista:
    """Shaker y madera, corriendo casi siempre.

    Es lo que separa organic house de progressive a secas, y ademas es lo que
    permite que una seccion se quede sin bateria sin quedarse sin nada: la
    percusion puede seguir cuando el bombo se va.

    Va en un kit aparte para no pisar la base.
    """
    p = Pista("Percusion", bpm, canal=9)
    for c in range(COMPASES_LOOP):
        # shaker en las semicorcheas de atras de cada pulso: empuja sin marcar
        for k in (0.75, 1.75, 2.75, 3.75):
            p.nota(c, k, SHAKER, 0.08, h.vel(40 if c % 2 else 46))
        # Click cada dos compases, corrido: es el detalle que hace que ocho
        # compases no suenen a uno repetido ocho veces. Va en 37 (rim) y no en
        # 51 (ride): el 51 cae en un tom o en un platillo segun el kit, y en un
        # kit acustico eso suena a timbal contra material electronico.
        if c % 2 == 1:
            p.nota(c, 1.25, RIM, 0.08, h.vel(50))
            p.nota(c, 3.5, RIM, 0.08, h.vel(42))
    return p


def _densidad(pistas: list[tuple[str, Pista]], objetivos: dict | None) -> str:
    """Compara lo generado contra lo medido, comparando lo mismo contra lo mismo.

    Existe porque el defecto que costo dos iteraciones encontrar no se veia
    escuchando ni leyendo el codigo: eran 44 notas por compas contra las 17.7 de
    los temas que se tocan. Un numero al lado del otro lo habria mostrado solo.

    La comparacion es sobre bombo + agudos + bajo, y nada mas. La mediana medida
    no incluye armonia —el stem `other` mezcla pad, arpegio y lead, y de ahi solo
    se saca el acorde, no la densidad— ni claps, porque esa metrica salio rota
    (daba 5 a 14 por compas donde un clap en house son 2). Comparar el total
    generado contra ese numero seria hacer ver bien el resultado sumando de un
    lado lo que del otro no se conto.
    """
    filas, comparable = [], 0.0
    for archivo, pista in pistas:
        encendidas = [e for e in pista._eventos if e.datos[0] & 0xF0 == 0x90]
        n = len(encendidas)
        detalle = ""
        if pista.nombre == "Bateria":
            c_kick = sum(1 for e in encendidas if e.datos[1] == KICK)
            c_clap = sum(1 for e in encendidas if e.datos[1] == CLAP)
            c_agudos = n - c_kick - c_clap
            detalle = (f"  (bombo {c_kick / COMPASES_LOOP:.1f}, "
                       f"clap {c_clap / COMPASES_LOOP:.1f}, "
                       f"agudos {c_agudos / COMPASES_LOOP:.1f})")
            comparable += (c_kick + c_agudos) / COMPASES_LOOP
        elif pista.nombre == "Bajo":
            comparable += n / COMPASES_LOOP
        filas.append(f"  {pista.nombre:9} {n / COMPASES_LOOP:5.1f} por compas{detalle}")

    filas.append("")
    filas.append(f"  comparable: bombo + agudos + bajo   {comparable:5.1f} por compas")
    if objetivos:
        medido = (objetivos["kick_x_compas"] + objetivos["hat_x_compas"]
                  + objetivos["bajo_x_compas"])
        filas.append(f"  lo mismo en los temas mas tocados   {medido:5.1f} por compas")
    return chr(10).join(filas)


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

    objetivos = _objetivos()
    plantilla = None
    if args.plantilla and args.plantilla.exists():
        plantilla = json.loads(args.plantilla.read_text(encoding="utf-8"))

    nombre = args.nombre or f"{nombre_tonalidad(args.camelot)}_{args.registro}"
    destino = args.out or (RAIZ / "postproduction" / "bocetos" / nombre)
    destino.mkdir(parents=True, exist_ok=True)

    pistas = [
        ("01_acordes.mid", _acordes(args.bpm, tonica, escala, grados, h)),
        ("02_bajo.mid", _bajo(args.bpm, tonica, escala, grados, h)),
        ("03_bateria.mid", _bateria(args.bpm, h)),
        ("04_detalle.mid", _detalle(args.bpm, tonica, escala, h)),
        ("05_atmosfera.mid", _atmosfera(args.bpm, tonica, escala, grados, h)),
        ("06_percusion.mid", _percusion(args.bpm, h)),
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
    print()
    print(_densidad(pistas, objetivos))
    print(f"\n-> {destino}")
    if not plantilla:
        print("\nSin plantilla medida: el plano usa valores por defecto. "
              "Correr scripts/derive_template.py para derivarla del corpus real.")


if __name__ == "__main__":
    main()
