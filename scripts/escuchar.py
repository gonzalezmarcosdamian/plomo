"""Traduce mediciones a lo que una persona va a decir cuando escuche.

Por que existe: el productor mide y no escucha. Reporta que el bajo cubre el 28%
del tiempo, y eso no le sirve a nadie hasta que alguien lo escucha y dice "suena
cortado". El costo de esa distancia se pago todo un dia: cada iteracion era
hacer escuchar algo, esperar una frase, y recien ahi buscar el numero que la
explicaba.

Esto invierte el orden. Cada umbral de aca salio de un caso real donde primero
vino la queja y despues aparecio la causa medida, asi que el instrumento esta
CALIBRADO contra un oido concreto — el de este DJ, sobre este genero.

No es escuchar. Es predecir la frase.

Lo que no puede hacer, y hay que decirlo: no juzga si una idea es buena. Un
boceto puede pasar los doce chequeos y no decir nada, que es exactamente lo que
paso el 2026-09-08. Esto detecta defectos, no ausencias.

Uso:
    python scripts/escuchar.py postproduction/bocetos/idea
    python scripts/escuchar.py <carpeta> --groove 12   # compas de referencia
"""
from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from plomo.midi import leer  # noqa: E402

# Capas donde el largo de la nota no cambia lo que se escucha: en un Drum Rack
# el sample se dispara entero.
#
# "hats" y "metales" se sumaron el 2026-09-19: son las mismas muestras del
# Drum Rack de bateria, solo que en su propia pista. hats sale literalmente de
# separar bateria en dos (`_hats()` en idea.py, "se escriben en la bateria
# como siempre y se separan despues"), y metales dispara la nota CHH del mismo
# kit ("AG Techno Kit" / "909 Core Kit" en set_v3.py, REMAPA en montar.py trata
# a las tres pistas igual). Sin esto, --tema es el unico camino que separa
# hats en su propio archivo y el chequeo de staccato las marcaba ALTO en las
# nueve secciones del tema completo — la misma alarma mal calibrada que ya
# describe docs/APRENDIZAJES.md ("Una alarma que avisa mal es peor que
# ninguna"), esta vez sobre una capa que --pleno/--climax/--tecno nunca habian
# probado porque nunca la escriben separada.
PERCUSIVAS = {"bateria", "percusion", "repiques", "subida", "hats", "metales"}
# Un racimo es dos ataques de capas distintas a menos de esto. Por debajo de
# 10 ms dos transientes agudos no se escuchan como flam sino como filtro de
# peine, y como la humanizacion los mueve al azar, la coloracion cambia compas
# a compas.
RACIMO_MS = 10.0
# Densidad de referencia, medida sobre los temas mas tocados: bombo + agudos +
# bajo. `data/arreglos_medidos.json`.
DENSIDAD_REF = 17.7
# Capas a las que no se les mide cobertura: no sostienen por diseño.
EFECTOS_Y_MELODIA = {"gancho", "solo", "cierre", "detalle", "melodia",
                     "arpegio", "riser", "voz", "subida", "lead"}
# Golpes sueltos: un platillo o un barrido que suena una vez cada ocho compases
# cubre el 6% del tiempo POR DISENIO, y decir que "puede sonar cortado" es
# gritar en falso. Un instrumento que avisa de lo que esta bien entrena a
# ignorarlo, que es peor que no avisar.
#
# La regla no es una lista de nombres sino una forma: menos de un golpe cada dos
# compases. Asi cubre cualquier capa de una sola vez que aparezca despues sin
# que haya que acordarse de agregarla aca.
GOLPES_SUELTOS_X_COMPAS = 0.5


class Dictamen:
    """Una frase que una persona diria, con el numero que la respalda."""

    def __init__(self) -> None:
        self.filas: list[tuple[str, str, str]] = []

    def agrega(self, gravedad: str, frase: str, dato: str) -> None:
        self.filas.append((gravedad, frase, dato))

    def imprime(self) -> None:
        if not self.filas:
            print("  Ninguno de los doce defectos conocidos. Eso NO quiere decir")
            print("  que suene bien: quiere decir que no tiene ninguno de los")
            print("  problemas que ya aprendimos a detectar.")
            return
        orden = {"ALTO": 0, "MEDIO": 1, "BAJO": 2}
        for g, frase, dato in sorted(self.filas, key=lambda x: orden[x[0]]):
            print(f"  [{g:5}] {frase}")
            print(f"          {dato}")


def _capas(carpeta: Path) -> dict[str, list]:
    fuera = {}
    for f in sorted(carpeta.glob("*.mid")):
        fuera[f.stem.split("_", 1)[-1].lower()] = leer(f)[2]
    return fuera


def _cobertura(notas: list) -> tuple[float, float]:
    """Fraccion del tiempo cubierta y duracion mediana, en pulsos."""
    if not notas:
        return 0.0, 0.0
    fin = max(n[0] + n[1] for n in notas)
    paso = 1 / 16
    ocupado = set()
    for inicio, dur, _, _ in notas:
        a, b = int(inicio / paso), int((inicio + dur) / paso)
        ocupado.update(range(a, max(a + 1, b)))
    return len(ocupado) / max(1, int(fin / paso)), statistics.median(n[1] for n in notas)


def revisa_cortado(capas: dict, d: Dictamen) -> None:
    """"suena cortado" — una capa melodica que no llega a sostener.

    Calibrado el 2026-09-08: el bajo cubria el 28% del tiempo contra el 71% de
    los temas de referencia, y esa fue exactamente la queja.
    """
    # Si hay una capa que sostiene por debajo, los golpes cortos de arriba NO
    # son un defecto: son la forma de que la armonia no suene a organo. Se juzga
    # el rol completo, no cada capa suelta.
    piso = max((_cobertura(n)[0] for cap, n in capas.items()
                if cap in ("atmosfera", "pad") and n), default=0.0)
    for nombre, notas in capas.items():
        if nombre in PERCUSIVAS or not notas:
            continue
        if nombre in ("acordes", "pad") and piso > 0.90:
            continue
        cob, dur = _cobertura(notas)
        # Staccato es RELATIVO al hueco, no absoluto.
        #
        # El umbral de 0.25 estaba pensado para una linea melodica, donde las
        # notas estan lejos. En un arpegio de semicorcheas el hueco entre nota y
        # nota ES 0.25, asi que una nota de 0.22 llena el 88% de su lugar y suena
        # casi legato. Medirla contra el absoluto la marcaba como click, que es
        # justo al reves de lo que pasa.
        arranques = sorted(n[0] for n in notas)
        huecos = [b - a for a, b in zip(arranques, arranques[1:]) if b > a]
        hueco = statistics.median(huecos) if huecos else 1.0
        llenado = dur / hueco if hueco else 1.0
        if llenado < 0.45 and dur < 0.4:
            d.agrega("ALTO", f"el/la {nombre} va a sonar a staccato",
                     f"cada nota dura {dur:.2f} pulsos y llena el {llenado:.0%} "
                     f"del hueco hasta la siguiente; abajo del 45% se escucha "
                     f"el silencio entre nota y nota")
        # Los efectos y las melodias no sostienen por definicion: un riser
        # dispara nueve veces en todo el tema y un gancho existe entre
        # silencios. Medirles cobertura seria medirles el arreglo.
        elif (cob < 0.55 and nombre not in EFECTOS_Y_MELODIA
              and len(notas) >= GOLPES_SUELTOS_X_COMPAS
              * (max(arranques) / 4 + 1)):
            d.agrega("MEDIO", f"el/la {nombre} puede sonar cortado",
                     f"cubre {cob:.0%} del tiempo; las referencias cubren 71-84%")


def revisa_huecos(capas: dict, d: Dictamen) -> None:
    """"se corta el fondo" — re-ataques sobre nota sonando.

    Escribir la misma altura solapada NO la sostiene: el stream queda
    `on, on, off, off` y el primer note-off apaga la nota. Costo real: una capa
    que se creia sostenida sonaba el 41% del tiempo, con cinco huecos de 7.5 s.
    """
    for nombre, notas in capas.items():
        por_altura: dict[int, list[tuple[float, float]]] = defaultdict(list)
        for inicio, dur, altura, _ in notas:
            por_altura[altura].append((inicio, inicio + dur))
        solapes = 0
        for tramos in por_altura.values():
            tramos.sort()
            solapes += sum(1 for a, b in zip(tramos, tramos[1:]) if b[0] < a[1] - 1e-6)
        if solapes:
            d.agrega("ALTO", f"el/la {nombre} tiene notas que se apagan solas",
                     f"{solapes} re-ataques sobre una altura que ya estaba "
                     f"sonando; el primer note-off mata a los dos")


# Notas del drum rack que cuentan como "agudos" en la referencia medida.
AGUDOS_REF = {42, 46, 51, 70, 63, 64}
KICK_REF = 36


def revisa_denso(capas: dict, compases: int, d: Dictamen) -> None:
    """"esta super denso" — mas eventos de los que el genero aguanta.

    Se cuenta lo MISMO que cuenta la referencia: bombo, elementos agudos de la
    percusion, y bajo. Los 17.7 de `arreglos_medidos.json` salen de eso y de
    nada mas — la armonia no entra porque el stem `other` mezcla pad, arpegio y
    lead y de ahi solo se saca el acorde, y el clap tampoco porque esa metrica
    salio rota.

    Sumar todo contra ese numero seria comparar de un lado lo que del otro no se
    conto, y hacer sonar la alarma por una diferencia que no existe.
    """
    total = 0
    for cap, notas in capas.items():
        if cap == "bajo":
            total += len(notas)
        elif cap in PERCUSIVAS:
            total += sum(1 for n in notas
                         if n[2] == KICK_REF or n[2] in AGUDOS_REF)
    por_compas = total / max(1, compases)
    if por_compas > 30:
        d.agrega("ALTO", "va a sonar denso, o directamente cargado",
                 f"{por_compas:.1f} notas por compas contando bombo, agudos y "
                 f"bajo; la mediana medida de los temas mas tocados es "
                 f"{DENSIDAD_REF}")
    elif por_compas > 25:
        d.agrega("MEDIO", "esta en el limite de lo denso",
                 f"{por_compas:.1f} notas por compas contra {DENSIDAD_REF} medido")


def revisa_robot(capas: dict, compases: int, d: Dictamen) -> None:
    """"suena a robot" — compases identicos al de 8 atras, POR CAPA.

    Estaba roto por agregacion y es el error mas caro del instrumento. La
    version anterior armaba UNA firma por compas con la union de todas las
    capas: como el gancho y los acordes si varian, la firma del compas siempre
    cambiaba, y trece capas repitiendo verbatim sesenta compases pasaban
    invisibles. El umbral del 30% no se disparaba nunca.

    Medido sobre el drop de la v3 con la version por capa: subkick 100%,
    repiques 96%, bateria 94%, hats 94%. El DJ venia diciendo "parece un
    ringtone" y el chequeo que existia para decir eso no lo decia.

    Y ojo con el periodo: una variacion que se repite cada 2 compases es
    invisible contra una celula de 8, porque 2 divide a 8.
    """
    peor, culpable = 0.0, ""
    detalle = []
    for nombre, notas in capas.items():
        if nombre in ("riser", "subida", "voz", "reversa", "splash", "cierre"):
            continue
        firma: dict[int, set] = defaultdict(set)
        for inicio, _, altura, _ in notas:
            firma[int(inicio // 4)].add((round(inicio % 4, 3), altura))
        con_notas = [c for c in range(compases) if firma.get(c)]
        if len(con_notas) < 16:
            continue
        iguales = sum(1 for c in range(8, compases)
                      if firma.get(c) and firma.get(c) == firma.get(c - 8))
        frac = iguales / max(1, compases - 8)
        detalle.append((frac, nombre))
        if frac > peor:
            peor, culpable = frac, nombre
    if peor > 0.60:
        otras = ", ".join(f"{n} {f:.0%}" for f, n in sorted(detalle, reverse=True)[1:4])
        d.agrega("ALTO", "va a sonar a maquina",
                 f"la capa {culpable} repite identica el {peor:.0%} de los compases "
                 f"(cada 8); tambien {otras}")
    elif peor > 0.35:
        d.agrega("MEDIO", "puede sonar repetitivo",
                 f"la capa {culpable} repite identica el {peor:.0%} de los compases")


# Notas del drum rack que viven arriba de 1 kHz. El peine solo importa entre
# transientes que comparten banda: un bajo cerca del bombo es normal y deseable
# —es el entrelazado del genero— y marcarlo seria la alarma que despues hay que
# aprender a ignorar.
AGUDOS = {37, 39, 42, 46, 51, 63, 64, 70}


def revisa_destiempo(capas: dict, d: Dictamen) -> None:
    """"a destiempo" y "arenoso" — dos transientes agudos en la misma semicorchea.

    No es que las notas esten mal puestas: dos ataques de banda ancha aguda
    separados por 1 a 9 ms dan filtro de peine —la primera muesca cerca de
    100 Hz, repitiendose cada 200— y como la humanizacion los mueve al azar la
    coloracion cambia compas a compas. Se escucha como suciedad y como desfase
    al mismo tiempo, que parece contradictorio y no lo es.

    Se mira POR ALTURA y no por capa: el problema real fue entre el hat cerrado
    y el shaker, que viven los dos adentro del clip de bateria.
    """
    eventos: list[tuple[float, str]] = []
    for nombre, notas in capas.items():
        # Solo capas percusivas: en un clip melodico el MIDI 64 es un mi, no una
        # conga. Las dos numeraciones comparten el rango y confundirlas hacia
        # que un acorde apareciera como choque de percusion.
        if nombre not in PERCUSIVAS:
            continue
        for inicio, _, altura, _ in notas:
            if altura not in AGUDOS:
                continue
            eventos.append((inicio, f"{nombre}:{altura}"))
    eventos.sort()
    ms_por_pulso = 60_000 / 121 / 1        # aproximado: alcanza para el umbral
    racimos = Counter()
    for (t1, c1), (t2, c2) in zip(eventos, eventos[1:]):
        if c1 == c2:
            continue
        if 0 < (t2 - t1) * ms_por_pulso < RACIMO_MS:
            racimos[tuple(sorted((c1, c2)))] += 1
    for (a, b), n in racimos.most_common(3):
        if n >= 10:
            d.agrega("ALTO", f"{a} y {b} se van a escuchar sucios y corridos",
                     f"{n} veces caen a menos de {RACIMO_MS:.0f} ms una de otra; "
                     f"eso es filtro de peine, no flam")


def revisa_brusco(capas: dict, compases: int, d: Dictamen) -> None:
    """"es brusco" — un cambio sin nada que lo prepare."""
    peso = defaultdict(int)
    for notas in capas.values():
        for inicio, _, _, vel in notas:
            peso[int(inicio // 4)] += vel
    con_algo = [v for v in peso.values() if v > 200]
    mediana = statistics.median(con_algo) if con_algo else 0
    peor, donde = 0.0, 0
    for c in range(compases - 1):
        # los dos compases tienen que existir de verdad: contra el vacio del
        # final todo salto da -100% y no significa nada
        # Los dos compases tienen que existir de verdad —contra el vacio del
        # final todo salto da -100%— y ademas tiene que haber algo sonando: un
        # +77% en una intro donde el nivel absoluto es bajo no se escucha como
        # corte, y marcarlo entrena a ignorar la alarma.
        if peso[c] < 200 or peso[c + 1] < 800:
            continue
        # Un salto que sale de un agujero DELIBERADO no es un corte: es el
        # pago. Si el compas anterior pesa menos de la mitad de la mediana del
        # tema, lo que hay antes es un vacio escrito a proposito —la tension de
        # Moonflare es exactamente eso— y marcarlo entrena a ignorar la alarma.
        if peso[c] < mediana * 0.5:
            continue
        salto = (peso[c + 1] - peso[c]) / peso[c]
        if abs(salto) > abs(peor):
            peor, donde = salto, c + 1
    if abs(peor) > 0.60:
        d.agrega("MEDIO", f"el cambio del compas {donde} al {donde + 1} se va a "
                 f"escuchar como un corte",
                 f"el peso salta {peor:+.0%}; arriba de 60% sin rampa el oido "
                 f"lo lee como interruptor")


def revisa_fino(capas: dict, d: Dictamen) -> None:
    """"muy fina la melodia" — la voz mas aguda es la mas floja.

    El techo de la textura lo tiene que poner la voz que lleva la linea. Cuando
    lo pone una voz de color, se escucha fino aunque la melodia este bien.
    """
    for nombre in ("gancho", "detalle", "melodia", "solo", "cierre"):
        notas = capas.get(nombre)
        if not notas:
            continue
        techo = max(n[2] for n in notas)
        vel_techo = max(n[3] for n in notas if n[2] == techo)
        vel_max = max(n[3] for n in notas)
        if techo > 85 and vel_techo < vel_max - 20:
            d.agrega("MEDIO", f"el/la {nombre} va a sonar fino",
                     f"la nota mas aguda es MIDI {techo} con velocidad "
                     f"{vel_techo}, y la mas fuerte del tema tiene {vel_max}: "
                     f"el techo lo pone la voz de color, no la melodia")


def revisa_iglesia(capas: dict, d: Dictamen) -> None:
    """"suena a iglesia" — triada sostenida.

    No es la septima ni el registro: es la duracion. El mismo acorde en golpes
    cortos en el contratiempo suena a progressive.
    """
    for nombre in ("acordes", "atmosfera", "pad"):
        notas = capas.get(nombre)
        if not notas:
            continue
        juntas = defaultdict(list)
        for inicio, dur, altura, _ in notas:
            juntas[round(inicio, 2)].append(dur)
        largas = [t for t, durs in juntas.items() if len(durs) >= 3 and min(durs) > 8]
        if largas and nombre == "acordes":
            d.agrega("MEDIO", f"el/la {nombre} puede sonar a organo de iglesia",
                     f"{len(largas)} acordes de 3+ notas sostenidos mas de 8 "
                     f"pulsos; lo que lo causa es la duracion, no la armonia")


def revisa_barro(capas: dict, d: Dictamen) -> None:
    """"embarrado" — tres capas melodicas en la misma banda grave.

    Entre 82 y 247 Hz —MIDI 40 a 59— viven el bajo, el pedal del pad y el cuarto
    armonico del bombo. Tres voces sostenidas ahi es donde un progressive se
    ensucia.

    "textura" (`_textura()` en idea.py) queda afuera: es una nota atada de
    principio a fin de la seccion en un MIDI fijo (48), pero el propio
    docstring de esa funcion dice que del otro lado hay "un sonido sin altura
    definida" — un piso de ruido, no una voz armonica. Contarla mide siempre
    3+ capas apenas hay otras dos voces sosteniendo debajo de 60, sin que
    aporte nada a un embarre real de armonia. Medido en _check_011 (vuelta
    011, semilla 7): sacarla baja pleno1/pleno2 de 82% a 29% y salida_dj de
    79% a 21% — las tres caen debajo del umbral de 40% y la alarma, que
    estaba mal calibrada, deja de sonar. drop queda en 71% (bajo, bajo2, sub
    y atmosfera sostenidos ahi de verdad) y sigue sonando: ese es un embarre
    real, no el bug.
    """
    BANDA = range(40, 60)
    SIN_ALTURA = {"textura"}
    ocupacion = defaultdict(set)
    for nombre, notas in capas.items():
        if nombre in PERCUSIVAS or nombre in SIN_ALTURA:
            continue
        for inicio, dur, altura, _ in notas:
            if altura in BANDA:
                for k in range(int(inicio * 4), max(int(inicio * 4) + 1,
                                                    int((inicio + dur) * 4))):
                    ocupacion[k].add(nombre)
    if not ocupacion:
        return
    apilado = sum(1 for caps in ocupacion.values() if len(caps) >= 3)
    frac = apilado / len(ocupacion)
    if frac > 0.40:
        quienes = Counter(c for caps in ocupacion.values() if len(caps) >= 3
                          for c in caps)
        d.agrega("MEDIO", "la banda grave se va a embarrar",
                 f"{frac:.0%} del tiempo hay 3+ capas melodicas entre 82 y "
                 f"247 Hz: {', '.join(k for k, _ in quienes.most_common(4))}")


def revisa_vacio(capas: dict, compases: int, d: Dictamen) -> None:
    """"esta vacio" — tramos con muy pocas capas sonando."""
    activas = defaultdict(set)
    for nombre, notas in capas.items():
        for inicio, dur, _, _ in notas:
            for c in range(int(inicio // 4), int((inicio + dur) // 4) + 1):
                activas[c].add(nombre)
    flacos = [c for c in range(compases) if len(activas.get(c, ())) <= 2]
    if len(flacos) > compases * 0.25:
        d.agrega("MEDIO", "va a haber tramos que suenen vacios",
                 f"{len(flacos)} de {compases} compases con 2 capas o menos; "
                 f"lo que falta ahi no son eventos sino algo que dure entre "
                 f"evento y evento")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta", type=Path)
    ap.add_argument("--compases", type=int, help="largo; se deduce si no se pasa")
    args = ap.parse_args()

    if not args.carpeta.exists():
        sys.exit(f"no existe {args.carpeta}")
    capas = _capas(args.carpeta)
    if not capas:
        sys.exit(f"no hay .mid en {args.carpeta}")

    fin = max(n[0] + n[1] for notas in capas.values() for n in notas)
    compases = args.compases or int(fin // 4) + 1

    print(f"\n  {args.carpeta.name} — {len(capas)} capas, {compases} compases\n")
    print(f"  {'capa':<12} {'notas':>6} {'x compas':>9} {'cobertura':>10} {'dur med':>9}")
    for nombre, notas in capas.items():
        cob, dur = _cobertura(notas)
        marca = "  (percusiva)" if nombre in PERCUSIVAS else ""
        print(f"  {nombre:<12} {len(notas):6d} {len(notas)/compases:9.1f} "
              f"{cob:9.0%} {dur:8.2f}p{marca}")

    print(f"\n  LO QUE UNA PERSONA VA A DECIR\n")
    d = Dictamen()
    revisa_cortado(capas, d)
    revisa_huecos(capas, d)
    revisa_denso(capas, compases, d)
    revisa_robot(capas, compases, d)
    revisa_destiempo(capas, d)
    revisa_brusco(capas, compases, d)
    revisa_fino(capas, d)
    revisa_iglesia(capas, d)
    revisa_barro(capas, d)
    revisa_vacio(capas, compases, d)
    d.imprime()
    print()


if __name__ == "__main__":
    main()
