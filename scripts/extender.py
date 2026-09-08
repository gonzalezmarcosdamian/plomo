"""Expande un loop de 8 compases a un tema con secciones, y lo manda a Live.

Por que existe: el loop ya funciona, pero un loop no es un tema. Lo que separa a
los dos no son mas notas: es que las mismas notas entren y salgan. Un drop no se
escucha como drop porque tenga mas cosas, sino porque antes hubo dieciseis
compases sin bombo — la energia es un contraste, no un nivel.

Por eso esto no compone nada nuevo. Toma la celula de 8 compases y decide, para
cada seccion, que capas suenan y con cuanta intensidad. Es como se arma el
genero de verdad y es lo que hace `make_sketch.py` en el papel de ARREGLO.md,
pero acá queda en MIDI y se escucha.

Uso:
    python scripts/extender.py postproduction/bocetos/boceto_medido --bpm 123
    python scripts/extender.py <carpeta> --repiques <carpeta>/02_repiques.mid
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from plomo.midi import Pista, leer  # noqa: E402

CELULA = 8          # compases del loop de origen
KICK, CLAP, OHH, RIM = 36, 39, 46, 37

# (nombre, compases, capas, intensidad)
#
# `capas` es que suena. `intensidad` mueve la velocidad: por debajo de 1 la
# seccion se siente contenida sin que haya que reescribirla.
#
# El breakdown de 16 compases sin bateria es la pieza central del arreglo. Es
# larga a proposito: si dura cuatro compases no es un breakdown, es un hueco, y
# el drop que viene despues no tiene contra que contrastar.
# La estructura no es una propuesta: sale de medir 41 temas de los mas tocados
# (`data/recetas/`). La plantilla es 240 compases con un breakdown de 32 que
# arranca en el compas 120 — la mitad exacta del tema. Y no es un promedio: 16 de
# los 41 caen en 32 compases de breakdown.
#
# 240 compases a 123 BPM son 7.8 minutos. Eso importa: la duracion es una de las
# DOS unicas cosas que distinguen lo que este DJ toca de lo que nunca toco
# (7.85 vs 7.37 min, p=4.1e-18 sobre 1816 tracks). La otra es el largo del
# breakdown. La mezcla —LUFS, rango dinamico, balance espectral, ancho— no
# distingue nada: sale igual en los dos grupos.
#
# Intro y salida largos no son relleno: son para que el tema se pueda mezclar.
#
# (nombre, compases, capas, intensidad)
# Todas las secciones son multiplo de 16 compases. No es prolijidad: cuando se
# mezclan dos temas alineando compas 1 con compas 1, las secciones del entrante y
# del saliente se encuentran. La version anterior tenia un Build de 8 que corria
# TODO lo que venia despues medio periodo de fraseo — 6 de 11 secciones caian
# fuera de la grilla de 16, incluido el breakdown, que es justo donde mas se
# mezcla.
#
# Eso obliga a mover el breakdown del compas 120 al 113: 120 no es alcanzable en
# una grilla de 16 (120/16 = 7.5). El 120 salio de un segmentador de audio sobre
# archivos, donde el compas 1 es el inicio del archivo y no una frontera de
# frase. 113 esta adentro del p25-p75 medido (105-131), asi que se pierde poco y
# se gana la grilla.
#
# El Drop 2 es el clima y por eso es el mas largo: 48 compases contra 32 del
# primero. Antes los dos eran identicos —mismas capas, misma intensidad— y el
# tema llegaba a su maximo a los 2:22 de 7:48 para no volver a superarlo nunca.
# Eso no es un arco: son dos mesetas iguales con un pozo en el medio.
#
# (nombre, compases, capas, intensidad)
ESTRUCTURA = [
    ("Intro",       16, {"bateria", "percusion", "atmosfera"},                  0.70),
    ("Base",        16, {"bateria", "bajo", "percusion", "atmosfera"},           0.80),
    ("Groove",      16, {"bateria", "bajo", "acordes", "percusion", "atmosfera"}, 0.90),
    ("Build",       16, {"bateria", "bajo", "acordes", "detalle", "percusion",
                         "atmosfera"},                                           0.94),
    # el primer drop NO lleva repiques: es lo que le deja algo nuevo al segundo
    ("Drop",        32, {"bateria", "bajo", "acordes", "detalle", "percusion",
                         "atmosfera"},                                           0.94),
    ("Meseta",      16, {"bateria", "bajo", "acordes", "percusion", "atmosfera"}, 0.86),
    # Con bateria pero sin bombo. Sin la bateria queda en el 44% del groove y
    # eso es un hueco; con ella y sin bombo queda cerca del 70% y sigue siendo un
    # breakdown. Un breakdown no es la ausencia de bateria: es la del bombo.
    ("Breakdown",   16, {"acordes", "detalle", "bateria", "percusion",
                         "atmosfera"},                                           0.74),
    ("Breakdown 2", 16, {"acordes", "detalle", "bateria", "percusion",
                         "atmosfera"},                                           0.82),
    ("Build 2",     16, {"bateria", "bajo", "acordes", "detalle", "percusion",
                         "atmosfera"},                                           0.92),
    ("Drop 2",      48, {"bateria", "bajo", "acordes", "detalle", "repiques",
                         "percusion", "atmosfera"},                              1.00),
    ("Salida",      16, {"bateria", "bajo", "percusion", "atmosfera"},           0.72),
    # los ultimos 16 compases SIN BAJO: es lo que hace mezclable la salida. Antes
    # el bajo llegaba hasta el compas 240 y el DJ tenia que cortar graves a mano
    # durante todo el outro.
    ("Salida 2",    16, {"bateria", "percusion", "atmosfera"},                   0.60),
]

SIN_BOMBO = {"Intro", "Breakdown", "Breakdown 2"}
# El clap en 2 y 4 sin nada en el 1 es la configuracion que hace que un DJ entre
# corrido medio compas. Y si el track saliente tiene clap —lo tiene, es
# progressive— son dos claps apilados durante toda la mezcla de entrada.
SIN_CLAP = {"Intro"}
# Ancla en el uno: en la intro no habia un solo transiente en el primer tiempo de
# ningun compas.
ANCLA_EN_UNO = {"Intro"}

# Doblajes por seccion y capa, en semitonos.
#
# Se saco el doblaje de octava del bajo en los drops. Llevaba el bajo a 7 notas
# por compas y hasta D4 (294 Hz) — arriba del maximo del corpus en las dos
# metricas, y con tres capas melodicas simultaneas en 82-247 Hz el 53% del
# tiempo. Eso no es un bajo con cuerpo: es una linea de medios peleando con el
# pad. Si se quiere sub mas medio, se resuelve con dos instrumentos sobre el
# mismo clip en Live, no duplicando notas.
#
# En el breakdown el pad se abre una octava para arriba y nada mas. Con [-12, 12]
# el breakdown terminaba con MAS notas por compas que cualquier drop, y un
# breakdown mas denso que el drop no le deja al drop contra que contrastar.
DOBLAJES = {
    "Breakdown": {"acordes": [12]},
    "Breakdown 2": {"acordes": [12]},
}

# Compases del final de cada frase de 16 donde una capa se calla. El progressive
# acumula hacia el turnaround dejando lugar, no agregando: sin esto los 240
# compases son 30 copias literales de los mismos 8.
FRASE = 16
HUECO_FINAL = 2

# Secciones que usan la celula B — otra progresion, misma tonalidad.
#
# El auditor lo marco y tenia razon: tres acordes repetidos 30 veces en 240
# compases no es un tema. La medicion dice 2 cambios de acorde cada 8 compases y
# eso se cumplia, pero nunca dijo que los 30 grupos de 8 tengan que ser el mismo
# grupo. La celula B se genera con `--registro oscuro` (i - VII - VI - VII, que
# no resuelve) contra la A que es i - VI - III.
CELULA_B = {"Breakdown", "Breakdown 2"}

NOTA_VOZ = 60          # C3, donde Simpler toca el sample sin transponer
LARGO_VOZ = 8.0        # pulsos que se sostiene la nota
# Un solo disparo. La frase entra al abrir el breakdown, que es donde el tema se
# queda mas solo. Repetirla tres veces la gastaba: una frase hablada es una idea,
# y una idea dicha tres veces en dos minutos deja de ser una idea.
COMPAS_VOZ = 32

NOTA_RISER = 60
# El riser entra dos compases antes de cada cambio de seccion. Es lo que hace
# que ocho compases y otros ocho suenen a un tema que va a algun lado, y no a
# dos bloques pegados.
AVISO = 2


def _voz(bpm: float) -> Pista:
    p = Pista("Voz", bpm, canal=0)
    p.nota(COMPAS_VOZ, 0, NOTA_VOZ, LARGO_VOZ, 104)
    return p


def _riser(bpm: float) -> Pista:
    """Un disparo antes de cada cambio de seccion, mas fuerte antes del drop."""
    p = Pista("Riser", bpm, canal=0)
    compas = 0
    for i, (_, largo, _, _) in enumerate(ESTRUCTURA[:-1]):
        compas += largo
        que_viene = ESTRUCTURA[i + 1][0]
        # Nada anunciando la salida. Antes habia riser y redoble completo
        # entrando al outro: una promesa que el tema no paga, y en cabina lee
        # como que va a pasar algo y no pasa nada.
        if que_viene.startswith("Salida"):
            continue
        # El grande va al Drop 2, que es el clima. Antes iba al Drop 1 porque la
        # comparacion era con "Drop" y nunca matcheaba "Drop 2": el momento mas
        # importante del tema tenia el build mas chico.
        p.nota(compas - AVISO, 0, NOTA_RISER, AVISO * 4,
               84 if que_viene == "Drop 2" else 58)
    return p


def _subida(bpm: float) -> Pista:
    """Redoble de clap que acelera en el ultimo compas de cada seccion.

    Acelera de corcheas a semicorcheas a fusas. Es el recurso mas gastado del
    genero y sigue funcionando por una razon simple: el oido mide el tiempo por
    la distancia entre golpes, y cuando esa distancia se achica lee que algo se
    acerca.
    """
    p = Pista("Subida", bpm, canal=9)
    compas = 0
    for i, (_, largo, _, _) in enumerate(ESTRUCTURA[:-1]):
        compas += largo
        if ESTRUCTURA[i + 1][0].startswith("Salida"):
            continue
        fuerte = ESTRUCTURA[i + 1][0] == "Drop 2"
        pasos = [0.0, 0.5, 1.0, 1.5, 2.0, 2.25, 2.5, 2.75,
                 3.0, 3.125, 3.25, 3.375, 3.5, 3.625, 3.75, 3.875]
        if not fuerte:
            pasos = pasos[:8]          # afuera del drop, medio redoble alcanza
        for k, pulso in enumerate(pasos):
            vel = int(52 + (100 - 52) * k / max(len(pasos) - 1, 1))
            p.nota(compas - 1, pulso, CLAP, 0.10, vel if fuerte else vel - 14)
    return p


def _expandir(nombre: str, notas: list, bpm: float, canal: int,
              notas_b: list | None = None) -> Pista:
    """Repite la celula seccion por seccion, con lo que corresponda a cada una."""
    p = Pista(nombre.capitalize(), bpm, canal=canal)
    compas = 0
    for seccion, largo, capas, intensidad in ESTRUCTURA:
        if nombre not in capas:
            compas += largo
            continue
        fuente = notas_b if (seccion in CELULA_B and notas_b) else notas
        for repeticion in range(largo // CELULA):
            base = compas + repeticion * CELULA
            for inicio, dur, altura, vel in fuente:
                if seccion in SIN_BOMBO and altura == KICK:
                    continue
                if seccion in SIN_CLAP and altura == CLAP:
                    continue
                c, pulso = divmod(inicio, 4)
                absoluto = base + int(c)
                # Donde cae este compas adentro de la frase de 16.
                en_frase = absoluto % FRASE
                ultimos = en_frase >= FRASE - HUECO_FINAL

                # El gancho se calla en los ultimos dos compases de cada frase:
                # el hueco antes del turnaround es lo que hace que la frase
                # termine en vez de simplemente repetirse.
                if ultimos and nombre == "detalle":
                    continue
                # El hat abierto solo en la SEGUNDA mitad de cada frase de 16.
                #
                # El periodo importa mas que la regla. La primera version lo
                # alternaba por compas par y no cambiaba nada: la celula se
                # repite cada 8 compases y 8 es par, asi que la paridad se
                # conserva y el compas 9 seguia siendo identico al 1. Una
                # variacion con periodo que divide a 8 es invisible.
                #
                # Con periodo 16 el hat entra en el compas 9 de cada frase, y
                # ahi las dos mitades dejan de ser iguales. Ademas es lo que hace
                # el genero: el abierto se abre cuando la frase ya arranco.
                if nombre == "bateria" and altura == OHH and en_frase < 8:
                    continue
                # el rim de la percusion, al reves: marca la primera mitad
                if nombre == "percusion" and altura == RIM and en_frase >= 8:
                    continue
                v = max(1, min(127, int(vel * intensidad)))
                # la ultima frase de cada seccion baja un poco: prepara el cambio
                if ultimos:
                    v = max(1, int(v * 0.88))
                p.nota(absoluto, pulso, altura, dur, v)
                for salto in DOBLAJES.get(seccion, {}).get(nombre, ()):
                    p.nota(absoluto, pulso, altura + salto, dur, max(1, v - 22))

            # Ancla en el uno de CADA compas donde no hay bombo ni clap. Sin
            # esto la intro no tenia un solo transiente en el primer tiempo, que
            # es lo que hace que un DJ entre corrido medio compas.
            if seccion in ANCLA_EN_UNO and nombre == "percusion":
                for k in range(CELULA):
                    p.nota(base + k, 0, RIM, 0.10, 54)
        compas += largo
    return p


def _por_seccion(fuentes: dict[str, list]) -> str:
    """Notas por compas en cada seccion, y cuanto es eso del groove.

    Existe por la misma razon que el reporte de `make_sketch`: el vacio no se
    ve leyendo la tabla de secciones, se ve en el numero. Medido sobre el
    repertorio propio, el breakdown tiene 11.8 onsets por compas contra 15.4 del
    groove — el 77%. Una version anterior de este arreglo dejaba el breakdown en
    el 17%, y eso no es contraste: es un hueco donde el oido lee que se corto el
    tema.
    """
    filas, groove = [], None
    for seccion, largo, capas, intensidad in ESTRUCTURA:
        n = sum(len(fuentes[c]) for c in capas if c in fuentes)
        # descontar el bombo donde no suena: si no, el reporte dice que la
        # seccion esta llena contando notas que el arreglo no escribe
        if seccion in SIN_BOMBO and "bateria" in capas and "bateria" in fuentes:
            n -= sum(1 for x in fuentes["bateria"] if x[2] == KICK)
        n /= CELULA
        if seccion == "Groove":
            groove = n
        filas.append((seccion, largo, n, len(capas & set(fuentes))))
    salida = ["  seccion        cps  capas  notas/cps   vs groove"]
    for seccion, largo, n, capas in filas:
        rel = f"{n / groove:5.0%}" if groove else "   --"
        aviso = "  <- vacio" if groove and n / groove < 0.55 else ""
        salida.append(f"  {seccion:13} {largo:4d} {capas:6d}  {n:9.1f}   {rel}{aviso}")
    salida.append("  (medido en el repertorio propio: el breakdown es el 77% del groove)")
    return chr(10).join(salida)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta", type=Path, help="carpeta del loop de 8 compases")
    ap.add_argument("--bpm", type=float, default=123.0)
    ap.add_argument("--repiques", type=Path, help="clip de repiques a sumar en el drop")
    ap.add_argument("--celula-b", type=Path,
                    help="segunda celula, con otra progresion, para el breakdown")
    ap.add_argument("--voz", action="store_true",
                    help="agrega los disparos de la voz (el sample se carga aparte)")
    ap.add_argument("--salida", type=Path)
    args = ap.parse_args()

    fuentes: dict[str, list] = {}
    for f in sorted(args.carpeta.glob("*.mid")):
        capa = f.stem.split("_", 1)[-1].lower()
        _, _, notas = leer(f)
        fuentes[capa] = notas
    fuentes_b: dict[str, list] = {}
    if args.celula_b and args.celula_b.exists():
        for f in sorted(args.celula_b.glob("*.mid")):
            fuentes_b[f.stem.split("_", 1)[-1].lower()] = leer(f)[2]
        print(f"  celula B: {len(fuentes_b)} capas desde {args.celula_b.name}")
    if args.repiques and args.repiques.exists():
        _, _, fuentes["repiques"] = leer(args.repiques)
    if not fuentes:
        sys.exit(f"  no hay clips en {args.carpeta}")

    total = sum(largo for _, largo, _, _ in ESTRUCTURA)
    salida = args.salida or (args.carpeta.parent / f"{args.carpeta.name}_tema")
    salida.mkdir(parents=True, exist_ok=True)
    for viejo in salida.glob("*.mid"):
        viejo.unlink()

    print(f"  {total} compases a {args.bpm:.0f} BPM = "
          f"{total * 4 * 60 / args.bpm / 60:.1f} min\n")
    orden = ["acordes", "bajo", "bateria", "detalle", "repiques",
             "atmosfera", "percusion"]
    for nombre, pista, archivo in (("voz", _voz(args.bpm), "06_voz.mid"),
                                   ("riser", _riser(args.bpm), "07_riser.mid"),
                                   ("subida", _subida(args.bpm), "08_subida.mid")):
        if nombre == "voz" and not args.voz:
            continue
        pista.guardar(salida / archivo)
        n = sum(1 for e in pista._eventos if e.datos[0] & 0xF0 == 0x90)
        print(f"  {nombre:9} {n:4d} notas")
    for n, capa in enumerate([c for c in orden if c in fuentes], start=1):
        canal = 9 if capa in ("bateria", "repiques") else 0
        p = _expandir(capa, fuentes[capa], args.bpm, canal, fuentes_b.get(capa))
        p.guardar(salida / f"{n:02d}_{capa}.mid")
        notas = sum(1 for e in p._eventos if e.datos[0] & 0xF0 == 0x90)
        suena = [s for s, _, capas, _ in ESTRUCTURA if capa in capas]
        print(f"  {capa:9} {notas:4d} notas   {', '.join(suena)}")

    print()
    print(_por_seccion(fuentes))
    print(f"\n  python scripts/a_live.py {salida} --bpm {args.bpm:.0f}")


if __name__ == "__main__":
    main()
