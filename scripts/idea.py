"""Un loop corto construido alrededor de UNA idea. Otra estrategia.

Por que existe: el generador anterior componia desde estadisticas. Se median
densidades, colocacion del bajo, color del timbre, continuidad, y se escribia lo
que cumpliera todos esos numeros. El resultado cumplia cada restriccion medida y
no decia nada.

La razon, en una linea: **una restriccion es una forma de no estar equivocado, no
una idea.** Acertar todas las restricciones del genero y no tener una idea da
exactamente lo que dio — un tema correcto y vacio. El promedio de muchos temas
buenos no es un tema bueno: es la ausencia de cualquier idea en particular.

Asi que esto arranca al reves. Primero la idea, despues las restricciones, y solo
las que no la peleen.

LA IDEA son dos cosas concretas:

1. **El ritmo del bajo**, medido sobre `Simon Vuarambon - Keep My Letters`. No
   se copian las alturas —esas son propias— sino la celula ritmica, que es lo
   que carga la identidad en este genero:

       . . A . . A . A . x . . . A . A

   Sus anclas son la 2, la 5, la 7, la 13 y la 15, y estan en los cuatro
   compases; el resto cambia. Ninguna cae en un pulso: su bajo esquiva el bombo
   —11-29% de las veces encima, contra 28-48% de Guy J— y de ahi sale que su
   groove flote en vez de marchar.

   (La primera version de este script uso la celula de `Moonflare`, que es otra:
   2, 5, 6, 9, 14. Se cambio al medir a Vuarambon y el encabezado quedo
   desactualizado hasta que el agente `bajo` lo marco.)

2. **Un gancho con forma de pregunta y respuesta.** Una nota larga que abre y
   tres cortas que contestan, dos veces, la segunda mas arriba y resolviendo
   para abajo. Eso es lo que hace que una melodia se recuerde: que tenga una
   pregunta y una respuesta, no que tenga las notas correctas de la escala.

Son 32 compases —poco mas de un minuto— a proposito. Un boceto que dura ocho
minutos no se puede iterar: para cuando termina ya no te acordas del principio.

Uso:
    python scripts/idea.py --camelot 11A --bpm 123
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NamedTuple

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plomo.humano import Humano  # noqa: E402
from plomo.midi import (  # noqa: E402
    MAYOR, MENOR, Pista, _Evento, grado, nombre_tonalidad, tonica_de_camelot,
    triada,
)

# ---------------------------------------------------------------------------
# El modo techno.
#
# Medido con `scripts/traducir.py` sobre "Tali Muss - Interlocutor (Kebin Van
# Reeken Extended Remix)" [Univack, 122 BPM] contra el original del mismo tema,
# que hace de control: la diferencia entre los dos ES lo que hace al remix
# techno, y no lo que hace a ese tema ese tema.
#
#                       remix        el boceto v1
#     bombo             4.00         4.0
#     clap              6.69         2.9
#     percusion         8.69         2.0
#     hat               9.19         6.0
#     bajo              2.62 ataques / 76% sonando      8.1 ataques
#     melodia           0.81 ataques / 77% sonando      arpegio de 13.6
#     sidechain bajo   -14.3 dB                          ninguno
#     graves            0.09 (casi mono)
#
# Lo importante no es que sea "mas" o "menos": es que la relacion se INVIERTE.
# La bateria se pone MAS densa —24.6 golpes por compas entre clap, percusion y
# hat contra los 10.9 del boceto— y lo melodico MUCHO menos. Un arpegio de
# catorce ataques por compas es lo contrario de techno por bien escrito que
# este: en techno lo de arriba se sostiene y lo que se mueve es la percusion.
#
# Por eso el modo techno saca cuatro pistas —arpegio, anchos, lead y cierre— y
# no las reemplaza. El pedido fue "baja instrumentos y pistas que necesites".
TECNO = False           # lo prende `--tecno`; lo leen los generadores

# La celula del bajo en techno: pocos ataques y notas largas.
#
# 2.62 ataques por compas con 76% de cobertura significa dos o tres notas que
# duran casi todo lo que hay entre una y la siguiente. No es la celula de
# Vuarambon con menos notas: es otra manera de tocar. La de Vuarambon empuja
# contra el bombo desde los huecos; esta se planta y deja que el sidechain le
# haga el ritmo.
FRASE_BAJO_TECNO = [
    # (semicorchea, largo en semicorcheas)
    [(0, 6), (6, 4), (10, 6)],
    [(0, 6), (6, 4), (10, 6)],
    [(0, 6), (6, 4), (10, 3), (13, 3)],
    [(0, 10), (10, 6)],
]

# El gancho en techno no es una melodia con figura: es una nota que se queda.
# 0.81 ataques por compas son cuatro notas cada cinco compases.
# Vuelta 1 del bucle (docs/BUCLE.md): "melodia suena" daba 100% contra 77% en
# la referencia. Las tres notas cubrian los dieciseis pulsos del bloque sin un
# solo hueco: 7.5 + 5.5 + 2.0 = 15 pulsos sonando de 16, y con la cola del pad
# el resto. La referencia respira: un cuarto del tiempo no hay nada arriba.
# Dos huecos por bloque —el pulso 4 al 5 y el 12 al 14— y la ultima nota mas
# corta. Cobertura escrita: 11.5 de 16 = 72%.
GANCHO_TECNO = [
    # (compas del grupo de 4, pulso, grado, duracion en pulsos)
    (0, 0.0, 0, 5.5),
    (1, 2.0, 4, 4.5),
    (3, 0.0, 2, 1.5),
]

COMPASES = 32
KICK, CLAP, CHH, OHH, RIM = 36, 39, 42, 46, 37
CRASH = 49
# El shaker y las congas NO son 70, 63 y 64. Esas son las notas del General
# MIDI, y los kits que usa el proyecto —909 Core Kit y 707 Core Kit— no tienen
# pad ahi: leidos por nombre desde Live, el 909 trae bombo, hats, clap, toms,
# rim, snare, crash y ride, y el 707 lo mismo mas tamb y cowbell. Durante dos
# dias todo lo escrito en 70/63/64 —el shaker en semicorcheas, las congas, el
# "filtro de peine" entre clap y shaker— fue MIDI a un pad vacio: silencio. Se
# descubrio grabando la pista sola y midiendo pico 0.000.
#
# Rim para el rol del shaker (un tick agudo a baja velocidad, que en techno es
# ademas lo idiomatico) y los toms alto y medio para las congas. Los tres pads
# existen en los dos kits, asi que el mismo MIDI suena en Bateria y en Repiques.
SHAKER = 37
CONGA_ALTA, CONGA_BAJA = 50, 47

# Los dos ultimos compases sueltan. El 32 era el mas lleno de todo el loop (peso
# 3706) y volvia al 1, que es el mas vacio (690): un salto de -81% cada vez que
# el loop da la vuelta. Un tema no loopea y no le pasaria; un boceto que se
# escucha en loop si, y es el corte que quedaba.
#
# La solucion no es llenar el compas 1 —ahi el tema tiene que empezar de la
# nada— sino que el 31 y el 32 bajen, que ademas es lo que hace cualquier
# turnaround.
# La bajada de la vuelta NO se aplica en el climax.
#
# VUELTA existe para que el loop no de la vuelta con todo sonando: prepara lo
# que viene. En la ultima seccion no viene nada, y aplicarla igual dejaba el
# tema terminando en bajo solo — que no es un cierre, es que se apagaron las
# cosas de a una sin motivo.
#
# Un final se sostiene y corta, o baja a proposito con una salida escrita. Lo
# que no puede es desarmarse por una regla pensada para otra cosa.
VUELTA_BASE = {29, 30, 31}
# El ultimo tiempo del ultimo compas queda casi vacio.
#
# La vuelta del loop tenia diez eventos en el cuarto tiempo del compas 32: el
# loop daba la vuelta con todo sonando y el compas 1 entraba encima. El aire es
# lo que convierte una vuelta en un turnaround — el oido necesita el hueco para
# leer que algo termino, y sin el escucha un corte.
#
# Queda el bajo, que es el que tira hacia el uno siguiente.
ULTIMO = COMPASES - 1

# La tension antes del drop, medida sobre los 8 compases previos al drop de
# `Cendryma, THMS (US) - Moonflare`:
#
#   c5  ................     dos compases de casi nada
#   c6  ................
#   c7  ............X.X.     empieza a aparecer algo al final
#   c8  ...XX..X.X..X...     y el ultimo acelera
#
# No es un riser: es un AGUJERO. Se vacia dos compases enteros y despues se
# llena acelerando. El riser anuncia por adicion —algo que crece encima de lo
# que ya suena— y esto anuncia por resta, que es mas fuerte porque el silencio
# no compite con nada.
# La subida al drop: los compases 29 a 32 de la seccion, o sea del 61 al 64.
#
# Antes esto era un POZO. Se vaciaban los compases 29 y 30 —peso 218 sobre una
# media de 1900, una sola capa sonando— con el argumento de que el silencio hace
# que lo que viene pegue mas fuerte. Medido en el arreglo entero se ve que no:
# el tema venia planchado hacia cuarenta y cuatro compases, y un agujero en el
# medio de una planicie no se escucha como tension, se escucha como que se corto
# la luz.
#
# El vacio funciona cuando lo que se vacia estaba lleno. Aca no lo estaba, y
# ademas es lo contrario de lo que un drop necesita: un drop no se prepara
# sacando, se prepara ACUMULANDO hasta que no entra nada mas y entonces cambia.
#
# Asi que no se calla nada. Todo lo que venia sonando sigue sonando, y encima se
# suman golpes que se aceleran: dos en el compas 29, tres en el 30, cinco en el
# 31, ocho en el 32. Es un redoble que se cierra, y las posiciones salen de la
# subida de Moonflare — pero SUMADAS al patron, no reemplazandolo.
VACIO: set[int] = set()
#
# Empieza en el compas 24 y no en el 28. Medida compas a compas, la subida vieja
# tenia DOCE compases planos y cuatro de redoble: del 65 al 76 el impacto se
# quedaba entre 850 y 1000, y recien en el 77 arrancaba a moverse. Eso no es una
# subida, es una espera con un susto al final.
#
# Ocho compases de acumulacion, de un golpe extra a ocho. El oido tiene que
# poder seguir la cuenta: si los golpes aparecen todos juntos en el ultimo
# compas, no hubo tension, hubo un anuncio.
SUBIDA = {24: [8],
          25: [8],
          26: [4, 12],
          27: [4, 12],
          28: [4, 8, 12],
          29: [4, 10, 14],
          30: [2, 6, 10, 12, 14],
          31: [0, 2, 4, 6, 8, 10, 12, 14]}
RELLENO: dict[int, list[int]] = {}

# El ultimo compas de cada bloque de 8: el que anuncia que algo cambia.
#
# La queja fue "es como brusco todo", y medido era literal: el compas 8 era
# identico al 7 y el 9 era otro tema — 1225 de velocidad sumada contra 2411 sin
# una sola nota en el medio que preparara el salto. Lo mismo en el 16 y en el
# 24. Un cambio de seccion se anuncia; nadie lo descubre cuando ya paso.
COMPASES_DE_PASO = (7, 15, 23)

# Cuanto se estira una nota del pad dentro del bloque siguiente, en pulsos.
# 0.9 pulsos son 440 ms a 123 BPM: alcanza para que la cola del acorde viejo
# tape el ataque del nuevo, que es todo lo que se le pide.
SOLAPE = 0.9

# El bajo, como FRASE DE OCHO COMPASES y no como celula de uno repetida.
#
# Las posiciones salen de medir a Simon Vuarambon (`data/recetas/vuarambon.json`),
# y son casi lo contrario de las de Guy J que estaban antes:
#
#   - Las ANCLAS son la 2, la 5, la 7, la 13 y la 15. Ninguna cae en un pulso.
#     Su bajo no toca donde toca el bombo: sobre cinco temas cae encima solo el
#     11-29% de las veces, contra el 40% de Lost & Found. Guy J se apoya en el
#     bombo; Vuarambon lo esquiva, y de ahi sale que su groove flote en vez de
#     marchar.
#   - El grupo 2-5-7 se amontona al principio del compas y despues hay un hueco
#     largo hasta la 13. Ese hueco es la mitad del asunto: es lo que deja
#     respirar antes de que la frase tire hacia el compas siguiente.
#
# Eran CUATRO compases y ahora son OCHO. La frase de cuatro se repetia seis
# veces entre el compas 9 y el 32 sin cambiar una sola nota: medido, la primera
# mitad de cada ocho tenia 24 notas y la segunda tambien 24 — +0%. En
# `Keep My Letters`, que es el tema del que salio esta celula, la segunda mitad
# tiene 30 contra 23 de la primera: **+30%**. La frase de Vuarambon se vacia y
# se vuelve a llenar adentro de los ocho compases; la nuestra se quedaba
# planchada en el medio y el unico movimiento que tenia era el de la velocidad.
#
# Los cuatro primeros compases son los que ya estaban (7, 6, 6, 5: baja y deja
# aire). Los cuatro de atras son los compases 5 a 8 medidos de `Keep My Letters`
# tal cual: 6, 9, 7, 8. La frase entera es 7-6-6-5-6-9-7-8, que se vacia hasta
# el cuarto compas y vuelve a subir hasta un pico en el sexto.
#
# Y de paso arregla el otro numero: las notas en pulso pasan de 2 sobre 24 (8%,
# por debajo del piso medido de 11%) a 8 sobre 54 (15%), adentro del 11-29% de
# Vuarambon. No hizo falta forzarlas — son las que el tema medido tiene en su
# segunda mitad, que es justo donde la frase empuja.
FRASE_BAJO = [
    [0, 2, 5, 7, 9, 13, 15],
    [2, 5, 7, 10, 13, 15],
    [2, 5, 7, 12, 13, 15],
    [2, 5, 7, 13, 15],
    [0, 2, 5, 7, 10, 15],
    [0, 2, 5, 7, 8, 10, 12, 13, 15],
    [2, 5, 7, 8, 10, 13, 15],
    [2, 4, 5, 7, 9, 10, 13, 15],
]

# La intro toca LA MISMA frase, con una ventana que se abre; no otra linea.
#
# Antes tocaba `[0, 7, 13]` fijo en los ocho compases. Tres problemas medidos:
# conservaba 2 de las 5 anclas, no variaba una sola nota en ocho compases —o
# sea que no era una frase— y el salto al compas 9 era de 3 a 7 notas, **+133%
# en un compas**. Todo el resto del boceto esta rampado para no dar saltos asi
# (el shaker se rampeo por uno de +273%, la articulacion del bajo se rampeo a lo
# largo de cuatro compases), y el bajo daba el suyo sin que nadie lo mirara.
#
# Ahora se filtra la frase real con un conjunto que crece de a dos compases: la
# densidad va 3-3-5-5-6-7-8-7 y llega al compas 9 en 7, que es exactamente donde
# arranca la celula completa. El salto es 0%.
#
# El 0 se agrega siempre: sin bombo el oido no tiene donde apoyar el uno, y esa
# es la unica razon por la que la intro toca en pulso.
VENTANA_INTRO = (
    {5, 13},                        # 1-2: las dos anclas que sostienen
    {5, 7, 13, 15},                 # 3-4: el par que tira hacia el compas que viene
    {2, 5, 7, 10, 13, 15},          # 5-6: entra la 2, que es donde vive el acento
    {2, 5, 7, 8, 10, 13, 15},       # 7-8: casi la celula entera, lista para el bombo
)

# Alturas del bajo por posicion, en grados de la escala. Propias.
# La septima en el 15 es la que tira hacia el compas siguiente.
#
# Tres alturas distintas y nada mas: la mediana medida sobre el repertorio es
# 3.5 (`data/arreglos_medidos.json`). Y el bajo NO sigue a PROGRESION a
# proposito — no es un olvido. Medido, `Cendryma - Typical Use` tiene 1 sola
# altura de bajo contra 5 cambios de acorde y `Repressure` tiene 2 contra 5: el
# pedal abajo de una armonia que se mueve es lo que hace el repertorio, y es lo
# que sostiene el trance de la cosa. Si alguien "arregla" esto moviendo el bajo
# con el acorde, esta rompiendo algo medido.
GRADOS_BAJO = {0: 0, 2: 0, 4: 0, 5: 0, 7: 0, 8: 0, 9: 0, 10: 0, 12: 0,
               13: 4, 15: 6}

# Progresion por bloque de 4 compases: i durante 16 compases, v durante 8, y
# vuelve.
#
# El v menor es el segundo grado mas usado de Vuarambon —sobre 40 compases
# medidos: i×25, v×6, VI#×4, iii×3, II×2— y `i - v` aparece en 2 de sus 5 temas
# analizados. No resuelve como el VI ni abre como el iv: deja todo colgando, y
# eso es lo que hace que su musica se sienta suspendida.
#
# Se queda quieta 16 compases antes de moverse. Un cambio cada cuatro obliga a
# escuchar la armonia; cuando no se mueve, el oido se va al groove.
PROGRESION = [0, 0, 0, 0, 4, 4, 0, 0]

# El gancho, en (compas del grupo de 4, pulso, grado, duracion en pulsos).
#
# Pregunta: una blanca. Respuesta: tres negras bajando. Se repite un grado mas
# arriba y resuelve. Ocho notas en cuatro compases — si hicieran falta mas para
# que se entienda, no seria un gancho.
GANCHO = [
    (0, 0.0, 4, 2.0),
    (1, 0.0, 7, 0.7), (1, 1.0, 6, 0.7), (1, 2.0, 4, 1.4),
    (2, 0.0, 5, 2.0),
    (3, 0.0, 4, 0.7), (3, 1.0, 3, 0.7), (3, 2.0, 1, 1.8),
]


def _empuje(compas: int) -> float:
    """Cuanto crece lo que YA suena hacia el final del bloque de 8 compases.

    Devuelve 0 en los primeros seis compases, 0.5 en el septimo y 1.0 en el
    octavo. Es el unico crescendo real del loop y es a proposito el mas barato
    que hay: no suma una nota: le sube la velocidad a las semicorcheas del
    shaker y de los hats que ya estaban ahi.

    Existe porque antes no habia forma de saber que venia un cambio hasta que
    el cambio ya habia entrado. Agregar cosas nuevas para preparar habria
    sumado densidad justo donde hace falta lo contrario — antes de que algo se
    sienta grande, lo anterior tiene que ser chico. Subir lo que ya esta no
    engorda nada.
    """
    posicion = compas % 8
    return 0.0 if posicion < 6 else (posicion - 5) / 2.0


def _bajo_tecno(bpm: float, tonica: int, escala: list[int], h: Humano,
                climax: bool = False) -> Pista:
    """Bajo sostenido: dos o tres notas por compas que llenan el compas.

    La altura sigue la progresion y casi no se mueve adentro del compas — el
    movimiento de un bajo de techno es de TIMBRE y de nivel, no de notas, y eso
    lo hacen el sidechain y el filtro, que no se escriben en el MIDI.
    """
    p = Pista("Bajo", bpm, canal=0)
    for c in range(COMPASES):
        g = PROGRESION[c // 4]
        celda = FRASE_BAJO_TECNO[c % len(FRASE_BAJO_TECNO)]
        for i, (k, largo) in enumerate(celda):
            # la quinta arriba en la ultima nota de la celda de cuatro compases
            grado_rel = g + (4 if climax and c % 4 == 3 and i == len(celda) - 1
                             else 0)
            alt = grado(tonica, escala, grado_rel, octava=1)
            pulso = k * 0.25
            vel = 104 if k == 0 else 92
            # 0.92 y no 1.0 del largo: si la nota llega justo al ataque de la
            # siguiente y es la misma altura, el note-off de una apaga la otra.
            p.nota(c, h.pulso("bajo", c, pulso), alt, largo * 0.25 * 0.92,
                   h.vel("bajo", c, pulso, vel))
    return p


def _bajo(bpm: float, tonica: int, escala: list[int], h: Humano,
          pleno: bool = False, climax: bool = False, tension: bool = False) -> Pista:
    p = Pista("Bajo", bpm, canal=0)
    for c in range(COMPASES):
        if tension and c in VACIO:
            continue
        intro = c < 8 and not pleno
        # En la intro el bajo toca LA MISMA frase, recortada por una ventana que
        # se abre, y siempre con el uno.
        #
        # La celula completa esta hecha para entrelazarse con el bombo: sus
        # anclas son la 2, la 5, la 7, la 13 y la 15, y ninguna cae en un pulso.
        # Eso funciona cuando hay bombo marcando los cuatro tiempos. Sin bombo
        # —que es toda la intro— queda una linea sincopada sin nada contra que
        # medirse, y el oido no encuentra donde esta el uno. Por eso va el 0.
        #
        # Lo que cambio: antes la reduccion era `[0, 7, 13]` fijo, ocho compases
        # identicos y un salto de +133% de densidad al entrar el bombo. Ahora es
        # la frase real filtrada, asi que la intro presenta las anclas que el
        # tema va a usar despues y llega al compas 9 con la misma densidad.
        celula = FRASE_BAJO[c % len(FRASE_BAJO)]
        if intro:
            celula = sorted({0} | (set(celula) & VENTANA_INTRO[c // 2]))
        # La duracion llega hasta la proxima nota: el bajo es una linea, no
        # golpes sueltos. Cuanto llega depende de si hay bombo: en la intro el
        # bajo es lo unico armonico que suena y tiene que SOSTENER (92% del
        # hueco, casi legato); con el bombo abajo pasa a MARCAR y se cierra al
        # 72%, que deja aire entre nota y nota.
        #
        # Eso pasaba de golpe en el compas 9 — 92% a 72% de un compas al otro,
        # en el mismo compas donde entraba el bombo y entraban los acordes. El
        # bajo cambiaba de articulacion en el peor momento posible y sumaba al
        # corte en vez de tapararlo. Ahora se cierra a lo largo de doce
        # compases: para cuando la mano suelta, el oido ya se acostumbro.
        #
        # Dos arreglos sobre esto:
        #
        #   - La rampa NO corre en `--pleno` ni en `--climax`. Existe para tapar
        #     la costura entre una intro sin bombo y el resto; en pleno el bombo
        #     suena desde el compas 1 y no hay costura. Medido, los primeros
        #     ocho compases del pleno cubrian el 96% del tiempo contra el 80%
        #     del resto de la seccion: el bajo arrancaba pegado y se abria
        #     despues, sin ningun motivo, en la seccion que se supone que es la
        #     mas firme de las tres.
        #   - Baja de a poco desde el primer compas en vez de quedarse en 0.92
        #     hasta el 8. Con la intro rampada en densidad, 0.92 sobre una
        #     celula que ya tiene siete notas daba 97% de cobertura y un hueco
        #     mediano de 25 ms: eso no es un bajo sostenido, es un pedal. Se
        #     abre a medida que entran notas, asi que la intro respira igual
        #     mientras se llena.
        if pleno:
            apertura = 0.72
        elif c < 8:
            apertura = 0.92 - 0.04 * (c // 2)     # 0.92, 0.88, 0.84, 0.80
        elif c < 12:
            apertura = 0.78 - 0.02 * (c - 8)      # 0.78, 0.76, 0.74, 0.72
        else:
            apertura = 0.72
        for i, k in enumerate(celula):
            siguiente = celula[i + 1] if i + 1 < len(celula) else 16 + celula[0]
            dur = max(0.22, (siguiente - k) * 0.25 * apertura)
            alt = grado(tonica, escala, GRADOS_BAJO[k], octava=1)
            pulso = k * 0.25
            # El acento va en las anclas que esquivan el bombo. Y las notas que
            # SI caen en pulso van mas flojas, no mas fuertes: ahi abajo ya hay
            # un bombo de 108, y dos transitorios en el mismo tick no suenan mas
            # fuerte, suenan mas sucios. Todo el sub-estilo es que el bajo
            # esquiva el bombo; cuando se lo cruza, le cede.
            vel = 104 if k in (2, 9) else 88
            if k % 4 == 0 and (pleno or c >= 8):
                vel -= 10
            p.nota(c, h.pulso("bajo", c, pulso), alt, dur,
                   h.vel("bajo", c, pulso, vel))
            # En el climax el bajo se dobla una octava ARRIBA, no abajo. Arriba
            # suma cuerpo audible en un celular y en un sistema chico; abajo solo
            # suma energia que no se escucha y se come el headroom. Va 20 de
            # velocidad mas bajo para que la fundamental siga mandando.
            #
            # Se dobla SOLO la tonica. Antes se doblaba todo, y eso rompia dos
            # reglas medidas de una: quedaban 6 alturas distintas (el tope es
            # 3-4, porque un bajo hipnotico ancla y no cuenta una melodia) y la
            # mas alta era E3 = 165 Hz, que esta 20 Hz por DEBAJO de la nota mas
            # grave del pad (F#3 = 185 Hz). O sea que el doblaje del climax se
            # metia adentro del registro del pad — que es exactamente la linea
            # de medios peleando con el pad que no tiene que ser.
            #
            # Doblando solo la tonica quedan 4 alturas y el techo del bajo es
            # F#2 = 92 Hz, una octava entera abajo del pad. Y el doblaje cae en
            # la 2, la 5 y la 7, que son las anclas: refuerza el groove en vez
            # de subrayar las notas de color.
            # Y solo en DOS posiciones, no en las seis que son tonica.
            #
            # Doblando toda la tonica el bajo pasaba a 11.6 notas por compas, y
            # el maximo del corpus es 7.75 con mediana 3.5. Un doblaje refuerza
            # los apoyos; cuando aparece en cada nota deja de ser un doblaje y
            # pasa a ser una segunda linea compitiendo con la primera. Con la 2 y
            # la 10 queda en 8.0, arriba de la mediana como corresponde a un
            # climax y adentro del techo medido.
            if climax and k in (2, 10):
                p.nota(c, h.pulso("bajo", c, pulso), alt + 12, dur,
                       h.vel("bajo", c, pulso, vel - 26))
    return p


HATS = {CHH, OHH}


def _hats(bateria: Pista, bpm: float) -> Pista:
    """Los hats separados de la bateria, para su propia pista de Live.

    Los hats en el Drum Rack salen al centro con el bombo, y por eso el ancho
    de la bateria medía 0.03 contra 0.74-0.90 de las referencias. En su pista
    se les puede poner Haas y ancho sin tocar al bombo, que tiene que quedar
    mono. Se escriben en la bateria como siempre y se separan despues, asi la
    humanizacion y las vueltas no cambian.
    """
    p = Pista("Hats", bpm, canal=9)
    p._eventos = [ev for ev in bateria._eventos if len(ev.datos) > 2 and ev.datos[1] in HATS]
    bateria._eventos = [ev for ev in bateria._eventos if not (len(ev.datos) > 2 and ev.datos[1] in HATS)]
    return p


def _bateria(bpm: float, h: Humano, pleno: bool = False,
             climax: bool = False, tension: bool = False,
             sin_bombo: bool = False) -> Pista:
    """Lo minimo que sostiene el groove. Nada mas."""
    p = Pista("Bateria", bpm, canal=9)
    vuelta = () if climax else VUELTA_BASE

    def calla(compas: int, pulso: float) -> bool:
        # Ya no calla nada por tension: la subida SUMA. Lo unico que sigue
        # soltando es el ultimo compas del loop, y solo su ultimo pulso.
        return compas == ULTIMO and pulso >= 3.0

    for c in range(COMPASES):
        # El platillo del drop.
        #
        # Sin esto el compas 64 —el ultimo del redoble, con ocho claps y el
        # shaker en semicorcheas— pesaba 4331 y el 65, el primero del drop,
        # 3895. Medido asi el drop entra un 10% mas flojo que la subida que lo
        # anuncia, y eso es exactamente lo que se escucha como "no explota".
        #
        # La respuesta no es adelgazar la subida. Un redoble tiene que ser denso
        # o no es un redoble. La respuesta es que el drop tenga un golpe que la
        # subida no tiene, y en este genero ese golpe es un platillo abierto en
        # el uno. Es lo unico del tema que suena una vez cada ocho compases, y
        # por eso marca donde empieza algo.
        # El platillo NO va en este kit. El crash del 909 es una muestra de un
        # platillo real y en un tema donde todo lo demas es sintetico se escucha
        # como lo unico acustico que hay: aparece una bateria en el medio de una
        # maquina. Se mudo a su propia pista, con un cimbal 808 —ruido metalico
        # sin cuerpo de bronce— y con su propio filtro y su propia reverb, que
        # dentro del kit no se le podian poner sin afectar al bombo.
        # El crescendo de fin de frase NO se aplica en la vuelta del loop: ahi
        # los dos empujes se peleaban y ganaba el crescendo, asi que el compas
        # 32 terminaba siendo mas pesado que el 31 justo donde tenia que soltar.
        # Un crescendo prepara lo que viene; en la ultima frase lo que viene es
        # el principio, y al principio no hay que empujarlo.
        emp = 0.0 if c in vuelta else _empuje(c)
        paso = c in COMPASES_DE_PASO
        if (pleno or c >= 8) and not sin_bombo:   # el bombo entra en el 9
            for pulso in range(4):
                if calla(c, pulso):
                    continue
                # El bombo del drop pega mas fuerte. Estaba en 108 en todo el
                # tema, asi que el momento mas grande tenia exactamente el mismo
                # golpe que la intro: mas capas encima, pero el mismo piso.
                p.nota(c, pulso, KICK, 0.25,
                       h.vel("kick", c, pulso, 120 if climax else 106))
        # El clap entra recien en el 13, cuatro compases DESPUES del bombo.
        #
        # Antes el 9 traia bombo, clap y acordes juntos: tres elementos nuevos
        # en el mismo tiempo 1, y el bajo cambiando de articulacion encima. Un
        # cambio se escucha; tres a la vez se escuchan como un corte de cinta.
        # Bombo solo cuatro compases y despues el contratiempo es el orden de
        # siempre del genero, y ademas le da al compas 13 un evento propio
        # donde antes no pasaba nada.
        # En los compases del redoble no va el clap de contratiempo: sus
        # semicorcheas 4 y 12 ya estan en RELLENO y se escribian dos veces en el
        # mismo tick. En Ableton quedan apiladas y el note-off de una corta la
        # otra, asi que se perdian 3 de los 7 golpes del acelerando.
        if (pleno or c >= 12) and not sin_bombo:
            for pulso in (1, 3):
                if calla(c, pulso):
                    continue
                p.nota(c, h.pulso("clap", c, pulso), CLAP, 0.25,
                       h.vel("clap", c, pulso, 110 if climax else 90))
            # 6.69 claps por compas en el remix contra 2.9 en el boceto. Los
            # de mas son fantasmas flojos entre los dos golpes principales: no
            # cambian donde esta el contratiempo, lo llenan.
            # Solo 1.5 y 3.5. Los fantasmas en 0.75 y 2.75 —la semicorchea
            # justo antes del pulso— se escuchan como un adelanto del golpe
            # que viene, casi un flam contra el bombo: "siento los claps a
            # destiempo". Lake Of Fire mide 7.8 claps por compas pero con 7.7
            # ms de dispersion; lo que da el numero es la regularidad, no
            # golpes que anticipan.
            if TECNO:
                for pulso in (1.5, 3.5):
                    if calla(c, pulso):
                        continue
                    p.nota(c, h.pulso("clap", c, pulso), CLAP, 0.12,
                           h.vel("clap", c, pulso, 52 if pulso % 1 else 46))
            # El eco del clap en 3.875 se fue: era una fusa antes del uno,
            # puesto para esquivar un shaker que resulto no sonar nunca. Con
            # la percusion real alrededor era un flam contra el bombo — "el
            # clap sigue a destiempo".
            if False and climax and not calla(c, 3.875):
                # El eco del clap antes de la vuelta al uno, en 3.875 y no en
                # 3.75: en 3.75 caia encima del shaker —26 veces a menos de
                # 10 ms— y dos transientes agudos tan cerca dan filtro de peine.
                p.nota(c, h.pulso("clap", c, 3.875), CLAP, 0.15,
                       h.vel("clap", c, 3.875, 64))
        # Hats: abierto y cerrado ALTERNADOS en los contratiempos de corchea.
        #
        # Antes el cerrado iba en 0.75, 1.75, 2.75, 3.75 — la semicorchea justo
        # ANTES de cada pulso. Eso no se escucha como un hat sino como un
        # adelanto del golpe que viene, casi un flam contra el bombo. Era el hat
        # raro.
        #
        # El contratiempo de corchea es donde vive el hat en house: abierto en el
        # 1 y el 3, cerrado en el 2 y el 4. Alternar los dos es lo que arma el
        # vaiven, y ademas evita que los dos caigan encima como pasaba antes.
        abiertos = ((0.5, 1.5, 2.5, 3.5) if (climax or TECNO)
                    else (0.5, 2.5))
        for pulso in abiertos:
            # El abierto entra en el compas 3 y las congas en el 5. Escrito
            # como estaba —`c % 8 >= 4 or c >= 8`— era literalmente `c >= 4`, y
            # ocultaba que dos capas entraban en el mismo compas: el salto del 4
            # al 5 era de +96%, el mas grande del boceto.
            if (pleno or c >= 2) and not sin_bombo:
                if calla(c, pulso):
                    continue
                # Rampa en sus primeros compases. Entrando de golpe daba el
                # salto de +77% del compas 2 al 3, el mas grande de la intro.
                sube = 1.0 if pleno else min(1.0, 0.45 + (c - 2) * 0.20)
                p.nota(c, h.pulso("hat_abierto", c, pulso), OHH, 0.20,
                       h.vel("hat_abierto", c, pulso,
                             max(8, int((58 + int(10 * emp)) * sube))))
        for pulso in (1.5, 3.5):
            # En el climax el abierto va en los cuatro contratiempos, asi que
            # el cerrado no se suma: se reemplaza. Sumandolo daban 60 racimos de
            # abierto y cerrado a menos de 7 ms.
            if climax:
                continue
            if paso and pulso == 3.5:
                # El repique que ocupaba este lugar se borro y quedo el guard
                # solo: los compases 8, 16 y 24 —los que anuncian el cambio—
                # terminaban con UN evento MENOS que sus vecinos. Se repone el
                # abierto, que era lo que el comentario prometia.
                p.nota(c, h.pulso("hat_abierto", c, 3.5), OHH, 0.35,
                       h.vel("hat_abierto", c, 3.5, 74))
                continue
            if calla(c, pulso):
                continue
            p.nota(c, h.pulso("hat", c, pulso), CHH, 0.10,
                   h.vel("hat", c, pulso, (40 if c < 8 else 54) + int(10 * emp)))
        # Fantasmas en 0.25 y 2.25, no en 1.75 y 3.75.
        #
        # El shaker toca las semicorcheas 3-7-11-15, o sea 0.75/1.75/2.75/3.75:
        # los fantasmas caian encima de la mitad. Medido, 35 racimos de dos
        # transitorios agudos separados por 1 a 9 ms. Eso no se escucha como
        # flam sino como filtro de peine —la primera muesca cerca de 100 Hz,
        # repitiendose cada 200— y como la dispersion es aleatoria por nota, la
        # coloracion cambia compas a compas. Eso es "arenoso" y "a destiempo"
        # al mismo tiempo.
        #
        # Ademas 0.25 y 2.25 caen DESPUES del pulso, asi que no vuelven a
        # leerse como el adelanto del bombo que el DJ ya habia rechazado.
        for pulso in (0.25, 2.25):
            if calla(c, pulso):
                continue
            p.nota(c, h.pulso("hat", c, pulso), CHH, 0.08,
                   h.vel("hat", c, pulso, 26 if c < 8 else 34))
        # Shaker en semicorcheas corridas. Es textura, no golpes: continuo y muy
        # abajo, es lo que llena sin que se escuche como un elemento mas.
        #
        # Y es el crescendo del tema. Sobre los dos ultimos compases de cada
        # bloque de 8 la velocidad sube dentro del compas —de la semicorchea 1
        # a la 16— hasta 26 puntos. No hay una nota mas que antes: son las
        # mismas y crecen. Un shaker que se abre es la forma mas vieja y mas
        # barata que hay de decir "viene algo", y es exactamente lo que el loop
        # no tenia.
        # El shaker entra en el compas 1 y CRECE; no aparece en el 5.
        #
        # Antes arrancaba junto con las congas y el salto del compas 4 al 5 era
        # de +273% de peso, el mas grande de todo el loop — mas grande incluso
        # que la entrada del bombo. Lo causaba que dos capas entraran juntas.
        # Separarlas y darle rampa a una lo baja sin sacarle nada al arreglo.
        # Cuatro por compas, no doce. Doce era un tercio de toda la densidad
        # del tema y lo que lo volvia denso; cuatro alcanzan para que se sienta
        # el movimiento sin que se escuche como arena.
        for k in (3, 7, 11, 15):
            rampa = (1.0 if pleno else min(1.0, 0.30 + c * 0.18)) * (0.40 if c in vuelta else 1.0)
            base = (24 if c < 8 else 32) + int(round(26 * emp * k / 15))
            # En los compases del redoble el shaker aprieta. Antes esto se hacia
            # escribiendo un SEGUNDO shaker encima del que ya estaba, y dos
            # capas en la misma grilla con distinta humanizacion es una capa
            # peleandose consigo misma: trece racimos a menos de 10 ms por
            # seccion. La capa que ya suena tocando mas fuerte hace lo mismo
            # sin agregar un solo transiente nuevo.
            if tension and c in SUBIDA:
                base = int(base * (1.10 + (c - 24) * 0.09))
            if calla(c, k * 0.25):
                continue
            p.nota(c, h.pulso("percusion", c, k * 0.25), SHAKER, 0.07,
                   h.vel("percusion", c, k * 0.25, max(6, int(base * rampa))))
        # Percusion en el registro medio, EN LA GRILLA de semicorcheas.
        #
        # Antes iba en tresillos contra las semicorcheas del hat. La idea era
        # que dos grillas distintas hicieran que un compas no sonara a un
        # compas — y lo que hizo fue que todo sonara a destiempo. Con el shaker
        # en semicorcheas, los hats con swing y las congas en tresillos habia
        # TRES grillas peleando, y el oido no las lee como poliritmia sino como
        # que nadie esta en tiempo.
        #
        # Dos golpes por compas, en el contratiempo. La poliritmia se puede
        # intentar de nuevo, pero con una sola capa fuera de grilla y no con
        # todo el resto encima.
        # 1.25 y 3.25: la "e" del 2 y la del 4, simetricas y sin pisar nada.
        # En 1.75 la conga era el TERCER transitorio de esa semicorchea, junto
        # al shaker y al fantasma. Es el mismo error que motivo sacar los
        # tresillos, mudado de tres grillas a una sola posicion.
        # En techno la percusion es lo que se mueve, y por eso es lo unico
        # que SUBE al pasar de house a techno: el remix mide 8.69 golpes por
        # compas de percusion contra los 2.0 del boceto. Seis posiciones en vez
        # de dos, todas en la grilla de semicorcheas.
        # "Mas electronico y menos conga": los toms en dos posiciones, no en
        # seis. La densidad de percusion de la referencia (9.4 por compas) la
        # ponen los repiques electronicos del 808, no los toms.
        posiciones = ((1.25, CONGA_BAJA), (3.25, CONGA_ALTA))
        for pulso, alt in posiciones:
            if c < 4 and not pleno:
                continue                 # en la intro solo shaker y rim
            if calla(c, pulso):
                continue
            rampa = (1.0 if pleno else min(1.0, 0.22 + c * 0.13)) * (0.38 if c in vuelta else 1.0)
            p.nota(c, h.pulso("percusion", c, pulso), alt, 0.12,
                   h.vel("percusion", c, pulso, max(8, int((52 + int(10 * emp)) * rampa))))
        # El redoble que acelera. Se SUMA al patron completo en vez de
        # reemplazarlo: en los cuatro compases de subida sigue sonando todo y
        # ademas entran estos golpes, cada vez mas juntos y mas fuertes.
        if tension and c in SUBIDA:
            for i, k in enumerate(SUBIDA[c]):
                if k % 4 == 0 and k // 4 in (1, 3):
                    continue             # ese contratiempo ya lo tiene el clap
                # Perfil "percusion" y no "clap", que es lo que parece que
                # corresponde. El motivo es el filtro de peine: el shaker base
                # ya toca las dieciseis semicorcheas con perfil "percusion", asi
                # que un golpe en la MISMA semicorchea con otro perfil cae a
                # unos milisegundos del shaker. Dos transientes agudos separados
                # por 1 a 9 ms no se escuchan como dos golpes sino como un golpe
                # con el timbre roto, y como la humanizacion los mueve al azar
                # el color cambia compas a compas. Con el mismo perfil caen
                # exactamente juntos, que es un golpe apilado y suena a uno solo.
                p.nota(c, h.pulso("percusion", c, k * 0.25), CLAP, 0.10,
                       h.vel("percusion", c, k * 0.25,
                             min(98, 44 + i * 6 + (c - 24) * 6)))
        # El rim marca el uno mientras no hay bombo — y en pleno y climax el
        # bombo entra en el compas 1, asi que ahi el rim era un flam pegado a su
        # ataque: 8 racimos de bombo y rim a menos de 7 ms.
        if c < 8 and not pleno:
            # calla(c, 0.0) y no calla(c, pulso): `pulso` no existe en este
            # alcance — es la que quedo colgada del for de las congas, o sea
            # siempre 3.25. Hoy no molesta porque el rim solo toca en c<8 y los
            # compases afectados son >=28, pero cualquier cambio a VACIO,
            # RELLENO o ULTIMO lo activaria en silencio.
            if calla(c, 0.0):
                continue
            p.nota(c, h.pulso("percusion", c, 0), RIM, 0.10,
                   h.vel("percusion", c, 0, 42))
    return p


# Los dos ultimos compases sueltan. El compas 32 era el mas lleno de todo el
# loop (peso 3706) y volvia al compas 1, que es el mas vacio (690): un salto de
# -81% en la vuelta, que se escucha como un corte cada vez que el loop da la
# vuelta. Un tema no loopea y no le pasaria; un boceto que se escucha en loop si.
#
# La solucion no es llenar el compas 1 —ahi el tema tiene que empezar de la
# nada— sino que el 31 y el 32 bajen, que ademas es lo que hace cualquier
# turnaround.
def _acordes(bpm: float, tonica: int, escala: list[int], h: Humano,
             pleno: bool = False, tension: bool = False) -> Pista:
    """La armonia se planta: i durante 16 compases, iv durante 8, y vuelve.

    Golpes cortos en el contratiempo mas una fundamental larga abajo: la triada
    sostenida con reverb es lo que suena a organo.
    """
    p = Pista("Acordes", bpm, canal=0)
    for bloque in range(COMPASES // 4):
        g = PROGRESION[bloque]
        notas = triada(tonica, escala, g, octava=3, septima=False)
        # La fundamental dura 16 pulsos + solape en vez de 15.5. Antes dejaba
        # 244 ms de silencio en cada frontera de cuatro compases y volvia a
        # atacar en el uno siguiente: un corte audible en la nota mas grave que
        # hay sonando, y justo donde cambia la seccion.
        # La fundamental larga se borro: era un DUPLICADO EXACTO de la
        # atmosfera —mismo pulso, misma altura, misma duracion, seis veces— y
        # existia solo como parche del piso, que estaba roto. Con la atmosfera
        # atada el piso lo hace el piso. Ademas su golpe del compas 16 mataba a
        # la fundamental del bloque siguiente 34 ms despues de que empezaba.
        if bloque < 2 and not pleno:     # los acordes entran en el compas 9
            continue
        for c in range(bloque * 4, bloque * 4 + 4):
            emp = _empuje(c)
            for pulso in (1.5, 3.5):
                # 0.55 pulsos y no 0.32. A 123 BPM 0.32 son 156 ms: eso no es
                # un golpe de acorde, es un click con altura. 0.55 sigue siendo
                # corto —268 ms, media negra— asi que no se vuelve el organo
                # sostenido que estos golpes existen para evitar, pero ahora
                # cada uno tiene cola. Un ataque sin cola es literalmente lo
                # que se escucha como brusco.
                p.acorde(c, h.pulso("acordes", c, pulso), notas[1:], 0.55,
                         h.vel("acordes", c, pulso,
                               (62 if pulso == 1.5 else 54) + int(10 * emp)))
    return p


# La melodia del climax: sale de su ciclo y resuelve dulce.
#
# El gancho de la primera parte pregunta y contesta adentro del mismo circulo —
# vuelve siempre al mismo lugar, que es lo que lo hace un gancho—. En el peak eso
# ya se dijo cuatro veces, y repetirlo una quinta no agrega: cansa.
#
# Esta figura es la respuesta larga. Tres cosas la hacen mas dulce sin salirse de
# la tonalidad:
#
#   - Arranca una octava arriba de donde venia el gancho, asi que el oido la
#     reconoce como la misma linea que subio.
#   - Sus tres notas largas son E, A y C#: eso ES el acorde de III. La
#     version anterior decia apoyarse en el III y usaba G#, que no pertenece
#     ni al III ni al VI — sonaba mas suspendida, no mas dulce.
#   - La ultima dura 1.9 y no 2.2: con 2.2 terminaba 0.2 pulsos DENTRO del
#     compas siguiente y su tercera mataba la blanca que abre la frase, que
#     duraba 99 ms en vez de 1.19 s tres veces de cuatro. El resto del tema vive en la i y el v, que son
#     los dos que suenan oscuros.
#   - Resuelve HACIA ABAJO y se queda ahi. La frase que sube es tension; la que
#     baja y se queda, cierre. Despues de tres minutos subiendo, corresponde.
#
# Bajada un grado respecto de la primera version: llegaba al MIDI 97, que en un
# pluck filtrado se escucha fino y se despega del resto. Un grado de la escala
# mantiene la figura y el contorno; bajarla una octava entera la habria metido
# en el mismo registro que el gancho principal y habrian dejado de distinguirse.
GANCHO_DULCE = [
    (0, 0.0, 6, 2.4),
    (1, 0.0, 8, 0.7), (1, 1.0, 7, 0.7), (1, 2.0, 6, 1.6),
    (2, 0.0, 9, 2.4),
    (3, 0.0, 7, 0.7), (3, 1.0, 6, 0.7), (3, 2.0, 4, 1.9),
]


# El pad se queda en su registro en vez de trepar con el grado.
#
# `triada()` apila terceras desde el grado, asi que el acorde SUBE cuando sube el
# grado: el i daba [54, 57, 61] y el v [61, 64, 68] — el v arranca donde
# terminaba el i, y el piso del pad pasaba de 185 a 277 Hz en el compas 17. Media
# octava para arriba en la unica capa que no se tiene que mover, y justo en la
# frontera de seccion.
#
# Aca las clases de altura se meten en una ventana fija y cada voz elige la
# posicion mas cerca de donde estaba. Es lo que hace una mano: sostiene lo que
# puede y mueve lo minimo.
PISO_PAD, TECHO_PAD = 54, 66     # F#3 a F#4: arriba del bajo, abajo del gancho


def _voces(tonica: int, escala: list[int], g: int,
           anterior: list[int] | None = None) -> list[int]:
    clases = sorted({a % 12 for a in
                     triada(tonica, escala, g, octava=3, septima=False)})
    fuera = []
    for c in clases:
        cand = [a for a in range(PISO_PAD, TECHO_PAD + 1) if a % 12 == c]
        if anterior:
            cand.sort(key=lambda a: (min(abs(a - b) for b in anterior), a))
        fuera.append(cand[0])
    return sorted(fuera)


def _atmosfera(bpm: float, tonica: int, escala: list[int]) -> Pista:
    """El piso: notas atadas que no se cortan nunca.

    Es lo unico que no golpea. Sin esto la intro son bajo corto, hat y rim —
    tres cosas que atacan y ninguna que sostenga— y eso se escucha percusivo y
    vacio a la vez, que parece una contradiccion y no lo es: lo que falta no son
    eventos, es algo que dure entre evento y evento.

    Las notas que siguen sonando en el bloque siguiente NO se vuelven a atacar:
    se ATAN.

    Esto es la correccion de un error grave y vale escribirlo entero. La version
    anterior hacia durar cada acorde 16 pulsos + 0.9 de solape, con el argumento
    —correcto— de que la cola del acorde viejo tiene que tapar el ataque del
    nuevo. Pero lo implementaba re-escribiendo LA MISMA ALTURA solapada, y en
    MIDI eso no sostiene: el stream queda `on, on, off, off` y el primer note-off
    apaga la nota. El pad terminaba mudo el 59% del tema, con cinco huecos de
    7.5 segundos — cincuenta y una veces peor que los 146 ms que decia arreglar.
    Y uno de esos huecos caia en el final, que es parte de por que el final
    sonaba a bajo solo.

    Atar es ademas lo que hace un tecladista: sostiene las notas comunes y mueve
    solo las voces que cambian. Ningun cambio de acorde queda con un ataque al
    descubierto, porque siempre hay voces sonando que lo tapan.
    """
    p = Pista("Atmosfera", bpm, canal=0)
    bloques = COMPASES // 4
    acordes: list[list[int]] = []
    for b in range(bloques):
        acordes.append(_voces(tonica, escala, PROGRESION[b],
                              acordes[-1] if acordes else None))
    for b, notas in enumerate(acordes):
        vel = 30 + round(24 * b / (bloques - 1))
        for alt in notas:
            if b and alt in acordes[b - 1]:
                continue                 # ya viene sonando: se ata
            largo = 1
            while b + largo < bloques and alt in acordes[b + largo]:
                largo += 1
            # Solo la ultima nota de la corrida lleva cola, y solo si viene otro
            # bloque que tape: la cola existe para el ataque del siguiente.
            cola = SOLAPE if b + largo < bloques else 0.0
            p.nota(b * 4, 0, alt, 4 * 4 * largo + cola, vel)
    return p


# -- la guitarra ------------------------------------------------------------
#
# El solo ocupa la SEGUNDA MITAD del climax: los compases 17 a 32, no los
# ultimos ocho. El gancho se calla en el 17 y a partir de ahi la voz que lleva
# es la guitarra. Con ocho compases no habia lugar para que el solo tuviera arco
# propio —arrancaba ya arriba porque no le quedaba otra—; con dieciseis puede
# empezar abajo y contenido y llegar arriba recien sobre el final, que es lo que
# hace que llegar arriba signifique algo.
COMPAS_SOLO = 16

# El material: PENTATONICA MENOR mas la quinta bemol, no la escala.
#
# Los grados II y VI son los que hacen que una escala suene a escala. Un solo de
# blues-rock no los toca: vive en i, III, iv, v, VII y pasa por el 5b. Por eso
# esto no usa `grado()` con MENOR —eso da la eolica entera— sino su propia
# escalera en semitonos sobre la tonica, que ademas es transportable.
#
# El 5b (indices 3 y 9) es la unica nota de afuera y se usa SIEMPRE de paso:
# sostenida desafina. Aca aparece tres veces y las tres dura menos de medio
# pulso.
#
# Ojo: esta escrita para tonalidad MENOR, que es lo que da 11A. En una tonalidad
# mayor la III de la pentatonica menor chocaria contra el acorde.
#
#  indice     0   1   2   3   4   5    6   7   8   9  10  11  12
#  grado      i  III  iv  5b   v VII    i III  iv  5b   v VII   i
#  en F#     F#4  A4  B4  C5 C#5  E5  F#5  A5  B5  C6 C#6  E6  F#6
ESCALERA = (0, 3, 5, 6, 7, 10, 12, 15, 17, 18, 19, 22, 24)

# Cuanto se estira una nota adentro de la siguiente cuando no cierra frase.
#
# Es la ligadura: en una guitarra la nota anterior no se corta para que empiece
# la que sigue, se pisan. Medido sobre `Lane 8 & Yotto - I love Y`, la capa
# melodica tiene 100% de continuidad y una nitidez de ataque de 3.3 contra 8.1
# de Moonflare: los ataques casi no sobresalen del sostenido. Eso no se consigue
# bajando velocidades, se consigue no dejando huecos entre nota y nota.
#
# 0.06 pulsos son 30 ms: alcanza para que no haya hueco y es demasiado poco para
# que se escuche como dos notas juntas.
LIGADURA = 0.06

# Aire sin pitch bend antes y despues del vibrato, en pulsos.
#
# El pitch bend es del CANAL, no de la nota. Si el vibrato de un apoyo sigue
# corriendo cuando entra la nota siguiente, la nota siguiente sale desafinada.
# Con 0.15 pulsos de margen a cada lado la rueda esta en cero cuando algo ataca.
MARGEN = 0.15
VIB_MINIMO = 0.40                # abajo de esto no entra vibrato: no da el largo

# La curva del bend. Mayor que 1 = llega tarde: la altura sube despacio al
# principio y rapido al final, que es lo que hace una mano empujando una cuerda.
# Un bend lineal suena a pitch shifter. Al soltar la curva es mas pareja, porque
# la cuerda vuelve sola.
CURVA_BEND = 2.4
CURVA_SUELTA = 1.4


class Toque(NamedTuple):
    """Una nota tocada, con lo que le pasa a la altura mientras suena.

    `dur` en 0 significa "hasta el ataque siguiente mas la ligadura". Se escribe
    a mano solo cuando la nota CIERRA una frase, o sea cuando lo que viene
    despues es silencio. Asi la data dice donde estan los ataques y donde
    respira, y no hay forma de dejar un hueco sin querer en el medio de una
    frase.
    """
    compas: int
    pulso: float
    grado: int                   # indice en ESCALERA
    vel: int
    dur: float = 0.0
    bend: float = 0.0            # semitonos DESDE los que se llega (negativo)
    bend_dur: float = 0.45
    curva: float = CURVA_BEND
    vib: float = 0.0             # ancho en semitonos
    vib_hz: float = 5.5
    vib_apaga: float = 0.0       # fraccion final en la que el vibrato se cierra
    suelta: float = 0.0          # semitonos que baja al final (soltar la cuerda)
    suelta_dur: float = 0.7


# El solo, en dieciseis compases y nueve frases.
#
# Tres cosas gobiernan la escritura y ninguna es la eleccion de las notas:
#
#   - **Los apoyos duran de 2 a 4 pulsos.** La mediana de duracion es de 1.4
#     pulsos contra 0.55 de la version anterior. Una guitarra no pica: planta
#     una nota y la sostiene con vibrato, y el sostenido ES el sonido. La
#     version anterior tenia treinta y siete notas en ocho compases; esta tiene
#     treinta y siete en dieciseis.
#   - **Entre apoyo y apoyo va una sola nota de conexion**, ligada, con la
#     velocidad veinte o treinta puntos mas abajo. Es el hammer-on o el pull-off:
#     la segunda nota no se pica. Una frase donde todas las notas tienen la misma
#     velocidad es una frase que nadie toco.
#   - **Cada frase termina y se calla.** Seis respiros de entre medio pulso y un
#     pulso y cuarto. Ocho compases sin un silencio no los toco una persona;
#     dieciseis, menos.
#
# El arco es lo que gana la seccion larga: F1 entra en E5 y F8 grita en E6, dos
# octavas de recorrido repartidas en catorce compases en vez de en seis. La
# velocidad sube 86 -> 118 en el mismo camino, sin un solo salto.
SOLO = [
    # F1 (c1-c2) — la entrada. Abajo, contenida, y el bend mas lento de todo el
    # solo: 0.75 pulsos para un tono. Se llega a la nota, no se la toca.
    Toque(0, 0.00, 5, 86, bend=-2, bend_dur=0.75, curva=2.6, vib=0.24, vib_hz=5.0),
    Toque(0, 3.50, 6, 68),                                   # ligado hacia el 2
    Toque(1, 0.00, 4, 90, dur=2.60, vib=0.26, vib_hz=5.2),   # cierra: baja una 3a
    Toque(1, 3.50, 2, 70),                                   # anacrusa de la F2

    # F2 (c3-c4) — la contesta y planta la tonalidad tocando la tonica abajo.
    # Es la unica vez en todo el solo que la guitarra baja a F#4, y esta a
    # proposito al principio: despues de esto no vuelve nunca mas abajo.
    Toque(2, 0.00, 1, 88, bend=-2, bend_dur=0.60, vib=0.26, vib_hz=5.2),
    Toque(2, 3.25, 2, 72),
    Toque(3, 0.00, 0, 84, dur=3.00, vib=0.30, vib_hz=4.6, vib_apaga=0.30),
    Toque(3, 3.60, 4, 80),

    # F3 (c5-c6) — sube un escalon. Mismo dibujo que F1 una cuarta arriba: la
    # frase que sigue contesta a la anterior o la lleva mas arriba, no cambia de
    # tema. Este apoyo no lleva bend: si todos los apoyos entran igual, la
    # entrada deja de ser un gesto y pasa a ser un tic.
    Toque(4, 0.00, 5, 94, vib=0.28, vib_hz=5.3),
    Toque(4, 3.60, 6, 74),
    Toque(5, 0.00, 7, 98, dur=2.80, bend=-2, bend_dur=0.50, vib=0.30, vib_hz=5.4),
    Toque(5, 3.40, 5, 78),

    # F4 (c7-c8) — el primer apoyo arriba: B5 con bend de tono desde A5, que es
    # EL gesto de este genero de solo. Y despues baja, porque todavia falta la
    # mitad del solo y llegar al techo aca lo dejaria sin ningun lado adonde ir.
    # El respiro que cierra es el mas largo de todo el solo: 1.10 pulsos.
    Toque(6, 0.00, 8, 102, bend=-2, bend_dur=0.45, vib=0.32, vib_hz=5.5),
    Toque(6, 3.40, 7, 76),
    Toque(7, 0.00, 6, 96, dur=2.40, vib=0.30, vib_hz=5.4, vib_apaga=0.25),
    Toque(7, 3.50, 7, 84),

    # F5 (c9-c10) — la mitad. Se instala arriba y ya no baja del registro. La
    # conexion es la quinta bemol: pasa por ella en cuatro decimas de pulso
    # camino a C#6 y no se apoya nunca.
    Toque(8, 0.00, 8, 104, vib=0.34, vib_hz=5.6),
    Toque(8, 3.60, 9, 74),                                   # 5b de paso
    Toque(9, 0.00, 10, 108, dur=3.00, bend=-2, bend_dur=0.42, curva=2.5,
          vib=0.34, vib_hz=5.6),
    Toque(9, 3.55, 8, 86),

    # F6 (c11-c12) — baja a tomar aire. Es la unica frase con dos conexiones
    # seguidas y es la unica que no lleva a ningun lado: existe para que lo que
    # viene despues tenga de donde subir. Antes de que algo se sienta grande, lo
    # anterior tiene que ser chico.
    Toque(10, 0.00, 7, 96, vib=0.30, vib_hz=5.4),
    Toque(10, 2.70, 6, 80),
    Toque(10, 3.35, 5, 84),
    Toque(11, 0.00, 6, 100, dur=3.00, bend=-2, bend_dur=0.55, vib=0.34,
          vib_hz=5.5, vib_apaga=0.25),
    Toque(11, 3.60, 7, 90),

    # F7 (c13-c14) — la subida. Aca y solo aca las notas se acortan: los apoyos
    # bajan de tres pulsos a uno y medio y las frases dejan de respirar. Es lo
    # unico que hace la aceleracion, porque acelerar con notas cortas cuando
    # todo el resto es largo se escucha sin que haya que subir nada.
    Toque(12, 0.00, 8, 102, bend=-2, bend_dur=0.35, curva=2.2, vib=0.30, vib_hz=5.7),
    Toque(12, 1.65, 10, 104, vib=0.30, vib_hz=5.7),
    Toque(12, 3.00, 9, 82),                                  # 5b de paso otra vez
    Toque(12, 3.40, 10, 108, vib=0.34, vib_hz=5.8),
    Toque(13, 1.10, 8, 92),
    Toque(13, 1.80, 10, 112, dur=2.20, bend=-2, bend_dur=0.38, vib=0.38, vib_hz=5.9),

    # F8 (c15) — el grito. E6, la nota mas alta del tema, con bend de tono desde
    # D6 que tarda 0.65 pulsos en llegar: se escucha subir.
    #
    # Se toca en DOS ataques y no en uno sostenido. Un guitarrista no aguanta
    # cuatro tiempos: la cuerda decae y la vuelve a picar con la mano todavia
    # empujando, por eso el segundo ataque no lleva bend —la cuerda ya esta
    # arriba— y lleva el vibrato mas ancho de todo el solo.
    #
    # Los dos ataques NO se solapan: el primero termina en 1.85 y el segundo
    # entra en 2.00. Escribir la misma altura solapada no la sostiene: el primer
    # note-off apaga a los dos y queda una nota de nada donde tenia que haber un
    # compas. Ese error ya se cometio dos veces en este proyecto.
    Toque(14, 0.00, 11, 118, dur=1.85, bend=-2, bend_dur=0.65, curva=2.8,
          vib=0.28, vib_hz=5.2),
    Toque(14, 2.00, 11, 110, dur=2.30, vib=0.46, vib_hz=6.1, suelta=-2.0,
          suelta_dur=0.75),

    # F9 (c16) — la caida y la resolucion. Tres notas bajando rapido, sin
    # apoyarse en ninguna, y la tonica de arriba sostenida con el vibrato mas
    # ancho y mas lento del solo hasta el final del compas. Despues de subir
    # catorce compases, caer es lo unico que cierra.
    Toque(15, 0.40, 10, 92),
    Toque(15, 0.80, 8, 78),
    Toque(15, 1.20, 7, 86),
    Toque(15, 1.60, 6, 114, dur=2.40, bend=-2, bend_dur=0.50, curva=2.5,
          vib=0.40, vib_hz=4.8, vib_apaga=0.35),
]


# El cierre: dieciseis compases DESPUES del climax. En el tema entero, del 97
# al 112.
#
# No es otro solo, y esa es toda la idea. El solo ya llego arriba y ya dijo lo
# que tenia para decir; volver a decirlo lo gasta. Un cierre despues de un peak
# es lo contrario: menos notas, mas largas, mas abajo, y sin llegar a ningun
# lado nuevo.
#
# Diez notas en dieciseis compases —0.6 por compas, contra 2.3 del solo— con la
# mediana de duracion en 5 pulsos. La mitad del tiempo no hay nada sonando, y
# ese silencio es la mitad del cierre: en un final el silencio pesa mas que en
# cualquier otra parte del tema.
#
# CITA el solo, no lo repite. La figura de F5 —B5, la quinta bemol de paso, C#6—
# vuelve una octava abajo en el compas 1 y otra vez, mas floja todavia, en el
# 11. Son las mismas tres notas y el mismo dibujo, sin el bend que las llevaba y
# sin el registro que las hacia gritar. Se escucha como el recuerdo de lo que
# paso, no como que vuelve a pasar.
#
# Y NO HAY UN SOLO BEND. Todo el solo se apoya en llegar a las notas empujando
# la cuerda; el cierre las toca donde estan. Es lo mismo que baja el vibrato de
# 0.46 a 0.30 y la velocidad de 118 a 60: la mano dejo de pelear.
CIERRE = [
    # F1 (c1-c3) — la cita. B4 seis pulsos, el 5b de paso, C#5 cinco pulsos.
    # Es la frase del compas 9 del solo, una octava abajo y sin bend.
    Toque(0, 0.00, 2, 76, dur=6.00, vib=0.30, vib_hz=4.6, vib_apaga=0.35),
    Toque(1, 3.50, 3, 54),                                   # 5b, casi inaudible
    Toque(2, 0.00, 4, 78, dur=5.00, vib=0.30, vib_hz=4.5, vib_apaga=0.35),

    # F2 (c5-c6) — baja. Dos notas y nada mas: A4 y la tonica abajo, ligadas,
    # sin ataque en el medio. El vibrato ya arranca mas angosto que el de F1.
    Toque(4, 0.00, 1, 72, vib=0.28, vib_hz=4.4, vib_apaga=0.35),
    Toque(5, 1.00, 0, 68, dur=4.00, vib=0.28, vib_hz=4.2, vib_apaga=0.40),

    # F3 (c8-c9) — el unico gesto que sube, y sube una segunda. Es lo mas cerca
    # que el cierre esta de intentar algo, y se rinde en la nota siguiente.
    Toque(7, 0.00, 5, 74, vib=0.26, vib_hz=4.4, vib_apaga=0.40),
    Toque(8, 1.00, 4, 66, dur=4.00, vib=0.26, vib_hz=4.2, vib_apaga=0.45),

    # F4 (c11-c12) — la cita otra vez, mas abajo y mas floja. Las mismas dos
    # notas con las que abrio el cierre, ahora sin el 5b y veinte puntos de
    # velocidad mas abajo.
    Toque(10, 0.00, 2, 64, vib=0.24, vib_hz=4.2, vib_apaga=0.45),
    Toque(11, 1.00, 1, 60, dur=4.00, vib=0.24, vib_hz=4.0, vib_apaga=0.50),

    # F5 (c14-c16) — la ultima nota del tema. Una sola, doce pulsos, la tonica.
    # Un ataque y ninguno mas: no se repica porque no tiene que sonar a que
    # alguien la esta tocando, tiene que sonar a que quedo sonando. El vibrato
    # se abre y se apaga en el ultimo tercio, y sobre el final la cuerda baja un
    # semitono: es la mano que afloja, no una nota nueva.
    #
    # De ahi para adelante el sonido lo hace la cola del amplificador y la
    # reverb, que no es algo que escriba el MIDI.
    Toque(13, 0.00, 0, 68, dur=12.00, vib=0.30, vib_hz=4.0, vib_apaga=0.55,
          suelta=-1.0, suelta_dur=1.60),
]


def _duraciones(toques: list[Toque]) -> list[float]:
    """La duracion de cada nota: la escrita, o hasta el ataque siguiente."""
    fuera = []
    for i, t in enumerate(toques):
        if t.dur:
            fuera.append(t.dur)
        elif i + 1 < len(toques):
            sig = toques[i + 1]
            salto = (sig.compas - t.compas) * 4 + sig.pulso - t.pulso
            # Si a la que viene se LLEGA con un bend, la ligadura se saca y esta
            # nota termina justo donde ataca la otra. El pitch bend es del CANAL:
            # con ligadura los ultimos 30 ms de esta nota se van un tono abajo
            # montados en el bend de la siguiente. Un ligado no desafina lo que
            # se esta apagando; ahi el guitarrista levanta el dedo y empuja.
            fuera.append(salto + (0.0 if sig.bend else LIGADURA))
        else:
            raise ValueError("la ultima nota tiene que llevar dur explicita")
    return fuera


def _tocar(nombre: str, bpm: float, tonica: int, h: Humano,
           toques: list[Toque], compas_cero: int, octava: int = 4) -> Pista:
    """Escribe una linea de guitarra: notas, bends, vibratos y sueltas.

    La velocidad se escribe A MANO y no pasa por `Humano.vel`. El perfil del
    gancho lleva un arco que sube a lo largo de cada bloque de ocho compases y
    se reinicia; sobre dieciseis compases eso mete un diente de sierra de veinte
    puntos justo en el compas 9, que es donde vive el apoyo mas importante de la
    primera mitad. El arco de un solo es la linea entera, no dos bloques
    iguales, y esta escrito nota por nota: 86 al entrar, 118 en el grito.

    El tiempo si pasa por `Humano`, con menos desvio en las notas rapidas. Una
    corrida de semicorcheas la toca alguien con la mano tensa; un apoyo de tres
    pulsos entra cuando quiere.
    """
    p = Pista(nombre, bpm, canal=0)
    for t, dur in zip(toques, _duraciones(toques)):
        c = compas_cero + t.compas
        crudo = h.pulso("gancho", c, t.pulso)
        pu = t.pulso + (crudo - t.pulso) * (1.0 if dur >= 1.0 else 0.4)

        p.nota(c, pu, 12 * (octava + 1) + tonica + ESCALERA[t.grado],
               dur, max(1, min(127, t.vel)))

        if t.bend:
            p.bend(c, pu, t.bend_dur, t.bend, 0.0, curva=t.curva)
        if t.suelta:
            p.bend(c, pu + dur - t.suelta_dur, t.suelta_dur, 0.0, t.suelta,
                   curva=CURVA_SUELTA)
        if t.vib:
            ini = (t.bend_dur if t.bend else 0.0) + MARGEN
            fin = dur - MARGEN - (t.suelta_dur if t.suelta else 0.0)
            if fin - ini >= VIB_MINIMO:
                p.vibrato(c, pu + ini, fin - ini, ancho=t.vib, hz=t.vib_hz,
                          retraso=0.25, desvanece=t.vib_apaga)
    return p


# El arpegio que reemplaza al solo, en semicorcheas.
#
# Medido sobre `Ezequiel Arias - Heat Above` con `scripts/instrumentos.py`: su
# capa melodica da 13.75 ataques por compas con el patron
#
#     x x A A x A A A A A A A A A A A
#
# o sea semicorcheas corridas con un hueco al principio del compas. Y la
# variacion dinamica es 0.13 — plano a proposito, porque un arpegio que acentua
# deja de ser textura y pasa a pelear con la melodia.
#
# Eze Arias NO toca solos. Un lead con bends es el concepto equivocado para este
# genero: su identidad melodica es una secuencia que corre.
#
# El hueco de las dos primeras semicorcheas es lo que lo salva de ser ruido. Un
# arpegio que no para nunca ya se probo en este proyecto y el veredicto fue "no
# fluye y tiene mucho ruido"; la diferencia es el hueco, el registro oscuro y
# que sea la unica capa melodica sonando.
HUECO_ARPEGIO = (0, 1)          # semicorcheas que quedan vacias

# Grados sobre los que gira, en indices de la escala. Sube y vuelve: un arpegio
# que solo sube se escucha como escala, y uno que se queda quieto como un
# ostinato de dos notas.
GIRO = [0, 2, 4, 6, 4, 2]


def _arpegio(bpm: float, tonica: int, escala: list[int], h: Humano) -> Pista:
    """Semicorcheas corridas, oscuras y planas. Ocupa el lugar del solo."""
    p = Pista("Arpegio", bpm, canal=0)
    # Desde el compas 1 del climax. Entraba en el 17 —a mitad del drop— y eso
    # dejaba dieciseis compases de "drop" con exactamente las mismas capas que
    # los dieciseis anteriores. El drop es donde entra todo; si la capa que lo
    # define llega a la mitad, la primera mitad no es un drop.
    for c in range(COMPASES):
        # el bloque de 4 compases decide sobre que acorde gira
        g = PROGRESION[c // 4]
        # y cada 4 compases la figura sube una posicion del giro: es lo que hace
        # que 16 compases no sean el mismo compas dieciseis veces
        desfase = ((c - COMPAS_SOLO) // 4) % len(GIRO)
        for k in range(16):
            if k in HUECO_ARPEGIO:
                continue
            grado_rel = GIRO[(k + desfase) % len(GIRO)]
            alt = grado(tonica, escala, g + grado_rel, octava=4)
            # velocidad casi pareja: la variacion medida es 0.13
            vel = 72 if k % 4 == 0 else 64
            p.nota(c, h.pulso("gancho", c, k * 0.25), alt, 0.22,
                   h.vel("gancho", c, k * 0.25, vel))
    return p


# Las tres capas que hacen que el tema crezca en vez de quedarse.
#
# El diagnostico que las motiva: medido compas por compas, del 17 al 60 el tema
# tenia SIEMPRE cuatro capas y un peso entre 1800 y 2500. Cuarenta y cuatro
# compases —mas de un tercio— sin que entre ni salga nada. Y el climax, que
# llegaba a 3874, arrancaba en 2328 cuando el compas 16 ya estaba en 2065: el
# drop era 1.7 veces la intro, que no alcanza para que se escuche como un drop.
#
# Un tema no crece porque las capas que ya estan toquen mas fuerte. Crece porque
# ENTRA algo que antes no estaba. Estas tres entran escalonadas y ninguna se va:
#
#     33  los golpes anchos      (el pleno deja de ser la intro con todo puesto)
#     65  el sub y los repiques  (el drop)
#
# Ninguna reemplaza a nada. Ese es el punto.


def _sub(bpm: float, tonica: int, escala: list[int]) -> Pista:
    """La fundamental sostenida abajo de todo. Entra en el drop y no se va.

    El bajo del tema es corto y saltarin: ataca, dura media semicorchea y suelta.
    Eso da empuje y no da PESO, porque entre golpe y golpe abajo no hay nada. Un
    drop se siente en el pecho antes de que el oido lo entienda, y lo que se
    siente en el pecho es una fundamental que no para.

    Va en la misma octava que el bajo y no una abajo. Una abajo cae donde ningun
    parlante de club reproduce nada util y lo unico que hace es comerse la
    dinamica del bombo. Aca la idea es sumar cuerpo, no sumar subgraves.

    Una nota por bloque de cuatro compases, atada mientras el grado no cambia.
    Atada de verdad: reescribir la misma altura solapada no sostiene en MIDI,
    apaga — ya se cometio ese error dos veces en este archivo.
    """
    p = Pista("Sub", bpm, canal=0)
    bloques = COMPASES // 4
    b = 0
    while b < bloques:
        g = PROGRESION[b]
        fin = b
        while fin + 1 < bloques and PROGRESION[fin + 1] == g:
            fin += 1
        alt = grado(tonica, escala, g, octava=1)
        largo = (fin - b + 1) * 4 * 4
        p.nota(b * 4, 0.0, alt, largo - 0.05, 86)
        b = fin + 1
    return p


# Los golpes anchos: la triada dos octavas arriba de donde la toca `_acordes`.
#
# `_acordes` ya golpea en 1.5 y 3.5, pero en la octava 3 — el mismo registro
# donde vive el pad, asi que se confunden y suman poco. Estos van arriba, donde
# no hay nada mas que el gancho, y en las OTRAS corcheas: 0.5 y 2.5. Entre las
# dos capas los cuatro contratiempos quedan ocupados, que es el vaiven del
# genero, y ninguna de las dos tuvo que moverse para que la otra entre.
ANCHO_PULSOS = (0.5, 2.5)


def _anchos(bpm: float, tonica: int, escala: list[int], h: Humano,
            climax: bool = False) -> Pista:
    """Golpes de acorde arriba. Entran en el pleno y se abren en el climax."""
    p = Pista("Anchos", bpm, canal=0)
    for bloque in range(COMPASES // 4):
        notas = triada(tonica, escala, PROGRESION[bloque], octava=5,
                       septima=False)
        for c in range(bloque * 4, bloque * 4 + 4):
            emp = _empuje(c)
            # En el climax los golpes anchos ocupan los CUATRO contratiempos,
            # no dos. Es lo que significa que un acorde "se abre": no que suene
            # mas fuerte sino que no deje huecos. Cubrian el 42% del tiempo con
            # dos golpes de 1.05 pulsos, y una capa que suena menos de la mitad
            # del tiempo se escucha cortada por bien colocada que este.
            #
            # Caen encima de `_acordes`, que toca 1.5 y 3.5 dos octavas abajo, y
            # eso esta bien MIENTRAS compartan el perfil de humanizacion: con el
            # mismo perfil los dos golpes caen en el mismo instante y se
            # escuchan como uno solo con mas cuerpo. Con perfiles distintos
            # caerian a unos milisegundos y eso es filtro de peine.
            for pulso in ((0.5, 1.5, 2.5, 3.5) if climax else ANCHO_PULSOS):
                # en el climax se suma la quinta abajo: el acorde se abre, no se
                # mueve
                voces = notas if not climax else [notas[0] - 12] + notas
                # 1.05 pulsos y no 0.45. A 123 BPM 0.45 son 220 ms: eso
                # cubre el 22% del tiempo cuando las referencias cubren 71-84%,
                # y una capa que suena una quinta parte del tiempo se escucha
                # cortada por bien colocada que este. 1.05 son 512 ms — sigue
                # siendo un golpe y no un pad, pero ahora tiene cola.
                # 0.92 y no 1.05, y el limite no es estetico: con cuatro
                # golpes por compas el hueco entre ataque y ataque es 1.0
                # pulso, asi que 1.05 hace que cada acorde se solape con el
                # siguiente EN LA MISMA ALTURA. En MIDI eso no sostiene, apaga:
                # el note-off del primero corta al segundo y la nota real dura
                # 0.05 pulsos. Es el mismo error de las notas ligadas, y esta
                # vez lo encontro `escuchar.py` avisando "va a sonar a
                # staccato", que era exactamente el sintoma.
                p.acorde(c, h.pulso("acordes", c, pulso), voces,
                         0.92 if climax else 1.30,
                         h.vel("acordes", c, pulso,
                               (58 if climax else 44) + int(12 * emp)))
    return p


# Los repiques del drop: la percusion que se suma cuando entra todo.
#
# No es otra conga en otro lugar. Son las mismas dos congas que ya suenan en
# 1.25 y 3.25, dobladas en las semicorcheas de al lado para armar un tresillo
# de dos golpes — la figura corta que hace que la percusion suene tocada por
# alguien con dos manos y no disparada por un secuenciador.
#
# Solo en el climax, y creciendo: en la primera mitad repica una vez por compas,
# en la segunda las dos.
# Los repiques van al 808 Core Kit, que es sintetico de punta a punta: claves
# (75) y rim (37). Nada de congas ni toms: "mas electronico y menos conga".
CLAVES, RIM_808 = 75, 37
REPIQUE = ((1.25, CLAVES, 1.375, RIM_808),
           (3.25, RIM_808, 3.375, CLAVES))


def _repiques(bpm: float, h: Humano) -> Pista:
    """La mano que se suma arriba de la percusion que ya estaba."""
    p = Pista("Repiques", bpm, canal=9)
    for c in range(COMPASES):
        emp = _empuje(c)
        cuantos = 2      # completos desde el compas 1 del drop
        for pulso, _, eco, alt in REPIQUE[:cuantos]:
            p.nota(c, h.pulso("percusion", c, eco), alt, 0.10,
                   h.vel("percusion", c, eco, 44 + int(10 * emp)))
        # y en el ultimo compas de cada frase, el giro completo
        if c % 8 == 7:
            for i, k in enumerate((3.5, 3.625, 3.75, 3.875)):
                p.nota(c, h.pulso("percusion", c, k),
                       CLAVES if i % 2 else RIM_808, 0.09,
                       h.vel("percusion", c, k, 48 + i * 8))
    return p


def _correr(pista: Pista, compases: int) -> Pista:
    """Corre una pista `compases` hacia adelante. Para las entradas escalonadas."""
    fuera = Pista(pista.nombre, pista.bpm, pista.canal)
    for ev in pista._eventos:
        fuera._eventos.append(
            _Evento(ev.tick + compases * TICKS_COMPAS, ev.orden, ev.datos))
    return fuera


# La rampa: una seccion que crece de punta a punta en vez de por bloques.
#
# `_empuje` ya hace crecer los ultimos compases de cada frase de ocho, pero eso
# es una figura DENTRO de la frase y se reinicia cada vez. Lo que faltaba es lo
# otro: que la seccion entera este mas fuerte al final que al principio.
#
# Sin esto una subida de dieciseis compases tiene la misma fuerza en el primero
# que en el ultimo, y toda la tension queda a cargo del redoble. Con esto el
# redoble deja de ser la unica cosa que sube y pasa a ser la ultima.
#
# Se aplica sobre los eventos ya escritos y no sobre los generadores, por la
# misma razon que `_podar`: la seccion tiene que ser EL MISMO material, y
# regenerarlo con otros parametros abre la puerta a que no lo sea.
def _rampa(pista: Pista, desde: float, hasta: float,
           compases: int = COMPASES) -> Pista:
    """Escala la velocidad linealmente de `desde` a `hasta` a lo largo de la seccion."""
    fuera = Pista(pista.nombre, pista.bpm, pista.canal)
    for ev in pista._eventos:
        datos = ev.datos
        if ev.orden == 1 and len(datos) > 2:
            c = min(compases - 1, ev.tick // TICKS_COMPAS)
            k = desde + (hasta - desde) * c / max(1, compases - 1)
            datos = bytes([datos[0], datos[1],
                           max(1, min(127, int(round(datos[2] * k))))])
        fuera._eventos.append(_Evento(ev.tick, ev.orden, datos))
    return fuera


# El riser: lo unico del tema que dura mas de un compas y no tiene ritmo.
#
# Se dispara CUATRO veces antes de cada drop, encimadas y cada vez mas fuerte,
# en vez de una sola vez larga. El motivo es practico: un sample de riser dura
# lo que dura y no se puede estirar desde el MIDI, asi que una sola nota da un
# barrido de dos compases seguido de silencio justo donde hace falta lo
# contrario. Cuatro disparos escalonados arman una escalera que llega arriba
# cualquiera sea el largo del sample.
RISER = [(24, 78), (28, 92), (30, 106), (31, 120)]


def _riser(bpm: float) -> Pista:
    """Los cuatro disparos que desembocan en el drop."""
    p = Pista("Riser", bpm, canal=0)
    for compas, vel in RISER:
        p.nota(compas, 0.0, SPLASH, 4.0, vel)
    return p


# El platillo del drop y el barrido que lo anuncia.
#
# Van en sus propias pistas por dos motivos y los dos importan. Uno: dentro del
# Drum Rack comparten la cadena con el bombo, asi que no se les puede abrir la
# reverb —que es la mitad de lo que hace que un platillo suene grande— sin
# ahogar el golpe que sostiene el tema. Dos: el crash del 909 es una muestra de
# un platillo de bronce, y en un tema donde todo lo demas es sintetico eso se
# escucha como que entro un baterista.
#
# El cimbal 808 no es un platillo grabado: es ruido pasado por seis osciladores
# cuadrados. No tiene el cuerpo del bronce y por eso no compite con nada en el
# medio — es puro brillo, que es exactamente lo que un drop necesita arriba.
SPLASH = 60          # los dos van en Simpler, y ahi el do central es la muestra
                     # sin transponer


def _splash(bpm: float, h: Humano, cada: int = 8) -> Pista:
    """El platillo, en el uno de cada frase. El primero pega mas fuerte."""
    p = Pista("Splash", bpm, canal=0)
    for c in range(0, COMPASES, cada):
        p.nota(c, 0.0, SPLASH, 2.0, 127 if c == 0 else 96)
    return p


def _reversa(bpm: float, compases: list[int]) -> Pista:
    """El barrido que entra al reves y desemboca en el golpe.

    Se dispara un compas antes del destino, no dos. Una reversa dura entre uno y
    dos segundos; a 123 BPM un compas son 1.95 s, asi que arranca casi inaudible
    y llega a su pico justo en el uno siguiente. Dos compases antes empieza a
    subir cuando todavia falta media frase y se escucha como un ruido que no
    lleva a ningun lado.

    No se humaniza. Es lo unico del tema que tiene que caer exacto: su pico ESTA
    en el final del sample, asi que correrle el ataque le corre el pico.
    """
    p = Pista("Reversa", bpm, canal=0)
    for c in compases:
        p.nota(c, 0.0, SPLASH, 4.0, 104)
    return p


def _cierre(bpm: float, tonica: int, h: Humano) -> Pista:
    """La linea de arriba de la salida: notas largas bajando.

    Se escribe desde el compas 0 de su propio archivo, no desde el 96. Es una
    seccion aparte y se arrastra al arreglo donde vaya; poner noventa y seis
    compases vacios adelante solo hace un clip que no se puede editar.

    NO es un instrumento solista y no lleva la seccion sola: la lleva
    `_salida()`, que le pone abajo el resto del tema soltando capas. Esta
    funcion escribe una capa, no un final.
    """
    return _tocar("Cierre", bpm, tonica, h, CIERRE, 0)


# La salida: los dieciseis compases del 97 al 112.
#
# La version anterior soltaba una capa cada cuatro compases y terminaba en 204
# de peso contra los 3874 del climax. Escrito parecia razonable —un final baja—
# y medido es el error central del arreglo: el tema pasaba treinta y dos
# compases construyendo el unico momento donde entra todo, y despues dedicaba
# dieciseis a desarmarlo.
#
# Un tema que explota no se apaga. La salida es el climax ENTERO, sin sacar
# nada, mas la linea larga de arriba que en el climax no estaba. Una capa mas
# que el momento mas grande del tema, no cinco menos.
#
# Y el ultimo compas no suelta: el turnaround existe para volver al principio y
# aca no se vuelve a ningun lado.
TICKS_COMPAS = 480 * 4


def _podar(pista: Pista, desde: int, hasta: int) -> Pista:
    """Recorta una pista a la ventana [desde, hasta) y la corre al compas 0.

    Nada mas: no saca capas.

    Dos cosas que parecen detalle y no lo son. Los note-off que caen despues del
    corte no se descartan, se pegan al corte — descartarlos deja la nota colgada
    y el sintetizador la sostiene para siempre, que es el mismo error que ya se
    cometio dos veces con las notas ligadas. Y las notas que ya venian sonando
    cuando arranca la ventana se vuelven a atacar en el compas 0, porque si no
    la atmosfera y el sub —que son una nota larga por bloque— desaparecerian
    justo en la seccion donde tienen que sostener el piso.
    """
    ini, corte = desde * TICKS_COMPAS, hasta * TICKS_COMPAS
    fuera = Pista(pista.nombre, pista.bpm, pista.canal)
    sonando: dict[int, bytes] = {}
    for ev in sorted(pista._eventos):
        if len(ev.datos) < 3:
            continue
        altura = ev.datos[1]
        if ev.tick < ini:
            if ev.orden == 1:
                sonando[altura] = ev.datos
            else:
                sonando.pop(altura, None)
            continue
        if ev.tick >= corte and ev.orden != 0:
            continue
        if altura in sonando and ev.orden == 0:
            fuera._eventos.append(_Evento(0, 1, sonando.pop(altura)))
        fuera._eventos.append(_Evento(min(ev.tick, corte) - ini, ev.orden, ev.datos))
    for altura, datos in sonando.items():
        fuera._eventos.append(_Evento(0, 1, datos))
        fuera._eventos.append(_Evento(corte - ini, 0,
                                      bytes([0x80 | pista.canal, altura, 0])))
    return fuera


def _salida(bpm: float, tonica: int, escala: list[int], h: Humano,
            compases: int = 16) -> list[tuple[str, Pista]]:
    """Los dieciseis finales: la mitad mas grande del climax, mas la linea larga.

    Se toma la SEGUNDA mitad del climax y no la primera. La primera pesa 3014 y
    la segunda 3845: empezar el final con la mitad liviana lo hacia caer un 25%
    justo despues del pico, que es la version elegante de apagarse.
    """
    base = [("01_atmosfera", _atmosfera(bpm, tonica, escala)),
            ("02_acordes", _acordes(bpm, tonica, escala, h, True, False)),
            ("03_bajo", _bajo(bpm, tonica, escala, h, True, True, False)),
            ("04_bateria", _bateria(bpm, h, True, True, False)),
            ("05_gancho", _gancho(bpm, tonica, escala, h, True, True, False)),
            ("06_arpegio", _arpegio(bpm, tonica, escala, h)),
            ("08_anchos", _anchos(bpm, tonica, escala, h, True)),
            ("09_sub", _sub(bpm, tonica, escala)),
            ("10_repiques", _repiques(bpm, h)),
            ("11_splash", _splash(bpm, h))]
    desde = COMPASES - compases
    fuera = [(f"{n}.mid", _podar(pi, desde, COMPASES)) for n, pi in base]
    fuera.append(("07_cierre.mid", _cierre(bpm, tonica, h)))
    return fuera


def _gancho_tecno(bpm: float, tonica: int, escala: list[int], h: Humano,
                  climax: bool = False) -> Pista:
    """La melodia sostenida. Tres notas cada cuatro compases, largas."""
    p = Pista("Gancho", bpm, canal=0)
    for bloque in range(COMPASES // 4):
        g = PROGRESION[bloque]
        for compas, pulso, grado_rel, dur in GANCHO_TECNO:
            c = bloque * 4 + compas
            if c >= COMPASES:
                continue
            octava = 4 if climax else 3
            p.nota(c, h.pulso("gancho", c, pulso),
                   grado(tonica, escala, g + grado_rel, octava=octava), dur,
                   h.vel("gancho", c, pulso, 78 if climax else 68))
    return p


def _gancho(bpm: float, tonica: int, escala: list[int], h: Humano,
            pleno: bool = False, climax: bool = False, tension: bool = False) -> Pista:
    """La melodia. Entra sola en el 17 y se abre en dos pasos, no en uno.

    Las alturas del gancho no se tocaron: las de los ultimos ocho compases son
    exactamente las mismas tres voces de antes. Lo que cambio es CUANDO llega
    cada una y cual de las tres lleva la melodia.

    Antes, en el compas 25, pasaban tres cosas en el mismo tiempo 1: la voz
    principal saltaba una octava entera (73 -> 85), se le sumaba la tercera
    arriba y se le sumaba la octava abajo. Tres movimientos de desarrollo
    gastados en un golpe, y peor: la linea que el oido venia siguiendo ocho
    compases desaparecia de donde estaba y reaparecia arriba, mientras su
    registro viejo quedaba ocupado por la voz mas floja de las tres. Eso no se
    escucha como que la melodia crecio: se escucha como un corte de cinta.

    Ahora la voz principal NO se mueve nunca de la octava 4. Es la misma linea
    de punta a punta, sin un solo salto:

        17-24  sola
        25-28  se le suma la octava arriba  (registro: se abre el rango)
        29-32  se le suma la tercera arriba (cuerpo: pasa a ser dos voces)

    Es la escalera de desarrollo en orden y de a un escalon por vez, que es
    para lo que sirve tener cuatro formas distintas de repetir con una
    diferencia. Si se gastan dos en el mismo compas queda un salto, y despues
    no queda a donde crecer.
    """
    p = Pista("Gancho", bpm, canal=0)
    vuelta = () if climax else VUELTA_BASE
    for bloque in (range(8) if pleno else (4, 5, 6, 7)):
        # en el climax, la segunda mitad se va a la figura dulce
        dulce = climax and bloque >= 4
        figura = GANCHO_DULCE if dulce else GANCHO
        # La escalera de desarrollo es de la PRIMERA pasada. En el climax ya se
        # subio entera, y volver a empezarla desde abajo hace que el drop abra
        # mas flojo que el compas anterior — que es exactamente lo que se medía:
        # el compas 63 pesaba 3436 y el 65, el primero del drop, 2830.
        doble = climax or bloque >= 6    # 25-32: octava arriba
        cuerpo = climax or bloque >= 7   # 29-32: y ademas la tercera
        for compas, pulso, g, dur in figura:
            c = bloque * 4 + compas
            if c >= COMPASES or (tension and c in VACIO):
                continue
            # El gancho suena los treinta y dos compases del climax. Antes se
            # callaba en el 17 para dejarle el lugar al arpegio, y eso no es
            # sumar una capa: es cambiarla. El oido no escucha "entro algo",
            # escucha "se fue la melodia". En el momento mas grande del tema
            # tienen que estar los dos.
            largo = dur > 1.2
            # La voz que lleva la melodia. Siempre la misma octava, y sube de
            # nivel en cada paso: la melodia se abre creciendo ella, no
            # cediendole el protagonismo a una voz nueva.
            base = (92 if largo else 76) + (4 if doble else 0) + (6 if cuerpo else 0)
            p.nota(c, h.pulso("gancho", c, pulso),
                   grado(tonica, escala, g, octava=4), dur,
                   h.vel("gancho", c, pulso, base))
            # La figura dulce ya vive arriba —sus grados son 4, 6, 7 y 8 contra
            # los 1 a 5 del gancho— asi que no se le suma la octava y su tercera
            # va en la MISMA octava. Antes la tercera caia una decima arriba y
            # llegaba al MIDI 95: en un pluck filtrado eso se escucha fino y se
            # despega del resto. El intervalo que da color es la tercera; la
            # decima es la misma nota mas lejos y suena a otra cosa.
            if doble and not dulce:
                # La tercera ABAJO, no la octava arriba.
                #
                # La octava arriba llevaba el techo a MIDI 90 con velocidad 60:
                # la voz mas aguda de todo el tema era la mas floja, y el techo
                # de la textura lo ponia la voz de color en vez de la que lleva
                # la linea. Eso es lo que se escucha como fino.
                #
                # Una tercera abajo engorda sin subir. La melodia vuelve a ser
                # la voz mas aguda, que es donde tiene que estar la mas fuerte,
                # y el desarrollo sigue teniendo sus dos escalones: primero
                # cuerpo abajo, despues color arriba.
                p.nota(c, h.pulso("gancho", c, pulso + 0.01),
                       grado(tonica, escala, g - 2, octava=4), dur,
                       h.vel("gancho", c, pulso, 74 if largo else 60))
            if cuerpo or dulce:
                # la tercera arriba es la que da el color: recien aca la
                # melodia deja de ser una linea y pasa a ser dos voces
                p.nota(c, h.pulso("gancho", c, pulso + 0.02),
                       (grado(tonica, escala, g - 2, octava=4) if dulce
                        else grado(tonica, escala, g + 2, octava=4)), dur,
                       h.vel("gancho", c, pulso, 62 if largo else 50))
    return p


# El lead: la unica capa que existe SOLO en el segundo drop.
#
# Medido, el primer drop y el segundo daban 2097 y 2099 de impacto — identicos
# al 0.1%. Dos drops iguales no son dos drops: son el mismo drop puesto dos
# veces, y el segundo no tiene entonces ningun motivo para existir.
#
# La forma de arreglarlo NO es achicar el primero. Es que el segundo tenga algo
# que el primero no tuvo, y que el oido pueda nombrar: aca es la figura dulce
# —la que hasta ahora solo aparecia adentro del gancho, tapada por las otras dos
# voces— tocada arriba de todo, larga y sola en su registro.
#
# Es tambien la razon por la que la bajada toca el gancho entero: cuando esta
# figura vuelve en el compas 161 ya se escucho, y volver es mas fuerte que
# aparecer.
PISO_LEAD = 5           # octava: arriba del gancho y arriba de los anchos


def _lead(bpm: float, tonica: int, escala: list[int], h: Humano) -> Pista:
    """La figura dulce arriba de todo, en notas largas."""
    p = Pista("Lead", bpm, canal=0)
    for bloque in range(COMPASES // 4):
        for compas, pulso, g, dur in GANCHO_DULCE:
            c = bloque * 4 + compas
            if c >= COMPASES:
                continue
            # Solo las notas largas de la figura. Las cortas son el adorno que
            # la conecta, y arriba de un drop entero un adorno no se escucha:
            # se escucha como suciedad en la banda donde vive el arpegio.
            if dur < 1.2:
                continue
            p.nota(c, h.pulso("gancho", c, pulso),
                   grado(tonica, escala, g, octava=PISO_LEAD), dur * 1.4,
                   h.vel("gancho", c, pulso, 84))
    return p


# Las cuatro capas que espesan.
#
# El diagnostico fue "sigue pareciendo un ringtone por momentos" y "le faltan
# pistas". Las dos frases dicen lo mismo desde dos lados: un ringtone es una
# melodia correcta tocada por UN sonido fino, sin nada abajo ni alrededor. La
# diferencia con una produccion no esta en las notas —las notas ya salen de
# medir referencias— sino en que cada rol lo tocan dos o tres cosas a la vez y en
# que siempre hay algo sonando que no es una nota.
#
# Ninguna de estas cuatro agrega una idea musical nueva. Todas espesan algo que
# ya estaba, que es exactamente el punto: una capa que trae una idea nueva
# compite, una que dobla suma cuerpo.


def _bajo_medio(bpm: float, tonica: int, escala: list[int], h: Humano,
                climax: bool = False) -> Pista:
    """El bajo doblado una octava arriba, corto y con ataque.

    Es la capa que hace que un bajo se ESCUCHE en un parlante chico. El grave
    solo se siente en el cuerpo y desaparece en un telefono o en un monitor de
    cinco pulgadas; el doblaje en la octava de arriba lleva la misma linea a
    donde si se oye. En techno esta siempre, y es la mitad de por que un bajo
    suena grande.
    """
    # Dobla EXACTAMENTE lo que toca el grave: se genera el bajo y se
    # transponen sus eventos una octava, con las notas recortadas. Escribirlo
    # aparte, con otra celula, es la forma segura de que un dia dejen de
    # coincidir.
    grave = _bajo(bpm, tonica, escala, h, True, climax, False)
    p = Pista("Bajo medio", bpm, canal=0)
    abiertas: dict[int, int] = {}
    for ev in sorted(grave._eventos):
        if len(ev.datos) < 3:
            continue
        alt = min(127, ev.datos[1] + 12)
        if ev.orden == 1:
            abiertas[alt] = ev.tick
            p._eventos.append(_Evento(ev.tick, 1, bytes([ev.datos[0], alt, int(ev.datos[2] * 0.8)])))
        else:
            ini = abiertas.pop(alt, ev.tick)
            fin = min(ev.tick, ini + int(0.45 * 480))
            p._eventos.append(_Evento(max(fin, ini + 1), 0, bytes([ev.datos[0], alt, 0])))
    return p


def _textura(bpm: float) -> Pista:
    """Una nota que no se corta nunca. Es el piso de ruido del tema.

    Lo que mas delata a un boceto es el SILENCIO entre eventos: en una grabacion
    siempre hay aire, cinta, sala, algo. Aca eso se escribe como una nota atada
    que dura la seccion entera y que del otro lado tiene un sonido sin altura
    definida.

    Va atada y no re-atacada, por la razon de siempre: reescribir la misma
    altura solapada no sostiene en MIDI, apaga.
    """
    p = Pista("Textura", bpm, canal=0)
    p.nota(0, 0.0, 48, COMPASES * 4 - 0.05, 54)
    return p


def _subkick(bpm: float, h: Humano) -> Pista:
    """Un seno corto abajo de cada bombo.

    El bombo del 909 tiene ataque y poco cuerpo abajo de 60 Hz. En un club eso
    se escucha flaco por mas que en auriculares parezca bien. El sub-kick no se
    escucha como un sonido aparte: se escucha como que el bombo pesa mas.
    """
    p = Pista("Subkick", bpm, canal=0)
    for c in range(COMPASES):
        for pulso in range(4):
            p.nota(c, h.pulso("kick", c, pulso),
                   grado(0, MENOR, 0, octava=0) + 5, 0.22,
                   h.vel("kick", c, pulso, 96))
    return p


# Los metales: la capa aguda que se mueve y no es un hat.
#
# El hat marca el tiempo y por eso es regular; esto es lo contrario, y por eso
# hace falta. Cae en semicorcheas que el hat no usa y cambia cada dos compases,
# asi que el oido nunca termina de aprenderselo — que es la definicion practica
# de "no suena a loop".
METALES = ((2.75, 3.25, 3.75), (0.75, 2.25, 3.75), (1.75, 2.75, 3.25),
           (0.75, 1.75, 3.75))


def _metales(bpm: float, h: Humano) -> Pista:
    p = Pista("Metales", bpm, canal=9)
    for c in range(COMPASES):
        for i, pulso in enumerate(METALES[(c // 2) % len(METALES)]):
            p.nota(c, h.pulso("percusion", c, pulso), CHH, 0.08,
                   h.vel("percusion", c, pulso, 44 + i * 6))
    return p


# ---------------------------------------------------------------------------
# La forma del tema entero.
#
# Los numeros no son una opinion: salen de medir con `scripts/estructura.py`
# tres de los temas mas tocados de la propia historia —Minicube, Go y Cryo—, que
# dan 7.2, 7.5 y 8.1 minutos, intro de DJ de 16 a 32 compases, una bajada grande
# de 28 a 56 compases pasada la mitad, y salida de DJ de 24 a 32.
#
# 240 compases a 123 BPM son 7:48: adentro de ese rango y del lado largo, que es
# el lado que distingue lo que este DJ toca de lo que no (7.85 min contra 7.37).
#
# Sobre la bajada, porque es la unica resta del tema y hay que justificarla. Lo
# que estaba mal en la version anterior no era que hubiera contraste: era que el
# arco no subia nunca —cuarenta y cuatro compases con las mismas cuatro capas y
# un "drop" que era 1.7 veces la intro—. Un breakdown despues de un drop de
# treinta y dos compases es lo que hace que entre el segundo; un pozo en el
# medio de una planicie no es lo mismo aunque se escriba igual.
#
# Y las dos puntas son groove sin melodia. Eso no es una decision artistica: es
# la zona por donde se mezcla. Un tema que arranca con la melodia puesta no se
# puede pinchar arriba de otro.
FORMA = [
    # (parte,      compas de entrada, largo)
    ("intro",           0,  32),   # groove de DJ: bajo, bateria y piso
    ("tema",           32,  32),   # entra la armonia y el gancho
    ("subida1",        64,  16),   # el redoble
    ("drop1",          80,  32),   # todo
    # La bajada era de 32 y el DJ la escucho como "larguisima y muy
    # silenciosa": dieciseis, y lo que se le saca se lo lleva el segundo drop,
    # que pasa a 48. Es literalmente "mas de peak". El total sigue en 240.
    # Medido en Vuarambon con transicion.py: Estigia hace un bajon de 3-4
    # compases y vuelve a pleno; Lake Of Fire baja gradual sin llegar nunca a
    # silencio; Stamina, Zenith y Prodiga NO tienen bajada despues del drop.
    # Para "mas de peak" la bajada es un bajon de ocho, con el groove intacto,
    # y el drop 2 se lleva el resto: 56 compases.
    ("bajada",        112,   8),   # se cae el bombo: un bajon, no un breakdown
    ("subida2",       120,  16),   # el redoble otra vez, mas fuerte
    ("drop2",         136,  56),   # el mas grande del tema, y el mas largo
    ("salida",        192,  16),   # todo mas la linea larga
    ("salida_dj",     208,  32),   # groove para mezclar de salida
]

# Cuanto pega cada parte. Es el arco del tema en una sola tabla, y por eso esta
# separado de las capas: se puede discutir el arco sin tocar el arreglo.
# El primer drop no llega al techo. Es la unica forma de que el segundo
# tenga a donde llegar, y 0.93 contra 1.0 son ocho puntos de velocidad en
# cada golpe: se escucha como que el segundo pega mas, no como que el
# primero esta flojo.
INTENSIDAD = {"intro": 0.70, "tema": 0.86, "subida1": 0.90, "drop1": 0.93,
              "bajada": 1.0, "subida2": 0.96, "drop2": 1.0, "salida": 1.0,
              "salida_dj": 0.78}


def _hats_ya_hechos(fuera: list, bpm: float) -> list:
    """Lo mismo que _separar_hats para una lista ya con ".mid" y corrida."""
    for n, pi in fuera:
        if n == "04_bateria.mid":
            return fuera + [("19_hats.mid", _hats(pi, bpm))]
    return fuera


def _separar_hats(base: list, bpm: float) -> list:
    """Si hay bateria en la parte, sus hats pasan a "19_hats"."""
    for n, pi in base:
        if n == "04_bateria":
            return base + [("19_hats", _hats(pi, bpm))]
    return base


def _parte(nombre: str, bpm: float, tonica: int, escala: list[int],
           semilla: int) -> list[tuple[str, Pista]]:
    """Las pistas de una parte, ya recortadas a su largo.

    Las partes de dieciseis compases se generan de treinta y dos y se recortan.
    Es a proposito: una subida son los ultimos dieciseis compases de una seccion
    con redoble, no una seccion distinta que casualmente tiene un redoble.
    Generarla aparte la desincronizaria del material que viene sonando.
    """
    h = Humano(semilla, INTENSIDAD[nombre])
    # El bajo sostenido del techno se fue: el pedido paso a "mas Vuarambon y
    # mas de peak", y Lake Of Fire mide 7.06 ataques por compas con 96% de
    # cobertura — la celula saltarina de siempre, no una nota tenida. Se
    # mantiene lo que si es de peak: la bateria densa, el pump, las capas.
    bajo = _bajo
    gancho = _gancho_tecno if TECNO else _gancho
    pleno = nombre != "intro"
    climax = nombre in ("drop1", "drop2", "salida")
    tension = nombre in ("subida1", "subida2")
    grande = nombre in ("drop2", "salida")

    if nombre == "bajada":
        # El breakdown. Sin bombo y sin clap, con lo melodico sostenido y el
        # gancho arriba. La atmosfera y el sub sostienen el piso: sin ellos esto
        # es una melodia colgada en el aire, que es la version mal hecha de un
        # breakdown — no se escucha como que bajo, se escucha como que se rompio.
        # Los treinta y dos compases de la bajada estaban PLANOS: entre 250 y
        # 470 de impacto de punta a punta, con las seis capas sonando desde el
        # compas 1. Una bajada que no crece no prepara nada; es un hueco largo.
        #
        # Ahora entra por capas y crece. Cada cosa aparece donde le toca y
        # ninguna se va: al final de la bajada suena todo lo que sonaba antes,
        # mas fuerte, y de ahi arranca la subida.
        # Medido con transicion.py en Minicube, Cryo, Go y Typical Use: en la
        # entrada a la bajada los GRAVES caen 20 dB y los medios y agudos
        # siguen planos, a +-1 dB. Se va el bombo y el grupo de bajo. Nada
        # mas: la percusion, los metales, la textura y la armonia siguen
        # exactamente como en el drop. Lo que junta tension es la ausencia del
        # bombo sobre un groove que no paro, no el silencio.
        base = [("01_atmosfera", _atmosfera(bpm, tonica, escala)),
                ("02_acordes", _acordes(bpm, tonica, escala, h, True, False)),
                ("05_gancho", gancho(bpm, tonica, escala, h, True, False, False)
                 if not TECNO else gancho(bpm, tonica, escala, h, False)),
                ("08_anchos", _anchos(bpm, tonica, escala, h, False)),
                ("04_bateria", _bateria(bpm, h, True, True, False, sin_bombo=True)),
                ("10_repiques", _repiques(bpm, h)),
                ("18_metales", _metales(bpm, h)),
                ("16_textura", _textura(bpm))]
        # (capa, compas en que entra) — la percusion ultima, que es lo que
        # avisa que el bombo esta por volver
        # Dieciseis compases: todo entra al doble de rapido que antes, y la
        # percusion sin bombo desde el 9, para que la bajada junte tension en
        # vez de vaciarse.
        # La percusion sin bombo desde el compas 1, no desde el 9. El DJ: "es
        # re brusco, es silencio y viene de una conga linda". Con las congas
        # sonando de verdad, pasar de eso a nada en un compas era un corte de
        # cinta. En la bajada se va el BOMBO, no el groove: la conga sigue, y
        # lo que se siente es que se abrio el piso, no que se apago la luz.
        ENTRADAS = {"01_atmosfera": 0, "02_acordes": 0, "05_gancho": 0,
                    "08_anchos": 0, "04_bateria": 0, "10_repiques": 0,
                    "18_metales": 0, "16_textura": 0}
        if TECNO:
            base = [(n, pi) for n, pi in base if n != "08_anchos"]
        # Un platillo en el uno de la bajada: marca que ALGO empezo, no que
        # algo termino. Sin el, el oido lee el compas 113 como que se cayo el
        # tema.
        base.append(("11_splash", _splash(bpm, h, cada=COMPASES)))
        ENTRADAS["11_splash"] = 0
        # El piso NO entra en la rampa. La atmosfera, los acordes y el sub son
        # lo que sostiene el espacio cuando se cae el bombo, y hacerlos crecer
        # junto con el resto dejaba el primer compas de la bajada en el 7% de la
        # energia del compas anterior: eso no se escucha como que bajo, se
        # escucha como que se corto. Lo que crece es lo que ENTRA, no lo que
        # aguanta.
        PISO = {"01_atmosfera", "02_acordes", "09_sub"}
        fuera = []
        for n, pi in base:
            desde = ENTRADAS[n]
            pi = _podar(pi, 0, COMPASES - desde)
            # sin rampa: las referencias mantienen medios y agudos planos
            # durante toda la bajada; lo que crece despues es la subida
            fuera.append((n + ".mid", _correr(pi, desde)))
        return _hats_ya_hechos(fuera, bpm)

    if nombre in ("intro", "salida_dj"):
        # Groove de DJ: la zona por donde se mezcla. Bajo, bateria y el piso, y
        # nada arriba. La salida lleva ademas los repiques, porque a esa altura
        # la percusion ya es parte del tema y sacarla suena a otra cancion.
        base = [("01_atmosfera", _atmosfera(bpm, tonica, escala)),
                ("03_bajo", bajo(bpm, tonica, escala, h, pleno, False, False)
                 if not TECNO else bajo(bpm, tonica, escala, h, False)),
                ("04_bateria", _bateria(bpm, h, pleno, False, False))]
        if nombre == "salida_dj":
            base.append(("10_repiques", _repiques(bpm, h)))
        if TECNO:
            base.append(("16_textura", _textura(bpm)))
            base.append(("15_bajo2", _bajo_medio(bpm, tonica, escala, h)))
            if nombre == "salida_dj":
                base += [("17_subkick", _subkick(bpm, h)),
                         ("18_metales", _metales(bpm, h))]
        return [(n + ".mid", pi) for n, pi in _separar_hats(base, bpm)]

    base = [("01_atmosfera", _atmosfera(bpm, tonica, escala)),
            ("02_acordes", _acordes(bpm, tonica, escala, h, pleno, tension)),
            ("03_bajo", bajo(bpm, tonica, escala, h, pleno, climax, tension)
             if not TECNO else bajo(bpm, tonica, escala, h, climax)),
            ("04_bateria", _bateria(bpm, h, pleno, climax, tension)),
            ("05_gancho", gancho(bpm, tonica, escala, h, pleno, climax, tension)
             if not TECNO else gancho(bpm, tonica, escala, h, climax))]
    if not TECNO:
        # Los golpes anchos son de piano y el piano no es de este genero. En
        # techno lo de arriba se sostiene; los acordes golpeados en la octava 5
        # son justo lo contrario.
        base.append(("08_anchos", _anchos(bpm, tonica, escala, h, climax)))
    if TECNO:
        # La textura esta SIEMPRE. Es lo unico del tema que no depende de la
        # seccion, porque el aire de una sala tampoco.
        base.append(("16_textura", _textura(bpm)))
        base.append(("15_bajo2", _bajo_medio(bpm, tonica, escala, h, climax)))
        if pleno:
            base += [("17_subkick", _subkick(bpm, h)),
                     ("18_metales", _metales(bpm, h))]
    if climax:
        base += [("09_sub", _sub(bpm, tonica, escala)),
                 ("10_repiques", _repiques(bpm, h)),
                 ("11_splash", _splash(bpm, h))]
        if not TECNO:
            # Un arpegio de 13.6 ataques por compas es lo contrario de techno
            # por bien escrito que este. La referencia mide 0.81.
            base.append(("06_arpegio", _arpegio(bpm, tonica, escala, h)))
    if grande and not TECNO:
        base.append(("13_lead", _lead(bpm, tonica, escala, h)))
    if nombre == "drop1":
        # El drop 1 no cae en la bajada: la anuncia. La reversa en su ultimo
        # compas convierte el corte en una puerta.
        base.append(("12_reversa", _reversa(bpm, [COMPASES - 1])))
    if tension:
        base.append(("12_reversa", _reversa(bpm, [COMPASES - 1])))
        base.append(("14_riser", _riser(bpm)))
        # La subida entera crece: al empezar suena al 72% y llega al 100%.
        # 0.82 y no 0.72: con 0.72 la subida arrancaba MAS BAJO que la
        # seccion anterior —la bajada terminaba en 12.4 de energia sostenida y
        # la subida empezaba en 10.6—, o sea que el compas donde vuelve el bombo
        # era un bajon. Una subida puede aflojar un poco para tomar carrera,
        # pero no puede empezar abajo de donde venia.
        base = [(n, _rampa(pi, 0.82, 1.0)) for n, pi in base]
    elif grande:
        base.append(("12_reversa", _reversa(bpm, [COMPASES // 2 - 1])))
    if nombre == "salida" and not TECNO:
        base.append(("07_cierre", _cierre(bpm, tonica, h)))

    base = _separar_hats(base, bpm)
    largo = {n: l for n, _, l in FORMA}[nombre]
    if largo == COMPASES:
        return [(n + ".mid", pi) for n, pi in base]
    if largo > COMPASES:
        # Una parte mas larga que lo que escriben los generadores (el drop 2
        # de 48) se extiende repitiendo su SEGUNDA mitad, que es la mas llena.
        # Recortar "los ultimos 48 de 32" daba una ventana negativa que corria
        # todo dieciseis compases y dejaba los primeros dieciseis vacios: el
        # render del drop medio 13 compases de silencio digital y se busco el
        # error en Live durante media hora.
        fuera = []
        for n, pi in base:
            cola = _correr(_podar(pi, COMPASES - (largo - COMPASES), COMPASES), COMPASES)
            pi._eventos = pi._eventos + cola._eventos
            fuera.append((n + ".mid", pi))
        return fuera
    # Las de dieciseis compases se quedan con la SEGUNDA mitad: en una subida es
    # donde esta el redoble, y en la salida es la mitad mas pesada del climax.
    return [(n + ".mid", _podar(pi, COMPASES - largo, COMPASES)) for n, pi in base]


def escribir_tema(bpm: float, tonica: int, escala: list[int], semilla: int,
                  destino: Path) -> list[tuple[str, int, int, int]]:
    """Escribe las nueve partes, cada una en su carpeta."""
    mapa = []
    for nombre, compas, largo in FORMA:
        d = destino / nombre
        d.mkdir(parents=True, exist_ok=True)
        for viejo in d.glob("*.mid"):
            viejo.unlink()
        pistas = _parte(nombre, bpm, tonica, escala, semilla)
        for archivo, pista in pistas:
            pista.guardar(d / archivo)
        mapa.append((nombre, compas, largo, len(pistas)))
    return mapa


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camelot", default="11A")
    ap.add_argument("--bpm", type=float, default=123.0)
    ap.add_argument("--nombre", default="idea")
    ap.add_argument("--tension", action="store_true",
                    help="vacia los compases 29-30 y acelera en 31-32, como hace "
                         "Moonflare antes de su drop")
    ap.add_argument("--climax", action="store_true",
                    help="la parte que explota: bajo doblado una octava arriba, "
                         "abierto en los cuatro contratiempos, eco de clap y el "
                         "gancho con las tres voces desde el compas 1")
    ap.add_argument("--pleno", action="store_true",
                    help="sin puertas de entrada: todo suena desde el compas 1. "
                         "Es la version para la SEGUNDA pasada — el loop de 32 "
                         "compases es una apertura de tema, no un loop, y ponerlo "
                         "dos veces mete un agujero justo despues del final")
    ap.add_argument("--cierre", action="store_true",
                    help="genera la SALIDA: los dieciseis compases que van "
                         "DESPUES del climax, con el tema entero soltando una "
                         "capa cada cuatro compases. No es una pista sola")
    ap.add_argument("--intensidad", type=float, default=1.0,
                    help="escala global de velocidad: 0.82 apertura, 0.92 pleno, "
                         "1.0 climax. Es como se dibuja el arco entre secciones")
    ap.add_argument("--semilla", type=int, default=7,
                    help="misma semilla, mismo archivo: sirve para comparar versiones")
    ap.add_argument("--tecno", action="store_true",
                    help="modo techno: bajo sostenido, melodia tenida, mas "
                         "percusion, y sin arpegio, anchos, lead ni cierre")
    ap.add_argument("--tema", action="store_true",
                    help="escribe el TEMA ENTERO: las nueve partes de FORMA, "
                         "240 compases = 7:48 a 123 BPM")
    args = ap.parse_args()

    global TECNO
    TECNO = args.tecno
    tonica, menor = tonica_de_camelot(args.camelot)
    escala = MENOR if menor else MAYOR
    if args.tema:
        raiz = Path("postproduction/bocetos") / args.nombre
        mapa = escribir_tema(args.bpm, tonica, escala, args.semilla, raiz)
        total = max(c + l for _, c, l, _ in mapa)
        seg = total * 4 * 60 / args.bpm
        print("  " + nombre_tonalidad(args.camelot) +
              " a %.0f BPM\n" % args.bpm)
        for nom, c, l, n in mapa:
            print("   %4d-%-5d %-11s %3d compases  %d pistas"
                  % (c + 1, c + l, nom, l, n))
        print("\n  %d compases = %d:%02d" % (total, seg // 60, seg % 60))
        return
    destino = Path("postproduction/bocetos") / args.nombre
    destino.mkdir(parents=True, exist_ok=True)
    for viejo in destino.glob("*.mid"):
        viejo.unlink()

    h = Humano(args.semilla, args.intensidad)
    pleno = args.pleno
    cl = args.climax
    pleno = pleno or cl
    te = args.tension
    pistas = [("01_atmosfera.mid", _atmosfera(args.bpm, tonica, escala)),
              ("02_acordes.mid", _acordes(args.bpm, tonica, escala, h, pleno, te)),
              ("03_bajo.mid", _bajo(args.bpm, tonica, escala, h, pleno, cl, te)),
              ("04_bateria.mid", _bateria(args.bpm, h, pleno, cl, te)),
              ("05_gancho.mid", _gancho(args.bpm, tonica, escala, h, pleno, cl, te))]
    # Las capas entran escalonadas y NINGUNA se va. Es lo que hace que el
    # numero de capas suba de punta a punta en vez de quedarse en cuatro.
    if pleno:
        pistas.append(("08_anchos.mid", _anchos(args.bpm, tonica, escala, h, cl)))
    if te:
        # la reversa del ultimo compas es lo que empalma la subida con el drop
        pistas.append(("12_reversa.mid", _reversa(args.bpm, [COMPASES - 1])))
    if cl:
        pistas.append(("06_arpegio.mid", _arpegio(args.bpm, tonica, escala, h)))
        pistas.append(("09_sub.mid", _sub(args.bpm, tonica, escala)))
        pistas.append(("10_repiques.mid", _repiques(args.bpm, h)))
        pistas.append(("11_splash.mid", _splash(args.bpm, h)))
        pistas.append(("12_reversa.mid", _reversa(args.bpm, [COMPASES // 2 - 1])))
    if args.cierre:
        # la salida REEMPLAZA a las pistas del loop: son sus propios dieciseis
        # compases, no los treinta y dos de la seccion
        pistas = _salida(args.bpm, tonica, escala, h)

    print(f"  {nombre_tonalidad(args.camelot)} a {args.bpm:.0f} BPM, "
          f"{COMPASES} compases = {COMPASES * 4 * 60 / args.bpm:.0f} segundos\n")
    print("  1-8    bajo y percusion, sin bombo")
    print("  9-12   entra el bombo solo, y la armonia")
    print("  13-16  entra el clap")
    if cl:
        print("  17-32  se calla el gancho y entra la guitarra: 16 compases")
        print("         17-22 abajo y contenida  23-28 se instala arriba")
        print("         29-30 la subida  31 el grito en E6  32 la caida")
    else:
        print("  17-24  entra el gancho, solo")
        print("  25-28  al gancho se le suma la octava arriba")
        print("  29-32  y ademas la tercera: la melodia queda en dos voces")
    print("  8/16/24  repique y crescendo de paso hacia cada cambio")
    print()
    for archivo, p in pistas:
        p.guardar(destino / archivo)
        n = sum(1 for e in p._eventos if e.datos[0] & 0xF0 == 0x90)
        print(f"  {archivo:16} {n:4d} notas = {n / COMPASES:4.1f} por compas")
    print(f"\n  python scripts/a_live.py {destino} --bpm {args.bpm:.0f}")


if __name__ == "__main__":
    main()
